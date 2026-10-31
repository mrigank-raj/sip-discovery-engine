"""SIP Discovery Engine Explorer. Run from the project root:  PYTHONPATH=src streamlit run app/explorer.py"""
import csv
import json
import os
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from engine import cluster, insights, store  # noqa: E402

if os.environ.get("ENGINE_DB"):  # point the Explorer at another database (used to render-check views on test data)
    cluster.DB_PATH = Path(os.environ["ENGINE_DB"])
elif not cluster.DB_PATH.exists():  # hosted copy: no local database, use the slim snapshot from `export-demo`
    cluster.DB_PATH = ROOT / "demo" / "engine.db"

st.set_page_config(page_title="SIP Discovery Engine", layout="wide")
NS = {"not_stated", "unknown", "none_stated", "unclear"}
BUCKETS = ["continuers", "considering", "acted", "instalment_failed", "switched_platform"]
COMPARE = ["emotion", "check_frequency", "what_they_check", "action_reason", "journey_stage", "outside_app_behaviour",
           "investor_experience", "life_stage", "income_type", "source_of_money", "influenced_by"]
STAGES = ["before_start", "first_3_months", "months_4_to_12", "after_12_months"]
# Reference palette (validated light and dark): categorical slots in fixed order; one-hue blue for magnitude; gray for neutral.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
BLUE, GRAY, LIGHT_GRAY = "#2a78d6", "#a3a29c", "#d9d8d3"
SEQ = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
PLACEHOLDER = "Populates when extraction completes (est. Oct 31)."
ROW = 38  # pixels per bar row, so every category label fits
YAXIS = alt.Axis(labelOverlap=False, labelLimit=260)


@st.cache_data(show_spinner="Loading the database")
def load(groww_only, first_only):
    db = store.connect(cluster.DB_PATH)
    keep = lambda i: (not groww_only or i["platform"] == "groww") and (not first_only or insights.FIRST(i))  # noqa: E731
    items = [i for i in cluster.load(db) if keep(i)]
    by_item = {r["item_id"]: r["name"] for r in db.execute(
        "SELECT ci.item_id, c.name FROM cluster_items ci JOIN clusters c USING(cluster_id)")}
    rows = [{**{k: i[k] for k in ("item_id", "source", "platform", "summary", "sip_action", "contrast_bucket", "severity", "url", *COMPARE)},
             "date": (i["created_at"] or "")[:10], "cluster": by_item.get(i["item_id"], "(none)"),
             "belief": i["rec"].get("belief_at_action"), "belief_quote": i["rec"].get("belief_quote"),
             "expectation": i["rec"].get("expectation_at_start")} for i in items]
    rel = {r["item_id"]: r["relevant"] for r in db.execute("SELECT item_id, relevant FROM filter_results WHERE relevant IS NOT NULL")}
    cards = [{**c, "confidence": insights.confidence(c)} for c in insights.candidates(db, keep)] if groww_only or first_only else None
    return {"items": pd.DataFrame(rows), "metrics": cluster.metrics(db, keep), "funnel": pd.DataFrame(cluster.funnel(db)), "relevant": rel,
            "cards": cards}


def hbar(df, x, y, color=BLUE, sort="-x", height=None, fmt=",.0f", title=None):
    """One-series horizontal bar with a value label at the end of each bar (relief for low-contrast hues) and a tooltip."""
    base = alt.Chart(df).encode(y=alt.Y(f"{y}:N", sort=sort, title=None, axis=YAXIS), x=alt.X(f"{x}:Q", title=title),
                                tooltip=[alt.Tooltip(f"{y}:N"), alt.Tooltip(f"{x}:Q", format=fmt)])
    bars = base.mark_bar(color=color, cornerRadiusEnd=4, height={"band": 0.7})
    text = base.mark_text(align="left", dx=4, color="#52514e").encode(text=alt.Text(f"{x}:Q", format=fmt))
    return (bars + text).properties(height=height or max(120, ROW * len(df)))


def heat(df, x, y, value, x_sort=None, y_sort=None, fmt=".0f", legend="% of group"):
    """Share heatmap: one-hue sequential blue, the value printed in each cell."""
    base = alt.Chart(df).encode(x=alt.X(f"{x}:N", sort=x_sort, title=None, axis=alt.Axis(labelAngle=-30)),
                                y=alt.Y(f"{y}:N", sort=y_sort, title=None, axis=YAXIS),
                                tooltip=[f"{y}:N", f"{x}:N", alt.Tooltip(f"{value}:Q", format=fmt)])
    rect = base.mark_rect(stroke="white", strokeWidth=2).encode(
        color=alt.Color(f"{value}:Q", scale=alt.Scale(range=SEQ[:4]), legend=alt.Legend(title=legend)))
    dark = 0.45 * df[value].max() if legend != "% of group" else 45  # white text where the cell colour is dark
    text = base.mark_text().encode(text=alt.Text(f"{value}:Q", format=fmt),
                                   color=alt.condition(f"datum['{value}'] > {dark}", alt.value("white"), alt.value("#0b0b0b")))
    return (rect + text).properties(height=max(160, ROW * df[y].nunique() + 60))


def show(chart):
    st.altair_chart(chart.configure_view(strokeWidth=0).configure_axis(grid=False, domainColor="#d9d8d3", tickColor="#d9d8d3"),
                    use_container_width=True)


def quote(q, src, url):
    st.markdown(f"> {q}  \n> *{src}* · [source]({url})")


groww_only = st.sidebar.toggle("Groww only", help="Only items about Groww: Groww store reviews, and posts that name Groww.")
first_only = st.sidebar.toggle("First-timers only", key="first_only", help="Only posts where the person says they are a first-time investor.")
D = load(groww_only, first_only)
items, ms, f = D["items"], D["metrics"], D["funnel"].fillna(0)
num = lambda c: int(f[c].sum())  # noqa: E731

st.title("SIP Discovery Engine")
st.caption("Why do first-time investors keep or stop their SIPs? Public reviews, forums and comments · counts are mentions in a "
           "sample, not population rates · Evidence log: [link coming]")

# ---- always visible: funnel, sources, evaluation --------------------------------------------------------------------
st.subheader("From collected posts to evidence")
stages = [("Seen", "seen"), ("Collected", "collected"), ("Keyword prefilter", "prefiltered"), ("Classified", "classified"), ("Relevant", "relevant"),
          ("Extracted", "extracted"), ("Used in analysis", "analysed")]
c = st.columns(len(stages))
for col, (label, k) in zip(c, stages):
    col.metric(label, f"{num(k):,}")
show(hbar(pd.DataFrame([{"stage": f"{i + 1}. {s}", "posts": num(k)} for i, (s, k) in enumerate(stages)]), "posts", "stage",
          sort=None, title="posts"))
st.caption("Seen: fetched by the collectors · Collected: kept after dropping too-short, duplicate and out-of-window posts")

left, right = st.columns([3, 2])
with left:
    st.markdown("**Each source after the prefilter**")
    src = []
    for r in f.to_dict("records"):
        src += [{"source": r["source"], "status": "relevant", "posts": r["relevant"], "o": 0},
                {"source": r["source"], "status": "not relevant", "posts": r["classified"] - r["relevant"], "o": 1},
                {"source": r["source"], "status": "not classified yet", "posts": r["prefiltered"] - r["classified"], "o": 2}]
    sdf = pd.DataFrame(src)
    show(alt.Chart(sdf).mark_bar(stroke="white", strokeWidth=2, height={"band": 0.7}).encode(
        y=alt.Y("source:N", title=None, axis=YAXIS), x=alt.X("posts:Q", stack="zero", title="prefiltered posts"),
        color=alt.Color("status:N", scale=alt.Scale(domain=["relevant", "not relevant", "not classified yet"], range=[BLUE, GRAY, LIGHT_GRAY]),
                        legend=alt.Legend(orient="top", title=None)),
        order="o:Q", tooltip=["source", "status", "posts"]).properties(height=ROW * f["source"].nunique() + 90))
with right:
    st.markdown("**Collected vs kept by the prefilter**")
    pdf = f[["source", "collected", "prefiltered"]].assign(pass_rate=lambda d: 100 * d["prefiltered"] / d["collected"])
    show(hbar(pdf, "pass_rate", "source", fmt=".0f", title="% of collected kept"))
with st.expander("Table: funnel by source"):
    st.dataframe(f.rename(columns={"no_sip_action_stated": "relevant, no SIP action stated (likely false positive)",
                                   "analysed": "used in analysis"}), hide_index=True, width="stretch")

st.subheader("How far to trust relevance: 20 hand-labelled posts")
gold = list(csv.DictReader(open(ROOT / "eval" / "golden_set.csv", encoding="utf-8-sig")))
pairs = [(g["is_relevant"].strip().lower() in ("yes", "y", "true", "1"), D["relevant"].get(g["item_id"])) for g in gold if g["is_relevant"].strip()]
pairs = [(m, bool(e)) for m, e in pairs if e is not None]
if pairs:
    tp = sum(m and e for m, e in pairs); fp = sum(e and not m for m, e in pairs)  # noqa: E702
    fn = sum(m and not e for m, e in pairs); tn = len(pairs) - tp - fp - fn  # noqa: E702
    g1, g2, g3, g4 = st.columns([1, 1, 1, 2])
    g1.metric("Agreement", f"{100 * (tp + tn) / len(pairs):.0f}%", help=f"{tp + tn} of {len(pairs)}")
    g2.metric("Recall", f"{100 * tp / (tp + fn):.0f}%" if tp + fn else "-", help="of posts I marked relevant, share the engine kept")
    g3.metric("Precision", f"{100 * tp / (tp + fp):.0f}%" if tp + fp else "-", help="of posts the engine kept, share I marked relevant")
    outcomes = ["both say relevant", "both say not relevant", "engine kept, I didn't", "engine dropped, I kept"]
    cm = pd.DataFrame({"outcome": outcomes, "posts": [tp, tn, fp, fn], "verdict": ["agree", "agree", "disagree", "disagree"]})
    with g4:
        base = alt.Chart(cm).encode(y=alt.Y("outcome:N", sort=outcomes, title=None, axis=YAXIS), x=alt.X("posts:Q", title="posts"),
                                    tooltip=["outcome", "posts"])
        show((base.mark_bar(cornerRadiusEnd=4, height={"band": 0.7}).encode(
            color=alt.Color("verdict:N", scale=alt.Scale(domain=["agree", "disagree"], range=SERIES[:2]), legend=alt.Legend(orient="top", title=None)))
              + base.mark_text(align="left", dx=4, color="#52514e").encode(text="posts:Q")).properties(height=ROW * 4 + 80))
    st.caption("Tuned on these same 20 posts, so optimistic. Errors lean towards keeping too much; the analysis drops posts with no SIP action.")
g = ROOT / "eval" / "results" / "golden_relevance.md"
if g.exists():
    with st.expander("Every disagreement, with the post"):
        st.markdown(g.read_text(encoding="utf8").split("## Relevance disagreements", 1)[-1])

pre, cls, rel, ext = num("prefiltered"), num("classified"), num("relevant"), num("extracted")
if cls < pre or ext < rel:
    st.progress(min(1.0, ext / rel) if rel else 0.0,
                text=f"{ext:,} of {rel:,} relevant posts extracted (the rest are queued, or held for manual review after "
                     f"failing the verbatim-quote check) · relevance {cls:,} of {pre:,} classified")

# ---- analysis views -------------------------------------------------------------------------------------------------
st.divider()
VIEWS = ["Insights", "Opportunity", "Stay vs stop", "Clusters", "Segments", "Beliefs", "Over time"]
view = st.segmented_control("View", VIEWS, default="Insights", key="view", label_visibility="collapsed") or "Insights"
if items.empty:
    st.info(PLACEHOLDER)
    st.stop()
side = ROOT / "eval" / "results" / "first_timers.md"
if first_only:
    st.caption(f"First-timers only: {len(items)} posts where the person says it is their first investing. Every view below is recomputed on them.")
    if side.exists():
        with st.expander("Side by side: first-timers vs all users"):
            st.markdown(side.read_text(encoding="utf8").split("\n", 1)[1])

if view == "Insights":
    p = ROOT / "eval" / "results" / "insights.json"
    if D["cards"] is not None:
        st.caption("Filtered view: cards recomputed on these posts and worded by code, not the model.")
        data = [{**c, "headline": c["fallback"], "weak": c["id"] in insights.WEAK_IDS or c["confidence"] == "low"} for c in D["cards"]]
    elif p.exists():
        data = json.loads(p.read_text(encoding="utf8"))["insights"]
    else:
        st.info(PLACEHOLDER)
    if D["cards"] is not None or p.exists():
        icon = {"high": "🟢", "medium": "🟠", "low": "🔴"}
        for i in [x for x in data if not x["weak"]] + [x for x in data if x["weak"]]:
            with st.container(border=True):
                st.markdown(f"#### {i['headline']}")
                st.caption(f"{icon[i['confidence']]} {i['confidence']} confidence · {i['n']} posts · {i['sources']} sources")
                with st.expander("Interpretation, caveat and evidence"):
                    if i["so_what"]:
                        st.markdown(f"**Hypothesis to test:** {i['so_what']}")
                    if i["caveat"]:
                        st.markdown(f"**Caveat:** {i['caveat']}")
                    st.json(i["facts"])
                    for q in i["quotes"]:
                        quote(q["quote"], q["source"], q["url"])

if view == "Opportunity":
    ranked = [m for m in ms if m["score"] is not None]
    if not ranked:
        st.info(f"No cluster has {cluster.MIN_ITEMS}+ posts yet. " + PLACEHOLDER)
    else:
        w = cluster.WEIGHTS
        st.caption(f"Score = {w['frequency']:.2f}·frequency + {w['acted']:.2f}·share acted + {w['stage']:.2f}·stage concentration + "
                   f"{w['evidence']:.2f}·source spread · bar length = score, colour = what earns it · weights are a judgment")
        parts = pd.DataFrame([{"cluster": m["name"], "part": p, "points": w[p] * m["score_parts"][p], "o": k}
                              for m in ranked for k, p in enumerate(w)])
        order = [m["name"] for m in sorted(ranked, key=lambda m: -m["score"])]
        show(alt.Chart(parts).mark_bar(stroke="white", strokeWidth=2, height={"band": 0.7}).encode(
            y=alt.Y("cluster:N", sort=order, title=None, axis=YAXIS), x=alt.X("points:Q", stack="zero", title="opportunity score"),
            color=alt.Color("part:N", scale=alt.Scale(domain=list(w), range=SERIES[:4]), legend=alt.Legend(orient="top", title=None)),
            order="o:Q", tooltip=["cluster", "part", alt.Tooltip("points:Q", format=".2f")]).properties(height=ROW * len(ranked) + 90))
        rank = pd.DataFrame([{"cluster": m["name"], "with Play": m["score"], "without Play": m["score_without_play"]} for m in ranked])
        long = rank.melt("cluster", var_name="ranking", value_name="score").dropna()
        st.markdown("**Does the order hold without Play Store reviews?**")
        show(alt.Chart(long).mark_circle(size=120, stroke="white", strokeWidth=2).encode(
            y=alt.Y("cluster:N", sort=order, title=None, axis=YAXIS), x=alt.X("score:Q", title="score"),
            color=alt.Color("ranking:N", scale=alt.Scale(domain=["with Play", "without Play"], range=SERIES[:2]),
                            legend=alt.Legend(orient="top", title=None)), tooltip=["cluster", "ranking", alt.Tooltip("score:Q", format=".2f")])
             .properties(height=ROW * len(ranked) + 90))
        small = cluster.below_min(ms)
        st.caption(f"{small['clusters']} clusters under {cluster.MIN_ITEMS} posts are not ranked ({small['items']} posts).")
        with st.expander("Table"):
            st.dataframe(pd.DataFrame([{"cluster": m["name"], "group": m["group"], "score": m["score"], "without Play": m["score_without_play"],
                                        "posts": m["items"], "threads": m["threads"], "sources": len(m["sources"]),
                                        "acted %": round(100 * m["acted_share"]), "failed instalment %": round(100 * m["instalment_failed_share"]),
                                        "stage note": m["stage_flag"] or ""} for m in ms]), hide_index=True, width="stretch")

if view == "Stay vs stop":
    sub = items[items["contrast_bucket"].isin(BUCKETS)]
    sizes = sub["contrast_bucket"].value_counts().reindex(BUCKETS, fill_value=0).rename_axis("group").reset_index(name="posts")
    show(hbar(sizes, "posts", "group", sort=BUCKETS, title="posts"))
    field = st.selectbox("Compare the groups on", COMPARE, format_func=lambda s: s.replace("_", " "))
    stated = sub[~sub[field].isin(NS)]
    if stated.empty:
        st.info("No post in these groups states this.")
    else:
        share = (stated.groupby(["contrast_bucket", field]).size() / stated.groupby("contrast_bucket").size() * 100).rename("share").reset_index()
        show(heat(share, field, "contrast_bucket", "share", y_sort=BUCKETS))
        st.caption("Share of each group's posts that state it · not-stated excluded · n stating it: "
                   + ", ".join(f"{b} {int((stated['contrast_bucket'] == b).sum())}" for b in BUCKETS))

if view == "Clusters":
    pick = st.selectbox("Cluster", [m["id"] for m in ms], format_func=lambda i: next(f"{m['name']} ({m['items']})" for m in ms if m["id"] == i))
    m = next(m for m in ms if m["id"] == pick)
    st.markdown(f"**{m['name']}** · {m['definition']}")
    k = st.columns(4)
    k[0].metric("Posts", m["items"])
    k[1].metric("Acted", f"{m['acted_share']:.0%}")
    k[2].metric("Failed instalment", f"{m['instalment_failed_share']:.0%}")
    k[3].metric("Score", "not ranked" if m["score"] is None else m["score"])
    a, b, c3 = st.columns(3)
    with a:
        st.markdown("**Sources**")
        show(hbar(pd.DataFrame(list(m["sources"].items()), columns=["source", "posts"]), "posts", "source"))
    with b:
        st.markdown("**Journey stage**")
        sm = pd.DataFrame([{"stage": s, "posts": m["stage_mix"].get(s, 0)} for s in STAGES + ["unknown"]])
        show(hbar(sm, "posts", "stage", sort=STAGES + ["unknown"]))
    with c3:
        st.markdown("**Reasons given**")
        if m["reasons"]:
            show(hbar(pd.DataFrame(list(m["reasons"].items()), columns=["reason", "posts"]), "posts", "reason"))
        else:
            st.caption("none stated")
    with st.expander("Quotes"):
        for q in m["quotes"]:
            quote(q["quote"], q["source"], q["url"])

if view == "Segments":
    seg = st.selectbox("Segment", ["investor_experience", "life_stage", "income_type", "source_of_money", "influenced_by"],
                       format_func=lambda s: s.replace("_", " "))
    stated = items[~items[seg].isin(NS)].assign(group=lambda d: d["contrast_bucket"].fillna(d["sip_action"]))
    st.caption(f"{len(stated)} of {len(items)} posts state it · segments are filled only when the person says so")
    if not stated.empty:
        cnt = stated.groupby([seg, "group"]).size().rename("posts").reset_index()
        show(alt.Chart(cnt).mark_rect(stroke="white", strokeWidth=2).encode(
            x=alt.X("group:N", title=None, axis=alt.Axis(labelAngle=-30)), y=alt.Y(f"{seg}:N", title=None),
            color=alt.Color("posts:Q", scale=alt.Scale(range=SEQ[:4])), tooltip=[seg, "group", "posts"])
             + alt.Chart(cnt).mark_text().encode(x="group:N", y=f"{seg}:N", text="posts:Q"))

if view == "Beliefs":
    st.warning("Candidate beliefs to validate in research, not findings. Each is stated by the person and backed by a verbatim quote.")
    bl = items[items["belief"].notna()]
    k = st.columns(2)
    k[0].metric("Posts stating a belief", len(bl))
    k[1].metric("Null rate", f"{100 * (1 - len(bl) / len(items)):.0f}%")
    if not bl.empty:
        show(hbar(bl["sip_action"].value_counts().rename_axis("action").reset_index(name="posts"), "posts", "action"))
        focus = bl["cluster"] == cluster.FOCUS_CLUSTER
        st.markdown(f"**Cross-tab** · {int(focus.sum())} of {len(bl)} sit in “{cluster.FOCUS_CLUSTER}” (★)")
        st.dataframe(bl.assign(focus=focus.map({True: "★", False: ""}), contrast_bucket=bl["contrast_bucket"].fillna("-"))
                     .sort_values(["focus", "cluster"], ascending=[False, True])
                     [["focus", "belief", "cluster", "sip_action", "contrast_bucket", "investor_experience"]], hide_index=True, width="stretch")
        show(heat(pd.crosstab(bl["contrast_bucket"].fillna("no bucket"), bl["investor_experience"]).stack().rename("posts").reset_index(),
                  "investor_experience", "contrast_bucket", "posts", legend="posts")
             .properties(title="Beliefs by group and investor experience (posts)"))
        for _, r in bl.iterrows():
            with st.expander(f"{r['belief']} · {r['sip_action']}"):
                quote(r["belief_quote"], r["source"], r["url"])

if view == "Over time":
    by = items.assign(month=items["date"].str[:7]).groupby(["month", "source"]).size().rename("posts").reset_index()
    srcs = sorted(by["source"].unique())
    show(alt.Chart(by).mark_bar(stroke="white", strokeWidth=1).encode(
        x=alt.X("month:O", title=None), y=alt.Y("posts:Q", stack="zero", title="posts used in analysis"),
        color=alt.Color("source:N", scale=alt.Scale(domain=srcs, range=SERIES[:len(srcs)]), legend=alt.Legend(orient="top", title=None)),
        tooltip=["month", "source", "posts"]).properties(height=300))
    st.caption("Play covers about 12 months, Reddit about two weeks, the rest 24 months.")
