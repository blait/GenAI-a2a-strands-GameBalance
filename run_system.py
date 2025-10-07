#!/usr/bin/env python3
"""
System Runner - Starts all three agents in parallel
"""

import subprocess
import time
import signal
import sys
from pathlib import Path

AGENTS_DIR = Path(__file__).parent / "agents"

processes = []

def cleanup(signum=None, frame=None):
    """Clean up all processes"""
    print("\n🛑 Shutting down all agents...")
    for process in processes:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    print("✅ All agents stopped")
    sys.exit(0)

def main():
    print("🚀 Starting Game Balance A2A System")
    print("=" * 50)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    agents = [
        ("CS Feedback Agent", "cs_feedback_agent.py", 9001),
        ("Data Analysis Agent", "data_analysis_agent.py", 9002),
        ("Game Balance Agent", "game_balance_agent.py", 9000)
    ]
    
    # Start each agent
    for name, script, port in agents:
        print(f"\n🚀 Starting {name} (port {port})...")
        process = subprocess.Popen(
            [sys.executable, str(AGENTS_DIR / script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(process)
        print(f"   PID: {process.pid}")
        time.sleep(3)  # Wait for agent to start
    
    print("\n" + "=" * 50)
    print("✅ All agents started successfully!")
    print("\n📋 Agent URLs:")
    print("   - CS Feedback Agent: http://localhost:9001")
    print("   - Data Analysis Agent: http://localhost:9002")
    print("   - Game Balance Agent: http://localhost:9000")
    print("\n💡 Test with:")
    print('   curl -X POST http://localhost:9000/send_message \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"message": {"role": "user", "parts": [{"type": "text", "text": "Analyze game balance"}], "messageId": "test-1"}}\'')
    print("\nPress Ctrl+C to stop all agents")
    print("=" * 50)
    
    # Monitor processes
    try:
        while True:
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    print(f"\n❌ {agents[i][0]} has stopped unexpectedly!")
                    cleanup()
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
