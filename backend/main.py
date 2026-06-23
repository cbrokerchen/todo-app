"""FastAPI Todo app entrypoint — Firestore backend."""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import CORS_ORIGINS
from auth import hash_password, verify_password, create_access_token, get_current_user
import models

app = FastAPI(title="Todo App", version="2.0.0")

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
    description: str | None = Field(None, max_length=1000)


class TodoUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)


class DetailResponse(BaseModel):
    detail: str


# ---------- Auth endpoints ----------

@app.post("/api/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest):
    existing = models.get_user(payload.username)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    models.create_user(payload.username, hash_password(payload.password))
    token = create_access_token(payload.username)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/api/login")
def login(payload: LoginRequest):
    user = models.get_user(payload.username)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    token = create_access_token(payload.username)
    return {"access_token": token, "token_type": "bearer"}


# ---------- Todo endpoints ----------

@app.get("/api/todos")
def list_todos(current_user: str = Depends(get_current_user)):
    return models.list_todos(current_user)


@app.post("/api/todos", status_code=status.HTTP_201_CREATED)
def create_todo(payload: TodoCreate, current_user: str = Depends(get_current_user)):
    return models.create_todo(
        current_user,
        title=payload.title,
        description=payload.description,
    )


@app.put("/api/todos/{todo_id}")
def update_todo(
    todo_id: str,
    payload: TodoUpdate,
    current_user: str = Depends(get_current_user),
):
    todo = models.get_todo(todo_id)
    if todo is None or todo.get("user_id") != current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    models.update_todo(todo_id, payload.title, payload.description)
    todo["title"] = payload.title
    todo["description"] = payload.description
    return todo


@app.delete("/api/todos/{todo_id}")
def delete_todo(todo_id: str, current_user: str = Depends(get_current_user)):
    todo = models.get_todo(todo_id)
    if todo is None or todo.get("user_id") != current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    models.delete_todo_doc(todo_id)
    return {"detail": "Todo deleted"}


@app.patch("/api/todos/{todo_id}/toggle")
def toggle_todo(todo_id: str, current_user: str = Depends(get_current_user)):
    todo = models.get_todo(todo_id)
    if todo is None or todo.get("user_id") != current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    completed = todo.get("completed", False)
    models.toggle_todo_doc(todo_id, completed)
    todo["completed"] = not completed
    return todo


# Allow `python main.py` to start the server as a convenience
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
