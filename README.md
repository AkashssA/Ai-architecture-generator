# AI System Architecture Generator

A full-stack application featuring a production-oriented FastAPI service and a modern React frontend that turns natural-language system design prompts into structured architecture recommendations, Mermaid diagrams, API endpoints, and scalability guidance.

## Features

**Backend (FastAPI)**
- Async FastAPI application with clean module boundaries
- OpenAI-backed architecture generation with deterministic fallback mode
- Request and response validation using Pydantic
- Mermaid diagram generation from structured component relationships
- Optional Redis caching with in-memory fallback
- API key authentication via `X-API-Key`
- In-memory rate limiting middleware
- Logging and centralized error handling
- Swagger/OpenAPI documentation enhancements

**Frontend (React & Vite)**
- Interactive modern UI built with React and TypeScript
- Real-time diagram rendering using Mermaid.js
- Dynamic generation form with loading states
- Clean, responsive design

## Project Structure

```text
.
├── app/               # FastAPI backend
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   ├── utils/
│   └── main.py
└── frontend/          # React frontend
    ├── src/
    ├── public/
    ├── package.json
    └── vite.config.ts
```

## Backend Setup

1. **Create and activate a virtual environment:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
```bash
copy .env.example .env
```
Set `OPENAI_API_KEY` to enable live LLM-backed generation. If it is empty, the API still works using built-in architecture templates and a generic fallback.

4. **Run the backend server:**
```bash
uvicorn app.main:app --reload
```
The backend API will run on `http://127.0.0.1:8000`. Swagger UI will be available at `http://127.0.0.1:8000/docs`.

## Frontend Setup

1. **Navigate to the frontend directory:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Run the development server:**
```bash
npm run dev
```
The frontend UI will run on `http://localhost:5173`.

## Authentication

If `API_KEY` is set in `.env`, pass the same value in the `X-API-Key` header. The frontend is currently configured to pass this seamlessly if set up.

## Caching

- If `REDIS_URL` is configured, Redis is used.
- Otherwise, the service falls back to in-memory TTL caching.

## Notes

- The built-in fallback mode is useful for local development, testing, and demos without an LLM API key.
- Ensure both the frontend development server and the backend FastAPI server are running simultaneously to use the full application.
