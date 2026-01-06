import ffmpeg
from faster_whisper import WhisperModel
from pathlib import Path


class BugLensAudio:
    def __init__(self, model_size: str = "base"):
        # base is fast; 'large-v3' for higher accuracy
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def process_audio(self, video_path: str):
        """Extracts audio from video and transcribes it."""
        video_file = Path(video_path)
        audio_output = video_file.with_suffix(".wav")

        # Extract audio via ffmpeg
        (
            ffmpeg.input(str(video_file))
            .output(str(audio_output), ac=1, ar="16k")
            .run(overwrite_output=True, quiet=True)
        )

        # Transcribe
        segments, info = self.model.transcribe(str(audio_output), beam_size=5)

        transcript_data = []
        for segment in segments:
            transcript_data.append(
                {
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "text": segment.text.strip(),
                }
            )

        return transcript_data


# Test the Audio Engine
if __name__ == "__main__":
    audio_engine = BugLensAudio()
    results = audio_engine.process_audio("data/raw/test_bug.mp4")
    for r in results:
        print(f"[{r['start']}s - {r['end']}s]: {r['text']}")
