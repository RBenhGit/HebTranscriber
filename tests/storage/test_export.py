from hebtranscriber.asr.transcriber import Segment
from hebtranscriber.storage.export import export_markdown, export_srt, export_txt


def test_export_txt_writes_raw_text(tmp_path):
    path = tmp_path / "out.txt"
    export_txt("טקסט לדוגמה", path)
    assert path.read_text(encoding="utf-8") == "טקסט לדוגמה"


def test_export_markdown_adds_title_heading(tmp_path):
    path = tmp_path / "out.md"
    export_markdown("תוכן התמלול", path, title="הפגישה שלי")
    assert path.read_text(encoding="utf-8") == "# הפגישה שלי\n\nתוכן התמלול\n"


def test_export_srt_formats_timestamps_and_numbering(tmp_path):
    path = tmp_path / "out.srt"
    segments = [
        Segment(start=0.0, end=1.5, text="שלום"),
        Segment(start=61.25, end=63.0, text="עולם"),
    ]
    export_srt(segments, path)

    assert path.read_text(encoding="utf-8") == (
        "1\n00:00:00,000 --> 00:00:01,500\nשלום\n\n2\n00:01:01,250 --> 00:01:03,000\nעולם\n"
    )
