# 마중(Majung) 데모 — 단일 오리진 컨테이너.
# 프론트(Vite)를 빌드해 정적 파일로 굽고, FastAPI(asgi:root)가 /api + 정적 SPA를 함께 서빙한다.
# 같은 오리진이라 CORS·프록시 없이 동작하며, 실시간 3중 게이트가 그대로 돈다.

# ── stage 1: 프론트 빌드 (base="/" 기본) ──
FROM node:20-slim AS frontend
WORKDIR /fe
COPY frontend/package*.json ./
RUN npm ci 2>/dev/null || npm install
COPY frontend/ ./
RUN npm run build

# ── stage 2: 백엔드 + 정적 ──
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MAJUNG_STATIC=/app/static
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt
COPY backend/ ./
COPY --from=frontend /fe/dist ./static
EXPOSE 8000
# Render/Fly 등은 $PORT 를 주입한다. 부팅 시 asgi 의 startup 훅이 DB를 시드한다.
CMD ["sh", "-c", "uvicorn app.asgi:root --host 0.0.0.0 --port ${PORT:-8000}"]
