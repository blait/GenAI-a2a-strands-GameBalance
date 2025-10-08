#!/bin/bash
# Quick restart script for all agents and GUIs

echo "🛑 Stopping all services..."
pkill -f "game_balance_agent|data_analysis_agent|cs_feedback_agent|streamlit"
sleep 2

echo "🚀 Starting agents..."
cd "/Users/hyeonsup/aws goa 2025/msk-a2a-demo/game-balance-a2a"

# Start agents
venv/bin/python -u agents/cs_feedback_agent.py > /tmp/cs_agent.log 2>&1 &
venv/bin/python -u agents/data_analysis_agent.py > /tmp/data_agent.log 2>&1 &
sleep 3
venv/bin/python -u agents/game_balance_agent.py > /tmp/balance_agent.log 2>&1 &

echo "⏳ Waiting for agents to start..."
sleep 5

echo "🎨 Starting GUIs..."
venv/bin/streamlit run gui/balance_gui.py --server.port 8501 > /tmp/balance_gui.log 2>&1 &
venv/bin/streamlit run gui/cs_gui.py --server.port 8502 > /tmp/cs_gui.log 2>&1 &
venv/bin/streamlit run gui/analysis_gui.py --server.port 8503 > /tmp/analysis_gui.log 2>&1 &

echo "⏳ Waiting for GUIs to start..."
sleep 5

echo ""
echo "✅ All services started!"
echo ""
echo "📊 Agents:"
lsof -i :8000,9001,9003 | grep LISTEN | awk '{print "  - Port " $9}'
echo ""
echo "🎨 GUIs:"
echo "  - Balance GUI: http://localhost:8501"
echo "  - CS GUI: http://localhost:8502"
echo "  - Analysis GUI: http://localhost:8503"
echo ""
echo "📝 Logs:"
echo "  - tail -f /tmp/balance_agent.log"
echo "  - tail -f /tmp/cs_agent.log"
echo "  - tail -f /tmp/data_agent.log"
