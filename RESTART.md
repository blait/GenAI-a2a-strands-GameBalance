# 빠른 재시작 가이드

## 한 번에 모두 재시작

```bash
./restart_all.sh
```

## 개별 재시작

### 1. 에이전트만 재시작

```bash
# 종료
pkill -f "game_balance_agent|data_analysis_agent|cs_feedback_agent"

# 시작
cd "/Users/hyeonsup/aws goa 2025/msk-a2a-demo/game-balance-a2a"
venv/bin/python -u agents/cs_feedback_agent.py > /tmp/cs_agent.log 2>&1 &
venv/bin/python -u agents/data_analysis_agent.py > /tmp/data_agent.log 2>&1 &
sleep 3
venv/bin/python -u agents/game_balance_agent.py > /tmp/balance_agent.log 2>&1 &
```

### 2. GUI만 재시작

```bash
# 종료
pkill -f streamlit

# 시작
cd "/Users/hyeonsup/aws goa 2025/msk-a2a-demo/game-balance-a2a"
venv/bin/streamlit run gui/balance_gui.py --server.port 8501 > /tmp/balance_gui.log 2>&1 &
venv/bin/streamlit run gui/cs_gui.py --server.port 8502 > /tmp/cs_gui.log 2>&1 &
venv/bin/streamlit run gui/analysis_gui.py --server.port 8503 > /tmp/analysis_gui.log 2>&1 &
```

### 3. 특정 에이전트만 재시작

```bash
# Balance Agent
pkill -f game_balance_agent
cd "/Users/hyeonsup/aws goa 2025/msk-a2a-demo/game-balance-a2a"
venv/bin/python -u agents/game_balance_agent.py > /tmp/balance_agent.log 2>&1 &

# CS Agent
pkill -f cs_feedback_agent
cd "/Users/hyeonsup/aws goa 2025/msk-a2a-demo/game-balance-a2a"
venv/bin/python -u agents/cs_feedback_agent.py > /tmp/cs_agent.log 2>&1 &

# Data Agent
pkill -f data_analysis_agent
cd "/Users/hyeonsup/aws goa 2025/msk-a2a-demo/game-balance-a2a"
venv/bin/python -u agents/data_analysis_agent.py > /tmp/data_agent.log 2>&1 &
```

## 상태 확인

```bash
# 에이전트 포트 확인
lsof -i :8000,9001,9003 | grep LISTEN

# GUI 포트 확인
lsof -i :8501,8502,8503 | grep LISTEN

# 로그 확인
tail -f /tmp/balance_agent.log
tail -f /tmp/cs_agent.log
tail -f /tmp/data_agent.log
```

## 접속 URL

- **Balance GUI**: http://localhost:8501
- **CS GUI**: http://localhost:8502
- **Analysis GUI**: http://localhost:8503

## 주요 기능

### 실시간 스트리밍
- 모든 GUI에서 AI의 사고 과정을 실시간으로 확인 가능
- "🧠 사고 과정 (실시간)" expander에서 Tool 호출 과정 표시
- 줄바꿈과 띄어쓰기가 보존된 코드 블록으로 표시

### 로그 확인
- `-u` 플래그로 unbuffered 출력 → 실시간 로그 확인 가능
- `/tmp/*.log` 파일에서 각 에이전트의 상세 로그 확인

## 문제 해결

### "The tool result was too large!" 에러
→ 에이전트 재시작으로 히스토리 초기화

### 포트 충돌
```bash
# 사용 중인 프로세스 확인
lsof -i :8000
# 강제 종료
kill -9 <PID>
```

### GUI 연결 실패
→ 에이전트가 먼저 실행되어야 함. 에이전트 재시작 후 GUI 재시작
