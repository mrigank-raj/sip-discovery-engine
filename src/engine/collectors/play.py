import time

from google_play_scraper import Sort, reviews


def fetch(cfg, limit, product_keys, since=None):
    """Newest reviews, any rating, India store, in every configured language, paged until the per-app limit or the date
    window is reached. `limit` caps each app (0 = use per_app_limit from sources.yaml).

    The date span reached per app and language is reported in the errors list, because a few weeks of reviews can reflect
    one market mood (see sampling_note in sources.yaml).
    """
    src = cfg["sources"]["play"]
    floor = since or _window_start(cfg)
    items, errors = [], []
    for key in product_keys:
        p = cfg["products"][key]
        if not p.get("play_id"):
            continue
        cap = limit or src["per_app_limit"]["groww" if p["role"] == "primary" else "contrast"]
        for lang in src["langs"]:
            token, got, dates = None, 0, []
            while got < cap:
                try:
                    batch, token = reviews(p["play_id"], lang=lang, country="in", sort=Sort.NEWEST,
                                           count=min(200, cap - got), continuation_token=token)
                except Exception as e:  # scraper raises assorted errors; record and move on
                    errors.append(f"{key}/{lang}: {type(e).__name__}: {e}")
                    break
                if not batch:
                    break
                for r in batch:
                    at = r["at"].isoformat() if r.get("at") else None
                    dates.append(at)
                    items.append({
                        "item_id": f"play:{r['reviewId']}", "source": "play", "product": key,
                        "url": f"https://play.google.com/store/apps/details?id={p['play_id']}&reviewId={r['reviewId']}",
                        "created_at": at, "text": r.get("content"), "rating": r.get("score"),
                        "helpful_count": r.get("thumbsUpCount"),
                        "app_or_os_version": r.get("reviewCreatedVersion") or r.get("appVersion"),
                        "locale": f"in-{lang}", "author": r.get("userName"), "raw": r,
                    })
                got += len(batch)
                if (dates[-1] or "9")[:10] < floor or token is None or token.token is None:
                    break
                time.sleep(0.3)
            dated = sorted(d for d in dates if d)
            errors.append(f"span {key}/{lang}: {got} reviews, {dated[0][:10] if dated else '-'} to {dated[-1][:10] if dated else '-'}")
    return items, errors


def _window_start(cfg):
    from datetime import date, timedelta
    return (date.today() - timedelta(days=30 * cfg["window_months"])).isoformat()
