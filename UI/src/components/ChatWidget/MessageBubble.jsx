import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function MessageBubble({ role, text, tools = [] }) {
  const isUser = role === 'user';

  return (
    <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
      <div
        className={`chat-bubble ${isUser ? 'user' : 'assistant'}`}
        style={{
          maxWidth: '85%',
          background: isUser ? '#d10a0a' : '#f4f6f8',
          color: isUser ? '#ffffff' : '#3c4043',
          borderRadius: 14,
          borderBottomRightRadius: isUser ? 3 : 14,
          borderBottomLeftRadius: isUser ? 14 : 3,
          padding: '10px 14px',
          fontSize: 14,
          lineHeight: 1.5,
          wordBreak: 'break-word',
        }}
      >
        {/* Tool chips: show which MCP tools the assistant used for this answer */}
        {!isUser && tools.length > 0 && (
          <div className="chat-bubble-tools">
            {tools.map((t, i) => (
              <span key={i} className="chat-bubble-chip" title={JSON.stringify(t.argumentos)}>
                🔧 {t.nombre}
              </span>
            ))}
          </div>
        )}

        {isUser ? (
          text
        ) : (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({ node, ...props }) => (
                <a {...props} target="_blank" rel="noopener noreferrer" />
              ),
            }}
          >
            {text}
          </ReactMarkdown>
        )}
      </div>
    </div>
  );
}
