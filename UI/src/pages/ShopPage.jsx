import { useMemo, useState } from 'react';
import Header from '../components/Header';
import PageBanner from '../components/PageBanner';
import SearchBar from '../components/SearchBar';
import ProductGrid from '../components/ProductGrid';
import CategorySidebar from '../components/CategorySidebar';

const CATEGORY_COUNT = 18;

export default function ShopPage({ productCount = 8 }) {
  const [query, setQuery] = useState('');

  const products = useMemo(
    () =>
      Array.from({ length: productCount }, (_, i) => ({
        w1: 72 + ((i * 37) % 24) + '%',
        w2: 46 + ((i * 23) % 30) + '%',
      })),
    [productCount],
  );

  const categories = useMemo(
    () =>
      Array.from({ length: CATEGORY_COUNT }, (_, i) => ({
        w: 52 + ((i * 41) % 74) + '%',
      })),
    [],
  );

  return (
    <div style={{ fontFamily: 'Roboto, system-ui, sans-serif', background: '#ffffff', color: '#3c4043' }}>
      <Header />
      <PageBanner title="Shop" />

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '42px 24px 90px', display: 'flex', gap: 48, alignItems: 'flex-start' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <SearchBar query={query} onQuery={setQuery} />
          <ProductGrid products={products} />
        </div>

        <CategorySidebar categories={categories} />
      </div>
    </div>
  );
}
