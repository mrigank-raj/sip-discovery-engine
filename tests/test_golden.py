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
