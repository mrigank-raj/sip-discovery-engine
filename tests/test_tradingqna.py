import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from engine.collectors import tradingqna as tq  # noqa: E402


def test_posts_become_items_with_the_first_post_as_thread_and_html_stripped():
    t = {"post_stream": {"posts": [
        {"post_number": 1, "cooked": "<p>Should I <b>stop</b> my SIP?</p>", "created_at": "2025-03-01T00:00:00Z", "username": "a"},
        {"post_number": 3, "cooked": "<p>No, keep going.</p>", "created_at": "2025-03-02T00:00:00Z", "username": "b"}]}}
    first, reply = tq.post_items((42, "stop-sip", "Stop SIP?"), t)
    assert (first["item_id"], first["thread_id"], first["parent_id"]) == ("tradingqna:42", "tradingqna:42", None)
    assert first["text"] == "Stop SIP?\n\nShould I stop my SIP?"
    assert (reply["item_id"], reply["parent_id"], reply["text"]) == ("tradingqna:42-3", "tradingqna:42", "No, keep going.")
    assert reply["url"] == "https://tradingqna.com/t/stop-sip/42/3"


def test_title_filter():
    assert tq.TITLE.search("Whats the easiest way to stop sip in regular fund?")
    assert not tq.TITLE.search("Nifty options expiry strategy")
