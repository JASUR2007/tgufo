# System Architecture - YouTube Clone

## Overview
This document describes the high-level and detailed architecture of the YouTube clone developed for the StackBridge / Gufo technical challenge.

## Component Architecture

```mermaid
flowchart TD
    Client["Web Browser (React SPA)"]
    Nginx["Nginx Reverse Proxy (:80)"]
    API["FastAPI Application (:8000)"]
    Worker["Async Media Worker (ffmpeg/ffprobe)"]
    DB[("PostgreSQL 16 Database")]
    S3[("MinIO S3 Object Storage")]

    Client -->|HTTP/REST /api/*| Nginx
    Client -->|Static Assets /*| Nginx
    Nginx -->|Proxy API| API
    API -->|Read/Write Metadata| DB
    API -->|Presigned URLs & Stream Proxy (Range: bytes)| S3
    API -->|Enqueue Transcoding Tasks| Worker
    Worker -->|Fetch Raw / Save Processed| S3
    Worker -->|Update Processing Status| DB
```

## Core Subsystems

### 1. API Gateway & Reverse Proxy (Nginx)
- Routes incoming traffic: `/api/` and `/docs` to FastAPI backend.
- Serves static compiled frontend bundle for `/`.
- Handles CORS, security headers, and client request size limits (up to 500MB for video uploads).

### 2. Backend Application (FastAPI)
- **Authentication**: JWT access tokens, bcrypt password hashing.
- **RBAC**: Three roles (`user`, `moderator`, `admin`).
- **Resource Authorization**:
  - `public`: visible in feed, search, and accessible to everyone.
  - `unlisted`: accessible via direct link, excluded from public feeds and search.
  - `private`: strictly accessible only to video owner, granted user IDs, and admin.
- **Streaming Service**: Custom range-aware streaming endpoint supporting RFC 7233 (`206 Partial Content`), allowing smooth browser seek and instant playback start.

### 3. Media Processing Pipeline
- **Validation**: File mime-type check, magic byte verification, max size checks.
- **Probe**: `ffprobe` determines duration, resolution, video/audio codecs.
- **Thumbnail Generation**: Automatically grabs a frame at 10% duration (or 1s) and exports a crisp JPEG/WebP.
- **Transcoding**: Converts input media into web-optimized H.264 MP4 with faststart flag (`+faststart` places moov atom at the front of the file for instant streaming).
- **Graceful Fallback**: If ffmpeg binary is absent in local dev, safe fallbacks generate SVG/PNG placeholders so development can proceed seamlessly.

### 4. Database Persistence (PostgreSQL)
- Relational schema enforcing foreign keys, cascade deletes, unique constraints (one reaction per user per video, one subscription per user per channel).
- Indexes on `video.title`, `video.channel_id`, `video.visibility`, `video.created_at`.
