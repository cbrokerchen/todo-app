"""FastAPI Todo app entrypoint."""
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import CORS_ORIGINS
from models import init_db, get_db, User, Todo
from auth import (
    hash_password, verify_password, create_access_token, get_current_user,
)

app = FastAPI(title="Todo App", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Schemas ----------

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=150)
    password: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class TodoUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class TodoOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DetailResponse(BaseModel):
    detail: str


# ---------- Helpers ----------

def serialize_todo(todo: Todo) -> dict:
    return {
        "id": todo.id,
        "title": todo.title,
        "description": todo.description,
        "completed": todo.completed,
        "created_at": todo.created_at.isoformat(),
    }


def get_owned_todo(db: Session, todo_id: int, user: User) -> Todo:
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is None or todo.user_id != user.id:
        # Hide existence of other users' todos behind 404
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


# ---------- Startup ----------

@app.on_event("startup")
def on_startup() -> None:
    init_db()


# ---------- Auth endpoints ----------

@app.post("/api/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    user = User(username=payload.username, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.username)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/api/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    token = create_access_token(user.username)
    return {"access_token": token, "token_type": "bearer"}


# ---------- Todo endpoints ----------

@app.get("/api/todos")
def list_todos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    todos = (
        db.query(Todo)
        .filter(Todo.user_id == current_user.id)
        .order_by(Todo.created_at.desc())
        .all()
    )
    return [serialize_todo(t) for t in todos]


@app.post("/api/todos", status_code=status.HTTP_201_CREATED)
def create_todo(
    payload: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    todo = Todo(
        title=payload.title,
        description=payload.description,
        completed=False,
        user_id=current_user.id,
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return serialize_todo(todo)


@app.put("/api/todos/{todo_id}")
def update_todo(
    todo_id: int,
    payload: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    todo = get_owned_todo(db, todo_id, current_user)
    todo.title = payload.title
    todo.description = payload.description
    db.commit()
    db.refresh(todo)
    return serialize_todo(todo)


@app.delete("/api/todos/{todo_id}")
def delete_todo(
    todo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    todo = get_owned_todo(db, todo_id, current_user)
    db.delete(todo)
    db.commit()
    return {"detail": "Todo deleted"}


@app.patch("/api/todos/{todo_id}/toggle")
def toggle_todo(
    todo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    todo = get_owned_todo(db, todo_id, current_user)
    todo.completed = not todo.completed
    db.commit()
    db.refresh(todo)
    return serialize_todo(todo)


# Allow `python main.py` to start the server as a convenience
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
