# Multi-Agent Workflow Configuration for YouTube Clone

## Overview
This repository contains a full-stack, enterprise-grade YouTube clone designed and built according to the StackBridge / Gufo technical specification. The project was engineered using a collaborative AI multi-agent architecture where the human engineer acts as the Chief Architect & Code Reviewer, directing specialized autonomous AI agents.

## Specialized AI Agent Roles

### 1. `system-architect`
- **Responsibilities**: High-level domain modeling, database ERD design, state machine definition for video lifecycles, security boundaries, and API contract specifications.
- **Key Deliverables**: Domain diagrams, PostgreSQL schema, role-based access control (RBAC), and private video access policies.

### 2. `backend-engineer`
- **Responsibilities**: Implementation of FastAPI REST API, SQLAlchemy 2.0 async models, Alembic migrations, Pydantic schemas, JWT authentication, and S3/MinIO storage streaming with HTTP Range headers (RFC 7233).
- **Standards**: Type safety with mypy/Pydantic, dependency injection, async I/O, robust error handling, OpenAPI/Swagger documentation.

### 3. `media-pipeline-engineer`
- **Responsibilities**: Video upload, validation, async task processing, thumbnail generation via ffmpeg/ffprobe, duration calculation, and video format normalization (H.264/AAC MP4).
- **Resilience**: Idempotent jobs, automatic retries, status state transitions (`uploading` -> `processing` -> `ready` | `failed`).

### 4. `frontend-engineer`
- **Responsibilities**: Pixel-perfect YouTube desktop & mobile web experience using React 18, TypeScript, TailwindCSS, and Lucide icons.
- **Key UX Components**: Sticky header, collapsible YouTube sidebar, category pill bar, responsive video cards, customizable HTML5 video player with seek/volume/fullscreen, comment threads, channel profiles, upload modal with progress, and a 1-click Quick Demo Switcher for fast evaluation.

### 5. `security-qa-engineer`
- **Responsibilities**: Automated pytest suite covering critical flows, private video isolation, ACL verification, moderator privilege enforcement, and SQL injection / IDOR prevention.

### 6. `devops-engineer`
- **Responsibilities**: Single-command clean Ubuntu deployment via Docker Compose, multi-stage Dockerfiles, Nginx reverse proxy, automated database migrations, healthchecks, and idempotent demo data seeding.

## Working Agreements & Guardrails
- **No Mock-Only Data**: Frontend must consume real API endpoints backed by PostgreSQL and S3/MinIO.
- **Range Header Support**: Video streaming MUST support `206 Partial Content` so timeline seeking works smoothly in browsers without buffering the entire file.
- **Strict ACL**: Unlisted videos are not in public feeds. Private videos are forbidden (403) unless requested by the owner, an administrator, or a granted user ID.
- **Idempotency**: All seeding and migration operations can be safely executed multiple times without corrupting state.
