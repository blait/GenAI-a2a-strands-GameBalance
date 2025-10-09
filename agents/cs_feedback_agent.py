#!/usr/bin/env python3
from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
import uvicorn

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

from cs_feedback_agent_executor import CSFeedbackExecutor
from starlette.routing import Route
from starlette.responses import StreamingResponse
import json
import re

async def ask_stream(request):
    """Streaming endpoint for GUI"""
    body = await request.json()
    query = body.get('query', '')
    
    async def generate():
        try:
            result = await agent.invoke_async(query)
            full_response = result.output if hasattr(result, 'output') else str(result)
            
            # Extract and send thinking
            thinking_matches = re.findall(r'<thinking>(.*?)</thinking>', full_response, re.DOTALL)
            for thinking in thinking_matches:
                yield f"data: {json.dumps({'type': 'thinking', 'content': thinking.strip()})}\n\n"
            
            # Remove thinking tags
            clean_response = re.sub(r'<thinking>.*?</thinking>', '', full_response, flags=re.DOTALL).strip()
            
            if clean_response:
                yield f"data: {json.dumps({'type': 'answer', 'content': clean_response})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

def create_app():
    from a2a.types import AgentCard, AgentCapabilities, AgentSkill
    
    agent_card = AgentCard(
        name="CS Feedback Agent",
        description="게임 포럼 고객 피드백 조회 에이전트",
        url="http://localhost:9002",
        version="1.0.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        skills=[
            AgentSkill(
                id="get_feedback",
                name="get_feedback",
                description="게임 포럼 피드백 조회",
                tags=[],
                input_description="조회할 종족 또는 긴급도",
                output_description="피드백 목록"
            )
        ],
        capabilities=AgentCapabilities(streaming=True, multi_turn=True)
    )
    
    request_handler = DefaultRequestHandler(
        agent_executor=CSFeedbackExecutor(),
        task_store=InMemoryTaskStore()
    )
    
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )
    
    base_app = server.build()
    base_app.routes.append(Route('/ask_stream', ask_stream, methods=['POST']))
    
    return base_app

app = create_app()

if __name__ == "__main__":
    print("📞 Starting CS Feedback Agent on port 9002...")
    uvicorn.run(app, host="127.0.0.1", port=9002)
