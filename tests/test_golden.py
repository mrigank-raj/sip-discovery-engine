import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from engine import golden  # noqa: E402

POOLS = {("play", "sip_or_mf"): [f"p{i}" for i in range(50)], ("play", "stop_or_fail"): [f"s{i}" for i in range(3)],
         ("youtube", "returns"): [f"y{i}" for i in range(20)]}


def test_pick_is_deterministic_spread_across_strata_and_tops_up_without_repeats():
    first = golden.pick(POOLS, 9)
    assert first == golden.pick(POOLS, 9) and len(set(first)) == 9
    assert {i[0] for i in first} == {"p", "s", "y"}                    # every stratum is represented
    assert [sum(i[0] == k for i in first) for k in "psy"] == [3, 3, 3]  # equal share per stratum, small pools included
    more = golden.pick(POOLS, 5, exclude=set(first))
    assert len(more) == 5 and not set(more) & set(first)


def test_label_columns_cover_relevance_beliefs_and_carry_no_model_fields():
    assert {"is_relevant", "belief_at_action", "belief_quote", "sip_action"} <= set(golden.LABELS)
    assert "summary" not in golden.LABELS and "confidence" not in golden.LABELS


def g(item_id, source, group, **labels):
    return {"item_id": item_id, "source": source, "group": group, "text": f"text of {item_id}", **labels}


def test_compare_scores_relevance_on_all_and_extraction_only_on_items_marked_relevant():
    rec = {"secondhand": False, **{f: "not_stated" for f in golden.ENUM_FIELDS}, "sip_action": "stopped",
           "belief_at_action": "Believed X", "expectation_at_start": None, "age_stated": None}
    gold = [g("a", "play", "stop_or_fail", is_relevant="y", sip_action="stopped", belief_at_action="null"),
            g("b", "youtube", "sip_or_mf", is_relevant="no", sip_action="continuing"),     # not relevant: only relevance scored
            g("c", "youtube", "returns", is_relevant="yes", sip_action="paused", belief_at_action="I thought X"),  # engine rejected it
            g("d", "play", "sip_or_mf", is_relevant="")]                                    # unlabelled: skipped
    engine = {"a": {"relevant": True, "rec": rec}, "b": {"relevant": True, "rec": rec}, "c": {"relevant": False, "rec": None}}
    cells, dis = golden.compare(gold, engine)
    assert {c["field"] for c in cells if c["source"] == "youtube" and c["group"] == "sip_or_mf"} == {"is_relevant"}
    r = golden.rates(cells)
    assert r["is_relevant"]["overall"] == (1, 3) and r["sip_action"]["overall"] == (1, 2)
    assert golden.rates(cells, "source")["sip_action"] == {"play": (1, 1), "youtube": (0, 1)}
    assert golden.rates(cells, "group")["is_relevant"] == {"stop_or_fail": (1, 1), "sip_or_mf": (0, 1), "returns": (0, 1)}
    belief = [d for d in dis if d["field"] == "belief_at_action"]
    assert [(d["item_id"], d["mine"], d["engine"]) for d in belief] == [("a", "null", "stated"), ("c", "stated", "(not extracted)")]
    assert not any(c["field"] == "age_stated" for c in cells)                    # blank presence cells are not scored
    assert any(d["item_id"] == "c" and d["field"] == "sip_action" and d["engine"] == "(not extracted)" for d in dis)


def cell(field, mine, engine, source="play", group="sip_or_mf"):
    return {"field": field, "mine": mine, "engine": engine, "agree": mine == engine, "source": source, "group": group}


def test_split_rates_separate_stated_agreement_from_false_stated_and_ignore_booleans():
    cells = [cell("sip_action", "stopped", "stopped"), cell("sip_action", "paused", "stopped", source="reddit"),
             cell("sip_action", "not_stated", "not_stated"), cell("sip_action", "not_stated", "continuing"),
             cell("sip_action", "not_stated", "(not extracted)"),                 # engine never ran: not a hallucination
             cell("journey_stage", "unknown", "first_3_months"), cell("is_relevant", True, True)]
    s = golden.split_rates(cells)
    assert s["stated"]["sip_action"]["overall"] == (1, 2)
    assert s["false_stated"]["sip_action"]["overall"] == (1, 3)
    assert s["false_stated"]["journey_stage"]["overall"] == (1, 1)
    assert "is_relevant" not in s["stated"] and "is_relevant" not in s["false_stated"]
    assert golden.split_rates(cells, "source")["stated"]["sip_action"] == {"play": (1, 1), "reddit": (0, 1)}
    assert golden.rates(cells)["sip_action"]["overall"] == (2, 5)      # overall is inflated by agreeing not_stated


def test_too_few_stated_labels_are_not_shown_as_a_percentage():
    assert golden.pct((1, 2), golden.MIN_STATED) == "too few to score (n=2)"
    assert golden.pct((2, 3), golden.MIN_STATED) == "67% (2/3)"
    assert golden.pct((0, 0)) == "-"
