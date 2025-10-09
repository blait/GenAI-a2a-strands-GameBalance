#!/usr/bin/env python3
"""
Streamlit GUI for CS Feedback Agent
Port: 8502
"""

import streamlit as st
import requests

# Agent URL
AGENT_URL = "http://localhost:9002"

st.set_page_config(
    page_title="CS 피드백 에이전트",
    page_icon="💬",
    layout="wide"
)

st.title("💬 CS 피드백 에이전트")
st.caption("플레이어 피드백 및 컴플레인 조회")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and "thinking" in message:
            with st.expander("🧠 사고 과정 보기"):
                st.code(message["thinking"], language=None)
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("질문을 입력하세요 (예: 테란 피드백 보여줘)"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Send to agent with streaming
    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        answer_placeholder = st.empty()
        
        thinking_text = ""
        answer_text = ""
        
        # Show loading indicator
        answer_placeholder.markdown("⏳ 응답 대기 중...")
        
        try:
            import json
            response = requests.post(
                f"{AGENT_URL}/ask_stream",
                json={"query": prompt},
                stream=True,
                timeout=120
            )
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        
                        if data['type'] == 'thinking':
                            thinking_text += data['content']
                            with thinking_placeholder.expander("🧠 사고 과정 (실시간)", expanded=True):
                                st.code(thinking_text)
                        elif data['type'] == 'answer':
                            answer_text += data['content']
                            answer_placeholder.markdown(answer_text)
                        elif data['type'] == 'done':
                            break
            
            # Parse JSON response
            try:
                import re
                clean_text = re.sub(r'<thinking>.*?</thinking>', '', answer_text, flags=re.DOTALL).strip()
                json_match = re.search(r'\{[^}]*"status"[^}]*"message"[^}]*\}', clean_text, re.DOTALL)
                if json_match:
                    response_json = json.loads(json_match.group())
                    status = response_json.get('status', 'completed')
                    message = response_json.get('message', '')
                    
                    # Status icon
                    status_icon = {'input_required': '❓', 'completed': '✅', 'error': '❌'}.get(status, '📝')
                    # Format: Status: [icon] [status]\nMessage: [icon] [message]
                    final_message = f"**Status:** {status_icon} {status}\n\n**Message:** 💬 {message}"
                else:
                    final_message = clean_text
            except:
                final_message = answer_text
            
            answer_placeholder.markdown(final_message)
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": final_message,
                "thinking": thinking_text
            })
            
        except Exception as e:
            st.error(f"에러 발생: {str(e)}")
            st.info("에이전트가 실행 중인지 확인하세요: `python agents/cs_feedback_agent.py`")

# Sidebar
with st.sidebar:
    st.header("에이전트 정보")
    st.info(f"**URL**: {AGENT_URL}")
    st.info("**포트**: 9002")
    
    st.header("빠른 질문")
    if st.button("전체 피드백 조회"):
        st.session_state.messages.append({"role": "user", "content": "모든 피드백 보여줘"})
        st.rerun()
    
    if st.button("테란 피드백"):
        st.session_state.messages.append({"role": "user", "content": "테란 피드백만 보여줘"})
        st.rerun()
    
    if st.button("저그 피드백"):
        st.session_state.messages.append({"role": "user", "content": "저그 피드백 보여줘"})
        st.rerun()
    
    if st.button("프로토스 피드백"):
        st.session_state.messages.append({"role": "user", "content": "프로토스 피드백 보여줘"})
        st.rerun()
    
    if st.button("대화 기록 초기화"):
        st.session_state.messages = []
        st.rerun()

