import { useState, useCallback } from 'react'
import { streamChat } from '../lib/api'
import type { ChatMessage, ThinkingStep, Citation } from '../lib/api'

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([])
  const [session, setSession] = useState<Record<string, string>>({})
  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return

    const userMsg: ChatMessage = { role: 'user', content: text.trim() }
    const assistantMsg: ChatMessage = { role: 'assistant', content: '', thinking: [], sources: [], isStreaming: true }

    setMessages(prev => [...prev, userMsg, assistantMsg])
    setIsLoading(true)
    setThinkingSteps([])

    const currentHistory = [...messages, userMsg]
    let content = ''
    let thinking: ThinkingStep[] = []
    let sources: Citation[] = []

    try {
      for await (const event of streamChat(text.trim(), currentHistory, session)) {
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

          case 'done':
            if (event.data.domain) {
              setSession(prev => ({ ...prev, domain: event.data.domain }))
            }
            if (event.data.topic) {
              setSession(prev => ({ ...prev, last_topic: event.data.topic }))
            }
            break

          case 'error':
            content += `\n\n> ⚠️ ${event.data.message}`
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
      content += `\n\n> ⚠️ 网络错误: ${err.message}`
    }

    setMessages(prev => {
      const updated = [...prev]
      const last = updated[updated.length - 1]
      if (last.role === 'assistant') {
        updated[updated.length - 1] = { ...last, content, isStreaming: false, thinking: [...thinking], sources }
      }
      return updated
    })
    setIsLoading(false)
    setThinkingSteps([])
  }, [messages, isLoading, session])

  const clearChat = useCallback(() => {
    setMessages([])
    setThinkingSteps([])
    setSession({})
  }, [])

  return { messages, isLoading, thinkingSteps, sendMessage, clearChat, session }
}
