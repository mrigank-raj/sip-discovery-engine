"""AI Evidence Log: docs/evidence_log.md, built from the database and the eval files only (nothing typed in by hand here).

Sections: sources and volume per stage, models and prompt versions, extraction quality (validator rejections and review),
golden-set agreement with failure examples, the corrections log, and known biases.
"""
import json
from pathlib import Path

import yaml

from engine import cluster, store

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "evidence_log.md"


def _table(rows, cols):
    return ["| " + " | ".join(cols) + " |", "|---" * len(cols) + "|"] + ["| " + " | ".join(str(r.get(c, "")) for c in cols) + " |" for r in rows]


def write(db_path=None):
    db = store.connect(db_path or cluster.DB_PATH)
    L = ["# AI Evidence Log", "", f"Generated {store.now()} by `engine.cli evidence-log`. Every number below is read from the database "
         "or the eval files at that time. Counts are mentions in a sample of public posts, not population rates.", ""]

    f = cluster.funnel(db)
    tot = {k: sum(r[k] or 0 for r in f) for k in ("collected", "prefiltered", "classified", "relevant", "extracted")}
    L += ["## 1. Sources and volume per stage", ""] + _table(f + [{"source": "**total**", **tot}],
                                                             ["source", "collected", "prefiltered", "classified", "relevant", "extracted"])
    rate = f"{100 * tot['relevant'] / tot['classified']:.0f}%" if tot["classified"] else "n/a"
    L += ["", f"Relevance rate among classified items: {rate} ({tot['relevant']} of {tot['classified']}). "
          f"Classified so far: {tot['classified']} of {tot['prefiltered']} prefiltered; extracted {tot['extracted']} of {tot['relevant']} relevant.", ""]
    src = yaml.safe_load((ROOT / "config" / "sources.yaml").read_text(encoding="utf8"))["sources"]
    L += ["Collection method and compliance per source (from config/sources.yaml):", ""]
    L += [f"- **{k}** ({'on' if v.get('enabled') else 'off'}): {v.get('tool') or v.get('reason', '')}" +
          (f" Compliance: {v['compliance']}" if v.get("compliance") else "") for k, v in src.items()]

    llm_cfg = yaml.safe_load((ROOT / "config" / "llm.yaml").read_text(encoding="utf8"))
    m = llm_cfg["providers"]["gemini"]["models"]
    L += ["", "## 2. Models and prompt versions", "",
          f"- Relevance: `{m['relevance']}`; extraction: `{m['extraction']}`; insight wording: `{m['extraction_strong']}` "
          f"(fallback `{m['relevance']}`). Budget: ${llm_cfg['budget_usd']}, free tier only.",
          f"- Current versions: `{json.dumps(store.versions())}`", "", "Model-backed runs recorded in the `runs` table:", ""]
    runs = [dict(r) for r in db.execute("SELECT stage, started_at, params_json, counts_json FROM runs WHERE stage IN "
                                        "('relevance','extract','cluster') ORDER BY started_at")]
    rows = []
    for r in runs:
        p = json.loads(r["params_json"] or "{}")
        rows.append({"stage": r["stage"], "started": r["started_at"][:16], "model": p.get("model", ""),
                     "taxonomy": p.get("taxonomy", ""), "relevance prompt": p.get("prompt_relevance_version") or p.get("prompt_relevance_sha", ""),
                     "extraction prompt sha": p.get("prompt_extraction_sha", ""), "counts": (r["counts_json"] or "")[:90]})
    L += _table(rows, ["stage", "started", "model", "taxonomy", "relevance prompt", "extraction prompt sha", "counts"])

    ext = db.execute("SELECT COUNT(*) FROM extractions").fetchone()[0]
    rev = db.execute("SELECT COUNT(DISTINCT item_id) FROM needs_review").fetchone()[0]
    reasons = db.execute("SELECT reason FROM needs_review LIMIT 5").fetchall()
    beliefs = db.execute("SELECT COUNT(*) FROM extractions WHERE has_belief=1").fetchone()[0]
    L += ["", "## 3. Extraction quality: validator rejections and review", "",
          "Every quote is checked to appear word for word in the text of the item it is attached to (NFC, zero-width characters "
          "removed, smart quotes made plain, whitespace collapsed). A record that fails is retried once, alone, with the error; if "
          "it fails again it goes to `needs_review` and is not used.", "",
          f"- Extracted and valid: {ext}; sent to review after the retry: {rev}"
          + (f" ({100 * rev / (ext + rev):.1f}% of attempted)" if ext + rev else ""),
          f"- Items with a stated belief (candidate, not finding): {beliefs} of {ext}"
          + (f"; null rate {100 * (ext - beliefs) / ext:.0f}%" if ext else "")]
    L += [f"  - review reason example: {r['reason'][:200]}" for r in reasons]

    L += ["", "## 4. Golden set", ""]
    for name in ("golden_relevance.md", "golden_score.md"):
        p = ROOT / "eval" / "results" / name
        if p.exists():
            L += [f"From `eval/results/{name}`:", "", p.read_text(encoding="utf8").replace("\n# ", "\n### ").replace("\n## ", "\n#### "), ""]
    L += ["## 5. Corrections log", "", (ROOT / "eval" / "corrections.md").read_text(encoding="utf8").replace("\n## ", "\n### ")
          .replace("# Corrections log", ""), "",
          "## 6. Known biases and limitations", "", (ROOT / "eval" / "evidence_notes.md").read_text(encoding="utf8")
          .replace("# Known biases and limitations", "")]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(L) + "\n", encoding="utf8")
    print(f"wrote {OUT} ({len(L)} lines)")
