"""Stage 0 feasibility benchmark: ASR speed/memory and LLM cleanup throughput.

See Docs/תכנית-עבודה-פיתוח-מתמלל_1.md, Stage 0, for the pass/fail criteria this
script exists to measure: transcription faster than 1x real-time, LLM above
15 tokens/sec.
"""

import argparse
import resource
import shutil
import time

import psutil
import requests

ASR_MODEL = "ivrit-ai/whisper-large-v3-turbo-ct2"
DEFAULT_LLM_MODEL = "qwen2.5:1.5b"
OLLAMA_URL = "http://localhost:11434/api/generate"

CLEANUP_SAMPLE_PROMPT = (
    "נקה את הטקסט הבא מהיסוסים ומילות מילוי, הוסף פיסוק, ואל תשנה את המשמעות. "
    "החזר אך ורק את הטקסט הנקי, ללא הקדמות:\n\n"
    "אה, אז ככה, אני חושב, כאילו, שאנחנו צריכים להתחיל את הפגישה, אמ, "
    "עכשיו, כי יש לנו הרבה זמן... לא, מעט זמן."
)


def hardware_info() -> dict:
    mem = psutil.virtual_memory()
    return {
        "ram_total_gb": round(mem.total / 1024**3, 1),
        "ram_available_gb": round(mem.available / 1024**3, 1),
        "cpu_count": psutil.cpu_count(logical=True),
        "gpu_available": shutil.which("nvidia-smi") is not None,
    }


def real_time_factor(processing_s: float, audio_duration_s: float) -> float:
    if audio_duration_s <= 0:
        raise ValueError("audio_duration_s must be positive")
    return processing_s / audio_duration_s


def tokens_per_second(eval_count: int, eval_duration_ns: int) -> float:
    if eval_duration_ns <= 0:
        raise ValueError("eval_duration_ns must be positive")
    return eval_count / (eval_duration_ns / 1e9)


def benchmark_asr(audio_path: str, model_name: str = ASR_MODEL, compute_type: str = "int8") -> dict:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device="cpu", compute_type=compute_type)

    start = time.monotonic()
    segments, info = model.transcribe(audio_path, language="he", beam_size=5)
    text = "".join(segment.text for segment in segments)
    processing_s = time.monotonic() - start

    return {
        "audio_duration_s": info.duration,
        "processing_s": processing_s,
        "real_time_factor": real_time_factor(processing_s, info.duration),
        "peak_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        "text": text,
    }


def benchmark_llm(model_name: str = DEFAULT_LLM_MODEL, prompt: str = CLEANUP_SAMPLE_PROMPT) -> dict:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        },
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()

    return {
        "tokens_per_second": tokens_per_second(data["eval_count"], data["eval_duration"]),
        "response_text": data["response"],
    }


def print_report(hw: dict, asr: dict | None, llm: dict | None) -> None:
    print("=== Hardware ===")
    print(
        f"RAM: {hw['ram_available_gb']}/{hw['ram_total_gb']} GB available, {hw['cpu_count']} CPUs, "
        f"GPU: {'yes' if hw['gpu_available'] else 'no'}"
    )

    if asr is not None:
        print("\n=== ASR (faster-whisper) ===")
        print(f"Audio duration: {asr['audio_duration_s']:.1f}s")
        print(f"Processing time: {asr['processing_s']:.1f}s")
        print(
            f"Real-time factor: {asr['real_time_factor']:.2f}x "
            f"({'PASS' if asr['real_time_factor'] < 1.0 else 'FAIL'}, target < 1.0x)"
        )
        print(f"Peak RSS: {asr['peak_rss_mb']:.0f} MB")
        print(f"Transcript: {asr['text'][:200]}")

    if llm is not None:
        print("\n=== LLM cleanup (Ollama) ===")
        print(
            f"Tokens/sec: {llm['tokens_per_second']:.1f} "
            f"({'PASS' if llm['tokens_per_second'] > 15 else 'FAIL'}, target > 15 tok/s)"
        )
        print(f"Sample output: {llm['response_text'][:200]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio_path", nargs="?", help="Path to a Hebrew audio file (any format)")
    parser.add_argument("--llm-model", default=DEFAULT_LLM_MODEL)
    parser.add_argument("--asr-model", default=ASR_MODEL)
    parser.add_argument("--skip-llm", action="store_true")
    args = parser.parse_args()

    hw = hardware_info()
    asr_result = benchmark_asr(args.audio_path, args.asr_model) if args.audio_path else None
    llm_result = None if args.skip_llm else benchmark_llm(args.llm_model)

    print_report(hw, asr_result, llm_result)


if __name__ == "__main__":
    main()
