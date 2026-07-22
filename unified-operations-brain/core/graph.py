"""
Industrial Knowledge Graph
==========================
Builds a heterogeneous graph linking documents to the entities they mention,
and entities to each other via document co-occurrence.

Schema
------
Node types:  DOCUMENT, EQUIPMENT, REGULATION, PARAMETER, PERSONNEL,
             FAILURE, CHEMICAL, LOCATION
Edge types:  MENTIONS      (document -> entity),   weight = occurrence count
             CO_OCCURS     (entity  <-> entity),   weight = shared documents

Why co-occurrence rather than a learned relation extractor: with a corpus of
tens to hundreds of documents, co-occurrence over a curated ontology gives a
graph that is both accurate and explainable -- every edge can be traced back to
the specific documents that produced it. That traceability is what makes the
graph usable as audit evidence, which a black-box relation model would forfeit.

The graph is the substrate for three capabilities the platform exposes:
  1. Cross-document discovery  -- "what else touches P-101A?"
  2. Systemic pattern mining   -- recurring failure/equipment pairs
  3. Knowledge-gap detection   -- orphaned or thinly-documented assets
"""

from collections import defaultdict, Counter
from itertools import combinations

import networkx as nx

from .ontology import ENTITY_COLORS, describe_equipment

# Entity classes admitted as graph nodes. PARAMETER is excluded by default --
# numeric readings are high-cardinality and would swamp the topology without
# adding relational signal. They remain queryable via retrieval.
GRAPH_ENTITY_TYPES = [
    "EQUIPMENT", "REGULATION", "PERSONNEL",
    "FAILURE", "CHEMICAL", "LOCATION", "DOCUMENT",
]

# Minimum occurrences before an entity earns a node -- suppresses OCR noise.
MIN_ENTITY_FREQ = 1


def build_graph(documents, include_parameters=False):
    """
    Construct the knowledge graph from a list of ingested document dicts.

    Returns a networkx.Graph with typed nodes and weighted edges.
    """
    allowed = list(GRAPH_ENTITY_TYPES)
    if include_parameters:
        allowed.append("PARAMETER")

    G = nx.Graph()

    # Track which documents each entity appears in, for co-occurrence
    entity_docs = defaultdict(set)
    entity_counts = Counter()

    for doc in documents:
        doc_node = f"DOC::{doc['doc_id']}"
        G.add_node(
            doc_node,
            node_type="DOCUMENT_FILE",
            label=doc["filename"],
            doc_type=doc["doc_type"],
            color="#e2e8f0",
            size=14,
        )

        # Aggregate entity occurrences within this document
        local = Counter()
        for ent in doc["entities"]:
            if ent["type"] not in allowed:
                continue
            key = (ent["type"], ent["value"])
            local[key] += 1

        for (etype, value), count in local.items():
            node_id = f"{etype}::{value}"
            entity_docs[node_id].add(doc["doc_id"])
            entity_counts[node_id] += count

            if node_id not in G:
                label = value
                subtitle = ""
                if etype == "EQUIPMENT":
                    subtitle = describe_equipment(value)
                G.add_node(
                    node_id,
                    node_type=etype,
                    label=label,
                    subtitle=subtitle,
                    color=ENTITY_COLORS.get(etype, "#888888"),
                    size=10,
                )

            G.add_edge(doc_node, node_id, edge_type="MENTIONS", weight=count)

    # ---- Entity-to-entity co-occurrence -----------------------------------
    # Two entities are linked when they appear in the same document. Edge
    # weight = number of shared documents, which acts as a confidence proxy.
    doc_entities = defaultdict(set)
    for node_id, docs in entity_docs.items():
        for d in docs:
            doc_entities[d].add(node_id)

    cooccur = Counter()
    for d, ents in doc_entities.items():
        # Cap combinatorial blowup on very entity-dense documents
        ents = sorted(ents)
        if len(ents) > 120:
            ents = [e for e in ents if entity_counts[e] > 1][:120]
        for a, b in combinations(ents, 2):
            cooccur[(a, b)] += 1

    for (a, b), w in cooccur.items():
        if G.has_edge(a, b):
            G[a][b]["weight"] += w
        else:
            G.add_edge(a, b, edge_type="CO_OCCURS", weight=w)

    # ---- Node sizing by degree -------------------------------------------
    for node in G.nodes():
        deg = G.degree(node)
        G.nodes[node]["degree"] = deg
        G.nodes[node]["size"] = 8 + min(deg, 30) * 1.2
        G.nodes[node]["frequency"] = entity_counts.get(node, 0)
        G.nodes[node]["doc_count"] = len(entity_docs.get(node, ()))

    return G


# ---------------------------------------------------------------------------
# GRAPH ANALYTICS
# ---------------------------------------------------------------------------

def graph_stats(G):
    """Headline metrics for the dashboard."""
    type_counts = Counter(
        G.nodes[n].get("node_type", "?") for n in G.nodes()
    )
    edge_types = Counter(
        G[u][v].get("edge_type", "?") for u, v in G.edges()
    )
    density = nx.density(G) if G.number_of_nodes() > 1 else 0.0
    components = nx.number_connected_components(G) if G.number_of_nodes() else 0

    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "node_types": dict(type_counts),
        "edge_types": dict(edge_types),
        "density": round(density, 4),
        "components": components,
    }


def central_entities(G, top_n=15, exclude_docs=True):
    """
    Rank entities by degree centrality -- the assets and topics that bind the
    corpus together. These are the organisation's knowledge hubs.
    """
    nodes = [
        n for n in G.nodes()
        if not (exclude_docs and G.nodes[n].get("node_type") == "DOCUMENT_FILE")
    ]
    if not nodes:
        return []

    sub = G.subgraph(nodes)
    ranked = sorted(
        sub.nodes(),
        key=lambda n: (G.degree(n), G.nodes[n].get("frequency", 0)),
        reverse=True,
    )[:top_n]

    return [
        {
            "id": n,
            "label": G.nodes[n].get("label", n),
            "type": G.nodes[n].get("node_type"),
            "degree": G.degree(n),
            "doc_count": G.nodes[n].get("doc_count", 0),
            "frequency": G.nodes[n].get("frequency", 0),
        }
        for n in ranked
    ]


def neighbourhood(G, node_id, hops=1, max_nodes=60):
    """Extract the local subgraph around an entity for focused exploration."""
    if node_id not in G:
        return G.subgraph([])
    nodes = {node_id}
    frontier = {node_id}
    for _ in range(hops):
        nxt = set()
        for n in frontier:
            nbrs = sorted(
                G.neighbors(n),
                key=lambda x: G[n][x].get("weight", 1),
                reverse=True,
            )
            nxt.update(nbrs[:25])
        nodes |= nxt
        frontier = nxt
        if len(nodes) >= max_nodes:
            break
    return G.subgraph(list(nodes)[:max_nodes])


def find_patterns(G, documents, min_support=2):
    """
    Systemic pattern mining: equipment-failure pairs recurring across
    MULTIPLE documents. This is the 'invisible to any individual review'
    capability -- a single maintenance engineer sees one work order; the
    graph sees the same failure mode on the same asset class across years.

    Returns ranked list of pattern dicts with supporting evidence.
    """
    # Map doc_id -> filename for evidence trails
    doc_names = {d["doc_id"]: d["filename"] for d in documents}

    # Build per-document entity sets by type
    per_doc = defaultdict(lambda: defaultdict(set))
    for d in documents:
        for ent in d["entities"]:
            per_doc[d["doc_id"]][ent["type"]].add(ent["value"])

    pair_docs = defaultdict(set)
    for doc_id, buckets in per_doc.items():
        equipment = buckets.get("EQUIPMENT", set())
        failures = buckets.get("FAILURE", set())
        chemicals = buckets.get("CHEMICAL", set())

        for eq in equipment:
            for fm in failures:
                pair_docs[("EQUIPMENT-FAILURE", eq, fm)].add(doc_id)
        for ch in chemicals:
            for fm in failures:
                pair_docs[("CHEMICAL-FAILURE", ch, fm)].add(doc_id)

    patterns = []
    for (kind, a, b), docs in pair_docs.items():
        if len(docs) < min_support:
            continue
        patterns.append({
            "kind": kind,
            "subject": a,
            "object": b,
            "support": len(docs),
            "doc_ids": sorted(docs),
            "evidence": [doc_names.get(d, d) for d in sorted(docs)],
        })

    patterns.sort(key=lambda p: p["support"], reverse=True)
    return patterns


def knowledge_gaps(G, documents):
    """
    Identify assets that are structurally under-documented.

    Two gap signals:
      - THIN COVERAGE : equipment mentioned in only one document
      - NO PROCEDURE  : equipment with incident/work-order coverage but
                        no linked SOP or manual

    This directly addresses the 'knowledge cliff' framing -- it tells you
    where undocumented expertise is currently load-bearing.
    """
    doc_types = {d["doc_id"]: d["doc_type"] for d in documents}

    gaps = []
    for n in G.nodes():
        if G.nodes[n].get("node_type") != "EQUIPMENT":
            continue

        linked_docs = [
            m for m in G.neighbors(n)
            if G.nodes[m].get("node_type") == "DOCUMENT_FILE"
        ]
        types_present = {
            doc_types.get(m.replace("DOC::", ""), "?") for m in linked_docs
        }

        label = G.nodes[n].get("label", n)
        subtitle = G.nodes[n].get("subtitle", "")

        procedural = {"Standard Operating Procedure", "Equipment Manual"}
        reactive = {"Incident Report", "Work Order", "Inspection Report"}

        if len(linked_docs) == 1:
            gaps.append({
                "entity": label,
                "class": subtitle,
                "severity": "HIGH",
                "gap": "Single-source coverage",
                "detail": f"Referenced in only 1 document ({len(linked_docs)} link). "
                          f"No corroborating record exists.",
                "doc_count": len(linked_docs),
            })
        elif (types_present & reactive) and not (types_present & procedural):
            gaps.append({
                "entity": label,
                "class": subtitle,
                "severity": "MEDIUM",
                "gap": "No procedural documentation",
                "detail": "Has incident/maintenance history but no linked SOP or "
                          "OEM manual. Operational knowledge is tacit.",
                "doc_count": len(linked_docs),
            })

    severity_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    gaps.sort(key=lambda g: (severity_rank.get(g["severity"], 9), -g["doc_count"]))
    return gaps


def compliance_matrix(documents):
    """
    Map regulatory references to the documents that cite them, and flag
    standards that appear in incident/audit records but have no procedural
    document referencing them -- a compliance evidence gap.
    """
    reg_docs = defaultdict(set)
    doc_type_of = {}

    for d in documents:
        doc_type_of[d["doc_id"]] = d["doc_type"]
        for ent in d["entities"]:
            if ent["type"] == "REGULATION":
                reg_docs[ent["value"]].add(d["doc_id"])

    rows = []
    procedural = {"Standard Operating Procedure", "Equipment Manual",
                  "Permit to Work", "Safety Datasheet"}

    for reg, docs in sorted(reg_docs.items(), key=lambda x: -len(x[1])):
        types = {doc_type_of[d] for d in docs}
        has_proc = bool(types & procedural)
        rows.append({
            "regulation": reg,
            "documents": len(docs),
            "doc_types": ", ".join(sorted(types)),
            "procedural_coverage": "Yes" if has_proc else "No",
            "status": "Covered" if has_proc else "Evidence Gap",
        })
    return rows
