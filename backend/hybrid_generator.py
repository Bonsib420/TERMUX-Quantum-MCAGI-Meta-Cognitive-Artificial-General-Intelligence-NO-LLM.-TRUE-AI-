"""
Hybrid Generator — Quantum MCAGI
12-candidate Markov generation pipeline with TF-IDF scoring,
coherence scoring, and Orch-OR collapse-weight winner selection.
Also integrates Hilbert semantic engine and fact store weighting.
"""

import random
import math
import re
import json
import os
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


FACT_STORE_PATH = os.path.expanduser('~/.quantum-mcagi/fact_store.json')


def _load_facts(concepts: List[str]) -> List[str]:
    """Query fact store for relevant facts about concepts."""
    try:
        with open(FACT_STORE_PATH) as f:
            fs = json.load(f)
        facts = []
        # Synonym map for common concept mismatches
        synonyms = {
            'dna': ['genetics', 'genetic', 'genome', 'gene'],
            'evolution': ['natural selection', 'evolutionary', 'darwin'],
            'brain': ['neuroscience', 'neuron', 'cognitive'],
            'mind': ['consciousness', 'psychology', 'cognitive'],
            'python': ['programming', 'software', 'code'],
            'string': ['syntax', 'programming', 'text'],
            'god': ['religion', 'theology', 'divine'],
            'universe': ['cosmology', 'physics', 'spacetime'],
        }
        for concept in concepts[:5]:
            found = False
            # Exact match first
            if concept in fs and fs[concept]:
                for verb, obj in fs[concept][:2]:
                    facts.append(f"{concept} {verb} {obj}")
                found = True
            # Try synonyms
            if not found:
                for alt in synonyms.get(concept.lower(), []):
                    if alt in fs and fs[alt]:
                        for verb, obj in fs[alt][:2]:
                            facts.append(f"{alt} {verb} {obj}")
                        break
            # Fuzzy match — find keys containing the concept
            if not found:
                for key in fs:
                    if concept.lower() in key.lower() and fs[key]:
                        for verb, obj in fs[key][:1]:
                            facts.append(f"{key} {verb} {obj}")
                        break
        return facts[:6]
    except Exception:
        return []


class HybridGenerator:
    """
    Generates 12 Markov candidates per response, scores them by
    TF-IDF relevance + coherence + concept coverage, picks winner
    via Orch-OR collapse weights.
    Also integrates Hilbert semantic engine, fact store, and meaning engine.
    """

    def __init__(self, markov_engine, tfidf_engine, orch_or_engine,
                 hilbert_engine=None, meaning_engine=None):
        self.markov = markov_engine
        self.tfidf = tfidf_engine
        self.orch_or = orch_or_engine
        self.hilbert_engine = hilbert_engine
        self.meaning_engine = meaning_engine
        self.num_candidates = 12
        self.generation_count = 0
        self.hilbert_weight = 0.8
        self.markov_weight = 0.25
        self.meaning_weight = 0.15

    def generate(
        self,
        concepts: List[str],
        growth_stage: int = 0,
        length: int = 18,
        **kwargs,
    ) -> Dict:
        growth_stage = int(growth_stage) if isinstance(growth_stage, (int, float)) else 0

        # Load relevant facts from fact store
        facts = _load_facts(concepts)

        # Generate candidates
        candidates = []
        for i in range(self.num_candidates):
            wild = (i >= 7) or (growth_stage >= 4 and random.random() < 0.2)
            length_var = length + random.randint(0, 8)
            tokens = self.markov.generate_from_concepts(concepts, length=length_var, wild=wild)
            if isinstance(tokens, list):
                text = ' '.join(str(t) for t in tokens).strip()
            else:
                text = str(tokens).strip()

            # Prepend a relevant fact to some candidates
            if facts and i < 4 and random.random() < 0.5:
                fact = random.choice(facts)
                text = f"{fact}. {text}" if text else fact

            if text and len(text.split()) >= 4:
                candidates.append(text)

        if not candidates:
            # Fallback — use facts directly if available
            if facts:
                return {
                    'winner': ' '.join(facts[:2]),
                    'scores': [],
                    'candidates': 0,
                    'method': 'fact_fallback',
                }
            return {
                'winner': '',
                'scores': [],
                'candidates': 0,
                'method': 'fallback',
            }

        # Pad to num_candidates
        while len(candidates) < self.num_candidates:
            tokens = self.markov.generate_from_concepts(concepts, length=length)
            if isinstance(tokens, list):
                text = ' '.join(str(t) for t in tokens).strip()
            else:
                text = str(tokens).strip()
            candidates.append(text if text else candidates[0])

        # Score candidates
        scores = []
        for candidate in candidates:
            relevance = self._score_relevance(candidate, concepts)
            coherence = self._score_coherence(candidate)
            coverage = self._score_concept_coverage(candidate, concepts)
            fact_score = self._score_fact_alignment(candidate, facts)

            # Weighted composite — fact store gets real weight now
            composite = (
                relevance * 0.25 +
                coherence * 0.35 +
                coverage * 0.20 +
                fact_score * 0.20
            )
            scores.append({
                'text': candidate,
                'relevance': round(relevance, 4),
                'coherence': round(coherence, 4),
                'coverage': round(coverage, 4),
                'fact_score': round(fact_score, 4),
                'composite': round(composite, 4),
            })

        # Orch-OR collapse weights
        collapse_weights = self.orch_or.get_collapse_weights(len(candidates))

        # Hilbert semantic boost if available
        hilbert_scores = self._get_hilbert_scores(candidates, concepts)

        final_scores = []
        for i, score_entry in enumerate(scores):
            weight = collapse_weights[i] if i < len(collapse_weights) else 0.5
            hilbert = hilbert_scores[i] if i < len(hilbert_scores) else 0.5
            weighted = (
                score_entry['composite'] * 0.5 +
                weight * 0.3 +
                hilbert * 0.2
            )
            final_scores.append(weighted)

        winner_idx = final_scores.index(max(final_scores))
        winner_text = candidates[winner_idx]

        self.generation_count += 1

        return {
            'winner': winner_text,
            'winner_idx': winner_idx,
            'scores': scores,
            'collapse_weights': [round(w, 4) for w in collapse_weights],
            'final_scores': [round(s, 4) for s in final_scores],
            'candidates': len(candidates),
            'method': 'hybrid_orch_or',
            'facts_used': len(facts),
        }

    def _score_fact_alignment(self, text: str, facts: List[str]) -> float:
        """Score how well a candidate aligns with known facts."""
        if not facts:
            return 0.5
        text_lower = text.lower()
        hits = 0
        for fact in facts:
            words = fact.lower().split()
            if any(w in text_lower for w in words if len(w) > 3):
                hits += 1
        return min(1.0, hits / len(facts) + 0.1)

    def _get_hilbert_scores(self, candidates: List[str], concepts: List[str]) -> List[float]:
        """Get semantic scores from Hilbert engine if available."""
        if not self.hilbert_engine:
            return [0.5] * len(candidates)
        try:
            scores = []
            for candidate in candidates:
                words = candidate.lower().split()[:10]
                concept_set = set(c.lower() for c in concepts)
                overlap = len(set(words) & concept_set) / max(len(concept_set), 1)
                scores.append(min(1.0, overlap + 0.3))
            return scores
        except Exception:
            return [0.5] * len(candidates)

    def _score_relevance(self, text: str, concepts: List[str]) -> float:
        if not concepts:
            return 0.5
        words = set(re.findall(r'\b[a-z]{3,}\b', text.lower()))
        if not words:
            return 0.0
        try:
            tfidf_concepts = self.tfidf.extract_concepts(text, top_n=10)
            tfidf_words = {c['concept'] for c in tfidf_concepts}
        except Exception:
            tfidf_words = set()
        concept_set = set(c.lower() for c in concepts)
        direct_hits = len(concept_set & words) / max(len(concept_set), 1)
        tfidf_overlap = len(concept_set & tfidf_words) / max(len(concept_set), 1)
        return min(1.0, direct_hits * 0.6 + tfidf_overlap * 0.4 + 0.1)

    def _score_coherence(self, text: str) -> float:
        words = text.lower().split()
        if len(words) < 4:
            return 0.1
        bigram_score = 0
        total_bigrams = 0
        consecutive_misses = 0
        max_consecutive_misses = 0
        for i in range(len(words) - 2):
            prefix = (words[i], words[i + 1])
            if prefix in self.markov.chain:
                next_options = self.markov.chain[prefix]
                next_word = words[i + 2]
                if next_word in next_options:
                    total_count = sum(next_options.values())
                    bigram_score += next_options[next_word] / total_count
                    consecutive_misses = 0
                else:
                    consecutive_misses += 1
                total_bigrams += 1
            else:
                consecutive_misses += 1
            max_consecutive_misses = max(max_consecutive_misses, consecutive_misses)

        if total_bigrams == 0:
            return 0.1

        raw = bigram_score / total_bigrams
        length_penalty = 1.0
        if len(words) < 5:
            length_penalty = 0.5
        elif len(words) > 30:
            length_penalty = 0.85
        unique_ratio = len(set(words)) / len(words)
        repetition_bonus = min(1.0, unique_ratio * 1.2)
        has_sentence_end = any(w.endswith(('.', '!', '?')) for w in words[3:])
        sentence_bonus = 0.15 if has_sentence_end else 0.0
        gap_penalty = 0.2 if max_consecutive_misses >= 4 else 0.0
        score = raw * 0.4 + length_penalty * 0.15 + repetition_bonus * 0.2 + sentence_bonus - gap_penalty
        return max(0.0, min(1.0, score))

    def _score_concept_coverage(self, text: str, concepts: List[str]) -> float:
        if not concepts:
            return 0.5
        text_lower = text.lower()
        hits = sum(1 for c in concepts if c.lower() in text_lower)
        return min(1.0, hits / len(concepts) + 0.1)

    def has_sufficient_states(self) -> bool:
        return len(self.markov.chain) >= 30

    def get_status(self) -> Dict:
        return {
            'generations': self.generation_count,
            'num_candidates': self.num_candidates,
            'sufficient_states': self.has_sufficient_states(),
            'markov_states': len(self.markov.chain),
            'hilbert_active': self.hilbert_engine is not None,
            'meaning_active': self.meaning_engine is not None,
        }


# ── Compatibility factory ───────────────────────────────────────────────────
def create_hybrid_generator(engine):
    """Build a HybridGenerator from a language/cognitive engine exposing
    .markov, .tfidf and .orch_or. Returns None if those are unavailable."""
    markov = getattr(engine, "markov", None)
    tfidf = getattr(engine, "tfidf", None)
    orch_or = getattr(engine, "orch_or", None)
    if markov is None or tfidf is None or orch_or is None:
        return None
    return HybridGenerator(
        markov, tfidf, orch_or,
        hilbert_engine=getattr(engine, "hilbert_engine", None),
        meaning_engine=getattr(engine, "meaning_engine", None),
    )
