import { useState, useEffect, useCallback } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { fetchTodos, createTodo } from '../api';
import type { Todo } from '../api';
import TodoItem from '../components/TodoItem';

export default function DashboardPage() {
  const { logout, token } = useAuth();
  const navigate = useNavigate();
  const [todos, setTodos] = useState<Todo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  const loadTodos = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchTodos();
      // Sort newest first
      data.sort((a, b) => b.id - a.id);
      setTodos(data);
    } catch (err: unknown) {
      setError(extractError(err) ?? '載入待辦事項失敗');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTodos();
  }, [loadTodos]);

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  async function handleAdd(e: FormEvent) {
    e.preventDefault();
    if (!newTitle.trim()) {
      setAddError('請輸入待辦事項標題');
      return;
    }
    setAdding(true);
    setAddError(null);
    try {
      const created = await createTodo({
        title: newTitle.trim(),
        description: newDescription.trim() || null,
      });
      setTodos((prev) => [created, ...prev]);
      setNewTitle('');
      setNewDescription('');
    } catch (err: unknown) {
      setAddError(extractError(err) ?? '新增失敗');
    } finally {
      setAdding(false);
    }
  }

  const username = decodeJwtSubject(token);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>我的待辦事項</h1>
          {username && <p className="dashboard-subtitle">目前已登入：{username}</p>}
        </div>
        <button type="button" onClick={handleLogout} className="btn-secondary">
          登出
        </button>
      </header>

      <section className="add-todo-section">
        <form onSubmit={handleAdd} className="add-todo-form">
          <input
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="輸入待辦事項…"
            maxLength={200}
            disabled={adding}
            required
          />
          <input
            type="text"
            value={newDescription}
            onChange={(e) => setNewDescription(e.target.value)}
            placeholder="備註（選填）"
            maxLength={1000}
            disabled={adding}
          />
          <button type="submit" disabled={adding} className="btn-primary">
            {adding ? '新增中…' : '新增'}
          </button>
        </form>
        {addError && <div className="error-banner">{addError}</div>}
      </section>

      <section className="todos-section">
        {loading ? (
          <div className="loading">
            <div className="spinner" aria-label="載入中" />
            <span>載入中…</span>
          </div>
        ) : error ? (
          <div className="error-banner">
            {error}
            <button
              type="button"
              onClick={() => void loadTodos()}
              className="btn-secondary btn-small retry-btn"
            >
              重試
            </button>
          </div>
        ) : todos.length === 0 ? (
          <div className="empty-state">
            <p>尚無待辦事項，在上方新增第一筆吧！</p>
          </div>
        ) : (
          <ul className="todo-list">
            {todos.map((todo) => (
              <TodoItem key={todo.id} todo={todo} onChange={() => void loadTodos()} />
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function extractError(err: unknown): string | null {
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const response = (err as { response?: { data?: { detail?: string } } }).response;
    if (response?.data?.detail) return response.data.detail;
  }
  return null;
}

function decodeJwtSubject(jwt: string | null): string | null {
  if (!jwt) return null;
  try {
    const parts = jwt.split('.');
    if (parts.length !== 3) return null;
    const payload = parts[1];
    // base64url → base64
    const padded = payload.replace(/-/g, '+').replace(/_/g, '/');
    const json = atob(padded);
    const data = JSON.parse(json) as { sub?: string };
    return data.sub ?? null;
  } catch {
    return null;
  }
}
