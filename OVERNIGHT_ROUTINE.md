# 야간 자동 개발 루틴 (마중 / JB 본선)

> 야간에 자동 실행되는 Claude Code(또는 Cowork) 세션이 그대로 따르는 작업 지침.
> 목적: 발표일(7/4~5) 전까지 매일 밤 백로그를 1~2건씩 안전하게 전진시킨다.
> 이 파일을 세션 프롬프트로 그대로 넣는다.

## 0. 절대 규칙 (위반 시 즉시 중단)
- 동결 구역 수정 금지: 게이트 판정(Gate A/B/C 순서·단일 실행 경로), lock/unlock·busyRef, 오프라인 폴백(healthRef 분기), paced 타이밍, suppressNotifs, api.js의 throw 금지 계약, 교차 고정 수치(FX 18.12/18.45, 대환 13.59%·연 246만, AML 컷 40/70).
- main 브랜치에 직접 커밋·푸시 금지. 모든 야간 작업은 nightly 브랜치에서만.
- 매 항목 후 빌드/테스트 통과를 반드시 확인. 실패하면 그 변경을 폐기하고 다음 항목으로.
- 새 작업은 표시 레이어·문서·테스트 중심. 송금 실행 경로 로직은 손대지 않는다.

## 0-B. 중복 방지 (매 실행 최우선 — 이 단계를 건너뛰지 마라)

매 세션 시작 시 아래 순서를 반드시 실행한다. **이미 된 일을 또 하지 않는 게 가장 중요하다.**

1. `git fetch origin main` → origin/main 최신화
2. `git log origin/main --oneline --since="14 days ago"` 출력 저장
3. `gh pr list --state open --json headRefName,title 2>/dev/null` (또는 GitHub MCP) 로 오픈 PR 목록 확인
4. NIGHTLY_BACKLOG.md의 각 미완료(- [ ]) 항목에 대해:
   - 최근 커밋 메시지에 항목 키워드(예: "E-9 페르소나", "계열사 시너지", "Q&A 방어")가 있으면 → **이미 완료로 간주, 백로그에서 [x] 처리 후 건너뜀**
   - 같은 키워드로 오픈 PR이 이미 존재하면 → **해당 PR 번호를 PROGRESS_LOG에 기록하고 건너뜀. 새 PR 절대 금지.**
5. 위 두 조건 모두 해당 없는 항목만 이번 세션에서 작업 대상으로 삼는다.
6. 작업 대상이 0건이면 → PROGRESS_LOG에 "중복 없음, 이번 세션 작업 없음" 기록 후 **즉시 종료**.

## 1. 매 실행 절차

1. origin/main 최신화 후 작업 브랜치 생성: `git fetch origin main && git checkout -b nightly-$(date +%Y%m%d) origin/main`  
   (시스템이 브랜치 이름을 자동 배정하는 환경이면 그 이름을 사용하되, **항상 origin/main 기준으로 시작**한다)
2. 0-B 중복 방지 체크 실행. 작업 대상 항목 선정 (최대 2건, 위험도 높음·보류 건너뜀).
3. 구현. 동결 구역 회피.
4. 검증:
   - 프론트: `cd frontend && npm install --prefer-offline && npx vite build --outDir /tmp/nightly-build --emptyOutDir`
   - 백엔드: `cd backend && python3 -m pytest -q`
   - 하나라도 실패하면 `git checkout -- .` 로 되돌리고 PROGRESS_LOG에 '실패·보류' 기록.
5. PROGRESS_LOG.md 맨 위에 한 줄 추가: 날짜 · 항목 · 결과 · 검증 · 다음 제안.
6. 백로그 항목 `- [ ]` → `- [x]`, 커밋: `git add -A && git commit -m "nightly: <항목 요약>"`
7. 푸시 후 **draft PR 1개** 생성. 이미 오픈 PR이 있으면 PR을 새로 만들지 않는다.
8. 정지 조건 전까지 2~7 반복.

## 2. 정지 조건
- 빌드 또는 테스트가 2회 연속 실패
- 진행하려면 동결 구역을 건드려야 하는 항목만 남음
- 백로그 미완료 항목 소진 (0-B 체크 후 기준)
- 최대 턴/시간 예산 도달

## 3. 예산 (토큰·시간)
- 1회 실행 1~2 항목. 과도한 코드베이스 탐색 금지. 라이브러리 추가·대규모 리팩터 금지.
- 권장 max-turns 40 내외. 더 필요하면 다음 밤으로 미룬다.
- 큰 작업은 여러 밤으로 쪼갠다.

## 4. 아침 인수인계
- PROGRESS_LOG.md 최신 항목 = 사람이 가장 먼저 읽는 곳.
- draft PR diff를 사람이 리뷰 후 main 머지. **머지 즉시 백로그가 업데이트되어 다음 세션이 중복 작업을 하지 않는다.**
- 머지 후 오래된 claude/* 브랜치는 삭제해도 안전하다.
