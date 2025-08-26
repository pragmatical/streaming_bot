# Streaming Bot – Features and Requirements

Last updated: 2025-08-26

## Overview
This document tracks features for the application. Checked items are implemented and verified in the codebase.

## Features (Flat List)
- [x] Backend FastAPI endpoint streams responses as plain text chunks: `POST /api/chat/stream`
- [x] Semantic Kernel integration (AzureChatCompletion) with SK-first streaming and OpenAI SDK fallback
- [x] Env-driven configuration via `backend/.env` (Azure settings, log level, app host/port)
- [x] CORS enabled for development
- [x] Logging and error handling
  - [x] Request ID added per request and returned as `X-Request-ID`
  - [x] Timings and token byte count logged; typed errors surfaced as friendly text in stream
- [x] Containerization and orchestration: Dockerfiles for backend/webapp + `docker-compose.yml`
- [x] Frontend (Vite + React + TypeScript) with streaming UI
  - [x] Streaming client that reads `ReadableStream` and appends chunks in real time
  - [x] Stop/Cancel via `AbortController`
  - [x] Responsive layout; scrollable chat window; input anchored at bottom
  - [x] Error display on request failure
- [x] Timestamp on all chat bubbles
  - Show when the message was written/emitted (local time). Display format: `HH:mm` (e.g., 14:07) with a tooltip for full ISO timestamp
  - Applies to roles: `user`, `assistant`
- [x] For assistant messages, capture and display streaming timing
  - Record `startedAt` when an assistant message begins printing/streaming
  - Record `endedAt` when the message finishes
  - Display as: `Started HH:mm:ss • Ended HH:mm:ss • Duration Xm Ys`

Notes:
- Times should use the browser’s local timezone for display; store as ISO 8601 strings internally.
- When a message is streaming, show a live “Started … • …” state, and fill `Ended`/Duration when complete.

## Acceptance Criteria
1) Timestamp on all chat bubbles
   - Given any message appears in the conversation, then below the message bubble there is a small, muted timestamp (e.g., `14:07`) and a tooltip reveals the full ISO timestamp.

2) Assistant message start/end timestamps
  - Given an assistant message streams to the UI, when it starts, the UI records `startedAt` and renders “Started HH:mm:ss”
  - When streaming completes, the UI sets `endedAt` and renders “Started … • Ended … • Duration …”

3) Accessibility and resilience
   - Timestamps are readable with sufficient contrast, and the UI gracefully handles missing timestamps (e.g., legacy messages without time metadata).

## Implementation Notes
Data model updates (frontend):
```ts
type Role = 'user' | 'assistant' | 'system'
interface Message {
  role: Role
  content: string
  // new fields
  createdAt?: string      // ISO timestamp for when message was created (user & assistant)
  startedAt?: string      // streaming start (assistant only)
  endedAt?: string        // streaming end (assistant only)
}
```

UI rendering:
- Show a small, muted timestamp row under each bubble:
  - Prefer `createdAt` if present; otherwise show `startedAt`/`endedAt` per role
- For streaming messages, update `endedAt` upon stream completion and compute a simple duration

Controller/service (optional):
- If we want server-authoritative times, add headers (e.g., `X-Started-At`, `X-Ended-At`) or embed JSON “meta” prelude in the stream; otherwise, client times are sufficient for the demo

Testing:
- Unit test message timestamp formatting and duration calculation
- Integration test that simulates streaming and verifies `startedAt` is set at first chunk and `endedAt` at completion
