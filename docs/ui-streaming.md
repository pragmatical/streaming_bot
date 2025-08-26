# UI Streaming (Vite + React)

Last updated: 2025-08-26

## Overview
This document describes how the web app consumes the backend streaming API and renders tokens incrementally in the chat UI. The client reads a chunked plain-text stream from `POST /api/chat/stream` and appends content to the current assistant message in real time. A Stop button cancels the in-flight request.

Goals:
- Low-latency rendering as tokens arrive
- Simple implementation built on `fetch` + `ReadableStream`
- Clean UX: typing indicator, timestamps, cancel support, and auto-scroll

## Files of interest
- `webapp/src/lib/streamClient.ts`
  - `streamChat(body, onToken, signal)` performs `fetch('/api/chat/stream')` and iterates `res.body.getReader()`.
  - Uses `TextDecoder` to convert Uint8Array chunks into text and calls `onToken` for each chunk.
  - Abides by `AbortSignal` for cancellation.

- `webapp/src/App.tsx`
  - Top-level state and orchestration:
    - `messages: Message[]` (user + assistant turns)
    - `isStreaming`, `error`
    - `liveIndexRef` points to the current assistant placeholder during streaming
    - `scrollRef` auto-scrolls the chat window on updates
  - Flow on send:
    1. Push a user message with `createdAt`.
    2. Push an empty assistant message placeholder (will be filled as tokens arrive).
    3. Call `streamChat(...)` with an `onToken` handler.
    4. In `onToken`, append to assistant content and set `startedAt` on the first token.
    5. When the stream completes (or is stopped), set `endedAt`.
  - Robust end-time logic: on completion, the code finds the last assistant message with no `endedAt` and assigns end time, ensuring resiliency.

- `webapp/src/components/ChatInput.tsx`
  - Renders the input bar (full-width) with Send and Stop buttons.
  - Manages an `AbortController` to cancel the current stream when Stop is clicked.

- `webapp/src/components/MessageList.tsx`
  - Displays user and assistant bubbles with timestamps:
    - User: shows `createdAt` in `HH:mm` and ISO tooltip
    - Assistant: shows `Started HH:mm:ss • Ended HH:mm:ss • Duration Xm Ys` when complete; shows `Started … • …` while streaming
  - Shows an animated three-dot typing indicator in the assistant bubble before the first chunk arrives.

- `webapp/src/lib/time.ts`
  - Helpers for `nowIso()`, `formatHM()`, `formatHMS()`, and `formatDurationMs()`.

- `webapp/src/styles.css`
  - Full-height flex layout, responsive padding, dark theme palette
  - Scrollable `.chat-window` with `overflow-y: auto` so input stays visible at bottom
  - `.input-row` for a tall, full-width input bar
  - `.typing` three-dot animation for assistant pre-stream indicator

- `webapp/vite.config.ts`
  - Dev server proxy for `/api` pointing to `VITE_API_BASE` (Compose sets `http://backend:8000`).

## Data model (frontend)
```ts
export type Role = 'user' | 'assistant' | 'system'
export interface Message {
  role: Role
  content: string
  createdAt?: string // user & assistant
  startedAt?: string // assistant streaming start
  endedAt?: string   // assistant streaming end
}
```

History is sent to the backend with each new user message; the assistant placeholder is filled as chunks stream back.

## Streaming flow (client)
1. User clicks Send
2. UI pushes a user message (with `createdAt`) and an empty assistant message
3. `streamChat` POSTs to `/api/chat/stream` and yields chunks
4. On each chunk:
   - Append to the assistant message content
   - Set `startedAt` if not already set
5. On completion (or Stop): set `endedAt`

## Error handling
- If the HTTP response is not OK (e.g., config error), `streamChat` throws with the response text when available.
- Server may also stream concise error messages as plain text; these will render like normal content if sent as chunks.
- The UI shows an error banner and leaves any partial content intact if the request is aborted.

## UX and accessibility
- Input bar remains fixed at the bottom; the chat area scrolls.
- Auto-scroll follows content as it streams; we could add a sticky behavior toggle if desired.
- Buttons expose disabled states while streaming.
- Typing indicator has an `aria-label` ("Assistant is typing").

## Non-streaming alternative (UI)
- Use `await fetch('/api/chat').then(r => r.json())` and set the assistant message content in one update.
- No reader loop; no `AbortController` needed.
- Simpler, but users wait longer before seeing the first characters of the response and cannot cancel mid-way with partial output preserved.

## Run locally
- Using Docker Compose:
  - `docker compose up --build`
  - Open http://localhost:5173
  - Send a message and watch the assistant bubble fill in with tokens, then show start/end timestamps and duration.

## Edge cases
- Very short responses: `startedAt` and `endedAt` may be seconds apart; UI still shows a small duration.
- Aborted before first chunk: we backfill `startedAt` from `createdAt` on completion to ensure Start/End render consistently.
- Multiple sends quickly: the `isStreaming` flag prevents concurrent sends; the last assistant placeholder is closed out with an end time on completion.

## Next steps
- Optional: sticky auto-scroll toggle when the user manually scrolls up
- Optional: a small toast when an error chunk is detected, separate from normal content
- Optional: tests for time formatters and the chunk-append logic
