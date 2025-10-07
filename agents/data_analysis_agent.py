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
        description="Analyzes game statistics and win rates",
        model=BedrockModel(model_id="us.amazon.nova-lite-v1:0", temperature=0.3),
        tools=[analyze_win_rates, analyze_game_duration],
        system_prompt="You are a data analyst. Use tools to analyze game statistics."
    )
    
    print("✅ Ready on port 9002")
    server = A2AServer(agent=agent, port=9002)
    server.serve()

if __name__ == "__main__":
    main()
