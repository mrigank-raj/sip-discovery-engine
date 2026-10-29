# AI Evidence Log

Generated 2026-10-29T19:20:58+00:00 by `engine.cli evidence-log`. Every number below is read from the database or the eval files at that time. Counts are mentions in a sample of public posts, not population rates.

## 1. Sources and volume per stage

| source | collected | prefiltered | classified | relevant | extracted | no_sip_action_stated | analysed |
|---|---|---|---|---|---|---|---|
| appstore | 1272 | 268 | 268 | 160 | 160 | 20 | 140 |
| play | 23037 | 1705 | 1705 | 726 | 537 | 105 | 432 |
| reddit | 547 | 251 | 251 | 119 | 16 | 1 | 15 |
| tradingqna | 742 | 411 | 411 | 152 | 17 | 6 | 11 |
| youtube | 2928 | 1045 | 1045 | 495 | 17 | 2 | 15 |
| **total** | 28526 | 3680 | 3680 | 1652 | 747 | 134 | 613 |

Relevance rate among classified items: 45% (1652 of 3680). Classified so far: 3680 of 3680 prefiltered; extracted 747 of 1652 relevant.

Collection method and compliance per source (from config/sources.yaml):

- **play** (on): python google-play-scraper (v1.2.7), country=in, sort newest, no rating filter (positive reviews matter here) Compliance: Public store pages; scraping is against Google's general terms, so keep volume modest and disclose the method.
- **appstore** (on): iTunes customer-reviews RSS (JSON), India store only Compliance: Official public feed.
- **youtube** (on): YouTube Data API v3 (official), regionCode=IN, English and Hindi videos Compliance: Official API; follow YouTube API Services terms; do not keep cached data longer than allowed.
- **tradingqna** (on): Discourse public JSON. Category listings /c/{slug}/{id}.json?page=N, then /t/{id}.json per topic. One request every 2 seconds.
- **reddit** (on): Apify actor automation-lab/reddit-scraper Compliance: Direct scraping is against Reddit's rules. Decision made by the project owner to use Apify at small, non-commercial scale, only when run by hand. Disclose this in the write-up.

- **hackernews** (off): Not where Indian retail SIP investors talk; collector removed.
- **stackexchange** (off): Not where Indian retail SIP investors talk; collector removed.
- **google_community** (off): Not relevant to this product; collector removed.

## 2. Models and prompt versions

- Relevance: `gemini-3.5-flash-lite`; extraction: `gemini-3.5-flash-lite`; insight wording: `gemini-3.5-flash` (fallback `gemini-3.5-flash-lite`). Budget: $0, free tier only.
- Current versions: `{"taxonomy": "v3", "taxonomy_sha": "dfee6caa", "prompt_relevance_sha": "b2c0f1cf", "prompt_relevance_version": "relevance-v5", "prompt_extraction_sha": "11b2f936"}`

Model-backed runs recorded in the `runs` table:

| stage | started | model | taxonomy | relevance prompt | extraction prompt sha | counts |
|---|---|---|---|---|---|---|
| relevance | 2026-10-29T13:16 | gemini-3.5-flash-lite | v2 | 13ee9458 | 11b2f936 | {'classified': 20, 'requests': 1, 'retries': 0, 'prompt_tokens': 3190, 'output_tokens': 91 |
| extract | 2026-10-29T13:17 | gemini-3.5-flash-lite | v2 | 13ee9458 | 11b2f936 | {"saved": 16, "requests": 2, "retries": 0, "prompt_tokens": 7494, "output_tokens": 4836} |
| relevance | 2026-10-29T13:17 | gemini-3.5-flash-lite | v2 | 13ee9458 | 11b2f936 | {} |
| relevance | 2026-10-29T13:43 | gemini-3.5-flash-lite | v2 | 13ee9458 | 11b2f936 | {'classified': 13, 'requests': 1, 'retries': 0, 'prompt_tokens': 2182, 'output_tokens': 58 |
| relevance | 2026-10-29T13:54 | gemini-3.5-flash-lite | v3 | relevance-v3 | 11b2f936 | {'classified': 20, 'requests': 1, 'retries': 0, 'prompt_tokens': 2959, 'output_tokens': 90 |
| relevance | 2026-10-29T14:26 | gemini-3.5-flash-lite | v3 | relevance-v4 | 11b2f936 | {'classified': 20, 'requests': 1, 'retries': 0, 'prompt_tokens': 3171, 'output_tokens': 11 |
| relevance | 2026-10-29T14:27 | gemini-3.5-flash-lite | v3 | relevance-v4 | 11b2f936 | {} |
| relevance | 2026-10-29T14:37 | gemini-3.5-flash-lite | v3 | relevance-v5 | 11b2f936 | {'classified': 20, 'requests': 1, 'retries': 0, 'prompt_tokens': 3241, 'output_tokens': 11 |
| relevance | 2026-10-29T14:38 | gemini-3.5-flash-lite | v3 | relevance-v5 | 11b2f936 | {} |
| relevance | 2026-10-29T15:15 | gemini-3.5-flash-lite | v3 | relevance-v5 | 11b2f936 | {'classified': 2660, 'requests': 148, 'retries': 20, 'prompt_tokens': 390977, 'output_toke |
| extract | 2026-10-29T18:51 | gemini-3.5-flash-lite | v3 | relevance-v5 | 11b2f936 | {} |
| cluster | 2026-10-29T19:05 | gemini-3.5-flash-lite | v3 | relevance-v5 | 11b2f936 | {"clusters": 24, "items": 425} |
| extract | 2026-10-29T19:08 | gemini-3.5-flash-lite | v3 | relevance-v5 | 11b2f936 | {"saved": 747, "requests": 23, "retries": 0, "prompt_tokens": 72687, "output_tokens": 2604 |

## 3. Extraction quality: validator rejections and review

Every quote is checked to appear word for word in the text of the item it is attached to (NFC, zero-width characters removed, smart quotes made plain, whitespace collapsed). A record that fails is retried once, alone, with the error; if it fails again it goes to `needs_review` and is not used.

- Extracted and valid: 747; sent to review after the retry: 5 (0.7% of attempted)
- Items with a stated belief (candidate, not finding): 5 of 747; null rate 99%
  - review reason example: severity 'acted' needs a paused, reduced, stopped or redeemed sip_action, got 'switched_platform'
  - review reason example: severity 'acted' needs a paused, reduced, stopped or redeemed sip_action, got 'started'
  - review reason example: evidence_quotes must hold 1 to 3 quotes, got 0
  - review reason example: severity 'acted' needs a paused, reduced, stopped or redeemed sip_action, got 'started'
  - review reason example: evidence_quotes must hold 1 to 3 quotes, got 0

## 4. Golden set

From `eval/results/golden_relevance.md`:

# Golden set: relevance only

Stratified for coverage, not proportional to volume; 20 items, so every rate rests on very few items.

- Agreement: 70% (14/20)
- Engine said relevant and you agreed (precision): 50% (6/12)
- You said relevant and the engine agreed (recall): 100% (6/6)
- By source: appstore 100% (4/4); play 50% (2/4); reddit 75% (3/4); tradingqna 50% (2/4); youtube 75% (3/4)
- By prefilter group: stop_or_fail 60% (3/5); returns 80% (8/10); sip_or_mf 60% (3/5)

#### Relevance, item by item

| # | source | group | you | engine | engine family | whose | language | confidence |
|---|---|---|---|---|---|---|---|---|
| G1 | appstore | returns | no | no | other | no_one | english | high |
| G2 **x** | play | returns | no | yes | sip_or_mf_journey | own | english | high |
| G3 **x** | reddit | returns | no | yes | sip_or_mf_journey | named_person | english | high |
| G4 | tradingqna | returns | no | no | other | no_one | english | high |
| G5 | youtube | returns | yes | yes | sip_or_mf_journey | own | hinglish | high |
| G6 | appstore | sip_or_mf | no | no | other | no_one | english | high |
| G7 | play | sip_or_mf | no | no | other | no_one | english | high |
| G8 | reddit | sip_or_mf | no | no | other | someone_else | english | high |
| G9 **x** | tradingqna | sip_or_mf | no | yes | sip_or_mf_journey | own | english | medium |
| G10 **x** | youtube | sip_or_mf | no | yes | sip_or_mf_journey | own | english | high |
| G11 | appstore | stop_or_fail | yes | yes | sip_or_mf_journey | named_person | english | high |
| G12 **x** | play | stop_or_fail | no | yes | sip_or_mf_journey | own | english | medium |
| G13 | reddit | stop_or_fail | yes | yes | sip_or_mf_journey | own | english | high |
| G14 **x** | tradingqna | stop_or_fail | no | yes | sip_or_mf_journey | own | english | medium |
| G15 | youtube | stop_or_fail | yes | yes | sip_or_mf_journey | own | hinglish | high |
| G16 | appstore | returns | no | no | app_bug_or_support | no_one | english | high |
| G17 | play | returns | no | no | other | no_one | english | high |
| G18 | reddit | returns | yes | yes | sip_or_mf_journey | own | english | high |
| G19 | tradingqna | returns | no | no | other | no_one | english | high |
| G20 | youtube | returns | yes | yes | sip_or_mf_journey | own | english | high |

#### Relevance disagreements

### G2 (play, returns): you no, engine yes as `sip_or_mf_journey` (high confidence)

> Your app shows me only historic XIRR returns of entire MF portfolio but not able to see my last 3M, 6M, 1Y, 3Y XIRR returns in MF . Kindly add this like other apps Zerodha, Groww.

### G3 (reddit, returns): you no, engine yes as `sip_or_mf_journey` (high confidence)

> Also honorable mention is the GST charged on each premium payment. Conveniently, nobody talks about that, and not even in your calculations. Add it, IIRC 4.5% on first premium payment, and 2.5% on subsequent payments, and your XIRR drops by 2-3% more.

### G9 (tradingqna, sip_or_mf): you no, engine yes as `sip_or_mf_journey` (medium confidence)

> [Feature request] Need option to select only mutual funds in Console
>
> Currently we see option to exclude the mutual funds in “Holdings” page which enables to select just stocks.
>
> Similarly I am looking for option to select just MF holdings for sector wise allocation and stocks they are holding.

### G10 (youtube, sip_or_mf): you no, engine yes as `sip_or_mf_journey` (high confidence)

> DSP Small Cap Fund - Direct Plan - Growth

### G12 (play, stop_or_fail): you no, engine yes as `sip_or_mf_journey` (medium confidence)

> if you r using groww for only mf don't upgrade to dmat. otherwise u will redeem your money only thg Grow. that fund's app redeem money more faster than grow. grow takes 2 day more time

### G14 (tradingqna, stop_or_fail): you no, engine yes as `sip_or_mf_journey` (medium confidence)

> Does it give detailed  CG statement with for each quarter as mandated by tax forms?



## 5. Corrections log



Cases where a person rejected or corrected AI output, and why. Filled in by hand. `engine.cli evidence-log` copies this file into
`docs/evidence_log.md` as it is.

### 0. Prefilter for YouTube comments and TradingQ&A replies (decision record)

- Problem: matching on the video or topic title passed 100% of YouTube comments, because every title is about SIPs by design.
- Proposed fix: match on the comment or reply text only. On 2026-10-29 this dropped 1,965 of 2,928 YouTube comments and 224 of
  473 TradingQ&A replies.
- Check: 40 dropped YouTube comments sampled at random (seed 20261029) into `eval/prefilter_dropped_sample.csv`, hand-labelled.
- Rule agreed beforehand: under about 10% own-SIP-experience keeps text-only; above that adds a second pass for comments under
  SIP-themed titles matching action verbs (band, ruk, rok, chhod, pause, stop, continue, chal raha, redeem, nikaal).
- Result: labelled 20 of the 40, stopping once the threshold was crossed; 12 of those 20 marked yes.
- Decision: Partial sample check (20/40) suggested the text-only rule drops SIP-related comments; chose the conservative verb pass to avoid losing Hinglish narratives. Labels were quick and not a precise rate.
- Applied: text-only matching for comments and replies, plus the verb pass for comments and replies (YouTube, TradingQ&A, Reddit)
  whose video or thread title names SIPs or mutual funds. The verb pass let in 87 more items (YouTube 82, Reddit 4, TradingQ&A 1);
  they are tagged `verb_pass` in `prefilter_groups`. The golden set was drawn before this pass, so it holds no verb-pass items.
- Date and who decided: 2026-10-29, project owner.

### 0b. Belief examples in the extraction prompt (prompt-design decision, 2026-10-29, before any extraction ran)

- What the AI wrote: worked examples with SIP-specific beliefs ("I thought SIP gives fixed returns like an FD, so I stopped",
  "I knew the first year would be flat, so I kept going", "he thought the money was gone") and an expectation example
  ("socha tha FD se zyada milega").
- What I changed it to: placeholder shapes with no SIP content ("I thought [X], so I [action]" has a belief; "[Event] happened,
  so I [action]" and "I am [emotion], so I [action]" do not). The rule that an action or emotion alone is not a belief is kept.
- Why: concrete domain beliefs in the prompt could seed the very findings the engine is meant to discover (the model would be
  primed to see FD-like expectations or paper-loss beliefs). The examples should teach the form of a stated belief, not its content.

### 0c. Relevance rule ambiguity exposed by golden set (2026-10-29)

- **First score.** Relevance on the 20 golden items, prompt v2 as first written: agreement 65% (13/20), precision 60% (9/15),
  recall 90% (9/10). Six items the engine called relevant were labelled not relevant; one labelled relevant was called `other`.
- **My own labels were inconsistent.** Reading the disagreements showed that I had applied two different rules:
  - G1 and G2 (requests for better XIRR views in INDmoney and in a Play app) were labelled yes, while G9 (a request for an MF-only
    filter in Console) and G16 ("xirr functionality works sometimes") were labelled no. All four are feature requests or app
    complaints about mutual-fund features with no SIP experience stated.
  - G19 (a reply explaining to another user that CAGR is shown net of the expense ratio) was labelled yes, while G8 (a reply
    advising someone else to start a liquid-fund SIP) was labelled no. Both are explanations or advice to someone else.
- **Decision order.** I first chose the rule, then applied it to all 20 items, and only then changed labels:
  - Rule (strict): relevant only if the writer states an action, experience, worry or decision about their own (or a named
    person's) SIP or mutual-fund holdings. Not relevant: feature requests, fund names alone, app-vs-app comparisons, app
    complaints with no SIP experience, and explanations or advice to someone else.
  - Under it, four labels changed from yes to no, and none from no to yes:
    - G1 (App Store, INDmoney): asks for XIRR on short holdings and a consolidated portfolio view. A feature request.
    - G2 (Play): asks for 3M / 6M / 1Y / 3Y XIRR "like other apps Zerodha, Groww". A feature request and app comparison.
    - G14 (TradingQ&A): "Does it give detailed CG statement ... as mandated by tax forms?" A question about a feature, with no
      SIP experience stated.
    - G19 (TradingQ&A): an explanation of CAGR and the expense ratio to another user. An explanation to someone else.
  - G1 and G2's sip_action and belief labels were cleared, as they are no longer relevant items.
  - Result: 6 relevant (G5, G11, G13, G15, G18, G20), 14 not relevant.
- **This relabelling happened after seeing engine output.** It is an adjudication of an ambiguous rule, not fitting the labels
  to the engine:
  - The rule was chosen first and then applied to every one of the 20 items, not only to the disagreements.
  - Against the engine's prompt-v2 answers, 3 of the 4 changes moved away from the engine (G1, G2 and G14 had been called
    relevant by the engine and are now labelled not relevant, so they became disagreements) and 1 moved towards it (G19).
    Scored against the same v2 answers, the relabel alone lowered agreement from 65% (13/20) to 55% (11/20), precision from
    60% to 40% (6/15), and left recall at 100% (6/6). The relabel made the engine look worse, not better.
  - The disagreements exposed that the labels themselves followed two different rules (see above); one rule had to be picked.
  - Remaining risk: the rule was chosen knowing which kinds of item caused disagreements, so any score after the prompt change
    is optimistic. A fresh sample labelled under the strict rule from the start would be a cleaner test.
- **Then the prompt was tightened** (relevance prompt v3, next step) to state the strict rule and the five not-relevant cases.
- **Scores on the same 20 items (strict labels), each prompt run once:**

  | prompt | agreement | precision | recall | disagreements |
  |---|---|---|---|---|
  | v3 (strict rule in the prompt) | 80% (16/20) | 60% (6/10) | 100% (6/6) | G3, G8, G12, G14 (all engine yes) |
  | v4 (adds `whose_holdings`; relevant = sip_or_mf_journey AND own or named_person, decided in code) | 80% (16/20) | 67% (4/6) | 67% (4/6) | G3, G14 (engine yes); G5, G15 (engine no) |

  v4 fixed the advice-to-others errors (G8, G12) but lost two Hinglish questions phrased as "we" / "agar ... kar rahe hai"
  (G5, G15), which it read as `someone_else`. Decision (owner, 2026-10-29): accept v4 and stop tuning on these 20 items;
  no holdout due to time.
- **v4 broke rule (a) for Hinglish/hypothetical questions; fixed in v5.** Owner's fix (2026-10-29, framed as restoring rule (a),
  "a person asking about their own SIP is relevant", not as tuning): `whose_holdings` = own when the writer asks about or
  describes their own situation using "we / hum / agar hum", "if I", hypotheticals or questions ("what if my SIP...", "can we
  restart"). The full v4 run was stopped at about 400 of 3,660 items and is restarted from scratch under v5. Golden set, run once:

  | prompt | agreement | precision | recall | disagreements |
  |---|---|---|---|---|
  | v5 | 70% (14/20) | 50% (6/12) | 100% (6/6) | G2, G3, G9, G10, G12, G14 (all engine yes) |

  v5 recovered G5 and G15 but lost G2, G9, G10 and G12, which v4 had right: feature requests, a fund name alone and an app
  comparison now come back as `own`. The example "can we restart" is close to G15's own wording, so this rerun is not an
  independent test of the fix. Per the owner's instruction, the full run restarts under v5 regardless of this score.

### 1. Correction

- Item or output:
- What the AI said:
- What I changed it to:
- Why:

### 2. Correction

- Item or output:
- What the AI said:
- What I changed it to:
- Why:

### 3. Correction (optional)

- Item or output:
- What the AI said:
- What I changed it to:
- Why:

### Summary spot-check (after golden-set labelling)

`golden-score` prints 10 engine summaries next to their original text only after your labels are scored, so the labelling stays
blind. For each, note whether the summary is faithful:

| item_id | faithful? (y/n) | note |
|---|---|---|


## 6. Known biases and limitations



Copied word for word into `docs/evidence_log.md` by `engine.cli evidence-log`. Edit here, not in the generated log.

- Golden-set relevance score was measured on the same 20 items used to tune the prompt (v2→v4), so it is optimistic. No separate holdout due to time.
- v5 trades precision (50% on golden) for recall (100%); the analysis layer excludes items with no stated SIP action, so false positives don't reach findings.
- Relevance-v5 (the version used for the full run) on the golden set: 70% agreement, 50% precision, 100% recall (6 of 6
  relevant items found, 12 called relevant). Errors run towards including too much: feature requests, a fund name and app
  comparisons. Downstream, such items mostly extract as `sip_action=not_stated`; counts of actions and reasons are less affected
  than the relevant-item total. (v4 had 80% / 67% / 67% but missed Hinglish questions about the writer's own SIP.)
- Golden set: 20 items hand-labelled for relevance by the author. Extraction fields were not hand-labelled at scale (2 items); extraction quality is guarded by the verbatim validator and is reported via validator rejection and review rates, not golden-set agreement.
- **Golden set is stratified for coverage, not proportional to volume.** Its 20 items are spread evenly across source x prefilter
  group (4 per source, 1 or 2 per cell), so a small stratum such as App Store "returns" (18 items in the pool) gets as many items
  as Play "sip_or_mf" (1,439). Agreement rates are reported overall, per source and per prefilter group; the overall rate is not a
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
- **The relevance rate in the budget was an assumption** (40%); the real rate is computed from the data in section 1 of the
  evidence log each time it is generated.
- **Beliefs are candidates, not findings (Option C).** The engine outputs only beliefs the person states, with a verbatim quote;
  they are grouped by hand and validated through survey open answers and follow-up messages, not by the engine.
- **Public posts skew to people with something to say,** usually a complaint; quiet continuers and quiet drop-offs post least.
- **Counts are mentions in a sample**, not how many investors have a problem.

