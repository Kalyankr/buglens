from loguru import logger
from .celery_app import celery_app
from src.database.session import SessionLocal
from src.database.models import BugJob
from src.engine.vision import BugLensVision
from src.engine.audio import BugLensAudio
from src.engine.fusion import BugLensFusion


@celery_app.task(name="process_bug_video")
def process_bug_video(job_id: str, file_path: str):
    logger.info(f"Processing task for job {job_id}")
    db = SessionLocal()
    try:
        # Update status to PROCESSING
        job = db.query(BugJob).filter(BugJob.id == job_id).first()
        if not job:
            return "Job not found"

        job.status = "PROCESSING"
        db.commit()
        logger.info(f"Worker started processing Job: {job_id}")

        # Run Engines
        vision = BugLensVision()
        audio = BugLensAudio()
        fuser = BugLensFusion()

        frames = vision.extract_frames(file_path)
        ui_logs = vision.detect_ui(frames)
        transcript = audio.process_audio(file_path)

        # Fuse Results
        final_report = fuser.fuse(ui_logs, transcript)

        # Save result and mark as COMPLETED
        job.result = final_report
        job.status = "COMPLETED"
        db.commit()
        logger.success(f"Worker finished Job: {job_id}")

    except Exception as e:
        logger.error(f"Worker failed on Job {job_id}: {str(e)}")
        job.status = "FAILED"
        job.error_message = str(e)
        db.commit()
    finally:
        db.close()
