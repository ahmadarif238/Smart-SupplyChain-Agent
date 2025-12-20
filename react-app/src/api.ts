import axios from 'axios';

// This looks for a Vercel variable first, then falls back to localhost for your computer
const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add Authorization header to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Error handler with detailed logging
api.interceptors.response.use(
  (response: any) => response,
  (error: any) => {
    if (error.response) {
      console.error('API Error Response:', error.response.status, error.response.data);
      // Handle 401 by redirecting to login
      if (error.response.status === 401) {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
      }
    } else if (error.request) {
      console.error('No response from API:', error.request);
    } else {
      console.error('API Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export const apiService = {
  // Health
  health: () => api.get('/health'),

  // Inventory
  inventory: {
    list: () => api.get('/inventory/'),
    add: (data: any) => api.post('/inventory/', data),
    forecast: () => api.get('/inventory/forecast'),
  },

  // Sales
  sales: {
    list: () => api.get('/sales/'),
    add: (data: any) => api.post('/sales/', data),
    summary: () => api.get('/sales/summary'),
  },

  // Orders
  orders: {
    list: () => api.get('/orders/'),
    create: (sku: string, quantity: number) => api.post('/orders/', { sku, quantity }),
    recommend: () => api.get('/orders/recommend'),
  },

  // Alerts
  alerts: {
    list: () => api.get('/alerts/'),
    create: (message: string, type: string) => api.post('/alerts/', { message, type }),
    analyze: () => api.get('/alerts/analyze'),
  },

  // Agent
  agent: {
    runOnce: () => {
      console.log('Making POST request to /agent/run_once');
      return api.post('/agent/run_once', {}, {
        headers: {
          'Content-Type': 'application/json',
        }
      }).then(response => {
        console.log('Agent runOnce response:', response);
        return response;
      }).catch(error => {
        console.error('Agent runOnce failed:', error.message);
        if (error.response) {
          console.error('Response status:', error.response.status);
          console.error('Response data:', error.response.data);
        }
        throw error;
      });
    },
    status: () => api.get('/agent/status'),
    jobs: () => api.get('/agent/jobs'),
    jobStatus: (jobId: string) => api.get(`/agent/job/${jobId}`),
    getSummary: (jobId: string) => api.get(`/agent/jobs/${jobId}/summary`),
    memory: () => api.get('/agent/memory'),
    learnedParams: () => api.get('/agent/learned-parameters'),
    feedbackHistory: (sku: string) => api.get(`/agent/feedback/history/${sku}`),
    submitFeedback: (data: any) => api.post('/agent/feedback', data),
    financeSummary: () => api.get('/agent/finance-summary'),
  },

  // Memory & Learning
  memory: {
    list: () => api.get('/memory/'),
  },

  feedback: {
    submit: (data: any) => api.post('/agent/feedback', data),
    history: (sku: string) => api.get(`/agent/feedback/history/${sku}`),
    learnedParams: () => api.get('/agent/learned-parameters'),
  },

  // Analyst Chat
  chat: {
    send: (message: string) => api.post('/chat/', { message }),
  },

  // Admin endpoints
  admin: {
    initLearning: () => api.post('/admin/init-learning', {}),
    triggerLearning: () => api.post('/admin/trigger-learning', {}),
  },

  // Generic methods
  get: (url: string) => api.get(url),
  post: (url: string, data?: any) => api.post(url, data),
};

export default api;
