import { useState, useCallback, useEffect } from 'react'
import { streamChat, fetchConversations, loadConversation, deleteConversation } from '../lib/api'
import type { ChatMessage, ThinkingStep, Citation, AgentMessage, GraphData, ScoreData, SearchStats, TokenUsage, ViralScoreData, NextStep, Conversation } from '../lib/api'

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([])
  const [session, setSession] = useState<Record<string, string>>({})
  const [conversationId, setConversationId] = useState<string>('')
  const [conversations, setConversations] = useState<Conversation[]>([])

  useEffect(() => {
    refreshConversations()
  }, [])

  const refreshConversations = useCallback(async () => {
    const list = await fetchConversations()
    setConversations(list)
  }, [])

  const loadHistory = useCallback(async (id: string) => {
    const msgs = await loadConversation(id)
    if (msgs) {
      setMessages(msgs.map(m => ({ ...m, isStreaming: false })))
      setConversationId(id)
      setThinkingSteps([])
    }
  }, [])

  const deleteHistory = useCallback(async (id: string) => {
    await deleteConversation(id)
    if (conversationId === id) {
      setMessages([])
      setConversationId('')
    }
    await refreshConversations()
  }, [conversationId, refreshConversations])

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return

    const userMsg: ChatMessage = { role: 'user', content: text.trim() }
    const assistantMsg: ChatMessage = {
      role: 'assistant',
      content: '',
      thinking: [],
      sources: [],
      agentMessages: [],
      isStreaming: true,
    }

    setMessages(prev => [...prev, userMsg, assistantMsg])
    setIsLoading(true)
    setThinkingSteps([])

    const currentHistory = [...messages, userMsg]
    let content = ''
    let thinking: ThinkingStep[] = []
    let sources: Citation[] = []
    let graph: GraphData | undefined
    let agentMessages: AgentMessage[] = []
    let scoreData: ScoreData | undefined
    let arbiterThinking = ''
    let searchStats: SearchStats | undefined
    let dataWarning = ''
    let tokenUsage: TokenUsage | undefined
    let viralScore: ViralScoreData | undefined
    let nextSteps: NextStep[] | undefined

    try {
      for await (const event of streamChat(text.trim(), currentHistory, session, conversationId)) {
        switch (event.type) {
          case 'thinking':
            thinking = [...thinking, event.data as ThinkingStep]
            setThinkingSteps([...thinking])
            setMessages(prev => {
              const updated = [...prev]
              const last = updated[updated.length - 1]
              if (last.role === 'assistant') {
                updated[updated.length - 1] = { ...last, thinking: [...thinking] }
              }
              return updated
            })
            break

          case 'content':
            content += event.data.delta
            setMessages(prev => {
              const updated = [...prev]
              const last = updated[updated.length - 1]
              if (last.role === 'assistant') {
                updated[updated.length - 1] = { ...last, content, thinking: [...thinking] }
              }
              return updated
            })
            break

          case 'sources':
            sources = event.data.citations || []
            setMessages(prev => {
              const updated = [...prev]
              const last = updated[updated.length - 1]
              if (last.role === 'assistant') {
                updated[updated.length - 1] = { ...last, sources }
              }
              return updated
            })
            break

          case 'graph':
            graph = event.data as GraphData
            setMessages(prev => {
              const updated = [...prev]
              const last = updated[updated.length - 1]
              if (last.role === 'assistant') {
                updated[updated.length - 1] = { ...last, graph }
              }
              return updated
            })
            break

          case 'agent_start':
          case 'agent_speak': {
            if (event.type === 'agent_speak') {
              const agentMsg = event.data as AgentMessage
              const idx = agentMessages.findIndex(
                m => m.agent.id === agentMsg.agent.id && m.round === agentMsg.round
              )
              if (idx >= 0) {
                agentMessages = [...agentMessages]
                agentMessages[idx] = agentMsg
              } else {
                agentMessages = [...agentMessages, agentMsg]
              }
              setMessages(prev => {
                const updated = [...prev]
                const last = updated[updated.length - 1]
                if (last.role === 'assistant') {
                  updated[updated.length - 1] = { ...last, agentMessages: [...agentMessages] }
                }
                return updated
              })
            }
            break
          }

          case 'arbiter_thinking':
            arbiterThinking = event.data.content || ''
            setMessages(prev => {
              const updated = [...prev]
              const last = updated[updated.length - 1]
              if (last.role === 'assistant') {
                updated[updated.length - 1] = { ...last, arbiterThinking }
              }
              return updated
            })
            break

          case 'score':
            scoreData = event.data as ScoreData
            setMessages(prev => {
              const updated = [...prev]
              const last = updated[updated.length - 1]
              if (last.role === 'assistant') {
                updated[updated.length - 1] = { ...last, scoreData }
              }
              return updated
            })
            break

          case 'done':
            if (event.data.domain) {
              setSession(prev => ({ ...prev, domain: event.data.domain }))
            }
            if (event.data.topic) {
              setSession(prev => ({ ...prev, last_topic: event.data.topic }))
            }
            if (event.data.conversation_id) {
              setConversationId(event.data.conversation_id)
            }
            if (event.data.next_steps) {
              nextSteps = event.data.next_steps as NextStep[]
              setMessages(prev => {
                const updated = [...prev]
                const last = updated[updated.length - 1]
                if (last.role === 'assistant') {
                  updated[updated.length - 1] = { ...last, nextSteps }
                }
                return updated
              })
            }
            break

          case 'search_stats':
            searchStats = event.data as SearchStats
            setMessages(prev => {
              const updated = [...prev]
              const last = updated[updated.length - 1]
              if (last.role === 'assistant') {
                updated[updated.length - 1] = { ...last, searchStats }
              }
              return updated
            })
            break

          case 'data_warning':
            dataWarning = event.data.message || ''
            setMessages(prev => {
              const updated = [...prev]
              const last = updated[updated.length - 1]
              if (last.role === 'assistant') {
                updated[updated.length - 1] = { ...last, dataWarning }
              }
              return updated
            })
            break

          case 'token_usage':
            tokenUsage = event.data as TokenUsage
            setMessages(prev => {
              const updated = [...prev]
              const last = updated[updated.length - 1]
              if (last.role === 'assistant') {
                updated[updated.length - 1] = { ...last, tokenUsage }
              }
              return updated
            })
            break

          case 'viral_score':
            viralScore = event.data as ViralScoreData
            setMessages(prev => {
              const updated = [...prev]
              const last = updated[updated.length - 1]
              if (last.role === 'assistant') {
                updated[updated.length - 1] = { ...last, viralScore }
              }
              return updated
            })
            break

          case 'error':
            content += `\n\n> ${event.data.message}`
            setMessages(prev => {
              const updated = [...prev]
              const last = updated[updated.length - 1]
              if (last.role === 'assistant') {
                updated[updated.length - 1] = { ...last, content }
              }
              return updated
            })
            break
        }
      }
    } catch (err: any) {
      content += `\n\n> 网络错误: ${err.message}`
    }

    setMessages(prev => {
      const updated = [...prev]
      const last = updated[updated.length - 1]
      if (last.role === 'assistant') {
        updated[updated.length - 1] = {
          ...last,
          content,
          isStreaming: false,
          thinking: [...thinking],
          sources,
          graph,
          agentMessages: [...agentMessages],
          scoreData,
          arbiterThinking,
          searchStats,
          dataWarning,
          tokenUsage,
          viralScore,
          nextSteps,
        }
      }
      return updated
    })
    setIsLoading(false)
    setThinkingSteps([])
    refreshConversations()
  }, [messages, isLoading, session, conversationId, refreshConversations])

  const clearChat = useCallback(() => {
    setMessages([])
    setThinkingSteps([])
    setSession({})
    setConversationId('')
  }, [])

  return {
    messages,
    isLoading,
    thinkingSteps,
    sendMessage,
    clearChat,
    session,
    conversationId,
    conversations,
    loadHistory,
    deleteHistory,
    refreshConversations,
  }
}
