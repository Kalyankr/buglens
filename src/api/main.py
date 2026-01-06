from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger
import shutil
from pathlib import Path

from src.worker.tasks import process_bug_video
from src.database.session import get_db, init_db
from src.database.models import BugJob
from src.utils.logging_config import setup_logging

# Initialize logging and database
setup_logging()
init_db()

app = FastAPI(title="BugLens API")
UPLOAD_DIR = Path("data/raw")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/upload")
async def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Receives a video, saves it, and creates a PENDING job in the DB.
    """
    file_path = UPLOAD_DIR / file.filename

    try:
        # Save file to disk
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create Database Record
        new_job = BugJob(filename=file.filename, status="PENDING")
        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        process_bug_video.delay(new_job.id, str(file_path))
        logger.info(f"Created Job {new_job.id} for file {file.filename}")

        return {"job_id": new_job.id, "status": "QUEUED"}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/status/{job_id}")
async def get_status(job_id: str, db: Session = Depends(get_db)):
    """
    Check the current status of a bug report.
    """
    job = db.query(BugJob).filter(BugJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "status": job.status,
        "result": job.result,
        "created_at": job.created_at,
    }
