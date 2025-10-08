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
                st.markdown(message["thinking"])
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("질문을 입력하세요 (예: 테란 피드백 보여줘)"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Send to agent
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            response = requests.post(
                f"{AGENT_URL}/ask",
                json={"query": prompt},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                # Parse response structure
                if "response" in result and "message" in result["response"]:
                    content = result["response"]["message"]["content"]
                    response_text = content[0]["text"] if content else "응답 없음"
                    
                    # Extract thinking and answer
                    if "<thinking>" in response_text and "</thinking>" in response_text:
                        thinking_start = response_text.find("<thinking>") + 10
                        thinking_end = response_text.find("</thinking>")
                        thinking = response_text[thinking_start:thinking_end].strip()
                        answer = response_text[thinking_end + 11:].strip()
                        
                        with st.expander("🧠 사고 과정 보기"):
                            st.markdown(thinking)
                        message_placeholder.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer, "thinking": thinking})
                    else:
                        message_placeholder.markdown(response_text)
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                else:
                    response_text = str(result)
                    message_placeholder.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
            else:
                error_msg = f"오류: {response.status_code}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        except Exception as e:
            error_msg = f"연결 실패: {str(e)}"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

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

