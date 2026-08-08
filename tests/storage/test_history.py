from hebtranscriber.storage.history import recent_sessions, save_session, search, stats


def test_save_and_recent_sessions_round_trip(tmp_path):
    db_path = tmp_path / "history.db"
    session_id = save_session("גולמי", "נקי אחד שתיים", duration_s=6.0, db_path=db_path)

    sessions = recent_sessions(db_path=db_path)
    assert len(sessions) == 1
    assert sessions[0].id == session_id
    assert sessions[0].raw_text == "גולמי"
    assert sessions[0].clean_text == "נקי אחד שתיים"
    assert sessions[0].words_per_minute == 30.0  # 3 words / 6s * 60


def test_save_session_with_zero_duration_does_not_divide_by_zero(tmp_path):
    db_path = tmp_path / "history.db"
    save_session("x", "y", duration_s=0.0, db_path=db_path)
    assert recent_sessions(db_path=db_path)[0].words_per_minute == 0.0


def test_recent_sessions_orders_newest_first(tmp_path):
    db_path = tmp_path / "history.db"
    save_session("r1", "c1", duration_s=1.0, db_path=db_path)
    save_session("r2", "c2", duration_s=1.0, db_path=db_path)

    sessions = recent_sessions(db_path=db_path)
    assert [s.clean_text for s in sessions] == ["c2", "c1"]


def test_search_finds_matching_session_by_hebrew_word(tmp_path):
    db_path = tmp_path / "history.db"
    save_session("r1", "פגישה מחר בבוקר", duration_s=1.0, db_path=db_path)
    save_session("r2", "קניות בסופר", duration_s=1.0, db_path=db_path)

    results = search("פגישה", db_path=db_path)
    assert len(results) == 1
    assert results[0].clean_text == "פגישה מחר בבוקר"


def test_search_finds_no_results_for_unmatched_term(tmp_path):
    db_path = tmp_path / "history.db"
    save_session("r1", "פגישה מחר", duration_s=1.0, db_path=db_path)
    assert search("קניות", db_path=db_path) == []


def test_stats_on_empty_history(tmp_path):
    db_path = tmp_path / "history.db"
    result = stats(db_path=db_path)
    assert result == {
        "total_sessions": 0,
        "total_words": 0,
        "last_session_words": 0,
        "average_words_per_minute": 0.0,
    }


def test_stats_aggregates_across_sessions(tmp_path):
    db_path = tmp_path / "history.db"
    save_session("r1", "מילה אחת", duration_s=2.0, db_path=db_path)  # 2 words, 60 wpm
    save_session("r2", "שלוש מילים כאן", duration_s=6.0, db_path=db_path)  # 3 words, 30 wpm

    result = stats(db_path=db_path)
    assert result["total_sessions"] == 2
    assert result["total_words"] == 5
    assert result["last_session_words"] == 3  # most recent session
    assert result["average_words_per_minute"] == 45.0
