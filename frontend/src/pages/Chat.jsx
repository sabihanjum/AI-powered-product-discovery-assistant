import { useState, useRef, useEffect } from 'react'
import { sendChatMessage } from '../api'
import './Chat.css'

function Chat() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hi! I\'m your AI shopping assistant. Ask me anything about hair care, skin care, or wellness products. For example:\n\n• "I\'m losing hair, what can help?"\n• "What products are good for dandruff?"\n• "I want something for better sleep"'
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const response = await sendChatMessage(userMessage)
      console.log('Chat response:', response)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.message || 'No response received',
        products: response.recommendations || []
      }])
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.'
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>🤖 AI Product Assistant</h1>
        <p>Ask me about products for your health and wellness needs</p>
      </div>

      <div className="messages-container">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.content}
              {msg.products && msg.products.length > 0 && (
                <div className="suggested-products">
                  <p className="products-label">Related Products:</p>
                  <div className="product-chips">
                    {msg.products.map((product, pidx) => (
                      <a 
                        key={pidx} 
                        href={`/product/${product.product_id}`}
                        className="product-chip"
                      >
                        {product.title}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="message-content typing">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about products..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  )
}

export default Chat
