import { useEffect, useRef, useState } from 'react';
import { sendChatMessage } from '../../api/chatClient';
import MessageBubble from './MessageBubble';
import { ChatIcon, CloseIcon, SendIcon } from './icons';
import './ChatWidget.css';

const WELCOME_MESSAGE = {
  role: 'assistant',
  text: '¡Hola! Soy tu asistente virtual. Si tienes alguna pregunta sobre nuestros productos, no dudes en escribirme. Estoy aquí para ayudarte.',
};

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (open) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, open, loading]);

  useEffect(() => {
    if (open) {
      inputRef.current?.focus();
    }
  }, [open]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    const history = messages;
    const nextMessages = [...history, { role: 'user', text }];
    setMessages(nextMessages);
    setInput('');
    setError(null);
    setLoading(true);

    try {
      const { reply, tools } = await sendChatMessage(text);
      setMessages((prev) => [...prev, { role: 'assistant', text: reply, tools }]);
    } catch (err) {
      setError('No se pudo conectar con el asistente. Intenta de nuevo.');
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div style={{ fontFamily: 'Roboto, system-ui, sans-serif' }}>
      {open && (
        <div
          role="dialog"
          aria-label="Asistente virtual"
          style={{
            position: 'fixed',
            right: 24,
            bottom: 96,
            width: 360,
            maxWidth: 'calc(100vw - 32px)',
            height: 520,
            maxHeight: 'calc(100vh - 140px)',
            background: '#ffffff',
            borderRadius: 12,
            boxShadow: '0 12px 32px rgba(0,0,0,.18)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            zIndex: 1000,
          }}
        >
          <div
            style={{
              background: '#d10a0a',
              height: 56,
              flex: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 16px',
            }}
          >
            <div style={{ color: '#ffffff', fontSize: 15, fontWeight: 500 }}>Asistente</div>
            <div
              onClick={() => setOpen(false)}
              role="button"
              aria-label="Cerrar chat"
              style={{ cursor: 'pointer', width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >
              <CloseIcon />
            </div>
          </div>

          <div
            className="chat-widget-messages"
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: 16,
              display: 'flex',
              flexDirection: 'column',
              gap: 10,
              background: '#ffffff',
            }}
          >
            {messages.map((m, i) => (
              <MessageBubble key={i} role={m.role} text={m.text} />
            ))}
            {loading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div
                  style={{
                    background: '#f4f6f8',
                    borderRadius: 14,
                    borderBottomLeftRadius: 3,
                    padding: '12px 14px',
                    display: 'flex',
                    gap: 4,
                    alignItems: 'center',
                  }}
                >
                  <span className="chat-widget-dot" />
                  <span className="chat-widget-dot" />
                  <span className="chat-widget-dot" />
                </div>
              </div>
            )}
            {error && (
              <div style={{ color: '#d10a0a', fontSize: 13, padding: '0 2px' }}>{error}</div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div style={{ borderTop: '1px solid #e9eaeb', padding: 12, display: 'flex', gap: 8, flex: 'none' }}>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Escribe un mensaje..."
              disabled={loading}
              style={{
                flex: 1,
                height: 42,
                border: '1px solid #dfe1e3',
                background: '#fafbfc',
                padding: '0 13px',
                fontSize: 14,
                fontFamily: 'Roboto, sans-serif',
                color: '#3c4043',
                outline: 'none',
                borderRadius: 6,
              }}
            />
            <button
              type="button"
              onClick={handleSend}
              disabled={loading || !input.trim()}
              aria-label="Enviar mensaje"
              style={{
                width: 42,
                height: 42,
                flex: 'none',
                border: 'none',
                borderRadius: 6,
                background: loading || !input.trim() ? '#e6a3a3' : '#d10a0a',
                cursor: loading || !input.trim() ? 'default' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <SendIcon />
            </button>
          </div>
        </div>
      )}

      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? 'Cerrar chat' : 'Abrir chat'}
        style={{
          position: 'fixed',
          right: 24,
          bottom: 24,
          width: 56,
          height: 56,
          borderRadius: '50%',
          border: 'none',
          background: '#d10a0a',
          boxShadow: '0 6px 18px rgba(0,0,0,.22)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}
      >
        {open ? <CloseIcon width={22} height={22} /> : <ChatIcon />}
      </button>
    </div>
  );
}
