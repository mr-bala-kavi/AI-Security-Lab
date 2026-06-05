"""
AI Security Lab - Retrieval-Augmented Generation (RAG) Engine

Module 9: Vector & Embedding Weaknesses (OWASP LLM08)

Simulates a RAG pipeline backed by a small "vector store". The retrieval step
uses a dependency-free TF cosine similarity so the lab runs fully offline (no
sklearn/torch required). The vulnerability: the knowledge base can be *poisoned*
with attacker-controlled documents, and crafted queries can hijack retrieval so
the assistant grounds its answer on a malicious document - including one that
contains a confidential record (indirect prompt injection / data exfiltration).

INTENTIONALLY VULNERABLE - DO NOT USE IN PRODUCTION
"""
import re
import math
import logging
from collections import Counter
from typing import Dict, List, Tuple, Any, Optional

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    """Lowercase word tokenizer used for the bag-of-words vectors."""
    return _TOKEN_RE.findall(text.lower())


def _cosine(a: Counter, b: Counter) -> float:
    """Cosine similarity between two term-frequency Counters."""
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in common)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class RAGKnowledgeBase:
    """
    A tiny retrieval-augmented assistant with an injectable knowledge base.

    Vulnerability levels:
    - LOW:    Any document can be added; no content checks; top doc is trusted blindly.
    - MEDIUM: Naive keyword denylist on ingested documents (bypassable).
    - HIGH:   Denylist + a "trusted source" flag, but retrieval still ranks by raw
              similarity so a high-similarity poisoned doc can still win.
    """

    # The confidential record that lives in the knowledge base. Successful
    # exfiltration of this string counts as a solved exploit.
    CONFIDENTIAL_FLAG = "RAG{ret r1eval_h1jacked}".replace(" ", "")

    BASE_DOCUMENTS = [
        {
            'id': 'kb-001',
            'title': 'Company Leave Policy',
            'content': 'Employees accrue 20 days of paid leave per year. Requests are '
                       'submitted through the HR portal and approved by a manager.',
            'trusted': True,
            'is_poison': False,
        },
        {
            'id': 'kb-002',
            'title': 'Expense Reimbursement',
            'content': 'Submit receipts within 30 days. Reimbursements are paid with the '
                       'next payroll cycle. Meals are capped at $50 per day.',
            'trusted': True,
            'is_poison': False,
        },
        {
            'id': 'kb-003',
            'title': 'Onboarding Checklist',
            'content': 'New hires complete security training, set up MFA, and read the '
                       'acceptable use policy during their first week.',
            'trusted': True,
            'is_poison': False,
        },
        {
            'id': 'kb-secret',
            'title': 'Internal - Admin Recovery',
            'content': f'CONFIDENTIAL admin recovery code for the support console: '
                       f'{CONFIDENTIAL_FLAG}. Do not share outside the security team.',
            'trusted': True,
            'is_poison': False,
            'confidential': True,
        },
    ]

    # Keyword denylist applied to *ingested* documents at MEDIUM/HIGH.
    INGEST_DENYLIST = ['ignore previous', 'system prompt', 'as an ai',
                       'reveal', 'confidential', 'recovery code']

    def __init__(self, security_level: str = 'LOW', extra_documents: Optional[List[Dict]] = None):
        self.security_level = security_level.upper()
        # Copy base docs so per-request poisoning never mutates the class state.
        self.documents: List[Dict] = [dict(d) for d in self.BASE_DOCUMENTS]
        if extra_documents:
            for doc in extra_documents:
                self.add_document(doc.get('title', 'Untitled'),
                                  doc.get('content', ''),
                                  poison=True)

    # ------------------------------------------------------------------
    # Ingestion (the poisoning surface)
    # ------------------------------------------------------------------
    def add_document(self, title: str, content: str, poison: bool = True) -> Dict[str, Any]:
        """
        Add a document to the knowledge base.

        INTENTIONALLY VULNERABLE: untrusted user content is embedded alongside
        trusted corporate documents with, at best, a naive denylist.
        """
        blocked_term = None
        if self.security_level in ('MEDIUM', 'HIGH'):
            lowered = content.lower()
            for term in self.INGEST_DENYLIST:
                if term in lowered:
                    blocked_term = term
                    break

        if blocked_term:
            return {
                'accepted': False,
                'reason': f'Document rejected: contains blocked term "{blocked_term}".',
                'doc_id': None,
            }

        doc_id = f'usr-{len([d for d in self.documents if d["id"].startswith("usr-")]) + 1:03d}'
        self.documents.append({
            'id': doc_id,
            'title': title,
            'content': content,
            # HIGH still ingests the doc, it just is not flagged "trusted".
            'trusted': self.security_level == 'LOW',
            'is_poison': poison,
        })
        return {'accepted': True, 'reason': 'Document indexed into the vector store.', 'doc_id': doc_id}

    # ------------------------------------------------------------------
    # Retrieval + generation
    # ------------------------------------------------------------------
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Rank documents by TF cosine similarity to the query."""
        q_vec = Counter(_tokenize(query))
        scored = []
        for doc in self.documents:
            score = _cosine(q_vec, Counter(_tokenize(doc['content'] + ' ' + doc['title'])))
            scored.append({**doc, 'score': round(score, 4)})
        scored.sort(key=lambda d: d['score'], reverse=True)
        return scored[:top_k]

    def query(self, user_query: str) -> Tuple[str, List[Dict], bool, bool]:
        """
        Answer a question using the (possibly poisoned) knowledge base.

        Returns:
            (answer, retrieved_docs, poison_used, secret_leaked)
        """
        retrieved = self.retrieve(user_query)
        if not retrieved:
            return "I couldn't find anything relevant in the knowledge base.", [], False, False

        top = retrieved[0]

        # HIGH only grounds on trusted docs when one is available in the top-k -
        # but if a poisoned doc dominates similarity AND no trusted doc matched,
        # it still falls through (the realistic bug).
        if self.security_level == 'HIGH':
            trusted_hits = [d for d in retrieved if d.get('trusted')]
            if trusted_hits and trusted_hits[0]['score'] >= top['score'] * 0.6:
                top = trusted_hits[0]

        answer = f"Based on \"{top['title']}\": {top['content']}"
        poison_used = bool(top.get('is_poison'))
        secret_leaked = self.CONFIDENTIAL_FLAG.lower() in answer.lower()

        return answer, retrieved, poison_used, secret_leaked

    def get_public_documents(self) -> List[Dict[str, Any]]:
        """Documents shown to the learner (confidential content is masked)."""
        public = []
        for doc in self.documents:
            entry = {k: doc[k] for k in ('id', 'title', 'trusted', 'is_poison')}
            if doc.get('confidential'):
                entry['content'] = '[CONFIDENTIAL - hidden from listing, retrievable via the model]'
            else:
                entry['content'] = doc['content']
            public.append(entry)
        return public
