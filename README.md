# streaming_bot

Streaming chatbot demo scaffold.

## Backend quick-start (Poetry)

1) Create and populate `.env` from `.env.example`.
2) Install Poetry dependencies.

```bash
poetry install
```

3) Run the dev server.

```bash
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

FastAPI will run on http://localhost:8000
