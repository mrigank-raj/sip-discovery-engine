"""Write a slim copy of the database for hosting the Explorer (demo/engine.db), check it, and optionally publish it.

Keeps everything the Explorer shows. Post text is kept only for items that were extracted; raw scraper payloads, author
hashes, run logs and review notes are dropped. `check` must pass before anything is pushed: the repository is public.
"""
import os
import sqlite3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEMO_DB = ROOT / "demo" / "engine.db"
PII_FIELDS = ("userName", "authorDisplayName", "authorChannelId", "authorChannelUrl", "author_fullname", "username")
SECRET_ENV = ("GEMINI_API_KEY", "YOUTUBE_API_KEY", "APIFY_TOKEN", "GROQ_API_KEY", "AUTHOR_HASH_SALT")


def export(src, dest=DEMO_DB):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    a, b = sqlite3.connect(src), sqlite3.connect(tmp)
    a.backup(b)  # a consistent copy even while a run is writing to the source
    a.close()
    b.execute("UPDATE raw_items SET text='', title=NULL WHERE item_id NOT IN (SELECT item_id FROM extractions)")
    b.execute("UPDATE raw_items SET raw_json='{}', author_hash=NULL")
    b.execute("DELETE FROM runs")
    b.execute("DELETE FROM needs_review")
    b.commit()
    b.execute("VACUUM")
    b.close()
    problems = check(tmp)
    if problems:
        tmp.unlink()
        raise SystemExit("snapshot NOT written, checks failed: " + "; ".join(problems))
    os.replace(tmp, dest)
    db = sqlite3.connect(dest)
    q = lambda s: db.execute(s).fetchone()[0]  # noqa: E731
    stats = {"items": q("SELECT COUNT(*) FROM raw_items"), "text_kept": q("SELECT COUNT(*) FROM raw_items WHERE text != ''"),
             "classified": q("SELECT COUNT(*) FROM filter_results WHERE relevant IS NOT NULL"),
             "extracted": q("SELECT COUNT(*) FROM extractions")}
    db.close()
    print(f"wrote {dest} ({dest.stat().st_size / 1e6:.1f} MB): {stats}; checks passed")
    return stats


def check(path):
    """Problems that must block publishing: author data, scraper payloads, run logs, text of non-extracted items, or any
    secret from .env appearing anywhere in the file. Returns a list (empty means safe to publish)."""
    db = sqlite3.connect(path)
    q = lambda s: db.execute(s).fetchone()[0]  # noqa: E731
    problems = []
    if q("SELECT COUNT(*) FROM raw_items WHERE author_hash IS NOT NULL"):
        problems.append("author hashes present")
    if q("SELECT COUNT(*) FROM raw_items WHERE raw_json != '{}'"):
        problems.append("raw scraper payloads present")
    if q("SELECT COUNT(*) FROM runs") or q("SELECT COUNT(*) FROM needs_review"):
        problems.append("run logs or review notes present")
    if q("SELECT COUNT(*) FROM raw_items WHERE text != '' AND item_id NOT IN (SELECT item_id FROM extractions)"):
        problems.append("text kept for items that were not extracted")
    dump = "\n".join(db.iterdump())
    db.close()
    problems += [f"field name {f!r} found" for f in PII_FIELDS if f in dump]
    from dotenv import dotenv_values
    secrets = [v for k, v in dotenv_values(ROOT / ".env").items() if k in SECRET_ENV and v and len(v) >= 8]
    problems += [f"a value from .env found" for s in secrets if s in dump]
    return problems


def publish(src, message=None):
    """Export, check, then commit and push the snapshot and the eval results it is shown with."""
    stats = export(src)
    paths = ["demo/engine.db", "eval/results"]
    subprocess.run(["git", "add", *paths], cwd=ROOT, check=True)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0:
        print("nothing changed; not pushed")
        return stats
    msg = message or (f"Hosted snapshot: {stats['extracted']} extracted, {stats['classified']} classified\n\n"
                      "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    subprocess.run(["git", "-c", "user.name=Mrigank Raj Chouhan", "-c", "user.email=mrigankrajchouhan@gmail.com",
                    "commit", "-q", "-m", msg, "--", *paths], cwd=ROOT, check=True)  # only these paths, never other staged work
    subprocess.run(["git", "push", "-q", "origin", "main"], cwd=ROOT, check=True)
    print("pushed")
    return stats


def publish_loop(src, every=500, poll=120, done_marker=ROOT / "data" / "step3_extract_v3.log"):
    """Publish a fresh snapshot each time `every` more items have been extracted, and once more when the extraction log
    shows the run has ended (finished or stopped for the day)."""
    import time
    last = sqlite3.connect(src).execute("SELECT COUNT(*) FROM extractions").fetchone()[0]
    print(f"watching: {last} extracted now; publishing every +{every}", flush=True)
    while True:
        n = sqlite3.connect(src).execute("SELECT COUNT(*) FROM extractions").fetchone()[0]
        ended = done_marker.exists() and any(line.startswith(("valid ", "STOPPED")) for line in done_marker.read_text(encoding="utf8").splitlines())
        if n >= last + every or (ended and n > last):
            publish(src)
            last = n
        if ended:
            print(f"extraction run ended at {n} extracted; last snapshot published", flush=True)
            return
        time.sleep(poll)
