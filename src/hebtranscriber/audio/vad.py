"""Stage 3: voice activity detection and utterance segmentation.

Pure signal processing — no microphone dependency, so it can run (and be
tested) on machines without PortAudio. See capture.py for the live mic feed.
"""

from collections.abc import Iterable, Iterator

import numpy as np
import torch
from silero_vad import VADIterator, load_silero_vad

SAMPLE_RATE = 16000
FRAME_SAMPLES = 512  # ~32ms at 16kHz, silero-vad's expected chunk size
SILENCE_DURATION_MS = 800  # within the work plan's 0.7-1.0s pause-ends-segment range
DEFAULT_THRESHOLD = 0.5  # silero-vad's own default; higher = less sensitive to speech


def segment_utterances(
    frames: Iterable[np.ndarray],
    sample_rate: int = SAMPLE_RATE,
    silence_duration_ms: int = SILENCE_DURATION_MS,
    threshold: float = DEFAULT_THRESHOLD,
) -> Iterator[np.ndarray]:
    """Consume a stream of fixed-size float32 audio frames and yield one
    concatenated array per utterance, once `silence_duration_ms` of silence
    follows detected speech. Any speech still buffered when `frames` ends
    is flushed as a final utterance.
    """
    model = load_silero_vad(onnx=True)
    vad_iterator = VADIterator(
        model,
        sampling_rate=sample_rate,
        min_silence_duration_ms=silence_duration_ms,
        threshold=threshold,
    )

    buffer: list[np.ndarray] = []
    in_speech = False

    for frame in frames:
        event = vad_iterator(torch.from_numpy(frame), return_seconds=False)

        if event is not None and "start" in event:
            in_speech = True
        if in_speech:
            buffer.append(frame)
        if event is not None and "end" in event:
            in_speech = False
            if buffer:
                yield np.concatenate(buffer)
            buffer = []

    if buffer:
        yield np.concatenate(buffer)
