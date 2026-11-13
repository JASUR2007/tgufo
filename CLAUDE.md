# Claude Code Agent Guidelines - YouTube Clone Project

## Commands & Workflows
- **Start Project via Docker**: `docker compose up -d --build`
- **One-Command Ubuntu Deployment**: `chmod +x deploy.sh && ./deploy.sh`
- **Run Backend Tests**: `cd backend && pytest`
- **Run Migrations**: `cd backend && alembic upgrade head`
- **Seed Demo Data**: `cd backend && python -m app.scripts.seed`
- **Build Frontend**: `cd frontend && npm install && npm run build`

## Architecture & Conventions
- **Backend**: FastAPI (Python 3.11+), SQLAlchemy 2.0 (async), Alembic, Pydantic v2, PostgreSQL 16.
- **Frontend**: React 18, Vite, TypeScript, TailwindCSS, Lucide-react.
- **Object Storage**: S3 / MinIO with HTTP Range streaming support.
- **Transcoding & Media**: ffmpeg/ffprobe worker for video processing and thumbnail generation.
- **Security**: JWT tokens in Authorization headers, bcrypt hashing, RBAC (user, moderator, admin), ACL for private video grants.
- **Code Style**:
  - Python: PEP 8, strict type hints, async/await for I/O operations.
  - TypeScript: Strict mode, interface schemas matching backend Pydantic models.
