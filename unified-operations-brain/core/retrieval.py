"""
Hybrid Retrieval Engine (fully offline, zero API cost)
======================================================
Three-signal fusion for retrieving evidence chunks:

  1. TF-IDF cosine       -- lexical similarity over character+word n-grams
  2. BM25                -- term saturation & length normalisation, which
                            outperforms raw TF-IDF on short technical queries
  3. Entity overlap      -- ontology-aware boost when the query names an
                            equipment tag, chemical, or standard that the
                            chunk also mentions

Why this beats naive embedding search *for this domain*:
Industrial queries are dominated by exact identifiers -- "P-101A", "OISD-STD-105",
"H2S". Dense embeddings notoriously blur these: 'P-101A' and 'P-102A' land in
almost the same vector neighbourhood. Lexical + ontology matching preserves the
exactness the domain demands, at zero inference cost, with fully explainable
scoring. Every retrieved result can state WHY it matched.

Character n-grams additionally give robustness to OCR noise and tag formatting
variance (P-101A / P101A / P 101 A).
"""

import re
import math
from collections import Counter, defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .ontology import extract_entities

# Fusion weights -- tuned so that an exact entity match can lift a chunk above
# a merely lexically-similar one, without letting it dominate entirely.
W_TFIDF = 0.25
W_BM25 = 0.28
W_ENTITY = 0.19
W_INTENT = 0.16
W_SUBJECT = 0.12

BM25_K1 = 1.5
BM25_B = 0.75

# ---------------------------------------------------------------------------
# QUERY INTENT SIGNALS
# ---------------------------------------------------------------------------
# Term matching alone answers "which documents mention X", not "which document
# ANSWERS my question about X". A work order that merely records a blocked
# strainer will out-score the OEM manual that states the cleaning interval,
# because both mention the same words.
#
# Intent detection closes that gap: we classify what KIND of answer the user
# wants, then boost chunks containing the linguistic markers of that answer
# type. This is the difference between a search engine and a knowledge system.

INTENT_PATTERNS = {
    "FREQUENCY": {
        "query": r"how often|frequency|interval|schedule|periodicity|how frequently|every how",
        "evidence": r"every\s+\d+|\d+\s*(?:day|days|month|months|year|years|hour|hours|week|weeks)"
                    r"|recommended frequency|shall be (?:inspected|cleaned|replaced|calibrated)"
                    r"|interval|periodic|routine|annually|monthly|quarterly",
    },
    "LIMIT": {
        "query": r"limit|threshold|setpoint|maximum|minimum|acceptable|allowable|"
                 r"what is the .*(?:level|value|rate|pressure|temperature)|exposure",
        "evidence": r"limit|threshold|shall not exceed|maximum|minimum required|"
                    r"acceptance|alarm|trip|setpoint|twa|stel|below|above|"
                    r"\d+\s*(?:ppm|barg|mm|degc|%)",
    },
    "PROCEDURE": {
        "query": r"how (?:do|to|should|is)|what steps|procedure|isolate|"
                 r"required before|process for|method",
        "evidence": r"step \d|shall|procedure|first|then|ensure|verify|confirm|"
                    r"apply|close|open|isolat|purge|lock",
    },
    "CAUSE": {
        "query": r"why|cause|reason|root cause|what led|how did .* (?:fail|happen)",
        "evidence": r"root cause|because|due to|caused by|resulted (?:in|from)|"
                    r"why \d|led to|consequence|failure mechanism|attributed",
    },
    "STATUS": {
        "query": r"status|open|outstanding|pending|closed|remain|implemented|"
                 r"what happened to|was .* (?:done|actioned|installed)",
        "evidence": r"status|not closed|not started|not implemented|not installed|"
                    r"outstanding|pending|deferred|completed|closed|pending",
    },
    "IDENTITY": {
        "query": r"which|what .*(?:were|was|are|is) (?:the )?\w+|list|identify|how many",
        "evidence": r"identified|found|recorded|raised|listed|total|\d+\s+\w+ (?:were|was)",
    },
}

_COMPILED_INTENT = {
    name: (re.compile(spec["query"], re.I), re.compile(spec["evidence"], re.I))
    for name, spec in INTENT_PATTERNS.items()
}


def detect_intent(query):
    """Return the set of intent labels a query expresses."""
    return {
        name for name, (q_re, _) in _COMPILED_INTENT.items()
        if q_re.search(query)
    }

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-&\.]*")

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "as", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "should", "could",
    "what", "which", "who", "whom", "when", "where", "why", "how", "all", "any",
    "this", "that", "these", "those", "it", "its", "if", "then", "than", "so",
    "we", "our", "you", "your", "i", "me", "my", "there", "here", "about",
}


def _tokenise(text):
    return [
        t.lower() for t in TOKEN_RE.findall(text or "")
        if t.lower() not in STOPWORDS and len(t) > 1
    ]


class RetrievalEngine:
    """
    Indexes chunks from ingested documents and serves hybrid ranked retrieval.

    Usage:
        engine = RetrievalEngine()
        engine.build(documents)
        hits = engine.search("seal failure on P-101A", top_k=5)
    """

    def __init__(self):
        self.chunks = []
        self.doc_lookup = {}
        self.vectorizer = None
        self.matrix = None
        self.chunk_tokens = []
        self.df = Counter()
        self.avg_len = 0.0
        self.chunk_entities = []
        self._ready = False

    # -- INDEX CONSTRUCTION -------------------------------------------------

    def build(self, documents):
        """Index every chunk across all supplied documents."""
        self.chunks = []
        self.doc_lookup = {d["doc_id"]: d for d in documents}

        for doc in documents:
            for ch in doc["chunks"]:
                self.chunks.append({
                    "chunk_id": ch["chunk_id"],
                    "doc_id": doc["doc_id"],
                    "filename": doc["filename"],
                    "doc_type": doc["doc_type"],
                    "page": ch.get("page", 1),
                    "section": ch.get("section", ""),
                    "text": ch["text"],
                })

        if not self.chunks:
            self._ready = False
            return self

        corpus = [c["text"] for c in self.chunks]

        # Word-level TF-IDF with sublinear scaling
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            sublinear_tf=True,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.92,
            token_pattern=r"[A-Za-z0-9][A-Za-z0-9\-&\.]*",
            stop_words=list(STOPWORDS),
        )
        self.matrix = self.vectorizer.fit_transform(corpus)

        # BM25 statistics
        self.chunk_tokens = [_tokenise(t) for t in corpus]
        self.df = Counter()
        for toks in self.chunk_tokens:
            for t in set(toks):
                self.df[t] += 1
        lengths = [len(t) for t in self.chunk_tokens]
        self.avg_len = sum(lengths) / max(len(lengths), 1)

        # Per-chunk entity sets for ontology-aware boosting
        self.chunk_entities = []
        for c in self.chunks:
            ents = extract_entities(c["text"])
            self.chunk_entities.append({
                (e["type"], e["value"].lower()) for e in ents
            })

        # Per-chunk intent evidence density, precomputed once at index time so
        # that query-time intent scoring is a lookup rather than a regex sweep.
        self.chunk_intents = []
        for c in self.chunks:
            marks = {}
            for name, (_, ev_re) in _COMPILED_INTENT.items():
                n_hits = len(ev_re.findall(c["text"]))
                if n_hits:
                    # Saturating density: presence matters most, volume a little
                    marks[name] = min(1.0, 0.55 + 0.15 * (n_hits - 1))
            self.chunk_intents.append(marks)

        # Document SUBJECT identifiers.
        #
        # A work order that references PTW-5518 and the permit PTW-5518 itself
        # both 'contain' that entity, so presence alone cannot separate them.
        # What separates them is that the permit is ABOUT it: the identifier
        # appears in the filename and the document header. Indexing subject
        # identity lets a query naming an entity prefer the document that is
        # the authoritative record for it over documents that merely cite it.
        self.doc_subjects = {}
        for doc in documents:
            head = doc["text"][:400]
            subj = set()
            for e in extract_entities(doc["filename"].replace("_", " ")):
                subj.add(e["value"].lower())
            for e in extract_entities(head):
                if e["type"] in ("DOCUMENT", "EQUIPMENT"):
                    subj.add(e["value"].lower())
            self.doc_subjects[doc["doc_id"]] = subj

        self._ready = True
        return self

    @property
    def ready(self):
        return self._ready and bool(self.chunks)

    # -- SCORING ------------------------------------------------------------

    def _bm25_scores(self, query_tokens):
        N = len(self.chunk_tokens)
        scores = np.zeros(N)
        if N == 0:
            return scores

        for term in set(query_tokens):
            df = self.df.get(term, 0)
            if df == 0:
                continue
            idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
            for i, toks in enumerate(self.chunk_tokens):
                tf = toks.count(term)
                if tf == 0:
                    continue
                dl = len(toks)
                denom = tf + BM25_K1 * (1 - BM25_B + BM25_B * dl / max(self.avg_len, 1))
                scores[i] += idf * (tf * (BM25_K1 + 1)) / denom

        mx = scores.max()
        return scores / mx if mx > 0 else scores

    def _subject_scores(self, query):
        """
        Boost chunks belonging to the document that a query's named entity is
        ABOUT, distinguishing the authoritative record from passing citations.
        """
        q_vals = {e["value"].lower() for e in extract_entities(query)}
        scores = np.zeros(len(self.chunks))
        if not q_vals:
            return scores

        for i, c in enumerate(self.chunks):
            subj = self.doc_subjects.get(c["doc_id"], set())
            if q_vals & subj:
                scores[i] = 1.0
        return scores

    def _intent_scores(self, query):
        """
        Score chunks by whether they contain the KIND of information the query
        asks for. A frequency question should surface the clause stating an
        interval, not merely another passage that mentions the same component.
        """
        intents = detect_intent(query)
        scores = np.zeros(len(self.chunks))
        if not intents:
            return scores, intents

        for i, marks in enumerate(self.chunk_intents):
            matched = [marks[k] for k in intents if k in marks]
            if matched:
                scores[i] = max(matched)
        return scores, intents

    def _entity_scores(self, query):
        q_ents = {
            (e["type"], e["value"].lower()) for e in extract_entities(query)
        }
        scores = np.zeros(len(self.chunks))
        if not q_ents:
            return scores, set()

        for i, ce in enumerate(self.chunk_entities):
            overlap = q_ents & ce
            if overlap:
                # Saturating: 1 match is most of the signal, more adds a little
                scores[i] = min(1.0, 0.6 + 0.2 * (len(overlap) - 1))
        return scores, q_ents

    # -- SEARCH -------------------------------------------------------------

    def search(self, query, top_k=6, doc_type_filter=None, min_score=0.02):
        """
        Hybrid ranked retrieval.

        Returns list of hit dicts including a per-signal score breakdown, so
        the UI can explain exactly why each result surfaced.
        """
        if not self.ready or not query.strip():
            return []

        # Signal 1: TF-IDF cosine
        qv = self.vectorizer.transform([query])
        tfidf = cosine_similarity(qv, self.matrix).flatten()
        if tfidf.max() > 0:
            tfidf = tfidf / tfidf.max()

        # Signal 2: BM25
        bm25 = self._bm25_scores(_tokenise(query))

        # Signal 3: ontology entity overlap
        ent_scores, q_ents = self._entity_scores(query)

        # Signal 4: answer-type intent match
        intent_scores, intents = self._intent_scores(query)

        # Signal 5: document subject identity
        subj_scores = self._subject_scores(query)

        combined = (W_TFIDF * tfidf + W_BM25 * bm25 +
                    W_ENTITY * ent_scores + W_INTENT * intent_scores +
                    W_SUBJECT * subj_scores)

        order = np.argsort(-combined)
        hits = []
        for idx in order:
            if len(hits) >= top_k:
                break
            score = float(combined[idx])
            if score < min_score:
                break
            c = self.chunks[idx]
            if doc_type_filter and c["doc_type"] not in doc_type_filter:
                continue

            matched = sorted(
                {v for (t, v) in (q_ents & self.chunk_entities[idx])}
            )
            hits.append({
                **c,
                "score": round(score, 4),
                "signals": {
                    "tfidf": round(float(tfidf[idx]), 3),
                    "bm25": round(float(bm25[idx]), 3),
                    "entity": round(float(ent_scores[idx]), 3),
                    "intent": round(float(intent_scores[idx]), 3),
                    "subject": round(float(subj_scores[idx]), 3),
                },
                "matched_entities": matched,
                "matched_intents": sorted(intents & set(self.chunk_intents[idx])),
            })
        return hits

    # -- ANSWER SYNTHESIS ---------------------------------------------------

    def answer(self, query, top_k=5, doc_type_filter=None):
        """
        Extractive, citation-first answer synthesis.

        No generative model is used. For an industrial knowledge system this
        is a deliberate safety property, not a limitation: a maintenance
        engineer acting on a hallucinated torque value or clearance is a
        safety incident. Every sentence returned is verbatim from a source
        document with a traceable citation.

        Confidence is derived from retrieval score distribution and source
        agreement, and is reported honestly -- including when it is low.
        """
        hits = self.search(query, top_k=top_k, doc_type_filter=doc_type_filter)
        if not hits:
            return {
                "found": False,
                "answer": "No supporting evidence found in the indexed corpus.",
                "confidence": 0.0,
                "confidence_label": "No Evidence",
                "citations": [],
                "hits": [],
            }

        q_tokens = set(_tokenise(query))
        q_intents = detect_intent(query)
        passages = []

        for rank, h in enumerate(hits, start=1):
            best_sent, best_overlap = self._best_sentences(
                h["text"], q_tokens, intents=q_intents
            )
            if not best_sent:
                continue
            passages.append({
                "rank": rank,
                "text": best_sent,
                "filename": h["filename"],
                "doc_type": h["doc_type"],
                "page": h["page"],
                "section": h["section"],
                "chunk_id": h["chunk_id"],
                "score": h["score"],
                "overlap": best_overlap,
                "matched_entities": h["matched_entities"],
            })

        top_score = hits[0]["score"]
        agreement = self._source_agreement(hits)
        confidence = min(0.99, 0.55 * top_score + 0.30 * agreement +
                         0.15 * min(len(passages) / 3.0, 1.0))

        if confidence >= 0.62:
            label = "High"
        elif confidence >= 0.38:
            label = "Moderate"
        else:
            label = "Low - verify against source"

        return {
            "found": True,
            "answer": passages[0]["text"] if passages else hits[0]["text"][:400],
            "passages": passages,
            "confidence": round(confidence, 3),
            "confidence_label": label,
            "source_agreement": round(agreement, 3),
            "citations": [
                {
                    "n": i + 1,
                    "filename": p["filename"],
                    "page": p["page"],
                    "section": p["section"],
                    "doc_type": p["doc_type"],
                }
                for i, p in enumerate(passages)
            ],
            "hits": hits,
        }

    @staticmethod
    def _best_sentences(text, q_tokens, intents=None, max_sentences=2):
        """
        Select the sentences that ANSWER the query, not merely those that
        echo its vocabulary.

        Query-term overlap alone systematically prefers sentences that restate
        the question ("Seal flush line found restricted") over the sentence
        carrying the answer ("The strainer element shall be cleaned every
        90 days"). Three additional signals correct this:

          - intent evidence : does the sentence contain the answer TYPE asked for
          - specificity     : concrete values (numbers, units, tags) score higher
          - declarativeness : normative statements ('shall', 'is', 'was') over
                              narrative fragments
        """
        intents = intents or set()
        sentences = re.split(r"(?<=[.!?])\s+|\n(?=[A-Z0-9])|\n{2,}", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 25]
        if not sentences:
            return text[:300].strip(), 0

        NUM_RE = re.compile(r"\d")
        UNIT_HINT = re.compile(
            r"\d+\s*(?:ppm|barg|bar|mm|mm/s|degc|°c|%|days?|months?|years?|hours?)",
            re.I,
        )
        NORMATIVE = re.compile(
            r"\bshall\b|\bmust\b|\bis\b|\bwas\b|\bare\b|\brequired\b|"
            r"\brecommended\b|\bnot\b",
            re.I,
        )

        scored = []
        for pos, s in enumerate(sentences):
            toks = set(_tokenise(s))
            overlap = len(q_tokens & toks)

            score = float(overlap) * 1.0

            # Intent evidence: the strongest correction signal
            for name in intents:
                _, ev_re = _COMPILED_INTENT[name]
                if ev_re.search(s):
                    score += 2.4
                    break

            # Specificity: concrete values are what an engineer needs
            if UNIT_HINT.search(s):
                score += 1.6
            elif NUM_RE.search(s):
                score += 0.5

            # Declarative statements over narrative fragments
            if NORMATIVE.search(s):
                score += 0.4

            # Mild positional prior: leading sentences of a chunk carry the
            # section's main assertion more often than trailing ones.
            score += max(0.0, 0.3 - pos * 0.04)

            scored.append((score, overlap, pos, s))

        scored.sort(key=lambda x: -x[0])
        top = scored[:max_sentences]
        if not top:
            return sentences[0], 0

        best_overlap = max(o for _, o, _, _ in top)
        # Restore document order for readability
        chosen = sorted(top, key=lambda x: x[2])
        return " ".join(s for _, _, _, s in chosen), best_overlap

    @staticmethod
    def _source_agreement(hits):
        """
        Fraction of top hits drawn from distinct documents. Corroboration
        across independent sources raises confidence; several hits from one
        file does not.
        """
        if not hits:
            return 0.0
        distinct = len({h["doc_id"] for h in hits})
        return min(1.0, distinct / min(len(hits), 3))


# ---------------------------------------------------------------------------
# QUERY SUGGESTION
# ---------------------------------------------------------------------------

def suggest_queries(documents, limit=8):
    """
    Generate corpus-grounded example questions so a judge can immediately
    exercise the system without knowing the data. Suggestions are built from
    the highest-frequency entities actually present.
    """
    eq = Counter()
    fail = Counter()
    reg = Counter()
    chem = Counter()

    for d in documents:
        for e in d["entities"]:
            if e["type"] == "EQUIPMENT":
                eq[e["value"]] += 1
            elif e["type"] == "FAILURE":
                fail[e["value"]] += 1
            elif e["type"] == "REGULATION":
                reg[e["value"]] += 1
            elif e["type"] == "CHEMICAL":
                chem[e["value"]] += 1

    out = []
    for tag, _ in eq.most_common(3):
        out.append(f"What is the maintenance history of {tag}?")
    for f, _ in fail.most_common(2):
        out.append(f"Which equipment has experienced {f}?")
    for r, _ in reg.most_common(2):
        out.append(f"What are the requirements under {r}?")
    for c, _ in chem.most_common(1):
        out.append(f"What are the exposure controls for {c}?")

    return out[:limit]
