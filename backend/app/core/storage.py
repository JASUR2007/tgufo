import os
import io
import aiofiles
from pathlib import Path
from typing import Optional, Tuple, BinaryIO, Generator
from fastapi import HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from app.core.config import settings

class StorageService:
    def __init__(self):
        self.storage_dir = Path(settings.LOCAL_STORAGE_DIR)
        self.videos_dir = self.storage_dir / "videos"
        self.thumbnails_dir = self.storage_dir / "thumbnails"
        self.avatars_dir = self.storage_dir / "avatars"

        # Ensure local cache directories exist
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        self.avatars_dir.mkdir(parents=True, exist_ok=True)

        self.s3_client = None
        if settings.STORAGE_TYPE == "minio":
            try:
                import boto3
                from botocore.client import Config
                self.s3_client = boto3.client(
                    "s3",
                    endpoint_url=settings.S3_ENDPOINT_URL,
                    aws_access_key_id=settings.S3_ACCESS_KEY,
                    aws_secret_access_key=settings.S3_SECRET_KEY,
                    config=Config(signature_version="s3v4"),
                    region_name="us-east-1"
                )
                # Ensure bucket exists
                try:
                    self.s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
                except Exception:
                    self.s3_client.create_bucket(Bucket=settings.S3_BUCKET_NAME)
                print(f"[StorageService] Connected to MinIO S3 at {settings.S3_ENDPOINT_URL}, bucket: {settings.S3_BUCKET_NAME}")
            except Exception as e:
                print(f"[StorageService] Warning: MinIO connection failed ({e}). Falling back to local storage.")
                self.s3_client = None

    async def save_file(self, content: bytes, folder: str, filename: str) -> str:
        s3_key = f"{folder}/{filename}"

        # 1. Primary write to S3/MinIO if enabled
        if self.s3_client:
            try:
                self.s3_client.put_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=s3_key,
                    Body=content
                )
            except Exception as e:
                print(f"[StorageService] S3 put_object failed ({e}). Saving locally.")

        # 2. Local copy for fast worker ffmpeg processing
        target_dir = self.storage_dir / folder
        target_dir.mkdir(parents=True, exist_ok=True)
        filepath = target_dir / filename
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)

        return filename

    def get_object_size(self, folder: str, filename: str) -> int:
        s3_key = f"{folder}/{filename}"
        if self.s3_client:
            try:
                head = self.s3_client.head_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
                return head["ContentLength"]
            except Exception:
                pass

        # Local fallback
        local_path = self.storage_dir / folder / filename
        if local_path.exists():
            return local_path.stat().st_size
        raise HTTPException(status_code=404, detail="Media file not found in storage")

    def create_range_streaming_response(
        self,
        folder: str,
        filename: str,
        range_header: Optional[str],
        media_type: str = "video/mp4"
    ) -> StreamingResponse:
        """
        RFC 7233 Range-compatible streaming response.
        Works seamlessly with both MinIO/S3 object storage and local filesystem.
        """
        s3_key = f"{folder}/{filename}"
        file_size = self.get_object_size(folder, filename)

        if not range_header:
            # Full content (200 OK)
            if self.s3_client:
                try:
                    s3_resp = self.s3_client.get_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
                    def s3_full_iterator():
                        body = s3_resp["Body"]
                        while chunk := body.read(1024 * 512):
                            yield chunk
                    headers = {
                        "Content-Length": str(file_size),
                        "Accept-Ranges": "bytes",
                        "Content-Type": media_type,
                    }
                    return StreamingResponse(s3_full_iterator(), status_code=200, headers=headers)
                except Exception as e:
                    print(f"[StorageService] S3 stream failed ({e}), trying local disk.")

            # Local disk full content
            local_path = self.storage_dir / folder / filename
            def local_full_iterator():
                with open(local_path, mode="rb") as f:
                    while chunk := f.read(1024 * 512):
                        yield chunk
            headers = {
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes",
                "Content-Type": media_type,
            }
            return StreamingResponse(local_full_iterator(), status_code=200, headers=headers)

        # Partial content (206 Partial Content) with Range: bytes=start-end
        try:
            byte_range = range_header.replace("bytes=", "").strip()
            parts = byte_range.split("-")
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
        except Exception:
            raise HTTPException(status_code=416, detail="Invalid Range header")

        if start >= file_size or end >= file_size or start > end:
            raise HTTPException(
                status_code=416,
                detail="Range Not Satisfiable",
                headers={"Content-Range": f"bytes */{file_size}"}
            )

        content_length = end - start + 1

        # Stream partial content from S3/MinIO
        if self.s3_client:
            try:
                s3_resp = self.s3_client.get_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=s3_key,
                    Range=f"bytes={start}-{end}"
                )
                def s3_partial_iterator():
                    body = s3_resp["Body"]
                    while chunk := body.read(1024 * 512):
                        yield chunk

                headers = {
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(content_length),
                    "Content-Type": media_type,
                }
                return StreamingResponse(s3_partial_iterator(), status_code=206, headers=headers)
            except Exception as e:
                print(f"[StorageService] S3 Range request failed ({e}), trying local disk.")

        # Local disk partial content iterator
        local_path = self.storage_dir / folder / filename
        def local_partial_iterator():
            bytes_left = content_length
            with open(local_path, mode="rb") as f:
                f.seek(start)
                while bytes_left > 0:
                    read_size = min(1024 * 512, bytes_left)
                    chunk = f.read(read_size)
                    if not chunk:
                        break
                    bytes_left -= len(chunk)
                    yield chunk

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Type": media_type,
        }
        return StreamingResponse(local_partial_iterator(), status_code=206, headers=headers)

    def get_thumbnail_response(self, filename: str) -> StreamingResponse:
        s3_key = f"thumbnails/{filename}"
        if self.s3_client:
            try:
                s3_resp = self.s3_client.get_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
                def s3_thumb_iterator():
                    body = s3_resp["Body"]
                    while chunk := body.read(1024 * 64):
                        yield chunk
                headers = {
                    "Content-Type": "image/jpeg",
                    "Cache-Control": "public, max-age=86400"
                }
                return StreamingResponse(s3_thumb_iterator(), media_type="image/jpeg", headers=headers)
            except Exception:
                pass

        # Local fallback
        local_path = self.storage_dir / "thumbnails" / filename
        if local_path.exists():
            return FileResponse(local_path, media_type="image/jpeg")
        raise HTTPException(status_code=404, detail="Thumbnail not found")

storage_service = StorageService()
