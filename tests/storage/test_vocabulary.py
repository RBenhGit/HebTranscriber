from hebtranscriber.storage.vocabulary import add_term, list_terms, remove_term


def test_add_and_list_terms(tmp_path):
    db_path = tmp_path / "vocab.db"
    add_term("דוד כהן", db_path=db_path)
    add_term('אקמה בע"מ', db_path=db_path)
    assert list_terms(db_path=db_path) == ['אקמה בע"מ', "דוד כהן"]


def test_add_term_strips_whitespace(tmp_path):
    db_path = tmp_path / "vocab.db"
    add_term("  שם עם רווחים  ", db_path=db_path)
    assert list_terms(db_path=db_path) == ["שם עם רווחים"]


def test_add_duplicate_term_is_idempotent(tmp_path):
    db_path = tmp_path / "vocab.db"
    add_term("מונח", db_path=db_path)
    add_term("מונח", db_path=db_path)
    assert list_terms(db_path=db_path) == ["מונח"]


def test_remove_term(tmp_path):
    db_path = tmp_path / "vocab.db"
    add_term("מונח א", db_path=db_path)
    add_term("מונח ב", db_path=db_path)
    remove_term("מונח א", db_path=db_path)
    assert list_terms(db_path=db_path) == ["מונח ב"]
