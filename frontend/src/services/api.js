import axios from 'axios';

// URL base da sua API Django (ajuste se necessário)
const API_BASE_URL = 'http://127.0.0.1:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  // timeout: 10000,
});

// Interceptor: Executa ANTES de cada requisição ser enviada
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// (Opcional) Adicionar interceptor de RESPOSTA para refresh token (lógica similar à versão TS)
// api.interceptors.response.use(...)

export default api;