# Known biases and limitations

Copied word for word into `docs/evidence_log.md` by `engine.cli evidence-log`. Edit here, not in the generated log.

- **Golden set is stratified for coverage, not proportional to volume.** Its 35 items are spread evenly across source x prefilter
  group (about 3 per cell), so a small stratum such as App Store "returns" (18 items in the pool) gets as many items as Play
  "sip_or_mf" (1,439). Agreement rates are reported overall, per source and per prefilter group; the overall rate is not a
  corpus-wide accuracy, and per-cell rates rest on very few items.
- **Clusters reflect the model's paraphrase, not the user's words.** Clustering embeds the English `summary` field written by the
  extraction model, because the local embedding model is English-only and handles Hinglish poorly. 10 summaries are
  spot-checked against the originals after golden-set scoring (see corrections).
- **Groww-specific store volume vs platform-agnostic sources.** Play and App Store reviews are about one app each (mostly Groww);
  YouTube, TradingQ&A and Reddit discuss SIPs across platforms.
- **TradingQ&A is Zerodha's forum** and skews to experienced investors and Coin users rather than first-timers.
- **Time windows differ.** Play covers about 12 months (newest 60,000 Groww English reviews reach back to 2025-11-08); the other
  sources cover 24 months.
- **Reddit was rate-limited and is thin.** Collected on 2026-10-29 through Apify (free plan, $0.55 of the $5 monthly credit, no
  money spent). The first run used site search (24 searches); Reddit answered most of them with HTTP 429, so only
  r/IndiaInvestments came back, and **202 of the 401 items it returned were older than the 24-month window** (paid for, then
  dropped on insert). One retry used keyword-filtered `/new/` listings instead of search, one run per subreddit, 90 seconds apart;
  it was not rate-limited, but listings reach only the newest posts, so those three subreddits cover about the last 11 days.
  Retrieved (stored, after the window and length checks):

  | subreddit | posts | comments | prefilter pass (posts / comments) | date span | Groww mentions |
  |---|---|---|---|---|---|
  | r/IndiaInvestments (search) | 32 | 137 | 21 / 42 | 2024-11-11 to 2026-10-29 | 1 |
  | r/mutualfunds (listing) | 39 | 191 | 39 / 84 | 2026-10-18 to 2026-10-29 | 6 |
  | r/personalfinanceindia (listing) | 16 | 89 | 16 / 35 | 2026-10-26 to 2026-10-29 | 0 |
  | r/IndianStockMarket (listing) | 7 | 36 | 4 / 6 | 2026-10-28 to 2026-10-29 | 13 |

  So Reddit mostly reflects one fortnight of market mood, and its comments were collected best-effort (the actor reported
  "Comment session blocked" on some threads). Treat Reddit counts as illustrative, not comparable with the other sources.
- **The relevance rate in the budget was an assumption** (40%); the real figure from the run replaces it here: ___.
- **Beliefs are candidates, not findings (Option C).** The engine outputs only beliefs the person states, with a verbatim quote;
  they are grouped by hand and validated through survey open answers and follow-up messages, not by the engine.
- **Public posts skew to people with something to say,** usually a complaint; quiet continuers and quiet drop-offs post least.
- **Counts are mentions in a sample**, not how many investors have a problem.
