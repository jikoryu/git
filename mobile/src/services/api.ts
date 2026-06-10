import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../store/authStore';

// Configure this to your backend URL.
// In development with Expo Go on a physical device, use your machine's LAN IP.
const API_BASE = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor: attach access token ──
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().accessToken;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// ── Response interceptor: handle 401, attempt token refresh ──
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

const processQueue = (token: string | null, err: unknown = null) => {
  failedQueue.forEach((p) => {
    if (token) p.resolve(token);
    else p.reject(err);
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({
          resolve: (token: string) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            resolve(api(originalRequest));
          },
          reject,
        });
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const refreshToken = useAuthStore.getState().refreshToken;
      if (!refreshToken) {
        useAuthStore.getState().logout();
        return Promise.reject(error);
      }

      const { data } = await axios.post(`${API_BASE}/auth/refresh`, {
        refresh_token: refreshToken,
      });

      useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
      processQueue(data.access_token);

      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
      }
      return api(originalRequest);
    } catch (refreshError) {
      processQueue(null, refreshError);
      useAuthStore.getState().logout();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);

export default api;

// ── API helper functions ──

// Auth
export const authApi = {
  register: (email: string, password: string) =>
    api.post('/auth/register', { email, password }),

  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),

  refresh: (refresh_token: string) =>
    api.post('/auth/refresh', { refresh_token }),

  getMe: () => api.get('/auth/me'),

  updateFcmToken: (fcm_token: string) =>
    api.put('/auth/me/fcm-token', { fcm_token }),
};

// Products
export const productsApi = {
  search: (q: string, platform?: string, page = 1) =>
    api.get('/products/search', { params: { q, platform, page } }),

  getById: (id: string) => api.get(`/products/${id}`),

  getHistory: (id: string, days = 30) =>
    api.get(`/products/${id}/history`, { params: { days } }),

  lookup: (url: string) => api.post('/products/lookup', { url }),
};

// Watchlist
export const watchlistApi = {
  getAll: () => api.get('/watchlist/'),

  add: (product_id: string, target_price?: number, notify_on_any_drop = true) =>
    api.post('/watchlist/', { product_id, target_price, notify_on_any_drop }),

  remove: (item_id: string) => api.delete(`/watchlist/${item_id}`),
};

// Alerts
export const alertsApi = {
  getAll: (page = 1, page_size = 20) =>
    api.get('/alerts/', { params: { page, page_size } }),
};
