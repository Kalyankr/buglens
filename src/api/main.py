import shutil
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from loguru import logger
from sqlalchemy.orm import Session

from src.api.schemas import JobStatusResponse
from src.database.models import BugJob
from src.database.session import get_db, init_db
from src.utils.logging_config import setup_logging
from src.worker.tasks import process_bug_video

# Initialize logging and database
setup_logging()
init_db()

app = FastAPI(title="BugLens API")
UPLOAD_DIR = Path("/app/data/raw")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# upload video
@app.post("/upload")
async def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Receives a video, saves it, and creates a PENDING job in the DB.
    """
    file_path = UPLOAD_DIR / file.filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        new_job = BugJob(
            filename=file.filename,
            file_path=str(file_path),
            status="PENDING",
        )

        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        process_bug_video.delay(new_job.id, str(file_path))
        logger.info(f"Created Job {new_job.id} for file {file.filename}")

        return {"job_id": new_job.id, "status": "QUEUED"}

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# get job status
@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_status(job_id: str, db: Session = Depends(get_db)):
    """
    Check the current status of a bug report.
    """
    job = db.query(BugJob).filter(BugJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


# get job list
@app.get("/jobs")
async def list_jobs(db: Session = Depends(get_db)):
    """
    Returns a list of all bug reports in the system.
    """
    jobs = db.query(BugJob).order_by(BugJob.created_at.desc()).all()
    return [
        {
            "id": j.id,
            "status": j.status,
            "filename": j.filename,
            "created_at": j.created_at,
        }
        for j in jobs
    ]


# delete job
@app.delete("/jobs/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(BugJob).filter(BugJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Delete the actual video file too
    video_path = UPLOAD_DIR / job.filename
    if video_path.exists():
        video_path.unlink()

    db.delete(job)
    db.commit()
    return {"message": "Job deleted"}
