export default function Header() {
  return (
    <header
      style={{
        background: '#d10a0a',
        height: 56,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 22px',
      }}
    >
      <div
        style={{
          width: 36,
          height: 36,
          background: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flex: 'none',
        }}
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d10a0a" strokeWidth="1.7">
          <path d="M12 3.5L20 20.5H4z" />
          <path d="M8.6 14.2h6.8" />
        </svg>
      </div>
      <div style={{ color: '#ffffff', fontSize: 17, letterSpacing: '.2px' }}>Tienda Online</div>
      <div style={{ width: 36, display: 'flex', justifyContent: 'flex-end', cursor: 'pointer' }}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="#b40a0a">
          <path d="M7.5 18.5a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm9.5 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM1 2.5h3.4l2.2 10.6h11.3L21 6H7.1" />
        </svg>
      </div>
    </header>
  );
}
