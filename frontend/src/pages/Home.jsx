import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getProducts } from '../api';
import './Home.css';

function Home() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const data = await getProducts();
        setProducts(data);
      } catch (err) {
        setError('Failed to load products');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
  }, []);

  if (loading) return <div className="loading">Loading products...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="home">
      <h1>Traya Health Products</h1>
      <p className="subtitle">AI-Powered Product Discovery</p>
      
      <div className="products-grid">
        {products.map((product) => (
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
    </div>
  );
}

export default Home;
