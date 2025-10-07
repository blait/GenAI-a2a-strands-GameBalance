#!/usr/bin/env python3
"""
Streamlit GUI for Data Analysis Agent
Port: 8503
"""

import streamlit as st
import httpx
from uuid import uuid4

# Agent URL
AGENT_URL = "http://localhost:9002"

st.set_page_config(
    page_title="Data Analysis Agent",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Data Analysis Agent")
st.caption("Game data analysis and win rate statistics")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about game statistics..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Send to agent
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # Create A2A message
            payload = {
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": prompt}],
                    "messageId": uuid4().hex
                }
            }
            
            # Send request
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{AGENT_URL}/send_message",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract response text
                    if "result" in result:
                        task_result = result["result"]
                        
                        if isinstance(task_result, dict):
                            if "status" in task_result and "message" in task_result["status"]:
                                status_msg = task_result["status"]["message"]
                                if isinstance(status_msg, dict) and "parts" in status_msg:
                                    response_text = ""
                                    for part in status_msg["parts"]:
                                        if "text" in part:
                                            response_text += part["text"]
                                else:
                                    response_text = str(status_msg)
                            elif "artifacts" in task_result:
                                response_text = ""
                                for artifact in task_result["artifacts"]:
                                    if "text" in artifact:
                                        response_text += artifact["text"]
                            else:
                                response_text = str(task_result)
                        else:
                            response_text = str(task_result)
                    else:
                        response_text = str(result)
                    
                    message_placeholder.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                else:
                    error_msg = f"Error: {response.status_code} - {response.text}"
                    message_placeholder.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Sidebar
with st.sidebar:
    st.header("Agent Info")
    st.info(f"**URL**: {AGENT_URL}")
    st.info("**Port**: 9002")
    
    st.header("Quick Actions")
    if st.button("Get Win Rates"):
        st.session_state.messages.append({"role": "user", "content": "What is the win rate for each race?"})
        st.rerun()
    
    if st.button("Detect Balance Issues"):
        st.session_state.messages.append({"role": "user", "content": "Detect balance issues"})
        st.rerun()
    
    if st.button("Terran vs Zerg Stats"):
        st.session_state.messages.append({"role": "user", "content": "Show Terran vs Zerg matchup statistics"})
        st.rerun()
    
    if st.button("Game Duration Stats"):
        st.session_state.messages.append({"role": "user", "content": "What is the average game duration?"})
        st.rerun()
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()
