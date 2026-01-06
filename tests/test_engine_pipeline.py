import pytest
from src.engine.vision import BugLensVision
from src.engine.audio import BugLensAudio
from src.engine.fusion import BugLensFusion


def test_full_pipeline_logic():
    # Use a small, 2-second sample video for testing
    test_video = "data/raw/test.mp4"

    vision = BugLensVision()
    audio = BugLensAudio()
    fuser = BugLensFusion()

    # Test individual components
    frames = vision.extract_frames(test_video)
    assert len(frames) > 0

    ui_logs = vision.detect_ui(frames)
    transcript = audio.process_audio(test_video)

    # Test fusion
    report = fuser.fuse(ui_logs, transcript)

    assert "status" in report
    assert "bug_events" in report
    assert report["status"] == "Complete"

    # CLEANUP: Senior engineers always clean up test artifacts
    import shutil

    shutil.rmtree("data/temp_frames", ignore_errors=True)
