#!/usr/bin/env python3
import asyncio
import httpx
from uuid import uuid4

async def test_game_balance():
    """Test Game Balance Agent with natural language request"""
    
    url = "http://localhost:9000/send_message"
    
    payload = {
        "message": {
            "role": "user",
            "parts": [
                {
                    "type": "text",
                    "text": "현재 게임 밸런스를 분석해줘. 승률 데이터와 고객 피드백을 모두 확인해서 종합적인 밸런스 리포트를 작성해줘."
                }
            ],
            "messageId": uuid4().hex
        }
    }
    
    print("📤 Sending request to Game Balance Agent...")
    print(f"   Query: {payload['message']['parts'][0]['text']}\n")
    
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Response received:\n")
            print("="*80)
            
            # Extract task result
            if "result" in result and "task" in result["result"]:
                task = result["result"]["task"]
                
                # Print artifacts
                if "artifacts" in task:
                    for artifact in task["artifacts"]:
                        for part in artifact["parts"]:
                            if part.get("type") == "text":
                                print(part["text"])
                                print("="*80)
            else:
                print(result)
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    asyncio.run(test_game_balance())
