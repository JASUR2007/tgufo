# API Reference Specification

All endpoints are prefixed with `/api/v1` and interactive Swagger docs are accessible at `/docs` (and ReDoc at `/redoc`).

## Authentication & Users
- `POST /api/v1/auth/register` — Register a new user, auto-creates their personal channel.
- `POST /api/v1/auth/login` — OAuth2 compatible password grant, returns JWT bearer token.
- `GET /api/v1/auth/me` — Return current authenticated user profile, channel info, and role.
- `GET /api/v1/users` — List users (for adding grants to private videos, searching authors).

## Videos & Streaming
- `GET /api/v1/videos` — Public video feed with pagination, sorting by views or recency.
- `POST /api/v1/videos/upload` — Upload video file & optional thumbnail (multipart/form-data), kicks off async processing.
- `GET /api/v1/videos/{video_id}` — Video details with view counter increment and strict ACL check.
- `PATCH /api/v1/videos/{video_id}` — Update title, description, visibility, access grants (Owner/Admin only).
- `DELETE /api/v1/videos/{video_id}` — Delete video and purge storage assets (Owner/Admin only).
- `GET /api/v1/videos/{video_id}/stream` — RFC 7233 range-compatible video stream endpoint.
- `GET /api/v1/videos/search` — Search videos by query keyword in title/description.

## Access Grants (Private Videos)
- `GET /api/v1/videos/{video_id}/grants` — List granted users for private video.
- `POST /api/v1/videos/{video_id}/grants` — Grant access to user (by username or email).
- `DELETE /api/v1/videos/{video_id}/grants/{user_id}` — Revoke access.

## Reactions & Comments
- `POST /api/v1/videos/{video_id}/reactions` — Toggle like or dislike.
- `GET /api/v1/videos/{video_id}/reactions/me` — Get current user's reaction.
- `GET /api/v1/videos/{video_id}/comments` — List comments for a video.
- `POST /api/v1/videos/{video_id}/comments` — Add comment.
- `DELETE /api/v1/comments/{comment_id}` — Delete comment (author or moderator/admin).

## Channels & Subscriptions
- `GET /api/v1/channels/{channel_id}` — Channel profile.
- `GET /api/v1/channels/{channel_id}/videos` — Channel's public/allowed videos.
- `POST /api/v1/channels/{channel_id}/subscribe` — Subscribe/unsubscribe toggle.
- `GET /api/v1/channels/{channel_id}/subscription/me` — Check current user's subscription status.

## Playlists
- `GET /api/v1/channels/{channel_id}/playlists` — List channel playlists.
- `POST /api/v1/playlists` — Create new playlist.
- `GET /api/v1/playlists/{playlist_id}` — Get playlist and its items.
- `POST /api/v1/playlists/{playlist_id}/items` — Add video to playlist.
- `DELETE /api/v1/playlists/{playlist_id}/items/{video_id}` — Remove video from playlist.

## Moderation (Moderator / Admin Role)
- `POST /api/v1/reports` — Submit report against a video (Authenticated user).
- `GET /api/v1/moderation/reports` — List pending reports (Moderator/Admin).
- `POST /api/v1/moderation/videos/{video_id}/hide` — Hide video with reason (Moderator/Admin).
- `POST /api/v1/moderation/videos/{video_id}/restore` — Restore video (Moderator/Admin).
- `GET /api/v1/moderation/actions` — Audit log of moderation decisions.
