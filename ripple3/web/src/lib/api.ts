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

export interface GraphNode {
  id: string
  name: string
  type: 'person' | 'topic' | 'platform' | 'format' | 'audience'
  val: number
  color: string
  desc?: string
}

export interface GraphLink {
  source: string
  target: string
  label: string
  strength: number
}

export interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
}

export interface AgentPersona {
  id: string
  name: string
  emoji: string
  color: string
}

export interface AgentMessage {
  agent: AgentPersona
  content: string
  round: number
}

export interface ScoreData {
  total_score: number
  verdict: string
  summary?: string
  dimensions: { name: string; score: number }[]
  hkrr: { name: string; score: number }[]
  key_risks?: string[]
  action_items?: string[]
}

export interface SearchStats {
  total_raw: number
  total_deduped: number
  engines: Record<string, number>
}

export interface TokenUsage {
  search_tokens: number
  llm_tokens: number
  total_tokens: number
  search_calls: number
  agent_rounds: number
  elapsed_ms: number
}

export interface ViralScoreData {
  total_score: number
  dimensions: { id: string; name: string; score: number; max: number; reason: string }[]
  predicted_pool: string
  pool_probability: string
  ces_analysis: string
  ces_weights: Record<string, number>
  traffic_pools: { name: string; exposure: string; threshold: string }[]
  strengths: string[]
  weaknesses: string[]
  optimization_tips: string[]
  engagement_formula: string
}

export interface SSEMessage {
  type: 'thinking' | 'content' | 'sources' | 'done' | 'error' | 'graph' | 'score' | 'agent_speak' | 'agent_start' | 'arbiter_thinking' | 'search_stats' | 'data_warning' | 'token_usage' | 'viral_score' | 'reflection'
  data: any
}

export interface NextStep {
  label: string
  prompt: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  thinking?: ThinkingStep[]
  sources?: Citation[]
  graph?: GraphData
  agentMessages?: AgentMessage[]
  scoreData?: ScoreData
  arbiterThinking?: string
  searchStats?: SearchStats
  dataWarning?: string
  tokenUsage?: TokenUsage
  viralScore?: ViralScoreData
  nextSteps?: NextStep[]
  isStreaming?: boolean
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

export async function fetchTrends(): Promise<Record<string, any[]>> {
  try {
    const resp = await fetch('/api/trends')
    if (!resp.ok) return {}
    const data = await resp.json()
    return data.trends || {}
  } catch {
    return {}
  }
}

export async function fetchMemory(): Promise<Record<string, string>> {
  try {
    const resp = await fetch('/api/memory')
    if (!resp.ok) return {}
    const data = await resp.json()
    return data.memory || {}
  } catch {
    return {}
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
