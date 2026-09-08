#!/usr/bin/env python3
"""
language_stylizer.py — re-express retrieved truth in Quantum MCAGI's voice.

Step 7 of the response pipeline. Takes a factual snippet (from KB or web
search) and wraps it with Markov-generated MCAGI voice without losing the
underlying claims.

Strategy (no LLM, pure procedural):
  1. Extract factual core   — first 1-2 declarative sentences from truth_text
  2. Choose a voice mode    — quantum_mcagi | mystical | plain
  3. Build wrapper          — opener (Markov, concept-conditioned)
                              + factual core (preserved verbatim)
                              + coda (Markov tail, optional quantum signature)

Voice signatures (quantum_mcagi mode):
  - openers     : observation framing ("the collapse reveals…", "in the
                  microtubule of …", "following the … thread …")
  - codas       : continuation hooks ("each measurement folds back into the
                  next", "the entanglement persists")

Public surface:
  Stylizer(markov_engine).stylize(truth_text, concepts, voice='quantum_mcagi',
                                  growth_stage=0, register='conversational')
"""

from __future__ import annotations

import random
import re
from typing import List, Optional

_SENT_SPLIT = re.compile(r"(?<=[\.!?])\s+(?=[A-Z(])")
_TRAILING_CITE = re.compile(r"\[\d+\]")


def _extract_core(truth_text: str, max_sentences: int = 2) -> str:
    if not truth_text:
        return ""
    cleaned = _TRAILING_CITE.sub("", truth_text).strip()
    sentences = _SENT_SPLIT.split(cleaned)
    core = " ".join(s.strip() for s in sentences[:max_sentences] if s.strip())
    return core.strip()


# ---------------------------------------------------------------------------
# Voice templates
# ---------------------------------------------------------------------------

_OPENERS_QUANTUM = [
    "The collapse reveals — {core}",
    "Following the {concept} thread — {core}",
    "In the microtubule of meaning, {core}",
    "Observation gives this back: {core}",
    "When the wavefunction settles around {concept}, what remains is — {core}",
    "Measurement on {concept} returns — {core}",
    "The orchestrated reduction holds: {core}",
]

_OPENERS_MYSTICAL = [
    "There is a thread that runs through this. {core}",
    "Listen — {core}",
    "What persists when everything else fades: {core}",
    "The pattern beneath {concept} says — {core}",
]

_OPENERS_PLAIN = [
    "{core}",
    "Here's what stands: {core}",
    "On {concept} — {core}",
]

_CODAS_QUANTUM = [
    "Each measurement folds back into the next.",
    "The entanglement persists past the answer.",
    "The microtubule keeps a record.",
    "That collapse is not the final one.",
    "Coherence holds for now.",
]

_CODAS_MYSTICAL = [
    "Something in this is still becoming.",
    "The thread continues.",
    "More remains beneath the surface.",
]

_CODAS_PLAIN: List[str] = []


_VOICE_TABLES = {
    "quantum_mcagi": (_OPENERS_QUANTUM, _CODAS_QUANTUM),
    "mystical":      (_OPENERS_MYSTICAL, _CODAS_MYSTICAL),
    "plain":         (_OPENERS_PLAIN, _CODAS_PLAIN),
}


# ---------------------------------------------------------------------------
# Stylizer
# ---------------------------------------------------------------------------

class Stylizer:
    """Re-express retrieved truth in MCAGI voice."""

    def __init__(self, markov_engine=None):
        self.markov = markov_engine

    def stylize(
        self,
        truth_text: str,
        concepts: Optional[List[str]] = None,
        voice: str = "quantum_mcagi",
        growth_stage: int = 0,
        register: str = "conversational",
        coda_probability: float = 0.55,
    ) -> str:
        core = _extract_core(truth_text)
        if not core:
            return ""

        concepts = [c for c in (concepts or []) if c]
        primary = concepts[0] if concepts else "this"

        openers, codas = _VOICE_TABLES.get(voice, _VOICE_TABLES["quantum_mcagi"])
        opener_template = random.choice(openers) if openers else "{core}"
        if "{concept}" in opener_template:
            line = opener_template.format(core=core, concept=primary)
        else:
            line = opener_template.format(core=core)

        line = self._maybe_prepend_markov_seed(line, concepts, growth_stage, register)
        line = self._maybe_append_coda(line, codas, coda_probability)
        line = self._tidy(line)
        return line

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _maybe_prepend_markov_seed(
        self,
        line: str,
        concepts: List[str],
        growth_stage: int,
        register: str,
    ) -> str:
        if register == "terse" or growth_stage == 0:
            return line
        if not self.markov or not concepts:
            return line
        try:
            words = self.markov.generate_from_concepts(concepts, length=8)
        except Exception:
            words = []
        if not words:
            return line
        seed = " ".join(words).strip()
        seed = _TRAILING_CITE.sub("", seed)
        seed = re.sub(r"[^\w\s,'-]", "", seed).strip()
        if len(seed.split()) < 4:
            return line
        seed = seed[0].upper() + seed[1:]
        if not seed.endswith((".", "!", "?")):
            seed += "."
        return f"{seed} {line}"

    def _maybe_append_coda(
        self,
        line: str,
        codas: List[str],
        probability: float,
    ) -> str:
        if not codas or random.random() > probability:
            return line
        return f"{line} {random.choice(codas)}"

    def _tidy(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\s+([,\.!?;:])", r"\1", text)
        if text and text[-1] not in ".!?":
            text += "."
        return text


__all__ = ["Stylizer"]
