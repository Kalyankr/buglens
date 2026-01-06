import cv2
import ffmpeg
from ultralytics import YOLO
from pathlib import Path


class BugLensVision:
    def __init__(self, model_path: str = "yolov8n.pt"):
        # Load the model (YOLOv10 or v8)
        self.model = YOLO(model_path)

    def extract_frames(self, video_path: str, output_folder: str, fps: int = 1):
        """Extracts frames from video using ffmpeg for efficiency."""
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        (
            ffmpeg.input(video_path)
            .filter("fps", fps=fps)
            .output(f"{output_folder}/frame_%04d.jpg")
            .run(overwrite_output=True, quiet=True)
        )
        return sorted(list(Path(output_folder).glob("*.jpg")))

    def detect_ui_elements(self, frame_paths: list):
        """Runs inference on extracted frames to find UI bugs/elements."""
        results_summary = []

        for frame in frame_paths:
            results = self.model(frame)[0]
            detections = []
            for box in results.boxes:
                # care about classes like 'Error Modal', 'Loading Spinner', etc.
                label = results.names[int(box.cls)]
                conf = float(box.conf)
                if conf > 0.4:  # Threshold
                    detections.append({"label": label, "confidence": conf})

            if detections:
                results_summary.append(
                    {"timestamp": frame.stem, "detections": detections}
                )

        return results_summary


# Example Usage
if __name__ == "__main__":
    engine = BugLensVision()
    frames = engine.extract_frames("test_bug.mp4", "./temp_frames")
    ui_logs = engine.detect_ui_elements(frames)
    print(ui_logs)
