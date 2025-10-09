#!/usr/bin/env python3
import asyncio
import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import Message, Part, TextPart, Role
from uuid import uuid4

async def test():
    async with httpx.AsyncClient(timeout=60) as client:
        resolver = A2ACardResolver(httpx_client=client, base_url='http://localhost:9003')
        agent_card = await resolver.get_agent_card()
        config = ClientConfig(httpx_client=client, streaming=False)
        factory = ClientFactory(config)
        a2a_client = factory.create(agent_card)
        
        # 명확하게 대화가 계속될 것을 암시하는 질문
        print("="*80)
        print("🆕 첫 번째 질문: 각 종족의 승률을 하나씩 알려줘. 먼저 테란부터")
        print("="*80)
        msg1 = Message(
            kind='message',
            role=Role.user,
            parts=[Part(TextPart(kind='text', text='각 종족의 승률을 하나씩 알려줘. 먼저 테란부터'))],
            message_id=uuid4().hex
        )
        
        task_id = None
        async for event in a2a_client.send_message(msg1):
            if isinstance(event, tuple):
                task = event[0]
                task_id = task.id
                print(f"\n📝 Task ID: {task_id}")
                print(f"📊 Task Status: {task.status.state}")
                if hasattr(task, 'artifacts') and task.artifacts:
                    for artifact in task.artifacts:
                        for part in artifact.parts:
                            if hasattr(part.root, 'text'):
                                print(f"\n응답:\n{part.root.text}\n")
        
        # 두 번째 메시지
        print("="*80)
        print("🔄 두 번째 질문 (같은 Task ID): 다음은 저그")
        print("="*80)
        msg2 = Message(
            kind='message',
            role=Role.user,
            parts=[Part(TextPart(kind='text', text='다음은 저그'))],
            message_id=uuid4().hex,
            task_id=task_id
        )
        
        try:
            async for event in a2a_client.send_message(msg2):
                if isinstance(event, tuple):
                    task = event[0]
                    print(f"\n📊 Task Status: {task.status.state}")
                    if hasattr(task, 'artifacts') and task.artifacts:
                        for artifact in task.artifacts:
                            for part in artifact.parts:
                                if hasattr(part.root, 'text'):
                                    print(f"\n응답:\n{part.root.text}\n")
        except Exception as e:
            print(f"\n❌ 에러: {e}")

asyncio.run(test())
