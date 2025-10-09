#!/usr/bin/env python3
"""Test multi-turn conversation with A2A Task support"""

import asyncio
import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import Message, Part, TextPart, Role
from uuid import uuid4

async def test_multiturn():
    """Test multi-turn conversation with Data Analysis Agent"""
    
    agent_url = "http://localhost:9003"
    
    async with httpx.AsyncClient(timeout=60) as client:
        # 1. Get AgentCard
        print("📥 Fetching AgentCard...")
        resolver = A2ACardResolver(httpx_client=client, base_url=agent_url)
        agent_card = await resolver.get_agent_card()
        print(f"✅ Connected to: {agent_card.name}\n")
        
        # 2. Create A2A client
        config = ClientConfig(httpx_client=client, streaming=False)
        factory = ClientFactory(config)
        a2a_client = factory.create(agent_card)
        
        # 3. First message (new Task)
        print("="*80)
        print("🆕 First message (new Task)")
        print("="*80)
        msg1 = Message(
            kind="message",
            role=Role.user,
            parts=[Part(TextPart(kind="text", text="승률 알려줘"))],
            message_id=uuid4().hex
        )
        
        task_id = None
        async for event in a2a_client.send_message(msg1):
            if isinstance(event, tuple):
                event = event[0]
            
            # Extract task_id
            if hasattr(event, 'task') and event.task:
                task_id = event.task.id
                print(f"📝 Task ID: {task_id}")
            
            # Extract response
            if hasattr(event, 'artifacts') and event.artifacts:
                for artifact in event.artifacts:
                    for part in artifact.parts:
                        if hasattr(part.root, 'text'):
                            print(f"\n응답:\n{part.root.text}\n")
        
        if not task_id:
            print("❌ No task_id received!")
            return
        
        # 4. Second message (continue Task)
        print("="*80)
        print(f"📝 Second message (continue Task: {task_id})")
        print("="*80)
        msg2 = Message(
            kind="message",
            role=Role.user,
            parts=[Part(TextPart(kind="text", text="테란 상세 데이터 줘"))],
            message_id=uuid4().hex
        )
        
        async for event in a2a_client.send_message(msg2, task_id=task_id):
            if isinstance(event, tuple):
                event = event[0]
            
            if hasattr(event, 'artifacts') and event.artifacts:
                for artifact in event.artifacts:
                    for part in artifact.parts:
                        if hasattr(part.root, 'text'):
                            print(f"\n응답:\n{part.root.text}\n")
        
        # 5. Third message (continue Task)
        print("="*80)
        print(f"📝 Third message (continue Task: {task_id})")
        print("="*80)
        msg3 = Message(
            kind="message",
            role=Role.user,
            parts=[Part(TextPart(kind="text", text="아까 말한 테란 승률이 몇 퍼센트였지?"))],
            message_id=uuid4().hex
        )
        
        async for event in a2a_client.send_message(msg3, task_id=task_id):
            if isinstance(event, tuple):
                event = event[0]
            
            if hasattr(event, 'artifacts') and event.artifacts:
                for artifact in event.artifacts:
                    for part in artifact.parts:
                        if hasattr(part.root, 'text'):
                            print(f"\n응답:\n{part.root.text}\n")
        
        print("="*80)
        print("✅ Multi-turn test completed!")
        print("="*80)

if __name__ == "__main__":
    asyncio.run(test_multiturn())
