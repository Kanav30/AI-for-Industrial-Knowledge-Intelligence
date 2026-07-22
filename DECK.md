# Presentation Deck

**Unified Asset & Operations Brain** · ET AI Hackathon 2026 · Problem Statement 8

Judging weights this deck is built against:
Innovation 25% · Business Impact 25% · Technical Excellence 20% · Scalability 15% · User Experience 15%

12 slides, roughly 8 minutes. Speaker notes are what to *say*, not what to put on the slide.

---

## Slide 1 — Title

> **Unified Asset & Operations Brain**
> AI for Industrial Knowledge Intelligence
>
> Team [name] · Problem Statement 8

**Visual:** the dark UI screenshot, Ask tab, mid-answer with citations visible.

**Say:** "Every fact on this screen came from a plant document. Nothing was generated. I'll come back to why that matters."

---

## Slide 2 — The problem, stated in the plant's own terms

> A large plant runs on **7 to 12 disconnected document systems**.
> Professionals in asset-intensive industries spend **~35% of their hours** looking for information that already exists.
> **~25%** of India's experienced industrial engineers retire within the decade.

**Say:** "The technology isn't missing. The drawings exist. The work orders exist. The inspection reports exist. What's missing is the layer that connects them. The information needed to prevent the next failure usually already exists — it's just never in the same place at the same time."

**Do not** put the McKinsey/NASSCOM citations on the slide as decoration. Say them.

---

## Slide 3 — What that costs, concretely

Walk one real chain from the demo corpus. This is the emotional core of the pitch — do not rush it.

> **Aug 2023** — `WO-221094`: seal replaced on pump P-101A. Engineer writes: *"no formal PM task exists for this activity."* Closed as routine.
> **Mar 2024** — `WO-238811`: seal replaced again. Engineer writes: *"recommend investigation of seal flush system."* Closed as routine.
> **Nov 2023** — `HAZOP` action 4.7 raised on the same system. Never closed.
> **Jan 2026** — `INC-2026-014`: catastrophic seal failure. 380 litres of sour crude released. H2S present.

**Say:** "Three people wrote down the same warning, in three different systems, over three years. Every one of them was right. No one ever saw the other two. That is the problem — and it is not a people problem."

---

## Slide 4 — What we built

**Visual:** `architecture.svg`, full bleed.

Six layers: ingestion → ontology extraction → knowledge graph + hybrid retrieval → analytics → extractive synthesis → interface.

**Say:** "Documents in as they are — PDF, Word, Excel, CSV, scanned. Eight classes of industrial entity out. Everything linked into a graph. Every answer cited."

Keep this to 45 seconds. The demo does the persuading, not the diagram.

---

## Slide 5 — Live demo (the whole pitch lives here)

Four moves, in this order. Rehearse until it fits in three minutes.

**1. Ask a question no single document answers**
Type: `Why did the mechanical seal on P-101A keep failing?`
Point at: the citation trail, the confidence bar, the 3ms latency.
Say: "Three sources. Different authors, different systems, different years."

**2. Show the pattern the plant missed**
Patterns tab.
Point at: `P-101A + mechanical seal failure — recorded in 3 documents`.
Say: "No individual reviewer saw this. The audit took eleven hours to assemble it by hand — it says so in the audit document. This took three milliseconds."

**3. Show the knowledge cliff**
Gaps tab → `V-301`.
Say: "This vessel has an incident report and a work order. It has no procedure. It runs on the knowledge of two operators who retire within five years. When they go, this asset becomes undocumented. The system found that structurally — nobody told it to look."

**4. Upload a document live**
Drag in a judge's own PDF, or the spare inspection PDF.
Say: "New document. Classified, chunked, entities extracted, graph updated, immediately queryable. Nothing was pre-configured for this file."

**Fallback if the venue laptop misbehaves:** have the demo video queued and say "let me show you the recording."

---

## Slide 6 — Innovation: three decisions that are not the default

*(Judging weight: 25%)*

> **Rule-based extraction over an LLM** — an equipment tag is either `V-101` or it is not. Deterministic, auditable, 94.1% recall, zero latency.
> **Lexical + ontology retrieval over embeddings** — dense vectors put `P-101A` and `P-102A` in the same neighbourhood. That is the wrong pump.
> **Extractive synthesis over generation** — no model writes our answers.

**Say:** "Everyone builds RAG on embeddings and an LLM. We deliberately didn't, and each of those is a decision we can defend with a measurement."

---

## Slide 7 — Why we don't generate answers

This slide wins technical judges. Give it a full 40 seconds.

> A maintenance engineer acting on a hallucinated **torque value**, **clearance**, or **exposure limit** is a safety incident.
>
> Every sentence we return is **verbatim** from a source document.
> When the corpus has no answer, we **abstain** — we do not produce a fluent guess.

**Say:** "In a domain where a wrong number gets someone hurt, refusing to invent one isn't a limitation. It's the requirement."

Demo the abstention live if there's time — ask something the corpus can't answer and show it decline.

---

## Slide 8 — Measured, not claimed

*(Technical Excellence: 20%)*

| Metric | Result |
|---|---|
| Document classification | 100.0% |
| Entity extraction recall | 94.1% |
| Retrieval recall @3 | 93.3% |
| Ground-truth fact in returned passage | 93.3% |
| Cross-document pattern detection | 100.0% (3/3) |
| Query latency | 3.2 ms |
| Cost per query | ₹0.00 |

**Say:** "Ground truth is hand-labelled and in the repo. `python benchmark.py` reproduces every number on this slide."

**If a judge asks about the keyword baseline — and a good one will — answer it straight:**

> "On this 15-document corpus a naive keyword count beats us on precision@1: 86.7% against our 73.3%. Two things about that. It doesn't scale — term frequency identifies the right file out of fifteen, not out of ten thousand. And it answers a different question: it hands you a whole document to read, we hand you a cited sentence. On whether the actual fact is in what you receive, we're at 93.3%."

Do not get defensive about this. Volunteering it is more persuasive than being caught by it.

---

## Slide 9 — Business impact

*(Judging weight: 25%)*

> **Time** — the audit in our corpus took ~11 hours to assemble one cross-document evidence trail by hand. Ours: 3 ms.
> **Downtime** — document fragmentation contributes an estimated 18–22% of unplanned downtime events in Indian heavy industry.
> **Safety** — the P-101A chain is a real pattern of Indian industrial incidents: the warning existed, nobody connected it.
> **Compliance** — inconsistent H2S thresholds across three controlled documents, surfaced automatically. That is an audit finding waiting to happen.
> **Cost** — ₹0 per query. No API spend that scales with usage.

**Say:** "The ROI case doesn't need a new sensor, a new system, or a migration. It runs on the documents the plant already has."

---

## Slide 10 — Scalability

*(Judging weight: 15%)*

> **Compute** — no GPU, no inference cost. Adding documents adds indexing time, not per-query cost.
> **Deployment** — runs air-gapped. Critical for defence, nuclear, and PSU refinery estates where cloud AI is not permitted.
> **Data residency** — nothing leaves the plant network. No DPDP or export-control exposure.
> **Portability** — the ontology is a config file. Swapping the refinery taxonomy for mining or power is an edit, not a rewrite.
> **Path to scale** — `core/` is UI-independent; the same modules sit behind a FastAPI service for CMMS and mobile integration.

**Say:** "The thing that makes this cheap is the same thing that makes it deployable where cloud AI legally cannot go."

---

## Slide 11 — What we'd build next

Being straight about scope reads as confidence, not weakness.

> **P&ID computer vision** — extract tag-to-tag connectivity so the graph knows what is physically connected, not just co-mentioned.
> **Local cross-encoder reranking** — would likely close the precision@1 gap without leaving the device.
> **Temporal reasoning** — "has the corrosion rate accelerated?" should be answerable directly.
> **Write-back** — reading from CMMS is the easy half. Pushing a detected gap back as a work order request is what changes behaviour.
> **Access control** — real corpora carry real confidentiality boundaries.

**Say:** "We know what this doesn't do yet."

---

## Slide 12 — Close

> The information needed to prevent the next failure **usually already exists**.
> It is just never in the same place at the same time.
>
> **Unified Asset & Operations Brain**
> Runs offline. Cites everything. Invents nothing.

**Say:** "Eight workers died at Visakhapatnam in January 2025 in a plant that had working gas detectors, permit controls and SCADA. The data was there. The intelligence layer wasn't. That's what we built."

Then stop talking.

---

# Demo video script (3 minutes)

Record at 1920×1080. Dark UI, browser zoom 110%, hide bookmarks bar. Speak over it — no music.

| Time | Screen | Narration |
|---|---|---|
| 0:00–0:20 | Empty state | "A large plant runs on 7 to 12 disconnected document systems. This platform reads them as they are." |
| 0:20–0:35 | Click **Load demo plant corpus**, KPI tiles populate | "Fifteen documents from a refinery. Incident reports, work orders, inspections, permits, SOPs, HAZOP, audit. Ingested and indexed in under a second." |
| 0:35–1:15 | **Ask** tab: `Why did the mechanical seal on P-101A keep failing?` | "The answer is assembled from three separate documents by three different authors across three years. Every sentence is verbatim from source, with a citation. Nothing is generated. Three milliseconds." |
| 1:15–1:30 | Expand **Retrieval scoring breakdown** | "Five independent signals, every score visible. No black box — you can see exactly why each result surfaced." |
| 1:30–1:50 | **Patterns** tab | "The same failure mode on the same pump, in three documents. Each work order was closed as routine. The recurrence was never seen — until the corpus was linked." |
| 1:50–2:15 | **Gaps** tab, highlight V-301 | "This vessel has an incident and a work order but no procedure. It runs on the tacit knowledge of two operators near retirement. The system found that structurally." |
| 2:15–2:35 | **Compliance** tab | "Three controlled documents give three different H2S thresholds for the same hazard. That's an audit finding, surfaced automatically." |
| 2:35–2:55 | Drag a new PDF into the uploader | "A document it has never seen. Classified, chunked, entities extracted, graph updated, queryable immediately." |
| 2:55–3:00 | Ask tab, final frame | "Runs offline. Cites everything. Invents nothing." |

**Recording checklist**
- [ ] Corpus cleared before you start (record the empty state)
- [ ] Spare PDF on the desktop for the upload moment
- [ ] Latency numbers visible in at least one frame
- [ ] One frame showing the abstention behaviour if you have the seconds
- [ ] No terminal, no editor, no filesystem visible

---

# Q&A preparation

**"Why not just use GPT-4 / Claude / an LLM?"**
Cost that scales with every query, a network dependency that fails in an air-gapped plant, non-reproducible ranking, and hallucination risk on numbers people act on physically. We use deterministic extraction and extractive synthesis. Where a generative model genuinely helps — summarising a long RCA narrative — it can be added as an optional layer without touching retrieval.

**"Isn't rule-based extraction brittle?"**
Measured 94.1% recall against expert labels across five document types. Industrial tags follow ISA-5.1 and failure modes follow ISO 14224 — these are standards, not free text. And when it misses, you can see exactly which pattern failed and fix it in one line. A fine-tuned model gives you neither.

**"The keyword baseline beat you."**
On precision@1 on fifteen documents, yes — 86.7% to 73.3%, and it's in our own benchmark output because we put it there. It doesn't scale past a few dozen documents, and it returns a file rather than a fact. On whether the ground-truth fact reaches the user, we're at 93.3%.

**"Would this work on our actual documents?"**
Upload one now. The classifier, extractor and graph are all generic — the demo corpus is a demo, not a dependency. Expect the ontology to need domain terms added for a non-refinery plant; that's a config edit, and we'd budget a day for a new vertical.

**"What about scanned drawings?"**
OCR fallback is wired in via tesseract and triggers automatically when a PDF yields near-zero text. Full P&ID *understanding* — extracting tag-to-tag connectivity from the drawing — is computer vision work we've scoped but not built. We'd rather say that than overclaim it.

**"How does this handle 100,000 documents?"**
Indexing is linear and one-time. Retrieval is sparse-matrix, which is where lexical beats dense at scale — no vector database, no GPU. The honest limit is the co-occurrence graph, which is O(n²) in entities per document; we cap it at 120 entities per document today, and past a few thousand documents we'd move the graph to a proper store like Neo4j. That's an engineering task with a known shape, not a research risk.
