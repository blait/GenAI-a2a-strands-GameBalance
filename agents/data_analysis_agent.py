#!/usr/bin/env python3
from strands import Agent, tool
from strands.multiagent.a2a import A2AServer
from strands.models.bedrock import BedrockModel
import pandas as pd

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

def main():
    print("📊 Starting Data Analysis Agent...")
    
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
    
    print("✅ Ready on port 9002")
    server = A2AServer(agent=agent, port=9002)
    server.serve()

if __name__ == "__main__":
    main()
