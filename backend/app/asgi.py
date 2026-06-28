"""배포용 단일 오리진 ASGI 진입점.

개발에서는 vite dev 서버가 `/api`를 :8000으로 프록시한다(경로 rewrite로 `/api` 제거).
배포(컨테이너)에서는 프록시가 없으므로, 여기서 기존 API 앱을 `/api`에 마운트하고
빌드된 프론트 정적 파일을 `/`에 서빙해 같은 오리진에서 동작시킨다.

- `/api/health`, `/api/chat`, … → main.app(루트 라우트)로 위임(경로에서 `/api` 제거)
- `/` 및 그 외 → 빌드된 SPA(index.html)

main.py·orchestrator.py·rules.py 등 동결/기존 코드는 수정하지 않는다(마운트만 추가).
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .db import DB_PATH
from .main import app as api_app
from .seed import seed

root = FastAPI(title="마중(Majung) 배포 — 단일 오리진", version="0.1.0")


@root.on_event("startup")
def _ensure_seed() -> None:
    """컨테이너 부팅 시 DB가 없으면 데모 데이터를 시드한다(재현 가능·멱등)."""
    if not DB_PATH.exists():
        seed()


# 기존 API 앱을 /api 에 마운트 → 프론트의 BASE="/api" 와 일치
root.mount("/api", api_app)

# 빌드된 프론트 정적 파일 서빙(있을 때만). Dockerfile이 /app/static 으로 복사한다.
_STATIC_DIR = os.environ.get("MAJUNG_STATIC", "/app/static")
if os.path.isdir(_STATIC_DIR):
    # html=True → "/" 에서 index.html, 정적 자산은 그대로 제공
    root.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
