# Streaming API with Semantic Kernel (FastAPI)

Last updated: 2025-08-26

## Overview
This document explains how the backend implements a streaming Chat API using Semantic Kernel (SK) with Azure OpenAI, how the endpoint is exposed via FastAPI, and how it differs from a traditional non‑streaming API.

Key goals:
- Low‑latency, token‑by‑token delivery to the client (better perceived responsiveness)
- Simple wire format (plain chunked text) for easy consumption by web clients
- Resilient design: SK streaming preferred, with a direct OpenAI SDK streaming fallback

## High-level flow
1) Client sends a POST to `/api/chat/stream` with the latest user message, prior history, and optional generation params.
2) Controller (`backend/src/controllers/chat_controller.py`) returns a `StreamingResponse` whose body is an async generator.
3) Service (`backend/src/services/llm_service.py`) attempts Semantic Kernel streaming first; on failure, falls back to the OpenAI SDK’s streaming API.
4) The server yields small text chunks to the client as they arrive from the provider; the client appends them incrementally.

## Contracts
- Endpoint: `POST /api/chat/stream`
- Request body (simplified):
  ```json
  {
    "message": "string",
    "history": [{ "role": "user|assistant", "content": "string" }],
    "options": { "max_tokens": 512, "temperature": 0.2, "top_p": 1.0 }
  }
  ```
- Response headers: `Content-Type: text/plain; charset=utf-8`, `Transfer-Encoding: chunked`, plus `X-Request-ID` for correlation.
- Response body: a sequence of plain text chunks (tokens or small segments). The stream closes when the completion ends or on error.

## Server implementation

### Files of interest
- `backend/src/controllers/chat_controller.py`
  - Wraps the async generator with request ID, timing logs, and graceful error streaming.
- `backend/src/services/llm_service.py`
  - Orchestrates SK streaming first; falls back to OpenAI SDK streaming when SK isn’t available.
- `backend/src/services/kernel_service.py`
  - Configures a Semantic Kernel instance with `AzureChatCompletion`.
- `backend/src/utils/errors.py` and `backend/src/utils/logging.py`
  - Typed errors (`ConfigError`, `UpstreamError`) and structured logging helpers.

### Semantic Kernel streaming
- We use SK’s chat connector for Azure OpenAI (`AzureChatCompletion`).
- Build a `ChatHistory` containing:
  - A system prompt (kept succinct to encourage concise responses)
  - Prior user/assistant messages
  - The latest user message
- Stream deltas using SK’s async streaming API:
  ```py
  async for delta in chat_service.get_streaming_chat_message_contents_async(history, **gen_cfg):
      yield delta.content
  ```
- If SK streaming raises, we log at debug and move to fallback.

### OpenAI SDK fallback (Azure)
- When SK isn’t available or fails, we use the OpenAI Python SDK’s Azure mode with `stream=True`:
  ```py
  stream = await client.chat.completions.create(model=deployment, messages=msgs, stream=True)
  async for event in stream:
      for choice in event.choices:
          if choice.delta and choice.delta.content:
              yield choice.delta.content
  ```

### Controller concerns
- Correlation: each request gets a UUID (`X-Request-ID` header) for tracing.
- Metrics: we log duration and an approximate byte count of streamed data.
- Error handling: service raises typed errors; controller streams concise messages (e.g., `[config error] …`).

## Client implementation (at a glance)
- The webapp uses `fetch` and reads `res.body.getReader()` to append decoded chunks to the UI in real time.
- A `Stop` button aborts the request via `AbortController`.
- Timestamps are attached to messages in the UI (createdAt, startedAt, endedAt) for user/assistant bubbles.

## Streaming vs Non‑Streaming

### What changes in streaming mode
- Response shape: streaming uses plain text chunked transfer; non‑streaming would be a single JSON response.
- Latency: streaming renders partial output immediately; non‑streaming waits for the entire completion to finish.
- UI complexity: streaming needs a reader loop and incremental DOM updates; non‑streaming is a simple `await res.json()`.
- Backpressure/abort: streaming must handle `AbortController` and partial rendering; non‑streaming typically only handles timeout.

### If we didn’t use streaming
- Server:
  - Call SK non‑streaming API (`get_chat_message_contents_async`) or OpenAI SDK without `stream=True`.
  - Return a single JSON payload: `{ content: "full string", usage: {...} }` and status 200.
- Client:
  - `const result = await res.json(); setMessage(result.content)`
  - No chunk loop; no incremental updates.
- Pros:
  - Simpler client code, fewer edge cases.
- Cons:
  - Slower perceived response, especially for long outputs.
  - No opportunity to cancel mid‑response with partial content preserved.

## Edge cases and error modes
- Missing configuration (env): `ConfigError` bubbles to a concise streamed message.
- Upstream service failure: `UpstreamError` yields a short hint; logs capture the full exception.
- Client abort: stream is closed; server logs may show a cancelled connection; UI preserves partial assistant content with an end timestamp.

## How to switch between modes
- Streaming (current):
  - SK: `get_streaming_chat_message_contents_async`
  - OpenAI SDK: `stream=True`
  - Controller returns `StreamingResponse` with an async generator.
- Non‑streaming (alternative):
  - SK: `get_chat_message_contents_async` and return the concatenated text.
  - OpenAI SDK: omit `stream=True`; return full `choices[0].message.content`.
  - Controller returns JSON with `application/json` content type.

## Local run & test (reference)
- Docker Compose: `docker compose up --build`
- Webapp: open http://localhost:5173, send a prompt, observe incremental tokens.
- Stop mid‑stream to confirm abort behavior and assistant end timestamp.

## Notes
- We intentionally use plain chunked text (not SSE) to keep the client simple. If we later need metadata per chunk, we could switch to SSE or JSON lines.
- For production, consider structured logging (JSON), authentication, rate limiting, and surfacing token usage.
