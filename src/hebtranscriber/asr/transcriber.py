"""Stage 1: file-to-text transcription via faster-whisper."""

from collections.abc import Callable
from dataclasses import dataclass

from faster_whisper import WhisperModel

ASR_MODEL = "ivrit-ai/whisper-large-v3-turbo-ct2"


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class TranscriptionResult:
    text: str
    segments: list[Segment]
    duration_s: float


def transcribe(
    audio_path: str,
    model_name: str = ASR_MODEL,
    compute_type: str = "int8",
    on_segment: Callable[[Segment], None] | None = None,
) -> TranscriptionResult:
    """Transcribe a Hebrew audio/video file.

    Calls `on_segment` as each segment is produced, so a caller can show
    progress on long files without this function chunking audio itself —
    faster-whisper already windows long input internally.
    """
    model = WhisperModel(model_name, device="cpu", compute_type=compute_type)
    raw_segments, info = model.transcribe(audio_path, language="he", beam_size=5)

    segments = []
    for raw in raw_segments:
        segment = Segment(start=raw.start, end=raw.end, text=raw.text)
        segments.append(segment)
        if on_segment is not None:
            on_segment(segment)

    return TranscriptionResult(
        text="".join(s.text for s in segments),
        segments=segments,
        duration_s=info.duration,
    )
