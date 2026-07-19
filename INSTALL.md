# NORAY Installation Guide

NORAY is designed to be a plug-and-play AI Operating System. This guide covers how to set up the environment natively, via Docker Compose, or completely offline.

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Git**
- **Docker & Docker Compose** (Optional, but highly recommended)

## Option 1: Automated Bootstrap (Recommended)

We provide automated setup scripts that detect your environment, install dependencies, and configure your local databases and AI models.

### Windows

Open PowerShell as Administrator and run:
```powershell
.\setup.ps1
```

### macOS / Linux

Open your terminal and run:
```bash
./setup.sh
```
*(Alternatively, you can run `make setup`)*

---

## Option 2: Manual Installation

If you prefer to configure everything manually, follow these steps.

### 1. Database Infrastructure

Start the supporting databases (PostgreSQL, Qdrant, Redis):
```bash
docker-compose up -d
```
> If you cannot use Docker, NORAY will automatically fall back to SQLite for relational data. However, Qdrant is required for semantic search (Local Embeddings).

### 2. Backend (FastAPI)

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -e .
   ```
3. Initialize the database and run migrations:
   ```bash
   python -m noray.database_init
   ```
4. Start the backend server:
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```

### 3. Frontend (Next.js)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

---

## Post-Installation: The First Run Wizard

Once the backend and frontend are running, open [http://localhost:3000](http://localhost:3000) in your browser. 
If this is your first time starting NORAY, the **First Run Wizard** will launch and automatically guide you through hardware detection and Local LLM installation.
