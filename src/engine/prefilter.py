"""Cheap, recall-oriented keyword filter that runs before any LLM call. Covers English, Hinglish and Hindi (Devanagari).

Terms are grouped so the golden set can be stratified on which kind of term matched, without using any model output.
"""
import re

GROUPS = {
    # stopping, pausing, failed or deducted instalments, redemption
    "stop_or_fail": r"\bsips? ?(band|rok|ruk|stop|pause|cancel)\w*|\b(stop|stopped|pause[d]?|cancel+e?d?|discontinu\w+) (my |the |all )?sips?\b|"
                    r"\bmandate|\bauto ?pay|\bnach\b|\binstal+ments?\b|\bpaisa (kat|cut)\w*|\bredeem\w*|\bredemption|"
                    r"एसआईपी (बंद|रोक)|किस्त",
    # returns, losses, NAV
    "returns": r"\bnav\b|\bxirr\b|\bcagr\b|\bloss (me|mein|mai)\b|\breturns? (nahi|nhi|kam)\b|लॉस|रिटर्न",
    # the product itself
    "sip_or_mf": r"\bsips?\b|\bmutual ?funds?\b|\bmfs?\b|\belss\b|\bindex funds?\b|\b(small|mid|flexi|large) ?cap\b|\bfolio\b|\bstep ?up\b|"
                 r"एसआईपी|म्यूचुअल",
}
COMPILED = {k: re.compile(v, re.I) for k, v in GROUPS.items()}
STORE_SOURCES = {"play", "appstore"}


def own_title(source, item_id, thread_id, title):
    """The title an item is judged with: its own for posts and reviews, none for comments and replies, whose title is the
    video's or thread's (on-topic by construction, so it would pass every comment)."""
    return None if source == "youtube" or (thread_id and thread_id != item_id) else title


def groups_hit(title, text):
    blob = f"{title or ''}\n{text or ''}"
    return [k for k, rx in COMPILED.items() if rx.search(blob)]


# Second pass for comments and replies (decision 2026-10-29, eval/corrections.md section 0): a hand check found SIP stories in
# comments the text-only rule dropped, often Hinglish with no SIP word ("3 saal se chal raha hai, band nahi karunga").
ACTION_VERBS = re.compile(r"\b(band|ruk\w*|rok\w*|chhod\w*|pause\w*|stop\w*|continu\w*|chal raha|redeem\w*|nikaal\w*)\b", re.I)


def passes(source, title, text, context_title=None):
    """Store reviews are mostly about stocks and F&O, so a returns word alone is not enough there; forum and video items are
    already on topic through their queries and categories, so any group passes. A comment or reply (title None) also passes
    when its video or thread title is about SIPs (`context_title`) and its own text uses an action verb."""
    hit = groups_hit(title, text)
    if source in STORE_SOURCES:
        return "sip_or_mf" in hit or "stop_or_fail" in hit
    return bool(hit) or verb_pass(title, text, context_title)


def verb_pass(title, text, context_title):
    return title is None and bool(context_title) and bool(COMPILED["sip_or_mf"].search(context_title)) \
        and bool(ACTION_VERBS.search(text or ""))
