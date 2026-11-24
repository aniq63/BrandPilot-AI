import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

from src.utilis.logging import logger, log_calls

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET") or "brand-assets"

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Supabase credentials are missing from .env")

client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024

_bucket_ready = False


@log_calls
def ensure_bucket() -> None:
    global _bucket_ready
    if _bucket_ready:
        return
    try:
        client.storage.get_bucket(BUCKET)
    except Exception:
        logger.info("Creating public Supabase bucket %s", BUCKET)
        client.storage.create_bucket(BUCKET, options={"public": True})
    _bucket_ready = True


@log_calls
def validate_image(filename: str, content_type: str, size: int) -> None:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Only JPG, PNG, WEBP and GIF images are allowed")
    if not content_type.startswith("image/"):
        raise ValueError("Uploaded file must be an image")
    if size > MAX_FILE_SIZE:
        raise ValueError("Image must be smaller than 10 MB")


@log_calls
def upload_image(
    *,
    user_id: int,
    project_id: int | None,
    filename: str,
    content: bytes,
    content_type: str,
    folder: str,
) -> tuple[str, str]:
    validate_image(filename, content_type, len(content))
    ensure_bucket()

    suffix = Path(filename).suffix.lower()
    scope = f"user_{user_id}/project_{project_id}" if project_id else f"user_{user_id}/drafts"
    path = f"{scope}/{folder}/{uuid.uuid4().hex}{suffix}"

    bucket = client.storage.from_(BUCKET)
    bucket.upload(
        path,
        content,
        {"content-type": content_type, "upsert": False},
    )
    return path, bucket.get_public_url(path)


@log_calls
def upload_brand_image(
    *,
    user_id: int,
    project_id: int | None,
    filename: str,
    content: bytes,
    content_type: str,
    folder: str,
) -> str:
    _, public_url = upload_image(
        user_id=user_id,
        project_id=project_id,
        filename=filename,
        content=content,
        content_type=content_type,
        folder=folder,
    )
    return public_url
