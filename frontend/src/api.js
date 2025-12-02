import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000, // 60 second timeout for AI responses
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getProducts = async (skip = 0, limit = 100) => {
  const response = await api.get(`/api/products?skip=${skip}&limit=${limit}`);
  return response.data;
};

export const getProduct = async (id) => {
  const response = await api.get(`/api/products/${id}`);
  return response.data;
};

export const sendChatMessage = async (message) => {
  const response = await api.post('/api/chat', { message });
  return response.data;
};

export default api;
