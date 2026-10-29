# SIP Discovery Engine

Reads public feedback by Indian investors about SIPs and mutual funds (Groww first, with Zerodha Coin, INDmoney and ET Money for
contrast) and turns it into evidence for one question: **why do first-time mutual-fund investors keep, pause or stop their first
SIP?** The business metric it serves is the share of first-time investors with an active SIP 12 months after starting.

It does not assume the user problem. It collects what people say, keeps only posts about a person's own (or a named person's) SIP
or holdings, extracts structured fields backed by verbatim quotes, groups them, and compares groups in code. It costs nothing to
run: every service is on a free tier and billing is never enabled.

Read `docs/evidence_log.md` first: volumes per stage, models and prompt versions, golden-set agreement, corrections, known biases.

## Setup

Python 3.11 or newer.

```
pip install -r requirements-pipeline.txt
cp .env.example .env                 # then fill in the keys below
python -m engine.cli init-db
python -m engine.cli check-keys
```

Run every command from the project folder with `PYTHONPATH=src` set (PowerShell: `$env:PYTHONPATH="src"`).

| Key | Where (free) | Used for |
|---|---|---|
| `GEMINI_API_KEY` | Google AI Studio, no billing | relevance, extraction, cluster names, insight wording |
| `YOUTUBE_API_KEY` | Google Cloud, YouTube Data API v3 | YouTube comments |
| `APIFY_TOKEN` | Apify free plan | Reddit only, and only when you run it |
| `AUTHOR_HASH_SALT` | any random string, set once | hashing usernames; real usernames are never stored |

Gemini's free tier allows about 500 requests a day on `gemini-3.5-flash-lite`. A run that hits the limit stops cleanly and
continues from where it stopped the next time it is run. `budget` prints the request arithmetic before a run.

## The pipeline, one stage per command

| Stage | Command | Output |
|---|---|---|
| Collect | `collect play --limit 0` (play, appstore, youtube, tradingqna, reddit) | `data/engine.db` |
| Keyword prefilter | `prefilter` | pass/fail and the term group per item (English, Hinglish, Devanagari) |
| Budget | `budget` | free-tier request arithmetic for the next stages |
| Relevance | `relevance-run` | relevant = family `sip_or_mf_journey` AND holdings own or a named person's (decided in code) |
| Extract + validate | `extract-run --out data/extract_v3.json --save-db --batch 8` | journey fields, beliefs, verbatim quotes |
| Cluster | `cluster-build`, `cluster-report` | clusters within action groups, opportunity scores, `analysis/candidate_beliefs.csv` |
| Insights | `insights` | `eval/results/insights.json` (model writes wording only; checked in code) |
| Golden set | `golden-sheet`, `label-views`, `golden-score [--relevance-only]` | blind hand labels vs engine |
| Evidence log | `evidence-log` | `docs/evidence_log.md` |
| Explorer | `streamlit run app/explorer.py` | Insights, Opportunity table, Continuers vs droppers, Cluster detail, Segments, Funnel, Candidate beliefs |

`refresh` runs collect (new items only), prefilter, relevance, extraction and nearest-cluster assignment in one go; Reddit only
with `--reddit`. `python -m pytest tests` runs the unit tests (no network).

## Hosting the Explorer (Streamlit Community Cloud, free)

The hosted app reads `demo/engine.db`, a slim snapshot: post text is kept only for extracted items, and raw payloads, author hashes
and run logs are removed. `requirements.txt` is deliberately small; the pipeline needs `requirements-pipeline.txt`.

1. `python -m engine.cli export-demo`, then commit `demo/engine.db` and `eval/results/` and push.
2. On share.streamlit.io: repository `sip-discovery-engine`, branch `main`, main file `app/explorer.py`.

Keep the repository private: it holds post text collected from public sites, and the Reddit part came through a method Reddit's
rules do not permit (disclosed in `config/sources.yaml`).

## What to trust

- **Solid:** counts, contrasts between groups, and quotes (every quote is checked word for word against the item it belongs to).
- **Hypotheses:** the "Interpretation" line on insight cards, and every candidate belief.
- **Measured but optimistic:** relevance agreement on the 20-item golden set, which was also used to tune the prompt.
- **Not the whole market:** public posts skew to people with something to say; see the biases section of the evidence log.

## Folder map

```
config/    sources.yaml (what is collected and why it is allowed), llm.yaml (models, free-tier limits), taxonomy.yaml (every field)
prompts/   relevance.md, extraction.md (versioned; hashes and version recorded in every run)
src/engine collectors/, store, prefilter, relevance, extract, pilot (resumable runs), cluster, insights, golden, evidence, refresh, cli
app/       explorer.py (Streamlit)
eval/      golden_set.csv, corrections.md, evidence_notes.md, label views, results/
analysis/  candidate_beliefs.csv (for grouping by hand)
docs/      architecture.md, evidence_log.md (generated)
demo/      engine.db (hosted snapshot)
data/      working database and run files (git-ignored)
tests/     pytest
```
