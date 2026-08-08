"""Stage 5: export transcripts to TXT, Markdown, and SRT."""

from pathlib import Path

from hebtranscriber.asr import Segment


def export_txt(text: str, path: str | Path) -> None:
    Path(path).write_text(text, encoding="utf-8")


def export_markdown(text: str, path: str | Path, title: str = "תמלול") -> None:
    Path(path).write_text(f"# {title}\n\n{text}\n", encoding="utf-8")


def _format_srt_timestamp(seconds: float) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    millis = round((secs % 1) * 1000)
    return f"{int(hours):02}:{int(minutes):02}:{int(secs):02},{millis:03}"


def export_srt(segments: list[Segment], path: str | Path) -> None:
    lines = []
    for i, segment in enumerate(segments, start=1):
        lines.append(str(i))
        timing = f"{_format_srt_timestamp(segment.start)} --> {_format_srt_timestamp(segment.end)}"
        lines.append(timing)
        lines.append(segment.text.strip())
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")
