import shutil
from pathlib import Path

import httpx
from loguru import logger

from src.database.models import BugJob
from src.database.session import SessionLocal
from src.engine.audio import BugLensAudio
from src.engine.fusion import BugLensFusion
from src.engine.vision import BugLensVision

from .celery_app import celery_app


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

        # Generate LLM Summary
        logger.info("Generating AI Summary via Ollama...")
        human_summary = generate_llm_summary(final_report)

        # Save result and mark as COMPLETED
        job.result = final_report
        job.summary = human_summary
        job.status = "COMPLETED"
        db.commit()
        logger.success(f"Worker finished Job: {job_id}")

    except Exception as e:
        logger.error(f"Worker failed on Job {job_id}: {str(e)}")
        job.status = "FAILED"
        job.error_message = str(e)
        db.commit()
    finally:
        # Cleanup frames to save disk space
        temp_path = Path("data/temp_frames")
        if temp_path.exists():
            shutil.rmtree(temp_path)
            logger.debug("Cleaned up temporary frames.")
        db.close()


def generate_llm_summary(fusion_data: dict):
    """
    Sends the JSON fusion data to Ollama to generate a human-readable report.
    """
    # 'host.docker.internal' is the magic URL to talk to  Mac from Docker
    ollama_url = "http://host.docker.internal:11434/api/generate"

    prompt = f"""
    You are BugLens AI. Summarize this screen recording metadata:
    Transcript: "{fusion_data}"

    Provide a 2-sentence summary of what happened and 
    list any potential 'bugs' or 'anomalies'.
    
    Format:
    - Summary: (What happened)
    - Visual Context: (What was seen)
    - Speech: (What was said)
    """

    try:
        response = httpx.post(
            ollama_url,
            json={"model": "llama3.2:3b", "prompt": prompt, "stream": False},
            timeout=30.0,
        )
        return response.json().get("response", "Could not generate summary.")
    except Exception as e:
        return f"Summarizer error: {str(e)}"
