# 마중 (Majung) — 작업 매뉴얼

이 파일은 이 레포에서 일하는 모든 Claude가 먼저 읽는다. 낮에 사람과 함께 일할 때도, 새벽에 루틴이 혼자 돌 때도 같은 규칙으로 움직인다. 목표는 하나다. JB금융그룹 Fin:AI Challenge 본선(7/4~5)에서 1등.

## 0. 한 줄
마중은 외국인 노동자를 위한 위임형 뱅킹 에이전트다. 모국어로 위임하면 급여가 들어올 때 환율 조건에 맞춰 자동 송금하고, 입국 후 쌓은 기록으로 사채를 JB 제도권 대출로 갈아타게 돕는다. 제1원칙: LLM은 송금 실행 경로에 없다. 판정과 실행은 결정적 코드(3중 게이트)가 한다.

## 1. 동결 구역 (절대 수정 금지, 읽기만)
다음은 데모의 심장이다. 검증·문서 작업 중에도 손대지 않는다.
- 게이트 판정과 단일 실행 경로: `backend/app/orchestrator.py`의 run_remittance, Gate A/B/C 순서.
- 룰: `backend/app/rules.py`, `mcp_tools.py`의 execute_remittance·screen_beneficiary_aml.
- 프론트 안전장치: lock/unlock·busyRef, 오프라인 폴백(healthRef 분기), paced 타이밍, suppressNotifs, `api.js`의 throw 금지 계약.
- 고정 수치: FX 18.12 / 18.45, 대환 13.59% · 연 246만, AML 컷 40 / 70.
규칙: 작업은 본선 브랜치 `claude/finals-prototype-prep-02e3b6`에서만. 코드를 고치면 `cd frontend && npx vite build`와 `cd backend && pytest -q`를 통과시키고, 깨지면 되돌린다. **7/3 이후는 동결이다. 문서·오탈자만 손댄다.**

## 2. 에이전트 팀 (.claude/agents)
본선 준비는 6에이전트 팀으로 굴린다. finals-orchestrator가 지휘하고 나머지가 일한다.
- **finals-orchestrator** — 검증·개선 라운드를 지휘하고 종합한다.
- **number-auditor** — 모든 수치를 `docs/출처맵.md`·산식·pytest와 대조한다. 폐기 수치 재등장을 잡는다. 수치 파일만 수정할 수 있다.
- **regulation-defender** — 방어 논리를 근거와 1:1로 점검한다. 읽기만 한다.
- **demo-qa** — 시연 런북과 실제 코드 동작 정합을 본다. 읽기만 한다.
- **pitch-scriptwriter** — 검증 통과한 사실로 대본을 쓴다.
- **korean-stylist** — humanize-korean으로 윤문한다. 내용·수치는 안 바꾼다.

흐름: 검증 셋(number·regulation·demo)을 병렬로 돌려 `_workspace/`에 리포트를 쌓는다 → scriptwriter가 반영해 대본을 고친다 → stylist가 윤문한다(최대 2회) → number-auditor 1패스로 수치가 안 깨졌는지 확인한다 → PROGRESS_LOG에 한 줄 남긴다. 에이전트 팀 모드(SendMessage)가 꺼져 있으면 메인 세션이 Task로 순차 실행한다.

## 3. 스킬 (.claude/skills)
- **humanize-korean** — AI 번역투·문어체를 빼고 사람이 말하듯 윤문한다. 대본·문서를 다듬을 때 "AI 티 없애줘", "번역투 제거"로 부른다. korean-stylist가 이 스킬을 쓴다.

## 4. 플러그인
- **harness** (`/plugin`, 레포 settings.json에 선언됨) — 도메인 설명으로 에이전트 팀과 스킬을 생성하는 공장이다. 팀을 새로 뽑거나 갈아엎을 때만 쓴다("하네스 구성해줘"). 한번 생성된 팀은 harness 없이도 돈다. 7/3 이후엔 새 에이전트 생성을 멈춘다.
- **ui-ux-pro-max** (플러그인 `waamengineer-ui-ux-pro-max-skill`, 마켓플레이스 `cascade-content-creation-misc-1`) — 프론트 데모 화면을 다듬는 낮 작업용 디자인 스킬(50+ 스타일, 21 팔레트, 폰트 페어링, 차트 템플릿). **새벽 루틴에는 자동 로딩하지 않는다.** 무인 세션에 외부 코드를 얹을 필요가 없고 비용·리스크만 는다. 낮에 데모를 손볼 때 사람이 직접 켠다.
  - `/plugin marketplace add joshuarweaver/cascade-content-creation-misc-1`
  - `/plugin install waamengineer-ui-ux-pro-max-skill@cascade-content-creation-misc-1`
  - demo-qa가 잡은 표시 문제를 고칠 때 이 스킬로 다듬는다.

## 5. 화법 (docs/화법_가이드.md)
모든 대본·문서는 이 화법으로 쓴다.
- 사람을 주어로, 명사를 동사로, 발표를 설명하지 말고 장면을 시작한다.
- 한 문장 한 메시지, 짧게 끊는다. 형용사 대신 숫자와 장면.
- em dash(—) 금지. 과장·버즈워드·신파 금지. 외국인 노동자는 주체로 둔다.

## 6. 수치 규율
- `docs/출처맵.md`가 모든 수치의 단일 진실이다. 발표·데모·문서가 이와 어긋나면 출처맵 기준으로 맞춘다.
- 단정하는 수치는 1인 연 246만 절약 하나. 거시 수익은 bottom-up 공식과 보수·기준·낙관 시나리오로, "JB 데이터로 확정"으로 둔다.
- 빼야 할 위험 수치 셋: "연 25조"(과장, 실제 5년 누적 25조·연 5조), "사채 연 20~40%"(이자율 미검증), "전환율 7%·잔액 693억·이자 66.5억 단정"(미검증 휴면 20만 기반).
- 추정은 추정으로, 미검증은 미검증으로 표기한다.

## 7. 하루 케이던스
- 낮·밤: 사람과 Claude가 함께 배치 단위로 개선한다. 사람이 산출물 품질을 확인한다.
- 새벽: 클라우드 루틴(`OVERNIGHT_ROUTINE.md`)이 혼자 돈다. 백로그를 전진시키고 검증·개선 라운드를 한 번 돌린다. 컴퓨터는 꺼져 있어도 된다.
- 아침: 사람이 PROGRESS_LOG와 PR diff를 보고 OK 또는 되돌리기를 정한다.

## 8. 문서 인덱스
- 발표: `docs/본선_발표덱.md` · 화법: `docs/화법_가이드.md` · Q&A: `docs/본선_QnA_방어카드.md`
- 수치: `docs/출처맵.md` · 전략 리서치: `docs/본선_리서치_2026-06-27.md` · 실무진: `docs/실무진_공감_분석.md`
- 계획: `docs/본선_개발계획.md` · 팀 설계: `docs/harness_적용안.md`
- 루틴: `OVERNIGHT_ROUTINE.md` · 백로그: `NIGHTLY_BACKLOG.md` · 진행: `PROGRESS_LOG.md`
