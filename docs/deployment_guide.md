# Single-Command Clean Ubuntu Deployment Guide

## Quick Start on Clean Ubuntu (22.04 / 24.04 LTS)

Run the automated bootstrap script directly:

```bash
git clone <repo_url> youtube-clone
cd youtube-clone
chmod +x deploy.sh
./deploy.sh
```

The script automatically:
1. Installs Docker and Docker Compose plugin if missing on the host.
2. Generates secure production secrets in `.env` if not present.
3. Builds and boots all microservices (Postgres 16, MinIO, FastAPI Backend, Celery/Worker, Nginx Frontend).
4. Runs database migrations (`alembic upgrade head`).
5. Seeds demo accounts, sample test videos with generated thumbnails, comments, likes, and playlists.
6. Displays the access URL and demo credentials.

## Access Points
- **Web Application**: `http://<server-ip>/`
- **Interactive API Docs (Swagger)**: `http://<server-ip>/docs`
- **ReDoc**: `http://<server-ip>/redoc`
- **MinIO Console**: `http://<server-ip>:9001` (login: `minioadmin` / `miniopassword`)

## Pre-seeded Demo Credentials

| Role | Email | Password | Handle |
|------|-------|----------|--------|
| **Admin** | `admin@youtube.local` | `AdminPass123!` | `@admin` |
| **Moderator** | `moderator@youtube.local` | `ModPass123!` | `@moderator` |
| **Creator** | `creator@youtube.local` | `CreatorPass123!` | `@tech_guru` |
| **Viewer** | `viewer@youtube.local` | `ViewerPass123!` | `@demo_viewer` |

> *Tip: The web interface contains a 1-click **Quick Demo Login** bar at the top for instant switching between roles during grading!*

## Local Development Without Docker

If running natively on a local workstation:
1. Backend:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   alembic upgrade head
   python -m app.scripts.seed
   uvicorn app.main:app --reload --port 8000
   ```
2. Frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
