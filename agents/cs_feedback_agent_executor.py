from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import TaskStatusUpdateEvent, TaskArtifactUpdateEvent, TaskStatus, TaskState, Artifact, TextPart
import json
import re
import uuid
import logging

logger = logging.getLogger(__name__)

class CSFeedbackExecutor(AgentExecutor):
    async def cancel(self, task_id: str) -> None:
        logger.info(f"Cancelling task {task_id}")
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            from cs_feedback_agent import agent
            
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
            
            # Agent 실행
            result = await agent.invoke_async(full_input)
            response = result.output if hasattr(result, 'output') else str(result)
            
            logger.info(f"Agent response: {response}")
            
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
