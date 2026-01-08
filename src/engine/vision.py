import os

import cv2
from loguru import logger
from ultralytics import YOLO


class BugLensVision:
    def __init__(self, model_path: str = "yolov8n.pt"):
        logger.info(f"Loading YOLO model: {model_path}")
        self.model = YOLO(model_path)

    def process_and_annotate(self, video_path: str, job_id: str):
        """
        Detects UI elements AND creates the 'AI Vision' video.
        Replaces extract_frames and detect_ui.
        """
        abs_video_path = os.path.abspath(video_path)
        output_dir = os.path.dirname(abs_video_path)
        # The new video will be saved as jobid_vision.mp4
        vision_video_path = os.path.join(output_dir, f"{job_id}_vision.mp4")

        logger.info(f"Starting Vision Engine: {abs_video_path}")

        cap = cv2.VideoCapture(abs_video_path)
        if not cap.isOpened():
            logger.error("Could not open video file.")
            raise FileNotFoundError(f"Video file missing: {abs_video_path}")

        # Get Video Properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        # Setup Video Writer for the 'Pro' Annotated Video
        # Using 'mp4v' codec for broad compatibility
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(vision_video_path, fourcc, fps, (width, height))

        ui_logs = []
        frame_count = 0

        logger.info("Processing frames and drawing AI Vision overlay...")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Run YOLO Inference on the current frame
            # verbose=False keeps the logs clean
            results = self.model(frame, verbose=False)
            result = results[0]

            # Create the annotated frame and write to video
            annotated_frame = result.plot()
            out.write(annotated_frame)

            # Record detections for the JSON timeline
            # log detections once per second of video
            if frame_count % int(fps) == 0:
                seconds = frame_count // int(fps)
                frame_detections = []

                for box in result.boxes:
                    conf = float(box.conf)
                    if conf > 0.4:  # Your confidence threshold
                        frame_detections.append(
                            {
                                "label": self.model.names[int(box.cls)],
                                "conf": round(conf, 2),
                            }
                        )

                if frame_detections:
                    ui_logs.append({"time": seconds, "detections": frame_detections})

            frame_count += 1

        cap.release()
        out.release()

        logger.success(f"Vision Complete. Annotated video saved: {vision_video_path}")
        return ui_logs, vision_video_path


# Example Usage
if __name__ == "__main__":
    engine = BugLensVision()
    logs, vid = engine.process_and_annotate("data/raw/test.mp4", "test")
    print(f"Found {len(logs)} events. Video at {vid}")
