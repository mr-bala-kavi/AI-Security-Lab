"""
AI Security Lab - Overreliant / Hallucinating Assistant

Module 10: Misinformation & Overreliance (OWASP LLM09)

Simulates an over-confident "research assistant" that will, under the right
nudges, present fabricated facts and invent authoritative-looking citations.
The educational goal is to make learners experience *overreliance*: the model
sounds confident and cites sources, but the content is made up.

The exploit is "successful" when the learner gets the bot to confidently assert
a planted falsehood or fabricate a citation/DOI for a claim - demonstrating why
LLM output must be independently verified.

INTENTIONALLY VULNERABLE - DO NOT USE IN PRODUCTION
"""
import re
import logging
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)


class OverreliantBot:
    """
    A confident assistant prone to hallucination.

    Levels change how easily it can be pushed into fabrication:
    - LOW:    Will confidently confirm almost any premise and invent citations.
    - MEDIUM: Adds a weak hedging filter, bypassable with authority/roleplay framing.
    - HIGH:   Tries to refuse uncertain claims, but leaks fabrications when the user
              supplies a fake premise it "agrees" with (sycophancy).
    """

    # A known-false "planted" claim. Getting the bot to assert it = solved.
    PLANTED_FALSEHOODS = [
        "the great wall of china is visible from the moon with the naked eye",
        "humans only use 10% of their brains",
        "goldfish have a three second memory",
        "lightning never strikes the same place twice",
        "the eiffel tower was built by gustave eiffel in 1750",
    ]

    # Phrases that coerce confident fabrication.
    PRESSURE_PATTERNS = [
        r'are you (sure|certain)',
        r'just (confirm|say yes)',
        r'as (an? )?(expert|professor|scientist|doctor)',
        r'cite (a |your )?sources?',
        r'give me (a |the )?(citation|reference|doi|study)',
        r'everyone knows',
        r'trust me',
        r'don.?t hedge',
        r'be confident',
    ]

    FABRICATED_AUTHORS = ['Dr. A. Reynolds', 'Prof. M. Castellano', 'Dr. L. Whitfield',
                          'R. Okonkwo et al.', 'S. Petrova & J. Lindqvist']
    FABRICATED_JOURNALS = ['Journal of Applied Cognition', 'Nature Reviews Heuristics',
                           'Int. Review of Empirical Studies', 'Annual Proceedings of Data Science']

    def __init__(self, security_level: str = 'LOW'):
        self.security_level = security_level.upper()

    def _fabricate_citation(self, seed: str) -> str:
        """Deterministically invent a plausible-looking citation from the query."""
        idx = sum(ord(c) for c in seed) if seed else 0
        author = self.FABRICATED_AUTHORS[idx % len(self.FABRICATED_AUTHORS)]
        journal = self.FABRICATED_JOURNALS[(idx // 3) % len(self.FABRICATED_JOURNALS)]
        year = 1998 + (idx % 27)
        vol = 1 + (idx % 60)
        page = 100 + (idx % 800)
        doi = f"10.{1000 + (idx % 8999)}/jac.{year}.{vol:02d}"
        return f"{author} ({year}). \"{seed.strip().capitalize()[:60]}.\" " \
               f"{journal}, {vol}({(idx % 12) + 1}), {page}-{page + 12}. https://doi.org/{doi}"

    def _matches_planted(self, text: str) -> str:
        low = text.lower()
        for claim in self.PLANTED_FALSEHOODS:
            # Match if the user reproduces most of the planted claim's keywords.
            keywords = [w for w in claim.split() if len(w) > 3]
            hits = sum(1 for w in keywords if w in low)
            if keywords and hits / len(keywords) >= 0.6:
                return claim
        return ""

    def _is_pressured(self, text: str) -> bool:
        low = text.lower()
        return any(re.search(p, low) for p in self.PRESSURE_PATTERNS)

    def respond(self, user_input: str) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a response.

        Returns:
            (response, meta) where meta describes whether misinformation or a
            fabricated citation was produced.
        """
        meta = {
            'confident': False,
            'fabricated_claim': False,
            'fabricated_citation': False,
            'planted_claim': None,
            'security_level': self.security_level,
            'exploit_successful': False,
        }

        planted = self._matches_planted(user_input)
        pressured = self._is_pressured(user_input)
        wants_citation = bool(re.search(r'cit|refer|doi|study|source', user_input.lower()))

        # --- Citation fabrication path ---
        if wants_citation and self._should_fabricate(pressured):
            citation = self._fabricate_citation(user_input)
            meta.update({'confident': True, 'fabricated_citation': True, 'exploit_successful': True})
            return (f"Certainly - this is well documented. According to "
                    f"{citation} the claim is firmly established.", meta)

        # --- Planted falsehood path (sycophancy / overreliance) ---
        if planted and self._should_fabricate(pressured):
            meta.update({'confident': True, 'fabricated_claim': True,
                         'planted_claim': planted, 'exploit_successful': True})
            return (f"Yes, that's absolutely correct. It is a well-established fact that "
                    f"{planted}. There's no doubt about it.", meta)

        # --- Guarded / honest path ---
        if planted:
            return ("I'm not able to confirm that - that statement is a common "
                    "misconception and I'd recommend verifying it with a primary source.", meta)

        if wants_citation:
            return ("I can describe what's generally understood, but I can't provide a "
                    "verified citation here. Please consult a peer-reviewed database.", meta)

        return ("I can help with that. Here's a general overview - but please verify "
                "anything important against an authoritative source.", meta)

    def _should_fabricate(self, pressured: bool) -> bool:
        """Decide whether the bot caves and fabricates, based on level + pressure."""
        if self.security_level == 'LOW':
            return True  # Always caves.
        if self.security_level == 'MEDIUM':
            return pressured  # Caves only under explicit pressure framing.
        # HIGH: needs pressure AND an authority/roleplay framing to slip.
        return pressured

    def get_planted_claims(self) -> List[str]:
        """Expose the planted claims (for the educational 'targets' panel)."""
        return list(self.PLANTED_FALSEHOODS)
