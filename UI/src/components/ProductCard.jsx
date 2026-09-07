import { useState } from 'react';

export default function ProductCard({ w1, w2 }) {
  const [hover, setHover] = useState(false);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
      <div
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        style={{
          position: 'relative',
          width: '100%',
          aspectRatio: '1/1',
          background: '#f2f2f2',
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <svg width="72" height="72" viewBox="0 0 24 24" fill="#c9cacb">
          <path d="M3 5h18v14H3z" fill="none" stroke="#c9cacb" strokeWidth="1.4" />
          <circle cx="8.5" cy="10" r="1.7" />
          <path d="M5 17l4.5-5 3 3.5L16 11l3 6z" />
        </svg>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: hover ? 1 : 0,
            transition: 'opacity .18s',
          }}
        >
          <div style={{ background: '#d10a0a', padding: '16px 26px', display: 'flex', gap: 26, alignItems: 'center' }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="1.7">
              <path d="M5 8h14l-1.2 12H6.2z" />
              <path d="M9 8V6a3 3 0 0 1 6 0v2" />
            </svg>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="1.7">
              <path d="M9.5 14.5l5-5" />
              <path d="M13 7.5l1.5-1.5a3.5 3.5 0 0 1 5 5L18 12.5" />
              <path d="M11 16.5L9.5 18a3.5 3.5 0 0 1-5-5L6 11.5" />
            </svg>
          </div>
        </div>
      </div>
      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, marginTop: 22 }}>
        <div style={{ height: 16, borderRadius: 2, background: '#c8cacc', width: w1 }} />
        <div style={{ height: 16, borderRadius: 2, background: '#c8cacc', width: w2 }} />
        <div style={{ height: 11, borderRadius: 2, background: '#d8d9db', width: '44%', marginTop: 4 }} />
        <div style={{ height: 14, borderRadius: 2, background: '#c8cacc', width: '38%', marginTop: 4 }} />
      </div>
    </div>
  );
}
