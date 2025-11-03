import axios from 'axios';
import { jwtDecode } from 'jwt-decode'; // Certifique-se de que 'jwt-decode' está instalado

// Define a URL base da API
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api', // O /api JÁ ESTÁ AQUI
});

// --- Interceptor de Requisição (Adiciona o Token) ---
// Isso é o que resolve o erro 401
api.interceptors.request.use(
  async (config) => {
    let accessToken = localStorage.getItem('accessToken');

    if (accessToken) {
      const user = jwtDecode(accessToken);
      const isExpired = user.exp * 1000 < Date.now();

      if (!isExpired) {
        // Se não expirou, apenas adiciona o header
        config.headers.Authorization = `Bearer ${accessToken}`;
        return config;
      }
      
      // --- Se expirou, tenta atualizar (Refresh Token) ---
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
         // Se não tem refresh, desloga
         console.log('Sessão expirada, refreshToken não encontrado.');
         // (Opcional: redirecionar para login) window.location.href = '/login';
         return Promise.reject(new Error('Sessão expirada.'));
      }
      
      try {
        console.log("Token expirado. Tentando atualizar...");
        // O endpoint de refresh NÃO PODE ter o interceptor de auth
        // Assumindo que o endpoint de refresh é /auth/token/refresh/
        const rs = await axios.post('http://127.0.0.1:8000/api/auth/token/refresh/', {
           refresh: refreshToken,
        });

        const { access } = rs.data;
        localStorage.setItem('accessToken', access);
        config.headers.Authorization = `Bearer ${access}`;
        console.log("Token atualizado com sucesso.");
        return config;

      } catch (refreshError) {
        console.error("Falha ao atualizar o token:", refreshError);
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user_nome');
        localStorage.removeItem('user_email');
        // Redireciona para login se o refresh falhar
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    // Se não tinha token, a requisição segue (ex: /login)
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;