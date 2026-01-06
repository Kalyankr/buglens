from loguru import logger
import ffmpeg
from ultralytics import YOLO
from pathlib import Path
import os


class BugLensVision:
    def __init__(self, model_path: str = "yolov8n.pt"):
        logger.info(f"Loading YOLO model: {model_path}")
        # Load the model (YOLOv10 or v8)
        self.model = YOLO(model_path)

    def extract_frames(
        self, video_path: str, output_dir: str = "data/temp_frames", fps: int = 1
    ):
        """Extracts frames from video using ffmpeg for efficiency."""

        abs_video_path = os.path.abspath(video_path)
        abs_output_dir = os.path.abspath(output_dir)

        logger.info(f"Extracting frames: {abs_video_path} -> {abs_output_dir}")

        if not os.path.exists(abs_video_path):
            logger.error(f"Input video not found: {abs_video_path}")
            raise FileNotFoundError(f"Video file missing: {abs_video_path}")

        Path(abs_output_dir).mkdir(parents=True, exist_ok=True)
        try:
            (
                ffmpeg.input(abs_video_path)
                .filter("fps", fps=fps)
                .output(os.path.join(abs_output_dir, "frame_%04d.jpg"))
                .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            # Log the actual stderr from ffmpeg
            logger.error(f"FFmpeg Stderr: {e.stderr.decode()}")
            raise e

        frames = sorted(list(Path(abs_output_dir).glob("*.jpg")))
        logger.success(f"Extracted {len(frames)} frames.")
        return frames

    def detect_ui(self, frame_paths: list):
        """Runs inference on extracted frames to find UI bugs/elements."""
        logger.info(f"Starting UI detection on {len(frame_paths)} frames...")
        results = []
        for frame in frame_paths:
            # stream=True is more memory efficient
            prediction = self.model(str(frame), verbose=False)[0]
            detections = []
            for box in prediction.boxes:
                label = prediction.names[int(box.cls)]
                conf = float(box.conf)
                if conf > 0.4:
                    detections.append({"label": label, "conf": conf})

            if detections:
                results.append({"timestamp": frame.stem, "detections": detections})

        logger.success(
            f"Vision analysis complete. Found anomalies in {len(results)} frames."
        )
        return results


# Example Usage
if __name__ == "__main__":
    engine = BugLensVision()
    frames = engine.extract_frames("data/raw/test.mp4", "data/temp_frames")
    ui_logs = engine.detect_ui(frames)
    print(ui_logs)
