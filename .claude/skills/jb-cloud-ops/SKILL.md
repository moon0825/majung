---
name: jb-cloud-ops
description: 마중 본선 데모 저장소의 PR 검수와 클라우드 작업과 배포 통제를 안전하게 운영하는 표준. PR 검수 게이트(브랜치 체크아웃, 동결 diff 확인, 회귀, 데모 e2e, 두 게이트, 보고), Ultraplan 플랜 리파인과 remote 에이전트 핸드오프, 병렬 polish와 통합 scoring-qa의 gate 워크플로, git과 PR 위생, 배포 스캐폴딩 인지를 정의한다. "PR 검수", "클라우드", "remote", "배포", "gate", "푸시", "머지", "브랜치 점검", "회귀 돌려" 같은 요청에 발동하고, "다시", "보완", "수정", "이전 결과 기반" 같은 후속 요청에도 발동한다. jb-demo-engineer와 총감독(jb-finals)이 공용으로 쓴다. 송금 실행 경로 동결 규칙 자체는 jb-demo-build가, 데모 표시 레이어 빌드는 jb-demo-engineer가 맡으므로 단순 화면 보강 요청에는 발동하지 않는다.
---

# 마중 본선 클라우드·PR 운영 표준 (jb-cloud-ops)

이 스킬은 jb-demo-engineer와 총감독(jb-finals)이 공용으로 쓴다. 마중 데모 저장소(`majung/`, 원격 origin은 github.com/moon0825/majung)에서 PR을 검수하고, 무거운 작업을 클라우드로 넘기며, 외부 푸시와 머지와 배포를 안전하게 통제하는 절차를 정한다. 제1전제는 jb-demo-build와 같다. 송금 실행 경로 로직은 손대지 않고 표시 레이어만 바꾼다. 이 스킬은 그 전제가 PR 단위로도 지켜졌는지를 기계적으로 증명한다.

Why: 클라우드 에이전트와 PR은 빠르다. 그러나 동결 구역을 모르는 변경이 main에 섞이거나 승인 없이 배포되면 무대가 깨지고 채점의 3종 일관성이 무너진다. 되돌리는 비용이 비싼 지점은 사람이 통제 지점을 쥔다. 속도보다 통제가 앞선다.

## 1. PR 검수 게이트 절차

PR은 다음 6단계를 순서대로 통과해야 머지 후보가 된다. 한 단계라도 실패하면 멈추고 차단 사유를 보고한다. 단계를 건너뛰지 않는다. "한 줄짜리라 괜찮다"는 PR도 동일하게 6단계를 거친다.

1. 브랜치 체크아웃. PR 브랜치를 로컬로 가져온다(`git fetch origin && git checkout <branch>`). 작업 트리가 깨끗한지 확인한다. 리뷰는 격리된 워크트리(`majung/.claude/worktrees/`)에서 진행해 현재 작업 브랜치를 오염시키지 않는다.

2. 동결 diff 확인. 송금 실행 경로가 손대졌는지 기계적으로 확인한다.
   ```bash
   git diff main...HEAD -- backend/app/orchestrator.py backend/app/rules.py
   ```
   출력이 공백이어야 통과다. 한 줄이라도 나오면 즉시 차단하고 리더에게 보고한다. 표시 레이어 우회로가 있는지부터 검토한다. Why: 이 두 파일은 LLM을 송금 실행에서 배제하는 3중 게이트의 본체이며 동결 구역이다. api.js의 throw 금지 계약, healthRef 폴백 분기, paced 타이밍, suppressNotifs에 닿는 변경도 같은 기준으로 본다(jb-demo-build 3절).

3. 회귀. 변경이 기존 동작을 깨지 않는지 확인한다.
   - 백엔드: `cd backend && pytest -q`. 20개를 유지한다. 하나라도 줄면 차단한다.
   - 프론트: `cd frontend && npx vite build --outDir /tmp/majung-dist --emptyOutDir`. 윈도우 dist 권한 문제를 피하려 샌드박스 경로로 컴파일만 검증한다.

4. 데모 e2e. 5단계 시나리오(자동 송금, 보류와 STR, 사기 차단, 대환 가심사, 위임 철회)와 유학생 4기능을 6/27 기준 캡처와 대조한다. 백엔드를 띄우고 `/api/health` 녹색등을 확인한 뒤 돌린다.

5. 완성도와 채점 두 게이트. PR이 바꾼 텍스트 산출물(UI 카피, 코드 주석, 문서, 자막)을 두 렌즈로 본다. jb-polish로 AI 티와 직역투와 em dash와 수치 표기를 보고, jb-scoring-qa로 사실과 3종 일관성과 고정 수치와 지뢰를 본다. 두 게이트를 모두 통과해야 한다. Why: 코드 정합은 3단계 회귀가 잡고, 텍스트 완성도와 채점 정합은 두 게이트가 잡는다. 두 렌즈는 서로를 대체하지 않는다.

6. 보고. 결과를 `_workspace/07_pr_review.md`에 정리해 총감독에게 회신한다. 담을 내용은 브랜치명, 동결 diff 공백 여부, pytest 통과 수, vite 빌드 결과, e2e 대조 결과, 두 게이트 판정, 그리고 최종 판정(머지 후보 또는 차단과 사유)이다. 머지는 권고만 하고 실행하지 않는다(4절).

## 2. 클라우드 핸드오프 (Ultraplan과 remote 에이전트)

무거운 작업은 클라우드로 넘긴다. 두 도구를 쓰임에 따라 가른다.

### 2-1. Ultraplan (플랜 리파인)

언제: 작업 범위가 넓거나 모호해 곧장 코드로 들어가면 헛돌 위험이 있을 때. 변경이 여러 파일에 걸치거나, 동결 구역 인접 작업이라 실행 전에 검토된 계획이 필요할 때.

어떻게: 목표와 v2 핵심 제약(동결 구역, 고정 수치, 두 게이트)을 넣어 정제된 플랜을 받는다. 산출물은 코드 변경이 아니라 플랜이다. 받은 플랜을 로컬에서 검토해 동결 구역 침범이 없는지 확인한 뒤에야 실행 단계로 넘긴다. Why: 플랜 리파인은 값싸고, 잘못된 실행을 되돌리는 비용은 비싸다. remote 실행 한 번을 태우기 전에 플랜으로 방향을 고정한다.

### 2-2. remote 에이전트 (Agent isolation:remote)

언제: 시간이 오래 걸리는 작업을 컴퓨터를 꺼 둔 사이에도 진행시키고 싶을 때(예: 야간 표시 레이어 리팩터, 대량 캡처 재생성, 긴 문서 정리).

어떻게:
- remote 격리 모드는 컴퓨터를 꺼도 클라우드에서 계속 돈다. 단 remote 에이전트에게는 저장소만 보인다. 부모 프로젝트의 전략 문서(`D:/JB_Fin_AI/JB_AI Challenge/`의 01~12 문서)와 하네스 스킬과 `_workspace/`는 저장소 밖이라 보이지 않는다.
- 그러므로 v2 핵심을 프롬프트에 자급한다. 프롬프트에 직접 박을 최소 세트는 다음과 같다.
  - 동결 구역 목록: orchestrator.py, rules.py, api.js throw 금지 계약, healthRef 폴백 분기, paced 타이밍, suppressNotifs. 표시 레이어만 손대고 이 영역은 불변.
  - 교차 고정 수치: 환율 7일 평균 18.12 대비 18.45로 1.82% 유리, 사채 대환 연 13.59%로 연 246만 원 절감, AML 임계치 보류 40과 차단 70, 전북은행 점유율 72%와 누적 24만 명.
  - 동결 diff 공백 규칙(1절 2단계)과 회귀 기준(pytest 20개, vite 빌드).
  - 위생 규칙: 브랜치 작업, main 자동머지 금지, 배포 금지, 외부 푸시 전 사용자 확인.
- 권한 한계: remote 에이전트는 브랜치에서 작업하고 그 브랜치를 푸시까지만 한다. 머지와 배포 권한은 주지 않는다. 결과는 로컬에서 1절 PR 검수 게이트로 받은 뒤에야 머지 후보가 된다.

Why: remote의 강점은 지속성이고 약점은 좁은 시야다. 시야는 프롬프트로 메우고, 결과는 반드시 게이트로 거른다. 저장소만 보는 에이전트에게 동결 구역을 알리지 않으면 송금 경로를 건드린 PR이 돌아온다.

## 3. gate 워크플로 패턴 (병렬 polish, 통합 scoring-qa)

PR이 여러 산출물을 바꿨으면 게이트를 다음 형태로 돌린다.

- polish는 병렬로. 산출물 하나하나의 완성도와 AI 티는 서로 독립적이므로, 바뀐 산출물마다 jb-polish를 병렬로 돌린다. 각 판정은 `_workspace/_gate/{artifact}.verdict.md`에 남긴다.
- scoring-qa는 통합으로. 고정 수치의 3종 일관성은 산출물 하나만 봐서는 잡히지 않는다. 모든 변경분을 한데 모아 jb-scoring-qa를 한 번에 돌려 교차 일관성과 지뢰를 본다. 결과는 `_workspace/06_scoring_report.md`에 합친다.

Why: polish의 렌즈는 산출물 단위(이 글이 사람답게 읽히는가)라 병렬이 효율적이고, scoring-qa의 렌즈는 변경 전체 단위(같은 수치가 모든 파일에서 토씨까지 같은가)라 통합이 정확하다. 반대로 묶으면 파일 사이에 흩어진 일관성 오류를 놓친다.

## 4. git과 PR 위생

저장소는 `majung/`(원격 origin = github.com/moon0825/majung)이다. 다음을 어기지 않는다.

- 브랜치에서만 작업한다. main에 직접 커밋하지 않는다. 작명은 기존 관례(feat/*, claude/*)를 따른다.
- main 자동머지 금지. main 머지는 사람의 판단이다. 두 게이트와 회귀를 통과해도 스킬이 자동으로 머지하지 않는다. 게이트는 머지 후보를 만들 뿐이다.
- 배포 금지. fly deploy, render 트리거, GitHub Pages 발행을 사용자 지시 없이 실행하지 않는다. 배포 스캐폴딩은 준비 상태로만 유지한다(5절).
- 커밋 메시지 끝에 Co-Authored-By trailer를 붙인다.
  ```
  Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
  ```
- 외부 푸시 전 사용자 확인. origin으로 푸시하기 전에 무엇을 어느 브랜치로 올리는지 사용자에게 확인받는다. 로컬 커밋과 워크트리 작업은 자유롭게 하되, 저장소 밖으로 나가는 순간이 확인 지점이다.

Why: 클라우드와 자동화는 빠르지만 main과 배포와 원격 푸시는 되돌리기 비싼 외부 효과를 낳는다. 통제 지점을 사람이 쥐어야 무대 직전에 사고가 새어 나오지 않는다.

## 5. 배포 스캐폴딩 인지

저장소에는 라이브 데모 링크용 배포 스캐폴딩이 이미 있다. 채점 4.2(실동작 MVP, GitHub 공개 레포와 라이브 데모)의 증거를 만들기 위한 것이다. 스킬은 이를 건강하게 유지하되 발행은 사용자 확인 뒤에만 한다.

| 파일 | 용도 |
|---|---|
| `Dockerfile`, `.dockerignore` | 단일 오리진 컨테이너(주 데모). 부팅 시 asgi.py가 seed로 재시드 |
| `fly.toml` | Fly.io 배포 |
| `render.yaml` | Render Blueprint. branch가 현재 feat/* 이므로 main 머지 후 main으로 변경 권고 |
| `.github/workflows/pages.yml` | GitHub Pages 정적 백업 URL(오프라인 미리보기 목 모드) |
| `DEPLOY.md` | 두 갈래 배포 절차와 시연 런북 |

아키텍처 사실 두 가지를 기억한다. 첫째, asgi.py가 기존 API 앱을 `/api`에 마운트하고 빌드된 SPA를 `/`에 서빙하므로 같은 오리진이라 CORS가 없고, main.py와 orchestrator.py와 rules.py는 마운트만 추가될 뿐 무수정이다. 둘째, 컨테이너는 `base="/"`로, Pages는 `VITE_BASE=/majung/`로 빌드한다. 배포 PR을 검수할 때 이 두 사실이 깨졌는지부터 본다.

Why: 라이브 데모 링크는 자가평가 88점 경계선에서 남은 실점 위험이 몰린 4.2 항목의 증거다. 스캐폴딩이 죽지 않게 지키는 것이 곧 채점 방어다.

## 6. 입력과 출력, 형제 스킬, 학습 루프

- 읽기: `_workspace/00_show_spec.md`(고정 수치 단일 진실), `majung/DEPLOY.md`, `majung/OVERNIGHT_ROUTINE.md`, `.claude/skills/jb-demo-build/SKILL.md`(동결 구역 단일 기준), `.claude/jb-learnings.md`.
- 쓰기: `_workspace/07_pr_review.md`(PR 검수 보고). 게이트 판정은 jb-polish와 jb-scoring-qa의 기존 경로(`_workspace/_gate/`, `_workspace/06_scoring_report.md`)에 합류한다.
- 형제 스킬: 동결 구역과 표시 레이어 빌드는 jb-demo-build, 완성도 게이트는 jb-craft-standard와 jb-polish, 채점과 일관성은 jb-scoring-rubric, 어체는 fin-biz-tone, 전체 지휘는 jb-finals. 노션에 자료를 옮길 때의 작성 함정은 `references/notion-writing.md`를 본다.
- 학습 루프: 작업 전 `.claude/jb-learnings.md`를 읽어 기록된 PR과 클라우드 실수를 처음부터 피한다. 작업 후 새로 잡은 동결 침범, 게이트 누락, 푸시 사고를 분류 `클라우드`로 한 줄 추가한다. 같은 사고가 두 번 이상 잡히면 본 스킬의 규칙으로 승격을 제안한다. 이전 PR 검수가 있으면 전체를 다시 보지 않고 바뀐 부분만 회귀로 본다.

이 문서 자체도 두 게이트 기준을 지킨다. AI 지문이나 직역투, em dash가 보이면 즉시 고친다.
