#!/usr/bin/env python3
"""
Archive Packaging Script for YouTube Clone Submission
Packages the entire repository INCLUDING .git, docs, backend, frontend,
ai_sessions, and agent configurations into a clean zip archive.
Strictly excludes local secret files (.env), temporary databases, and caches.
"""

import os
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_ZIP = ROOT_DIR / "youtube_clone_submission.zip"

EXCLUDE_DIRS = {
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "storage",
    "miniodata",
    "pgdata"
}

EXCLUDE_FILES = {
    ".env",
    ".env.local",
    ".env.production",
    ".DS_Store",
    "Thumbs.db",
    "test_youtube.db",
    "test_seed.db",
    "youtube_clone_submission.zip"
}

def create_archive():
    print(f"📦 Packaging submission into: {OUTPUT_ZIP.name}")
    count = 0
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(ROOT_DIR):
            # Prune excluded directories in-place (except .git which is REQUIRED!)
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                if file in EXCLUDE_FILES or file.endswith((".pyc", ".pyo", ".key", ".pem")):
                    continue

                abs_path = Path(root) / file
                rel_path = abs_path.relative_to(ROOT_DIR)

                zf.write(abs_path, rel_path)
                count += 1

    # Security verification
    with zipfile.ZipFile(OUTPUT_ZIP, "r") as zf:
        namelist = zf.namelist()
        assert ".env" not in namelist, "SECURITY ALERT: .env found in archive!"
        assert ".git/config" in [n.replace('\\', '/') for n in namelist], "VALIDATION ERROR: .git missing from archive!"

    size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"✅ Submission packaged successfully! {count} files, {size_mb:.2f} MB")
    print(f"🔒 Security check passed: .env excluded, .git repository included.")
    print(f"📁 Archive ready at: {OUTPUT_ZIP}")

if __name__ == "__main__":
    create_archive()
