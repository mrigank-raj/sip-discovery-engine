"""Golden set: a hand-labelled sample picked before any model has run, so the labels are blind.

Items are stratified by source and by which prefilter term group matched. No relevance or extraction output is read when
picking, and every label column is written blank.
"""
import csv
import random
from collections import defaultdict
from pathlib import Path

from engine import store
from engine.prefilter import groups_hit, passes

ROOT = Path(__file__).resolve().parents[2]
SHEET = ROOT / "eval" / "golden_set.csv"
SEED = 20261029
PRIORITY = ["stop_or_fail", "returns", "sip_or_mf"]  # an item's stratum is its first matching group in this order
# One column per extraction field (summary is model-only and confidence is a model self-rating, so neither is labelled).
LABELS = ["is_relevant", "secondhand", "investor_experience", "platform", "journey_stage", "sip_action", "action_reason",
          "expectation_at_start", "belief_at_action", "belief_quote", "what_they_check", "check_frequency", "outside_app_behaviour",
          "emotion", "life_stage", "age_stated", "income_type", "source_of_money", "influenced_by", "severity", "evidence_quotes"]
HEAD = ["item_id", "source", "app", "title", "text", "url"]


def stratum(r):
    """The prefilter group an item is stratified on, or None if it does not pass on its own text. Comments and replies are
    judged without the video or thread title, which keeps the pool valid under either prefilter rule being decided."""
    title = None if r["source"] == "youtube" or (r["thread_id"] and r["thread_id"] != r["item_id"]) else r["title"]
    if not passes(r["source"], title, r["text"]):
        return None
    hit = groups_hit(title, r["text"])
    return next(g for g in PRIORITY if g in hit)


def strata(db):
    """{(source, group): [item ids]} over items that pass the keyword filter on their own text."""
    out = defaultdict(list)
    for r in db.execute("SELECT item_id, source, thread_id, title, text FROM raw_items ORDER BY item_id"):
        g = stratum(r)
        if g:
            out[(r["source"], g)].append(r["item_id"])
    return out


def pick(pools, n, exclude=(), seed=SEED):
    """Round robin over sources, then over each source's groups, drawing from seeded shuffles. Deterministic, so a top-up
    with a larger n continues the same order."""
    rnd = random.Random(seed)
    order = {k: rnd.sample(v, len(v)) for k, v in sorted(pools.items())}
    by_source = defaultdict(list)
    for src, grp in order:
        by_source[src].append((src, grp))
    chosen, depth = [], 0
    while len(chosen) < n and any(len(v) > depth for v in order.values()):
        for src in sorted(by_source):
            for key in by_source[src]:
                ids = [i for i in order[key] if i not in exclude and i not in chosen]
                if len(order[key]) > depth and ids and len(chosen) < n:
                    chosen.append(ids[0])
        depth += 1
    return chosen


def make_sheet(n=35, add=0):
    """Write eval/golden_set.csv with n items, or with `add` more items appended to the existing sheet (labels kept)."""
    db = store.connect(ROOT / "data" / "engine.db")
    pools = strata(db)
    existing = list(csv.DictReader(open(SHEET, encoding="utf-8-sig"))) if add and SHEET.exists() else []
    have = {r["item_id"] for r in existing}
    ids = pick(pools, add, exclude=have) if add else pick(pools, n)
    rows = {r["item_id"]: r for r in db.execute(f"SELECT item_id, source, product, title, text, url FROM raw_items WHERE item_id IN "
                                                 f"({','.join('?' * len(ids))})", ids)}
    with open(SHEET, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(HEAD + LABELS + ["notes"])
        for r in existing:
            w.writerow([r[c] for c in HEAD + LABELS + ["notes"]])
        for i in ids:
            r = rows[i]
            w.writerow([i, r["source"], r["product"] or "", r["title"] or "", r["text"], r["url"]] + [""] * (len(LABELS) + 1))
    counts = defaultdict(int)
    for i in ids:
        counts[next(k for k, v in pools.items() if i in v)] += 1
    print(f"{'appended' if add else 'wrote'} {len(ids)} items to {SHEET.name} (seed {SEED}); pool sizes and picks:")
    for k in sorted(pools):
        print(f"  {k[0]:<11}{k[1]:<13} pool {len(pools[k]):>5}  picked {counts[k]}")


# ---- scoring -------------------------------------------------------------------------------------------------------------
ENUM_FIELDS = ["investor_experience", "platform", "journey_stage", "sip_action", "action_reason", "what_they_check", "check_frequency",
               "outside_app_behaviour", "emotion", "life_stage", "income_type", "source_of_money", "influenced_by", "severity"]
PRESENCE_FIELDS = ["expectation_at_start", "belief_at_action", "age_stated"]  # scored as stated vs null; wording is not compared
YES, NO = {"y", "yes", "1", "true", "t"}, {"n", "no", "0", "false", "f"}
EMPTY = {"", "null", "none", "-"}


def _bool(v):
    v = (v or "").strip().lower()
    return True if v in YES else False if v in NO else None


def _present(v):
    return (v or "").strip().lower() not in EMPTY


def compare(gold, engine):
    """gold: dicts with item_id, source, group, text and the label columns. engine: {item_id: {"relevant": bool or None,
    "rec": extraction dict or None}}. Relevance is scored on every labelled item; extraction fields only on items the person
    marked relevant. Blank enum cells are treated as not labelled. Returns (cells, disagreements)."""
    cells, dis = [], []

    def add(g, field, mine, theirs):
        cells.append({"field": field, "source": g["source"], "group": g["group"], "agree": mine == theirs})
        if mine != theirs:
            dis.append({"item_id": g["item_id"], "source": g["source"], "group": g["group"], "field": field,
                        "mine": mine, "engine": theirs, "text": g["text"]})

    for g in gold:
        e = engine.get(g["item_id"], {})
        mine = _bool(g.get("is_relevant"))
        if mine is None:
            continue
        add(g, "is_relevant", mine, e.get("relevant"))
        if not mine:
            continue
        rec = e.get("rec")
        if _bool(g.get("secondhand")) is not None:
            add(g, "secondhand", _bool(g["secondhand"]), None if rec is None else bool(rec["secondhand"]))
        for f in ENUM_FIELDS:
            if (g.get(f) or "").strip():
                add(g, f, g[f].strip().lower(), "(not extracted)" if rec is None else rec[f])
        for f in PRESENCE_FIELDS:
            add(g, f, "stated" if _present(g.get(f)) else "null",
                "(not extracted)" if rec is None else "stated" if rec.get(f) else "null")
    return cells, dis


def rates(cells, by=None):
    """{field: {key: (agree, n)}} where key is 'overall' or the value of `by` (source or group)."""
    out = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for c in cells:
        k = "overall" if by is None else c[by]
        out[c["field"]][k][0] += c["agree"]
        out[c["field"]][k][1] += 1
    return {f: {k: tuple(v) for k, v in d.items()} for f, d in out.items()}


def _engine(db, ids):
    q = ",".join("?" * len(ids))
    rel = {r["item_id"]: None if r["relevant"] is None else bool(r["relevant"])
           for r in db.execute(f"SELECT item_id, relevant FROM filter_results WHERE item_id IN ({q})", ids)}
    import json
    recs = {r["item_id"]: json.loads(r["json"]) for r in db.execute(f"SELECT item_id, json FROM extractions WHERE item_id IN ({q})", ids)}
    return {i: {"relevant": rel.get(i), "rec": recs.get(i)} for i in ids}


def score(spot_checks=10):
    """Compare the engine with the hand labels in eval/golden_set.csv; print rates overall, per source and per prefilter group,
    and write every disagreement plus a post-scoring summary spot-check to eval/results/golden_score.md and .json."""
    import json
    db = store.connect(ROOT / "data" / "engine.db")
    rows = list(csv.DictReader(open(SHEET, encoding="utf-8-sig")))
    meta = {r["item_id"]: r for r in db.execute(f"SELECT item_id, source, thread_id, title, text FROM raw_items WHERE item_id IN "
                                                 f"({','.join('?' * len(rows))})", [r["item_id"] for r in rows])}
    gold = [{**r, "group": stratum(meta[r["item_id"]]), "text": meta[r["item_id"]]["text"]} for r in rows]
    labelled = [g for g in gold if _bool(g.get("is_relevant")) is not None]
    engine = _engine(db, [g["item_id"] for g in gold])
    cells, dis = compare(gold, engine)
    overall, by_src, by_grp = rates(cells), rates(cells, "source"), rates(cells, "group")
    fmt = lambda t: f"{100 * t[0] / t[1]:.0f}% ({t[0]}/{t[1]})" if t[1] else "-"  # noqa: E731
    L = ["# Golden-set agreement", "",
         f"{len(labelled)} of {len(gold)} items labelled; {sum(_bool(g['is_relevant']) for g in labelled)} marked relevant. "
         "The set is stratified by source and prefilter group for coverage, not proportional to volume, so the overall rate is "
         "not a corpus-wide accuracy. Extraction fields are scored only on items marked relevant; blank cells are not scored.", "",
         "| field | overall | " + " | ".join(sorted({c["source"] for c in cells})) + " | " + " | ".join(PRIORITY) + " |",
         "|---" * (2 + len({c["source"] for c in cells}) + len(PRIORITY)) + "|"]
    for f in ["is_relevant", "secondhand", *ENUM_FIELDS, *PRESENCE_FIELDS]:
        if f in overall:
            L.append(f"| {f} | {fmt(overall[f]['overall'])} | " + " | ".join(fmt(by_src[f].get(s, (0, 0))) for s in sorted({c['source'] for c in cells}))
                     + " | " + " | ".join(fmt(by_grp[f].get(g, (0, 0))) for g in PRIORITY) + " |")
    bel = [d for d in dis if d["field"] == "belief_at_action"]
    L += ["", "## Beliefs: stated vs null", "",
          f"- Engine found a belief you did not: {sum(d['engine'] == 'stated' for d in bel)}",
          f"- You found a belief the engine did not: {sum(d['mine'] == 'stated' for d in bel)}", ""]
    for d in bel:
        rec = engine[d["item_id"]]["rec"] or {}
        L.append(f"- `{d['item_id']}` you: {d['mine']}, engine: {d['engine']} {('- engine quote: ' + repr(rec.get('belief_quote'))) if rec.get('belief_quote') else ''}\n  > {d['text'][:400]}")
    L += ["", "## Every disagreement", ""]
    for d in dis:
        L.append(f"- `{d['item_id']}` ({d['source']}, {d['group']}) **{d['field']}**: you `{d['mine']}`, engine `{d['engine']}`\n  > {d['text'][:400]}")
    with_rec = [g for g in labelled if _bool(g["is_relevant"]) and engine[g["item_id"]]["rec"]]
    pick_ = random.Random(SEED).sample(with_rec, min(spot_checks, len(with_rec)))
    L += ["", "## Summary spot-check (shown only after scoring, so labelling stayed blind)", "",
          "Mark each one faithful or not in eval/corrections.md.", ""]
    for g in pick_:
        L.append(f"- `{g['item_id']}` summary: {engine[g['item_id']]['rec']['summary']}\n  > {g['text'][:400]}")
    out = ROOT / "eval" / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "golden_score.md").write_text("\n".join(L) + "\n", encoding="utf8")
    (out / "golden_score.json").write_text(json.dumps({"labelled": len(labelled), "overall": overall, "by_source": by_src,
                                                       "by_group": by_grp, "disagreements": dis}, indent=1, ensure_ascii=False), encoding="utf8")
    print("\n".join(L[:L.index("## Beliefs: stated vs null") + 4]))
    print(f"\n{len(dis)} disagreements listed in eval/results/golden_score.md")
