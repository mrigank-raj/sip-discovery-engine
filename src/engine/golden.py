"""Golden set: a hand-labelled sample picked before any model has run, so the labels are blind.

Items are stratified by source and by which prefilter term group matched. No relevance or extraction output is read when
picking, and every label column is written blank.
"""
import csv
import random
from collections import defaultdict
from pathlib import Path

from engine import store
from engine.prefilter import groups_hit, own_title, passes

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
    title = own_title(r["source"], r["item_id"], r["thread_id"], r["title"])
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
    """One item per stratum per pass, drawing from seeded shuffles. Within a pass the order is group position outer, source
    inner, so a partial last pass spreads its items across sources instead of giving them all to the first one. Deterministic,
    so a top-up continues the same order."""
    rnd = random.Random(seed)
    order = {k: rnd.sample(v, len(v)) for k, v in sorted(pools.items())}
    by_source = defaultdict(list)
    for src, grp in order:
        by_source[src].append((src, grp))
    width = max(len(v) for v in by_source.values())
    keys = [by_source[s][j] for j in range(width) for s in sorted(by_source) if j < len(by_source[s])]
    chosen, depth = [], 0
    while len(chosen) < n and any(len(v) > depth for v in order.values()):
        for key in keys:
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


def _quote_block(text):
    return "\n".join("> " + line if line.strip() else ">" for line in text.strip().splitlines())


def label_views():
    """Readable, paste-friendly copies of the two labelling sheets for labelling in a chat. They hold only the item text and
    its context (row number, source, title): no engine output, no ids, no prefilter result."""
    ev = ROOT / "eval"
    pre = list(csv.DictReader(open(ev / "prefilter_dropped_sample.csv", encoding="utf-8-sig")))
    L = ["# Prefilter check: 40 YouTube comments the text-only rule drops", "",
         "For each: is this a person's own SIP experience? (y/n)", ""]
    for k, r in enumerate(pre, 1):
        L += [f"## {k}", "", f"Video title: {r['video_title']}", "", _quote_block(r["comment_text"]), ""]
    (ev / "label_view_prefilter_sample.md").write_text("\n".join(L), encoding="utf8")
    gold = list(csv.DictReader(open(SHEET, encoding="utf-8-sig")))
    L = ["# Golden set: items to label", "",
         "Fill: is_relevant, sip_action, action_reason, journey_stage, investor_experience, belief_at_action, belief_quote. "
         "For no belief, write null.", ""]
    for k, r in enumerate(gold, 1):
        L += [f"## {k}", "", f"Source: {r['source']}"] + ([f"Title: {r['title']}"] if r["title"].strip() else []) + \
             ["", _quote_block(r["text"]), ""]
    (ev / "label_view_golden.md").write_text("\n".join(L), encoding="utf8")
    print(f"wrote eval/label_view_prefilter_sample.md ({len(pre)} items) and eval/label_view_golden.md ({len(gold)} items)")


# ---- scoring -------------------------------------------------------------------------------------------------------------
ENUM_FIELDS = ["investor_experience", "platform", "journey_stage", "sip_action", "action_reason", "what_they_check", "check_frequency",
               "outside_app_behaviour", "emotion", "life_stage", "income_type", "source_of_money", "influenced_by", "severity"]
# A sip_action label may be one of these groups instead of a single value; the engine's value is then compared as its group.
SIP_GROUPS = {"staying_in": {"started", "continuing", "increased"},
              "pulling_back": {"considering_stopping", "paused", "reduced", "stopped"},
              "out_or_failed": {"instalment_failed", "redeemed", "switched_platform"}}
PRESENCE_FIELDS =["expectation_at_start", "belief_at_action", "age_stated"]  # scored as stated vs null; wording is not compared
YES, NO = {"y", "yes", "1", "true", "t"}, {"n", "no", "0", "false", "f"}
EMPTY = {"", "null", "none", "-"}


def _bool(v):
    v = (v or "").strip().lower()
    return True if v in YES else False if v in NO else None


def _present(v):
    return (v or "").strip().lower() not in EMPTY


def compare(gold, engine, relevance_only=False):
    """gold: dicts with item_id, source, group, text and the label columns. engine: {item_id: {"relevant": bool or None,
    "rec": extraction dict or None}}. Relevance is scored on every labelled item; extraction fields only on items the person
    marked relevant (never with relevance_only). Blank enum cells are treated as not labelled. Returns (cells, disagreements)."""
    cells, dis = [], []

    def add(g, field, mine, theirs):
        cells.append({"field": field, "source": g["source"], "group": g["group"], "agree": mine == theirs,
                      "mine": mine, "engine": theirs})
        if mine != theirs:
            dis.append({"item_id": g["item_id"], "source": g["source"], "group": g["group"], "field": field,
                        "mine": mine, "engine": theirs, "text": g["text"]})

    for g in gold:
        e = engine.get(g["item_id"], {})
        mine = _bool(g.get("is_relevant"))
        if mine is None:
            continue
        add(g, "is_relevant", mine, e.get("relevant"))
        if not mine or relevance_only:
            continue
        rec = e.get("rec")
        if _bool(g.get("secondhand")) is not None:
            add(g, "secondhand", _bool(g["secondhand"]), None if rec is None else bool(rec["secondhand"]))
        for f in ENUM_FIELDS:
            if (g.get(f) or "").strip():
                mine_f, theirs_f = g[f].strip().lower(), "(not extracted)" if rec is None else rec[f]
                if f == "sip_action" and mine_f in SIP_GROUPS:  # labelled at group level: compare the engine's group
                    theirs_f = next((k for k, v in SIP_GROUPS.items() if theirs_f in v), theirs_f)
                add(g, f, mine_f, theirs_f)
        for f in PRESENCE_FIELDS:  # blank = not labelled; "null" (or none, -) = labelled as not stated
            if not (g.get(f) or "").strip():
                continue
            add(g, f, "stated" if _present(g.get(f)) else "null",
                "(not extracted)" if rec is None else "stated" if rec.get(f) else "null")
    return cells, dis


NULLISH = {"not_stated", "unknown", "none_stated", "unclear", "null"}  # the "text does not say" value of each field
NOT_RUN = "(not extracted)"
MIN_STATED = 3


def rates(cells, by=None):
    """{field: {key: (agree, n)}} where key is 'overall' or the value of `by` (source or group)."""
    out = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for c in cells:
        k = "overall" if by is None else c[by]
        out[c["field"]][k][0] += c["agree"]
        out[c["field"]][k][1] += 1
    return {f: {k: tuple(v) for k, v in d.items()} for f, d in out.items()}


def split_rates(cells, by=None):
    """Two rates that a pile of agreeing not_stated labels cannot inflate, per field and key:
    - stated: agreement on items where the person labelled a real value (not not_stated / unknown / null);
    - false_stated: items the person labelled not_stated where the engine filled a value (a possible hallucination).
    Both are (count, n). Boolean fields (is_relevant, secondhand) have no not_stated value and are left out."""
    stated = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    false = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for c in cells:
        if isinstance(c["mine"], bool):
            continue
        k = "overall" if by is None else c[by]
        if c["mine"] in NULLISH:
            false[c["field"]][k][1] += 1
            false[c["field"]][k][0] += c["engine"] not in NULLISH and c["engine"] != NOT_RUN
        else:
            stated[c["field"]][k][1] += 1
            stated[c["field"]][k][0] += c["agree"]
    freeze = lambda d: {f: {k: tuple(v) for k, v in x.items()} for f, x in d.items()}  # noqa: E731
    return {"stated": freeze(stated), "false_stated": freeze(false)}


def pct(t, min_n=1):
    """'67% (2/3)'; 'too few to score (n=2)' below min_n; '-' when there is nothing to score."""
    a, n = t
    if not n:
        return "-"
    return f"too few to score (n={n})" if n < min_n else f"{100 * a / n:.0f}% ({a}/{n})"


def _engine(db, ids):
    q = ",".join("?" * len(ids))
    rel = {r["item_id"]: None if r["relevant"] is None else bool(r["relevant"])
           for r in db.execute(f"SELECT item_id, relevant FROM filter_results WHERE item_id IN ({q})", ids)}
    import json
    recs = {r["item_id"]: json.loads(r["json"]) for r in db.execute(f"SELECT item_id, json FROM extractions WHERE item_id IN ({q})", ids)}
    return {i: {"relevant": rel.get(i), "rec": recs.get(i)} for i in ids}


def relevance_report(db, gold, engine, dis):
    """Every golden item's relevance with the engine's family, language and confidence, and each disagreement in full."""
    q = ",".join("?" * len(gold))
    fam = {r["item_id"]: r for r in db.execute(f"SELECT item_id, problem_family, whose_holdings, language, confidence FROM filter_results "
                                               f"WHERE item_id IN ({q})", [g["item_id"] for g in gold])}
    yn = {True: "yes", False: "no", None: "not classified"}
    L = ["## Relevance, item by item", "", "| # | source | group | you | engine | engine family | whose | language | confidence |",
         "|---|---|---|---|---|---|---|---|---|"]
    for k, g in enumerate(gold, 1):
        f = fam.get(g["item_id"]) or {}
        mine, theirs = _bool(g.get("is_relevant")), engine[g["item_id"]]["relevant"]
        L.append(f"| G{k}{'' if mine == theirs else ' **x**'} | {g['source']} | {g['group']} | {yn[mine]} | {yn[theirs]} | "
                 f"{f['problem_family'] if f else '-'} | {(f['whose_holdings'] or '-') if f else '-'} | {f['language'] if f else '-'} | {f['confidence'] if f else '-'} |")
    row = {g["item_id"]: k for k, g in enumerate(gold, 1)}
    L += ["", "## Relevance disagreements", ""]
    for d in [d for d in dis if d["field"] == "is_relevant"]:
        f = fam.get(d["item_id"]) or {}
        L += [f"### G{row[d['item_id']]} ({d['source']}, {d['group']}): you {yn[d['mine']]}, engine {yn[d['engine']]} "
              f"as `{f['problem_family'] if f else '-'}` ({f['confidence'] if f else '-'} confidence)", "",
              _quote_block(d["text"]), ""]
    return L


def score(spot_checks=10, relevance_only=False):
    """Compare the engine with the hand labels in eval/golden_set.csv; print rates overall, per source and per prefilter group,
    and write every disagreement plus a post-scoring summary spot-check to eval/results/golden_score.md and .json.
    relevance_only=True scores and reports relevance alone (used before extraction has run)."""
    import json
    db = store.connect(ROOT / "data" / "engine.db")
    rows = list(csv.DictReader(open(SHEET, encoding="utf-8-sig")))
    meta = {r["item_id"]: r for r in db.execute(f"SELECT item_id, source, thread_id, title, text FROM raw_items WHERE item_id IN "
                                                 f"({','.join('?' * len(rows))})", [r["item_id"] for r in rows])}
    gold = [{**r, "group": stratum(meta[r["item_id"]]), "text": meta[r["item_id"]]["text"]} for r in rows]
    labelled = [g for g in gold if _bool(g.get("is_relevant")) is not None]
    engine = _engine(db, [g["item_id"] for g in gold])
    cells, dis = compare(gold, engine, relevance_only)
    if relevance_only:
        o, s, gr = rates(cells)["is_relevant"], rates(cells, "source")["is_relevant"], rates(cells, "group")["is_relevant"]
        tp = sum(c["mine"] and c["engine"] for c in cells)
        fp = sum(not c["mine"] and c["engine"] for c in cells)
        fn = sum(c["mine"] and not c["engine"] for c in cells)
        L = ["# Golden set: relevance only", "",
             "Stratified for coverage, not proportional to volume; 20 items, so every rate rests on very few items.", "",
             f"- Agreement: {pct(o['overall'])}",
             f"- Engine said relevant and you agreed (precision): {pct((tp, tp + fp))}",
             f"- You said relevant and the engine agreed (recall): {pct((tp, tp + fn))}",
             "- By source: " + "; ".join(f"{k} {pct(v)}" for k, v in sorted(s.items())),
             "- By prefilter group: " + "; ".join(f"{k} {pct(gr.get(k, (0, 0)))}" for k in PRIORITY), ""]
        L += relevance_report(db, gold, engine, dis)
        out = ROOT / "eval" / "results"
        out.mkdir(parents=True, exist_ok=True)
        (out / "golden_relevance.md").write_text("\n".join(L) + "\n", encoding="utf8")
        print("\n".join(L))
        return
    overall, by_src, by_grp = rates(cells), rates(cells, "source"), rates(cells, "group")
    split = {k: split_rates(cells, by) for k, by in (("overall", None), ("source", "source"), ("group", "group"))}
    sources = sorted({c["source"] for c in cells})
    fields = ["is_relevant", "secondhand", *ENUM_FIELDS, *PRESENCE_FIELDS]

    def table(get, min_n):
        """One row per field: overall, then each source, then each prefilter group."""
        rows = ["| field | overall | " + " | ".join(sources) + " | " + " | ".join(PRIORITY) + " |",
                "|---" * (2 + len(sources) + len(PRIORITY)) + "|"]
        for f in fields:
            o = get("overall", f, "overall")
            if o is None:
                continue
            rows.append(f"| {f} | {pct(o, min_n)} | " + " | ".join(pct(get("source", f, s) or (0, 0), min_n) for s in sources)
                        + " | " + " | ".join(pct(get("group", f, g) or (0, 0), min_n) for g in PRIORITY) + " |")
        return rows

    plain = {"overall": overall, "source": by_src, "group": by_grp}
    L = ["# Golden-set agreement", "",
         f"{len(labelled)} of {len(gold)} items labelled; {sum(_bool(g['is_relevant']) for g in labelled)} marked relevant. "
         "The set is stratified by source and prefilter group for coverage, not proportional to volume, so the overall rate is "
         "not a corpus-wide accuracy. Extraction fields are scored only on items marked relevant; blank cells are not scored.", "",
         "## False-stated rate (read this first)", "",
         "Items you labelled not stated (not_stated, unknown, none_stated, unclear, null) where the engine filled a value: possible "
         "hallucination. Lower is better. Shown as count of your not-stated labels.", ""]
    L += table(lambda k, f, key: split[k]["false_stated"].get(f, {}).get(key), 1)
    L += ["", f"## Stated-only agreement", "",
          f"Items where you labelled a real value. Fewer than {MIN_STATED} such labels shows 'too few to score'.", ""]
    L += table(lambda k, f, key: split[k]["stated"].get(f, {}).get(key), MIN_STATED)
    L += ["", "## Overall agreement (inflated by agreeing not-stated labels; read with the two tables above)", ""]
    L += table(lambda k, f, key: plain[k].get(f, {}).get(key), 1)
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
                                                       "by_group": by_grp, "split": split, "disagreements": dis},
                                                      indent=1, ensure_ascii=False), encoding="utf8")
    print("\n".join(L[:L.index("## Beliefs: stated vs null") + 4]))
    print(f"\n{len(dis)} disagreements listed in eval/results/golden_score.md")
