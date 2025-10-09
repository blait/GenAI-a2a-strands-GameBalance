# Game Balance A2A System

3개의 AI 에이전트가 A2A 프로토콜로 통신하며 게임 밸런스를 분석하는 시스템

<img width="1187" height="1145" alt="image" src="https://github.com/user-attachments/assets/26fab216-7c21-43f7-9633-9dc91845cb8c" />

## 🔄 **멀티턴 대화 지원 (A2A Task 기반)**

이 시스템은 **A2A Task Store**를 활용하여 에이전트 간 멀티턴 대화를 지원합니다.

### **작동 방식:**

1. **첫 호출**: 새로운 Task 생성, Task ID 반환
2. **추가 호출**: 같은 Task ID 사용 → 이전 대화 기억
3. **A2AServer**: Task Store가 대화 히스토리 자동 관리

### **사용 예시:**

```python
# Balance Agent에서
call_data_analysis_agent("승률 알려줘")  
# → 새 Task 생성

call_data_analysis_agent("테란 상세 데이터 줘", continue_conversation=True)
# → 같은 Task 이어가기 (이전 대화 기억!)
```

### **테스트:**

```bash
# 멀티턴 대화 테스트
python test_multiturn.py
```

---

## 빠른 시작

```bash
# 1. 가상환경 설정
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. AWS 설정
aws configure

# 3. 시스템 실행
./restart_all.sh  # 에이전트 시작
./run_gui.sh      # GUI 시작

# 4. 접속
# http://localhost:8501 - Balance Agent (메인)
# http://localhost:8502 - CS Feedback Agent  
# http://localhost:8503 - Data Analysis Agent
```


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
- **멀티턴**: `continue_conversation=True` 파라미터 지원


### 2. CS Feedback Agent (포트 9001)
- **역할**: CS 피드백 데이터 제공
- **GUI**: http://localhost:8502
- **기능**: 고객 컴플레인 조회 및 분석

### 3. Data Analysis Agent (포트 9002)
- **역할**: 게임 데이터 분석
- **GUI**: http://localhost:8503
- **기능**: 승률 계산, 밸런스 이슈 감지

## 설치 및 실행

### 1. Python 가상환경 설정
```bash
# 가상환경 생성 (프로젝트 루트에서)
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate     # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. AWS 자격 증명 설정
```bash
# AWS CLI 설정
aws configure

# 또는 환경 변수 설정
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
```

### 3. 시스템 실행

#### 방법 1: 자동 실행 스크립트 (권장)
```bash
# 모든 에이전트 자동 시작
./restart_all.sh

# GUI 실행
./run_gui.sh
```

#### 방법 2: 수동 실행
```bash
# 가상환경이 활성화된 상태에서 실행

# 1. 에이전트 실행 (순서 중요)
python agents/cs_feedback_agent.py &
python agents/data_analysis_agent.py &
sleep 3
python agents/game_balance_agent.py &

# 2. GUI 실행 (각각 별도 터미널에서)
streamlit run gui/balance_gui.py --server.port 8501 &
streamlit run gui/cs_gui.py --server.port 8502 &
streamlit run gui/analysis_gui.py --server.port 8503 &
```

### 4. 접속 및 테스트

**GUI 접속:**
- **Balance Agent**: http://localhost:8501 (메인 - A2A 허브)
- **CS Feedback Agent**: http://localhost:8502 (피드백 조회)  
- **Data Analysis Agent**: http://localhost:8503 (통계 분석)

**CLI 테스트:**
```bash
# A2A 통신 흐름 시각화
./trace.sh "게임 밸런스 분석해줘"

# 직접 API 호출
curl -X POST http://localhost:9000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "테란 승률은?"}'
```

## 시스템 구조

### 에이전트 포트
- **Game Balance Agent**: 8000 (A2A Hub)
- **Data Analysis Agent**: 9001
- **CS Feedback Agent**: 9002

### GUI 포트
- **Balance GUI**: 8501
- **CS GUI**: 8502
- **Analysis GUI**: 8503

### A2A 통신 흐름
```
사용자 → Balance Agent (8000)
         ├─→ Data Analysis Agent (9001) [A2A 호출]
         └─→ CS Feedback Agent (9002) [A2A 호출]
         
사용자 → Data Analysis Agent (9001) [직접 호출]
사용자 → CS Feedback Agent (9002) [직접 호출]
```
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

# 최근 50줄 확인
tail -50 /tmp/balance_agent.log
tail -50 /tmp/cs_agent.log
tail -50 /tmp/data_agent.log

# 에러만 확인
grep -i error /tmp/balance_agent.log
grep -i error /tmp/cs_agent.log
grep -i error /tmp/data_agent.log
```

### 로그 파일 위치
- Game Balance Agent: `/tmp/balance_agent.log`
- CS Feedback Agent: `/tmp/cs_agent.log`
- Data Analysis Agent: `/tmp/data_agent.log`

## 문제 해결

### 가상환경 관련
```bash
# 가상환경이 활성화되지 않은 경우
source venv/bin/activate

# 가상환경 확인
which python  # venv/bin/python이 나와야 함

# 의존성 재설치
pip install -r requirements.txt
```

### 에이전트가 시작되지 않을 때
```bash
# 포트 사용 확인
lsof -i :9000,9001,9002

# 프로세스 강제 종료
pkill -f "game_balance_agent|data_analysis_agent|cs_feedback_agent"

# 재시작
./restart_all.sh
```

### "too large" 에러 발생 시
에이전트가 대화 히스토리를 계속 쌓아서 메시지 크기가 초과된 경우:
```bash
# 에이전트 재시작으로 히스토리 초기화
./restart_all.sh
```

### AWS 자격 증명 오류
```bash
# 설정 확인
aws configure list
echo $AWS_REGION

# 재설정
aws configure
```

### Streamlit 연결 오류
```bash
# 에이전트가 먼저 실행되어야 함
# 포트 충돌 확인
lsof -i :8501,8502,8503

# GUI 프로세스 종료
pkill -f streamlit

# GUI 재시작
./run_gui.sh
```

## 라이선스

MIT License
