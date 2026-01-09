from loguru import logger


class BugLensFusion:
    def __init__(self, window=3.0):
        self.window = window

    def fuse(self, ui_data, audio_data):
        logger.info("Fusing multimodal signals...")
        report = []

        # Check if we have data to fuse
        if not audio_data:
            logger.warning("No audio data found. Returning vision-only report.")
            return {"status": "Complete", "bug_events": []}

        for speech in audio_data:
            # Create a time window around the speech segment
            t_start = max(0, speech["start"] - self.window)
            t_end = speech["end"] + self.window

            # Match visual frames to this speech window
            relevant_frames = [
                f for f in ui_data if t_start <= float(f["time"]) <= t_end
            ]

            if relevant_frames:
                logger.info(f"Found visual correlation for: '{speech['text'][:30]}...'")
                report.append(
                    {
                        "time": int(speech["start"]),  # Anchor event to start of speech
                        "voice": speech["text"],
                        "visuals": relevant_frames,
                    }
                )

        logger.success(f"Fusion complete. Linked {len(report)} voice-to-visual events.")
        return {"status": "Complete", "bug_events": report}
