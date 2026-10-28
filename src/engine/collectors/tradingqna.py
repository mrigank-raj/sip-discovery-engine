"""TradingQ&A (Zerodha's Discourse forum) through its public JSON. robots.txt disallows /search, so topics are found by paging
category listings and filtering titles here; each matching topic is then read from /t/{id}.json. One request every 2 seconds."""
import re
import time

import requests
from bs4 import BeautifulSoup

BASE = "https://tradingqna.com"
HEADERS = {"User-Agent": "sip-discovery-research (non-commercial study; 1 request per 2s)"}
PAUSE = 2.0
TITLE = re.compile(r"\bsips?\b|mutual ?funds?|\bmfs?\b|\belss\b|index funds?|\bnav\b|\bcoin\b|redeem|redemption|mandate|step ?up", re.I)


def _get(path, **params):
    time.sleep(PAUSE)
    r = requests.get(f"{BASE}{path}", params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def topics(cfg, since):
    """(id, slug, title) of SIP or mutual-fund topics created on or after `since`, newest first per category."""
    src = cfg["sources"]["tradingqna"]
    found, errors = {}, []
    for slug, cid in src["categories"].items():
        for page in range(src.get("max_pages", {}).get(slug, 1000)):
            try:
                tl = _get(f"/c/{slug}/{cid}.json", page=page)["topic_list"]
            except (requests.RequestException, ValueError, KeyError) as e:
                errors.append(f"listing {slug} p{page}: {e}")
                break
            rows = tl.get("topics", [])
            for t in rows:
                if (t.get("created_at") or "")[:10] >= since and TITLE.search(t["title"]):
                    found[t["id"]] = (t["id"], t["slug"], t["title"])
            if not rows or not tl.get("more_topics_url") or all((t.get("bumped_at") or "")[:10] < since for t in rows):
                break
    return list(found.values()), errors


def html_text(html):
    """Line breaks only at block tags, so inline tags such as <b> do not split a sentence (quotes must stay verbatim)."""
    soup = BeautifulSoup(html or "", "lxml")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for b in soup.find_all(["p", "li", "blockquote", "h1", "h2", "h3", "h4", "pre", "aside"]):
        b.append("\n")
    return re.sub(r"\n{3,}", "\n\n", soup.get_text()).strip()


def post_items(topic, t):
    tid, slug, title = topic
    out = []
    for p in t.get("post_stream", {}).get("posts", []):
        text = html_text(p.get("cooked"))
        first = p["post_number"] == 1
        out.append({"item_id": f"tradingqna:{tid}" if first else f"tradingqna:{tid}-{p['post_number']}", "source": "tradingqna",
                    "product": None, "url": f"{BASE}/t/{slug}/{tid}/{p['post_number']}", "thread_id": f"tradingqna:{tid}",
                    "parent_id": None if first else f"tradingqna:{tid}", "created_at": p.get("created_at"), "title": title,
                    "text": f"{title}\n\n{text}" if first else text, "helpful_count": p.get("like_count") or p.get("score"),
                    "author": p.get("username"), "raw": {"topic_id": tid, "post_number": p["post_number"]}})
    return out


def fetch(cfg, limit, product_keys, since=None):
    """limit = max topics to read. Only the first page of posts per topic (Discourse returns up to 20) is read."""
    from datetime import date, timedelta
    from engine.store import infer_product
    since = since or (date.today() - timedelta(days=30 * cfg["window_months"])).isoformat()
    found, errors = topics(cfg, since)
    items = []
    for topic in found[:limit]:
        try:
            items += post_items(topic, _get(f"/t/{topic[0]}.json"))
        except (requests.RequestException, ValueError) as e:
            errors.append(f"topic {topic[0]}: {e}")
    for it in items:
        it["product"] = infer_product(it["title"], it["text"])
    errors.append(f"topics_matched={len(found)} topics_read={min(len(found), limit)}")
    return items, errors
