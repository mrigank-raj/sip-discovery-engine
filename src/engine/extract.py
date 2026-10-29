"""Structured extraction of SIP-journey evidence with a verbatim-quote validator.

Several items go to the model in one request, but every quote is checked against the text of the item it is attached to and
nothing else: a quote copied from another item in the same batch is rejected.
"""
import json
import re
import unicodedata
from pathlib import Path

import yaml

from engine import llm

ROOT = Path(__file__).resolve().parents[2]
TEXT_LIMIT, STARTER_LIMIT = 2500, 600
ENUMS = ["investor_experience", "platform", "journey_stage", "sip_action", "action_reason", "what_they_check", "check_frequency",
         "outside_app_behaviour", "emotion", "life_stage", "income_type", "source_of_money", "influenced_by", "severity", "confidence"]
QUOTE_FIELDS = ["expectation_at_start", "belief_quote", "age_stated"]  # each must be verbatim in the item's own text when not null
ACTED = {"paused", "reduced", "stopped", "redeemed"}
BUCKET = {"continuing": "continuers", "increased": "continuers", "considering_stopping": "considering",
          **{a: "acted" for a in ACTED}, "instalment_failed": "instalment_failed", "switched_platform": "switched_platform"}
# Store reviews are about the app being reviewed, so the platform comes from the source, not the model.
STORE_PLATFORM = {"groww": "groww", "coin": "zerodha", "indmoney": "indmoney", "et_money": "etmoney"}


def taxonomy():
    return yaml.safe_load((ROOT / "config" / "taxonomy.yaml").read_text(encoding="utf8"))


def _enum(tax, name):
    return {"type": "STRING", "enum": list(tax[name])}


def schema(tax):
    text = {"type": "STRING", "nullable": True}
    props = {"i": {"type": "INTEGER"}, "summary": {"type": "STRING"}, "secondhand": {"type": "BOOLEAN"},
             **{n: _enum(tax, n) for n in ENUMS}, **{n: text for n in QUOTE_FIELDS}, "belief_at_action": text,
             "evidence_quotes": {"type": "ARRAY", "items": {"type": "STRING"}}}
    required = ["i", "summary", "secondhand", *ENUMS, "evidence_quotes"]
    return {"type": "ARRAY", "items": {"type": "OBJECT", "properties": props, "required": required}}


def build_prompt(items, tax, error_note=None):
    blocks = []
    for i, it in enumerate(items):
        text = it["text"] if len(it["text"]) <= TEXT_LIMIT else it["text"][:TEXT_LIMIT] + " [...]"
        head = f"### {i} | source: {it['source']} | app: {it.get('product') or '-'} | title: {it.get('title') or '-'}"
        starter = it.get("starter")
        ctx = f"\n[thread starter, context only, never quote: {starter[:STARTER_LIMIT]!r}]" if starter else ""
        blocks.append(f"{head}{ctx}\n{text}")
    prompt = (ROOT / "prompts" / "extraction.md").read_text(encoding="utf8")
    for n in ENUMS:
        prompt = prompt.replace("{" + n + "}", "\n".join(f"- {k}: {v}" for k, v in tax[n].items()))
    prompt = prompt.replace("{items}", "\n\n".join(blocks))
    if error_note:
        prompt += f"\n\nYour previous answer for this item was rejected: {error_note}\nAnswer again; copy quotes exactly."
    return prompt


ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿"))  # Devanagari text often carries joiners a model drops
PLAIN = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})


def norm(s):
    """Applied identically to the source text and to every quote: NFC, zero-width removed, smart quotes made plain,
    whitespace collapsed, case folded."""
    s = unicodedata.normalize("NFC", s).translate(ZERO_WIDTH).translate(PLAIN)
    return re.sub(r"\s+", " ", s).strip().casefold()


def quote_ok(quote, text):
    return bool(quote) and bool(norm(quote)) and norm(quote) in norm(text)


def validate(rec, text, tax):
    """Deterministic checks against THIS item's text only; returns a list of error strings (empty means valid)."""
    errs = []
    for field in ENUMS:
        if rec.get(field) not in tax[field]:
            errs.append(f"{field}={rec.get(field)!r} is not an allowed value")
    quotes = rec.get("evidence_quotes") or []
    if not 1 <= len(quotes) <= 3:
        errs.append(f"evidence_quotes must hold 1 to 3 quotes, got {len(quotes)}")
    for q in quotes:
        if not quote_ok(q, text):
            errs.append(f"evidence quote is not verbatim in this item's text: {q!r}")
    for f in QUOTE_FIELDS:
        if rec.get(f) is not None and not quote_ok(rec[f], text):
            errs.append(f"{f} is not verbatim in this item's text: {rec[f]!r}")
    if bool(rec.get("belief_at_action")) != bool(rec.get("belief_quote")):
        errs.append("belief_at_action and belief_quote must both be set or both be null")
    if rec.get("severity") == "acted" and rec.get("sip_action") not in ACTED:
        errs.append(f"severity 'acted' needs a paused, reduced, stopped or redeemed sip_action, got {rec.get('sip_action')!r}")
    return errs


def _batch(items, model, tax, generate):
    answer = generate(model, build_prompt(items, tax), schema(tax), max_output_tokens=16384)
    return {a["i"]: a for a in answer if isinstance(a, dict) and a.get("i") in range(len(items))}


def extract(items, model, batch=8, generate=llm.generate_json, progress=None, on_batch=None):
    """items: dicts with source, product, title, text, starter (optional). Returns (records, review) where records[i] is a
    valid record or None, and review lists (index, reason) for items that never validated."""
    tax = taxonomy()
    records, review = [None] * len(items), []
    for start in range(0, len(items), batch):
        chunk = items[start:start + batch]
        got = _batch(chunk, model, tax, generate)
        for i, it in enumerate(chunk):
            rec = got.get(i)
            errs = validate(rec, it["text"], tax) if rec else ["no answer for this item"]
            if errs:  # one retry, item alone, with the error message
                again = generate(model, build_prompt([it], tax, "; ".join(errs)[:600]), schema(tax), max_output_tokens=16384)
                rec = next((a for a in again if isinstance(a, dict)), None)
                errs = validate(rec, it["text"], tax) if rec else ["no answer for this item"]
            if errs:
                review.append((start + i, "; ".join(errs)[:500]))
            else:
                records[start + i] = rec
        if on_batch:  # lets the caller save finished work before a quota error can lose it
            on_batch(start, records[start:start + len(chunk)], [(i, w) for i, w in review if i >= start])
        if progress:
            progress(min(start + batch, len(items)), len(items))
    return records, review


def with_starters(db, rows):
    """Attach the thread's first post (context only) to replies and comments."""
    out = []
    for r in rows:
        d = dict(r)
        starter = None
        if d.get("thread_id") and d["thread_id"] != d["item_id"]:
            s = db.execute("SELECT text FROM raw_items WHERE item_id=?", (d["thread_id"],)).fetchone()
            starter = s["text"] if s else None
        out.append({**d, "starter": starter})
    return out


def new_pool(db):
    """Items the classifier called a SIP or mutual-fund journey (any language) that have no extraction yet, taking one item
    from each source in turn, so a run that stops on the daily quota has covered every source, not only the first in id order."""
    return [r[0] for r in db.execute(
        "SELECT f.item_id FROM filter_results f JOIN raw_items r USING(item_id) LEFT JOIN extractions e USING(item_id) "
        "WHERE f.relevant=1 AND e.item_id IS NULL "
        "ORDER BY ROW_NUMBER() OVER (PARTITION BY r.source ORDER BY f.item_id), r.source")]


def save(db, item_id, rec, model, run_id, taxonomy_version, source=None, product=None):
    if source in ("play", "appstore") and product in STORE_PLATFORM:
        rec = {**rec, "platform": STORE_PLATFORM[product]}
    cols = ["item_id", "json", "summary", "secondhand", *ENUMS, "contrast_bucket", "has_expectation", "has_belief",
            "taxonomy_version", "model", "run_id"]
    vals = [item_id, json.dumps(rec, ensure_ascii=False), rec["summary"], int(bool(rec["secondhand"])), *(rec[n] for n in ENUMS),
            BUCKET.get(rec["sip_action"]), int(rec.get("expectation_at_start") is not None), int(rec.get("belief_quote") is not None),
            taxonomy_version, model, run_id]
    db.execute(f"INSERT OR REPLACE INTO extractions({', '.join(cols)}) VALUES({', '.join('?' * len(cols))})", vals)
