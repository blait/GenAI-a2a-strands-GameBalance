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
    """Game Balance Coordinator using A2A protocol"""
    
    def __init__(self):
        self.known_agents = {
            "http://localhost:9001": None,
            "http://localhost:9002": None
        }
        self.agent_clients = {}
        self.httpx_client = None
        self.delegation_tools = []
        self.executor = ThreadPoolExecutor(max_workers=5)
    
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
    
    async def send_a2a_message(self, agent_name: str, agent_url: str, query: str) -> str:
        """Send message to agent via A2A protocol"""
        print(f"\n[GAME BALANCE] 📤 Sending A2A message to {agent_name}")
        print(f"[GAME BALANCE]    Query: {query[:100]}...")
        
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
                async for event in a2a_client.send_message(msg):
                    if isinstance(event, tuple) and len(event) > 0:
                        event = event[0]
                    
                    if hasattr(event, 'artifacts') and event.artifacts:
                        for artifact in event.artifacts:
                            for part in artifact.parts:
                                if hasattr(part.root, 'text'):
                                    response_text = part.root.text
                
                if response_text:
                    print(f"[GAME BALANCE]    ✅ Response from {agent_name} ({len(response_text)} chars)")
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
                
                def delegation_function(query: str) -> str:
                    # Run in separate thread with its own event loop
                    def run_async_in_thread():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            return loop.run_until_complete(
                                self.send_a2a_message(name, url, query)
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
    
Returns:
    Response from {name}
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
            description="Coordinates game balance analysis by gathering data from other agents",
            model=BedrockModel(model_id="us.amazon.nova-lite-v1:0", temperature=0.3),
            tools=self.delegation_tools,
            system_prompt="""You are a game balance coordinator for a StarCraft-like game.

When asked to analyze game balance:
1. First, call the Data Analysis Agent to get win rate statistics
2. Then, call the CS Feedback Agent to get player complaints
3. Carefully analyze both responses
4. Provide a comprehensive balance recommendation

Be specific and data-driven in your analysis. Always use the tools to gather information."""
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
        # Invoke agent (Strands uses __call__)
        result = await asyncio.to_thread(lambda: agent(request.query))
        return {"query": request.query, "response": result}
    
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
