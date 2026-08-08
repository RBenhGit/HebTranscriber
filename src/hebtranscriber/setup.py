"""Stage 6: first-run setup — download the ASR and LLM models if missing,
with progress reporting.

faster-whisper's own download-on-first-use (via huggingface_hub) already
reports its own progress to stderr; `ensure_asr_model` just triggers it
early instead of waiting for the first real transcription. Ollama model
pulls are streamed here explicitly since Ollama's API otherwise gives no
feedback until the whole (multi-GB) download finishes.
"""

import json
from collections.abc import Callable

import requests

from hebtranscriber.asr import ensure_model_loaded

OLLAMA_PULL_URL = "http://localhost:11434/api/pull"


def ensure_asr_model(model_name: str | None = None, compute_type: str = "int8") -> None:
    if model_name is None:
        ensure_model_loaded(compute_type=compute_type)
    else:
        ensure_model_loaded(model_name, compute_type)


def ensure_llm_model(model_name: str, on_progress: Callable[[dict], None] | None = None) -> None:
    """Pull an Ollama model, streaming progress events. No-ops quickly if
    the model is already installed — safe to call on every startup."""
    with requests.post(
        OLLAMA_PULL_URL, json={"model": model_name, "stream": True}, stream=True, timeout=None
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line:
                continue
            event = json.loads(line)
            if on_progress is not None:
                on_progress(event)
