import { useState, useRef, useEffect } from 'react'

type Message = {
  role: 'user' | 'assistant';
  content: string;
}

function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [status, setStatus] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const msgsEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    msgsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, status])

  const sendMessage = async () => {
    if (!input.trim()) return
    const userText = input
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userText }])
    setMessages(prev => [...prev, { role: 'assistant', content: '' }]) // 占位
    setIsLoading(true)
    setStatus('初始化...')

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userText })
      })

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader!.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        buffer += chunk
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)
            if (dataStr === '[DONE]') break

            const data = JSON.parse(dataStr)

            if (data.type === 'token') {
              // 类似 Elixir 的 reduce 更新状态
              setMessages(prev => {
                const newMsgs = [...prev]
                const last = newMsgs[newMsgs.length - 1]
                last.content += data.content
                return newMsgs
              })
            } else if (data.type === 'status') {
              setStatus(data.content)
            }
          }
        }
      }
    } catch (e) {
      console.error(e)
    } finally {
      setIsLoading(false)
      setStatus('')
    }
  }

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '20px', fontFamily: 'sans-serif' }}>
      <h1>Reflective Chatbot</h1>

      <div style={{ height: '400px', overflowY: 'auto', border: '1px solid #ccc', padding: '10px', borderRadius: '8px' }}>
        {messages.map((m, i) => (
          <div key={i} style={{
            textAlign: m.role === 'user' ? 'right' : 'left',
            margin: '10px 0'
          }}>
            <span style={{
              background: m.role === 'user' ? '#007bff' : '#f1f1f1',
              color: m.role === 'user' ? 'white' : 'black',
              padding: '8px 12px',
              borderRadius: '12px',
              display: 'inline-block'
            }}>
              {m.content}
            </span>
          </div>
        ))}
        {isLoading && <div style={{ fontSize: '12px', color: '#666', fontStyle: 'italic' }}>🤖 {status}</div>}
        <div ref={msgsEndRef} />
      </div>

      <div style={{ marginTop: '10px', display: 'flex', gap: '10px' }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage()}
          style={{ flex: 1, padding: '10px' }}
          placeholder="试着说一句简短的话 (触发反思机制)..."
        />
        <button onClick={sendMessage} disabled={isLoading} style={{ padding: '10px 20px' }}>发送</button>
      </div>
    </div>
  )
}

export default App
