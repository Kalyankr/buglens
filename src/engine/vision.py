import os

import cv2
import easyocr
from loguru import logger
from ultralytics import YOLO


class BugLensVision:
    def __init__(self, model_path: str = "yolov8n.pt"):
        logger.info(f"Loading YOLO model: {model_path}")
        self.model = YOLO(model_path)

        # set gpu=True if GPU available in Docker
        logger.info("Initializing OCR Engine...")
        self.reader = easyocr.Reader(["en"], gpu=False)

    def process_and_annotate(self, video_path: str, job_id: str):
        abs_video_path = os.path.abspath(video_path)
        output_dir = os.path.dirname(abs_video_path)
        vision_video_path = os.path.join(output_dir, f"{job_id}_vision.mp4")

        cap = cv2.VideoCapture(abs_video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Video file missing: {abs_video_path}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        # Using mp4v (ffmpeg handles the conversion later)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(vision_video_path, fourcc, fps, (width, height))

        ui_logs = []
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            results = self.model(frame, verbose=False)
            result = results[0]

            annotated_frame = result.plot()
            out.write(annotated_frame)

            # OCR and Detection Logic (Every 1 second of video)
            if frame_count % int(fps) == 0:
                seconds = frame_count // int(fps)
                frame_events = []

                for box in result.boxes:
                    conf = float(box.conf)
                    cls_id = int(box.cls)
                    label = self.model.names[cls_id]

                    if conf > 0.4:
                        coords = box.xyxy[0].cpu().numpy().astype(int)
                        x1, y1, x2, y2 = coords

                        roi = frame[y1:y2, x1:x2]

                        ocr_text = ""
                        if roi.size > 0:
                            ocr_results = self.reader.readtext(roi)
                            ocr_text = " ".join([res[1] for res in ocr_results])

                        frame_events.append(
                            {
                                "label": label,
                                "conf": round(conf, 2),
                                "text_found": ocr_text,
                                "box": [int(x1), int(y1), int(x2), int(y2)],
                            }
                        )

                if frame_events:
                    ui_logs.append({"time": seconds, "visuals": frame_events})

            frame_count += 1

        cap.release()
        out.release()
        return ui_logs, vision_video_path


# Example Usage
if __name__ == "__main__":
    engine = BugLensVision()
    logs, vid = engine.process_and_annotate("data/raw/test.mp4", "test")
    print(f"Found {len(logs)} events. Video at {vid}")
