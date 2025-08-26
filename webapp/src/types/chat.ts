export type Role = 'user' | 'assistant' | 'system'

export interface Message {
  role: Role
  content: string
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
