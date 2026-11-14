import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "YouTube Clone API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-youtube-clone-key-change-in-production-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://youtube_user:youtube_pass@localhost:5432/youtube_db"
    )

    # Storage: "minio" or "local"
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "minio")
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "minioadmin")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "miniopassword")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "youtube-videos")
    S3_PUBLIC_URL: str = os.getenv("S3_PUBLIC_URL", "http://localhost:9005")
    LOCAL_STORAGE_DIR: str = os.getenv("LOCAL_STORAGE_DIR", "storage")

    # Uploads
    MAX_UPLOAD_SIZE_MB: int = 500

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

settings = Settings()
