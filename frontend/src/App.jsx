import { useState, useEffect, useCallback, useRef } from 'react'
import './App.css'

const PAGE_SIZE = 10

function formatTime(ts) {
  const d = new Date(ts * 1000)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function api(path, opts = {}) {
  const token = localStorage.getItem('token')
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) }
  if (token) headers['Authorization'] = `Bearer ${token}`
  return fetch(path, { ...opts, headers })
}

function AuthPage({ onLogin }) {
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const res = await api(`/api/${mode}`, {
        method: 'POST',
        body: JSON.stringify({ username, password })
      })
      const data = await res.json()
      if (!res.ok) { setError(data.detail); return }
      localStorage.setItem('token', data.token)
      localStorage.setItem('username', data.username)
      onLogin(data.username)
    } catch { setError('网络错误') }
  }

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-sm">
        <h1 className="text-2xl font-bold text-center mb-6">文枢</h1>
        <div className="flex mb-6 border-b">
          <button onClick={() => { setMode('login'); setError('') }}
            className={`flex-1 pb-2 text-sm font-medium ${mode === 'login' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-400'}`}>登录</button>
          <button onClick={() => { setMode('register'); setError('') }}
            className={`flex-1 pb-2 text-sm font-medium ${mode === 'register' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-400'}`}>注册</button>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <input value={username} onChange={e => setUsername(e.target.value)} placeholder="用户名"
            className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <input value={password} onChange={e => setPassword(e.target.value)} type="password" placeholder="密码"
            className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button type="submit"
            className="w-full py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition">
            {mode === 'login' ? '登录' : '注册'}
          </button>
        </form>
      </div>
    </div>
  )
}

function Pagination({ page, totalPages, onPage }) {
  if (totalPages <= 1) return null
  const pages = []
  let start = Math.max(1, page - 2)
  let end = Math.min(totalPages, page + 2)
  if (end - start < 4) {
    if (start === 1) end = Math.min(totalPages, start + 4)
    else start = Math.max(1, end - 4)
  }
  for (let i = start; i <= end; i++) pages.push(i)
  const btn = (p, label, disabled = false) => (
    <button key={label} disabled={disabled || p === page} onClick={() => onPage(p)}
      className={`px-3 py-1.5 text-sm rounded border transition
        ${p === page ? 'bg-blue-500 text-white border-blue-500' : 'bg-white hover:bg-gray-50'}
        ${disabled ? 'opacity-40 cursor-not-allowed' : ''}`}>{label}</button>
  )
  return (
    <div className="flex items-center gap-1.5 mt-6 justify-center flex-wrap">
      {btn(1, '首页', page === 1)}
      {btn(page - 1, '‹', page === 1)}
      {start > 1 && <span className="px-1 text-gray-400">…</span>}
      {pages.map(p => btn(p, p))}
      {end < totalPages && <span className="px-1 text-gray-400">…</span>}
      {btn(page + 1, '›', page === totalPages)}
      {btn(totalPages, '尾页', page === totalPages)}
    </div>
  )
}

const TAG_COLORS = {
  '网盘': { bg: 'bg-purple-100', text: 'text-purple-700', active: 'bg-purple-500 text-white' },
  '日记': { bg: 'bg-amber-100', text: 'text-amber-700', active: 'bg-amber-500 text-white' },
  '代码': { bg: 'bg-emerald-100', text: 'text-emerald-700', active: 'bg-emerald-500 text-white' },
}
const DEFAULT_TAG_COLOR = { bg: 'bg-gray-100', text: 'text-gray-600', active: 'bg-gray-500 text-white' }

function LinkifyText({ text }) {
  const urlRegex = /(https?:\/\/[^\s]+)/g
  const parts = text.split(urlRegex)
  return (
    <>
      {parts.map((part, i) =>
        urlRegex.test(part) ? (
          <a key={i} href={part} target="_blank" rel="noopener noreferrer"
            className="text-blue-500 hover:underline break-all">{part}</a>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </>
  )
}

function MessageContent({ msg }) {
  const isCode = msg.tags && msg.tags.includes('代码')
  if (isCode) {
    return (
      <pre className="bg-gray-50 text-gray-700 rounded-lg p-4 overflow-x-auto text-sm font-mono leading-relaxed whitespace-pre-wrap break-all">
        <code>{msg.content}</code>
      </pre>
    )
  }
  return <LinkifyText text={msg.content} />
}

function TagBadge({ name, small = false }) {
  const c = TAG_COLORS[name] || DEFAULT_TAG_COLOR
  return (
    <span className={`inline-block rounded-full ${c.bg} ${c.text} ${small ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm'} font-medium`}>
      {name}
    </span>
  )
}

function MoreMenu({ onEdit, onDelete }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <div className="relative" ref={ref}>
      <button onClick={() => setOpen(!open)}
        className="w-7 h-7 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition text-lg leading-none">
        ⋯
      </button>
      {open && (
        <div className="absolute right-0 top-8 bg-white border rounded-lg shadow-lg py-1 z-10 min-w-[80px]">
          <button onClick={() => { onEdit(); setOpen(false) }}
            className="w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 text-left">
            编辑
          </button>
          <button onClick={() => { onDelete(); setOpen(false) }}
            className="w-full px-4 py-2 text-sm text-red-500 hover:bg-red-50 text-left">
            删除
          </button>
        </div>
      )}
    </div>
  )
}

function App() {
  const [username, setUsername] = useState(() => localStorage.getItem('username'))
  const [messages, setMessages] = useState([])
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [input, setInput] = useState('')
  const [page, setPage] = useState(1)
  const [copiedId, setCopiedId] = useState(null)
  const [tags, setTags] = useState([])
  const [activeTag, setActiveTag] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [editContent, setEditContent] = useState('')

  const fetchTags = useCallback(async () => {
    const res = await api('/api/tags')
    if (res.ok) setTags(await res.json())
  }, [])

  const fetchMessages = useCallback(async () => {
    let url = `/api/messages?page=${page}&page_size=${PAGE_SIZE}`
    if (activeTag) url += `&tag=${encodeURIComponent(activeTag)}`
    const res = await api(url)
    if (res.status === 401) { localStorage.clear(); setUsername(null); return }
    const data = await res.json()
    setMessages(data.items)
    setTotal(data.total)
    setTotalPages(data.total_pages)
  }, [page, activeTag])

  useEffect(() => { if (username) { fetchMessages(); fetchTags() } }, [username, fetchMessages, fetchTags])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim()) return
    await api('/api/messages', { method: 'POST', body: JSON.stringify({ content: input }) })
    setInput('')
    setPage(1)
    setActiveTag(null)
    fetchMessages()
    fetchTags()
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e) }
  }

  const toggleProcess = async (id) => {
    await api(`/api/messages/${id}/process`, { method: 'PUT' })
    fetchMessages()
  }

  const deleteMessage = async (id) => {
    await api(`/api/messages/${id}`, { method: 'DELETE' })
    fetchMessages()
    fetchTags()
  }

  const startEdit = (msg) => {
    setEditingId(msg.id)
    setEditContent(msg.content)
  }

  const saveEdit = async (id) => {
    if (!editContent.trim()) return
    await api(`/api/messages/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ content: editContent })
    })
    setEditingId(null)
    setEditContent('')
    fetchMessages()
    fetchTags()
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditContent('')
  }

  const copyToClipboard = (text, id) => {
    const ta = document.createElement('textarea')
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0'
    document.body.appendChild(ta); ta.select(); document.execCommand('copy')
    document.body.removeChild(ta)
    setCopiedId(id); setTimeout(() => setCopiedId(null), 1500)
  }

  const logout = () => { localStorage.clear(); setUsername(null) }

  const clickTag = (name) => {
    setActiveTag(prev => prev === name ? null : name)
    setPage(1)
  }

  if (!username) return <AuthPage onLogin={setUsername} />

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold">文枢</h1>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500">{username}</span>
            <button onClick={logout} className="text-sm text-gray-400 hover:text-gray-600">退出</button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mb-6 relative">
          <textarea value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown}
            placeholder="输入消息... (Enter 发送，Shift+Enter 换行)" rows={3}
            className="w-full p-3 pb-12 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono" />
          <button type="submit"
            className="absolute right-3 bottom-3 px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition">发布</button>
        </form>

        {tags.length > 0 && (
          <div className="flex items-center gap-2 mb-4 flex-wrap">
            <span className="text-sm text-gray-400 mr-1">标签：</span>
            {tags.map(t => {
              const c = TAG_COLORS[t.name] || DEFAULT_TAG_COLOR
              const isActive = activeTag === t.name
              return (
                <button key={t.name} onClick={() => clickTag(t.name)}
                  className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-sm font-medium transition
                    ${isActive ? c.active : `${c.bg} ${c.text} hover:opacity-80`}`}>
                  {t.name}
                  <span className={`text-xs ${isActive ? 'opacity-80' : 'opacity-50'}`}>{t.count}</span>
                </button>
              )
            })}
            {activeTag && (
              <button onClick={() => { setActiveTag(null); setPage(1) }}
                className="text-xs text-gray-400 hover:text-gray-600 ml-1">清除筛选</button>
            )}
          </div>
        )}

        <div className="text-sm text-gray-400 mb-3">
          共 {total} 条{activeTag ? ` · 筛选：${activeTag}` : ''}
        </div>

        <div className="space-y-3">
          {messages.map(msg => {
            const isCode = msg.tags && msg.tags.includes('代码')
            return (
              <div key={msg.id} className={`group p-4 rounded-lg border ${msg.is_processed ? 'bg-gray-50 border-gray-300' : 'bg-white border-gray-200'}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className={`flex items-start gap-2 min-w-0 flex-1 ${isCode ? 'flex-col' : ''}`}>
                    <span className="text-xs text-gray-400 font-mono shrink-0">#{msg.id}</span>
                    {editingId === msg.id ? (
                      <div className="flex-1 flex gap-2 w-full">
                        <textarea value={editContent} onChange={e => setEditContent(e.target.value)}
                          className="flex-1 p-2 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-mono"
                          rows={4} autoFocus
                          onKeyDown={e => { if (e.key === 'Enter' && e.metaKey) { saveEdit(msg.id) }; if (e.key === 'Escape') cancelEdit() }} />
                        <div className="flex flex-col gap-1">
                          <button onClick={() => saveEdit(msg.id)}
                            className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600">保存</button>
                          <button onClick={cancelEdit}
                            className="px-2 py-1 text-xs bg-gray-200 text-gray-600 rounded hover:bg-gray-300">取消</button>
                        </div>
                      </div>
                    ) : (
                      <div className={`flex-1 ${isCode ? 'w-full' : ''}`}>
                        <MessageContent msg={msg} />
                        {msg.is_edited && <span className="text-xs text-gray-400 ml-1">(已编辑)</span>}
                      </div>
                    )}
                  </div>
                  {editingId !== msg.id && (
                    <div className="flex items-center gap-1.5 shrink-0">
                      <button onClick={() => copyToClipboard(msg.content, msg.id)}
                        title="复制"
                        className={`w-7 h-7 flex items-center justify-center rounded-full transition text-sm
                          ${copiedId === msg.id ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-600'}`}>
                        {copiedId === msg.id ? '✓' : (
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <rect x="9" y="9" width="13" height="13" rx="2"/>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                          </svg>
                        )}
                      </button>
                      <button onClick={() => toggleProcess(msg.id)}
                        title={msg.is_processed ? '已处理' : '标为已处理'}
                        className={`w-7 h-7 flex items-center justify-center rounded-full transition text-sm
                          ${msg.is_processed
                            ? 'bg-green-100 text-green-600 hover:bg-green-200'
                            : 'bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-600'
                          }`}>
                        {msg.is_processed ? '✓' : '○'}
                      </button>
                      <MoreMenu onEdit={() => startEdit(msg)} onDelete={() => deleteMessage(msg.id)} />
                    </div>
                  )}
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <div className="flex gap-1.5">
                    {msg.tags.map(t => <TagBadge key={t} name={t} small />)}
                  </div>
                  <span className="text-xs text-gray-400">{formatTime(msg.created_at)}</span>
                </div>
              </div>
            )
          })}
        </div>

        <Pagination page={page} totalPages={totalPages} onPage={setPage} />
      </div>
    </div>
  )
}

export default App
