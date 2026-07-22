"""
UNIFIED ASSET & OPERATIONS BRAIN
Industrial Knowledge Intelligence Platform

ET AI Hackathon 2026 -- Problem Statement 8

Run:  streamlit run app.py
"""

import os
import glob
import time
import io

import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go

from core.ingest import ingest_document, ingest_path, SUPPORTED_EXTENSIONS
from core.graph import (
    build_graph, graph_stats, central_entities, neighbourhood,
    find_patterns, knowledge_gaps, compliance_matrix,
)
from core.retrieval import RetrievalEngine, suggest_queries
from core.ontology import ENTITY_COLORS, ENTITY_DESCRIPTIONS, entity_summary

# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Unified Asset & Operations Brain",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEMO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_corpus")

# ---------------------------------------------------------------------------
# THEME
# ---------------------------------------------------------------------------
# Palette rationale: a control-room aesthetic. Deep slate ground, cyan as the
# instrument accent (the colour of process HMI trend lines), amber and red
# reserved exclusively for genuine risk states so that colour carries meaning
# rather than decoration.

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
    --ground:    #0b1017;
    --panel:     #131b26;
    --panel-2:   #1a2430;
    --line:      #263241;
    --ink:       #e8eef5;
    --ink-dim:   #8698ad;
    --accent:    #00d4ff;
    --warn:      #ffb020;
    --danger:    #ff5c5c;
    --ok:        #3ddc97;
}

html, body, [class*="css"], .stApp {
    font-family: 'IBM Plex Sans', system-ui, sans-serif;
}
.stApp { background: var(--ground); }

/* ---- Masthead ---- */
.masthead {
    border-left: 3px solid var(--accent);
    padding: 0.1rem 0 0.1rem 1rem;
    margin-bottom: 0.4rem;
}
.masthead h1 {
    font-size: 1.55rem; font-weight: 700; letter-spacing: -0.02em;
    color: var(--ink); margin: 0; line-height: 1.15;
}
.masthead .sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem; letter-spacing: 0.16em; text-transform: uppercase;
    color: var(--accent); margin-top: 0.28rem;
}

/* ---- Metric tiles ---- */
.tile {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 3px;
    padding: 0.85rem 1rem;
    height: 100%;
}
.tile .v {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.7rem; font-weight: 600; color: var(--ink);
    line-height: 1;
}
.tile .k {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem; letter-spacing: 0.13em; text-transform: uppercase;
    color: var(--ink-dim); margin-top: 0.4rem;
}
.tile .d { font-size: 0.7rem; color: var(--ink-dim); margin-top: 0.18rem; }
.tile.accent { border-left: 2px solid var(--accent); }
.tile.warn   { border-left: 2px solid var(--warn); }
.tile.danger { border-left: 2px solid var(--danger); }
.tile.ok     { border-left: 2px solid var(--ok); }

/* ---- Answer card ---- */
.answer {
    background: var(--panel);
    border: 1px solid var(--line);
    border-left: 3px solid var(--accent);
    border-radius: 3px;
    padding: 1.1rem 1.3rem;
    margin: 0.6rem 0 1rem 0;
}
.answer .txt { font-size: 1.0rem; line-height: 1.65; color: var(--ink); }

.cite {
    background: var(--panel-2);
    border: 1px solid var(--line);
    border-radius: 3px;
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.5rem;
}
.cite .head {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem; letter-spacing: 0.06em;
    color: var(--accent); text-transform: uppercase;
    margin-bottom: 0.35rem;
}
.cite .body { font-size: 0.86rem; line-height: 1.55; color: var(--ink); }
.cite .meta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem; color: var(--ink-dim); margin-top: 0.4rem;
}

/* ---- Confidence bar ---- */
.confbar {
    height: 4px; background: var(--panel-2); border-radius: 2px;
    overflow: hidden; margin: 0.5rem 0 0.2rem 0;
}
.confbar > div { height: 100%; }

/* ---- Chips ---- */
.chip {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.63rem; letter-spacing: 0.05em;
    padding: 0.16rem 0.5rem; border-radius: 2px;
    margin: 0.12rem 0.22rem 0.12rem 0;
    border: 1px solid var(--line); color: var(--ink-dim);
    background: var(--panel-2);
}

/* ---- Finding rows ---- */
.finding {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 3px;
    padding: 0.8rem 1rem; margin-bottom: 0.55rem;
}
.finding.high   { border-left: 3px solid var(--danger); }
.finding.medium { border-left: 3px solid var(--warn); }
.finding.low    { border-left: 3px solid var(--ink-dim); }
.finding .t {
    font-weight: 600; font-size: 0.94rem; color: var(--ink);
    margin-bottom: 0.25rem;
}
.finding .d { font-size: 0.82rem; color: var(--ink-dim); line-height: 1.55; }
.finding .e {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem; color: var(--accent); margin-top: 0.45rem;
}

/* ---- Section label ---- */
.seclabel {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem; letter-spacing: 0.16em; text-transform: uppercase;
    color: var(--ink-dim);
    border-bottom: 1px solid var(--line);
    padding-bottom: 0.4rem; margin: 1.1rem 0 0.75rem 0;
}

/* ---- Streamlit overrides ---- */
[data-testid="stSidebar"] { background: var(--panel); border-right: 1px solid var(--line); }
.stTabs [data-baseweb="tab-list"] { gap: 1.4rem; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] {
    background: transparent; padding: 0.5rem 0;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem; letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--ink-dim);
}
.stTabs [aria-selected="true"] { color: var(--accent) !important; }
div[data-testid="stDataFrame"] { border: 1px solid var(--line); }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------------
def init_state():
    defaults = {
        "documents": [],
        "graph": None,
        "engine": None,
        "corpus_loaded": False,
        "last_query": "",
        "ingest_log": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


def rebuild_indexes():
    """Rebuild graph and retrieval index after any corpus change."""
    docs = st.session_state.documents
    if not docs:
        st.session_state.graph = None
        st.session_state.engine = None
        return
    st.session_state.graph = build_graph(docs)
    st.session_state.engine = RetrievalEngine().build(docs)


def load_demo_corpus():
    paths = sorted(glob.glob(os.path.join(DEMO_DIR, "*")))
    docs = []
    log = []
    for p in paths:
        t0 = time.time()
        d = ingest_path(p)
        if d:
            docs.append(d)
            log.append({
                "file": d["filename"],
                "type": d["doc_type"],
                "chunks": len(d["chunks"]),
                "entities": len(d["entities"]),
                "ms": round((time.time() - t0) * 1000, 1),
            })
    st.session_state.documents = docs
    st.session_state.ingest_log = log
    st.session_state.corpus_loaded = True
    rebuild_indexes()


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="masthead"><h1>Operations Brain</h1>'
        '<div class="sub">Knowledge Intelligence</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    st.markdown('<div class="seclabel">Corpus</div>', unsafe_allow_html=True)

    if not st.session_state.corpus_loaded:
        if st.button("Load demo plant corpus", use_container_width=True, type="primary"):
            with st.spinner("Ingesting..."):
                load_demo_corpus()
            st.rerun()
        st.caption(
            "15 documents from a synthetic refinery: incident reports, work orders, "
            "inspection surveys, permits, SOPs, HAZOP and audit records."
        )
    else:
        n = len(st.session_state.documents)
        chunks = sum(len(d["chunks"]) for d in st.session_state.documents)
        st.markdown(
            f'<div class="tile accent"><div class="v">{n}</div>'
            f'<div class="k">Documents indexed</div>'
            f'<div class="d">{chunks} retrievable passages</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="seclabel">Add your own</div>', unsafe_allow_html=True)
    uploads = st.file_uploader(
        "Upload documents",
        type=[e.lstrip(".") for e in SUPPORTED_EXTENSIONS],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploads:
        existing = {d["filename"] for d in st.session_state.documents}
        added = 0
        for uf in uploads:
            if uf.name in existing:
                continue
            d = ingest_document(uf.name, uf.read())
            if d:
                st.session_state.documents.append(d)
                st.session_state.ingest_log.append({
                    "file": d["filename"], "type": d["doc_type"],
                    "chunks": len(d["chunks"]), "entities": len(d["entities"]),
                    "ms": 0.0,
                })
                added += 1
        if added:
            st.session_state.corpus_loaded = True
            rebuild_indexes()
            st.success(f"Added {added} document(s)")
            st.rerun()

    st.caption("Supported: " + " ".join(e.lstrip(".") for e in SUPPORTED_EXTENSIONS))

    if st.session_state.documents:
        st.markdown('<div class="seclabel">Session</div>', unsafe_allow_html=True)
        if st.button("Clear corpus", use_container_width=True):
            st.session_state.documents = []
            st.session_state.ingest_log = []
            st.session_state.corpus_loaded = False
            rebuild_indexes()
            st.rerun()

    st.markdown('<div class="seclabel">Architecture</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-family:IBM Plex Mono,monospace;font-size:0.66rem;'
        'line-height:1.9;color:#8698ad">'
        'INGEST &nbsp;· pdf docx xlsx csv txt<br>'
        'EXTRACT · 8-class ontology<br>'
        'GRAPH &nbsp;&nbsp;· networkx heterograph<br>'
        'RETRIEVE · tfidf + bm25 + entity<br>'
        'SYNTH &nbsp;&nbsp;· extractive, cited<br>'
        '<span style="color:#3ddc97">RUNS FULLY OFFLINE</span>'
        '</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# EMPTY STATE
# ---------------------------------------------------------------------------
if not st.session_state.documents:
    st.markdown(
        '<div class="masthead"><h1>Unified Asset &amp; Operations Brain</h1>'
        '<div class="sub">Industrial Knowledge Intelligence · ET AI Hackathon 2026</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("")
    st.markdown(
        "A large plant runs on 7 to 12 disconnected document systems. Drawings sit in "
        "one, work orders in another, inspection records in a third, procedures in a "
        "fourth. The information needed to prevent the next failure usually already "
        "exists — it is just never in the same place at the same time."
    )
    st.markdown(
        "This platform ingests those documents as they are, extracts the entities that "
        "matter, links them into a knowledge graph, and makes the collective intelligence "
        "queryable with citations back to source."
    )
    st.markdown("")
    c1, c2, c3 = st.columns(3)
    for col, (t, d) in zip([c1, c2, c3], [
        ("Ask across everything",
         "Natural-language questions answered from the whole corpus, every sentence traceable to a source document."),
        ("See what recurs",
         "Failure patterns that span multiple documents and years — invisible to any single reviewer."),
        ("Find what is missing",
         "Assets carrying operational history but no procedure. The knowledge cliff, made visible."),
    ]):
        col.markdown(
            f'<div class="tile"><div style="font-weight:600;color:#e8eef5;'
            f'margin-bottom:0.4rem">{t}</div>'
            f'<div style="font-size:0.83rem;color:#8698ad;line-height:1.6">{d}</div></div>',
            unsafe_allow_html=True,
        )
    st.markdown("")
    st.info("Load the demo corpus from the sidebar, or upload your own documents to begin.")
    st.stop()


# ---------------------------------------------------------------------------
# HEADER + KPIs
# ---------------------------------------------------------------------------
docs = st.session_state.documents
G = st.session_state.graph
engine = st.session_state.engine
stats = graph_stats(G) if G else {"nodes": 0, "edges": 0, "node_types": {}}

st.markdown(
    '<div class="masthead"><h1>Unified Asset &amp; Operations Brain</h1>'
    '<div class="sub">Industrial Knowledge Intelligence · ET AI Hackathon 2026</div></div>',
    unsafe_allow_html=True,
)

patterns = find_patterns(G, docs) if G else []
gaps = knowledge_gaps(G, docs) if G else []
n_equipment = stats["node_types"].get("EQUIPMENT", 0)
n_chunks = sum(len(d["chunks"]) for d in docs)

k1, k2, k3, k4, k5 = st.columns(5)
tiles = [
    (k1, "accent", len(docs), "Documents", f"{n_chunks} passages"),
    (k2, "accent", stats["nodes"], "Graph nodes", f"{stats['edges']} relationships"),
    (k3, "ok", n_equipment, "Assets tracked", "auto-extracted tags"),
    (k4, "warn", len(patterns), "Recurring patterns", "multi-document"),
    (k5, "danger", len(gaps), "Knowledge gaps", "under-documented"),
]
for col, cls, val, key, det in tiles:
    col.markdown(
        f'<div class="tile {cls}"><div class="v">{val}</div>'
        f'<div class="k">{key}</div><div class="d">{det}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("")

tab_ask, tab_graph, tab_patterns, tab_gaps, tab_compliance, tab_corpus = st.tabs([
    "Ask", "Knowledge Graph", "Patterns", "Gaps", "Compliance", "Corpus",
])


# ===========================================================================
# TAB 1 -- ASK
# ===========================================================================
with tab_ask:
    st.markdown(
        '<div class="seclabel">Expert Knowledge Copilot</div>',
        unsafe_allow_html=True,
    )

    qcol, fcol = st.columns([3, 1])
    with qcol:
        query = st.text_input(
            "Question",
            value=st.session_state.last_query,
            placeholder="e.g. Why did the mechanical seal on P-101A keep failing?",
            label_visibility="collapsed",
        )
    with fcol:
        types_present = sorted({d["doc_type"] for d in docs})
        dfilter = st.multiselect(
            "Restrict to", types_present, default=[],
            label_visibility="collapsed",
            placeholder="All document types",
        )

    sugg = suggest_queries(docs, limit=5)
    if sugg:
        cols = st.columns(len(sugg))
        for c, s in zip(cols, sugg):
            if c.button(s, use_container_width=True, key=f"sg_{s}"):
                st.session_state.last_query = s
                st.rerun()

    if query:
        st.session_state.last_query = query
        t0 = time.time()
        result = engine.answer(query, top_k=6, doc_type_filter=dfilter or None)
        elapsed = (time.time() - t0) * 1000

        if not result["found"]:
            st.warning(
                "No supporting evidence in the indexed corpus. The system does not "
                "generate an answer when the documents do not contain one."
            )
        else:
            conf = result["confidence"]
            colour = "#3ddc97" if conf >= 0.62 else ("#ffb020" if conf >= 0.38 else "#ff5c5c")

            st.markdown(
                f'<div class="answer"><div class="txt">{result["answer"]}</div>'
                f'<div class="confbar"><div style="width:{conf*100:.0f}%;'
                f'background:{colour}"></div></div>'
                f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.66rem;'
                f'color:#8698ad;margin-top:0.4rem">'
                f'CONFIDENCE {conf:.0%} · {result["confidence_label"].upper()} &nbsp;|&nbsp; '
                f'SOURCE AGREEMENT {result["source_agreement"]:.0%} &nbsp;|&nbsp; '
                f'{elapsed:.0f} ms &nbsp;|&nbsp; {len(result["citations"])} SOURCES'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            if conf < 0.38:
                st.warning(
                    "Low confidence. Treat this as a pointer to the source documents "
                    "rather than an answer. Verify before acting."
                )

            st.markdown('<div class="seclabel">Evidence</div>', unsafe_allow_html=True)

            for p in result.get("passages", []):
                sec = f" · {p['section'][:60]}" if p["section"] else ""
                ents = "".join(
                    f'<span class="chip">{e}</span>' for e in p["matched_entities"][:6]
                )
                st.markdown(
                    f'<div class="cite">'
                    f'<div class="head">[{p["rank"]}] {p["filename"]}</div>'
                    f'<div class="body">{p["text"]}</div>'
                    f'<div class="meta">{p["doc_type"]} · page {p["page"]}{sec} '
                    f'· relevance {p["score"]:.3f}</div>'
                    f'<div>{ents}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            with st.expander("Retrieval scoring breakdown"):
                st.caption(
                    "Every result is ranked by three independent signals. No neural "
                    "inference is involved, so the ranking is fully reproducible and "
                    "each contribution can be inspected."
                )
                rows = [{
                    "Rank": i + 1,
                    "Source": h["filename"][:38],
                    "TF-IDF": h["signals"]["tfidf"],
                    "BM25": h["signals"]["bm25"],
                    "Entity match": h["signals"]["entity"],
                    "Combined": h["score"],
                } for i, h in enumerate(result["hits"])]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ===========================================================================
# TAB 2 -- KNOWLEDGE GRAPH
# ===========================================================================
with tab_graph:
    st.markdown(
        '<div class="seclabel">Entity Relationship Graph</div>',
        unsafe_allow_html=True,
    )

    gc1, gc2, gc3 = st.columns([2, 1, 1])
    with gc1:
        entity_options = ["— whole corpus —"] + [
            f"{G.nodes[n].get('label', n)}  ({G.nodes[n].get('node_type')})"
            for n in sorted(
                (x for x in G.nodes() if G.nodes[x].get("node_type") != "DOCUMENT_FILE"),
                key=lambda x: -G.degree(x),
            )[:80]
        ]
        focus = st.selectbox("Focus on entity", entity_options, label_visibility="collapsed")
    with gc2:
        hops = st.slider("Hops", 1, 2, 1, label_visibility="collapsed",
                         help="Relationship depth from the focused entity")
    with gc3:
        max_nodes = st.slider("Max nodes", 25, 150, 70, step=5,
                              label_visibility="collapsed",
                              help="Limit for readability")

    # Resolve focus selection back to a node id
    sub = G
    if focus != "— whole corpus —":
        label_part = focus.rsplit("  (", 1)[0]
        type_part = focus.rsplit("  (", 1)[1].rstrip(")")
        node_id = f"{type_part}::{label_part}"
        if node_id in G:
            sub = neighbourhood(G, node_id, hops=hops, max_nodes=max_nodes)
    else:
        if G.number_of_nodes() > max_nodes:
            keep = sorted(G.nodes(), key=lambda n: -G.degree(n))[:max_nodes]
            sub = G.subgraph(keep)

    if sub.number_of_nodes() == 0:
        st.info("No nodes to display.")
    else:
        pos = nx.spring_layout(sub, k=0.65, iterations=60, seed=42)

        edge_x, edge_y = [], []
        for u, v in sub.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y, mode="lines",
            line=dict(width=0.55, color="rgba(120,150,180,0.25)"),
            hoverinfo="none",
        )

        node_x, node_y, colours, sizes, texts, labels = [], [], [], [], [], []
        for n in sub.nodes():
            x, y = pos[n]
            node_x.append(x)
            node_y.append(y)
            nd = sub.nodes[n]
            colours.append(nd.get("color", "#888"))
            sizes.append(max(9, min(nd.get("size", 10), 32)))
            lbl = nd.get("label", n)
            labels.append(lbl if len(lbl) <= 22 else lbl[:20] + "…")
            texts.append(
                f"<b>{lbl}</b><br>{nd.get('node_type','')}"
                f"<br>{nd.get('subtitle','')}"
                f"<br>links: {sub.degree(n)}"
                f"<br>documents: {nd.get('doc_count', '-')}"
            )

        node_trace = go.Scatter(
            x=node_x, y=node_y, mode="markers+text",
            marker=dict(size=sizes, color=colours,
                        line=dict(width=1.1, color="#0b1017")),
            text=labels, textposition="top center",
            textfont=dict(size=8.5, color="#8698ad", family="IBM Plex Mono"),
            hovertext=texts, hoverinfo="text",
        )

        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            showlegend=False, hovermode="closest",
            margin=dict(l=0, r=0, t=6, b=0), height=580,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        )
        st.plotly_chart(fig, use_container_width=True)

        legend = "".join(
            f'<span class="chip" style="border-color:{c};color:{c}">{t}</span>'
            for t, c in ENTITY_COLORS.items()
            if t in stats["node_types"] or t == "EQUIPMENT"
        )
        st.markdown(
            legend + '<span class="chip" style="border-color:#e2e8f0;color:#e2e8f0">DOCUMENT FILE</span>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="seclabel">Knowledge hubs</div>', unsafe_allow_html=True)
    st.caption(
        "Entities with the most connections. These are the assets and topics that "
        "bind the corpus together — and the ones whose documentation quality matters most."
    )
    hubs = central_entities(G, top_n=12)
    if hubs:
        st.dataframe(
            pd.DataFrame([{
                "Entity": h["label"],
                "Class": h["type"],
                "Connections": h["degree"],
                "Documents": h["doc_count"],
                "Mentions": h["frequency"],
            } for h in hubs]),
            use_container_width=True, hide_index=True,
        )


# ===========================================================================
# TAB 3 -- PATTERNS
# ===========================================================================
with tab_patterns:
    st.markdown(
        '<div class="seclabel">Lessons Learned &amp; Failure Intelligence</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "A failure recorded once is an event. The same failure on the same asset, "
        "recorded three times across three different systems by three different "
        "people, is a pattern — and it is exactly what no individual reviewer sees. "
        "These are surfaced by linking entities across the whole corpus."
    )

    min_support = st.slider(
        "Minimum documents for a pattern", 2, 6, 2,
        help="How many separate documents must contain the pairing before it is reported",
    )
    pats = find_patterns(G, docs, min_support=min_support)

    if not pats:
        st.info("No recurring patterns at this support threshold. Try lowering it.")
    else:
        st.caption(f"{len(pats)} recurring relationships detected")
        for p in pats[:20]:
            sev = "high" if p["support"] >= 4 else ("medium" if p["support"] == 3 else "low")
            kind = "Asset ↔ failure mode" if p["kind"] == "EQUIPMENT-FAILURE" \
                else "Substance ↔ failure mode"
            ev = " · ".join(e[:40] for e in p["evidence"][:5])
            st.markdown(
                f'<div class="finding {sev}">'
                f'<div class="t">{p["subject"]} — {p["object"]}</div>'
                f'<div class="d">{kind}. Recorded independently in '
                f'<b>{p["support"]} documents</b>.</div>'
                f'<div class="e">EVIDENCE: {ev}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ===========================================================================
# TAB 4 -- GAPS
# ===========================================================================
with tab_gaps:
    st.markdown(
        '<div class="seclabel">Knowledge Cliff Analysis</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "Around a quarter of India's experienced industrial engineers retire within "
        "the decade. The risk is not the documents that exist — it is the assets that "
        "run on knowledge nobody wrote down. This identifies where that dependency sits."
    )

    if not gaps:
        st.success("No documentation gaps detected in the current corpus.")
    else:
        high = [g for g in gaps if g["severity"] == "HIGH"]
        med = [g for g in gaps if g["severity"] == "MEDIUM"]

        c1, c2 = st.columns(2)
        c1.markdown(
            f'<div class="tile danger"><div class="v">{len(high)}</div>'
            f'<div class="k">Single-source assets</div>'
            f'<div class="d">Referenced in only one document</div></div>',
            unsafe_allow_html=True,
        )
        c2.markdown(
            f'<div class="tile warn"><div class="v">{len(med)}</div>'
            f'<div class="k">No procedural cover</div>'
            f'<div class="d">History exists, procedure does not</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown("")

        show_all = st.checkbox("Show all gaps", value=False)
        shown = gaps if show_all else (med + high)[:14]

        for g in shown:
            cls = g["severity"].lower()
            cls = "high" if cls == "high" else ("medium" if cls == "medium" else "low")
            klass = f" · {g['class']}" if g["class"] else ""
            st.markdown(
                f'<div class="finding {cls}">'
                f'<div class="t">{g["entity"]}{klass}</div>'
                f'<div class="d"><b>{g["gap"]}.</b> {g["detail"]}</div>'
                f'<div class="e">SEVERITY {g["severity"]} · LINKED DOCUMENTS {g["doc_count"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ===========================================================================
# TAB 5 -- COMPLIANCE
# ===========================================================================
with tab_compliance:
    st.markdown(
        '<div class="seclabel">Regulatory Coverage Matrix</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "Standards cited across the corpus, and whether each one is reflected in a "
        "controlled procedural document. A standard that appears only in incident and "
        "audit records — never in a procedure — is an evidence gap an auditor will find."
    )

    matrix = compliance_matrix(docs)
    if not matrix:
        st.info("No regulatory references detected in the current corpus.")
    else:
        gap_rows = [r for r in matrix if r["status"] == "Evidence Gap"]
        c1, c2 = st.columns(2)
        c1.markdown(
            f'<div class="tile accent"><div class="v">{len(matrix)}</div>'
            f'<div class="k">Standards referenced</div>'
            f'<div class="d">auto-extracted from text</div></div>',
            unsafe_allow_html=True,
        )
        c2.markdown(
            f'<div class="tile {"danger" if gap_rows else "ok"}">'
            f'<div class="v">{len(gap_rows)}</div>'
            f'<div class="k">Evidence gaps</div>'
            f'<div class="d">no procedural document cites these</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown("")

        df = pd.DataFrame([{
            "Standard": r["regulation"],
            "Documents": r["documents"],
            "Appears in": r["doc_types"],
            "Procedural cover": r["procedural_coverage"],
            "Status": r["status"],
        } for r in matrix])
        st.dataframe(df, use_container_width=True, hide_index=True)

        if gap_rows:
            st.markdown('<div class="seclabel">Flagged</div>', unsafe_allow_html=True)
            for r in gap_rows[:8]:
                st.markdown(
                    f'<div class="finding medium">'
                    f'<div class="t">{r["regulation"]}</div>'
                    f'<div class="d">Cited in {r["documents"]} document(s) — '
                    f'{r["doc_types"]} — but no controlled procedure references it. '
                    f'Compliance is asserted without procedural evidence.</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


# ===========================================================================
# TAB 6 -- CORPUS
# ===========================================================================
with tab_corpus:
    st.markdown('<div class="seclabel">Ingestion Record</div>', unsafe_allow_html=True)
    st.caption(
        "Every document is classified by type on ingest using keyword-signature "
        "voting, then chunked on structural boundaries and passed through the "
        "ontology extractor."
    )

    df = pd.DataFrame([{
        "Document": d["filename"],
        "Classified as": d["doc_type"],
        "Confidence": f"{d['type_confidence']:.0%}",
        "Pages": d["metadata"]["pages"],
        "Passages": d["metadata"]["n_chunks"],
        "Entities": d["metadata"]["n_entities"],
        "Size": f"{d['metadata']['size_kb']} KB",
    } for d in docs])
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown('<div class="seclabel">Extracted Entity Classes</div>', unsafe_allow_html=True)

    all_entities = [e for d in docs for e in d["entities"]]
    summary = entity_summary(all_entities)

    cols = st.columns(4)
    for i, (etype, values) in enumerate(sorted(
        summary.items(), key=lambda x: -sum(x[1].values())
    )):
        col = cols[i % 4]
        top = sorted(values.items(), key=lambda x: -x[1])[:6]
        chips = "".join(f'<span class="chip">{v} ×{c}</span>' for v, c in top)
        colour = ENTITY_COLORS.get(etype, "#888")
        col.markdown(
            f'<div class="tile" style="border-left:2px solid {colour};margin-bottom:0.6rem">'
            f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.66rem;'
            f'letter-spacing:0.1em;color:{colour}">{etype}</div>'
            f'<div class="v" style="font-size:1.3rem;margin-top:0.3rem">'
            f'{len(values)}</div>'
            f'<div class="d">{ENTITY_DESCRIPTIONS.get(etype,"")}</div>'
            f'<div style="margin-top:0.5rem">{chips}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="seclabel">Inspect a document</div>', unsafe_allow_html=True)
    pick = st.selectbox("Document", [d["filename"] for d in docs],
                        label_visibility="collapsed")
    doc = next(d for d in docs if d["filename"] == pick)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Type", doc["doc_type"])
    m2.metric("Passages", doc["metadata"]["n_chunks"])
    m3.metric("Entities", doc["metadata"]["n_entities"])
    m4.metric("Characters", f"{doc['metadata']['chars']:,}")

    esum = entity_summary(doc["entities"])
    for etype, values in sorted(esum.items()):
        chips = "".join(
            f'<span class="chip" style="border-color:{ENTITY_COLORS.get(etype)};'
            f'color:{ENTITY_COLORS.get(etype)}">{v}</span>'
            for v in sorted(values)[:14]
        )
        st.markdown(
            f'<div style="margin-bottom:0.4rem">'
            f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.64rem;'
            f'letter-spacing:0.1em;color:#8698ad">{etype}</span><br>{chips}</div>',
            unsafe_allow_html=True,
        )

    with st.expander("Raw extracted text"):
        st.text(doc["text"][:6000] + ("\n\n[truncated]" if len(doc["text"]) > 6000 else ""))
