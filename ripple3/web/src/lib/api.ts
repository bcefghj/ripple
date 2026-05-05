export interface ThinkingStep {
  step: string
  detail: string
  progress: number
  agents?: AgentStatus[]
}

export interface AgentStatus {
  name: string
  status: 'pending' | 'running' | 'done'
  count?: number
}

export interface Citation {
  title: string
  url: string
  snippet?: string
}

export interface SSEMessage {
  type: 'thinking' | 'content' | 'sources' | 'done' | 'error'
  data: any
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  thinking?: ThinkingStep[]
  sources?: Citation[]
  isStreaming?: boolean
}

export async function* streamChat(
  message: string,
  history: ChatMessage[],
  session: Record<string, string>,
): AsyncGenerator<SSEMessage> {
  const body = {
    message,
    history: history.map(m => ({ role: m.role, content: m.content })),
    session,
  }

  const resp = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!resp.ok) {
    yield { type: 'error', data: { message: `HTTP ${resp.status}` } }
    return
  }

  const reader = resp.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    let currentEvent = ''
    let currentData = ''

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim()
      } else if (line.startsWith('data: ')) {
        currentData = line.slice(6)
        if (currentEvent && currentData) {
          try {
            const parsed = JSON.parse(currentData)
            yield { type: currentEvent as SSEMessage['type'], data: parsed }
          } catch {
            // skip malformed JSON
          }
          currentEvent = ''
          currentData = ''
        }
      } else if (line === '') {
        currentEvent = ''
        currentData = ''
      }
    }
  }
}
