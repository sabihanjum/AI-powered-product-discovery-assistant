import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getProduct } from '../api';
import './ProductDetail.css';

function ProductDetail() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        const data = await getProduct(id);
        setProduct(data);
      } catch (err) {
        setError('Failed to load product');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchProduct();
  }, [id]);

  if (loading) return <div className="loading">Loading product...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!product) return <div className="error">Product not found</div>;

  const features = product.features || {};
  const featureList = Array.isArray(features) 
    ? features 
    : typeof features === 'object' 
      ? Object.entries(features).map(([k, v]) => `${k}: ${v}`)
      : [];

  return (
    <div className="product-detail">
      <Link to="/" className="back-link">← Back to Products</Link>
      
      <div className="product-container">
        <div className="product-image-large">
          <img 
            src={product.image_url || 'https://via.placeholder.com/400'} 
            alt={product.title}
            onError={(e) => { e.target.src = 'https://via.placeholder.com/400'; }}
          />
        </div>
        
        <div className="product-details">
          <span className="category-badge">{product.category}</span>
          <h1>{product.title}</h1>
          <p className="price">{product.price || 'Price N/A'}</p>
          
          <div className="description">
            <h3>Description</h3>
            <p>{product.description || 'No description available.'}</p>
          </div>
          
          {featureList.length > 0 && (
            <div className="features">
              <h3>Features</h3>
              <ul>
                {featureList.map((feature, idx) => (
                  <li key={idx}>{typeof feature === 'string' ? feature : JSON.stringify(feature)}</li>
                ))}
              </ul>
            </div>
          )}
          
          {product.source_url && (
            <a href={product.source_url} target="_blank" rel="noopener noreferrer" className="source-link">
              View on Traya.health →
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProductDetail;
