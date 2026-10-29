"""Group SIP-journey extractions into named clusters within action groups, and measure them in code (not by a model).

Every number here is a count of mentions in a sample of public posts, not a population rate.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from engine import llm, store
from engine.extract import ACTED

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "engine.db"
# Clusters are built inside these groups, so a cluster never mixes people who stayed with people who stopped.
GROUP = {"started": "starting", "continuing": "staying_in", "increased": "staying_in", "considering_stopping": "considering",
         **{a: "pulled_back" for a in ACTED}, "instalment_failed": "instalment_failed", "switched_platform": "switched_platform",
         "not_stated": "no_action_stated"}
STAGES = ["before_start", "first_3_months", "months_4_to_12", "after_12_months"]
SEGMENTS = ["investor_experience", "life_stage", "income_type", "source_of_money", "influenced_by"]
# Opportunity score (shown in the Explorer): weights are a judgment, not a measurement.
WEIGHTS = {"frequency": 0.40, "acted": 0.30, "stage": 0.15, "evidence": 0.15}
MIN_ITEMS, MIN_KNOWN_STAGE = 8, 10


def load(db):
    """Every extracted item with its raw context. Item dicts carry the flattened fields plus the full record as `rec`."""
    rows = db.execute("SELECT e.*, r.source, r.product, r.title, r.text, r.url, r.created_at, r.thread_id FROM extractions e "
                      "JOIN raw_items r USING(item_id)").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["rec"] = json.loads(d.pop("json"))
        d["group"] = GROUP[d["sip_action"]]
        d["thread"] = d["thread_id"] or d["item_id"]
        d["signature"] = d["summary"]  # English, model-written: the local embedding model handles Hinglish poorly
        d["voluntary_acted"] = d["severity"] == "acted" and d["sip_action"] in ACTED
        out.append(d)
    return out


def embed(texts):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2").encode(texts, normalize_embeddings=True, show_progress_bar=False)


def subcluster(vectors, per_cluster=18, min_size=5):
    """Ward agglomerative clustering, about one cluster per `per_cluster` items; tiny clusters merge into the nearest one."""
    n = len(vectors)
    if n < 2 * per_cluster - 6:
        return np.zeros(n, dtype=int)
    from sklearn.cluster import AgglomerativeClustering
    labels = AgglomerativeClustering(n_clusters=max(2, round(n / per_cluster)), linkage="ward").fit_predict(vectors)
    while True:
        counts = Counter(labels)
        small = [c for c, k in counts.items() if k < min_size]
        if not small or len(counts) == 1:
            return labels
        c = small[0]
        centroids = {k: vectors[labels == k].mean(0) for k in counts}
        nearest = max((k for k in counts if k != c), key=lambda k: float(centroids[c] @ centroids[k]))
        labels[labels == c] = nearest


def build(model, name_clusters=True):
    db = store.connect(DB_PATH)
    items = load(db)
    if not items:
        raise SystemExit("no extractions yet")
    vectors = embed([i["signature"] for i in items])
    by_group = defaultdict(list)
    for idx, it in enumerate(items):
        by_group[it["group"]].append(idx)
    clusters = []
    for group, idxs in sorted(by_group.items()):
        labels = subcluster(vectors[idxs])
        for lab in sorted(set(labels)):
            clusters.append({"group": group, "members": [idxs[k] for k in range(len(idxs)) if labels[k] == lab]})
    for cid, c in enumerate(clusters, start=1):
        c["id"], c["name"], c["definition"] = cid, f"{c['group']} #{cid}", ""
    if name_clusters:
        _name(clusters, items, model)
    run_id = store.log_run(db, "cluster", None, {"model": model, "method": "group by sip_action group, then Ward on MiniLM of summary",
                                                  **store.versions()}, {"clusters": len(clusters), "items": len(items)}, [], store.now())
    db.execute("DELETE FROM cluster_items")
    db.execute("DELETE FROM clusters")
    tax = store.versions()["taxonomy"]
    for c in clusters:
        db.execute("INSERT INTO clusters(cluster_id, name, definition, taxonomy_version, run_id, grp) VALUES(?,?,?,?,?,?)",
                   (c["id"], c["name"], c["definition"], tax, run_id, c["group"]))
        db.executemany("INSERT INTO cluster_items VALUES(?,?)", [(c["id"], items[m]["item_id"]) for m in c["members"]])
    db.commit()
    print(f"{len(clusters)} clusters over {len(items)} extracted items")
    for c in clusters:
        print(f"  #{c['id']:<3}{c['group']:<19}n={len(c['members']):<4}{c['name']}")


def _name(clusters, items, model):
    schema = {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
        "cluster": {"type": "INTEGER"}, "name": {"type": "STRING"}, "definition": {"type": "STRING"}},
        "required": ["cluster", "name", "definition"]}}
    for group in sorted({c["group"] for c in clusters}):
        block = []
        for c in [c for c in clusters if c["group"] == group]:
            ex = "\n".join(f"  - {items[m]['summary']} | \"{(items[m]['rec']['evidence_quotes'] or [''])[0][:100]}\""
                           for m in c["members"][:12])
            block.append(f"Cluster {c['id']} ({len(c['members'])} posts):\n{ex}")
        prompt = (f"These clusters group public posts by Indian investors about their SIPs and mutual funds (all in the group '{group}'). "
                  "For each cluster give a plain-language name of at most 6 words and a one-sentence definition precise enough for a "
                  "reader to decide whether a new post belongs. Base them only on the examples, say nothing about causes the examples "
                  "do not state, and make the clusters in this group distinguishable.\n\n" + "\n\n".join(block))
        for a in llm.generate_json(model, prompt, schema):
            c = next((c for c in clusters if c["id"] == a["cluster"]), None)
            if c:
                c["name"], c["definition"] = a["name"], a["definition"]


def _norm01(values):
    lo, hi = min(values), max(values)
    return [0.0 if hi == lo else (v - lo) / (hi - lo) for v in values]


def _share(ms, pred):
    return sum(map(pred, ms)) / len(ms) if ms else 0.0


def describe(ms):
    """Measures for one set of member items (code only)."""
    n = len(ms)
    known = [m["journey_stage"] for m in ms if m["journey_stage"] in STAGES]
    top_stage, top_n = Counter(known).most_common(1)[0] if known else (None, 0)
    return {
        "items": n, "threads": len({m["thread"] for m in ms}), "sources": dict(Counter(m["source"] for m in ms)),
        "platforms": dict(Counter(m["platform"] for m in ms)),
        "acted_share": _share(ms, lambda m: m["voluntary_acted"]),
        "considered_share": _share(ms, lambda m: m["severity"] == "considered"),
        "instalment_failed_share": _share(ms, lambda m: m["sip_action"] == "instalment_failed"),
        "outside_app_share": _share(ms, lambda m: m["outside_app_behaviour"] != "none_stated"),
        "stage_mix": dict(Counter(m["journey_stage"] for m in ms)),
        "known_stage_items": len(known), "top_stage": top_stage,
        "stage_concentration": top_n / len(known) if len(known) >= MIN_KNOWN_STAGE else 0.0,
        "stage_flag": None if len(known) >= MIN_KNOWN_STAGE else f"only {len(known)} items with a known stage (need {MIN_KNOWN_STAGE}); set to 0",
        "segments": {s: dict(Counter(m[s] for m in ms if m[s] != "not_stated")) for s in SEGMENTS},
        "reasons": dict(Counter(m["action_reason"] for m in ms if m["action_reason"] != "not_stated")),
        "beliefs": sum(bool(m["has_belief"]) for m in ms),
    }


def score(rows):
    """Opportunity score over clusters with at least MIN_ITEMS items: 0.40 frequency + 0.30 share acted + 0.15 stage
    concentration + 0.15 evidence strength, each scaled 0 to 1 across the ranked clusters. Frequency is distinct threads;
    evidence strength is the number of distinct sources."""
    ranked = [r for r in rows if r["items"] >= MIN_ITEMS]
    if not ranked:
        return {}
    parts = {"frequency": _norm01([r["threads"] for r in ranked]), "acted": [r["acted_share"] for r in ranked],
             "stage": [r["stage_concentration"] for r in ranked], "evidence": _norm01([len(r["sources"]) for r in ranked])}
    return {r["id"]: {"parts": {p: round(parts[p][k], 2) for p in parts},
                      "score": round(sum(WEIGHTS[p] * parts[p][k] for p in parts), 3)} for k, r in enumerate(ranked)}


def metrics(db, keep=lambda item: True):
    """One row per cluster with its measures, opportunity score with and without Play Store, and quotes with links.
    `keep` filters member items first (the Explorer's Groww-only view), so every measure and score is recomputed on them."""
    items = {i["item_id"]: i for i in load(db) if keep(i)}
    members = defaultdict(list)
    for r in db.execute("SELECT cluster_id, item_id FROM cluster_items"):
        if r["item_id"] in items:
            members[r["cluster_id"]].append(items[r["item_id"]])
    rows, rows_np = [], []
    for c in db.execute("SELECT cluster_id, name, definition, grp FROM clusters ORDER BY cluster_id"):
        ms = members[c["cluster_id"]]
        if not ms:
            continue
        quotes, seen = [], set()
        for m in sorted(ms, key=lambda m: m["confidence"] != "high"):
            q = next((q for q in m["rec"]["evidence_quotes"] if len(q) > 25), None)
            if q and (m["source"] not in seen or len(quotes) < 3) and len(quotes) < 5:
                quotes.append({"item_id": m["item_id"], "source": m["source"], "quote": q, "url": m["url"]})
                seen.add(m["source"])
        base = {"id": c["cluster_id"], "name": c["name"], "definition": c["definition"], "group": c["grp"]}
        rows.append({**base, **describe(ms), "quotes": quotes})
        np_ms = [m for m in ms if m["source"] != "play"]
        if np_ms:
            rows_np.append({**base, **describe(np_ms)})
    with_play, without_play = score(rows), score(rows_np)
    for r in rows:
        s = with_play.get(r["id"])
        r["score"], r["score_parts"] = (s["score"], s["parts"]) if s else (None, None)
        r["score_without_play"] = (without_play.get(r["id"]) or {}).get("score")
    return sorted(rows, key=lambda r: (r["score"] is None, -(r["score"] or 0)))


def below_min(ms):
    small = [m for m in ms if m["score"] is None]
    return {"clusters": len(small), "items": sum(m["items"] for m in small)}


BUCKETS = ["continuers", "considering", "acted", "instalment_failed", "switched_platform"]


def contrast(db):
    """Continuers vs considering vs acted (instalment_failed and switched_platform shown separately) on what they expected,
    how often they check, how they feel, why, and who they are. Shares are within each bucket."""
    items = [i for i in load(db) if i["contrast_bucket"]]
    out = {}
    for b in BUCKETS:
        ms = [i for i in items if i["contrast_bucket"] == b]
        n = len(ms)
        dist = lambda f: {k: v for k, v in Counter(m[f] for m in ms).most_common()}  # noqa: E731
        out[b] = {"items": n, "with_expectation": sum(bool(m["has_expectation"]) for m in ms),
                  "with_belief": sum(bool(m["has_belief"]) for m in ms),
                  "check_frequency": dist("check_frequency"), "what_they_check": dist("what_they_check"), "emotion": dist("emotion"),
                  "action_reason": dist("action_reason"), "journey_stage": dist("journey_stage"),
                  "outside_app_behaviour": dist("outside_app_behaviour"), **{s: dist(s) for s in SEGMENTS}}
    return out


def candidate_beliefs(db, path=ROOT / "analysis" / "candidate_beliefs.csv"):
    """Every stated belief, for grouping by hand. These are candidates to validate in research, not findings."""
    import csv
    rows = [i for i in load(db) if i["has_belief"]]
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "source", "sip_action", "journey_stage", "investor_experience", "belief_at_action", "belief_quote", "link"])
        for i in sorted(rows, key=lambda i: (i["sip_action"], i["item_id"])):
            w.writerow([i["item_id"], i["source"], i["sip_action"], i["journey_stage"], i["investor_experience"],
                        i["rec"]["belief_at_action"], i["rec"]["belief_quote"], i["url"]])
    return len(rows)


def funnel(db):
    return [dict(r) for r in db.execute(
        """SELECT r.source, COUNT(*) collected, SUM(f.prefilter_pass) prefiltered, SUM(f.relevant IS NOT NULL) classified,
           SUM(f.relevant=1) relevant, SUM(e.item_id IS NOT NULL) extracted
           FROM raw_items r JOIN filter_results f USING(item_id) LEFT JOIN extractions e USING(item_id)
           GROUP BY r.source ORDER BY r.source""")]


def report():
    db = store.connect(DB_PATH)
    ms = metrics(db)
    print(f"{'#':<4}{'score':>6}{'no-play':>8} {'name':<38}{'items':>6}{'thr':>5}{'src':>4}{'acted':>7}{'failed':>7}{'stage':>7}")
    for m in ms:
        sc = lambda v: f"{v:.2f}" if v is not None else "n/a"  # noqa: E731
        print(f"{m['id']:<4}{sc(m['score']):>6}{sc(m['score_without_play']):>8} {m['name'][:37]:<38}{m['items']:>6}{m['threads']:>5}"
              f"{len(m['sources']):>4}{m['acted_share']:>7.0%}{m['instalment_failed_share']:>7.0%}{m['stage_concentration']:>7.0%}")
    small = below_min(ms)
    print(f"\nclusters below n={MIN_ITEMS} (not ranked): {small['clusters']}, holding {small['items']} items")
    print("candidate beliefs exported:", candidate_beliefs(db))
    out = ROOT / "eval" / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "clusters.json").write_text(json.dumps({"weights": WEIGHTS, "min_items": MIN_ITEMS, "below_min": small, "clusters": ms,
                                                   "contrast": contrast(db)}, indent=1, ensure_ascii=False), encoding="utf8")


ASSIGN_MIN_SIM = 0.35


def _unit(v):
    return v / (np.linalg.norm(v) or 1.0)


def assign_new(db, embed_fn=embed, min_sim=ASSIGN_MIN_SIM):
    """Put extracted items that have no cluster into the nearest existing cluster of the same action group."""
    items = load(db)
    assigned = {r["item_id"]: r["cluster_id"] for r in db.execute("SELECT item_id, cluster_id FROM cluster_items")}
    group_of = {r["cluster_id"]: r["grp"] for r in db.execute("SELECT cluster_id, grp FROM clusters")}
    todo = [i for i in items if i["item_id"] not in assigned]
    if not todo or not group_of:
        return {"new": len(todo), "assigned": 0}
    vecs = embed_fn([i["signature"] for i in items])
    pos = {i["item_id"]: k for k, i in enumerate(items)}
    cents = {}
    for cid in group_of:
        idx = [pos[i] for i, c in assigned.items() if c == cid and i in pos]
        if idx:
            cents[cid] = _unit(vecs[idx].mean(0))
    n = 0
    for it in todo:
        sims = {cid: float(vecs[pos[it["item_id"]]] @ c) for cid, c in cents.items() if group_of[cid] == it["group"]}
        if sims:
            best = max(sims, key=sims.get)
            if sims[best] >= min_sim:
                db.execute("INSERT OR IGNORE INTO cluster_items VALUES(?,?)", (best, it["item_id"]))
                n += 1
    db.commit()
    return {"new": len(todo), "assigned": n}
