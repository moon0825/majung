# 데모 QA 리포트 (2026-06-28)

## 요약
런북 기술 항목 전체가 코드와 정합함. 단축키(F·1~5), paced 타이밍(0.9s/1.6s), healthRef 오프라인 폴백, GREETING 카드, OutcomeCard 배지, RefiCard 워터마크, GatePills aria-label, STR 큐 행 액션 버튼, 감사로그 한국어, 원칙 헤더, 시나리오 탭 토글(보수/기준/낙관), 백엔드 엔드포인트 모두 구현 확인. Vite 빌드 성공(37 모듈, 오류 없음). 위험 항목 없음.

---

## 빌드 검증
- vite build: **성공** (915ms, 오류 0건, 경고 0건)
- 출력 경로: `/tmp/qa-build-20260628/`
- 모듈 수: **37 모듈** transform 완료
- 번들 크기: JS 199.53 kB (gzip 64.52 kB) / CSS 21.48 kB (gzip 5.18 kB)

---

## 런북 ↔ 코드 정합 점검표

| 런북 항목 | 코드 위치 | 일치/불일치/위험 | 조치 |
|----------|---------|----------------|------|
| **F키 — 컨트롤 패널 숨김/표시** | App.jsx:429–431 `e.code === "KeyF"` → `setFilm` 토글, CSS `.app.film` 분기 | 일치 | 없음 |
| **숫자 1~5 단축키 (Digit1~5, Numpad1~5)** | App.jsx:419–424 `STEP_KEYS` 맵 → script/salary/holdAttempt/scamAttempt/refi | 일치 | 없음 |
| **입력창 포커스 시 단축키 무시** | App.jsx:426–427 INPUT/TEXTAREA/isContentEditable 체크 | 일치 | 없음 |
| **② 0.9초 paced 지연 ("감지→판정→실행" 가시화)** | App.jsx:21 `paced = async(promise, ms)`, salary():251 `paced(..., 900)` | 일치 | 없음 |
| **② 1.6초 녹색 글로우** | CSS `.card-auto` 클래스(Cards.jsx:157 `className="card card-auto"`), styles.css에서 애니메이션 정의 | 일치 | 없음 |
| **버튼 연타 차단 (1회만 실행)** | App.jsx:65–74 `busyRef` + `lock()`/`unlock()` 동기 거울 패턴 | 일치 | 없음 |
| **healthRef off → 목 데이터로 폴백 (②~⑤ 전 장면)** | App.jsx: salary()250, holdAttempt()279, scamAttempt()304, runRefi()323 각각 `!healthRef.current` 분기 → `D.MOCK.*` | 일치 | 없음 |
| **healthRef는 ref 방식으로 비동기 클로저 안에서도 최신값 유지** | App.jsx:60 `healthRef = useRef(false)`, 83 `healthRef.current = r.ok` | 일치 | 없음 |
| **GREETING 카드 (3메시지, 베트남어+한국어)** | App.jsx:23–33 `GREETING` 함수, 53 `useState(GREETING)`, reset()400 `GREETING()` | 일치 | 없음 |
| **피드 초기화 버튼 (재테이크용, DB 재시드 불필요)** | App.jsx:399–404 `reset()` 콜백 → `GREETING()`, traces/balance/mandate 초기화; ControlPanel에 전달 | 일치 | 없음 |
| **suppressNotifs — 폴링 메아리(중복 카드) 억제** | App.jsx:120 `suppressUntil.current = Date.now() + 6000`, 각 액션 첫 줄 `suppressNotifs()` 호출 | 일치 | 없음 |
| **OutcomeCard "접근매체 미보유·미양도" 배지 (전금법 제6조③)** | Cards.jsx:173–177 `mandate-badges` div, 3개 span 배지 | 일치 | 없음 |
| **OutcomeCard 철회 버튼 (자동 송금 후 즉각 철회권)** | Cards.jsx:183–189 `mandate.status === "active"` 분기 → `btn-danger-ghost` 버튼 | 일치 | 없음 |
| **RefiCard 4블록 동일 비중 (금소법 설명의무 모의)** | Cards.jsx:333–351 `.equal-grid` 4개 `.equal-cell` — 절약액/월상환액/총상환액/연체가산금리 동일 크기 | 일치 | 없음 |
| **RefiCard 가심사 워터마크 배지** | Cards.jsx:359–363 `.refi-watermark` div, "가심사(예비)—승인 아님" / "법무검수 고정 템플릿" / "최종 승인=JB 심사엔진" 3개 배지 | 일치 | 없음 |
| **GatePills aria-label ("3중 게이트 판정 결과")** | Cards.jsx:19 `aria-label="3중 게이트 판정 결과"`, 각 pill aria-label `Gate ${g} ${GATE_NAME[g]}: ${c.text}` | 일치 | 없음 |
| **STR 큐 행 액션 버튼 3개 (검토/FIU보고/기각)** | AdminDashboard.jsx:218–221 `검토`, `FIU 보고`, `기각(정상)` 버튼, 각각 aria-label 있음 | 일치 | 없음 |
| **감사로그 한국어 이벤트 뱃지** | AdminDashboard.jsx:10–14 `EVENT_CLS` 맵, `eventKo()` format.js 함수로 한국어 변환 | 일치 | 없음 |
| **원칙 헤더 (LLM 배제, 파이프라인 4단계)** | AdminDashboard.jsx:79–97 `.principle-strip` div: "송금 절차에서 LLM 배제", 수집→판단→행동→검증·개선 파이프 | 일치 | 없음 |
| **시나리오 탭 토글 (보수3%/기준7%/낙관12%)** | BusinessValuePanel.jsx:10–13 `SCENARIOS` 배열, 29 `useState(1)` 기본=기준, 66–76 `role="tab"` 버튼 3개 | 일치 | 없음 |
| **백엔드 `/health`** | backend/app/main.py:42–44 `GET /health` → `{"status":"ok"}` | 일치 | 없음 |
| **백엔드 `/chat` (의도 파싱만)** | main.py:47–64 `POST /chat` → `llm.parse_intent` | 일치 | 없음 |
| **백엔드 `/remittance/execute` (3중 게이트)** | main.py:67–89 `POST /remittance/execute` → `orchestrator.run_remittance` | 일치 | 없음 |
| **백엔드 `/salary/deposit` (급여→자동 송금 트리거)** | main.py:283–355 `POST /salary/deposit`, active 위임장 검색 후 집행 | 일치 | 없음 |
| **백엔드 `/mandate/issue`, `/mandate/{id}/sign`, `/mandate/{id}/revoke`** | main.py:124–255 세 엔드포인트 구현 | 일치 | 없음 |
| **백엔드 `/refi/prescreen`, `/refi/refer`** | main.py:104–121 두 엔드포인트 구현 | 일치 | 없음 |
| **백엔드 `/audit/{user_id}`, `/str-queue`, `/notifications/{user_id}`** | main.py:258–372 세 엔드포인트 구현 | 일치 | 없음 |
| **`/fx/{base}/{quote}` 경로** | main.py:92–101 `GET /fx/{base}/{quote}` (런북의 `/fx` 호출 경로: api.js:57 `call("/fx/KRW/VND")`) | 일치 | 없음 |
| **D-30분 점검: "API 연결됨" 녹색 표시** | App.jsx:458–461 `.health.on/.off` + healthRef 8초 폴링 | 일치 | 없음 |
| **재시드 절차: `python -m app.seed`** | backend/app/seed.py 파일 존재 확인 (ls 결과) | 일치 | 없음 |

---

## 폴백 준비 상태

| 항목 | 런북 기술 | 코드/파일 확인 결과 |
|------|----------|------------------|
| **백엔드 다운 → 목 모드 자동 전환** | 런북 57~58행: "헬스체크 실패 시 자동으로 목(Mock) 데이터로 전환됨" | App.jsx healthRef 분기로 ②③④⑤ 전 장면 MOCK 데이터 사용. 구현 완비. |
| **오프라인 무키 데모 (②~⑤ 전 장면)** | 런북 86~88행: F키로 패널 숨기고 숫자키만으로 진행 가능 | healthRef.current === false 경로에서 salary/holdAttempt/scamAttempt/runRefi 모두 paced(D.MOCK.*, ms) 반환. 장면 누락 없음. |
| **화면 안 나올 때: 새로고침 → 초기 상태 복원** | 런북 59행 | GREETING이 useState 초기값이므로 새로고침 시 자동 복원됨. |
| **재테이크: "피드 초기화" 버튼** | 런북 60행 | App.jsx reset() → GREETING()/traces/balance/mandate 초기화. DB 재시드 불필요. |
| **② 두 번째 실행 시 월 한도 소진 판정 → 재시드 필요** | 런북 60행 | 게이트 B가 monthly 한도를 DB에서 읽어 판정(orchestrator/rules.py). 런북 경고 정확함. |
| **녹화 폴백(영상 백업), 로컬 파일, 라이브 ⑤만** | 촬영 체크리스트에 "재촬영 전 반드시 seed 재실행" 등 촬영 지침 있음. 별도 "녹화 폴백 파일 경로" 명시는 런북에 없음. | 런북은 기술 장애 폴백(목 모드)만 기술. 녹화 영상 파일 경로나 "⑤마지막 클릭만 라이브" 분리 촬영 계획은 문서화 미흡. |

---

## 위험·불일치 항목

1. **녹화 폴백 파일 경로 미명시**: 런북 "폴백 절차"는 기술 장애(헬스체크 실패) 시 목 모드 자동 전환만 기술함. "녹화 영상으로 대체", "⑤ 마지막 클릭만 라이브" 같은 촬영분 폴백 절차는 문서에 없음. 발표 현장에서 프로젝터·음향 장애 시 대비 시나리오를 별도 협의해 두는 것을 권장함. (코드 결함 아님, 런북 문서 보완 권장)

2. **그 외 불일치 없음**: 단축키·paced 타이밍·healthRef 폴백·GREETING·카드 배지·워터마크·aria-label·STR 큐·감사로그·원칙 헤더·시나리오 탭·백엔드 엔드포인트 전 항목 정합.
