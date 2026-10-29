"""SIP Discovery Engine Explorer. Run from the project root:  PYTHONPATH=src streamlit run app/explorer.py"""
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from engine import cluster, store  # noqa: E402

if not cluster.DB_PATH.exists():  # hosted copy: no local database, use the slim snapshot from `export-demo`
    cluster.DB_PATH = ROOT / "demo" / "engine.db"

st.set_page_config(page_title="SIP Discovery Engine", layout="wide")
NS = {"not_stated", "unknown", "none_stated", "unclear"}
BUCKETS = ["continuers", "considering", "acted", "instalment_failed", "switched_platform"]
COMPARE = ["emotion", "check_frequency", "what_they_check", "action_reason", "journey_stage", "outside_app_behaviour",
           "investor_experience", "life_stage", "income_type", "source_of_money", "influenced_by"]


@st.cache_data(show_spinner="Loading the database")
def load(groww_only):
    db = store.connect(cluster.DB_PATH)
    keep = (lambda i: i["platform"] == "groww") if groww_only else (lambda i: True)
    items = [i for i in cluster.load(db) if keep(i)]
    by_item = {r["item_id"]: (r["cluster_id"], r["name"]) for r in db.execute(
        "SELECT ci.item_id, c.cluster_id, c.name FROM cluster_items ci JOIN clusters c USING(cluster_id)")}
    rows = [{**{k: i[k] for k in ("item_id", "source", "platform", "summary", "sip_action", "contrast_bucket", "severity", "url",
                                  "text", *COMPARE)},
             "date": (i["created_at"] or "")[:10], "cluster": by_item.get(i["item_id"], (None, "(none)"))[1],
             "belief": i["rec"].get("belief_at_action"), "belief_quote": i["rec"].get("belief_quote"),
             "expectation": i["rec"].get("expectation_at_start"), "quotes": i["rec"]["evidence_quotes"]} for i in items]
    f = cluster.funnel(db)
    return {"items": pd.DataFrame(rows), "metrics": cluster.metrics(db, keep), "funnel": pd.DataFrame(f)}


groww_only = st.sidebar.toggle("Groww only", help="Keep only items about Groww: Groww store reviews, and forum or video posts that name Groww.")
D = load(groww_only)
items, ms, f = D["items"], D["metrics"], D["funnel"]

st.title("SIP Discovery Engine")
st.caption("Why first-time mutual-fund investors on Groww keep or stop their SIPs, from public reviews, forums and video comments.")
st.warning("Counts are **mentions in a sample of public posts**, not how many investors do something. Store reviews are mostly "
           "about one app; Reddit covers about two weeks; relevance agreed with hand labels on 16 of 20 tuning items. "
           "Read the Evidence log in docs/evidence_log.md before relying on any number.")
pre, cls, rel, ext = (int(f[c].sum()) for c in ("prefiltered", "classified", "relevant", "extracted"))
if cls < pre or ext < rel:
    st.info(f"**Run in progress: {ext} of {rel} items extracted** (relevance classified {cls} of {pre} prefiltered items). "
            "Every view reflects only what has been processed so far.")
if items.empty:
    st.stop()

VIEWS = ["Insights", "Opportunity table", "Continuers vs droppers", "Cluster detail", "Segments", "Funnel and volume", "Candidate beliefs"]
view = st.segmented_control("View", VIEWS, default="Insights", key="view", label_visibility="collapsed") or "Insights"


def quote(q, src, url):
    st.markdown(f"> {q}  \n> *{src}* - [source]({url})")


if view == "Insights":
    p = ROOT / "eval" / "results" / "insights.json"
    if not p.exists():
        st.info("No insights yet. Run `PYTHONPATH=src python -m engine.cli insights`.")
    else:
        st.caption("Written by the engine from measured contrasts over all platforms. Every number is checked against the data behind it, "
                   "confidence is set from sample size and source spread, and wording that overstates a minority is rejected.")
        data = json.loads(p.read_text(encoding="utf8"))["insights"]
        for i in [x for x in data if not x["weak"]] + [x for x in data if x["weak"]]:
            with st.container(border=True):
                st.markdown(f"#### {i['headline']}")
                if i["so_what"]:
                    st.markdown(f"**Interpretation (a hypothesis to test, not a finding).** {i['so_what']}")
                color = {"high": "green", "medium": "orange", "low": "red"}[i["confidence"]]
                st.markdown(f":{color}[**Confidence: {i['confidence']}**] ({i['n']} items, {i['sources']} sources)"
                            + ("" if i["written_by_llm"] else "  ·  plain text"))
                if i["caveat"]:
                    st.caption(f"Caveat: {i['caveat']}")
                with st.expander("Evidence"):
                    st.json(i["facts"])
                    for q in i["quotes"]:
                        quote(q["quote"], q["source"], q["url"])

if view == "Opportunity table":
    w = cluster.WEIGHTS
    st.markdown(f"**Score = {w['frequency']:.2f} x frequency + {w['acted']:.2f} x share acted + {w['stage']:.2f} x stage concentration "
                f"+ {w['evidence']:.2f} x evidence strength**")
    st.caption(f"Frequency: distinct threads, scaled 0 to 1 across ranked clusters. Share acted: posts that actually paused, reduced, stopped "
               f"or redeemed (failed instalments are not counted; they have their own column). Stage concentration: share of known-stage "
               f"posts in the cluster's most common journey stage, set to 0 below {cluster.MIN_KNOWN_STAGE} known-stage posts. Evidence "
               f"strength: number of distinct sources, scaled 0 to 1. Clusters under {cluster.MIN_ITEMS} posts are not ranked. "
               "The weights are a judgment, not a measurement; the 'without Play' column re-ranks after removing Play Store reviews.")
    t = pd.DataFrame([{"#": m["id"], "score": m["score"], "without Play": m["score_without_play"], "cluster": m["name"], "group": m["group"],
                       "posts": m["items"], "threads": m["threads"], "sources": len(m["sources"]), "acted %": round(100 * m["acted_share"]),
                       "failed instalment %": round(100 * m["instalment_failed_share"]), "top stage": m["top_stage"],
                       "stage conc. %": round(100 * m["stage_concentration"]), "stage note": m["stage_flag"] or "",
                       "outside app %": round(100 * m["outside_app_share"])} for m in ms])
    st.dataframe(t, hide_index=True, width="stretch")
    small = cluster.below_min(ms)
    st.caption(f"{small['clusters']} clusters are below {cluster.MIN_ITEMS} posts and unranked; they hold {small['items']} posts.")

if view == "Continuers vs droppers":
    st.caption("Shares within each group of posts. Continuers: continuing or increased. Considering: thinking of stopping. Acted: paused, "
               "reduced, stopped or redeemed. Failed instalments and platform switches are shown separately. 'not stated' is excluded "
               "from each comparison and its count shown, because most posts do not say.")
    sizes = items["contrast_bucket"].value_counts()
    st.write(" · ".join(f"**{b}** {int(sizes.get(b, 0))} posts" for b in BUCKETS))
    field = st.selectbox("Compare on", COMPARE)
    sub = items[items["contrast_bucket"].isin(BUCKETS)]
    stated = sub[~sub[field].isin(NS)]
    if stated.empty:
        st.info("No post in these groups states this.")
    else:
        tab = pd.crosstab(stated[field], stated["contrast_bucket"], normalize="columns").reindex(columns=[b for b in BUCKETS if b in set(stated["contrast_bucket"])])
        st.dataframe((100 * tab).round(0), width="stretch")
        st.caption("Posts stating it, per group: " + ", ".join(f"{b} {int((stated['contrast_bucket'] == b).sum())} of {int(sizes.get(b, 0))}" for b in BUCKETS))
    exp = sub[sub["expectation"].notna()]
    with st.expander(f"Stated expectations at start ({len(exp)} posts)"):
        for _, r in exp.head(60).iterrows():
            quote(r["expectation"], f"{r['source']}, {r['contrast_bucket']}", r["url"])

if view == "Cluster detail":
    pick = st.selectbox("Cluster", [m["id"] for m in ms], format_func=lambda i: next(f"#{m['id']}  {m['name']} ({m['items']})" for m in ms if m["id"] == i))
    m = next(m for m in ms if m["id"] == pick)
    st.markdown(f"**{m['name']}** · group `{m['group']}`  \n{m['definition']}")
    c = st.columns(5)
    c[0].metric("Posts", m["items"])
    c[1].metric("Threads", m["threads"])
    c[2].metric("Acted", f"{m['acted_share']:.0%}")
    c[3].metric("Failed instalment", f"{m['instalment_failed_share']:.0%}")
    c[4].metric("Score", "not ranked" if m["score"] is None else m["score"])
    left, right = st.columns(2)
    left.write("Sources")
    left.bar_chart(pd.Series(m["sources"]))
    right.write("Journey stage")
    right.bar_chart(pd.Series(m["stage_mix"]))
    st.write("Quotes (open the link to read the original post)")
    for q in m["quotes"]:
        quote(q["quote"], q["source"], q["url"])
    st.dataframe(items[items["cluster"] == m["name"]][["source", "platform", "date", "sip_action", "action_reason", "summary", "url"]],
                 hide_index=True, width="stretch", column_config={"url": st.column_config.LinkColumn("link")})

if view == "Segments":
    st.caption("Segment fields are filled only when the person says so, so most posts are 'not stated'; the stated count is shown for each.")
    seg = st.selectbox("Segment", ["investor_experience", "life_stage", "income_type", "source_of_money", "influenced_by"])
    stated = items[~items[seg].isin(NS)]
    st.write(f"{len(stated)} of {len(items)} posts state {seg.replace('_', ' ')}.")
    if not stated.empty:
        st.dataframe(pd.crosstab(stated[seg], stated["contrast_bucket"].fillna(stated["sip_action"])), width="stretch")

if view == "Funnel and volume":
    st.dataframe(f, hide_index=True, width="stretch")
    st.caption("collected → kept by the keyword prefilter → classified by the relevance model → relevant (own or a named person's SIP or "
               "mutual-fund holdings) → extracted and passed the verbatim-quote validator.")
    st.bar_chart(items.groupby(items["date"].str[:7]).size().rename("extracted posts by month"))
    st.dataframe(items.groupby(["source", "platform"]).size().rename("posts").reset_index(), hide_index=True, width="stretch")

if view == "Candidate beliefs":
    st.warning("**Candidate beliefs to validate in research, not findings.** Only beliefs a person states, each backed by a verbatim "
               "quote. They are grouped by hand (analysis/candidate_beliefs.csv), not by the engine.")
    b = items[items["belief"].notna()]
    st.write(f"{len(b)} of {len(items)} extracted posts state a belief ({len(items) - len(b)} null).")
    if not b.empty:
        st.bar_chart(b["sip_action"].value_counts())
        for _, r in b.iterrows():
            with st.container(border=True):
                st.markdown(f"**{r['belief']}** · `{r['sip_action']}` · {r['journey_stage']} · {r['investor_experience']}")
                quote(r["belief_quote"], r["source"], r["url"])
