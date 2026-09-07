export default function MessageBubble({ role, text }) {
  const isUser = role === 'user';

  return (
    <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
      <div
        style={{
          maxWidth: '78%',
          padding: '10px 14px',
          borderRadius: 14,
          borderBottomRightRadius: isUser ? 3 : 14,
          borderBottomLeftRadius: isUser ? 14 : 3,
          background: isUser ? '#d10a0a' : '#f4f6f8',
          color: isUser ? '#ffffff' : '#3c4043',
          fontSize: 14,
          lineHeight: 1.4,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {text}
      </div>
    </div>
  );
}
