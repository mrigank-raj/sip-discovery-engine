# Corrections log

Cases where a person rejected or corrected AI output, and why. Filled in by hand. `engine.cli evidence-log` copies this file into
`docs/evidence_log.md` as it is.

## 0. Prefilter for YouTube comments and TradingQ&A replies (decision record)

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

## 0b. Belief examples in the extraction prompt (prompt-design decision, 2026-10-29, before any extraction ran)

- What the AI wrote: worked examples with SIP-specific beliefs ("I thought SIP gives fixed returns like an FD, so I stopped",
  "I knew the first year would be flat, so I kept going", "he thought the money was gone") and an expectation example
  ("socha tha FD se zyada milega").
- What I changed it to: placeholder shapes with no SIP content ("I thought [X], so I [action]" has a belief; "[Event] happened,
  so I [action]" and "I am [emotion], so I [action]" do not). The rule that an action or emotion alone is not a belief is kept.
- Why: concrete domain beliefs in the prompt could seed the very findings the engine is meant to discover (the model would be
  primed to see FD-like expectations or paper-loss beliefs). The examples should teach the form of a stated belief, not its content.

## 0c. Relevance rule ambiguity exposed by golden set (2026-10-29)

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

## 1. Correction

- Item or output:
- What the AI said:
- What I changed it to:
- Why:

## 2. Correction

- Item or output:
- What the AI said:
- What I changed it to:
- Why:

## 3. Correction (optional)

- Item or output:
- What the AI said:
- What I changed it to:
- Why:

## Summary spot-check (after golden-set labelling)

`golden-score` prints 10 engine summaries next to their original text only after your labels are scored, so the labelling stays
blind. For each, note whether the summary is faithful:

| item_id | faithful? (y/n) | note |
|---|---|---|
