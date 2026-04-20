import { useState, useEffect, useRef } from 'react'
import { api } from '../api'

export default function AgentMemory() {
  const [sessions, setSessions] = useState([])
  const [activeSession, setActiveSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [role, setRole] = useState('user')
  const [agentName, setAgentName] = useState('lab-agent')
  const [loading, setLoading] = useState(false)
  const chatRef = useRef(null)

  const loadSessions = () => {
    api.listSessions().then(setSessions).catch(() => {})
  }

  useEffect(loadSessions, [])

  useEffect(() => {
    if (!activeSession) return
    api.getMessages(activeSession).then(setMessages)
  }, [activeSession])

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight
    }
  }, [messages])

  const createSession = async () => {
    setLoading(true)
    try {
      const s = await api.createSession({ agent_name: agentName })
      loadSessions()
      setActiveSession(s.session_id)
    } catch {}
    setLoading(false)
  }

  const deleteSession = async (id) => {
    try {
      await api.deleteSession(id)
      if (activeSession === id) {
        setActiveSession(null)
        setMessages([])
      }
      loadSessions()
    } catch {}
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim() || !activeSession) return
    try {
      await api.appendMessage(activeSession, { role, content: input })
      setInput('')
      api.getMessages(activeSession).then(setMessages)
    } catch {}
  }

  return (
    <div>
      <div className="page-header">
        <h2>Agent Memory Lab</h2>
        <p>
          Use Lakebase as a persistent session/message store for AI agents.
          This demonstrates using PostgreSQL as a backing store for conversational
          memory without LangChain or external dependencies.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 16 }}>
        {/* Sessions sidebar */}
        <div className="card" style={{ alignSelf: 'start' }}>
          <div className="card-header">
            <h3>Sessions</h3>
          </div>
          <div className="form-group">
            <label>Agent Name</label>
            <input value={agentName} onChange={(e) => setAgentName(e.target.value)} placeholder="lab-agent" />
          </div>
          <button className="btn btn-primary btn-sm" onClick={createSession} disabled={loading} style={{ marginBottom: 16, width: '100%' }}>
            + New Session
          </button>

          {sessions.length === 0 ? (
            <div className="empty-state" style={{ padding: 20 }}>
              <p>No sessions yet</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {sessions.map((s) => (
                <div
                  key={s.session_id}
                  style={{
                    padding: '8px 12px',
                    borderRadius: 6,
                    cursor: 'pointer',
                    background: activeSession === s.session_id ? 'rgba(255,111,60,0.12)' : 'var(--bg-primary)',
                    border: `1px solid ${activeSession === s.session_id ? 'var(--accent)' : 'var(--border)'}`,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                  onClick={() => setActiveSession(s.session_id)}
                >
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{s.session_id}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                      {s.agent_name} | {s.message_count} msgs
                    </div>
                  </div>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={(e) => { e.stopPropagation(); deleteSession(s.session_id) }}
                    style={{ padding: '2px 6px', fontSize: 10 }}
                  >
                    X
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Chat area */}
        <div className="card">
          {!activeSession ? (
            <div className="empty-state">
              <div className="empty-icon">💬</div>
              <p>Select or create a session to start chatting</p>
            </div>
          ) : (
            <>
              <div className="card-header">
                <h3>Session: {activeSession}</h3>
                <span className="badge badge-info">{messages.length} messages</span>
              </div>

              <div className="chat-messages" ref={chatRef}>
                {messages.length === 0 && (
                  <div className="empty-state" style={{ padding: 20 }}>
                    <p>No messages yet. Send one below.</p>
                  </div>
                )}
                {messages.map((m, i) => (
                  <div key={i} className={`chat-msg ${m.role}`}>
                    <div className="msg-role">{m.role}</div>
                    {m.content}
                  </div>
                ))}
              </div>

              <form onSubmit={sendMessage} style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  style={{ width: 110, padding: '8px', background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text-primary)', fontSize: 13 }}
                >
                  <option value="user">user</option>
                  <option value="assistant">assistant</option>
                  <option value="system">system</option>
                  <option value="tool">tool</option>
                </select>
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Type a message..."
                  style={{ flex: 1, padding: '8px 12px', background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text-primary)', fontSize: 13 }}
                />
                <button className="btn btn-primary" type="submit">Send</button>
              </form>

              <div style={{ marginTop: 16 }}>
                <h4 style={{ fontSize: 13, marginBottom: 8, color: 'var(--text-secondary)' }}>Schema</h4>
                <div className="code-block">{`-- Sessions table
CREATE TABLE demo.agent_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Messages table (cascading delete)
CREATE TABLE demo.agent_messages (
    message_id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) REFERENCES demo.agent_sessions ON DELETE CASCADE,
    role VARCHAR(20) CHECK (role IN ('user','assistant','system','tool')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);`}</div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
