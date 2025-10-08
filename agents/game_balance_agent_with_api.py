#!/usr/bin/env python3
"""Game Balance Agent with simple HTTP API for users"""
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from agents.game_balance_agent import GameBalanceCoordinator

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

coordinator = None

@app.post("/ask")
async def ask_agent(request: QueryRequest):
    """Simple endpoint for users to ask questions"""
    # Use the agent's LLM directly
    # This is a simplified version - in production you'd use the full agent
    return {
        "query": request.query,
        "response": "Agent processing... (implement agent call here)"
    }

if __name__ == "__main__":
    # Start on port 8000 for user API
    uvicorn.run(app, host="0.0.0.0", port=8000)
