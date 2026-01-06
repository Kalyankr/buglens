from loguru import logger


class BugLensFusion:
    def __init__(self, window=3.0):
        self.window = window

    def fuse(self, ui_data, audio_data):
        logger.info("Fusing multimodal signals...")
        report = []

        for speech in audio_data:
            t_start = speech["start"] - self.window
            t_end = speech["end"] + self.window

            # Match visual frames to this speech window
            relevant_frames = [
                f
                for f in ui_data
                if t_start <= float(f["timestamp"].split("_")[1]) <= t_end
            ]

            if relevant_frames:
                logger.info(f"Found visual correlation for: '{speech['text'][:30]}...'")
                report.append(
                    {
                        "time": speech["start"],
                        "voice": speech["text"],
                        "visuals": relevant_frames,
                    }
                )

        logger.success("Fusion complete. Finalizing report structure.")
        return {"status": "Complete", "bug_events": report}
