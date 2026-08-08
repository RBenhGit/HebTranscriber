"""Stage 1: file-to-text transcription via faster-whisper."""

from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
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


@lru_cache(maxsize=4)
def _load_model(model_name: str, compute_type: str) -> WhisperModel:
    return WhisperModel(model_name, device="cpu", compute_type=compute_type)


def transcribe(
    audio: str | np.ndarray,
    model_name: str = ASR_MODEL,
    compute_type: str = "int8",
    on_segment: Callable[[Segment], None] | None = None,
) -> TranscriptionResult:
    """Transcribe a Hebrew audio/video file path, or an in-memory mono
    float32 waveform at 16kHz (for live dictation).

    Calls `on_segment` as each segment is produced, so a caller can show
    progress on long files without this function chunking audio itself —
    faster-whisper already windows long input internally. The model is
    cached across calls (by model_name/compute_type) so repeated live
    utterances don't pay the model-load cost each time.
    """
    model = _load_model(model_name, compute_type)
    raw_segments, info = model.transcribe(audio, language="he", beam_size=5)

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
