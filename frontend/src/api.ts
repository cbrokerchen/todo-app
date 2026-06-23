import axios from 'axios';

const API_BASE_URL = '/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token to every outgoing request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Redirect to /login on 401 Unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      // Only redirect if we're not already on the auth pages
      const currentPath = window.location.pathname;
      if (currentPath !== '/login' && currentPath !== '/register') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  },
);

// --- Auth helpers ---

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export async function login(username: string, password: string): Promise<AuthResponse> {
  const res = await api.post<AuthResponse>('/login', { username, password });
  return res.data;
}

export async function register(username: string, password: string): Promise<AuthResponse> {
  const res = await api.post<AuthResponse>('/register', { username, password });
  return res.data;
}

// --- Todo helpers ---

export interface Todo {
  id: string;
  title: string;
  description: string | null;
  completed: boolean;
  created_at: string;
}

export interface TodoCreate {
  title: string;
  description: string | null;
}

export async function fetchTodos(): Promise<Todo[]> {
  const res = await api.get<Todo[]>('/todos');
  return res.data;
}

export async function createTodo(payload: TodoCreate): Promise<Todo> {
  const res = await api.post<Todo>('/todos', payload);
  return res.data;
}

export async function updateTodo(id: string, payload: TodoCreate): Promise<Todo> {
  const res = await api.put<Todo>(`/todos/${id}`, payload);
  return res.data;
}

export async function deleteTodo(id: string): Promise<void> {
  await api.delete(`/todos/${id}`);
}

export async function toggleTodo(id: string): Promise<Todo> {
  const res = await api.patch<Todo>(`/todos/${id}/toggle`);
  return res.data;
}
