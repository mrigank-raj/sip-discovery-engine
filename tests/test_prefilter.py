import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from engine.prefilter import groups_hit, passes  # noqa: E402


def test_store_reviews_need_a_sip_or_stop_term():
    assert passes("play", None, "Started my first SIP here, very easy")
    assert passes("play", None, "sip band kar diya, paisa kat gaya bina bataye")
    assert passes("play", None, "Autopay mandate failed twice this month")
    assert passes("play", None, "म्यूचुअल फंड में एसआईपी बंद नहीं हो रहा")
    assert not passes("play", None, "F&O charges are too high, worst app")
    assert not passes("play", None, "loss me hu bhai, stocks gir gaye")       # returns word alone: stocks noise
    assert not passes("appstore", None, "Great app for trading")


def test_words_inside_other_words_do_not_match():
    assert groups_hit(None, "gossip and navigation and mfg date") == []


def test_forums_pass_on_any_group_and_groups_are_reported():
    assert passes("youtube", "SIP returns", "return nahi aa raha 2 saal se")
    assert groups_hit("", "NAV dropped, I paused my SIP") == ["stop_or_fail", "returns", "sip_or_mf"]


def test_verb_pass_lets_in_comments_under_sip_titles_only():
    assert passes("youtube", None, "3 saal se chal raha hai, band nahi karunga", context_title="Should I stop my SIP?")
    assert passes("youtube", None, "I will continue no matter what", context_title="SIP returns explained")
    assert not passes("youtube", None, "I will continue no matter what", context_title="Top 5 stocks to buy")  # not a SIP title
    assert not passes("youtube", None, "Great video sir, thanks", context_title="Should I stop my SIP?")      # no action verb
    assert not passes("youtube", None, "the band played well", context_title=None)
    assert not passes("play", None, "stopped working after update", context_title="SIP")                    # store reviews: no verb pass
