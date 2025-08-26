export function nowIso(): string {
  return new Date().toISOString()
}

export function formatHM(d: Date | string | undefined): string {
  if (!d) return ''
  const date = typeof d === 'string' ? new Date(d) : d
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export function formatHMS(d: Date | string | undefined): string {
  if (!d) return ''
  const date = typeof d === 'string' ? new Date(d) : d
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export function formatDurationMs(ms: number): string {
  if (!isFinite(ms) || ms < 0) return ''
  const s = Math.floor(ms / 1000)
  const m = Math.floor(s / 60)
  const sec = s % 60
  if (m > 0) return `${m}m ${sec}s`
  return `${sec}s`
}
