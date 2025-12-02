import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getProducts } from '../api';
import './Home.css';

function Home() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const data = await getProducts();
        // Handle both array and object response formats
        const productList = Array.isArray(data) ? data : (data.products || []);
        setProducts(productList);
      } catch (err) {
        setError('Failed to load products. Please ensure the backend is running.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
  }, []);

  // Filter products based on search
  const filteredProducts = products.filter(p => 
    !searchTerm || 
    (p.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (p.description || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) return <div className="loading">Loading products...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="home">
      <h1>Traya Health Products</h1>
      <p className="subtitle">AI-Powered Product Discovery</p>
      
      <div className="search-bar">
        <input
          type="text"
          placeholder="Search products..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <span className="product-count">{filteredProducts.length} products</span>
      </div>
      
      <div className="products-grid">
        {filteredProducts.map((product) => (
          <Link to={`/product/${product.id}`} key={product.id} className="product-card">
            <div className="product-image">
              <img 
                src={product.image_url || 'https://via.placeholder.com/200'} 
                alt={product.title}
                onError={(e) => { e.target.src = 'https://via.placeholder.com/200'; }}
              />
            </div>
            <div className="product-info">
              <h3>{product.title}</h3>
              <p className="price">{product.price || 'Price N/A'}</p>
              <p className="category">{product.category}</p>
            </div>
          </Link>
        ))}
      </div>
      
      {filteredProducts.length === 0 && (
        <div className="no-results">
          No products found matching "{searchTerm}"
        </div>
      )}
    </div>
  );
}

export default Home;
