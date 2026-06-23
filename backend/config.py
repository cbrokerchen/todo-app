"""Application configuration."""
import os

# JWT settings
SECRET_KEY = "dev-secret-key-change-in-prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Database
DATABASE_URL = "sqlite:///" + os.path.join(os.path.dirname(__file__), "todo.db")

# CORS
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
