# 마중 (Majung)

> 외국인 근로자의 신용 사다리를 자동으로 올려주는 **위임(Mandate)형 뱅킹 에이전트**
> JB Fin:AI Challenge MVP · 전북은행 · 브라보코리아 · 한패스 연계

브라보코리아 생태계의 **전환 엔진(Conversion Engine)**. 휴면 다운로드 20만 + 기존 외국인 고객 24만 위에서 동작.

- **1막 (쇼·상호투표용)** — 위임 송금: 급여 감지 → 환율 Rule 판단 → 한도 내 자동 실행 → 사기 수취인 자동 보류
- **2막 (본진·실무진용)** — 신용 사다리: 급여·부채 분석 → 사채 대환 가심사("연 ~250만원 절약") → 적금 연계. **승인은 JB 심사엔진의 배타적 권한**

## 제1원칙

> **"LLM은 송금 실행 경로에 없다."**
> 의도 파싱(LLM)은 자연어만 담당. 판정·실행은 전부 결정적(deterministic) 코드.

```
[발화/이벤트]
   ▼
LLM 의도 파싱 ── 자연어만 (금액·실행 결정 못 함)
   ▼ 구조화된 intent
╔══ 3중 게이트 (전부 결정적 코드) ══╗
║ Gate A — 위임장 검증 (전자서명·유효기간·철회·범위)   ║
║ Gate B — Rule 한도·조건 (FX Rule + 금액 한도)        ║
║ Gate C — 수취인 화이트리스트 + AML 스크리닝          ║
╚════════════ PASS만 통과 ════════════╝
   ▼
[실행 엔진] 송금 → 건별 모국어 통지 + 철회 버튼
   ▼
[검증/개선] 사후 성과 → 위임장 임계값 조정 제안
```

## Agent 루프 (평가 용어 그대로)

- 큰 루프: **판단**(Gate A·B·C) → **행동**(실행/보류/알림) → **검증/개선**(사후 성과→위임 조정)
- 세부: **수집** → **검색** → **판단** → **생성** → **검증** → **후속액션**

## 스택

| 영역 | 기술 |
|---|---|
| 백엔드 | Python 3.11 · FastAPI · SQLite |
| 오케스트레이터 | MCP 호스트 (3중 게이트 강제) |
| 룰 엔진 | rules.py (FX / AML / 대환) — 결정적 |
| 프론트 | React (Vite) 챗 UI + 관리 대시보드 |
| LLM | 의도 파싱·설명 생성 전용 (실행권한 없음) |

## 실행

```bash
# 백엔드
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
python -m app.seed          # 데모 데이터 시드 (DB 생성)
uvicorn app.main:app --reload --port 8000

# 프론트 (별도 터미널)
cd frontend
npm install
npm run dev
```

## 데모 수치 (재현 검증용)

| 시나리오 | 입력 | 결과 |
|---|---|---|
| 1막 자동송금 | 7일평균 18.12 vs 현재 18.45 | **+1.82% 유리** → 조건 충족 → 자동 실행 |
| 1막 자동보류 | 위임밖 신규수취인 480만 새벽 2:40 | AML score → 보류 + STR 큐 |
| 1막 사기차단 | OTP·신분증 요구 수취인 | 블랙리스트 즉시 차단 |
| 2막 대환 | 사채 1,500만 연 30% → JB 연 13.59% | **연 246만원 절약** |

## 폴더 구조

```
majung/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 엔드포인트
│   │   ├── orchestrator.py  # 3중 게이트 강제 (Gate A/B/C, LLM 실행 차단)
│   │   ├── rules.py         # FX / AML / 대환 룰 엔진
│   │   ├── mcp_tools.py     # MCP 도구 13종
│   │   ├── models.py        # 위임장 등 Pydantic 스키마
│   │   ├── llm.py           # 의도 파싱 (실행권한 없음)
│   │   ├── db.py            # SQLite 연결
│   │   ├── schema.sql       # DDL
│   │   └── seed.py          # 데모 시드
│   └── tests/
└── frontend/                # React(Vite) 챗 UI + 대시보드
```

> 상세 설계 기준: 제출 기능명세서(PDF) 참조
