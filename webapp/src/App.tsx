import { useEffect, useMemo, useRef, useState } from 'react'
import { MessageList } from './components/MessageList'
import { ChatInput } from './components/ChatInput'
import { streamChat } from './lib/streamClient'
import type { Message } from './types/chat'
import { nowIso } from './lib/time'

export default function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const liveIndexRef = useRef<number | null>(null)
  const scrollRef = useRef<HTMLDivElement | null>(null)

  const history = useMemo(
    () => messages.filter((m) => m.role !== 'system'),
    [messages],
  )

  const handleSend = async (text: string, controller: AbortController) => {
    setError(null)
    setIsStreaming(true)
    // push user message and an empty assistant message we'll fill as tokens arrive
    const createdAt = nowIso()
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: text, createdAt },
      { role: 'assistant', content: '', createdAt },
    ])
    liveIndexRef.current = messages.length + 1 // index of the placeholder assistant message
    try {
      await streamChat(
        {
          message: text,
          history: history,
          options: { temperature: 0.2, max_tokens: 512 },
        },
        (chunk) => {
          setMessages((prev) => {
            const idx = liveIndexRef.current
            if (idx == null || idx >= prev.length) return prev
            const next = [...prev]
            const msg = next[idx]
            next[idx] = {
              ...msg,
              content: msg.content + chunk,
              startedAt: msg.startedAt ?? nowIso(),
            }
            return next
          })
        },
        controller.signal,
      )
    } catch (e: any) {
      setError(e?.message || 'Request failed')
    } finally {
      setIsStreaming(false)
      // set endedAt for the assistant message when stream finishes (or stops)
      setMessages((prev) => {
        const next = [...prev]
        for (let i = next.length - 1; i >= 0; i--) {
          const msg = next[i]
          if (msg.role === 'assistant' && !msg.endedAt) {
            next[i] = {
              ...msg,
              endedAt: nowIso(),
              startedAt: msg.startedAt ?? msg.createdAt ?? nowIso(),
            }
            break
          }
        }
        return next
      })
      liveIndexRef.current = null
    }
  }

  const handleStop = () => {
    // AbortController handled in ChatInput
    setIsStreaming(false)
  }

  useEffect(() => {
    // auto-scroll to bottom on new messages
    const el = scrollRef.current
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  }, [messages])

  return (
    <div className="app">
      <div className="container">
        <div className="header">Streaming Bot</div>
        {error && <div style={{ color: 'crimson' }}>{error}</div>}
        <div className="chat-window" ref={scrollRef}>
          <MessageList messages={messages} />
        </div>
        <div className="footer">
          <div className="input-row">
            <ChatInput onSend={handleSend} isStreaming={isStreaming} onStop={handleStop} />
          </div>
        </div>
      </div>
    </div>
  )
}
