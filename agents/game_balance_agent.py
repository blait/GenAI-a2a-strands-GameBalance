#!/usr/bin/env python3
from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
import uvicorn
import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import Message, Part, TextPart, Role
from uuid import uuid4

# A2A client for calling other agents
class A2AClient:
    def __init__(self):
        self.agents = {
            "data": "http://localhost:9003",
            "cs": "http://localhost:9002"
        }
        self.cards = {}
    
    async def init(self):
        async with httpx.AsyncClient(timeout=60) as client:
            for name, url in self.agents.items():
                try:
                    resolver = A2ACardResolver(httpx_client=client, base_url=url)
                    self.cards[name] = await resolver.get_agent_card()
                    print(f"✅ Connected to {name} agent")
                except Exception as e:
                    print(f"❌ Failed to connect to {name}: {e}")
    
    async def call_agent(self, agent_name: str, query: str) -> str:
        if agent_name not in self.cards:
            return f"Agent {agent_name} not available"
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                config = ClientConfig(httpx_client=client, streaming=False)
                factory = ClientFactory(config)
                a2a_client = factory.create(self.cards[agent_name])
                
                msg = Message(
                    kind="message",
                    role=Role.user,
                    parts=[Part(TextPart(kind="text", text=query))],
                    message_id=uuid4().hex
                )
                
                response_text = ""
                async for event in a2a_client.send_message(msg):
                    if isinstance(event, tuple):
                        event = event[0]
                    if hasattr(event, 'artifacts') and event.artifacts:
                        for artifact in event.artifacts:
                            for part in artifact.parts:
                                if hasattr(part.root, 'text'):
                                    response_text = part.root.text
                
                return response_text or "No response"
        except Exception as e:
            return f"Error: {e}"

a2a_client = A2AClient()

@tool
async def call_data_agent(query: str) -> str:
    """Call data analysis agent to get game statistics
    
    Args:
        query: Question about game data (win rates, pick rates, etc)
    """
    return await a2a_client.call_agent("data", query)

@tool
async def call_cs_agent(query: str) -> str:
    """Call CS agent to get player feedback
    
    Args:
        query: Question about player complaints or feedback
    """
    return await a2a_client.call_agent("cs", query)

agent = Agent(
    name="Game Balance Agent",
    description="게임 밸런스 조정을 위한 코디네이터 에이전트",
    model=BedrockModel(model_id="us.amazon.nova-lite-v1:0", temperature=0.3),
    tools=[call_data_agent, call_cs_agent],
    system_prompt="""당신은 게임 밸런스 조정 담당자입니다.

**응답 형식 (JSON):**
{
  "status": "completed" | "input_required" | "error",
  "message": "사용자에게 보여줄 메시지"
}

**도구 사용:**
- call_data_agent(query): 게임 데이터 분석 (승률, 픽률 등)
- call_cs_agent(query): 플레이어 피드백 조회

**상태 결정:**
- completed: 분석을 완료하고 결과를 제공한 경우
- input_required: 추가 정보가 필요한 경우
- error: 오류 발생 시

**중요: 모든 응답은 한글로 작성하세요.**"""
)

from game_balance_agent_executor import GameBalanceExecutor
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
            # Use invoke_async to get full response
            result = await agent.invoke_async(query)
            full_response = result.output if hasattr(result, 'output') else str(result)
            
            # Extract and send thinking
            thinking_matches = re.findall(r'<thinking>(.*?)</thinking>', full_response, re.DOTALL)
            for thinking in thinking_matches:
                yield f"data: {json.dumps({'type': 'thinking', 'content': thinking.strip()})}\n\n"
            
            # Send answer (remove thinking and response tags)
            clean_response = re.sub(r'<thinking>.*?</thinking>', '', full_response, flags=re.DOTALL)
            clean_response = re.sub(r'<response>|</response>', '', clean_response, flags=re.DOTALL).strip()
            
            if clean_response:
                yield f"data: {json.dumps({'type': 'answer', 'content': clean_response})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

def create_app():
    from a2a.types import AgentCard, AgentCapabilities, AgentSkill
    
    # Initialize A2A client
    import asyncio
    asyncio.run(a2a_client.init())
    
    agent_card = AgentCard(
        name="Game Balance Agent",
        description="게임 밸런스 조정 코디네이터",
        url="http://localhost:9001",
        version="1.0.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        skills=[
            AgentSkill(
                id="coordinate_balance",
                name="coordinate_balance",
                description="게임 밸런스 분석 및 조정",
                tags=[],
                input_description="밸런스 관련 질문",
                output_description="분석 결과 및 제안"
            )
        ],
        capabilities=AgentCapabilities(streaming=True, multi_turn=True)
    )
    
    request_handler = DefaultRequestHandler(
        agent_executor=GameBalanceExecutor(),
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
    print("⚖️ Starting Game Balance Agent on port 9001...")
    uvicorn.run(app, host="127.0.0.1", port=9001)
