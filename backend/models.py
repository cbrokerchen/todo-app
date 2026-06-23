"""Firestore database client and helpers."""
import firebase_admin
from firebase_admin import credentials, firestore
from config import SERVICE_ACCOUNT_PATH

cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
firebase_admin.initialize_app(cred)
db = firestore.client()


# ---------- Users ----------

def get_user(username: str) -> dict | None:
    doc = db.collection("users").document(username).get()
    if not doc.exists:
        return None
    return doc.to_dict()


def create_user(username: str, password_hash: str) -> None:
    db.collection("users").document(username).set({
        "password_hash": password_hash,
    })


# ---------- Todos ----------

def list_todos(username: str) -> list[dict]:
    docs = (
        db.collection("todos")
        .where("user_id", "==", username)
        .stream()
    )
    result = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        result.append(data)
    # Sort by created_at descending (Python-side, avoids Firestore composite index)
    result.sort(key=lambda t: t.get("created_at", ""), reverse=True)
    return result


def create_todo(username: str, title: str, description: str | None) -> dict:
    import datetime
    doc_ref = db.collection("todos").document()
    data = {
        "title": title,
        "description": description,
        "completed": False,
        "user_id": username,
        "created_at": datetime.datetime.utcnow().isoformat(),
    }
    doc_ref.set(data)
    data["id"] = doc_ref.id
    return data


def get_todo(todo_id: str) -> dict | None:
    doc = db.collection("todos").document(todo_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["id"] = doc.id
    return data


def update_todo(todo_id: str, title: str, description: str | None) -> None:
    db.collection("todos").document(todo_id).update({
        "title": title,
        "description": description,
    })


def delete_todo_doc(todo_id: str) -> None:
    db.collection("todos").document(todo_id).delete()


def toggle_todo_doc(todo_id: str, current_completed: bool) -> None:
    db.collection("todos").document(todo_id).update({
        "completed": not current_completed,
    })
