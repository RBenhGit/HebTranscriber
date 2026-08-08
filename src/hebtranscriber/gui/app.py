"""Stage 4: Flet desktop GUI.

Mic capture (sounddevice) and the global hotkey (pynput) are imported lazily,
inside the handlers that need them, not at module level — both crash at
*import time* on machines missing their system libraries (PortAudio /
display-server input hooks), and the rest of the app (file transcription,
cleanup, transformations, settings) must stay usable without them.
"""

import threading
import time

import flet as ft
import numpy as np
import requests

from hebtranscriber.asr import ensure_model_loaded, transcribe
from hebtranscriber.cleaning import DEFAULT_MODEL, clean, list_models, prewarm, transform
from hebtranscriber.storage import list_terms, save_session

TRANSFORM_LABELS = {
    "keypoints": "נקודות עיקריות",
    "formal": "פורמלי",
    "short": "קצר",
    "long": "ארוך",
}


def _list_mic_devices() -> list[str]:
    try:
        import sounddevice as sd

        return [d["name"] for d in sd.query_devices() if d["max_input_channels"] > 0]
    except OSError:
        return []


def main(page: ft.Page) -> None:
    page.title = "מתמלל"
    page.rtl = True
    page.window.width = 720
    page.window.height = 640

    state = {
        "recording": False,
        "raw_text": "",
        "clean_text": "",
        "raw_parts": [],
        "session_parts": [],
        "session_start": 0.0,
        "llm_model": DEFAULT_MODEL,
        "vad_threshold": 0.5,
    }

    transcript = ft.TextField(
        label="תמלול", multiline=True, min_lines=10, max_lines=10, read_only=True, expand=True
    )
    level_meter = ft.ProgressBar(value=0, width=400)
    status_text = ft.Text("")
    raw_clean_switch = ft.Switch(label="הצג גולמי")

    def _refresh_display() -> None:
        transcript.value = state["raw_text"] if raw_clean_switch.value else state["clean_text"]
        page.update()

    raw_clean_switch.on_change = lambda e: _refresh_display()

    def _run_dictation() -> None:
        try:
            from hebtranscriber.audio.capture import microphone_frames
            from hebtranscriber.audio.vad import segment_utterances
        except OSError as exc:
            status_text.value = f"מיקרופון לא זמין: {exc}"
            state["recording"] = False
            record_button.text = "התחל הקלטה"
            page.update()
            return

        def leveled_frames():
            for frame in microphone_frames():
                level_meter.value = min(float(np.sqrt(np.mean(frame**2))) * 8, 1.0)
                page.update()
                yield frame

        vocabulary = list_terms()
        for utterance in segment_utterances(leveled_frames(), threshold=state["vad_threshold"]):
            if not state["recording"]:
                break
            result = transcribe(utterance)
            if not result.text.strip():
                continue
            state["raw_text"] = result.text
            _refresh_display()
            cleaned = clean(result.text, model=state["llm_model"], vocabulary=vocabulary)
            state["clean_text"] = cleaned
            state["raw_parts"].append(result.text)
            state["session_parts"].append(cleaned)
            _refresh_display()

        level_meter.value = 0
        page.update()

    def toggle_recording(_e) -> None:
        state["recording"] = not state["recording"]
        if state["recording"]:
            record_button.text = "עצור הקלטה"
            status_text.value = "מקליט..."
            state["raw_parts"] = []
            state["session_parts"] = []
            state["session_start"] = time.monotonic()
            threading.Thread(target=_run_dictation, daemon=True).start()
        else:
            record_button.text = "התחל הקלטה"
            full_text = " ".join(state["session_parts"])
            if full_text:
                duration_s = time.monotonic() - state["session_start"]
                save_session(" ".join(state["raw_parts"]), full_text, duration_s)

                import pyperclip

                try:
                    pyperclip.copy(full_text)
                    status_text.value = f"הועתקו {len(full_text)} תווים ללוח"
                except pyperclip.PyperclipException as exc:
                    status_text.value = f"העתקה ללוח נכשלה: {exc}"
            else:
                status_text.value = "לא זוהה דיבור"
        page.update()

    record_button = ft.ElevatedButton(
        "התחל הקלטה", icon=ft.Icons.MIC, on_click=toggle_recording, height=60
    )

    def _make_transform_handler(kind: str):
        def handler(_e):
            if not state["clean_text"]:
                return
            transcript.value = transform(state["clean_text"], kind, model=state["llm_model"])
            page.update()

        return handler

    transform_buttons = ft.Row(
        [
            ft.ElevatedButton(label, on_click=_make_transform_handler(kind))
            for kind, label in TRANSFORM_LABELS.items()
        ]
    )

    def _on_file_picked(e: ft.FilePickerResultEvent) -> None:
        if not e.files:
            return
        path = e.files[0].path
        status_text.value = f"מתמלל את {path}..."
        page.update()

        def worker():
            result = transcribe(path)
            state["raw_text"] = result.text
            state["clean_text"] = clean(
                result.text, model=state["llm_model"], vocabulary=list_terms()
            )
            state["session_parts"] = [state["clean_text"]]
            status_text.value = "הושלם"
            _refresh_display()

        threading.Thread(target=worker, daemon=True).start()

    # Flet has no stable OS-level file drag-and-drop API (only in-app
    # DragTarget/Draggable between controls) — a file picker dialog is the
    # supported way to get a file path from the user.
    file_picker = ft.FilePicker(on_result=_on_file_picked)
    page.overlay.append(file_picker)
    file_button = ft.ElevatedButton(
        "בחר קובץ לתמלול",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=lambda e: file_picker.pick_files(allow_multiple=False),
    )

    try:
        available_models = list_models()
    except (requests.exceptions.RequestException, KeyError, ValueError):
        available_models = [DEFAULT_MODEL]
    model_dropdown = ft.Dropdown(
        label="מודל ניקוי",
        value=state["llm_model"],
        options=[ft.dropdown.Option(m) for m in available_models],
    )
    mic_dropdown = ft.Dropdown(
        label="מיקרופון",
        options=[ft.dropdown.Option(m) for m in _list_mic_devices()]
        or [ft.dropdown.Option("ברירת מחדל")],
    )
    threshold_slider = ft.Slider(
        label="סף VAD: {value}", min=0.1, max=0.9, value=state["vad_threshold"]
    )

    def _save_settings(_e) -> None:
        state["llm_model"] = model_dropdown.value or state["llm_model"]
        state["vad_threshold"] = threshold_slider.value
        settings_dialog.open = False
        page.update()

    settings_dialog = ft.AlertDialog(
        title=ft.Text("הגדרות"),
        content=ft.Column([mic_dropdown, model_dropdown, threshold_slider], tight=True),
        actions=[ft.TextButton("שמור", on_click=_save_settings)],
    )
    page.overlay.append(settings_dialog)

    def _open_settings(_e) -> None:
        settings_dialog.open = True
        page.update()

    def _setup_global_hotkey() -> None:
        try:
            from pynput import keyboard

            listener = keyboard.GlobalHotKeys({"<ctrl>+<shift>+d": lambda: toggle_recording(None)})
            listener.start()
        except Exception as exc:  # noqa: BLE001 - platform hotkey backends fail in
            # too many different, undocumented ways (missing display, Wayland
            # input restrictions, no X server) to enumerate; this is a
            # best-effort convenience feature and must never crash the app.
            status_text.value = f"קיצור מקלדת גלובלי (Ctrl+Shift+D) לא זמין: {exc}"
            page.update()

    _setup_global_hotkey()

    # Load both models now, in the background, so the first real action
    # isn't slowed down by a cold model load (Stage 6: "load once, stay warm").
    threading.Thread(target=ensure_model_loaded, daemon=True).start()
    threading.Thread(target=prewarm, args=(state["llm_model"],), daemon=True).start()

    page.add(
        ft.Row(
            [
                ft.Text("מתמלל", size=24, weight=ft.FontWeight.BOLD),
                ft.IconButton(icon=ft.Icons.SETTINGS, on_click=_open_settings),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        record_button,
        level_meter,
        status_text,
        raw_clean_switch,
        transcript,
        transform_buttons,
        file_button,
    )
