import { useState, useEffect, useRef, useCallback } from 'react'
import api, { API_BASE_URL } from '../services/api'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/* ─── AI sparkle icon (reused) ─── */
const SparkleIcon = ({ className = 'w-4 h-4' }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
  </svg>
)

export default function SmartStudyChat({ onClose }) {
  const [messages, setMessages] = useState([])
  const msgIdRef = useRef(0)
  const nextMsgId = () => ++msgIdRef.current
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const [suggestedPrompts, setSuggestedPrompts] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(true)
  const [entering, setEntering] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const backdropRef = useRef(null)
  const activeControllerRef = useRef(null)
  const [showHistory, setShowHistory] = useState(false)
  const [conversations, setConversations] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [chatError, setChatError] = useState(null)

  useEffect(() => { requestAnimationFrame(() => setEntering(true)) }, [])
  useEffect(() => {
    if (!chatError) return
    const t = setTimeout(() => setChatError(null), 5000)
    return () => clearTimeout(t)
  }, [chatError])
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])
  useEffect(() => { loadSuggestedPrompts() }, [])
  useEffect(() => { if (entering && !loading) inputRef.current?.focus() }, [entering])

  useEffect(() => {
    const handleKeyDown = (e) => { if (e.key === 'Escape') close() }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Abort any active stream on unmount
  useEffect(() => {
    return () => { activeControllerRef.current?.abort() }
  }, [])

  const close = () => { setEntering(false); setTimeout(onClose, 200) }

  const loadSuggestedPrompts = async () => {
    try {
      const r = await api.get('/api/v1/smartstudy/suggested-prompts')
      setSuggestedPrompts(r.data || [])
    } catch (e) { /* suggested prompts are non-critical, fail silently */ }
  }

  const fallbackToNonStreaming = async (content) => {
    try {
      const r = await api.post('/api/v1/smartstudy/chat', { content, conversation_id: conversationId })
      if (!conversationId && r.data.conversation_id) setConversationId(r.data.conversation_id)
      setMessages(prev => [...prev, { id: nextMsgId(), role: 'assistant', content: r.data.ai_response, tokens_used: r.data.tokens_used }])
    } catch (e) {
      console.error('SmartStudy chat error:', e)
      setMessages(prev => [...prev, {
        id: nextMsgId(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        error: true,
        originalContent: content,
      }])
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }

  const sendMessage = async (messageText) => {
    const content = (messageText || input).trim()
    if (!content) return

    setMessages(prev => [...prev, { id: nextMsgId(), role: 'user', content }])
    setInput('')
    setShowSuggestions(false)
    setLoading(true)

    const baseUrl = API_BASE_URL
    const token = localStorage.getItem('access_token')

    // Abort if no data received within 60 seconds
    const controller = new AbortController()
    activeControllerRef.current = controller
    const timeout = setTimeout(() => controller.abort(), 60000)

    let response
    try {
      response = await fetch(`${baseUrl}/api/v1/smartstudy/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ content, conversation_id: conversationId }),
        signal: controller.signal,
      })
    } catch (e) {
      clearTimeout(timeout)
      console.error('Streaming connection error:', e)
      // Network error — fall back to non-streaming
      return fallbackToNonStreaming(content)
    }

    if (!response.ok) {
      // Server error — fall back to non-streaming
      return fallbackToNonStreaming(content)
    }

    // Add placeholder streaming message
    const newMsgId = nextMsgId()
    setMessages(prev => [...prev, { id: newMsgId, role: 'assistant', content: '', streaming: true }])

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() // keep incomplete chunk

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed.startsWith('data: ')) continue
          let event
          try { event = JSON.parse(trimmed.slice(6)) } catch { continue }

          if (event.type === 'meta') {
            if (!conversationId && event.conversation_id) setConversationId(event.conversation_id)
          } else if (event.type === 'token') {
            setMessages(prev => prev.map(msg =>
              msg.id === newMsgId ? { ...msg, content: msg.content + event.content } : msg
            ))
          } else if (event.type === 'done') {
            setMessages(prev => prev.map(msg =>
              msg.id === newMsgId ? { ...msg, streaming: false } : msg
            ))
          } else if (event.type === 'error') {
            setMessages(prev => prev.map(msg =>
              msg.id === newMsgId
                ? { ...msg, streaming: false, error: true, content: event.message, originalContent: content }
                : msg
            ))
          }
        }
      }

      // Ensure streaming flag is cleared even if no done event
      setMessages(prev => prev.map(msg =>
        msg.id === newMsgId && msg.streaming ? { ...msg, streaming: false } : msg
      ))
    } catch (e) {
      console.error('Stream read error:', e)
      setMessages(prev => prev.map(msg =>
        msg.id === newMsgId
          ? { ...msg, streaming: false, error: true, content: e.name === 'AbortError' ? 'Request timed out. Please try again.' : 'Connection lost. Please try again.', originalContent: content }
          : msg
      ))
    } finally {
      clearTimeout(timeout)
      activeControllerRef.current = null
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }

  const retryMessage = (originalContent) => {
    // Remove the error message and re-send
    setMessages(prev => prev.slice(0, -1))
    sendMessage(originalContent)
  }

  const startNewConversation = () => {
    setMessages([])
    setConversationId(null)
    setShowSuggestions(true)
    loadSuggestedPrompts()
  }

  const loadConversations = async () => {
    setLoadingHistory(true)
    try {
      const r = await api.get('/api/v1/smartstudy/conversations', { params: { limit: 20 } })
      setConversations(r.data || [])
    } catch (e) {
      console.error('Error loading conversations:', e)
      setChatError('Could not load conversation history.')
    } finally { setLoadingHistory(false) }
  }

  const loadConversation = async (conv) => {
    try {
      const r = await api.get(`/api/v1/smartstudy/conversations/${conv.id}`)
      const data = r.data
      setConversationId(data.id)
      setMessages((data.messages || []).map(m => ({ id: nextMsgId(), role: m.role, content: m.content, tokens_used: m.tokens_used })))
      setShowHistory(false)
      setShowSuggestions(false)
    } catch (e) {
      console.error('Error loading conversation:', e)
      setChatError('Could not load this conversation.')
    }
  }

  const deleteConversation = async (convId, e) => {
    e.stopPropagation()
    try {
      await api.delete(`/api/v1/smartstudy/conversations/${convId}`)
      setConversations(prev => prev.filter(c => c.id !== convId))
      if (conversationId === convId) startNewConversation()
    } catch (e) {
      console.error('Error deleting conversation:', e)
      setChatError('Could not delete conversation.')
    }
  }

  const toggleHistory = () => {
    if (!showHistory) loadConversations()
    setShowHistory(prev => !prev)
  }

  /* ─── Prompt icon fallback ─── */
  const promptIcon = (category) => {
    const map = {
      study: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" /></svg>,
      tasks: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
      motivation: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" /></svg>,
      grades: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" /></svg>,
    }
    return map[category] || <SparkleIcon className="w-4 h-4" />
  }

  return (
    <div
      ref={backdropRef}
      onClick={(e) => e.target === backdropRef.current && close()}
      role="dialog"
      aria-modal="true"
      aria-label="SmartStudy AI Coach"
      className={`fixed inset-0 bg-navy-950/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-opacity duration-200 ${entering ? 'opacity-100' : 'opacity-0'}`}
    >
      <div className={`bg-white rounded-2xl shadow-2xl max-w-3xl w-full h-[85vh] flex flex-col overflow-hidden transition-all duration-300 ${
        entering ? 'scale-100 translate-y-0 opacity-100' : 'scale-95 translate-y-4 opacity-0'
      }`}>

        {/* ── Header ── */}
        <div className="flex-shrink-0 px-5 py-4 border-b border-surface-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-navy-800 flex items-center justify-center">
              <SparkleIcon className="w-[18px] h-[18px] text-white" />
            </div>
            <div>
              <h2 className="text-[15px] font-bold text-navy-900 leading-tight">SmartStudy</h2>
              <p className="text-[11px] text-surface-400">AI learning coach</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={toggleHistory}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-semibold transition-colors ${
                showHistory ? 'text-navy-800 bg-surface-100' : 'text-navy-600 hover:text-navy-800 hover:bg-surface-100'
              }`}
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              History
            </button>
            {conversationId && (
              <button
                onClick={startNewConversation}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-semibold text-navy-600 hover:text-navy-800 hover:bg-surface-100 transition-colors"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                New chat
              </button>
            )}
            <button
              onClick={close}
              className="p-1.5 rounded-lg text-surface-300 hover:text-surface-400 hover:bg-surface-100 transition-all"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* ── History Panel ── */}
        {showHistory && (
          <div className="flex-shrink-0 border-b border-surface-100 bg-white max-h-[50%] overflow-y-auto">
            <div className="px-4 py-3">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-[13px] font-bold text-navy-900">Recent Conversations</h3>
                <button
                  onClick={() => { startNewConversation(); setShowHistory(false) }}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold text-navy-600 hover:bg-surface-100 transition-colors"
                >
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                  </svg>
                  New
                </button>
              </div>
              {loadingHistory ? (
                <div className="flex justify-center py-6">
                  <div className="w-5 h-5 border-2 border-navy-200 border-t-navy-600 rounded-full animate-spin" />
                </div>
              ) : conversations.length === 0 ? (
                <p className="text-[12px] text-surface-400 text-center py-6">No conversations yet</p>
              ) : (
                <div className="space-y-1">
                  {conversations.map(conv => (
                    <button
                      key={conv.id}
                      onClick={() => loadConversation(conv)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all group ${
                        conversationId === conv.id
                          ? 'bg-navy-800/[0.06] border border-navy-200/60'
                          : 'hover:bg-surface-50 border border-transparent'
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-[12px] font-medium text-navy-900 truncate">
                          {conv.title || conv.preview || 'Untitled conversation'}
                        </p>
                        <p className="text-[10px] text-surface-400 mt-0.5">
                          {conv.message_count || 0} messages · {new Date(conv.updated_at || conv.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <button
                        onClick={(e) => deleteConversation(conv.id, e)}
                        className="p-1 rounded-md text-surface-300 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                        </svg>
                      </button>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Messages ── */}
        <div className="flex-1 overflow-y-auto px-5 py-5 space-y-4 bg-surface-50/50">

          {/* Welcome state */}
          {messages.length === 0 && (
            <div className="pt-8 pb-4">
              <div className="text-center mb-8">
                <div className="w-14 h-14 rounded-2xl bg-navy-800/[0.06] flex items-center justify-center mx-auto mb-4">
                  <SparkleIcon className="w-7 h-7 text-navy-700" />
                </div>
                <h3 className="text-[18px] font-bold text-navy-900 mb-1">What can I help with?</h3>
                <p className="text-[13px] text-surface-400 max-w-sm mx-auto">
                  I know your courses, tasks, and goals. Ask me anything or pick a suggestion.
                </p>
              </div>

              {/* Suggested prompts */}
              {showSuggestions && suggestedPrompts.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg mx-auto">
                  {suggestedPrompts.map((prompt) => (
                    <button
                      key={prompt.prompt}
                      onClick={() => sendMessage(prompt.prompt)}
                      className="group flex items-start gap-3 p-3.5 rounded-xl border border-surface-200/80 bg-white hover:border-navy-300/60 hover:bg-navy-800/[0.02] transition-all text-left"
                    >
                      <div className="w-7 h-7 rounded-lg bg-surface-100 group-hover:bg-navy-800/[0.06] flex items-center justify-center flex-shrink-0 mt-0.5 text-surface-400 group-hover:text-navy-600 transition-colors">
                        {promptIcon(prompt.category)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[12px] font-medium text-navy-800 leading-snug line-clamp-2">{prompt.prompt}</p>
                        <span className="text-[10px] text-surface-300 capitalize mt-1 block">{prompt.category}</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Message bubbles */}
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'assistant' && (
                <div className="w-6 h-6 rounded-lg bg-navy-800 flex items-center justify-center flex-shrink-0 mr-2.5 mt-1">
                  <SparkleIcon className="w-3 h-3 text-white" />
                </div>
              )}
              <div className={`max-w-[75%] ${
                msg.role === 'user'
                  ? 'rounded-2xl rounded-br-md bg-navy-800 text-white px-4 py-3'
                  : msg.error
                  ? 'rounded-2xl rounded-bl-md bg-red-50 text-red-700 border border-red-100 px-4 py-3'
                  : 'rounded-2xl rounded-bl-md bg-white border border-surface-200/80 text-navy-900 px-4 py-3 shadow-sm'
              }`}>
                {msg.role === 'user' ? (
                  <p className="text-[13px] leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                ) : msg.error ? (
                  <div>
                    <p className="text-[13px] leading-relaxed">{msg.content}</p>
                    {msg.originalContent && (
                      <button
                        onClick={() => retryMessage(msg.originalContent)}
                        className="mt-2 px-3 py-1 text-[11px] font-semibold bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors"
                      >
                        Retry
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="prose-chat text-[13px] leading-relaxed">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                    {msg.streaming && (
                      <span className="inline-block w-1.5 h-4 bg-navy-600 animate-pulse ml-0.5 -mb-0.5 rounded-sm" />
                    )}
                  </div>
                )}
                {msg.tokens_used && (
                  <p className="font-mono text-[10px] text-surface-300 mt-2 text-right">~{msg.tokens_used} tokens</p>
                )}
              </div>
            </div>
          ))}

          {/* Loading dots — only when not already streaming */}
          {loading && !messages.some(m => m.streaming) && (
            <div className="flex justify-start">
              <div className="w-6 h-6 rounded-lg bg-navy-800 flex items-center justify-center flex-shrink-0 mr-2.5 mt-1">
                <SparkleIcon className="w-3 h-3 text-white" />
              </div>
              <div className="bg-white border border-surface-200/80 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
                <div className="flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 bg-navy-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-1.5 h-1.5 bg-navy-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-1.5 h-1.5 bg-navy-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* ── Input ── */}
        <div className="flex-shrink-0 border-t border-surface-100 px-4 py-3 bg-white">
          <form onSubmit={(e) => { e.preventDefault(); sendMessage() }} className="flex items-end gap-2.5">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about your courses, tasks, or study strategies..."
                className="w-full bg-surface-50 border border-surface-200/80 rounded-xl px-4 py-2.5 text-[13px] text-navy-900 placeholder:text-surface-300 focus:border-navy-300 focus:ring-2 focus:ring-navy-100 focus:bg-white transition-all outline-none"
                disabled={loading}
              />
            </div>
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="flex-shrink-0 w-10 h-10 rounded-xl bg-navy-800 hover:bg-navy-900 disabled:bg-surface-200 disabled:cursor-not-allowed text-white flex items-center justify-center transition-all"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
              </svg>
            </button>
          </form>
          <p className="text-[10px] text-surface-300 mt-2 text-center">
            SmartStudy knows your enrolled courses, task deadlines, and CGPA goals
          </p>
        </div>

        {/* ── Error toast ── */}
        {chatError && (
          <div className="absolute bottom-20 left-1/2 -translate-x-1/2 z-10 animate-fade-up">
            <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-red-50/95 border border-red-200/80 text-red-700 shadow-lg backdrop-blur-sm">
              <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
              <p className="text-[12px] font-medium">{chatError}</p>
              <button onClick={() => setChatError(null)} className="p-0.5 rounded-md hover:bg-red-100 transition-colors ml-1">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
