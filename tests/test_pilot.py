import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from engine import extract, pilot, store  # noqa: E402


def test_run_saves_each_batch_to_the_database_as_it_goes(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTHOR_HASH_SALT", "t")
    db_path = store.init_db(tmp_path / "t.db")
    monkeypatch.setattr(pilot, "DB_PATH", db_path)
    db = store.connect(db_path)
    for k in range(3):
        db.execute("INSERT INTO raw_items(item_id, source, product, url, fetched_at, text, content_hash) VALUES(?,?,?,?,?,?,?)",
                   (f"i{k}", "play", "groww", "u", "t", f"my SIP was paused number {k}", f"h{k}"))
        db.execute("INSERT INTO filter_results(item_id, prefilter_pass, relevant) VALUES(?,1,1)", (f"i{k}",))
    db.commit()
    seen = []

    def fake_extract(rows, model, batch, on_batch, progress):
        for start in range(0, len(rows), batch):
            chunk = rows[start:start + batch]
            recs = [{"summary": "s", "secondhand": False, **{n: "not_stated" for n in extract.ENUMS}, "sip_action": "paused",
                     "evidence_quotes": ["my SIP was paused"]} for _ in chunk]
            on_batch(start, recs, [])
            seen.append(store.connect(db_path).execute("SELECT COUNT(*) FROM extractions").fetchone()[0])  # visible mid-run

    monkeypatch.setattr(extract, "extract", fake_extract)
    pilot.run("new", str(tmp_path / "state.json"), "m", True, batch=2)
    assert seen == [2, 3]
    assert json.loads((tmp_path / "state.json").read_text())["records"].keys() == {"i0", "i1", "i2"}
