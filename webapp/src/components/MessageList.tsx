import type { Message } from '../types/chat'

export function MessageList({ messages }: { messages: Message[] }) {
  return (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {messages.map((m, i) => (
        <div
          key={i}
          style={{
            alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
      background: m.role === 'user' ? '#10305a' : '#0b152b',
      border: '1px solid #1e293b',
      borderRadius: 12,
      padding: '10px 12px',
      maxWidth: 'min(680px, 100%)',
            whiteSpace: 'pre-wrap',
          }}
        >
          {m.content}
        </div>
      ))}
    </div>
  )
}
