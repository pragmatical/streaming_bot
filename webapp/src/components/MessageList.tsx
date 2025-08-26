import type { Message } from '../types/chat'
import { formatHM, formatHMS, formatDurationMs } from '../lib/time'

export function MessageList({ messages }: { messages: Message[] }) {
  return (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {messages.map((m, i) => {
        const created = m.createdAt ? new Date(m.createdAt) : undefined
        const started = m.startedAt ? new Date(m.startedAt) : undefined
        const ended = m.endedAt ? new Date(m.endedAt) : undefined
        const duration = started && ended ? formatDurationMs(ended.getTime() - started.getTime()) : ''
        const timeLabel = created ? formatHM(created) : started ? formatHM(started) : ''

        return (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: 4, alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div
              style={{
                background: m.role === 'user' ? '#10305a' : '#0b152b',
                border: '1px solid #1e293b',
                borderRadius: 12,
                padding: '10px 12px',
                maxWidth: 'min(680px, 100%)',
                whiteSpace: 'pre-wrap',
              }}
              title={created?.toISOString() || started?.toISOString() || ''}
            >
              {m.role === 'assistant' && !m.startedAt && !m.content ? (
                <span className="typing" aria-label="Assistant is typing">
                  <span />
                  <span />
                  <span />
                </span>
              ) : (
                m.content
              )}
            </div>
            <div style={{ fontSize: 12, color: '#94a3b8' }}>
              {m.role === 'assistant' && started ? (
                ended ? (
                  <>Started {formatHMS(started)} • Ended {formatHMS(ended)} • Duration {duration}</>
                ) : (
                  <>Started {formatHMS(started)} • …</>
                )
              ) : (
                <>{timeLabel}</>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
