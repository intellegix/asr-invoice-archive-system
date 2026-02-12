import axios, { AxiosInstance, AxiosError } from 'axios';
import toast from 'react-hot-toast';

export class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-ID': import.meta.env.VITE_TENANT_ID || 'default',
      },
    });

    // Request interceptor for auth
    this.client.interceptors.request.use((config) => {
      const apiKey = sessionStorage.getItem('api_key');
      if (apiKey) {
        config.headers.Authorization = `Bearer ${apiKey}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        this.handleApiError(error);
        return Promise.reject(error);
      }
    );
  }

  private handleApiError(error: AxiosError) {
    const status = error.response?.status;
    const message = (error.response?.data as any)?.message || error.message;

    switch (status) {
      case 400:
        toast.error(`Invalid request: ${message}`);
        break;
      case 401:
        toast.error('Authentication required');
        sessionStorage.removeItem('api_key');
        sessionStorage.removeItem('tenant_id');
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        break;
      case 403:
        toast.error('Access denied');
        break;
      case 404:
        toast.error('Resource not found');
        break;
      case 413:
        toast.error('File too large (max 10MB)');
        break;
      case 429:
        toast.error('Too many requests. Please wait.');
        break;
      case 500:
        toast.error('Server error. Please try again.');
        break;
      default:
        toast.error('An unexpected error occurred');
    }
  }

  async get<T>(url: string, params?: any): Promise<T> {
    const response = await this.client.get(url, { params });
    return response.data;
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post(url, data);
    return response.data;
  }

  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.put(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete(url);
    return response.data;
  }

  async uploadFile<T>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        const progress = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
        onProgress?.(progress);
      },
    });

    return response.data;
  }
}

export const apiClient = new ApiClient();