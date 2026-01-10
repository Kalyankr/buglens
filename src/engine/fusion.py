import re

from loguru import logger


class BugLensFusion:
    def __init__(self, window=3.0):
        self.window = window

    def parse_logs(self, log_content):
        """
        Extracts errors and timestamps from raw log text.
        Assumes standard log formats (e.g., 2026-01-08 22:09:14 ERROR ...)
        """
        log_events = []
        pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+) \| (.*)"

        for line in log_content.splitlines():
            match = re.search(pattern, line)
            if match:
                ts_str, level, message = match.groups()
                if level in ["ERROR", "CRITICAL", "WARNING"]:
                    log_events.append(
                        {"timestamp": ts_str, "level": level, "message": message}
                    )
        return log_events

    def fuse(self, ui_data, audio_data, log_data=None):
        logger.info("Fusing multimodal signals (Vision + Audio + Logs)...")
        report = []

        if not audio_data:
            logger.warning("No audio data found. Fusion will be degraded.")
            return {"status": "Incomplete", "bug_events": []}

        for speech in audio_data:
            t_start = max(0, speech["start"] - self.window)
            t_end = speech["end"] + self.window

            relevant_frames = [
                f for f in ui_data if t_start <= float(f["time"]) <= t_end
            ]

            relevant_logs = []
            if log_data:
                # Basic relative sync for now
                relevant_logs = [
                    log for log in log_data if "ERROR" in log.get("level", "")
                ]
            if relevant_frames or relevant_logs:
                logger.info(f"Found evidence for: '{speech['text'][:30]}...'")
                report.append(
                    {
                        "time": int(speech["start"]),
                        "voice": speech["text"],
                        "visuals": relevant_frames,
                        "logs": relevant_logs,
                    }
                )

        logger.success(f"Fusion complete. {len(report)} multi-layered events found.")
        return {"status": "Complete", "bug_events": report}
