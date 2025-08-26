import type { ChatRequest } from '../types/chat'

export async function streamChat(
  body: ChatRequest,
  onToken: (t: string) => void,
  signal?: AbortSignal,
) {
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })

  if (!res.ok || !res.body) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `HTTP ${res.status}`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value, { stream: true })
      if (chunk) onToken(chunk)
    }
  } finally {
    reader.releaseLock()
  }
}
