"""Stage 3: live microphone capture, producing fixed-size audio frames.

Requires the system PortAudio library (`libportaudio2` on Debian/Ubuntu) and
an available input device. Both are environment-specific and can't be
verified in a headless/CI environment — this module has no automated test
coverage; verify manually by running dictate.py.
"""

from collections.abc import Iterator

import numpy as np
import sounddevice as sd

from hebtranscriber.audio.vad import FRAME_SAMPLES, SAMPLE_RATE


def microphone_frames(
    sample_rate: int = SAMPLE_RATE, frame_samples: int = FRAME_SAMPLES
) -> Iterator[np.ndarray]:
    """Yield fixed-size mono float32 frames from the default microphone,
    forever, until the caller stops iterating."""
    with sd.InputStream(
        samplerate=sample_rate, channels=1, dtype="float32", blocksize=frame_samples
    ) as stream:
        while True:
            frame, _overflowed = stream.read(frame_samples)
            yield frame[:, 0]
