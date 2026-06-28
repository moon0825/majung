# 풀 검증 결과 — 2026-06-28

## number-auditor
```
[PASS] FX now=18.45: demoData.js FX_SEED.now=18.45 일치
[PASS] FX ma=18.12: demoData.js FX_SEED.ma=18.12 일치
[PASS] FX advantagePct=1.82: demoData.js FX_SEED.advantagePct=1.82 일치
[PASS] 대환 금리 JB 13.59%: demoData.js MOCK.refi.jb_apr=0.1359 및 BIZ.jbRefiApr=0.1359 일치
[PASS] 대환 금리 사채 30%: demoData.js MOCK.refi.current_apr=0.30 및 BIZ.loanSharkApr=0.30 일치
[PASS] 대환 절약 246만 원 (MOCK): annual_saving_krw=2_461_500 → 246.15만, 공식 일치
[FAIL] 대환 절약 1인당 (BIZ 콘솔): BIZ.perCapitaSavingKrw=2_500_000 (250만) → 출처맵 기준 246만과 불일치
[PASS] AML 컷 SCORE_HOLD=40: rules.py L67 일치
[PASS] AML 컷 SCORE_STR=70: rules.py L68 일치
[PASS] 대환 잔액 693억: BIZ.refiBalanceKrw=69_300_000_000 일치
[PASS] 연 이자 66.5억: BIZ.annualInterestKrw=6_650_000_000 일치
[PASS] 외국인 신용대출 점유율 72%: BIZ.marketSharePct=72 일치
[PASS] 외국인 누적 대출 24만 명: BIZ.cumulativeBorrowers=240_000 일치
```
**총평: 12개 중 11 PASS, 1 FAIL** — BIZ 콘솔 perCapitaSavingKrw 수정 필요 → 이번 사이클에 수정 완료

## regulation-defender
```
[PASS] AML 스코어 컷 40/70: rules.py SCORE_HOLD=40, SCORE_STR=70 정확히 구현
[PASS] STR 보류 경로: str_hold 시 enqueue_str_candidate() 호출, GET /str-queue 조회 가능
[WARN] 외환 연간 5만달러 한도: 코드 미구현 (데모 범위 외, 실 서비스 전 보완 필요)
[WARN] 신규계좌 1일 30만원 상한: is_limited_account 플래그 존재하나 Gate B와 미연결 (데모 범위 외)
[PASS] Gate A→B→C 순서 보장: orchestrator.py 단일 실행 경로, 테스트 검증 완료
[PASS] throw 금지 계약: api.js 전 경로 catch→반환, throw 없음
```
**총평: 4 PASS, 2 WARN** — WARN 2건은 실 서비스용이며 데모 범위 외, 보류

## demo-qa
```
[PASS] E-9 페르소나 헤더: m-acct에 (E-9) 표시 있음
[WARN] 사채 문맥 첫 장면 부재: "브로커사채 연 30%"는 대환 카드 열람 후에만 노출됨 → E-9 개선 대상
[PASS] 베트남어 인사(WELCOME.vi): 기본 lang="vi" 초기화, 첫 화면 베트남어 표시
[PASS] 다국어 토글(vi/zh): 구현 정상, OutcomeCard 제목 반응
[PASS] 3중 게이트 표시: GatePills 컴포넌트, 전 경로 호출
[PASS] BusinessValuePanel BIZ 수치: 693억·66.5억·퍼널 5단계 표시
[PASS] StudentView 세그먼트 분리: App.jsx 탭 분리, 베트남어 누출 없음
[PASS] 오프라인 폴백 MOCK 데이터: healthyRef 분기 완전
```
**총평: 7 PASS, 1 WARN** — E-9 사채 문맥 첫 장면 추가 → 이번 사이클 구현

## 사이클 계획
1. ~~BIZ.perCapitaSavingKrw 2_500_000 → 2_461_500 수정~~
2. ~~E-9 CustomerChat 헤더에 사채 문맥 한 줄 추가~~
3. ~~vite build 검증 후 커밋~~
