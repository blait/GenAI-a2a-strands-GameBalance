# Game Balance A2A System

3개의 AI 에이전트가 A2A 프로토콜로 통신하며 게임 밸런스를 분석하는 시스템

## 아키텍처

```
┌─────────────────────────────────────────────────────┐
│           Game Balance Agent (9000)                 │
│              Coordinator + A2A Server               │
└─────────────────────────────────────────────────────┘
         ↓ A2A Protocol          ↓ A2A Protocol
┌──────────────────────┐  ┌──────────────────────┐
│  CS Feedback Agent   │  │ Data Analysis Agent  │
│    (9001)            │  │      (9002)          │
│    A2A Server        │  │    A2A Server        │
└──────────────────────┘  └──────────────────────┘
```

## 에이전트 구성

### 1. Game Balance Agent (포트 9000)
- **역할**: 코디네이터 - 다른 에이전트 조율
- **GUI**: http://localhost:8501
- **기능**: 종합 밸런스 분석 및 패치 제안

### 2. CS Feedback Agent (포트 9001)
- **역할**: CS 피드백 데이터 제공
- **GUI**: http://localhost:8502
- **기능**: 고객 컴플레인 조회 및 분석

### 3. Data Analysis Agent (포트 9002)
- **역할**: 게임 데이터 분석
- **GUI**: http://localhost:8503
- **기능**: 승률 계산, 밸런스 이슈 감지

## 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. AWS 자격 증명 설정
```bash
# AWS CLI 설정 또는 환경 변수
export AWS_REGION=us-east-1
```

### 3. 전체 시스템 시작
```bash
# 모든 에이전트 시작
python run_system.py
```

### 4. 개별 에이전트 시작 (선택)
```bash
# CS Feedback Agent
python agents/cs_feedback_agent.py

# Data Analysis Agent
python agents/data_analysis_agent.py

# Game Balance Agent
python agents/game_balance_agent.py
```

### 5. Streamlit GUI 시작
```bash
# 각각 별도 터미널에서 실행

# Game Balance GUI (포트 8501)
streamlit run gui/balance_gui.py

# CS Feedback GUI (포트 8502)
streamlit run gui/cs_gui.py --server.port 8502

# Data Analysis GUI (포트 8503)
streamlit run gui/analysis_gui.py --server.port 8503
```

## 사용 예시

### Game Balance Agent
```
질문: "현재 게임 밸런스를 분석해줘"

응답:
1. Data Analysis Agent에서 승률 데이터 조회
   - Terran: 60% 승률
   - Zerg: 20% 승률
   - Protoss: 20% 승률

2. CS Feedback Agent에서 피드백 조회
   - Terran 너프 요청: 4건 (high urgency)
   - Zerg 버프 요청: 3건 (high urgency)

3. 종합 분석 및 권장사항:
   - Terran 공격력 -5% 너프
   - Zerg 체력 +10% 버프
```

### CS Feedback Agent
```
질문: "Terran에 대한 피드백 보여줘"

응답:
- 마린 러시가 너무 강력 (high urgency, 245 upvotes)
- 탱크 사거리가 너무 김 (medium urgency, 189 upvotes)
- 벙커 건설 속도가 빠름 (high urgency, 201 upvotes)
```

### Data Analysis Agent
```
질문: "승률 통계 보여줘"

응답:
- Terran: 60% (18승)
- Zerg: 20% (6승)
- Protoss: 20% (6승)
- 밸런스 이슈 감지: Terran이 40% 더 높음 (high severity)
```

## A2A 프로토콜 테스트

### trace.sh로 에이전트 대화 흐름 시각화
```bash
# 기본 사용
./trace.sh "테란 승률은?"

# 출력 예시:
# 🎯 Query: 테란 승률은?
# 📊 Total Cycles: 3
# 🆕 New Request: Cycle 2 ~ 3
# 
# 📍 Cycle 2 🆕
# 🧠 [Thinking] ...
# 📞 → Data Analysis Agent: Retrieve win rate statistics for Terran race.
# ✅ ← Data Analysis Agent: Terran has a win rate of 100.00%...
```

### curl로 직접 테스트
```bash
# Game Balance Agent
curl -X POST http://localhost:9000/send_message \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "role": "user",
      "parts": [{"type": "text", "text": "Analyze game balance"}],
      "messageId": "test-1"
    }
  }'

# AgentCard 조회
curl http://localhost:9000/.well-known/agent.json
```

## 프로젝트 구조

```
game-balance-a2a/
├── agents/
│   ├── game_balance_agent.py      # 코디네이터 (9000)
│   ├── cs_feedback_agent.py       # CS 피드백 (9001)
│   └── data_analysis_agent.py     # 데이터 분석 (9002)
├── data/
│   ├── feedback_data.json         # 샘플 피드백 (10건)
│   └── game_logs.json             # 샘플 게임 로그 (30건)
├── gui/
│   ├── balance_gui.py             # 밸런스 GUI (8501)
│   ├── cs_gui.py                  # CS GUI (8502)
│   └── analysis_gui.py            # 분석 GUI (8503)
├── run_system.py                  # 전체 시스템 실행
├── requirements.txt
└── README.md
```

## 구현 특징

### 명시적 Task 관리
- AgentExecutor로 Task 생성 및 상태 관리
- TaskStatusUpdateEvent (working → completed/failed)
- TaskArtifactUpdateEvent (결과 전송)

### 명시적 AgentCard
- AgentSkill 정의
- AgentCapabilities (streaming, pushNotifications)
- 예시 쿼리 포함

### A2A 프로토콜
- 표준 Message/Task 구조
- HTTP 기반 통신
- 에이전트 간 느슨한 결합

## 에이전트 관리

### 에이전트 재시작 (히스토리 초기화)
에이전트는 대화 히스토리를 메모리에 저장하므로, 오래 실행하면 메시지 크기가 커져 "too large" 에러가 발생할 수 있습니다.

```bash
# 1. 모든 에이전트 종료
pkill -f "game_balance_agent|data_analysis_agent|cs_feedback_agent"

# 2. 재시작 (절대 경로 사용)
cd "/Users/hyeonsup/aws goa 2025/msk-a2a-demo/game-balance-a2a"

venv/bin/python agents/cs_feedback_agent.py > /tmp/cs_agent.log 2>&1 &
venv/bin/python agents/data_analysis_agent.py > /tmp/data_agent.log 2>&1 &
sleep 3
venv/bin/python agents/game_balance_agent.py > /tmp/balance_agent.log 2>&1 &

# 3. 확인 (10초 대기 후)
sleep 10
lsof -i :8000,9000,9001,9002 | grep LISTEN
```

### 에이전트 상태 확인
```bash
# 포트 확인
lsof -i :8000,9000,9001,9002 | grep LISTEN

# 로그 확인
tail -f /tmp/balance_agent.log
tail -f /tmp/cs_agent.log
tail -f /tmp/data_agent.log
```

## 문제 해결

### "The tool result was too large!" 에러
- **원인**: 에이전트가 대화 히스토리를 계속 쌓아서 메시지 크기 초과
- **해결**: 위의 "에이전트 재시작" 절차 수행

### 에이전트가 시작되지 않음
```bash
# 포트 확인
lsof -i :9000
lsof -i :9001
lsof -i :9002

# 프로세스 강제 종료
kill -9 <PID>
```

### AWS 자격 증명 오류
```bash
# AWS CLI 설정 확인
aws configure list

# 환경 변수 확인
echo $AWS_REGION
```

### Streamlit 연결 오류
- 에이전트가 먼저 실행되어야 함
- 포트 충돌 확인
- 방화벽 설정 확인

## 라이선스

MIT License
