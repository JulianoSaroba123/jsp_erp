import axios from 'axios';
import { clearAccessToken, getAccessToken } from '../../auth/auth-storage';
import { AppHttpError, toAppHttpError } from '../errors/http-error';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

type ErrorHandler = (error: AppHttpError) => void;

let unauthorizedHandler: ErrorHandler | null = null;
let forbiddenHandler: ErrorHandler | null = null;

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export function setUnauthorizedHandler(handler: ErrorHandler) {
  unauthorizedHandler = handler;
  return () => {
    if (unauthorizedHandler === handler) {
      unauthorizedHandler = null;
    }
  };
}

export function setForbiddenHandler(handler: ErrorHandler) {
  forbiddenHandler = handler;
  return () => {
    if (forbiddenHandler === handler) {
      forbiddenHandler = null;
    }
  };
}

apiClient.interceptors.request.use(
  (config) => {
    const token = getAccessToken();

    if (token) {
      config.headers = config.headers ?? {};
      (config.headers as Record<string, string>).Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(toAppHttpError(error))
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const normalizedError = toAppHttpError(error);

    if (normalizedError.status === 401) {
      clearAccessToken();
      unauthorizedHandler?.(normalizedError);
    }

    if (normalizedError.status === 403) {
      forbiddenHandler?.(normalizedError);
    }

    return Promise.reject(normalizedError);
  }
);
