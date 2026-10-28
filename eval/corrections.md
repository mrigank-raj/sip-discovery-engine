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
