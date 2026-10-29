import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from engine import cluster  # noqa: E402


def m(i, source="play", stage="unknown", action="stopped", severity="acted", thread=None):
    return {"item_id": i, "source": source, "thread": thread or i, "platform": "groww", "journey_stage": stage, "sip_action": action,
            "severity": severity, "voluntary_acted": severity == "acted" and action in cluster.ACTED, "outside_app_behaviour": "none_stated",
            "action_reason": "market_fall", "has_belief": 0, **{s: "not_stated" for s in cluster.SEGMENTS}}


def test_stage_concentration_needs_ten_known_stages_and_is_flagged_otherwise():
    few = cluster.describe([m("a", stage="months_4_to_12"), m("b", stage="months_4_to_12")])
    assert few["stage_concentration"] == 0.0 and "only 2" in few["stage_flag"]
    many = cluster.describe([m(str(k), stage="first_3_months" if k < 8 else "after_12_months") for k in range(10)])
    assert many["stage_concentration"] == 0.8 and many["stage_flag"] is None and many["top_stage"] == "first_3_months"


def test_failed_instalments_do_not_count_as_acted():
    d = cluster.describe([m("a", action="instalment_failed", severity="unclear"), m("b"), m("c", action="considering_stopping", severity="considered")])
    assert round(d["acted_share"], 2) == 0.33 and round(d["instalment_failed_share"], 2) == 0.33 and round(d["considered_share"], 2) == 0.33


def test_clusters_under_the_minimum_are_not_ranked_and_scores_use_the_stated_formula():
    rows = [{"id": 1, **cluster.describe([m(f"a{k}") for k in range(12)])},
            {"id": 2, **cluster.describe([m(f"b{k}", source="youtube" if k % 2 else "reddit", severity="unclear", action="continuing") for k in range(8)])},
            {"id": 3, **cluster.describe([m(f"c{k}") for k in range(7)])}]
    s = cluster.score(rows)
    assert set(s) == {1, 2}                                            # 7 items is below the minimum of 8
    assert s[1]["parts"] == {"frequency": 1.0, "acted": 1.0, "stage": 0.0, "evidence": 0.0}
    assert s[1]["score"] == 0.70 and s[2]["score"] == 0.15             # 0.40 x 1 + 0.30 x 1; 0.15 x 1 (two sources vs one)
    assert cluster.below_min([{"score": None, "items": 7}, {"score": 0.5, "items": 9}]) == {"clusters": 1, "items": 7}


def test_analysis_excludes_items_with_no_sip_action_belief_or_emotion(tmp_path, monkeypatch):
    from engine import extract, store
    monkeypatch.setenv("AUTHOR_HASH_SALT", "t")
    db = store.connect(store.init_db(tmp_path / "t.db"))
    base = {"i": 0, "summary": "s", "secondhand": False, **{n: "not_stated" for n in extract.ENUMS}, "journey_stage": "unknown",
            "severity": "unclear", "confidence": "low", "outside_app_behaviour": "none_stated", "expectation_at_start": None,
            "belief_at_action": None, "belief_quote": None, "age_stated": None, "evidence_quotes": ["q"]}
    cases = {"noise": {}, "action": {"sip_action": "paused"}, "emotion": {"emotion": "anxious"},
             "belief": {"belief_at_action": "b", "belief_quote": "q"}}
    for k, extra in cases.items():
        db.execute("INSERT INTO raw_items(item_id, source, url, fetched_at, text, content_hash) VALUES(?,?,?,?,?,?)", (k, "play", "u", "t", "q", k))
        db.execute("INSERT INTO filter_results(item_id, prefilter_pass, relevant) VALUES(?,1,1)", (k,))
        extract.save(db, k, {**base, **extra}, "m", "r", "v3", "play", "groww")
    assert {i["item_id"] for i in cluster.load(db)} == {"action", "emotion", "belief"}
    assert len(cluster.load(db, analysable_only=False)) == 4
    f = cluster.funnel(db)[0]
    assert (f["extracted"], f["no_sip_action_stated"], f["analysed"]) == (4, 1, 3)
