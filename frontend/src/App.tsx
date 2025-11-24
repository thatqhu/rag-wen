import { useState, useRef, useEffect } from 'react'

// 类型定义
type Message = {
  role: 'user' | 'assistant';
  content: string;
}

function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [status, setStatus] = useState('') // 显示后台状态 (搜索中/反思中)
  const [isLoading, setIsLoading] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  // 自动滚动
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, status])

  const sendMessage = async () => {
    if (!input.trim()) return
    const userMsg = input
    setInput('')

    // 1. UI 乐观更新：先显示用户消息
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setMessages(prev => [...prev, { role: 'assistant', content: '' }]) // 占位符
    setIsLoading(true)
    setStatus('正在初始化 Agent...')

    try {
      // 2. 发起请求 (注意 URL 端口是 8000)
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      })

      if (!response.body) throw new Error('No response body')

      // 3. 处理 SSE 流
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n') // SSE 标准分隔符
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6)
            if (jsonStr === '[DONE]') break

            try {
              const data = JSON.parse(jsonStr)

              if (data.type === 'token') {
                // 收到文本 Token -> 更新最后一条消息
                setMessages(prev => {
                  const newMsgs = [...prev]
                  const lastMsg = newMsgs[newMsgs.length - 1]
                  lastMsg.content += data.content
                  return newMsgs
                })
              } else if (data.type === 'status') {
                // 收到状态更新 -> 更新状态栏
                setStatus(data.content)
              }
            } catch (e) {
              console.error('Parse error', e)
            }
          }
        }
      }
    } catch (err) {
      console.error(err)
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ 连接服务器失败' }])
    } finally {
      setIsLoading(false)
      setStatus('')
    }
  }

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '20px', fontFamily: 'system-ui' }}>
      <header style={{ marginBottom: '20px', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
        <h2 style={{ margin: 0 }}>LangGraph Explorer</h2>
        <small style={{ color: '#666' }}>Elixir Mindset Edition 💧</small>
      </header>

      {/* 消息列表 */}
      <div style={{
        height: '60vh',
        overflowY: 'auto',
        background: '#f9f9f9',
        borderRadius: '10px',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px'
      }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{
            alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '80%',
            padding: '10px 15px',
            borderRadius: '15px',
            background: msg.role === 'user' ? '#007AFF' : '#E5E5EA',
            color: msg.role === 'user' ? 'white' : 'black',
            lineHeight: '1.5'
          }}>
            {msg.content}
          </div>
        ))}

        {/* 状态指示器 */}
        {isLoading && status && (
          <div style={{ alignSelf: 'flex-start', color: '#888', fontSize: '0.9em', fontStyle: 'italic' }}>
            {status}
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* 输入框 */}
      <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !isLoading && sendMessage()}
          placeholder="输入问题 (例如: 搜索关于 iPhone 16 的新闻)..."
          style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid #ccc' }}
          disabled={isLoading}
        />
        <button
          onClick={sendMessage}
          disabled={isLoading}
          style={{
            padding: '0 20px',
            borderRadius: '8px',
            border: 'none',
            background: isLoading ? '#ccc' : '#007AFF',
            color: 'white',
            cursor: isLoading ? 'not-allowed' : 'pointer'
          }}
        >
          发送
        </button>
      </div>
    </div>
  )
}

export default App
