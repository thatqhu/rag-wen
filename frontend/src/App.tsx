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
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, status])

  const sendMessage = async () => {
    if (!input.trim()) return
    const userMsg = input
    setInput('')

    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])
    setIsLoading(true)
    setStatus('Initializing Agent...')

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      })

      if (!response.body) throw new Error('No response body')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6)
            if (jsonStr === '[DONE]') break

            try {
              const data = JSON.parse(jsonStr)

              if (data.type === 'status') {
                setStatus(data.content)
              }  else if (data.type === 'result') {
                setMessages(prev => {
                const newMsgs = [...prev]
                const lastMsg = newMsgs[newMsgs.length - 1]

                if (lastMsg.role === 'assistant') {
                    lastMsg.content = data.content
                } else {
                    newMsgs.push({ role: 'assistant', content: data.content })
                }
                return newMsgs
              })
            }
            } catch (e) {
              console.error('Parse error', e)
            }
          }
        }
      }
    } catch (err) {
      console.error(err)
      setMessages(prev => [...prev, { role: 'assistant', content: 'Failed to connect to server' }])
    } finally {
      setIsLoading(false)
      setStatus('')
    }
  }

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '20px', fontFamily: 'system-ui' }}>
      <header style={{ marginBottom: '20px', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
        <h2 style={{ margin: 0 }}>Chatbox with LangGraph</h2>
      </header>

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

        {isLoading && status && (
          <div style={{ alignSelf: 'flex-start', color: '#888', fontSize: '0.9em', fontStyle: 'italic' }}>
            {status}
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !isLoading && sendMessage()}
          placeholder="Input question (Like: get the weather for New York city)..."
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
          SEND
        </button>
      </div>
    </div>
  )
}

export default App
