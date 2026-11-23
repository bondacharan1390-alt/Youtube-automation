"""Render job orchestration: start, track, and complete render jobs."""
import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.project import RenderJob, Project
from app.services.hardware_queue import HardwareTaskQueue
from app.services.video.video_composer import compose_video_async

logger = logging.getLogger(__name__)

class RenderJobService:
    _background_tasks = set()

    @staticmethod
    async def start_render(
        project_id: str,
        resolution: str,
        include_subtitles: bool,
        bgm_volume: float,
        db: Session,
        bitrate_kbps: int = 5000,
        fps: int = 25,
    ) -> RenderJob:
        """Create a render job and start async background composition."""
        # Cancel any existing queued job for same project
        existing = (
            db.query(RenderJob)
            .filter(RenderJob.project_id == project_id, RenderJob.status == "queued")
            .first()
        )
        if existing:
            existing.status = "cancelled"
            db.commit()

        job = RenderJob(
            project_id=project_id,
            status="queued",
            progress_percentage=0,
            error_log="Initialising render pipeline...",
            started_at=datetime.now(timezone.utc),
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id

        async def _run():
            # Need a fresh db session for the background coroutine
            from app.core.database import SessionLocal
            bg_db = SessionLocal()
            try:
                bg_job = bg_db.query(RenderJob).filter(RenderJob.id == job_id).first()
                if bg_job:
                    bg_job.status = "rendering"
                    bg_db.commit()

                output_path = await HardwareTaskQueue.run_sequential(
                    f"VideoRender_{project_id}",
                    compose_video_async(
                        project_id=project_id,
                        resolution=resolution,
                        include_subtitles=include_subtitles,
                        bgm_volume=bgm_volume,
                        db=bg_db,
                        job_id=job_id,
                        bitrate_kbps=bitrate_kbps,
                        fps=fps,
                    ),
                )

                bg_job = bg_db.query(RenderJob).filter(RenderJob.id == job_id).first()
                if bg_job:
                    bg_job.status = "completed"
                    bg_job.output_file_path = output_path
                    bg_job.completed_at = datetime.now(timezone.utc)
                    bg_job.progress_percentage = 100
                    bg_db.commit()
            except Exception as e:
                logger.exception(f"Render job {job_id} failed: {e}")
                try:
                    bg_job = bg_db.query(RenderJob).filter(RenderJob.id == job_id).first()
                    if bg_job:
                        bg_job.status = "failed"
                        bg_job.error_log = str(e)
                        bg_db.commit()
                except Exception:
                    pass
            finally:
                bg_db.close()

        task = asyncio.create_task(_run())
        RenderJobService._background_tasks.add(task)
        task.add_done_callback(RenderJobService._background_tasks.discard)
        return job

    @classmethod
    async def stop_background_tasks(cls) -> None:
        """Cancel outstanding render tasks during application/test shutdown."""
        tasks = [task for task in cls._background_tasks if not task.done()]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        cls._background_tasks.clear()

    @staticmethod
    def get_job_status(job_id: str, db: Session) -> dict:
        db.expire_all()
        job = db.query(RenderJob).filter(RenderJob.id == job_id).first()
        if not job:
            return {"error": "Job not found"}
        output_url = None
        if job.output_file_path and job.status == "completed":
            import os
            fname = os.path.basename(job.output_file_path)
            output_url = f"/storage/renders/{fname}"
        return {
            "job_id": job.id,
            "project_id": job.project_id,
            "status": job.status,
            "progress_percentage": job.progress_percentage,
            "output_url": output_url,
            "error_log": job.error_log,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }
