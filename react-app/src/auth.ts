import axios from 'axios';

// 1. Use VITE_API_URL (to match Vercel) 
// 2. Hardcode the fallback to Hugging Face to be safe
const API_BASE = (import.meta as any).env.VITE_API_URL || 'https://arifantarctic7-smart-supply-chain-agent.hf.space';

let token: string | null = localStorage.getItem('auth_token');

const authApi = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ... rest of the file

// Add Authorization header to all requests
authApi.interceptors.request.use((config) => {
  const currentToken = localStorage.getItem('auth_token');
  if (currentToken) {
    config.headers.Authorization = `Bearer ${currentToken}`;
  }
  return config;
});

// Handle 401 responses
authApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const login = async (username: string, password: string) => {
  console.log('Auth: Attempting login for', username);
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);

  try {
    const response = await axios.post(`${API_BASE}/token`, formData);
    console.log('Auth: Login response received', response);
    token = response.data.access_token;
    if (token) {
      localStorage.setItem('auth_token', token);
      console.log('Auth: Token stored');
    } else {
      console.error('Auth: No token in response', response.data);
    }
    return response.data;
  } catch (error) {
    console.error('Auth: Login request failed', error);
    throw error;
  }
};

export const logout = () => {
  token = null;
  localStorage.removeItem('auth_token');
};

export const getToken = () => token || localStorage.getItem('auth_token');

export const isAuthenticated = () => !!getToken();

export default authApi;
