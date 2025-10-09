#!/usr/bin/env python3
"""Test multi-turn conversation"""

import asyncio
import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import Message, Part, TextPart, Role
from uuid import uuid4

async def test_multiturn():
    agent_url = "http://localhost:9003"
    
    async with httpx.AsyncClient(timeout=60) as client:
        resolver = A2ACardResolver(httpx_client=client, base_url=agent_url)
        agent_card = await resolver.get_agent_card()
        
        config = ClientConfig(httpx_client=client, streaming=False)
        factory = ClientFactory(config)
        a2a_client = factory.create(agent_card)
        
        # First message
        print("="*80)
        print("🆕 첫 번째 메시지: 테란 승률 알려줘")
        print("="*80)
        msg1 = Message(
            kind="message",
            role=Role.user,
            parts=[Part(TextPart(kind="text", text="테란 승률 알려줘"))],
            message_id=uuid4().hex
        )
        
        task_id = None
        async for event in a2a_client.send_message(msg1):
            if isinstance(event, tuple):
                event = event[0]
            if hasattr(event, 'id'):
                task_id = event.id
            if hasattr(event, 'artifacts') and event.artifacts:
                for artifact in event.artifacts:
                    for part in artifact.parts:
                        if hasattr(part.root, 'text'):
                            print(f"\n응답: {part.root.text}\n")
        
        print(f"📝 Task ID: {task_id}\n")
        
        # Second message - new task with context
        print("="*80)
        print("🔄 두 번째 메시지: 저그는?")
        print("="*80)
        msg2 = Message(
            kind="message",
            role=Role.user,
            parts=[Part(TextPart(kind="text", text="저그는?"))],
            message_id=uuid4().hex
        )
        
        async for event in a2a_client.send_message(msg2):
            if isinstance(event, tuple):
                event = event[0]
            if hasattr(event, 'artifacts') and event.artifacts:
                for artifact in event.artifacts:
                    for part in artifact.parts:
                        if hasattr(part.root, 'text'):
                            print(f"\n응답: {part.root.text}\n")

if __name__ == "__main__":
    asyncio.run(test_multiturn())
