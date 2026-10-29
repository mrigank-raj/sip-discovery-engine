import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from engine import demo, store  # noqa: E402


def test_export_strips_authors_and_unextracted_text_and_check_blocks_leaks(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTHOR_HASH_SALT", "t")
    monkeypatch.setattr(demo, "ROOT", tmp_path)                      # no .env here, so no secrets to look for
    src = store.init_db(tmp_path / "src.db")
    db = store.connect(src)
    store.insert_items(db, [{"item_id": i, "source": "play", "url": "u", "text": f"review number {i} about my SIP", "author": "Jane",
                             "raw": {"userName": "Jane", "keep": 1}} for i in ("a", "b")], since_date="2000-01-01")
    db.execute("INSERT INTO extractions(item_id, json) VALUES('a', '{}')")
    db.execute("INSERT INTO runs(run_id, stage) VALUES('r', 'x')")
    db.commit()
    stats = demo.export(src, tmp_path / "out.db")
    out = sqlite3.connect(tmp_path / "out.db")
    assert stats["text_kept"] == 1 and out.execute("SELECT text FROM raw_items WHERE item_id='b'").fetchone()[0] == ""
    assert out.execute("SELECT COUNT(*) FROM raw_items WHERE author_hash IS NOT NULL OR raw_json != '{}'").fetchone()[0] == 0
    assert demo.check(tmp_path / "out.db") == []
    out.execute("UPDATE raw_items SET author_hash='x'")
    out.execute("INSERT INTO runs(run_id, stage) VALUES('r', 'x')")
    out.commit()
    assert set(demo.check(tmp_path / "out.db")) == {"author hashes present", "run logs or review notes present"}
