from unittest.mock import Mock, patch

import pytest

from hebtranscriber.benchmark import (
    benchmark_llm,
    hardware_info,
    real_time_factor,
    tokens_per_second,
)


def test_real_time_factor_faster_than_real_time():
    assert real_time_factor(processing_s=2.0, audio_duration_s=10.0) == pytest.approx(0.2)


def test_real_time_factor_rejects_zero_duration():
    with pytest.raises(ValueError):
        real_time_factor(processing_s=1.0, audio_duration_s=0.0)


def test_tokens_per_second():
    # 30 tokens in 2 seconds (2e9 ns) => 15 tok/s
    assert tokens_per_second(eval_count=30, eval_duration_ns=2_000_000_000) == pytest.approx(15.0)


def test_tokens_per_second_rejects_zero_duration():
    with pytest.raises(ValueError):
        tokens_per_second(eval_count=10, eval_duration_ns=0)


def test_hardware_info_reports_expected_fields():
    info = hardware_info()
    assert info["ram_total_gb"] > 0
    assert info["ram_available_gb"] >= 0
    assert info["cpu_count"] >= 1
    assert isinstance(info["gpu_available"], bool)


def test_benchmark_llm_computes_tokens_per_second_from_ollama_response():
    fake_response = Mock()
    fake_response.json.return_value = {
        "response": "טקסט נקי",
        "eval_count": 15,
        "eval_duration": 1_000_000_000,
    }
    fake_response.raise_for_status = Mock()

    with patch("hebtranscriber.benchmark.requests.post", return_value=fake_response) as mock_post:
        result = benchmark_llm(model_name="qwen2.5:1.5b", prompt="test")

    assert result["tokens_per_second"] == pytest.approx(15.0)
    assert result["response_text"] == "טקסט נקי"
    mock_post.assert_called_once()
