#!/usr/bin/env python3
from strands import Agent, tool
from strands.multiagent.a2a import A2AServer
from strands.models.bedrock import BedrockModel
from a2a.server.tasks import InMemoryTaskStore  # Task Store 추가
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import asyncio

FEEDBACK_DATA = [
    {"race": "Terran", "complaint": "테란 마린 러시가 너무 강력합니다. 초반 방어가 불가능해요.", "upvotes": 245, "urgency": "high", "date": "2025-10-01"},
    {"race": "Zerg", "complaint": "저그 뮤탈이 너프되어서 이제 쓸모가 없습니다.", "upvotes": 312, "urgency": "high", "date": "2025-10-01"},
    {"race": "Protoss", "complaint": "프로토스 광전사 체력이 너무 약합니다.", "upvotes": 189, "urgency": "medium", "date": "2025-10-02"},
    {"race": "Terran", "complaint": "테란 벙커 건설 속도가 너무 빨라서 러시 방어가 쉽습니다.", "upvotes": 201, "urgency": "high", "date": "2025-10-03"},
    {"race": "Zerg", "complaint": "저그 히드라 사거리가 짧아서 쓸모가 없어요.", "upvotes": 156, "urgency": "medium", "date": "2025-10-03"},
    {"race": "Protoss", "complaint": "프로토스 스톰 데미지가 너무 강력합니다.", "upvotes": 267, "urgency": "high", "date": "2025-10-04"},
]

@tool
def get_feedback(urgency: str = None, race: str = None) -> str:
    """Get customer feedback from game forums
    
    Args:
        urgency: Filter by urgency level (high, medium, low)
        race: Filter by race (Terran, Zerg, Protoss)
    """
    filtered = FEEDBACK_DATA
    if urgency:
        filtered = [f for f in filtered if f["urgency"] == urgency]
    if race:
        filtered = [f for f in filtered if f["race"] == race]
    
    result = []
    for f in filtered:
        result.append(f"[{f['race']}] {f['complaint']} (추천: {f['upvotes']}, 날짜: {f['date']})")
    
    return "\n".join(result) if result else "No feedback found"

# Agent 생성
agent = Agent(
    name="CS Feedback Agent",
    description="게임 포럼에서 고객 피드백을 조회하는 에이전트",
    model=BedrockModel(model_id="us.amazon.nova-lite-v1:0", temperature=0.3),
    tools=[get_feedback],
    system_prompt="""당신은 고객 지원 담당자입니다. 

**도구 사용법:**
- get_feedback(): 모든 피드백 조회 (필터 없음)
- get_feedback(race="Terran"): 특정 종족 피드백만 조회
- get_feedback(urgency="high"): 긴급도별 피드백 조회
- get_feedback(race="Terran", urgency="high"): 복합 필터

**중요:**
1. 필터를 지정하지 않으면 모든 피드백이 반환됩니다
2. 도구를 한 번만 호출하세요 (반복 호출 금지)
3. 도구 결과를 그대로 사용자에게 전달하세요

**멀티턴 대화 지원:**
이 에이전트는 A2A Task를 통해 대화 히스토리를 자동으로 유지합니다.
이전 대화 내용을 참고하여 답변하세요.

**중요: 모든 응답은 반드시 한글로 작성하세요.**"""
)

# HTTP API (선택적 - 디버깅용)
app = FastAPI()

class QueryRequest(BaseModel):
    query: str

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
    print("📞 Starting CS Feedback Agent...")
    print("  - A2A Server on port 9001 (with Task Store)")
    print("  - HTTP API on port 9002")
    
    # Task Store 생성 (대화 히스토리 자동 관리)
    task_store = InMemoryTaskStore()
    
    # A2A Server 시작 (Task Store 포함)
    import threading
    a2a_server = A2AServer(
        agent=agent, 
        port=9001,
        task_store=task_store  # 👈 Task Store 활성화
    )
    a2a_thread = threading.Thread(target=a2a_server.serve, daemon=True)
    a2a_thread.start()
    
    print("  ✅ A2A Task Store enabled - Multi-turn conversations supported!")
    
    # Start FastAPI server
    uvicorn.run(app, host="127.0.0.1", port=9002)

if __name__ == "__main__":
    main()
