from unittest.mock import Mock, patch

import pytest

from hebtranscriber.cleaning.cleaner import _chunk_words, clean, list_models, transform


def test_chunk_words_single_chunk_when_under_limit():
    words = ["מילה"] * 10
    chunks = _chunk_words(words, limit=500, overlap=50)
    assert chunks == [("", " ".join(words))]


def test_chunk_words_splits_without_duplicating_words():
    words = [str(i) for i in range(120)]
    chunks = _chunk_words(words, limit=50, overlap=10)

    # every word appears as a *target* exactly once across all chunks
    all_targets = " ".join(target for _, target in chunks).split()
    assert all_targets == words

    # each chunk's context is the previous chunk's trailing words
    assert chunks[0][0] == ""
    assert chunks[1][0] == " ".join(words[40:50])
    assert chunks[2][0] == " ".join(words[90:100])


def test_clean_returns_empty_string_for_empty_input():
    assert clean("") == ""


def _fake_chat_response(content: str) -> Mock:
    response = Mock()
    response.json.return_value = {"message": {"role": "assistant", "content": content}}
    response.raise_for_status = Mock()
    return response


def test_clean_sends_one_request_per_chunk_and_joins_responses():
    words = [str(i) for i in range(600)]  # over CHUNK_WORD_LIMIT (500), forces 2 chunks
    text = " ".join(words)

    with patch(
        "hebtranscriber.cleaning.cleaner.requests.post",
        side_effect=[_fake_chat_response(" נקי א "), _fake_chat_response(" נקי ב ")],
    ) as mock_post:
        result = clean(text, model="qwen2.5:1.5b")

    assert result == "נקי א נקי ב"
    assert mock_post.call_count == 2
    for call in mock_post.call_args_list:
        assert call.kwargs["json"]["model"] == "qwen2.5:1.5b"
        roles = [m["role"] for m in call.kwargs["json"]["messages"]]
        assert roles == ["system", "user"]


def test_clean_passes_prior_chunk_tail_as_context_not_as_target():
    words = [str(i) for i in range(600)]
    text = " ".join(words)

    with patch(
        "hebtranscriber.cleaning.cleaner.requests.post",
        side_effect=[_fake_chat_response("א"), _fake_chat_response("ב")],
    ) as mock_post:
        clean(text, model="qwen2.5:1.5b")

    second_call_user_message = mock_post.call_args_list[1].kwargs["json"]["messages"][1]["content"]
    assert " ".join(words[450:500]) in second_call_user_message
    assert "הקשר קודם" in second_call_user_message


def test_transform_rejects_unknown_kind():
    with pytest.raises(ValueError):
        transform("טקסט", kind="not-a-real-kind")


def test_transform_sends_correct_prompt_for_kind():
    with patch(
        "hebtranscriber.cleaning.cleaner.requests.post",
        return_value=_fake_chat_response("- נקודה אחת"),
    ) as mock_post:
        result = transform("טקסט לדוגמה", kind="keypoints")

    assert result == "- נקודה אחת"
    sent_messages = mock_post.call_args.kwargs["json"]["messages"]
    user_content = sent_messages[1]["content"]
    assert "טקסט לדוגמה" in user_content
    assert "נקודות עיקריות" in user_content


def test_list_models_returns_installed_model_names():
    fake_response = Mock()
    fake_response.json.return_value = {
        "models": [{"name": "qwen2.5:1.5b"}, {"name": "gemma2:latest"}]
    }
    fake_response.raise_for_status = Mock()

    with patch(
        "hebtranscriber.cleaning.cleaner.requests.get", return_value=fake_response
    ) as mock_get:
        result = list_models()

    assert result == ["qwen2.5:1.5b", "gemma2:latest"]
    mock_get.assert_called_once()
