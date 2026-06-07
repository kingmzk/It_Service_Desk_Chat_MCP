import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import './App.css'

const API_URL = 'http://localhost:8000/api/chat'

type Role = 'user' | 'assistant'

interface Message {
  role: Role
  content: string
  timestamp: Date
}

interface Turn {
  role: Role
  content: string
}

const QUICK_PROMPTS = [
  'My VPN is not connecting',
  'Outlook is not syncing emails',
  'My laptop is running very slow',
  'I need to reset my Windows password',
  'Show all open tickets',
]

function TypingIndicator() {
  return (
    <div className="message assistant">
      <div className="avatar">🤖</div>
      <div className="bubble typing">
        <span /><span /><span />
      </div>
    </div>
  )
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hello! I'm your IT Service Desk assistant. How can I help you today?\n\nI can help you troubleshoot issues, create support tickets, check ticket status, or search our knowledge base.",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const getHistory = (): Turn[] =>
    messages.map(m => ({ role: m.role, content: m.content }))

  const sendMessage = async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || loading) return

    const userMsg: Message = { role: 'user', content: trimmed, timestamp: new Date() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, history: getHistory() }),
      })

      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const data = await res.json()

      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: data.reply, timestamp: new Date() },
      ])
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: '⚠️ Sorry, I could not reach the server. Please check that the backend is running on port 8000.',
          timestamp: new Date(),
        },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const formatTime = (d: Date) =>
    d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

  return (
    <div className="app">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo">🖥️</div>
          <h1>IT Service Desk</h1>
          <p>Powered by MCP + Azure OpenAI</p>
        </div>

        <div className="sidebar-section">
          <h3>Quick Actions</h3>
          <ul className="quick-list">
            {QUICK_PROMPTS.map(q => (
              <li key={q}>
                <button onClick={() => sendMessage(q)} disabled={loading}>
                  {q}
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="sidebar-section capabilities">
          <h3>Capabilities</h3>
          <ul>
            <li>🔍 Search knowledge base</li>
            <li>🎫 Create support tickets</li>
            <li>📋 Check ticket status</li>
            <li>🚨 Escalate critical issues</li>
            <li>📂 List & filter tickets</li>
          </ul>
        </div>
      </aside>

      {/* ── Chat Area ── */}
      <main className="chat">
        <header className="chat-header">
          <div className="status-dot" />
          <span>Agent Online</span>
          <button
            className="clear-btn"
            onClick={() =>
              setMessages([{
                role: 'assistant',
                content: "Hello! I'm your IT Service Desk assistant. How can I help you today?",
                timestamp: new Date(),
              }])
            }
          >
            Clear chat
          </button>
        </header>

        <div className="messages">
          {messages.map((m, i) => (
            <div key={i} className={`message ${m.role}`}>
              <div className="avatar">{m.role === 'user' ? '👤' : '🤖'}</div>
              <div className="bubble">
                <div className="bubble-content">
                  <ReactMarkdown>{m.content}</ReactMarkdown>
                </div>
                <div className="bubble-time">{formatTime(m.timestamp)}</div>
              </div>
            </div>
          ))}
          {loading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        <footer className="chat-footer">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Describe your IT issue… (Enter to send, Shift+Enter for new line)"
            rows={2}
            disabled={loading}
          />
          <button
            className="send-btn"
            onClick={() => sendMessage(input)}
            disabled={loading || !input.trim()}
          >
            {loading ? '⏳' : '➤'}
          </button>
        </footer>
      </main>
    </div>
  )
}

export default App