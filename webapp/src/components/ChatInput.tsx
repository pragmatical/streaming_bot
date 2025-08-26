import { useEffect, useRef, useState } from 'react'

interface Props {
  onSend: (text: string, controller: AbortController) => void
  isStreaming: boolean
  onStop: () => void
}

export function ChatInput({ onSend, isStreaming, onStop }: Props) {
  const [text, setText] = useState('')
  const controllerRef = useRef<AbortController | null>(null)

  useEffect(() => {
    return () => controllerRef.current?.abort()
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim() || isStreaming) return
    const controller = new AbortController()
    controllerRef.current = controller
    onSend(text.trim(), controller)
    setText('')
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8 }}>
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Ask something..."
        disabled={isStreaming}
        style={{ flex: 1, padding: '8px 12px' }}
      />
      {isStreaming ? (
        <button
          type="button"
          onClick={() => {
            controllerRef.current?.abort()
            onStop()
          }}
        >
          Stop
        </button>
      ) : (
        <button type="submit" disabled={!text.trim()}>
          Send
        </button>
      )}
    </form>
  )
}
