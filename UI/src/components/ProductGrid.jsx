import ProductCard from './ProductCard';

export default function ProductGrid({ products }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(200px,1fr))', gap: '38px 34px' }}>
      {products.map((p, i) => (
        <ProductCard key={i} w1={p.w1} w2={p.w2} />
      ))}
    </div>
  );
}
