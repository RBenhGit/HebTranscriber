from unittest.mock import Mock, patch

import pytest

from hebtranscriber.asr.transcriber import Segment, _load_model, ensure_model_loaded, transcribe


@pytest.fixture(autouse=True)
def _clear_model_cache():
    # _load_model is lru_cache'd across calls (deliberately, for live dictation);
    # clear it so each test's WhisperModel patch is actually exercised.
    _load_model.cache_clear()
    yield
    _load_model.cache_clear()


def _fake_raw_segment(start, end, text):
    seg = Mock()
    seg.start = start
    seg.end = end
    seg.text = text
    return seg


def test_transcribe_builds_full_text_and_segments():
    fake_info = Mock(duration=12.5)
    fake_segments = [
        _fake_raw_segment(0.0, 2.0, "שלום "),
        _fake_raw_segment(2.0, 4.5, "עולם"),
    ]
    fake_model = Mock()
    fake_model.transcribe.return_value = (iter(fake_segments), fake_info)

    with patch("hebtranscriber.asr.transcriber.WhisperModel", return_value=fake_model) as mock_cls:
        result = transcribe("fake.wav")

    mock_cls.assert_called_once()
    fake_model.transcribe.assert_called_once_with("fake.wav", language="he", beam_size=5)
    assert result.text == "שלום עולם"
    assert result.duration_s == 12.5
    assert result.segments == [
        Segment(0.0, 2.0, "שלום "),
        Segment(2.0, 4.5, "עולם"),
    ]


def test_transcribe_reports_progress_via_callback():
    fake_info = Mock(duration=2.0)
    fake_segments = [_fake_raw_segment(0.0, 2.0, "בדיקה")]
    fake_model = Mock()
    fake_model.transcribe.return_value = (iter(fake_segments), fake_info)

    seen = []
    with patch("hebtranscriber.asr.transcriber.WhisperModel", return_value=fake_model):
        transcribe("fake.wav", on_segment=seen.append)

    assert seen == [Segment(0.0, 2.0, "בדיקה")]


def test_ensure_model_loaded_triggers_and_caches_model_load():
    with patch("hebtranscriber.asr.transcriber.WhisperModel", return_value=Mock()) as mock_cls:
        ensure_model_loaded("some-model", "int8")
        ensure_model_loaded("some-model", "int8")

    mock_cls.assert_called_once()  # second call hits the lru_cache, no reload
