# 마중(Majung) 데모 배포 가이드

시연 안정성을 위한 두 갈래 배포.

| 방식 | 백엔드 | 용도 | 비용 |
|---|---|---|---|
| **단일 오리진 컨테이너** (Render·Fly·로컬 Docker) | 실시간 3중 게이트 | **주 데모** | 무료 플랜 가능 |
| **GitHub Pages** (정적) | 미동작(오프라인 미리보기·목) | **백업 URL** | 무료 |

아키텍처: `backend/app/asgi.py`(`root`)가 기존 API 앱을 `/api`에 마운트하고, 빌드된 프론트 SPA를 `/`에 서빙한다. 같은 오리진이라 CORS·프록시가 없고, `main.py`·`orchestrator.py`·`rules.py`는 무수정(마운트만 추가).

---

## A. 단일 오리진 컨테이너 (실시간 백엔드)

### A-1. 로컬 Docker — 행사장 인터넷 의존 0, 가장 안정적
```bash
docker build -t majung-demo .
docker run --rm -p 8000:8000 majung-demo
# → http://localhost:8000  (부팅 시 DB 자동 시드)
```

### A-2. Render (Blueprint)
1. Render 대시보드 → **New → Blueprint** → 이 저장소 선택 → `render.yaml` 자동 인식.
2. 배포 후 URL 확인. `render.yaml`의 `branch`는 현재 `feat/majung-v2-student-segment` — main 머지 후 `main`으로 변경 권장.
3. 무료 플랜은 콜드스타트가 있으니 **시연 직전 `/api/health` 1회 호출로 워밍업**.

### A-3. Fly.io
```bash
fly launch --no-deploy --copy-config   # app 이름은 본인 것으로
fly deploy
fly open                                # 배포 URL 열기
```

> 모든 컨테이너 방식은 부팅 시 `asgi.py`의 startup 훅이 `seed()`로 데모 데이터를 재시드한다(멱등). 재시연 시 컨테이너 재시작만으로 초기화.

### 동작 검증
```bash
curl -s https://<배포-URL>/api/health        # {"status":"ok","service":"majung"}
# 브라우저: 근로자 5단계 + 유학생 ①~④ + 관리자 대시보드
```

---

## B. GitHub Pages (백업, 정적)

main 브랜치에 `.github/workflows/pages.yml`가 있으면 **main 푸시 시 자동 배포**되거나, Actions 탭에서 **Deploy demo to GitHub Pages → Run workflow**로 수동 실행한다.

- URL: `https://moon0825.github.io/majung/`
- 정적이라 백엔드 미동작 → 헬스체크 실패 → **오프라인 미리보기(목 데이터)** 모드. 카드·게이트·유학생 4기능 클릭 시연은 그대로 가능(실행 판정만 시드 기준 목).
- 서브패스(`/majung/`) 자산 경로 때문에 `VITE_BASE=/majung/`로 빌드한다(워크플로에 설정됨).

> 컨테이너 배포는 기본 `base="/"`, Pages는 `VITE_BASE=/majung/`. `vite.config.js`가 환경변수로 분기한다.

---

## 시연 런북(요약)
1. (주) 컨테이너 URL `/api/health` 워밍업 → 근로자·유학생 탭 전체 클릭.
2. (백업) Pages URL을 다른 탭에 미리 열어둠 — 주 데모 장애 시 즉시 전환.
3. 재시연: 컨테이너 재시작(자동 재시드) 또는 브라우저 새로고침.
