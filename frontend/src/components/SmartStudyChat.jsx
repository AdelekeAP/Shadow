import { useState, useEffect, useRef } from 'react';
import api from '../services/api';

export default function SmartStudyChat({ onClose }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [suggestedPrompts, setSuggestedPrompts] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const messagesEndRef = useRef(null);

  // Scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load suggested prompts on mount
  useEffect(() => {
    loadSuggestedPrompts();
  }, []);

  const loadSuggestedPrompts = async () => {
    try {
      const response = await api.get('/api/v1/smartstudy/suggested-prompts');
      setSuggestedPrompts(response.data || []);
    } catch (error) {
      console.error('Error loading suggested prompts:', error);
    }
  };

  const sendMessage = async (messageText) => {
    const content = messageText || input;
    if (!content.trim()) return;

    // Add user message immediately
    const userMessage = { role: 'user', content: content.trim() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setShowSuggestions(false);
    setLoading(true);

    try {
      const response = await api.post('/api/v1/smartstudy/chat', {
        content: content.trim(),
        conversation_id: conversationId
      });

      // Set conversation ID on first message
      if (!conversationId && response.data.conversation_id) {
        setConversationId(response.data.conversation_id);
      }

      // Add AI response
      const aiMessage = {
        role: 'assistant',
        content: response.data.ai_response,
        tokens_used: response.data.tokens_used
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      // Add error message
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handlePromptClick = (prompt) => {
    sendMessage(prompt);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage();
  };

  const startNewConversation = () => {
    setMessages([]);
    setConversationId(null);
    setShowSuggestions(true);
    loadSuggestedPrompts();
  };

  return (
    <div className="fixed inset-0 bg-stone-900/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full h-[85vh] flex flex-col animate-scale-in">
        {/* Header */}
        <div className="bg-gradient-to-r from-navy-800 to-navy-700 text-white p-6 rounded-t-2xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-white/20 rounded-full p-2">
                <span className="text-2xl">🤖</span>
              </div>
              <div>
                <h2 className="text-2xl font-bold">SmartStudy AI</h2>
                <p className="text-navy-200 text-sm">Your personal learning coach</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {conversationId && (
                <button
                  onClick={startNewConversation}
                  className="bg-white/20 hover:bg-white/30 px-4 py-2 rounded-xl transition-all duration-200"
                  title="New conversation"
                >
                  <span className="text-sm">✨ New Chat</span>
                </button>
              )}
              <button
                onClick={onClose}
                className="text-white hover:bg-white/20 rounded-lg p-2 transition-all duration-200"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-stone-50">
          {/* Welcome Message */}
          {messages.length === 0 && (
            <div className="text-center py-8">
              <div className="text-6xl mb-4">🎓</div>
              <h3 className="text-2xl font-bold text-stone-800 mb-2">Welcome to SmartStudy!</h3>
              <p className="text-stone-600 mb-6 max-w-md mx-auto">
                I'm your AI learning coach. I know your courses, tasks, and goals.
                Ask me anything or choose a suggestion below!
              </p>
            </div>
          )}

          {/* Suggested Prompts */}
          {showSuggestions && suggestedPrompts.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
              {suggestedPrompts.map((prompt, index) => (
                <button
                  key={index}
                  onClick={() => handlePromptClick(prompt.prompt)}
                  className="bg-white border-2 border-navy-200 hover:border-navy-400 hover:bg-navy-50 p-4 rounded-xl text-left transition-all duration-200 group"
                >
                  <div className="flex items-start gap-3">
                    <span className="text-2xl group-hover:scale-110 transition-transform duration-200">
                      {prompt.icon}
                    </span>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-stone-700 group-hover:text-navy-800">
                        {prompt.prompt}
                      </p>
                      <span className="text-xs text-stone-500 capitalize mt-1 inline-block">
                        {prompt.category}
                      </span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Messages */}
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-5 py-3 ${
                  message.role === 'user'
                    ? 'bg-navy-600 text-white'
                    : message.error
                    ? 'bg-red-100 text-red-800 border-2 border-red-300'
                    : 'bg-white text-stone-800 border-2 border-stone-200'
                }`}
              >
                {message.role === 'assistant' && !message.error && (
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">🤖</span>
                    <span className="text-xs font-semibold text-navy-600">SmartStudy AI</span>
                  </div>
                )}
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                {message.tokens_used && (
                  <p className="text-xs text-stone-500 mt-2">
                    ~{message.tokens_used} tokens
                  </p>
                )}
              </div>
            </div>
          ))}

          {/* Loading Indicator */}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border-2 border-stone-200 rounded-2xl px-5 py-3 max-w-[80%]">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🤖</span>
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-navy-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-navy-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-navy-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t-2 border-stone-200 p-4 bg-white rounded-b-2xl">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything about your courses, tasks, or study tips..."
              className="flex-1 border-2 border-stone-300 focus:border-navy-500 focus:ring-2 focus:ring-navy-200 rounded-xl px-4 py-3 outline-none transition-all duration-200"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="bg-navy-600 hover:bg-navy-700 disabled:bg-stone-300 disabled:cursor-not-allowed text-white px-6 py-3 rounded-xl font-semibold transition-all duration-200 flex items-center gap-2"
            >
              <span>Send</span>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </button>
          </form>
          <p className="text-xs text-stone-500 mt-2 text-center">
            💡 Tip: I can help with course concepts, task prioritization, study strategies, and motivation!
          </p>
        </div>
      </div>
    </div>
  );
}
