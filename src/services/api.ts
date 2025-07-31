import axios, { AxiosInstance, AxiosError } from 'axios';
import { getToken, removeToken } from '../utils/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  private axios: AxiosInstance;
  
  constructor() {
    this.axios = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    // Request interceptor to add auth token
    this.axios.interceptors.request.use(
      (config) => {
        const token = getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );
    
    // Response interceptor to handle auth errors
    this.axios.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          removeToken();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }
  
  // Auth endpoints
  async login(email: string, password: string) {
    const response = await this.axios.post('/auth/login', { email, password });
    return response.data;
  }
  
  async logout() {
    const response = await this.axios.post('/auth/logout');
    return response.data;
  }
  
  async refreshToken() {
    const response = await this.axios.post('/auth/refresh');
    return response.data;
  }
  
  async forgotPassword(email: string) {
    const response = await this.axios.post('/auth/forgot-password', { email });
    return response.data;
  }
  
  async resetPassword(token: string, password: string) {
    const response = await this.axios.post('/auth/reset-password', { token, password });
    return response.data;
  }
  
  // User endpoints
  async getProfile() {
    const response = await this.axios.get('/users/profile');
    return response.data;
  }
  
  async updateProfile(data: any) {
    const response = await this.axios.put('/users/profile', data);
    return response.data;
  }
  
  async changePassword(currentPassword: string, newPassword: string) {
    const response = await this.axios.post('/users/change-password', {
      currentPassword,
      newPassword
    });
    return response.data;
  }
  
  // Generic request method
  async request(method: string, url: string, data?: any, config?: any) {
    const response = await this.axios.request({
      method,
      url,
      data,
      ...config
    });
    return response.data;
  }
}

export default new ApiService();