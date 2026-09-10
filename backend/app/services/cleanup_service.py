import os
import time
import asyncio
from app.config import settings
from app.utils.logger import logger

class CleanupService:
    @staticmethod
    def ensure_temp_directory():
        os.makedirs(settings.TEMP_DIR, exist_ok=True)

    @classmethod
    def get_video_path(cls, session_id: str) -> str:
        cls.ensure_temp_directory()
        return os.path.join(settings.TEMP_DIR, f"{session_id}.webm")

    @classmethod
    def delete_video_file(cls, session_id: str) -> bool:
        video_path = cls.get_video_path(session_id)
        if os.path.exists(video_path):
            try:
                os.remove(video_path)
                logger.info(f"Successfully deleted temporary video recording for session {session_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete video file {video_path}: {e}")
                return False
        return False

    @classmethod
    def purge_expired_videos(cls) -> int:
        cls.ensure_temp_directory()
        ttl_seconds = settings.VIDEO_TTL_MINUTES * 60
        now = time.time()
        deleted_count = 0

        try:
            for filename in os.listdir(settings.TEMP_DIR):
                if filename.endswith(".webm") or filename.endswith(".mp4"):
                    filepath = os.path.join(settings.TEMP_DIR, filename)
                    file_age = now - os.path.getmtime(filepath)
                    if file_age > ttl_seconds:
                        try:
                            os.remove(filepath)
                            deleted_count += 1
                            logger.info(f"TTL Worker purged expired video file: {filename}")
                        except Exception as e:
                            logger.error(f"Error purging file {filename}: {e}")
        except Exception as e:
            logger.error(f"Error scanning temp directory for TTL cleanup: {e}")

        return deleted_count

    @classmethod
    async def start_background_cleanup_worker(cls, interval_minutes: int = 15):
        logger.info("Starting background video TTL cleanup worker task...")
        while True:
            try:
                purged = cls.purge_expired_videos()
                if purged > 0:
                    logger.info(f"Background worker purged {purged} expired interview recordings.")
            except Exception as e:
                logger.error(f"Error in video cleanup worker loop: {e}")
            await asyncio.sleep(interval_minutes * 60)
