from typing import List, Dict


class BugLensFusion:
    def __init__(self, window_size: float = 3.0):
        self.window_size = window_size  # seconds to look ahead/behind

    def fuse_signals(self, ui_logs: List[Dict], transcript: List[Dict]):
        """
        Alines CV and NLP signals to find the bug's 'Ground Zero'.
        """
        fused_events = []

        # Simple keywords indicating user frustration or intent
        action_keywords = [
            "click",
            "press",
            "button",
            "error",
            "broken",
            "why",
            "not working",
        ]

        for text_segment in transcript:
            # Check if user sounds frustrated or describes an action
            is_relevant = any(
                kw in text_segment["text"].lower() for kw in action_keywords
            )

            if is_relevant:
                # Look for UI detections within the time window
                t_start = text_segment["start"] - self.window_size
                t_end = text_segment["end"] + self.window_size

                nearby_ui = [
                    log
                    for log in ui_logs
                    if t_start <= float(log["timestamp"].replace("frame_", "")) <= t_end
                ]

                if nearby_ui:
                    fused_events.append(
                        {
                            "timestamp": text_segment["start"],
                            "user_said": text_segment["text"],
                            "visuals_seen": nearby_ui,
                        }
                    )

        return fused_events
