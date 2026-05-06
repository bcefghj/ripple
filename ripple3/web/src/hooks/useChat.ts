import { useState, useCallback, useEffect } from 'react'
import { streamChat, fetchConversations, loadConversation, deleteConversation } from '../lib/api'
import type { ChatMessage, ThinkingStep, Citation, GraphData, Conversation } from '../lib/api'
import { DEMO_CASES } from '../data/demoCases'

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
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

    const demoCase = DEMO_CASES.find(c => c.prompt === text.trim())
    if (demoCase) {
      const userMsg: ChatMessage = { role: 'user', content: text.trim() }
      setMessages(prev => [...prev, userMsg, { ...demoCase.result, isStreaming: false }])
      setIsLoading(false)
      return
    }

    const userMsg: ChatMessage = { role: 'user', content: text.trim() }
    const assistantMsg: ChatMessage = {
      role: 'assistant',
      content: '',
      thinking: [],
      sources: [],
      isStreaming: true,
    }

    setMessages(prev => [...prev, userMsg, assistantMsg])
    setIsLoading(true)

    const currentHistory = [...messages, userMsg]
    let content = ''
    let thinking: ThinkingStep[] = []
    let sources: Citation[] = []
    let graph: GraphData | undefined

    try {
      for await (const event of streamChat(text.trim(), currentHistory, session, conversationId)) {
        switch (event.type) {
          case 'thinking':
            thinking = [...thinking, event.data as ThinkingStep]
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
                updated[updated.length - 1] = { ...last, content }
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
        }
      }
      return updated
    })
    setIsLoading(false)
    refreshConversations()
  }, [messages, isLoading, session, conversationId, refreshConversations])

  const clearChat = useCallback(() => {
    setMessages([])
    setSession({})
    setConversationId('')
  }, [])

  return {
    messages,
    isLoading,
    sendMessage,
    clearChat,
    conversationId,
    conversations,
    loadHistory,
    deleteHistory,
  }
}
