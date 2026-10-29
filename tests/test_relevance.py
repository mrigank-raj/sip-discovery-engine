import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from engine import relevance  # noqa: E402

ITEMS = [{"source": "play", "title": None, "text": f"sip band kar diya {i}"} for i in range(5)]


def fake_generate(model, prompt, schema):
    """Answers every item except number 3 in the first pass; answers a one-item retry normally."""
    n = prompt.count("### ")
    ids = range(n) if n == 1 else [i for i in range(n) if i != 3]
    return [{"i": i, "language": "hinglish", "problem_family": "sip_or_mf_journey", "confidence": "high"} for i in ids]


def test_prompt_contains_definitions_and_items_and_no_placeholders():
    p = relevance.build_prompt(ITEMS[:2])
    assert "- sip_or_mf_journey:" in p and "- hinglish:" in p and "### 0 | source: play" in p and "### 1 |" in p
    assert "{" not in p.split("Items:")[0]


def test_hinglish_and_hindi_are_classes_not_rejections():
    assert {"hinglish", "hindi"} <= set(relevance.schema()["items"]["properties"]["language"]["enum"])
    assert "not_english" not in relevance.schema()["items"]["properties"]["language"]["enum"]


def test_classify_retries_items_the_model_skipped():
    out = relevance.classify(ITEMS, "m", batch=5, generate=fake_generate)
    assert all(o is not None for o in out) and len(out) == 5


def test_prompt_version_is_recorded_but_never_sent():
    from engine import store
    assert store.versions()["prompt_relevance_version"] == "relevance-v3"
    p = relevance.build_prompt(ITEMS[:1])
    assert "version:" not in p and "<!--" not in p and p.startswith("You classify")
    assert "Feature requests" in p and "Explanations, answers or advice to someone else" in p
