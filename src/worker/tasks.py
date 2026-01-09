import shutil
import subprocess
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
        job = db.query(BugJob).filter(BugJob.id == job_id).first()
        if not job:
            return "Job not found"

        job.status = "PROCESSING"
        db.commit()

        vision = BugLensVision()
        audio = BugLensAudio()
        fuser = BugLensFusion()

        # Vision Engine (Creates the job_id_vision.mp4)
        ui_logs, annotated_video_path = vision.process_and_annotate(file_path, job_id)

        # Web transcoding
        logger.info("Starting web-ready transcoding for browser compatibility...")
        web_path = str(annotated_video_path).replace(".mp4", "_web.mp4")

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(annotated_video_path),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "ultrafast",
            "-crf",
            "28",
            web_path,
        ]

        subprocess.run(cmd, check=True)
        logger.success(f"Transcoding complete: {web_path}")

        # Audio Engine
        transcript = audio.process_audio(file_path)

        # Fuse Results
        final_report = fuser.fuse(ui_logs, transcript)

        # Generate LLM Summary
        logger.info("Generating AI Summary ...")
        human_summary = generate_llm_summary(final_report)

        # Save Results
        job.result = final_report
        job.vision_file_path = web_path
        job.summary = human_summary
        job.status = "COMPLETED"
        db.commit()

        logger.success(f"Worker finished Job: {job_id}")

    except Exception as e:
        logger.error(f"Worker failed on Job {job_id}: {str(e)}")
        if job:
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
    # 'host.docker.internal' is the URL to talk to  Mac from Docker
    ollama_url = "http://host.docker.internal:11434/api/generate"

    prompt = f"""
    ### ROLE
    You are 'BugLens Advisor', an expert QA Automation Engineer. Your task is to analyze raw metadata from a screen recording and identify discrepancies.

    ### DATA INPUT
    - User Speech (Whisper): "{fusion_data.get("transcript", "No audio detected")}"
    - Visual Detections (YOLO): {fusion_data.get("ui_logs", "No visual logs")}

    ### INSTRUCTIONS
    1. **Compare** the user's intent (Speech) with the system's reality (Detections).
    2. **Identify Anomaly**: Is there a "Mismatch"? (e.g., User says "I'm clicking Login" but YOLO only sees "Error Popup").
    3. **Tone**: Be professional, concise, and technical.

    ### OUTPUT FORMAT
    Return your response using this EXACT Markdown structure:
    **Executive Summary**: (One sentence)
    **User Intent**: (What the user was trying to do)
    **Visual Evidence**: (What was actually seen on screen)
    **Verdict**: (BUG, ANOMALY, or EXPECTED BEHAVIOR)
    """

    try:
        response = httpx.post(
            ollama_url,
            json={
                "model": "llama3.2:3b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3},
            },
            timeout=45.0,
        )
        return response.json().get("response", "Analysis unavailable.")
    except Exception as e:
        return f"Summarizer error: {str(e)}"
