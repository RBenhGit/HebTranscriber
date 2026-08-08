from unittest.mock import Mock, patch

from hebtranscriber.setup import ensure_asr_model, ensure_llm_model


def test_ensure_asr_model_triggers_model_load():
    with patch("hebtranscriber.setup.ensure_model_loaded") as mock_ensure:
        ensure_asr_model("some-model", "int8")

    mock_ensure.assert_called_once_with("some-model", "int8")


def test_ensure_asr_model_uses_default_when_none_given():
    with patch("hebtranscriber.setup.ensure_model_loaded") as mock_ensure:
        ensure_asr_model()

    mock_ensure.assert_called_once_with(compute_type="int8")


def test_ensure_llm_model_streams_progress_events():
    fake_response = Mock()
    fake_response.__enter__ = Mock(return_value=fake_response)
    fake_response.__exit__ = Mock(return_value=False)
    fake_response.raise_for_status = Mock()
    fake_response.iter_lines.return_value = [
        b'{"status": "pulling manifest"}',
        b'{"status": "success"}',
    ]

    events = []
    with patch("hebtranscriber.setup.requests.post", return_value=fake_response) as mock_post:
        ensure_llm_model("qwen2.5:1.5b", on_progress=events.append)

    assert events == [{"status": "pulling manifest"}, {"status": "success"}]
    assert mock_post.call_args.kwargs["json"]["model"] == "qwen2.5:1.5b"
