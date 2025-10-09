import logging
import uuid
import json
import re
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import TaskState, TaskStatus, Artifact, TaskStatusUpdateEvent, TaskArtifactUpdateEvent, TextPart
from strands import Agent, tool
from strands.models.bedrock import BedrockModel

logger = logging.getLogger(__name__)

FEEDBACK_DATA = [
    {"race": "Terran", "complaint": "테란 마린 러시가 너무 강력합니다. 초반 방어가 불가능해요.", "upvotes": 245, "urgency": "high", "date": "2025-10-01"},
    {"race": "Zerg", "complaint": "저그 뮤탈이 너프되어서 이제 쓸모가 없습니다.", "upvotes": 312, "urgency": "high", "date": "2025-10-01"},
    {"race": "Protoss", "complaint": "프로토스 광전사 체력이 너무 약합니다.", "upvotes": 189, "urgency": "medium", "date": "2025-10-02"},
    {"race": "Terran", "complaint": "테란 벙커 건설 속도가 너무 빨라서 러시 방어가 쉽습니다.", "upvotes": 201, "urgency": "high", "date": "2025-10-03"},
    {"race": "Zerg", "complaint": "저그 히드라 사거리가 짧아서 쓸모가 없어요.", "upvotes": 156, "urgency": "medium", "date": "2025-10-03"},
    {"race": "Protoss", "complaint": "프로토스 스톰 데미지가 너무 강력합니다.", "upvotes": 267, "urgency": "high", "date": "2025-10-04"},
]

@tool
def get_feedback(urgency: str = None, race: str = None) -> str:
    """Get customer feedback from game forums
    
    Args:
        urgency: Filter by urgency level (high, medium, low)
        race: Filter by race (Terran, Zerg, Protoss)
    """
    filtered = FEEDBACK_DATA
    if urgency:
        filtered = [f for f in filtered if f["urgency"] == urgency]
    if race:
        filtered = [f for f in filtered if f["race"] == race]
    
    result = []
    for f in filtered:
        result.append(f"[{f['race']}] {f['complaint']} (추천: {f['upvotes']}, 날짜: {f['date']})")
    
    return "\n".join(result) if result else "No feedback found"

agent = Agent(
    name="CS Feedback Agent",
    description="게임 포럼에서 고객 피드백을 조회하는 에이전트",
    model=BedrockModel(model_id="us.amazon.nova-lite-v1:0", temperature=0.3),
    tools=[get_feedback],
    system_prompt="""당신은 고객 지원 담당자입니다.

**응답 형식 (JSON):**
{
  "status": "completed" | "input_required" | "error",
  "message": "사용자에게 보여줄 메시지"
}

**도구 사용:**
- get_feedback(): 모든 피드백 조회
- get_feedback(race="Terran"): 특정 종족 피드백
- get_feedback(urgency="high"): 긴급도별 피드백

**상태 결정:**
- completed: 요청을 완료하고 결과를 제공한 경우
- input_required: 추가 정보가 필요한 경우
- error: 오류 발생 시

**중요: 모든 응답은 한글로 작성하세요.**"""
)

class CSFeedbackExecutor(AgentExecutor):
    async def cancel(self, task_id: str) -> None:
        logger.info(f"Cancelling task {task_id}")
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            # Message에서 텍스트 추출
            input_text = ""
            if context.message and hasattr(context.message, 'parts') and context.message.parts:
                for part in context.message.parts:
                    if hasattr(part, 'root') and hasattr(part.root, 'text'):
                        input_text += part.root.text
            
            logger.info(f"Executing task {context.task_id}: '{input_text}'")
            
            # 대화 히스토리 구성
            conversation_history = []
            if context.current_task and hasattr(context.current_task, 'artifacts'):
                for artifact in context.current_task.artifacts:
                    if hasattr(artifact, 'parts'):
                        for part in artifact.parts:
                            if hasattr(part, 'text'):
                                conversation_history.append(part.text)
            
            # 전체 컨텍스트 구성
            if conversation_history:
                full_input = f"이전 대화:\n" + "\n".join(conversation_history) + f"\n\n현재 질문: {input_text}"
            else:
                full_input = input_text
            
            logger.info(f"Full context: {full_input}")
            
            # Agent 스트리밍 실행
            full_response = ""
            thinking_buffer = ""
            
            async for event in agent.stream_async(full_input):
                if isinstance(event, dict):
                    event_type = event.get('type')
                    
                    # Thinking 이벤트 - 실시간 전송
                    if event_type == 'thinking':
                        thinking_text = event.get('content', '')
                        thinking_buffer += thinking_text
                        # Thinking artifact 전송
                        await event_queue.enqueue_event(TaskArtifactUpdateEvent(
                            taskId=context.task_id,
                            contextId=context.context_id,
                            artifact=Artifact(
                                artifactId=str(uuid.uuid4()),
                                parts=[TextPart(text=f"🧠 {thinking_buffer}")]
                            )
                        ))
                    
                    # 텍스트 델타
                    elif event_type == 'text_delta':
                        full_response += event.get('content', '')
                    
                    # 최종 메시지
                    elif event_type == 'message':
                        full_response = event.get('content', '')
            
            # 최종 응답 확인
            if not full_response:
                result = await agent.invoke_async(full_input)
                full_response = result.output if hasattr(result, 'output') else str(result)
            
            logger.info(f"Agent response: {full_response}")
            response = full_response
            
            # JSON 파싱 시도
            try:
                # <thinking> 태그 제거
                clean_response = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL).strip()
                response_data = json.loads(clean_response)
                status = response_data.get('status', 'completed')
                message = response_data.get('message', response)
            except Exception as parse_error:
                # JSON 파싱 실패 시 기본값
                logger.warning(f"JSON parsing failed: {parse_error}, using defaults")
                status = 'completed'
                message = response
            
            # Artifact 생성
            artifact = Artifact(
                artifactId=str(uuid.uuid4()),
                parts=[TextPart(text=message)]
            )
            
            # Artifact 먼저 전송
            await event_queue.enqueue_event(TaskArtifactUpdateEvent(
                taskId=context.task_id,
                contextId=context.context_id,
                artifact=artifact
            ))
            
            # 상태에 따라 Task 업데이트
            if status == 'input_required':
                await event_queue.enqueue_event(TaskStatusUpdateEvent(
                    taskId=context.task_id,
                    contextId=context.context_id,
                    status=TaskStatus(state=TaskState.input_required),
                    final=True
                ))
            elif status == 'error':
                await event_queue.enqueue_event(TaskStatusUpdateEvent(
                    taskId=context.task_id,
                    contextId=context.context_id,
                    status=TaskStatus(state=TaskState.failed),
                    final=True
                ))
            else:  # completed
                await event_queue.enqueue_event(TaskStatusUpdateEvent(
                    taskId=context.task_id,
                    contextId=context.context_id,
                    status=TaskStatus(state=TaskState.completed),
                    final=True
                ))
                
        except Exception as e:
            logger.error(f"Error executing task: {e}", exc_info=True)
            error_artifact = Artifact(
                artifactId=str(uuid.uuid4()),
                parts=[TextPart(text=f"에러 발생: {str(e)}")]
            )
            await event_queue.enqueue_event(TaskArtifactUpdateEvent(
                taskId=context.task_id,
                contextId=context.context_id,
                artifact=error_artifact
            ))
            await event_queue.enqueue_event(TaskStatusUpdateEvent(
                taskId=context.task_id,
                contextId=context.context_id,
                status=TaskStatus(state=TaskState.failed),
                final=True
            ))
