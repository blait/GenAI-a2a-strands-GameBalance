#!/usr/bin/env python3
"""Test Game Balance Agent's A2A coordination flow"""

import asyncio
import httpx
from uuid import uuid4
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import Message, Part, Role, TextPart

async def test_game_balance_coordination():
    print("=" * 80)
    print("🎮 Testing Game Balance Agent A2A Coordination Flow")
    print("=" * 80)
    
    agent_url = "http://localhost:9000"
    query = "Analyze current game balance"
    
    print(f"\n📍 Step 1: Connecting to Game Balance Agent")
    print(f"   URL: {agent_url}")
    
    try:
        async with httpx.AsyncClient(timeout=120) as httpx_client:
            print(f"\n📍 Step 2: Fetching Agent Card")
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=agent_url)
            agent_card = await resolver.get_agent_card()
            
            print(f"   ✅ Agent Name: {agent_card.name}")
            print(f"   ✅ Available Tools:")
            for skill in agent_card.skills:
                print(f"      - {skill.name}")
            
            print(f"\n📍 Step 3: Creating A2A Client")
            config = ClientConfig(httpx_client=httpx_client, streaming=True)
            factory = ClientFactory(config)
            client = factory.create(agent_card)
            print(f"   ✅ Client created")
            
            print(f"\n📍 Step 4: Sending User Query")
            print(f"   Query: '{query}'")
            
            msg = Message(
                kind="message",
                role=Role.user,
                parts=[Part(TextPart(kind="text", text=query))],
                message_id=uuid4().hex
            )
            
            print(f"\n📍 Step 5: Processing Response (Streaming)")
            print("-" * 80)
            
            event_count = 0
            tool_calls = []
            tool_results = []
            
            async for event in client.send_message(msg):
                event_count += 1
                
                # Parse history for tool calls and results
                if hasattr(event, 'history') and event.history:
                    for msg_item in event.history:
                        if hasattr(msg_item, 'parts') and msg_item.parts:
                            for part in msg_item.parts:
                                # Tool call detection
                                if hasattr(part, 'root'):
                                    root = part.root
                                    
                                    # Check for tool_call
                                    if hasattr(root, 'tool_call'):
                                        tc = root.tool_call
                                        tool_name = getattr(tc, 'name', 'unknown')
                                        tool_input = getattr(tc, 'input', {})
                                        tool_id = getattr(tc, 'id', 'unknown')
                                        
                                        # Avoid duplicates
                                        if tool_id not in [t['id'] for t in tool_calls]:
                                            tool_calls.append({
                                                'id': tool_id,
                                                'name': tool_name,
                                                'input': tool_input
                                            })
                                            print(f"\n   🔧 Tool Call #{len(tool_calls)}: {tool_name}")
                                            print(f"      ID: {tool_id}")
                                            if tool_input:
                                                print(f"      Input: {str(tool_input)[:150]}")
                                    
                                    # Check for tool_result
                                    if hasattr(root, 'tool_result'):
                                        tr = root.tool_result
                                        tool_call_id = getattr(tr, 'tool_call_id', 'unknown')
                                        content = getattr(tr, 'content', '')
                                        
                                        # Avoid duplicates
                                        if tool_call_id not in [t['call_id'] for t in tool_results]:
                                            tool_results.append({
                                                'call_id': tool_call_id,
                                                'content': content
                                            })
                                            print(f"\n   ✅ Tool Result for call {tool_call_id}")
                                            print(f"      Content: {str(content)[:200]}")
                
                # Check for final artifacts
                if hasattr(event, 'artifacts') and event.artifacts:
                    print(f"\n📍 Step 6: Final Response")
                    print("-" * 80)
                    for artifact in event.artifacts:
                        for part in artifact.parts:
                            if hasattr(part.root, 'text'):
                                print(part.root.text)
                    break
            
            print("\n" + "=" * 80)
            print("📊 A2A Protocol Summary")
            print("=" * 80)
            print(f"   Total streaming events: {event_count}")
            print(f"   Tool calls made: {len(tool_calls)}")
            for i, tc in enumerate(tool_calls, 1):
                print(f"      {i}. {tc['name']}")
            print(f"   Tool results received: {len(tool_results)}")
            print("=" * 80)
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("\n🚀 Starting Game Balance Agent Flow Test")
    print("   This test ONLY calls Game Balance Agent")
    print("   Game Balance Agent will coordinate with other agents internally\n")
    
    success = await test_game_balance_coordination()
    
    if success:
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed")

if __name__ == "__main__":
    asyncio.run(main())
