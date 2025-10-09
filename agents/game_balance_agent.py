#!/usr/bin/env python3
import asyncio
import httpx
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from strands import Agent, tool
from strands.multiagent.a2a import A2AServer
from strands.models.bedrock import BedrockModel
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import Message, Part, TextPart, Role

class GameBalanceCoordinator:
    """Game Balance Coordinator using A2A protocol with Task-based sessions"""
    
    def __init__(self):
        self.known_agents = {
            "http://localhost:9001": None,  # CS Agent A2A
            "http://localhost:9003": None   # Data Agent A2A
        }
        self.agent_clients = {}
        self.httpx_client = None
        self.delegation_tools = []
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.active_tasks = {}  # agent_name → task_id (for multi-turn conversations)
    
    async def discover_agents(self):
        """Discover agents by fetching their agent cards"""
        print("\n" + "="*80)
        print("🔍 Discovering Available Agents")
        print("="*80)
        
        self.httpx_client = httpx.AsyncClient(timeout=60)
        
        for agent_url in self.known_agents.keys():
            print(f"\n📥 Fetching agent card from {agent_url}")
            try:
                resolver = A2ACardResolver(httpx_client=self.httpx_client, base_url=agent_url)
                agent_card = await resolver.get_agent_card()
                self.known_agents[agent_url] = agent_card
                
                print(f"   ✅ Agent: {agent_card.name}")
                print(f"   ✅ Description: {agent_card.description}")
                if agent_card.skills:
                    print(f"   ✅ Skills: {[s.name for s in agent_card.skills]}")
            except Exception as e:
                print(f"   ❌ Failed to fetch agent card: {e}")
        
        print("\n" + "="*80)
    
    async def send_a2a_message(self, agent_name: str, agent_url: str, query: str, continue_task: bool = False) -> str:
        """Send message to agent via A2A protocol with Task-based session support
        
        Args:
            agent_name: Name of the target agent
            agent_url: URL of the target agent
            query: Query to send
            continue_task: If True, continue previous Task conversation
        """
        print(f"\n[GAME BALANCE] 📤 Sending A2A message to {agent_name}")
        print(f"[GAME BALANCE]    Query: {query[:100]}...")
        
        # Get existing task_id if continuing conversation
        task_id = None
        if continue_task and agent_name in self.active_tasks:
            task_id = self.active_tasks[agent_name]
            print(f"[GAME BALANCE]    📝 Continuing Task: {task_id}")
        else:
            print(f"[GAME BALANCE]    🆕 Creating new Task")
        
        try:
            # Create new httpx client for this request (thread-safe)
            async with httpx.AsyncClient(timeout=60) as client:
                agent_card = self.known_agents[agent_url]
                config = ClientConfig(httpx_client=client, streaming=False)
                factory = ClientFactory(config)
                a2a_client = factory.create(agent_card)
                
                msg = Message(
                    kind="message",
                    role=Role.user,
                    parts=[Part(TextPart(kind="text", text=query))],
                    message_id=uuid4().hex
                )
                
                response_text = None
                returned_task_id = None
                
                # Send message with optional task_id
                async for event in a2a_client.send_message(msg, task_id=task_id):
                    if isinstance(event, tuple) and len(event) > 0:
                        event = event[0]
                    
                    # Extract task_id from response
                    if hasattr(event, 'task') and event.task:
                        returned_task_id = event.task.id
                        if returned_task_id:
                            self.active_tasks[agent_name] = returned_task_id
                            print(f"[GAME BALANCE]    💾 Saved Task ID: {returned_task_id}")
                    
                    if hasattr(event, 'artifacts') and event.artifacts:
                        for artifact in event.artifacts:
                            for part in artifact.parts:
                                if hasattr(part.root, 'text'):
                                    response_text = part.root.text
                
                if response_text:
                    print(f"[GAME BALANCE]    ✅ Response from {agent_name}:")
                    print(f"[GAME BALANCE]    {response_text}")
                    return response_text
                else:
                    return "No response received"
        
        except Exception as e:
            print(f"[GAME BALANCE]    ❌ Error: {e}")
            return f"Error communicating with {agent_name}: {e}"
    
    def create_delegation_tools(self):
        """Create delegation tools after agents are discovered"""
        print("\n🔧 Creating Delegation Tools")
        print("="*80)
        
        tools = []
        
        for agent_url, agent_card in self.known_agents.items():
            if agent_card is None:
                continue
            
            agent_name = agent_card.name
            description = agent_card.description
            
            # Create tool with proper closure
            def make_tool(name, url, desc):
                tool_name = f"call_{name.lower().replace(' ', '_').replace('-', '_')}"
                
                def delegation_function(query: str, continue_conversation: bool = False) -> str:
                    """Call agent with optional conversation continuation
                    
                    Args:
                        query: The question or task to send to the agent
                        continue_conversation: If True, continue previous conversation with this agent.
                                             Use this for follow-up questions to maintain context.
                    
                    Returns:
                        Response from the agent
                    
                    Example:
                        # First call - new conversation
                        result1 = call_agent("What is the win rate?")
                        
                        # Follow-up - continue conversation
                        result2 = call_agent("Show me details for Terran", continue_conversation=True)
                    """
                    # Run in separate thread with its own event loop
                    def run_async_in_thread():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            return loop.run_until_complete(
                                self.send_a2a_message(name, url, query, continue_task=continue_conversation)
                            )
                        finally:
                            loop.close()
                    
                    future = self.executor.submit(run_async_in_thread)
                    return future.result(timeout=60)
                
                # Set metadata BEFORE @tool decorator
                delegation_function.__name__ = tool_name
                delegation_function.__doc__ = f"""Send query to {name}: {desc}
                
Args:
    query: The question or task to send to the agent
    continue_conversation: If True, continue previous conversation (maintains context)
    
Returns:
    Response from {name}
    
Example:
    # New conversation
    {tool_name}("What is the win rate?")
    
    # Continue conversation
    {tool_name}("Show details for Terran", continue_conversation=True)
"""
                return tool(delegation_function)
            
            tool_func = make_tool(agent_name, agent_url, description)
            tools.append(tool_func)
            print(f"   ✅ Created tool: {tool_func.__name__}")
        
        print("="*80)
        return tools
    
    def create_agent(self):
        """Create the Game Balance Agent with delegation tools"""
        if not self.delegation_tools:
            print("   ⚠️  Warning: No delegation tools available!")
        
        agent = Agent(
            name="Game Balance Agent",
            description="게임 밸런스 분석을 조율하는 코디네이터 에이전트",
            model=BedrockModel(model_id="us.amazon.nova-lite-v1:0", temperature=0.3),
            tools=self.delegation_tools,
            system_prompt="""당신은 스타크래프트 스타일 게임의 밸런스 조율 담당자입니다.

게임 밸런스 분석 요청을 받으면:
1. 먼저 Data Analysis Agent를 호출하여 승률 통계를 가져옵니다
2. 그 다음 CS Feedback Agent를 호출하여 플레이어 컴플레인을 가져옵니다
3. 두 응답을 신중하게 분석합니다
4. 종합적인 밸런스 권장사항을 제공합니다

**멀티턴 대화 (중요!):**
- 같은 에이전트에게 연속 질문할 때는 `continue_conversation=True`를 사용하세요
- 예시:
  * 첫 질문: call_data_analysis_agent("승률 알려줘")
  * 추가 질문: call_data_analysis_agent("테란 상세 데이터 줘", continue_conversation=True)
- continue_conversation=True를 사용하면 이전 대화 내용을 기억합니다
- 새로운 주제로 바꿀 때는 continue_conversation=False (기본값)

구체적이고 데이터 기반의 분석을 제공하세요. 항상 도구를 사용하여 정보를 수집하세요.

**중요: 모든 응답은 반드시 한글로 작성하세요.**"""
        )
        
        return agent

def main():
    """Entry point"""
    print("⚖️  Starting Game Balance Agent...")
    print("="*80)
    
    # Create coordinator
    coordinator = GameBalanceCoordinator()
    
    # Discover agents (run in new event loop)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(coordinator.discover_agents())
    
    # Create delegation tools (after discovery completes)
    coordinator.delegation_tools = coordinator.create_delegation_tools()
    
    # Create agent
    agent = coordinator.create_agent()
    
    print("\n✅ Game Balance Agent ready")
    print("   A2A Server: http://localhost:9000 (for other agents)")
    print("   REST API: http://localhost:8000/ask (for users)")
    print("   Waiting for requests...\n")
    
    # Start both servers
    from fastapi import FastAPI
    from pydantic import BaseModel
    import uvicorn
    from threading import Thread
    
    # User-facing REST API
    app = FastAPI()
    
    class QueryRequest(BaseModel):
        query: str
    
    @app.post("/ask")
    async def ask(request: QueryRequest):
        """User endpoint - simple REST API"""
        import time
        request_timestamp = time.time()
        
        # Invoke agent (Strands uses __call__)
        result = await asyncio.to_thread(lambda: agent(request.query))
        
        return {
            "query": request.query, 
            "response": result,
            "request_timestamp": request_timestamp
        }
    
    @app.post("/ask_stream")
    async def ask_stream(request: QueryRequest):
        """Streaming endpoint for real-time thinking"""
        from fastapi.responses import StreamingResponse
        import json
        import queue
        import threading
        import sys
        
        event_queue = queue.Queue()
        
        class StreamCapture:
            def __init__(self, queue, original):
                self.queue = queue
                self.original = original
                
            def write(self, text):
                self.original.write(text)
                self.original.flush()
                if text and text.strip():
                    self.queue.put(('log', text))
                    
            def flush(self):
                self.original.flush()
        
        def run_agent():
            try:
                old_stdout = sys.stdout
                sys.stdout = StreamCapture(event_queue, old_stdout)
                
                print(f"\n🎯 Query: {request.query}\n")
                
                result = agent(request.query)
                
                sys.stdout = old_stdout
                
                # Parse result
                if hasattr(result, 'message') and hasattr(result.message, 'content'):
                    content = result.message.content[0].text if result.message.content else ""
                else:
                    content = str(result)
                
                event_queue.put(('answer', content))
                event_queue.put(('done', None))
            except Exception as e:
                event_queue.put(('error', str(e)))
        
        async def generate():
            thread = threading.Thread(target=run_agent, daemon=True)
            thread.start()
            
            while True:
                try:
                    event_type, data = event_queue.get(timeout=0.1)
                    
                    if event_type == 'done':
                        yield f"data: {json.dumps({'type': 'done'})}\n\n"
                        break
                    elif event_type == 'error':
                        yield f"data: {json.dumps({'type': 'error', 'content': data})}\n\n"
                        break
                    elif event_type == 'log':
                        yield f"data: {json.dumps({'type': 'thinking', 'content': data})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': event_type, 'content': data})}\n\n"
                except queue.Empty:
                    await asyncio.sleep(0.1)
            
            thread.join(timeout=1)
        
        return StreamingResponse(generate(), media_type="text/event-stream")
    
    # Start REST API in separate thread
    def run_rest_api():
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    
    rest_thread = Thread(target=run_rest_api, daemon=True)
    rest_thread.start()
    
    # Start A2A server (blocks)
    server = A2AServer(agent=agent, port=9000)
    server.serve()

if __name__ == "__main__":
    main()
