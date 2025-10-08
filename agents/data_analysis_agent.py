#!/usr/bin/env python3
from strands import Agent, tool
from strands.multiagent.a2a import A2AServer
from strands.models.bedrock import BedrockModel
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import uvicorn
import asyncio

GAME_DATA = [
    {"game_id": 1, "race": "Terran", "result": "win", "duration": 15},
    {"game_id": 2, "race": "Zerg", "result": "loss", "duration": 20},
    {"game_id": 3, "race": "Protoss", "result": "loss", "duration": 18},
    {"game_id": 4, "race": "Terran", "result": "win", "duration": 12},
    {"game_id": 5, "race": "Terran", "result": "win", "duration": 14},
    {"game_id": 6, "race": "Zerg", "result": "loss", "duration": 22},
    {"game_id": 7, "race": "Protoss", "result": "win", "duration": 25},
    {"game_id": 8, "race": "Terran", "result": "win", "duration": 11},
    {"game_id": 9, "race": "Terran", "result": "win", "duration": 13},
    {"game_id": 10, "race": "Zerg", "result": "loss", "duration": 19},
] * 3

@tool
def analyze_win_rates(race: str = None) -> str:
    """Analyze win rates by race
    
    Args:
        race: Filter by specific race (Terran, Zerg, Protoss)
    """
    df = pd.DataFrame(GAME_DATA)
    if race:
        df = df[df["race"] == race]
    
    stats = df.groupby("race").apply(
        lambda x: f"{x['race'].iloc[0]}: {(x['result'] == 'win').sum() / len(x) * 100:.2f}% ({(x['result'] == 'win').sum()}/{len(x)})"
    )
    return "\n".join(stats.values)

@tool
def analyze_game_duration(race: str = None) -> str:
    """Analyze average game duration
    
    Args:
        race: Filter by specific race
    """
    df = pd.DataFrame(GAME_DATA)
    if race:
        df = df[df["race"] == race]
    
    stats = df.groupby("race")["duration"].mean()
    return "\n".join([f"{r}: {d:.1f}분" for r, d in stats.items()])

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

agent = Agent(
    name="Data Analysis Agent",
    description="게임 통계와 승률을 분석하는 에이전트",
    model=BedrockModel(model_id="us.amazon.nova-lite-v1:0", temperature=0.3),
    tools=[analyze_win_rates, analyze_game_duration],
    system_prompt="""당신은 데이터 분석가입니다.

도구를 사용하여 게임 통계를 분석하세요:
- analyze_win_rates: 종족별 승률 분석
- analyze_game_duration: 평균 게임 시간 분석

질문을 받으면 적절한 도구를 선택하여 데이터를 조회하고 분석 결과를 제공하세요.

**중요: 모든 응답은 반드시 한글로 작성하세요.**"""
)

@app.post("/ask")
async def ask(request: QueryRequest):
    result = await asyncio.to_thread(lambda: agent(request.query))
    return {"query": request.query, "response": result}

@app.post("/ask_stream")
async def ask_stream(request: QueryRequest):
    """Streaming endpoint for real-time thinking"""
    from fastapi.responses import StreamingResponse
    import json
    import queue
    import threading
    import sys
    
    event_queue = queue.Queue()
    
    class StreamCapture:
        def __init__(self, queue, original):
            self.queue = queue
            self.original = original
            
        def write(self, text):
            self.original.write(text)
            self.original.flush()
            if text and text.strip():
                self.queue.put(('log', text))
                
        def flush(self):
            self.original.flush()
    
    def run_agent():
        try:
            old_stdout = sys.stdout
            sys.stdout = StreamCapture(event_queue, old_stdout)
            
            print(f"\n🎯 Query: {request.query}\n")
            
            result = agent(request.query)
            
            sys.stdout = old_stdout
            
            if hasattr(result, 'message') and hasattr(result.message, 'content'):
                content = result.message.content[0].text if result.message.content else ""
            else:
                content = str(result)
            
            event_queue.put(('answer', content))
            event_queue.put(('done', None))
        except Exception as e:
            event_queue.put(('error', str(e)))
    
    async def generate():
        thread = threading.Thread(target=run_agent, daemon=True)
        thread.start()
        
        while True:
            try:
                event_type, data = event_queue.get(timeout=0.1)
                
                if event_type == 'done':
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    break
                elif event_type == 'error':
                    yield f"data: {json.dumps({'type': 'error', 'content': data})}\n\n"
                    break
                elif event_type == 'log':
                    yield f"data: {json.dumps({'type': 'thinking', 'content': data})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': event_type, 'content': data})}\n\n"
            except queue.Empty:
                await asyncio.sleep(0.1)
        
        thread.join(timeout=1)
    
    return StreamingResponse(generate(), media_type="text/event-stream")

def main():
    print("📊 Starting Data Analysis Agent...")
    print("  - A2A Server on port 9003")
    print("  - HTTP API on port 9004")
    
    # Start A2A Server in background thread
    import threading
    a2a_server = A2AServer(agent=agent, port=9003)
    a2a_thread = threading.Thread(target=a2a_server.serve, daemon=True)
    a2a_thread.start()
    
    # Start FastAPI server
    uvicorn.run(app, host="127.0.0.1", port=9004)

if __name__ == "__main__":
    main()
