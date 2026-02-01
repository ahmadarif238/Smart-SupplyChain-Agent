import axios from 'axios';

const API_BASE = (import.meta as any).env.VITE_API_BASE || 'http://127.0.0.1:8000';

// DEMO MODE: Set to true for public demo (no login required)
const DEMO_MODE = true;

let token: string | null = localStorage.getItem('auth_token');

const authApi = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add Authorization header to all requests (only if not in demo mode)
authApi.interceptors.request.use((config) => {
  if (!DEMO_MODE) {
    const currentToken = localStorage.getItem('auth_token');
    if (currentToken) {
      config.headers.Authorization = `Bearer ${currentToken}`;
    }
  }
  return config;
});

// Handle 401 responses (disabled in demo mode)
authApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!DEMO_MODE && error.response?.status === 401) {
      logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const login = async (username: string, password: string) => {
  if (DEMO_MODE) {
    // In demo mode, simulate successful login
    return { access_token: 'demo_token', token_type: 'bearer' };
  }

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

// DEMO MODE: Always return true to skip login
export const isAuthenticated = () => DEMO_MODE ? true : !!getToken();

export default authApi;

