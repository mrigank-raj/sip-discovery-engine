"""Resumable extraction run: a free-tier daily quota can stop it part-way, and running it again continues where it stopped."""
import json
from pathlib import Path

from engine import extract, llm, store

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "engine.db"


def rows_for(db, ids):
    q = ",".join("?" * len(ids))
    by_id = {r["item_id"]: r for r in db.execute(
        f"SELECT item_id, source, product, title, text, thread_id FROM raw_items WHERE item_id IN ({q})", ids)}
    return extract.with_starters(db, [by_id[i] for i in ids])


def run(pool, out, model, save_db, batch=8, ids=None):
    """pool 'new' = relevant items not yet extracted; pass `ids` to extract a fixed list (the golden set)."""
    db = store.connect(DB_PATH)
    ids = ids if ids is not None else extract.new_pool(db)
    tax_version = extract.taxonomy()["version"]
    path = Path(out)
    state = {"model": model, "taxonomy": tax_version, "records": {}, "review": []}
    if path.exists():
        prior = json.loads(path.read_text(encoding="utf8"))
        if (prior["model"], prior["taxonomy"]) != (model, tax_version):
            raise SystemExit(f"{path.name} was made with {prior['model']}/{prior['taxonomy']}; use a new --out file")
        state = prior
    done = set(state["records"]) | {r[0] for r in state["review"]}
    rows = rows_for(db, [i for i in ids if i not in done]) if len(done) < len(ids) else []
    print(f"{len(ids)} items in the {pool} pool; {len(done)} already done; extracting {len(rows)} with {model}")
    path.parent.mkdir(parents=True, exist_ok=True)

    def flush():
        state["usage"] = llm.usage
        path.write_text(json.dumps(state, indent=1, ensure_ascii=False), encoding="utf8")

    def on_batch(start, recs, review):
        for r, rec in zip(rows[start:start + len(recs)], recs):
            if rec:
                state["records"][r["item_id"]] = rec
        state["review"] += [[rows[i]["item_id"], why] for i, why in review if [rows[i]["item_id"], why] not in state["review"]]
        flush()

    stopped = None
    try:
        extract.extract(rows, model, batch=batch, on_batch=on_batch, progress=lambda d, n: print(f"  {d}/{len(rows)}", flush=True))
    except llm.DailyQuotaExhausted as e:
        stopped = str(e)
    flush()
    if save_db:
        run_id = store.log_run(db, "extract", None, {"model": model, "pool": pool, "batch": batch, **store.versions()},
                               {"saved": len(state["records"]), **llm.usage}, [stopped] if stopped else [], store.now())
        meta = {r["item_id"]: r for r in db.execute("SELECT item_id, source, product FROM raw_items")}
        for item_id, rec in state["records"].items():
            extract.save(db, item_id, rec, model, run_id, tax_version, meta[item_id]["source"], meta[item_id]["product"])
        db.executemany("INSERT INTO needs_review VALUES(?,?,?)", [(i, why, None) for i, why in state["review"]])
        db.commit()
    print(f"valid {len(state['records'])}/{len(ids)}; needs_review {len(state['review'])}; requests {llm.usage['requests']}; "
          f"tokens in {llm.usage['prompt_tokens']} out {llm.usage['output_tokens']}; saved {out}")
    if stopped:
        print(f"STOPPED: daily free quota used ({stopped}). Run the same command again later to resume.")
    return stopped
