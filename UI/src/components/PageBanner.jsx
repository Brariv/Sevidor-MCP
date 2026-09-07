export default function PageBanner({ title }) {
  return (
    <div style={{ borderBottom: '1px solid #e9eaeb', padding: '54px 24px 60px', textAlign: 'center' }}>
      <h1 style={{ margin: 0, color: '#e01212', fontSize: 46, fontWeight: 400, letterSpacing: '.4px' }}>
        {title}
      </h1>
    </div>
  );
}
