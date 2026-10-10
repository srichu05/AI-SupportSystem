import logging
from typing import Dict, Any, Optional
from backend.app.core.config import settings

logger = logging.getLogger("complaint_assistant.supabase")


class SupabaseService:
    """Service to interact with Supabase SDK and Supabase Storage."""

    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
        self.bucket = settings.SUPABASE_STORAGE_BUCKET
        self._client = None

    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.key)

    def get_client(self):
        """Lazily initialize Supabase client if configured."""
        if not self.is_configured:
            return None
        if self._client is None:
            try:
                from supabase import create_client
                self._client = create_client(self.url, self.key)
            except Exception as e:
                logger.error("Failed to initialize Supabase client: %s", e)
                raise
        return self._client

    def check_storage_access(self) -> Dict[str, Any]:
        """Verify Supabase Storage bucket connectivity."""
        if not self.is_configured:
            return {
                "configured": False,
                "status": "not_configured",
                "message": "SUPABASE_URL or key not provided in .env",
                "storage_bucket": self.bucket
            }

        try:
            client = self.get_client()
            buckets = client.storage.list_buckets()
            bucket_names = [b.name for b in buckets] if buckets else []
            bucket_exists = self.bucket in bucket_names

            return {
                "configured": True,
                "status": "verified" if bucket_exists else "bucket_not_found",
                "message": (
                    f"Bucket '{self.bucket}' found."
                    if bucket_exists
                    else f"Bucket '{self.bucket}' not found in accessible buckets: {bucket_names}"
                ),
                "storage_bucket": self.bucket,
                "bucket_exists": bucket_exists
            }
        except Exception as exc:
            logger.warning("Supabase storage verification failed: %s", exc)
            return {
                "configured": True,
                "status": "failed",
                "message": str(exc).splitlines()[0],
                "storage_bucket": self.bucket,
                "bucket_exists": False
            }

    def upload_file(
        self,
        destination_path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload binary or text file to Supabase Storage bucket.
        Returns the storage path upon success.
        """
        if not self.is_configured:
            logger.warning("Supabase not configured; returning mock storage path: %s", destination_path)
            return f"local://{self.bucket}/{destination_path}"

        client = self.get_client()
        try:
            # Upsert into storage bucket
            file_options = {"upsert": "true", "content-type": content_type}
            client.storage.from_(self.bucket).upload(
                path=destination_path,
                file=content,
                file_options=file_options,
            )
            logger.info("Successfully uploaded %s to Supabase Storage bucket %s", destination_path, self.bucket)
            return f"{self.bucket}/{destination_path}"
        except Exception as exc:
            logger.error("Failed to upload %s to Supabase Storage: %s", destination_path, exc)
            raise

    def get_public_or_signed_url(self, storage_path: str, expires_in: int = 3600) -> Optional[str]:
        """Generate a signed URL for private bucket access."""
        if not self.is_configured:
            return None
        try:
            client = self.get_client()
            clean_path = storage_path.removeprefix(f"{self.bucket}/")
            res = client.storage.from_(self.bucket).create_signed_url(clean_path, expires_in)
            if isinstance(res, dict) and "signedURL" in res:
                return res["signedURL"]
            return getattr(res, "signed_url", None) or str(res)
        except Exception as exc:
            logger.warning("Failed to create signed URL for %s: %s", storage_path, exc)
            return None


supabase_service = SupabaseService()
