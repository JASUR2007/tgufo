import asyncio
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from app.core.storage import storage_service

class VideoProcessingService:
    def __init__(self):
        self.ffmpeg_path = shutil.which("ffmpeg")
        self.ffprobe_path = shutil.which("ffprobe")

    async def get_video_duration(self, video_path: Path) -> float:
        if self.ffprobe_path and video_path.exists():
            try:
                cmd = [
                    self.ffprobe_path,
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(video_path)
                ]
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await proc.communicate()
                if stdout:
                    val = float(stdout.decode().strip())
                    return max(val, 0.0)
            except Exception as e:
                print(f"[VideoProcessing] ffprobe error: {e}")
        # Fallback duration estimation: ~1 second per 50KB or minimum 10s
        if video_path.exists():
            return max(10.0, float(min(600, video_path.stat().st_size // 50000)))
        return 10.0

    async def generate_thumbnail(self, video_path: Path, thumbnail_filename: str, title: str = "Video") -> str:
        target_path = storage_service.thumbnails_dir / thumbnail_filename
        
        # Method 1: Try ffmpeg if available
        if self.ffmpeg_path and video_path.exists():
            try:
                cmd = [
                    self.ffmpeg_path,
                    "-y",
                    "-ss", "00:00:01",
                    "-i", str(video_path),
                    "-vframes", "1",
                    "-q:v", "2",
                    "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
                    str(target_path)
                ]
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                if target_path.exists() and target_path.stat().st_size > 0:
                    return thumbnail_filename
            except Exception as e:
                print(f"[VideoProcessing] ffmpeg thumbnail failed: {e}")

        # Method 2: Graceful fallback with Pillow (crisp 1280x720 graphic thumbnail)
        try:
            img = Image.new("RGB", (1280, 720), color=(24, 24, 27)) # dark zinc
            draw = ImageDraw.Draw(img)

            # Draw a YouTube-like red badge / play button
            # Play button background
            draw.rounded_rectangle([560, 280, 720, 440], radius=32, fill=(255, 0, 0))
            # Play triangle in white
            draw.polygon([(620, 320), (620, 400), (680, 360)], fill=(255, 255, 255))

            # Draw title bar at bottom
            draw.rectangle([0, 620, 1280, 720], fill=(15, 15, 15))
            draw.text((40, 650), title[:60], fill=(240, 240, 240))

            target_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(target_path), "JPEG", quality=85)
            return thumbnail_filename
        except Exception as e:
            print(f"[VideoProcessing] Pillow thumbnail fallback failed: {e}")
            return thumbnail_filename

video_processing_service = VideoProcessingService()
