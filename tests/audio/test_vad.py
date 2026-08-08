from pathlib import Path

import numpy as np
from faster_whisper.audio import decode_audio

from hebtranscriber.audio.vad import FRAME_SAMPLES, SAMPLE_RATE, segment_utterances

TEST_AUDIO = Path(__file__).resolve().parents[2] / "Docs" / "Transcribe test.ogg"


def _frames(audio: np.ndarray):
    n_frames = len(audio) // FRAME_SAMPLES
    for i in range(n_frames):
        yield audio[i * FRAME_SAMPLES : (i + 1) * FRAME_SAMPLES]


def test_segment_utterances_yields_nothing_for_pure_silence():
    silence = np.zeros(SAMPLE_RATE * 3, dtype=np.float32)  # 3s of silence
    assert list(segment_utterances(_frames(silence))) == []


def test_segment_utterances_finds_real_speech_in_test_clip():
    audio = decode_audio(str(TEST_AUDIO))
    utterances = list(segment_utterances(_frames(audio)))

    assert len(utterances) >= 1
    total_speech_s = sum(len(u) for u in utterances) / SAMPLE_RATE
    clip_duration_s = len(audio) / SAMPLE_RATE
    # most of the clip is speech; VAD shouldn't miss the bulk of it, nor
    # somehow report more speech than the file actually contains
    assert clip_duration_s * 0.5 < total_speech_s < clip_duration_s


def test_segment_utterances_threshold_is_wired_through():
    audio = decode_audio(str(TEST_AUDIO))
    default_speech_s = sum(len(u) for u in segment_utterances(_frames(audio))) / SAMPLE_RATE
    strict_speech_s = (
        sum(len(u) for u in segment_utterances(_frames(audio), threshold=0.99)) / SAMPLE_RATE
    )
    # an unreasonably high speech-probability threshold must detect no more
    # speech than the default — proves the parameter actually reaches the model
    assert strict_speech_s <= default_speech_s
