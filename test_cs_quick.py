#!/usr/bin/env python3
import asyncio
import httpx
from uuid import uuid4
from a2a.client import ClientFactory, ClientConfig
from a2a.types import AgentCard, Message, Role, Part, TextPart

async def test_cs_agent():
    from a2a.types import AgentCapabilities, AgentSkill
    
    agent_card = AgentCard(
        name="CS Feedback Agent",
        description="CS Agent",
        url="http://localhost:9002",
        version="1.0.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        skills=[AgentSkill(id="test", name="test", description="test", tags=[], input_description="", output_description="")],
        capabilities=AgentCapabilities(streaming=True, multi_turn=True)
    )
    
    async with httpx.AsyncClient(timeout=60) as client:
        config = ClientConfig(httpx_client=client, streaming=False)
        factory = ClientFactory(config)
        a2a_client = factory.create(agent_card)
        
        query = "테란 관련 피드백 보여줘"
        print(f"📤 Query: {query}\n")
        
        msg = Message(
            kind="message",
            role=Role.user,
            parts=[Part(TextPart(kind="text", text=query))],
            message_id=uuid4().hex
        )
        
        async for event in a2a_client.send_message(msg):
            if hasattr(event, 'artifacts') and event.artifacts:
                for artifact in event.artifacts:
                    if hasattr(artifact, 'parts'):
                        for part in artifact.parts:
                            if hasattr(part, 'text'):
                                print(f"📥 Response: {part.text}\n")

if __name__ == "__main__":
    asyncio.run(test_cs_agent())
