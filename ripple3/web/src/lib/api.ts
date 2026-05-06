export interface ThinkingStep {
  step?: string
  label?: string
  text?: string
  detail?: string
  progress?: number
  status?: string
  type?: string
  id?: string
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

export interface GraphNode {
  id: string
  name: string
  type: string
  val: number
  color: string
  desc?: string
}

export interface GraphLink {
  source: string
  target: string
  label: string
  strength?: number
}

export interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  thinking?: ThinkingStep[]
  sources?: Citation[]
  graph?: GraphData
  isStreaming?: boolean
}

export interface SSEMessage {
  type: 'thinking' | 'content' | 'sources' | 'done' | 'error' | 'graph' | string
  data: any
}

export interface Conversation {
  id: string
  title: string
  domain: string
  updated_at: string
}

export async function* streamChat(
  message: string,
  history: ChatMessage[],
  session: Record<string, string>,
  conversationId?: string,
): AsyncGenerator<SSEMessage> {
  const body = {
    message,
    history: history.map(m => ({ role: m.role, content: m.content })),
    session,
    conversation_id: conversationId || '',
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

export async function fetchConversations(): Promise<Conversation[]> {
  try {
    const resp = await fetch('/api/conversations')
    if (!resp.ok) return []
    const data = await resp.json()
    return data.conversations || []
  } catch {
    return []
  }
}

export async function loadConversation(id: string): Promise<ChatMessage[] | null> {
  try {
    const resp = await fetch(`/api/conversations/${id}`)
    if (!resp.ok) return null
    const data = await resp.json()
    return data.messages || null
  } catch {
    return null
  }
}

export async function deleteConversation(id: string): Promise<boolean> {
  try {
    const resp = await fetch(`/api/conversations/${id}`, { method: 'DELETE' })
    return resp.ok
  } catch {
    return false
  }
}

export async function* expandGraphNode(
  nodeId: string,
  nodeName: string,
  nodeType: string,
  domain: string,
): AsyncGenerator<SSEMessage> {
  const body = { node_id: nodeId, node_name: nodeName, node_type: nodeType, domain }

  const resp = await fetch('/api/graph/expand', {
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
            // skip
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
