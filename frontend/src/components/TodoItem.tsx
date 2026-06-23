import { useState } from 'react';
import type { FormEvent } from 'react';
import type { Todo } from '../api';
import { updateTodo, toggleTodo, deleteTodo } from '../api';

interface TodoItemProps {
  todo: Todo;
  onChange: () => void;
}

export default function TodoItem({ todo, onChange }: TodoItemProps) {
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(todo.title);
  const [editDescription, setEditDescription] = useState(todo.description ?? '');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleToggle() {
    setBusy(true);
    setError(null);
    try {
      await toggleTodo(todo.id);
      onChange();
    } catch (err: unknown) {
      setError(extractError(err) ?? '切換狀態失敗');
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (!window.confirm('確定要刪除這個待辦事項嗎？')) return;
    setBusy(true);
    setError(null);
    try {
      await deleteTodo(todo.id);
      onChange();
    } catch (err: unknown) {
      setError(extractError(err) ?? '刪除失敗');
    } finally {
      setBusy(false);
    }
  }

  function startEditing() {
    setEditTitle(todo.title);
    setEditDescription(todo.description ?? '');
    setEditing(true);
    setError(null);
  }

  function cancelEditing() {
    setEditing(false);
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    if (!editTitle.trim()) {
      setError('標題不能為空');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await updateTodo(todo.id, {
        title: editTitle.trim(),
        description: editDescription.trim() || null,
      });
      setEditing(false);
      onChange();
    } catch (err: unknown) {
      setError(extractError(err) ?? '儲存失敗');
    } finally {
      setBusy(false);
    }
  }

  if (editing) {
    return (
      <li className="todo-item editing">
        <form onSubmit={handleSave} className="todo-edit-form">
          <input
            type="text"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            required
            maxLength={200}
            autoFocus
          />
          <input
            type="text"
            value={editDescription}
            onChange={(e) => setEditDescription(e.target.value)}
            placeholder="備註（選填）"
            maxLength={1000}
          />
          {error && <div className="error-inline">{error}</div>}
          <div className="todo-actions">
            <button type="submit" disabled={busy} className="btn-primary btn-small">
              {busy ? '儲存中…' : '儲存'}
            </button>
            <button
              type="button"
              onClick={cancelEditing}
              disabled={busy}
              className="btn-secondary btn-small"
            >
              取消
            </button>
          </div>
        </form>
      </li>
    );
  }

  return (
    <li className={`todo-item ${todo.completed ? 'completed' : ''}`}>
      <label className="todo-checkbox">
        <input
          type="checkbox"
          checked={todo.completed}
          onChange={handleToggle}
          disabled={busy}
        />
        <span className="todo-content">
          <span className="todo-title">{todo.title}</span>
          {todo.description && (
            <span className="todo-description">{todo.description}</span>
          )}
        </span>
      </label>
      <div className="todo-actions">
        <button
          type="button"
          onClick={startEditing}
          disabled={busy}
          className="btn-secondary btn-small"
        >
          編輯
        </button>
        <button
          type="button"
          onClick={handleDelete}
          disabled={busy}
          className="btn-danger btn-small"
        >
          刪除
        </button>
      </div>
      {error && <div className="error-inline todo-error">{error}</div>}
    </li>
  );
}

function extractError(err: unknown): string | null {
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const response = (err as { response?: { data?: { detail?: string } } }).response;
    if (response?.data?.detail) return response.data.detail;
  }
  return null;
}
