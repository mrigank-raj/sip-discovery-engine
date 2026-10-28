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


def strata(db):
    """{(source, group): [item ids]} over items that pass the keyword filter on their own text. Comments and replies are
    judged without the video or thread title, which keeps this pool valid under either prefilter rule being decided."""
    out = defaultdict(list)
    for r in db.execute("SELECT item_id, source, thread_id, title, text FROM raw_items ORDER BY item_id"):
        title = None if r["source"] == "youtube" or (r["thread_id"] and r["thread_id"] != r["item_id"]) else r["title"]
        if passes(r["source"], title, r["text"]):
            hit = groups_hit(title, r["text"])
            out[(r["source"], next(g for g in PRIORITY if g in hit))].append(r["item_id"])
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
