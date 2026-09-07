export default function CategorySidebar({ categories }) {
  return (
    <aside style={{ width: 300, flex: 'none', background: '#f4f6f8', padding: '26px 30px 30px' }}>
      <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 22 }}>
        {categories.map((cat, i) => (
          <li key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ width: 6, height: 6, background: '#8a8d90', flex: 'none' }} />
            <div style={{ height: 11, borderRadius: 2, background: '#c8cacc', width: cat.w }} />
          </li>
        ))}
      </ul>
    </aside>
  );
}
