import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from engine import extract  # noqa: E402

TAX = extract.taxonomy()

# play:4abb04a9-f38e-4c03-a5cf-e0c35b00eb18, copied word for word from the collected data
HINGLISH_PENALTY = 'bahut kharab sip ke liye 472 ka penalty marta hai 100 ki sip miss hua to aur koi reminder ya usko pement ka option bhi baad me deta hai'
# play:3775c7a2-04ff-487f-a7f3-6501003ff588, copied word for word from the collected data
HINGLISH_QUESTION = 'kon kon se din SIP update karte ho aap? Daily Updates nahi hota to App bandh kar dijiye or Notification Bhej dijiye na???'
# play:769ac3fb-3d10-4f83-b477-28f0d396adbc, copied word for word from the collected data
HINGLISH_CONTINUER = 'Ekdum smooth experience hai! App ka interface bahut clean aur simple hai, jiski wajah se mutual funds aur SIP mein invest karna bahut easy ho gaya hai. Beginners ke liye ye best app hai. 5 stars!'
# play:2abb5638-377e-46ee-a7f6-8d008fb9dd9f, copied word for word from the collected data
DEVANAGARI = 'SIP का पैसा नही आया एकाउंट में GROWW ने अपने एकाउंट में ले लिया FAKE आप है GROWW isme koe sip mat karna'


def rec(**kw):
    base = {"i": 0, "summary": "s", "secondhand": False, **{n: "not_stated" for n in extract.ENUMS},
            "journey_stage": "unknown", "severity": "unclear", "confidence": "medium", "expectation_at_start": None,
            "belief_at_action": None, "belief_quote": None, "age_stated": None, "evidence_quotes": []}
    base["outside_app_behaviour"] = "none_stated"
    return {**base, **kw}


def test_hinglish_quotes_validate_verbatim_and_paraphrases_fail():
    assert extract.validate(rec(sip_action="instalment_failed", evidence_quotes=["472 ka penalty marta hai 100 ki sip miss hua"]),
                            HINGLISH_PENALTY, TAX) == []
    assert extract.validate(rec(evidence_quotes=["Daily Updates nahi hota to App bandh kar dijiye"]), HINGLISH_QUESTION, TAX) == []
    assert extract.validate(rec(sip_action="continuing", evidence_quotes=["mutual funds aur SIP mein invest karna bahut easy ho gaya hai"]),
                            HINGLISH_CONTINUER, TAX) == []
    errs = extract.validate(rec(evidence_quotes=["472 ka penalty lagta hai jab sip miss ho"]), HINGLISH_PENALTY, TAX)
    assert any("not verbatim" in e for e in errs)


def test_devanagari_quote_survives_nfd_zero_width_and_smart_quotes():
    q = "SIP का पैसा नही आया एकाउंट में"
    assert extract.validate(rec(evidence_quotes=[q]), DEVANAGARI, TAX) == []
    assert extract.validate(rec(evidence_quotes=[unicodedata.normalize("NFD", q)]), DEVANAGARI, TAX) == []
    assert extract.validate(rec(evidence_quotes=["SIP का पैसा न\u200dही आया"]), DEVANAGARI, TAX) == []
    assert extract.norm("it’s “fine”") == extract.norm("it's \"fine\"")
    assert extract.validate(rec(evidence_quotes=["SIP का पैसा वापस आया"]), DEVANAGARI, TAX) != []


def test_a_quote_from_another_item_in_the_same_batch_is_rejected():
    items = [{"source": "play", "title": None, "text": HINGLISH_PENALTY}, {"source": "play", "title": None, "text": HINGLISH_CONTINUER}]
    quote_a = "472 ka penalty marta hai"

    def fake(model, prompt, schema, **kw):  # the model attaches item 0's quote to item 1, on the first pass and the retry
        if prompt.count("### ") == 1:
            return [rec(i=0, evidence_quotes=[quote_a])]
        return [rec(i=0, evidence_quotes=[quote_a]), rec(i=1, evidence_quotes=[quote_a])]

    records, review = extract.extract(items, "m", generate=fake)
    assert records[0] is not None and records[1] is None
    assert review and review[0][0] == 1 and "not verbatim" in review[0][1]


def test_belief_needs_its_quote_and_vice_versa():
    q = "isme koe sip mat karna"
    assert extract.validate(rec(evidence_quotes=[q], belief_at_action="Thought the money was taken", belief_quote=None), DEVANAGARI, TAX)
    assert extract.validate(rec(evidence_quotes=[q], belief_at_action=None, belief_quote=q), DEVANAGARI, TAX)
    assert extract.validate(rec(evidence_quotes=[q], belief_at_action="b", belief_quote="made up belief"), DEVANAGARI, TAX)
    assert extract.validate(rec(evidence_quotes=[q], belief_at_action="b", belief_quote=q), DEVANAGARI, TAX) == []


def test_rules_on_enums_quote_count_and_acted():
    q = "isme koe sip mat karna"
    assert any("sip_action" in e for e in extract.validate(rec(sip_action="quit", evidence_quotes=[q]), DEVANAGARI, TAX))
    assert any("1 to 3" in e for e in extract.validate(rec(), DEVANAGARI, TAX))
    assert any("acted" in e for e in extract.validate(rec(severity="acted", sip_action="instalment_failed", evidence_quotes=[q]), DEVANAGARI, TAX))
    assert extract.validate(rec(severity="acted", sip_action="stopped", evidence_quotes=[q]), DEVANAGARI, TAX) == []


def test_store_review_platform_comes_from_the_app_and_buckets_from_the_action(tmp_path, monkeypatch):
    from engine import store
    monkeypatch.setenv("AUTHOR_HASH_SALT", "t")
    db = store.connect(store.init_db(tmp_path / "t.db"))
    extract.save(db, "play:x", rec(sip_action="considering_stopping", platform="not_stated", evidence_quotes=["q"]), "m", "r", "v2", "play", "coin")
    row = db.execute("SELECT platform, contrast_bucket, has_belief FROM extractions").fetchone()
    assert tuple(row) == ("zerodha", "considering", 0)


def test_prompt_marks_thread_starter_as_context_only_and_injects_definitions():
    p = extract.build_prompt([{"source": "youtube", "title": "T", "text": "reply text", "starter": "the original post"}], TAX)
    assert "context only, never quote" in p and "the original post" in p and "- instalment_failed:" in p and "{sip_action}" not in p
