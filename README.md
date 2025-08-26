# streaming_bot

Streaming chatbot demo scaffold.

## Project structure

```
backend/      # FastAPI app (Python + Poetry)
webapp/       # Vite + React UI
docker-compose.yml
```

## Run with Docker Compose

1) Create `.env` at repo root (copy from `.env.example`).
2) Build and start services:

```bash
docker compose up --build
```

Services:
- Backend: http://localhost:8000
- Webapp:  http://localhost:5173

The webapp proxies `/api` to the backend in dev.

## Backend dev (without Docker)

```
cd backend
poetry install
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## Webapp dev (without Docker)

```
cd webapp
npm install
npm run dev -- --host
```
