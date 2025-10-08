#!/usr/bin/env python3
"""Test script for A2A agents"""

import asyncio
import httpx
from uuid import uuid4
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import Message, Part, Role, TextPart

async def test_agent(agent_url: str, agent_name: str, query: str):
    print(f"\n{'='*60}")
    print(f"Testing {agent_name}")
    print(f"URL: {agent_url}")
    print(f"Query: {query}")
    print('='*60)
    
    try:
        async with httpx.AsyncClient(timeout=60) as httpx_client:
            # Get agent card
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=agent_url)
            agent_card = await resolver.get_agent_card()
            print(f"✅ Connected to {agent_name}")
            print(f"   Skills: {[s.name for s in agent_card.skills]}")
            
            # Create client
            config = ClientConfig(httpx_client=httpx_client, streaming=False)
            factory = ClientFactory(config)
            client = factory.create(agent_card)
            
            # Create message
            msg = Message(
                kind="message",
                role=Role.user,
                parts=[Part(TextPart(kind="text", text=query))],
                message_id=uuid4().hex
            )
            
            # Send message
            print(f"📤 Sending message...")
            try:
                async for event in client.send_message(msg):
                    print(f"📥 Response:")
                    if hasattr(event, 'artifacts') and event.artifacts:
                        for artifact in event.artifacts:
                            for part in artifact.parts:
                                if hasattr(part.root, 'text'):
                                    print(part.root.text)
                    else:
                        event_str = str(event)
                        print(event_str[:500] + "..." if len(event_str) > 500 else event_str)
                    break
            except Exception as e:
                print(f"❌ Message Error: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🚀 Starting A2A Agent Tests")
    
    # Test CS Feedback Agent
    await test_agent(
        "http://localhost:9001",
        "CS Feedback Agent",
        "Show high urgency feedback"
    )
    
    # Test Data Analysis Agent
    await test_agent(
        "http://localhost:9002",
        "Data Analysis Agent",
        "What is the win rate for each race?"
    )
    
    # Test Game Balance Agent
    await test_agent(
        "http://localhost:9000",
        "Game Balance Agent",
        "Analyze current game balance"
    )
    
    print("\n" + "="*60)
    print("✅ All tests completed")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
