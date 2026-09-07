import { useState } from 'react';

export default function SearchBar({ query, onQuery }) {
  const [hover, setHover] = useState(false);

  return (
    <div style={{ marginBottom: 54, maxWidth: 760 }}>
      <div style={{ fontSize: 15, color: '#5f6368', marginBottom: 10 }}>Buscar</div>
      <div style={{ display: 'flex' }}>
        <input
          type="text"
          placeholder="Buscar productos..."
          value={query}
          onChange={(e) => onQuery(e.target.value)}
          style={{
            flex: 1,
            height: 48,
            border: '1px solid #dfe1e3',
            borderRight: 'none',
            background: '#fafbfc',
            padding: '0 15px',
            fontSize: 15,
            fontFamily: 'Roboto, sans-serif',
            color: '#3c4043',
            outline: 'none',
          }}
        />
        <div
          onMouseEnter={() => setHover(true)}
          onMouseLeave={() => setHover(false)}
          style={{
            width: 58,
            height: 48,
            border: '1px solid #dfe1e3',
            background: hover ? '#dae4ee' : '#e9eff5',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3c4043" strokeWidth="2">
            <path d="M9 4l8 8-8 8" />
          </svg>
        </div>
      </div>
    </div>
  );
}
