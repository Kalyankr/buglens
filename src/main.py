import json

from loguru import logger

from engine.audio import BugLensAudio
from engine.fusion import BugLensFusion
from engine.vision import BugLensVision
from utils.logging_config import setup_logging


@logger.catch  # Automatically catch and log any crash in the entire pipeline
def run_pipeline(video_path):
    setup_logging()

    # Initialize Engines
    vision = BugLensVision()
    audio = BugLensAudio()
    fuser = BugLensFusion()

    # Process
    frames = vision.extract_frames(video_path)
    ui_logs = vision.detect_ui(frames)
    transcript = audio.process_audio(video_path)

    # Fuse and Output
    final_report = fuser.fuse(ui_logs, transcript)
    logger.info("Report Output:")
    print(json.dumps(final_report, indent=2))


if __name__ == "__main__":
    run_pipeline("data/raw/test.mp4")
