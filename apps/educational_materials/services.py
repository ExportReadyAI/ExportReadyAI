"""
Services for Module 7: Educational Materials

File Storage Service for Supabase Storage
"""

import logging
import os
import uuid
from typing import Optional
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


class SupabaseStorageService:
    """
    Service for handling file uploads to Supabase Storage.
    
    Falls back to Django's default storage if Supabase is not configured.
    """

    def __init__(self):
        # Supabase Storage configuration from environment variables
        self.supabase_url = getattr(settings, "SUPABASE_URL", "")
        self.supabase_key = getattr(settings, "SUPABASE_ANON_KEY", "")
        self.bucket_name = getattr(settings, "SUPABASE_STORAGE_BUCKET", "educational-materials")
        
        # Try to import and initialize Supabase client
        self.client = None
        try:
            from supabase import create_client, Client
            if self.supabase_url and self.supabase_key:
                self.client: Optional[Client] = create_client(self.supabase_url, self.supabase_key)
                logger.info(f"✅ Supabase Storage client initialized successfully")
                logger.info(f"   URL: {self.supabase_url}")
                logger.info(f"   Bucket: {self.bucket_name}")
            else:
                logger.warning("⚠️ Supabase credentials not configured. File uploads will use local storage.")
                logger.warning(f"   SUPABASE_URL: {'Set' if self.supabase_url else 'NOT SET'}")
                logger.warning(f"   SUPABASE_ANON_KEY: {'Set' if self.supabase_key else 'NOT SET'}")
        except ImportError:
            logger.warning("⚠️ supabase-py not installed. Install with: pip install supabase. File uploads will use local storage.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}. File uploads will use local storage.")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    def upload_file(self, file, article_id: int) -> str:
        """
        Upload file to Supabase Storage.
        
        Args:
            file: Django UploadedFile object
            article_id: ID of the article
            
        Returns:
            Public URL of the uploaded file
        """
        # Generate unique filename
        file_ext = Path(file.name).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        storage_path = f"articles/{article_id}/{unique_filename}"
        
        if self.client:
            try:
                # Read file content
                file.seek(0)  # Reset file pointer
                file_content = file.read()
                
                # Upload to Supabase Storage
                # supabase-py upload method: upload(path, file, file_options={})
                # file_options: {"content-type": "...", "upsert": "true"}
                file_options = {
                    "content-type": file.content_type or "application/octet-stream",
                    "upsert": "true"
                }
                
                logger.info(f"Attempting to upload to Supabase: bucket={self.bucket_name}, path={storage_path}, size={len(file_content)} bytes")
                
                # Upload file
                response = self.client.storage.from_(self.bucket_name).upload(
                    path=storage_path,
                    file=file_content,
                    file_options=file_options
                )
                
                logger.info(f"Supabase upload response type: {type(response)}, value: {response}")
                
                # Supabase returns a dict with 'error' key if failed, or the path if successful
                if isinstance(response, dict):
                    if "error" in response:
                        error_msg = response.get("error", "Unknown error")
                        error_message = response.get("message", "")
                        raise Exception(f"Supabase upload error: {error_msg} - {error_message}")
                    # Success response might be: {"path": "articles/1/uuid.pdf"}
                    if "path" in response:
                        logger.info(f"Upload successful, path: {response['path']}")
                
                # Get public URL
                public_url = self.client.storage.from_(self.bucket_name).get_public_url(storage_path)
                logger.info(f"✅ File uploaded to Supabase Storage: {storage_path}")
                logger.info(f"Public URL: {public_url}")
                return public_url
                
            except Exception as e:
                logger.error(f"❌ Supabase upload failed: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Fallback to local storage
                logger.warning("Falling back to local storage...")
                return self._upload_local(file, storage_path)
        else:
            # Fallback to local storage
            return self._upload_local(file, storage_path)

    def _upload_local(self, file, storage_path: str) -> str:
        """Fallback to local filesystem storage."""
        try:
            file.seek(0)  # Reset file pointer
            saved_path = default_storage.save(storage_path, file)
            file_url = default_storage.url(saved_path)
            logger.info(f"File uploaded to local storage: {saved_path}")
            return file_url
        except Exception as e:
            logger.error(f"Local file upload failed: {e}")
            raise

    def delete_file(self, file_url: str) -> bool:
        """
        Delete file from Supabase Storage.
        
        Args:
            file_url: Public URL of the file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.client:
            # For local storage, file deletion is handled by Django
            return True
        
        try:
            # Extract path from URL
            # Supabase URLs format: https://{project}.supabase.co/storage/v1/object/public/{bucket}/{path}
            if "supabase.co/storage" in file_url or "supabase.co/storage/v1/object/public" in file_url:
                # Extract the path after the bucket name
                if f"/{self.bucket_name}/" in file_url:
                    path = file_url.split(f"/{self.bucket_name}/")[-1].split("?")[0]  # Remove query params
                    self.client.storage.from_(self.bucket_name).remove([path])
                    logger.info(f"File deleted from Supabase Storage: {path}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Supabase file deletion failed: {e}")
            return False

