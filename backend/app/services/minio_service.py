"""MinIO file storage service."""

import logging
from io import BytesIO
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.config import Settings
from app.utils.exceptions import MinIOException

logger = logging.getLogger(__name__)


class MinioService:
    """Service for MinIO file storage operations."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket_resumes = settings.minio_bucket_resumes
        self.bucket_audio = settings.minio_bucket_audio

    async def ensure_buckets(self) -> None:
        """Ensure required buckets exist on startup."""
        for bucket in [self.bucket_resumes, self.bucket_audio]:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info(f"Created MinIO bucket: {bucket}")
                else:
                    logger.info(f"MinIO bucket already exists: {bucket}")
            except S3Error as e:
                logger.error(f"Failed to ensure bucket {bucket}: {e}")
                raise MinIOException(f"MinIO bucket initialization failed: {e}")

    async def upload_file(
        self,
        bucket: str,
        object_key: str,
        file_data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None,
    ) -> str:
        """Upload a file to MinIO and return the object key."""
        try:
            data_stream = BytesIO(file_data)
            data_size = len(file_data)
            self.client.put_object(
                bucket_name=bucket,
                object_name=object_key,
                data=data_stream,
                length=data_size,
                content_type=content_type,
                metadata=metadata or {},
            )
            logger.info(f"Uploaded file to {bucket}/{object_key}")
            return object_key
        except S3Error as e:
            logger.error(f"Failed to upload file: {e}")
            raise MinIOException(f"File upload failed: {e}")

    async def get_presigned_url(self, bucket: str, object_key: str, expires_seconds: int = 3600) -> str:
        """Generate a presigned URL for downloading a file."""
        from datetime import timedelta
        try:
            url = self.client.presigned_get_object(
                bucket_name=bucket,
                object_name=object_key,
                expires=timedelta(seconds=expires_seconds),
            )
            return url
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise MinIOException(f"Presigned URL generation failed: {e}")

    async def delete_file(self, bucket: str, object_key: str) -> None:
        """Delete a file from MinIO."""
        try:
            self.client.remove_object(bucket_name=bucket, object_name=object_key)
            logger.info(f"Deleted file {bucket}/{object_key}")
        except S3Error as e:
            logger.error(f"Failed to delete file: {e}")
            raise MinIOException(f"File deletion failed: {e}")

    async def get_file(self, bucket: str, object_key: str) -> bytes:
        """Download file content from MinIO."""
        try:
            response = self.client.get_object(bucket_name=bucket, object_name=object_key)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Failed to get file: {e}")
            raise MinIOException(f"File download failed: {e}")
