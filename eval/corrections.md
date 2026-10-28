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
- Result: ___ of 40 are a person's own SIP experience (___%).
- Decision: ___
- Date and who decided: ___

## 0b. Belief examples in the extraction prompt (prompt-design decision, 2026-10-29, before any extraction ran)

- What the AI wrote: worked examples with SIP-specific beliefs ("I thought SIP gives fixed returns like an FD, so I stopped",
  "I knew the first year would be flat, so I kept going", "he thought the money was gone") and an expectation example
  ("socha tha FD se zyada milega").
- What I changed it to: placeholder shapes with no SIP content ("I thought [X], so I [action]" has a belief; "[Event] happened,
  so I [action]" and "I am [emotion], so I [action]" do not). The rule that an action or emotion alone is not a belief is kept.
- Why: concrete domain beliefs in the prompt could seed the very findings the engine is meant to discover (the model would be
  primed to see FD-like expectations or paper-loss beliefs). The examples should teach the form of a stated belief, not its content.

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
