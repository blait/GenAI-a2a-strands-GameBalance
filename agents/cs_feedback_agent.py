#!/usr/bin/env python3
from strands import Agent, tool
from strands.multiagent.a2a import A2AServer
from strands.models.bedrock import BedrockModel

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

def main():
    print("📞 Starting CS Feedback Agent...")
    
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

**중요: 모든 응답은 반드시 한글로 작성하세요.**"""
    )
    
    print("✅ Ready on port 9001")
    server = A2AServer(agent=agent, port=9001)
    server.serve()

if __name__ == "__main__":
    main()
