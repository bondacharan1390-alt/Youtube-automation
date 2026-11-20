"""Official YouTube Data API v3 Chunked Resumable Upload Engine."""
import logging
import math
import os
import time
from typing import Callable, Dict, Any, Optional, Tuple
import httpx

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB standard Google chunk size
MIN_CHUNK_SIZE = 256 * 1024           # 256 KB minimum unit


class ResumableUploader:
    """Manages RFC 7233 byte-range chunked uploads to YouTube with network interruption recovery."""

    @classmethod
    def initiate_resumable_session(
        cls,
        access_token: str,
        title: str,
        description: str,
        tags: list,
        privacy_status: str,
        total_file_size: int,
        category_id: str = "28",
        scheduled_publish_time: Optional[str] = None,
    ) -> str:
        """Initiates a resumable upload session and returns the upload location URI."""
        url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Length": str(total_file_size),
            "X-Upload-Content-Type": "video/mp4",
        }
        body: Dict[str, Any] = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags,
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status.lower(),
                "selfDeclaredMadeForKids": False,
            },
        }
        if scheduled_publish_time and privacy_status.lower() == "private":
            body["status"]["publishAt"] = scheduled_publish_time

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=body, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to initiate resumable upload session: {resp.status_code} - {resp.text}")
            upload_url = resp.headers.get("Location")
            if not upload_url:
                raise RuntimeError("Google did not return a resumable Location URL in response headers.")
            return upload_url

    @classmethod
    def upload_chunk(
        cls,
        upload_url: str,
        file_path: str,
        start_byte: int,
        chunk_size: int,
        total_bytes: int,
    ) -> Tuple[int, int, Optional[str]]:
        """Uploads a single byte-range chunk. Returns (status_code, next_start_byte, video_id_if_complete)."""
        end_byte = min(start_byte + chunk_size - 1, total_bytes - 1)
        actual_chunk_length = end_byte - start_byte + 1

        headers = {
            "Content-Range": f"bytes {start_byte}-{end_byte}/{total_bytes}",
            "Content-Length": str(actual_chunk_length),
            "Content-Type": "video/mp4",
        }

        with open(file_path, "rb") as f:
            f.seek(start_byte)
            data = f.read(actual_chunk_length)

        with httpx.Client(timeout=180.0) as client:
            resp = client.put(upload_url, content=data, headers=headers)
            status_code = resp.status_code

            if status_code in (200, 201):
                # Video fully uploaded!
                res_json = resp.json()
                video_id = res_json.get("id")
                return status_code, total_bytes, video_id

            elif status_code == 308:
                # 308 Resume Incomplete: parse Range header
                range_header = resp.headers.get("Range")
                if range_header:
                    # e.g., "bytes=0-5242879"
                    confirmed_end = int(range_header.split("-")[1])
                    return status_code, confirmed_end + 1, None
                else:
                    return status_code, end_byte + 1, None

            else:
                raise RuntimeError(f"Chunk upload failed with HTTP {status_code}: {resp.text}")

    @classmethod
    def query_upload_status(cls, upload_url: str, total_bytes: int) -> int:
        """Queries the Google upload server for how many bytes have been safely received."""
        headers = {
            "Content-Range": f"bytes */{total_bytes}",
            "Content-Length": "0",
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.put(upload_url, headers=headers)
            if resp.status_code == 308:
                range_header = resp.headers.get("Range")
                if range_header:
                    # bytes=0-456789
                    confirmed_end = int(range_header.split("-")[1])
                    return confirmed_end + 1
            elif resp.status_code in (200, 201):
                return total_bytes
        return 0

    @classmethod
    def upload_video_resumable(
        cls,
        upload_url: str,
        file_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        max_retries: int = 3,
    ) -> str:
        """Uploads full video in chunks with automatic retry and range resumption."""
        total_bytes = os.path.getsize(file_path)
        if total_bytes == 0:
            raise ValueError(f"Video file is empty (0 bytes): {file_path}")
        start_byte = 0

        # Check if session already has partial progress
        try:
            confirmed = cls.query_upload_status(upload_url, total_bytes)
            if confirmed > 0:
                start_byte = confirmed
                logger.info(f"Resuming upload from confirmed byte position {start_byte}/{total_bytes}")
        except Exception:
            pass

        while start_byte < total_bytes:
            attempt = 0
            chunk_success = False

            while attempt < max_retries and not chunk_success:
                try:
                    status_code, next_byte, video_id = cls.upload_chunk(
                        upload_url=upload_url,
                        file_path=file_path,
                        start_byte=start_byte,
                        chunk_size=chunk_size,
                        total_bytes=total_bytes,
                    )

                    start_byte = next_byte
                    chunk_success = True

                    if progress_callback:
                        progress_callback(start_byte, total_bytes)

                    if video_id:
                        return video_id

                except Exception as e:
                    attempt += 1
                    logger.warning(f"Chunk upload error (attempt {attempt}/{max_retries}): {e}")
                    if attempt >= max_retries:
                        raise RuntimeError(f"Upload failed after {max_retries} attempts: {e}")
                    # Exponential backoff
                    time.sleep(2 ** attempt)
                    # Query current server position before re-attempting
                    try:
                        confirmed = cls.query_upload_status(upload_url, total_bytes)
                        if confirmed > 0:
                            start_byte = confirmed
                    except Exception:
                        pass

        raise RuntimeError("Upload ended without receiving a YouTube Video ID.")

    @classmethod
    def simulate_resumable_upload(
        cls,
        file_path: str,
        chunk_size: int = 512 * 1024,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """Simulates full RFC 7233 resumable upload validation without external network requirements."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found for simulation: {file_path}")

        total_bytes = os.path.getsize(file_path)
        if total_bytes == 0:
            raise ValueError(f"Video file is empty (0 bytes): {file_path}")
        chunks_count = math.ceil(total_bytes / chunk_size)
        start_byte = 0
        validated_headers = []

        for i in range(chunks_count):
            end_byte = min(start_byte + chunk_size - 1, total_bytes - 1)
            actual_len = end_byte - start_byte + 1

            # Validate header structure
            content_range = f"bytes {start_byte}-{end_byte}/{total_bytes}"
            content_length = str(actual_len)
            validated_headers.append({
                "chunk_index": i + 1,
                "Content-Range": content_range,
                "Content-Length": content_length,
                "bytes_transferred": actual_len,
            })

            start_byte = end_byte + 1
            if progress_callback:
                progress_callback(start_byte, total_bytes)

        import uuid
        simulated_id = f"sim_{uuid.uuid4().hex[:11]}"
        return {
            "success": True,
            "status": "uploaded",
            "video_id": simulated_id,
            "total_bytes": total_bytes,
            "chunks_transferred": chunks_count,
            "validated_headers": validated_headers,
        }
