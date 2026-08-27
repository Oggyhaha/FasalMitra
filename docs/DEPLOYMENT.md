# FasalMitra — Deployment & Production Setup

## 1. Local & Hackathon Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- Docker & Docker Compose (optional for containerized deployment)

### Quickstart (Zero-Config Development Mode)

1. **Install Backend Dependencies:**
   ```bash
   cd backend
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Ingest Seed Knowledge Base:**
   ```bash
   python -m ingestion.ingest
   ```

3. **Start Backend Server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Start Frontend Dashboard:**
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```

5. Access Application:
   - **Frontend Simulator & Expert Dashboard:** `http://localhost:5173`
   - **Backend API Docs (Swagger):** `http://localhost:8000/docs`

---

## 2. Docker Architecture (`infra/docker-compose.yml`)

The platform is fully containerized into three microservices:
- `fasalmitra-backend`: FastAPI application engine.
- `fasalmitra-frontend`: React/Vite web application served via Nginx.
- `fasalmitra-db`: PostgreSQL database for persistent storage.
