import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from engine.collectors.youtube import title_ok  # noqa: E402


def test_title_filter_keeps_sip_videos_and_drops_trading_and_shorts():
    assert title_ok("Should I stop my SIP? Market fall explained")
    assert title_ok("Groww mutual fund SIP kaise kare")
    assert title_ok("SIP बंद करें या नहीं")
    assert not title_ok("Best F&O strategy for SIP of profits")
    assert not title_ok("SIP returns in 30 sec #shorts")
    assert not title_ok("Top 5 stocks to buy now")
