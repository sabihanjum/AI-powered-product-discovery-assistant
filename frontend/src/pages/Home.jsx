import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { getProducts } from '../api';
import './Home.css';

function Home() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [retryCount, setRetryCount] = useState(0);
  const [isWakingUp, setIsWakingUp] = useState(false);

  const fetchProducts = useCallback(async (isRetry = false) => {
    if (isRetry) {
      setIsWakingUp(true);
      setError(null);
    }
    setLoading(true);
    
    try {
      const data = await getProducts();
      // Handle both array and object response formats
      const productList = Array.isArray(data) ? data : (data.products || []);
      setProducts(productList);
      setError(null);
      setIsWakingUp(false);
    } catch (err) {
      console.error(err);
      // Auto-retry up to 3 times for cold start
      if (retryCount < 3) {
        setIsWakingUp(true);
        setError(null);
        setTimeout(() => {
          setRetryCount(prev => prev + 1);
        }, 3000); // Wait 3 seconds before retry
      } else {
        setError('Backend is taking longer than expected. Please click "Retry" or wait a moment.');
        setIsWakingUp(false);
      }
    } finally {
      setLoading(false);
    }
  }, [retryCount]);

  useEffect(() => {
    fetchProducts();
  }, [retryCount]);

  const handleRetry = () => {
    setRetryCount(0);
    fetchProducts(true);
  };

  // Filter products based on search
  const filteredProducts = products.filter(p => 
    !searchTerm || 
    (p.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (p.description || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading || isWakingUp) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        <p>{isWakingUp ? '⏳ Server is waking up... (Free tier cold start)' : 'Loading products...'}</p>
        {isWakingUp && <p className="loading-hint">This may take 30-60 seconds on first visit</p>}
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="error">
        <p>{error}</p>
        <button onClick={handleRetry} className="retry-btn">🔄 Retry</button>
        <p className="error-hint">Free tier servers spin down after 15 minutes of inactivity</p>
      </div>
    );
  }

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
