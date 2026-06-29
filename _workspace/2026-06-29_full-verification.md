# 풀 검증 결과 2026-06-29

실행: claude/busy-cerf-43ijj5 (읽기전용 패스)

---

## 1. number-auditor (수치 감사)

| 동결 수치 | 코드 위치 | 값 | 상태 |
|---|---|---|---|
| FX 18.45 (now) | demoData.js FX_SEED.now | 18.45 | ✅ |
| FX 18.12 (MA) | demoData.js FX_SEED.ma | 18.12 | ✅ |
| 대환 JB 13.59% | demoData.js MOCK.refi.jb_apr | 0.1359 | ✅ |
| 대환 JB 13.59% | demoData.js BIZ.jbRefiApr | 0.1359 | ✅ |
| 연 246만 (절약) | demoData.js MOCK.refi.annual_saving_krw | 2,461,500 | ✅ |
| AML 컷 40 | backend/app/rules.py SCORE_HOLD | 40 | ✅ |
| AML 컷 70 | backend/app/rules.py SCORE_STR | 70 | ✅ |
| 사채 금리 30% | demoData.js MOCK.refi.current_apr | 0.30 | ✅ |

**⚠️ 주의 플래그:**
- `BIZ.perCapitaSavingKrw = 2_500_000` (250만원) vs 출처맵 "연 246만" 불일치
  - 사업가치 콘솔(BusinessValuePanel)에서 250만원으로 표시됨
  - MOCK.refi는 2,461,500원(246만)으로 정확한데 BIZ 콘솔만 다름
  - 동결구역 인접(표시 레이어 수치 변경) → 사람 리뷰 필요

---

## 2. regulation-defender (규제 준수)

- Gate A→B→C 순서 강제: orchestrator.py run_remittance ✅
- LLM 직접 execute_remittance 호출 불가: 게이트 통과 후에만 실행 ✅
- AML SCORE_HOLD=40, SCORE_STR=70: rules.py ✅
- late_night 가중치=0 (교대근무 외국인 오탐 방지): rules.py AML_WEIGHTS ✅
- 블랙리스트 즉시 차단: blacklist_hardcut=100, 하드컷 로직 ✅
- STR 후보 큐 등록: enqueue_str_candidate 호출 ✅
- 위임범위 밖 → AML 회부(hold_and_ask): Gate B 분기 ✅
- 대환 가심사 REFER_TO_JB_ENGINE (승인 아님): ✅

규제 준수 이슈 없음.

---

## 3. demo-qa (표시 레이어 QA)

### CustomerChat (E-9 페르소나)
- 베트남어 환대: "Chào mừng bạn đến Hàn Quốc" ✅
- E-9 표시: USER_NAME 🇻🇳 (E-9) ✅
- 언어 토글: Tiếng Việt / 中文 ✅
- 채팅 입력 플레이스홀더: 베트남어 ✅

**⚠️ 백로그 미반영:**
- "입국 시 브로커 사채 1,500만·연 30%" 한 줄 미표시 → E-9 백로그 항목 대기중
- 베트남어 인사 강화 미완 → 동 항목

### 기타 화면
- BusinessValuePanel: 사업가치 콘솔 정상 구성 ✅
- StudentView: 유학생 세그먼트 구분 ✅

---

## 결론

- 규제 준수: 이상 없음
- 수치: BIZ.perCapitaSavingKrw 250만 vs 출처맵 246만 불일치 → 사람 리뷰 필요 (동결구역 인접)
- 표시: E-9 첫 장면 context 한 줄 미반영 → 이번 사이클 구현 예정
