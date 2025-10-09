#!/usr/bin/env python3
"""Debug multi-turn conversation - check event structure"""

import asyncio
import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import Message, Part, TextPart, Role
from uuid import uuid4
import json

async def test_multiturn_debug():
    """Test multi-turn with debug output"""
    
    agent_url = "http://localhost:9003"
    
    async with httpx.AsyncClient(timeout=60) as client:
        # Get AgentCard
        print("📥 Fetching AgentCard...")
        resolver = A2ACardResolver(httpx_client=client, base_url=agent_url)
        agent_card = await resolver.get_agent_card()
        print(f"✅ Connected to: {agent_card.name}\n")
        
        # Create A2A client
        config = ClientConfig(httpx_client=client, streaming=False)
        factory = ClientFactory(config)
        a2a_client = factory.create(agent_card)
        
        # First message
        print("="*80)
        print("🆕 First message")
        print("="*80)
        msg1 = Message(
            kind="message",
            role=Role.user,
            parts=[Part(TextPart(kind="text", text="모든 종족 승률 알려줘"))],
            message_id=uuid4().hex
        )
        
        task_id = None
        async for event in a2a_client.send_message(msg1):
            print(f"\n🔍 Event type: {type(event)}")
            print(f"🔍 Event: {event}")
            
            if isinstance(event, tuple):
                print(f"   Tuple length: {len(event)}")
                event = event[0]
                print(f"   First element: {event}")
            
            # Check all attributes
            print(f"   Attributes: {dir(event)}")
            
            # Try to find task_id
            if hasattr(event, 'task'):
                print(f"   ✅ Has 'task' attribute: {event.task}")
                if event.task:
                    task_id = event.task.id
                    print(f"   📝 Task ID: {task_id}")
            
            if hasattr(event, 'id'):
                task_id = event.id
                print(f"   Has 'id' attribute: {task_id}")
            
            # Extract response
            if hasattr(event, 'artifacts') and event.artifacts:
                for artifact in event.artifacts:
                    for part in artifact.parts:
                        if hasattr(part.root, 'text'):
                            print(f"\n응답:\n{part.root.text}\n")
        
        print(f"\n📝 Final task_id: {task_id}")

if __name__ == "__main__":
    asyncio.run(test_multiturn_debug())
