#!/usr/bin/env python3
from strands import Agent
from strands.multiagent.a2a import A2AServer
from strands.models.bedrock import BedrockModel
from strands_tools.a2a_client import A2AClientToolProvider

# Initialize A2A client tools for CS and Data Analysis agents
provider = A2AClientToolProvider(known_agent_urls=[
    "http://localhost:9001",  # CS Feedback Agent
    "http://localhost:9002"   # Data Analysis Agent
])

def main():
    print("⚖️  Starting Game Balance Agent...")
    
    agent = Agent(
        name="Game Balance Agent",
        description="Coordinates game balance analysis by gathering data from other agents",
        model=BedrockModel(model_id="us.amazon.nova-lite-v1:0", temperature=0.3),
        tools=provider.tools,
        system_prompt="""You are a game balance coordinator. You MUST use the available tools to gather real data.

IMPORTANT: Always call the tools to get actual data. Do NOT provide generic answers.

When asked to analyze game balance:
1. Call get_win_rates tool to get actual win rate statistics
2. Call get_player_feedback tool to get actual player complaints
3. Combine the data to provide specific recommendations

Never skip calling the tools. Always use real data from the tools."""
    )
    
    print("✅ Ready on port 9000")
    server = A2AServer(agent=agent, port=9000)
    server.serve()

if __name__ == "__main__":
    main()
