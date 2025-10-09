#!/usr/bin/env python3
import streamlit as st
import requests

AGENT_URL = "http://localhost:9003"

st.set_page_config(page_title="데이터 분석 에이전트", page_icon="📊", layout="wide")
st.title("📊 데이터 분석 에이전트")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and "thinking" in message:
            with st.expander("🧠 사고 과정 보기"):
                st.code(message["thinking"])
        st.markdown(message["content"])

if prompt := st.chat_input("질문을 입력하세요 (예: 승률 알려줘)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        answer_placeholder = st.empty()
        
        thinking_text = ""
        answer_text = ""
        
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
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer_text,
                "thinking": thinking_text
            })
            
        except Exception as e:
            st.error(f"에러 발생: {str(e)}")
            st.info("에이전트가 실행 중인지 확인하세요")

with st.sidebar:
    st.header("에이전트 정보")
    st.info(f"**URL**: {AGENT_URL}")
    
    if st.button("🔄 대화 초기화"):
        st.session_state.messages = []
        st.rerun()
    
    st.header("빠른 질문")
    if st.button("승률 조회"):
        st.session_state.messages.append({"role": "user", "content": "승률 알려줘"})
        st.rerun()
