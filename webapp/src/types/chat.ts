export type Role = 'user' | 'assistant' | 'system'

export interface Message {
  role: Role
  content: string
  // timestamps
  createdAt?: string // ISO timestamp when the message was created (user & assistant)
  startedAt?: string // ISO timestamp when assistant streaming started
  endedAt?: string   // ISO timestamp when assistant streaming ended
}

export interface ChatOptions {
  max_tokens?: number
  temperature?: number
  top_p?: number
}

export interface ChatRequest {
  message: string
  history?: Message[]
  options?: ChatOptions
}
