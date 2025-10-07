#!/usr/bin/env python3
import asyncio
from agents.game_balance_agent import get_win_rates, get_player_feedback

async def main():
    print("Testing get_win_rates...")
    result = await get_win_rates()
    print(f"Result: {result}\n")
    
    print("Testing get_player_feedback...")
    result = await get_player_feedback()
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
