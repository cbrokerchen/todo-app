# Todo App — API Contract (shared between backend & frontend)

## Base URL
`http://localhost:8000/api`

## Endpoints

### POST /api/register
- Body: `{"username": "string", "password": "string"}`
- Response 201: `{"access_token": "string", "token_type": "bearer"}`
- Error 400: `{"detail": "Username already exists"}`

### POST /api/login
- Body: `{"username": "string", "password": "string"}`
- Response 200: `{"access_token": "string", "token_type": "bearer"}`
- Error 401: `{"detail": "Invalid credentials"}`

### GET /api/todos
- Header: `Authorization: Bearer <token>`
- Response 200: `[{"id": 1, "title": "string", "description": "string|null", "completed": false, "created_at": "ISO8601"}]`

### POST /api/todos
- Header: `Authorization: Bearer <token>`
- Body: `{"title": "string", "description": "string|null"}`
- Response 201: `{"id": 1, "title": "...", "description": "...", "completed": false, "created_at": "..."}`

### PUT /api/todos/{id}
- Header: `Authorization: Bearer <token>`
- Body: `{"title": "string", "description": "string|null"}`
- Response 200: updated todo object

### DELETE /api/todos/{id}
- Header: `Authorization: Bearer <token>`
- Response 200: `{"detail": "Todo deleted"}`

### PATCH /api/todos/{id}/toggle
- Header: `Authorization: Bearer <token>`
- Response 200: updated todo object (with toggled `completed`)

## Data Types
- `id`: integer
- `title`: string, required, max 200 chars
- `description`: string or null, optional, max 1000 chars
- `completed`: boolean, default false
- `created_at`: ISO 8601 datetime string
- `access_token`: JWT string (HS256, subject=username, expires 24h)
