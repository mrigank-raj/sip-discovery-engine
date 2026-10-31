"""Insights: turn the tables into findings a reader can act on.

Code finds notable contrasts in the data (detectors) and sets the confidence itself from sample size and source spread. An LLM
writes each one up as a headline, a "so what" and a caveat. A validator rejects write-ups that use a number the data does not
contain, or that call a minority "most", "often" or "significant", and a second LLM pass rejects claims the facts do not
support. If the LLM fails, a plain fallback headline is used. Candidate beliefs are never turned into cards.
"""
import json
import re
from collections import Counter
from pathlib import Path

from engine import cluster, llm, store

ROOT = Path(__file__).resolve().parents[2]
OVERCLAIM = re.compile(r"\b(most|majority|often|frequently|significant|dominat\w*|heavily|vast|almost all|widespread)\b", re.I)
NS = {"not_stated", "unknown", "none_stated", "unclear"}


def _pct(a, b):
    return round(100 * a / b) if b else 0


def _quotes(items, pick, n=3, min_len=28):
    """Up to n verbatim evidence quotes (already validated against the post text), one per source where possible."""
    out, seen = [], set()
    pool = [(i, q) for i in items if pick(i) for q in i["rec"]["evidence_quotes"] if len(q) >= min_len]
    for i, q in sorted(pool, key=lambda p: p[0]["confidence"] != "high"):
        if i["source"] not in seen and len(out) < n:
            out.append({"item_id": i["item_id"], "source": i["source"], "quote": q, "url": i["url"]})
            seen.add(i["source"])
    return out


ANGLES = {
    "why_pull_back": "Among posts where the person actually paused, reduced, stopped or redeemed, what reasons they give, and how many give none.",
    "contrast": "How posts by people who keep investing differ from posts by people who pulled back or are considering it, on emotion and on how often they check.",
    "involuntary": "How many lapses in the sample are failed instalments the person did not choose, against voluntary pull-backs.",
    "when": "At which journey stage pull-backs are described, among posts that say how long the person has been investing.",
    "outside_app": "Where people turn outside the app, and whether that differs between people who stay and people who pull back.",
    "first_time": "How posts by self-described first-time investors differ from posts by experienced investors in what action they describe.",
    "blind": "The biggest blind spots: what this data cannot tell us.",
}
WEAK_IDS = {"blind"}


def _cand(id_, facts, fallback, quotes, n, sources, main_pct=None, llm_=True, so_what="", caveat=""):
    return {"id": id_, "angle": ANGLES[id_], "facts": facts, "fallback": fallback, "quotes": quotes, "n": n, "sources": sources,
            "main_pct": main_pct, "heuristic": False, "llm": llm_, "so_what": so_what, "caveat": caveat}


def confidence(c):
    """Set by code, not by the LLM: high needs 50+ items across 4+ sources; medium 20+ across 2+."""
    level = "high" if c["n"] >= 50 and c["sources"] >= 4 else "medium" if c["n"] >= 20 and c["sources"] >= 2 else "low"
    return "medium" if c["heuristic"] and level == "high" else level


def _dist(items, field, top=5):
    c = Counter(i[field] for i in items if i[field] not in NS)
    return {k: v for k, v in c.most_common(top)}


def candidates(db, keep=lambda item: True):
    items = [i for i in cluster.load(db) if keep(i)]
    nsrc = lambda g: len({i["source"] for i in g})  # noqa: E731
    acted = [i for i in items if i["voluntary_acted"]]
    stay = [i for i in items if i["contrast_bucket"] == "continuers"]
    back = [i for i in items if i["contrast_bucket"] in ("acted", "considering")]
    failed = [i for i in items if i["sip_action"] == "instalment_failed"]
    out = []

    no_reason = sum(i["action_reason"] == "not_stated" for i in acted)
    top = _dist(acted, "action_reason")
    lead = max(top.values()) if top else 0
    out.append(_cand("why_pull_back", {"posts_that_paused_reduced_stopped_or_redeemed": len(acted), "give_no_reason": no_reason,
                                       "reasons_given_posts": top},
                     f"{len(acted)} posts describe actually pulling back; {no_reason} give no reason.",
                     _quotes(acted, lambda i: i["action_reason"] not in NS), len(acted), nsrc(acted), _pct(lead, len(acted))))

    def prof(g):
        return {"posts": len(g), "emotion_posts": _dist(g, "emotion"), "check_frequency_posts": _dist(g, "check_frequency"),
                "state_how_often_they_check": sum(i["check_frequency"] not in NS for i in g)}
    out.append(_cand("contrast", {"keep_investing": prof(stay), "pulled_back_or_considering": prof(back)},
                     f"{len(stay)} posts describe staying in and {len(back)} pulling back or considering it.",
                     _quotes(stay, lambda i: True, n=2) + _quotes(back, lambda i: True, n=2), len(stay) + len(back), nsrc(stay + back)))

    lapses = len(acted) + len(failed)
    out.append(_cand("involuntary", {"failed_instalments": len(failed), "voluntary_pull_backs": len(acted), "all_lapses": lapses,
                                     "failed_share_of_lapses_pct": _pct(len(failed), lapses),
                                     "failed_reasons_posts": _dist(failed, "action_reason")},
                     f"{len(failed)} of {lapses} lapses described ({_pct(len(failed), lapses)}%) are failed instalments.",
                     _quotes(failed, lambda i: True), lapses, nsrc(acted + failed), _pct(len(failed), lapses)))

    staged = [i for i in acted if i["journey_stage"] in cluster.STAGES]
    out.append(_cand("when", {"pull_backs": len(acted), "pull_backs_with_a_stated_stage": len(staged),
                              "by_stage_posts": dict(Counter(i["journey_stage"] for i in staged))},
                     f"{len(staged)} of {len(acted)} pull-backs say how long the person had been investing.",
                     _quotes(staged, lambda i: True), len(staged), nsrc(staged)))

    def outside(g):
        return {"posts": len(g), "turn_outside_the_app": sum(i["outside_app_behaviour"] not in NS for i in g),
                "where_posts": _dist(g, "outside_app_behaviour")}
    out.append(_cand("outside_app", {"keep_investing": outside(stay), "pulled_back_or_considering": outside(back)},
                     "Some posts describe asking someone or watching videos before deciding.",
                     _quotes(stay + back, lambda i: i["outside_app_behaviour"] not in NS), len(stay) + len(back), nsrc(stay + back)))

    first = [i for i in items if i["investor_experience"] == "first_time"]
    exp = [i for i in items if i["investor_experience"] == "experienced"]
    bucket = lambda g: dict(Counter(i["contrast_bucket"] or i["sip_action"] for i in g).most_common(6))  # noqa: E731
    out.append(_cand("first_time", {"first_time_posts": len(first), "experienced_posts": len(exp),
                                    "first_time_by_action_posts": bucket(first), "experienced_by_action_posts": bucket(exp)},
                     f"{len(first)} posts are by self-described first-time investors, {len(exp)} by experienced ones.",
                     _quotes(first, lambda i: True), len(first) + len(exp), nsrc(first + exp)))

    n = len(items)
    out.append(_cand("blind", {"extracted_posts": n, "state_journey_stage_pct": _pct(sum(i["journey_stage"] not in NS for i in items), n),
                               "state_income_type_pct": _pct(sum(i["income_type"] not in NS for i in items), n),
                               "state_investor_experience_pct": _pct(sum(i["investor_experience"] not in NS for i in items), n),
                               "state_a_belief": sum(bool(i["has_belief"]) for i in items)},
                     f"Of {n} extracted posts, {_pct(sum(i['journey_stage'] not in NS for i in items), n)}% say how long the person has invested, "
                     f"{_pct(sum(i['income_type'] not in NS for i in items), n)}% their income type and "
                     f"{_pct(sum(i['investor_experience'] not in NS for i in items), n)}% whether they are first-time investors.",
                     [], n, len({i["source"] for i in items}), llm_=False,
                     so_what="Segment and stage questions (who drops off, and when) mostly cannot be answered from public posts; they need the "
                             "app's own data or primary research.",
                     caveat="Absence from posts does not mean absence in the population; people rarely write these details down."))
    return out


def _numbers(obj, acc=None):
    acc = acc if acc is not None else set()
    if isinstance(obj, dict):
        for v in obj.values():
            _numbers(v, acc)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _numbers(v, acc)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        acc.add(float(obj))
    return acc


def check_numbers(text, facts):
    """Return numbers in `text` (10 or more, or written with a %) that do not appear in the facts."""
    allowed = _numbers(facts)
    bad = []
    for m in re.finditer(r"\d[\d,]*\.?\d*\s*%?", text):
        raw = m.group(0)
        x = float(raw.replace(",", "").replace("%", "").strip() or 0)
        if (x >= 10 or "%" in raw) and not any(abs(x - a) < 0.51 for a in allowed):
            bad.append(raw.strip())
    return bad


def overclaims(text, main_pct):
    """Words like 'most' or 'often' are only allowed when the headline share is 50% or more (or unknown)."""
    return sorted({m.group(0).lower() for m in OVERCLAIM.finditer(text)}) if main_pct is not None and main_pct < 50 else []


SCHEMA = {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
    "id": {"type": "STRING"}, "headline": {"type": "STRING"}, "so_what": {"type": "STRING"}, "caveat": {"type": "STRING"}},
    "required": ["id", "headline", "so_what", "caveat"]}}

PROMPT = """You are a product analyst writing findings from a study of what public app reviews, forum posts and video comments by Indian investors say about their SIPs (systematic investment plans) and mutual funds.
Below are candidate findings, each with an `angle` (the point it should make), its measured facts and example quotes. Write about the angle, using the facts. For each one write:
- `headline`: ONE sentence that states the insight, meaning what the numbers imply that a reader would not already assume. Include the one or two numbers that make the point. A skeptic must be able to test it against the facts.
- `so_what`: one or two sentences on what this suggests is worth investigating about why investors keep or stop their SIPs. State it as a plain sentence, never as a question. Do NOT name a feature or give a recommendation.
- `caveat`: one sentence, the main reason to limit this finding.
Hard rules:
- Use ONLY numbers in that candidate's facts. Never invent a number, a percentage, a cause, a product mechanism or a source.
- Do not explain WHY something happens unless the facts or quotes say so.
- Counts are mentions in a sample of posts, not how many investors do something. Say "posts", never "users", "investors" or "people generally".
- If a share is under 50%, state it plainly ("one in five posts"; do not use the word minority). Never write most, majority, often, frequently, significant, dominated, heavily or almost all for it.
- No repeated ideas across findings. Plain words, no jargon.

Candidates (JSON):
{candidates}
"""

VERIFY_SCHEMA = {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
    "id": {"type": "STRING"}, "ok": {"type": "BOOLEAN"}, "issue": {"type": "STRING"}}, "required": ["id", "ok", "issue"]}}
VERIFY_PROMPT = """You check written findings against the facts behind them. For each finding decide whether EVERY claim is supported by its facts.
Mark ok=false and state the issue in one sentence if the text: says two numbers match, are similar or are comparable when they differ; claims a cause
("driven by", "because", "due to", "leading to") that the facts do not state; generalises beyond the sample (for example says "users", "investors" or
"people" where the facts count posts); or describes a measure as something other than what its fact name says. Otherwise ok=true with an empty issue. Be strict.

Findings (JSON):
{items}
"""


def verify(written, cands, model, fallback_model, generate=llm.generate_json):
    """Second LLM pass whose only job is to reject write-ups that the facts do not support. Returns {id: issue}."""
    facts = {c["id"]: c["facts"] for c in cands}
    payload = [{"id": k, "facts": facts[k], "text": " ".join((v["headline"], v["so_what"], v["caveat"]))} for k, v in written.items()]
    if not payload:
        return {}
    prompt = VERIFY_PROMPT.replace("{items}", json.dumps(payload, indent=1, ensure_ascii=False))
    try:
        answer = generate(model, prompt, VERIFY_SCHEMA, max_output_tokens=8192)
    except llm.DailyQuotaExhausted:
        answer = generate(fallback_model, prompt, VERIFY_SCHEMA, max_output_tokens=8192)
    return {a["id"]: a["issue"] or "unsupported claim" for a in answer if isinstance(a, dict) and not a.get("ok", True)}


def narrate(cands, model, fallback_model, generate=llm.generate_json):
    cands = [c for c in cands if c["llm"]]
    payload = [{"id": c["id"], "angle": c["angle"], "facts": c["facts"], "example_quotes": [q["quote"] for q in c["quotes"]]} for c in cands]
    by_id, note = {}, ""
    for attempt in range(2):
        prompt = PROMPT.replace("{candidates}", json.dumps(payload, indent=1, ensure_ascii=False)) + (
            f"\nYour previous answer was rejected: {note}\nFix only those findings.\n" if note else "")
        try:
            answer = generate(model if attempt == 0 else fallback_model, prompt, SCHEMA, max_output_tokens=16384)
        except llm.DailyQuotaExhausted:
            answer = generate(fallback_model, prompt, SCHEMA, max_output_tokens=16384)
        by_id.update({a["id"]: a for a in answer if isinstance(a, dict)})
        problems = []
        for c in cands:
            a = by_id.get(c["id"])
            if a:
                text = " ".join((a["headline"], a["so_what"], a["caveat"]))
                bad, over = check_numbers(text, c["facts"]), overclaims(text, c["main_pct"])
                if "?" in a["so_what"]:
                    over = over + ["a question in so_what"]
                if bad or over:
                    problems.append(f"{c['id']}: " + (f"numbers not in its facts {bad}; " if bad else "") +
                                    (f"words not allowed for a {c['main_pct']}% share {over}" if over else ""))
                    by_id.pop(c["id"])
        for cid, issue in verify(dict(by_id), cands, model, fallback_model, generate).items():
            problems.append(f"{cid}: {issue}")
            by_id.pop(cid, None)
        if not problems:
            return by_id
        note = " | ".join(problems)[:600]
        payload = [p for p in payload if p["id"] not in by_id]
    return by_id


def build(model, fallback_model, use_llm=True):
    db = store.connect(cluster.DB_PATH)
    cands = candidates(db)
    written = narrate(cands, model, fallback_model) if use_llm else {}
    out = []
    for c in cands:
        w = written.get(c["id"])
        out.append({"id": c["id"], "headline": w["headline"] if w else c["fallback"], "so_what": w["so_what"] if w else c["so_what"],
                    "caveat": w["caveat"] if w else c["caveat"], "confidence": confidence(c), "n": c["n"], "sources": c["sources"],
                    "weak": c["id"] in WEAK_IDS or confidence(c) == "low", "written_by_llm": bool(w), "plain_text": not c["llm"],
                    "facts": c["facts"], "quotes": c["quotes"]})
    res = ROOT / "eval" / "results"
    res.mkdir(parents=True, exist_ok=True)
    (res / "insights.json").write_text(json.dumps({"versions": store.versions(), "insights": out}, indent=1, ensure_ascii=False), encoding="utf8")
    (res / "insights.md").write_text(to_markdown(out), encoding="utf8")
    return out


FIRST = lambda i: i["investor_experience"] == "first_time"  # noqa: E731


def _cell(n, total):
    return f"{n} ({_pct(n, total)}%)" if total else "-"


def side_by_side(db, keep=FIRST, label="First-timers"):
    """All users next to one cut (self-described first-time investors by default): opportunity ranking, pull-back reasons,
    stay-vs-stop sizes and emotion, and the code-worded cards. No LLM. Writes eval/results/first_timers.md."""
    everyone, cut = cluster.load(db), [i for i in cluster.load(db) if keep(i)]
    L = [f"# {label} vs all users", "",
         f"{len(cut)} of {len(everyone)} analysed posts are in the cut. investor_experience is filled only when the person says it, so "
         "first-timers who do not say so sit in all users; how many the engine misses is measured by the experience label set. "
         "Counts are posts in a sample, not population rates.", ""]

    ms_all, ms_cut = cluster.metrics(db), cluster.metrics(db, keep)
    rank = lambda ms: {m["id"]: (k, m) for k, m in enumerate([m for m in ms if m["score"] is not None], 1)}  # noqa: E731
    ra, rc = rank(ms_all), rank(ms_cut)
    posts_cut = {m["id"]: m["items"] for m in ms_cut}
    show = [cid for cid in ra if ra[cid][0] <= 15] + [cid for cid in rc if cid in ra and ra[cid][0] > 15] + [cid for cid in rc if cid not in ra]
    L += ["## Opportunity ranking", "",
          f"Scores are rescaled within each view, so compare ranks, not raw scores. A cluster needs {cluster.MIN_ITEMS}+ posts in the view "
          f"to be ranked; {len(rc)} clusters reach that among {label.lower()}. Top 15 for all users, plus every cluster ranked in the cut.", "",
          f"| cluster | all: rank | all: score | all: posts | {label}: rank | {label}: score | {label}: posts |", "|---|---|---|---|---|---|---|"]
    for cid in show:
        m = (ra.get(cid) or rc[cid])[1]
        a, c = ra.get(cid), rc.get(cid)
        L.append(f"| {m['name']} | {a[0] if a else '-'} | {a[1]['score'] if a else '-'} | {a[1]['items'] if a else '-'} | "
                 f"{c[0] if c else 'not ranked'} | {c[1]['score'] if c else '-'} | {posts_cut.get(cid, 0)} |")

    acted_a, acted_c = [i for i in everyone if i["voluntary_acted"]], [i for i in cut if i["voluntary_acted"]]
    reasons = Counter(i["action_reason"] for i in acted_a)
    L += ["", "## Pull-back reasons", "", f"Posts that paused, reduced, stopped or redeemed: all {len(acted_a)}, {label.lower()} {len(acted_c)}.", "",
          f"| reason | all users | {label} |", "|---|---|---|"]
    for r, _ in reasons.most_common():
        L.append(f"| {r} | {_cell(reasons[r], len(acted_a))} | {_cell(sum(i['action_reason'] == r for i in acted_c), len(acted_c))} |")

    con_a, con_c = cluster.contrast(db), cluster.contrast(db, keep)
    tot_a, tot_c = sum(v["items"] for v in con_a.values()), sum(v["items"] for v in con_c.values())
    L += ["", "## Stay vs stop: group sizes", "", f"| group | all users | {label} |", "|---|---|---|"]
    L += [f"| {b} | {_cell(con_a[b]['items'], tot_a)} | {_cell(con_c[b]['items'], tot_c)} |" for b in cluster.BUCKETS]
    L += ["", "## Stay vs stop: emotion", "", "Share of each group's posts; not-stated emotions are left out of the list but kept in the base.", "",
          f"| group | emotion | all users | {label} |", "|---|---|---|---|"]
    for b in ("continuers", "considering", "acted"):
        for e, n in con_a[b]["emotion"].items():
            if e not in NS:
                L.append(f"| {b} | {e} | {_cell(n, con_a[b]['items'])} | {_cell(con_c[b]['emotion'].get(e, 0), con_c[b]['items'])} |")

    ca = {c["id"]: c for c in candidates(db)}
    cc = {c["id"]: c for c in candidates(db, keep)}
    L += ["", "## Cards, worded by code (no model)", "", f"| card | all users | {label} |", "|---|---|---|"]
    for cid in ("why_pull_back", "contrast", "involuntary", "when"):
        L.append(f"| {cid} | {ca[cid]['fallback']} ({confidence(ca[cid])}) | {cc[cid]['fallback']} ({confidence(cc[cid])}) |")
    emo = lambda c, g: ", ".join(f"{k} {v}" for k, v in c["facts"][g]["emotion_posts"].items()) or "none stated"  # noqa: E731
    for g, name in (("keep_investing", "emotion, keep investing"), ("pulled_back_or_considering", "emotion, pulled back or considering")):
        L.append(f"| {name} | {emo(ca['contrast'], g)} of {ca['contrast']['facts'][g]['posts']} | {emo(cc['contrast'], g)} of {cc['contrast']['facts'][g]['posts']} |")
    out = ROOT / "eval" / "results" / "first_timers.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf8")
    return L


def to_markdown(out):
    L = []
    for k, i in enumerate([x for x in out if not x["weak"]] + [x for x in out if x["weak"]], 1):
        L += [f"### {k}. {i['headline']}", ""]
        if i["so_what"]:
            L += [f"**Interpretation (a hypothesis to test, not a finding).** {i['so_what']}", ""]
        L += [f"**Confidence: {i['confidence']}** ({i['n']} items, {i['sources']} sources)." + (f" **Caveat.** {i['caveat']}" if i["caveat"] else "")]
        L += [f"- \"{q['quote']}\" ({q['source']}, [link]({q['url']}))" for q in i["quotes"]] + [""]
    return "\n".join(L)
