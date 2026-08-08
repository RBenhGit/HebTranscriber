from unittest.mock import Mock, patch

from hebtranscriber.asr.transcriber import Segment, transcribe


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
