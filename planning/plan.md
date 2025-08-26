# Plan: Streaming Chatbot Demo (FastAPI + Azure OpenAI + Semantic Kernel + React/Vite)

## Objectives
- Build a small, end-to-end demo chatbot with:
  - Backend: FastAPI endpoint that streams responses from Azure OpenAI Chat Completions via Semantic Kernel (Python).
  - Frontend: React (Vite) UI that supports streaming responses as the user chats.
- Keep the design simple, clear, and production-lean: typed contracts, env-driven config, and basic tests.

## High-level Architecture
- Client (Vite + React + TypeScript)
  - Chat UI with message history, input box, send + stop buttons.
  - Uses fetch with ReadableStream to render streaming tokens as they arrive.
- API (FastAPI)
  - Route: POST `/api/chat/stream` that returns a chunked streaming response of model output tokens.
  - Uses Semantic Kernel to orchestrate prompts and an Azure OpenAI Chat Completions deployment for generation.
  - Secured with server-side API keys via environment variables; client never sees Azure keys.
- Azure OpenAI
  - Chat Completions model (deployment) configured in Azure.
  - Streaming enabled to send incremental tokens to the API, which re-streams to the UI.
- Observability
  - Basic logging in API (request id, timing, token usage from response if available).

## Contracts
- Endpoint: `POST /api/chat/stream`
  - Request body (JSON):
    ```json
    {
      "message": "string",
      "history": [
        { "role": "user|assistant|system", "content": "string" }
      ],
      "options": {
        "max_tokens": 512,
        "temperature": 0.2,
        "top_p": 1.0
      }
    }
    ```
  - Response: `text/plain; charset=utf-8` streamed chunks (Transfer-Encoding: chunked). Each chunk is a token or small text segment. The final chunk may include a delimiter like `\n[END]` or end-of-stream closes the connection.
  - Errors: return HTTP error + JSON body (non-stream): `{ "error": { "code": "string", "message": "string" } }`.

Notes:
- We use plain chunked text streaming instead of SSE to allow POST bodies easily and keep client parsing simple.
- If we later want structured streaming, we can switch to SSE (`text/event-stream`) and a small event parser.

## Backend Implementation (FastAPI + Semantic Kernel)

### Tech
- Python 3.11+
- FastAPI, Uvicorn
- Semantic Kernel (Python) for orchestration
- OpenAI SDK with Azure configuration (or azure-ai-openai SDK). We'll use OpenAI Python SDK (1.x) with Azure settings.
- httpx (if needed), pydantic, python-dotenv
- Optional: structlog/logging

### Config (env)
- `AZURE_OPENAI_API_KEY` (required)
- `AZURE_OPENAI_ENDPOINT` (required, e.g., https://<resource>.openai.azure.com)
- `AZURE_OPENAI_DEPLOYMENT` (required; the Chat Completions deployment name)
- `AZURE_OPENAI_API_VERSION` (optional; pinned version known to support streaming)
- `APP_HOST=0.0.0.0`, `APP_PORT=8000` (optional)
- `LOG_LEVEL=INFO` (optional)

### Files and Structure (proposed)
```
src/
  config/
    settings.py            # Pydantic settings for env vars
  schemas/
    chat.py                # Pydantic models for request/response
  services/
    llm_service.py         # Azure OpenAI streaming via OpenAI SDK
    kernel_service.py      # Semantic Kernel setup and integration
  controllers/
    chat_controller.py     # FastAPI route(s), streaming response
  utils/
    logging.py             # Logging setup
  main.py                  # FastAPI app factory and startup
```

### Flow
1. FastAPI receives POST `/api/chat/stream` with `message`, optional `history`, and `options`.
2. Build a Semantic Kernel chat prompt/context (system prompt + history + user message).
3. Call Azure OpenAI via OpenAI SDK with `stream=True` using the configured deployment.
4. For each streamed delta/token from the SDK, yield to the client via `StreamingResponse`.
5. On completion, close the stream. On error, close stream and log; client shows error.

### Pseudocode (controller)
```python
@router.post("/api/chat/stream")
async def chat_stream(payload: ChatRequest):
    generator = llm_service.stream_chat(
        message=payload.message,
        history=payload.history,
        options=payload.options,
    )
    return StreamingResponse(generator, media_type="text/plain")
```

### Pseudocode (service)
```python
async def stream_chat(message, history, options):
    # Prepare SK kernel + prompt based on history and message
    # Call OpenAI with stream=True
    async for token in azure_openai_stream(...):
        yield token
```

### Testing
- Unit test `llm_service` using mocks to simulate streaming iterator.
- Unit test controller to confirm headers and that streaming yields chunks.
- Minimal contract tests for payload validation and error modes.

## Frontend Implementation (Vite + React + TS)

### Tech
- Node 20+, Vite, React 18+, TypeScript
- UI components: minimal, clean styling (CSS modules or Tailwind optional)

### Structure (proposed)
```
ui/
  index.html
  src/
    main.tsx
    App.tsx
    components/
      ChatWindow.tsx
      MessageList.tsx
      ChatInput.tsx
    lib/
      streamClient.ts      # fetch streaming helper
    types/
      chat.ts
```

### Streaming Client Outline
```ts
export async function streamChat(body: ChatRequest, onToken: (t: string) => void, signal?: AbortSignal) {
  const res = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    onToken(decoder.decode(value, { stream: true }));
  }
}
```

### UI Behavior
- Maintain `messages` state: array of `{ role: 'user' | 'assistant' | 'system'; content: string }`.
- On send:
  - Push user message to `messages`.
  - Start `streamChat` with current history; append tokens incrementally to a live assistant message buffer.
  - Provide a Cancel/Stop button wired to an `AbortController`.
- On error: show toast/message; allow retry.

### Styling
- Keep simple: fixed-width container, message bubbles, sticky input at bottom.

## Milestones and Tasks

1) Repo scaffolding
- [x] Add Python project structure under `src/` with FastAPI app
- [x] Adopt Poetry with `pyproject.toml`
- [x] Add `.env.example` with required Azure vars
- [x] Update README with Poetry install/run instructions
- [x] Add `.gitignore` for Python, Poetry, and future UI

2) Backend streaming API
- [x] Define Pydantic schemas (`ChatRequest`, `Message`, `Options`)
- [ ] Implement `llm_service.stream_chat(...)` using OpenAI SDK (Azure)
- [ ] Integrate Semantic Kernel (system prompt + history)
- [x] Implement FastAPI route returning `StreamingResponse`
- [ ] Add basic logging and error handling
- [ ] Unit tests with mocked streaming

3) Frontend UI (Vite + React)
- [ ] Scaffold Vite + React + TS app under `ui/`
- [ ] Implement `streamClient.ts` and types
- [ ] Build `ChatWindow` with `MessageList` + `ChatInput`
- [ ] Wire streaming to append tokens incrementally
- [ ] Add stop/cancel support via `AbortController`
- [ ] Simple styling

4) Integration & polish
- [ ] Configure Vite dev proxy to `/api` for local dev
- [ ] End-to-end smoke test
- [ ] Add README with setup/run instructions
- [ ] Optional: Dockerfile(s) for API and UI, or a single compose

## Risks & Mitigations
- Azure SDK/API version differences
  - Mitigation: pin SDK versions and API version; provide `.env.example`.
- CORS/proxy issues in dev
  - Mitigation: use Vite proxy to backend; configure CORS in FastAPI for production.
- Streaming parsing in client
  - Mitigation: start with plain chunked text; keep tokens small; add SSE later if needed.
- Secrets exposure
  - Mitigation: never expose Azure keys to client; backend-only; use env.

## Deliverables
- Working API that streams model output from Azure OpenAI via SK.
- React UI that displays streaming responses and supports cancel.
- Minimal tests for backend streaming logic.
- README with setup and quick-start.

## Quick-start (planned)
- Backend (dev):
  - Install deps, set `.env`, run FastAPI with Uvicorn.
- Frontend (dev):
  - `npm install` and `npm run dev` with Vite proxy to `/api`.
- Open browser to Vite dev server; chat with the bot; observe streaming.

## Stretch Ideas (later)
- SSE protocol with event types and JSON payloads
- Chat history persistence (SQLite/Postgres)
- Auth (JWT) and per-user rate limits
- Telemetry (OpenTelemetry traces and token usage metrics)
- Multi-turn context with a light memory via SK
