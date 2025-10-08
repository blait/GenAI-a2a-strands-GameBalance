#!/bin/bash

# Run all Streamlit GUIs for the game balance system

cd "$(dirname "$0")"

echo "🚀 Starting Streamlit GUIs..."
echo ""

# Balance Agent GUI (port 8501)
echo "Starting Balance Agent GUI on http://localhost:8501"
venv/bin/streamlit run gui/balance_gui.py --server.port 8501 > /tmp/balance_gui.log 2>&1 &

# Data Analysis Agent GUI (port 8503)
echo "Starting Data Analysis Agent GUI on http://localhost:8503"
venv/bin/streamlit run gui/analysis_gui.py --server.port 8503 > /tmp/analysis_gui.log 2>&1 &

# CS Feedback Agent GUI (port 8502)
echo "Starting CS Feedback Agent GUI on http://localhost:8502"
venv/bin/streamlit run gui/cs_gui.py --server.port 8502 > /tmp/cs_gui.log 2>&1 &

sleep 3

echo ""
echo "✅ All GUIs started!"
echo ""
echo "📱 Access the GUIs:"
echo "  - Balance Agent:       http://localhost:8501"
echo "  - CS Feedback Agent:   http://localhost:8502"
echo "  - Data Analysis Agent: http://localhost:8503"
echo ""
echo "📋 Logs:"
echo "  - Balance GUI:   tail -f /tmp/balance_gui.log"
echo "  - CS GUI:        tail -f /tmp/cs_gui.log"
echo "  - Analysis GUI:  tail -f /tmp/analysis_gui.log"
echo ""
echo "🛑 To stop all GUIs: pkill -f streamlit"
