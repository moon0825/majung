# 규제 준수 감사 보고서 — 마중(Majung) JB 본선 데모
작성일: 2026-06-29  
감사 범위: frontend/src/api.js, frontend/src/App.jsx, frontend/src/demoData.js,  
          backend/app/orchestrator.py, backend/app/rules.py, backend/app/mcp_tools.py,  
          backend/app/main.py, backend/app/models.py, backend/app/schema.sql,  
          backend/app/seed.py, backend/tests/ (3파일)

---

## 1. 게이트 판정 순서·단일 실행 경로 (Gate A → B → C)

**판정: PASS**

`orchestrator.py`의 `run_remittance()` 함수는 다음 순서를 엄격히 지킨다.

- Gate A(`validate_mandate`) → 실패 시 즉시 `rejected` 반환, C로 진입 불가
- Gate B(`check_limits` + `evaluate_fx`) → 위임 범위 내 트랜잭션에만 적용; FX 미달 시 `held` 반환, C로 진입 불가
- Gate C(`screen_beneficiary_aml`) → BLOCK/STR_HOLD/HOLD 별 조기 반환
- 게이트 전부 통과한 경우에만 `execute_remittance` 호출

`execute_remittance`는 `mcp_tools.py` 내에 격리되어 있고, LLM(`/chat` 엔드포인트)은 이 함수를 직접 호출하는 경로가 없다. `/student/tuition/execute`도 동일한 `run_remittance`를 `fx_pair="KRW/CNY"`만 바꿔 재사용하므로 게이트 구조가 동일하게 적용된다.

우려사항: 없음.

---

## 2. lock/unlock·busyRef 패턴 (이중 실행 방지)

**판정: PASS**

`App.jsx`에서 `busyRef`(동기 거울)와 `lock()`/`unlock()` 패턴이 모든 액션 함수에 일관되게 적용되어 있다.

- `lock()`: `busyRef.current`가 이미 `true`이면 즉시 `false` 반환 → 연타·동시 클릭 차단
- `unlock()`: `finally` 블록 내에서만 호출 → 예외 발생 시에도 항상 해제
- 대상 액션: `send`, `sign`, `salary`, `holdAttempt`, `scamAttempt`, `refiButton`, `refer`

`runRefi`와 `runRevoke`는 `lock()` 없이 호출되지만, 이 함수들은 항상 `lock()`을 보유한 상위 래퍼(`refiButton`, `send`) 내에서만 호출되므로 실질적으로 보호된다.

우려사항: 없음.

---

## 3. 오프라인 폴백 (healthRef 분기)

**판정: PASS**

`healthRef.current`를 기준으로 모든 액션 함수가 두 분기를 구현한다.

- 온라인 분기: 실제 백엔드 API 호출
- 오프라인 분기: `demoData.js`의 `MOCK.*` 또는 시드값 사용 (`D.SEED_*`)

`useEffect` 헬스체크(8초 주기)가 `healthRef.current`와 `setHealthy`를 동시에 갱신하며, 헬스체크 결과가 `false`인 경우 알림 폴링도 `healthRef.current`를 재확인해 건너뛴다.

우려사항: 없음.

---

## 4. suppressNotifs 플래그 (중복 알림 억제)

**판정: PASS**

`suppressUntil` ref와 `suppressNotifs()` 함수가 `App.jsx`에 구현되어 있다.

- `suppressNotifs()`는 `suppressUntil.current = Date.now() + 6000`으로 6초 억제 창을 설정
- 알림 폴링 루프에서 `Date.now() < suppressUntil.current`이면 신규 알림 카드 삽입을 건너뜀
- 버튼 액션(`sign`, `salary`, `holdAttempt`, `scamAttempt`, `runRefi`, `refer`, `runRevoke`) 진입 직후 반드시 호출됨

우려사항: 없음.

---

## 5. api.js throw 금지 계약

**판정: PASS**

`api.js` 파일 전체에 `throw` 문이 존재하지 않는다. 내부 `call()` 함수는 다음 두 가지 경우를 모두 `{ ok, status, data, error }` 형태로 반환한다.

- HTTP 에러 응답 (`!res.ok`): `{ ok: false, status, data, error: String(msg) }` 반환
- 네트워크/타임아웃 예외 (`catch`): `{ ok: false, status: 0, data: null, error: "백엔드(8000) 연결 실패" }` 반환

`extractOutcome()` 헬퍼도 예외 없이 `null`을 반환하는 방어적 구현이다.

우려사항: 없음.

---

## 6. 특금법 STR/CDD/CTR 의무

**판정: PASS (데모 범위 내)**

STR(의심거래보고) 구현:
- `rules.py`의 `evaluate_aml()`: 누적 스코어 ≥70 → `STR_HOLD` 결정
- `orchestrator.py`: `STR_HOLD` 수신 시 `mcp_tools.enqueue_str_candidate()` 호출 → `str_queue` 테이블 적재
- `GET /str-queue` 엔드포인트로 관리자 조회 가능
- AML 스코어링 로직: 블랙리스트 하드컷(+100), 구조화(+50), 위임 범위 밖(+30), 반복 한도 직하(+30), 신규 수취인(+25), 고액(+20)

CDD(고객주의의무) 관련:
- 수취인 화이트리스트 사전 등록 구조 (`beneficiaries` 테이블, `is_whitelisted` 필드)
- 위임장 전자서명 필수 (`esign_hash` 검증, Gate A)
- 모국어 재확인 (`reconfirmed_in_language: true`)

CTR(고액현금거래보고):
- **미구현**: 현 코드베이스에 일일 1천만 원 이상 CTR 자동 보고 로직이 없음. 단, 데모 시나리오의 최대 거래액(200만~480만 원)이 CTR 임계액(1천만 원) 미만이고, 데모 범위는 MVㅔ임을 감안할 때 본선 심사에서 문제가 될 가능성은 낮음.

우려사항 (WARN): CTR 로직 미구현. 실제 서비스 시 KoFIU 요건 충족을 위한 별도 구현 필요. 데모 범위 이상의 배포 시 추가 필요.

---

## 7. 외국인 거주자 무증빙 송금 연 5만 달러 한도 (외국환거래법)

**판정: WARN**

`출처맵.md`와 `build_docx.py`의 설계 설명("게이트 B에 누적 한도 검증 로직을, 게이트 C에 분할 송금 탐지 로직을 구현함")에는 이 제약이 명시되어 있다.

그러나 실제 코드에서는:
- `check_limits()`(Gate B): 위임장 내 `limit_per_tx_krw`와 `limit_monthly_krw`만 확인. 연간 누적 USD 환산 한도 검증 없음.
- `evaluate_aml()`(Gate C): `structuring` 플래그가 있으나, 연간 누적 금액을 집계하는 로직이 없음. `structuring` 탐지는 `AmlContext`에 필드는 있지만 `screen_beneficiary_aml()`에서 항상 `False`로 설정됨 (외부에서 주입하지 않음).
- `transactions` 테이블에 연간 누적 USD 합계를 쿼리하는 코드가 없음.

데모 시나리오에서 1인 월 200만 원(≈약 1,500달러)은 연 5만 달러(약 6,700만 원)의 0.4% 수준으로 실질적 초과 위험은 없으나, 설계 설명과 실제 구현 간 불일치가 존재한다.

우려사항 (WARN):  
- 연간 누적 USD 한도 검증 로직이 Gate B에 없음  
- `structuring` 플래그가 `screen_beneficiary_aml()`에서 항상 `False` (DB 기반 반복 패턴 탐지 미구현)  
- 실제 서비스 전 외국환거래법 §18(무증빙 한도) 준수 로직 추가 필요

---

## 8. AML STR 보류 로직 존재 여부

**판정: PASS**

STR 보류 흐름이 코드 전반에 완전히 구현되어 있다:

1. `rules.py`: `SCORE_STR = 70`, 스코어 ≥70 시 `AmlDecision("STR_HOLD", ...)`
2. `orchestrator.py`: `aml["decision"] == "STR_HOLD"` 분기 → `enqueue_str_candidate()` 호출 후 `RemittanceOutcome("str_hold", ...)` 반환
3. `mcp_tools.py`: `enqueue_str_candidate()` → `str_queue` 테이블 INSERT
4. `backend/tests/test_gates.py`: `test_aml_out_of_mandate_new_high_amount_scores_75_and_routes_to_str()` 테스트가 score=75, decision=STR_HOLD, late_night 플래그를 검증

---

## 종합 평가

| 항목 | 판정 |
|---|---|
| Gate A→B→C 순서·단일 실행 경로 | PASS |
| lock/unlock·busyRef 이중 실행 방지 | PASS |
| 오프라인 폴백 (healthRef 분기) | PASS |
| suppressNotifs 플래그 | PASS |
| api.js throw 금지 계약 | PASS |
| 특금법 STR 보류 로직 | PASS |
| 특금법 CTR 로직 | WARN — 미구현 (데모 범위 초과 시 필요) |
| 외국인 무증빙 송금 연 5만 달러 한도 | WARN — 설계 명세와 구현 불일치 |

### 전체 판정: **YELLOW**

동결 구역 6개 항목은 모두 무결하게 보존되어 있다. 핵심 규제 의무(STR 보류, AML 스코어링, 블랙리스트 차단)도 구현 완료되어 있다. 다만 두 가지 WARN이 존재한다:

1. CTR(고액현금거래보고) 미구현 — 데모 거래액이 임계액 미만이라 시연 리스크는 없으나 심사위원 질문 대비 필요
2. 외환 연간 한도 검증 코드 미구현 — 설계 문서에 명시된 기능이 실제 코드에 없음. 심사에서 "실제 동작하냐"고 질문받을 경우 "데모 한도 내 MVP" 수준으로 답변해야 함

RED 항목 없음. 동결 구역 위반 없음. 본선 시연에 지장 없음.
