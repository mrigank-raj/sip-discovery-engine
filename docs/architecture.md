# Architecture

How the engine turns public posts into comparable, evidence-backed findings about SIP journeys.

## Principles

1. **The schema and taxonomy are the product.** Scrapers, models and the clustering library are replaceable.
2. **Every finding resolves to a verbatim quote and a link.** The validator enforces it; nothing is taken on trust from a model.
3. **Cheap before expensive.** Keyword filter, then a batched small model for relevance, then batched extraction.
4. **Models label; code counts.** Relevance, buckets, metrics, scores and confidence are decided in code from model fields.
5. **Never guess.** Every field has a not-stated value; segment fields and beliefs are filled only when the person says so.

## Pipeline

```
collect (Play in-en/in-hi, App Store India, YouTube, TradingQ&A, Reddit via Apify)
  -> raw_items (dedupe on id and content hash; usernames salted-hashed; any language kept)
  -> prefilter (English, Hinglish, Devanagari term groups; comments judged on their own text,
                plus an action-verb pass under SIP-themed titles)
  -> relevance (20 items per request): language, whose_holdings, problem_family
       relevant = sip_or_mf_journey AND whose_holdings in (own, named_person)   [code]
  -> extraction (8 items per request) -> validator -> extractions | needs_review
  -> clusters within action groups (Ward on MiniLM embeddings of the English summary; model names them)
  -> metrics, contrast, opportunity score (code) -> insight cards (model wording, code checks) -> Explorer
```

## Extraction record

One record per relevant item; enums and one-line definitions are in `config/taxonomy.yaml`.

| Field | Values / rule |
|---|---|
| summary | English sentence, model-written, used only to cluster |
| secondhand | true when about a named other person's SIP |
| investor_experience | first_time, experienced, not_stated |
| platform | groww, zerodha, indmoney, etmoney, other, not_stated (store reviews: the app reviewed, set in code) |
| journey_stage | before_start, first_3_months, months_4_to_12, after_12_months, unknown |
| sip_action | started ... switched_platform, not_stated; contrast_bucket derived in code |
| action_reason | main reason, or not_stated |
| expectation_at_start | verbatim quote or null |
| belief_at_action + belief_quote | stated belief (English paraphrase) with a verbatim quote, or both null |
| what_they_check, check_frequency | stated only; none_or_never when they say they stopped looking |
| outside_app_behaviour, emotion | stated only |
| life_stage, age_stated, income_type, source_of_money, influenced_by | stated only |
| severity | considered, acted (actually paused, reduced, stopped or redeemed), unclear |
| evidence_quotes | 1 to 3, verbatim |

## Validator (deterministic)

Rejects a record if an enum value is not in the taxonomy; any quote (evidence, expectation, belief, age) is not a substring of
the text of the item it belongs to (never another item in the batch), after NFC, removing zero-width characters, making smart
quotes plain and collapsing whitespace; a belief has no quote or a quote has no belief; `severity=acted` comes with a non-acted
action; or there are not 1 to 3 evidence quotes. A rejected record is retried once alone with the error; then it goes to
`needs_review`.

## Analysis

- **Clusters** are built inside action groups (starting, staying_in, considering, pulled_back, instalment_failed,
  switched_platform, no_action_stated), so one cluster never mixes people who stayed with people who stopped.
- **Per-cluster metrics (code):** posts, distinct threads, source spread, share acted (voluntary only), share considered,
  share with a failed instalment, journey-stage mix and concentration, segment mix where stated, share with an outside-app step.
- **Opportunity score:** 0.40 x frequency (distinct threads, min-max) + 0.30 x share acted + 0.15 x stage concentration (0 and
  flagged below 10 known-stage posts) + 0.15 x evidence strength (distinct sources, min-max). Clusters under 8 posts are not
  ranked. Scores are shown with and without Play Store reviews.
- **Contrast:** continuers (continuing, increased) vs considering (considering_stopping) vs acted (paused, reduced, stopped,
  redeemed); instalment_failed and switched_platform shown separately and kept in the metric view.
- **Candidate beliefs** are exported for grouping by hand and shown as candidates to validate, never turned into insight cards.
- **Insight cards:** detectors compute facts; a model writes the headline, interpretation and caveat; text is rejected if it uses
  a number not in the facts, overclaims a minority, or fails a second-pass check against the facts.

## Evaluation

- **Golden set:** 20 items stratified by source x prefilter group, drawn before any model ran, labelled blind by the owner for
  relevance. `golden-score` reports overall, stated-only and false-stated rates per source and per prefilter group. It was also
  used to tune the relevance prompt (v2 to v4), so its score is optimistic.
- **Extraction quality** is reported through validator rejection and review rates.
- **Versioning:** the taxonomy version, prompt version and file hashes are recorded on every model-backed run.

## Zero spend

Gemini free tier only (`config/llm.yaml`, `budget_usd: 0`), a rate limiter under the per-minute limit, and a clean stop when a
daily quota is exhausted. Apify runs carry a hard charge cap and refuse to start below a reserve of free credit.
