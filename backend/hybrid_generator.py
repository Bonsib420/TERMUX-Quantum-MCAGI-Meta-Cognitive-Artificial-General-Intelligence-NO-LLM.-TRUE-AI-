"""
Hybrid Generator — Quantum MCAGI
8-candidate Markov generation pipeline with TF-IDF scoring,
coherence scoring, and Orch-OR collapse-weight winner selection.
"""

import random
import math
import re
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class HybridGenerator:
    """
    Generates 8 Markov candidates per response, scores them by
    TF-IDF relevance + coherence + concept coverage, picks winner
    via Orch-OR collapse weights.
    """

    def __init__(self, markov_engine, tfidf_engine, orch_or_engine):
        """
        Initialize the HybridGenerator with the provided Markov, TF-IDF, and Orch‑OR engines and default generation settings.
        
        Parameters:
            markov_engine: Markov-style generation engine used to produce candidate text from concepts; expected to expose a `generate_from_concepts` method and a `chain` attribute.
            tfidf_engine: TF-IDF extraction/scoring engine used to derive concept importance from candidate text; expected to expose an `extract_concepts` method.
            orch_or_engine: Orch‑OR weighting engine used to provide collapse weights for final candidate weighting; expected to expose a `get_collapse_weights` method.
        
        Attributes initialized:
            self.markov: assigned markov_engine
            self.tfidf: assigned tfidf_engine
            self.orch_or: assigned orch_or_engine
            self.num_candidates (int): default number of candidates to generate (12)
            self.generation_count (int): counter of how many generations have been produced (starts at 0)
        """
        self.markov = markov_engine
        self.tfidf = tfidf_engine
        self.orch_or = orch_or_engine
        self.num_candidates = 12
        self.generation_count = 0

    def generate(
        self,
        concepts: List[str],
        growth_stage: int = 0,
        length: int = 18,
    ) -> Dict:
        """
        Generate multiple candidate texts from provided concepts, score them by relevance, coherence, and concept coverage, and select a winner using Orch-OR collapse weights.
        
        Parameters:
        	concepts (List[str]): Seed concepts used to guide Markov generation.
        	growth_stage (int): Higher values increase chance of "wild" (creative) generations; defaults to 0.
        	length (int): Base token length for generation; each candidate may vary slightly above this value.
        
        Returns:
        	dict: A summary containing:
        		- winner (str): The selected winning text.
        		- winner_idx (int): Index of the winner within the returned candidates.
        		- scores (List[dict]): Per-candidate records with keys `text`, `relevance`, `coherence`, `coverage`, and `composite` (each numeric, rounded to 4 decimals).
        		- collapse_weights (List[float]): Orch-OR collapse weights used (rounded to 4 decimals).
        		- final_scores (List[float]): Final blended scores combining composite score and collapse weight (rounded to 4 decimals).
        		- candidates (int): Number of candidates evaluated.
        		- method (str): Generation method identifier (always `'hybrid_orch_or'` or `'fallback'` when no candidates were created).
        """
        candidates = []
        for i in range(self.num_candidates):
            wild = (i >= 7) or (growth_stage >= 4 and random.random() < 0.2)
            length_var = length + random.randint(0, 8)
            tokens = self.markov.generate_from_concepts(concepts, length=length_var, wild=wild)
            text = ' '.join(tokens).strip()
            if text and len(text.split()) >= 5:
                candidates.append(text)

        if not candidates:
            return {
                'winner': '',
                'scores': [],
                'candidates': 0,
                'method': 'fallback',
            }

        while len(candidates) < self.num_candidates:
            tokens = self.markov.generate_from_concepts(concepts, length=length)
            text = ' '.join(tokens).strip()
            candidates.append(text if text else candidates[0])

        scores = []
        for candidate in candidates:
            relevance = self._score_relevance(candidate, concepts)
            coherence = self._score_coherence(candidate)
            coverage = self._score_concept_coverage(candidate, concepts)
            composite = relevance * 0.3 + coherence * 0.5 + coverage * 0.2
            scores.append({
                'text': candidate,
                'relevance': round(relevance, 4),
                'coherence': round(coherence, 4),
                'coverage': round(coverage, 4),
                'composite': round(composite, 4),
            })

        collapse_weights = self.orch_or.get_collapse_weights(len(candidates))

        final_scores = []
        for i, score_entry in enumerate(scores):
            weight = collapse_weights[i] if i < len(collapse_weights) else 0.5
            weighted = score_entry['composite'] * 0.7 + weight * 0.3
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
        }

    def _score_relevance(self, text: str, concepts: List[str]) -> float:
        """
        Compute how well the given text matches the provided concepts by combining direct word matches and TF-IDF-derived concept overlap.
        
        Parameters:
            text (str): The candidate text to evaluate.
            concepts (List[str]): Target concept strings to measure against.
        
        Returns:
            float: A relevance score between 0.0 and 1.0. If `concepts` is empty returns 0.5; if no valid words are extracted from `text` returns 0.0. The score blends direct concept word hits and TF-IDF overlap with a small baseline and is capped at 1.0.
        """
        if not concepts:
            return 0.5

        words = set(re.findall(r'\b[a-z]{3,}\b', text.lower()))
        if not words:
            return 0.0

        tfidf_concepts = self.tfidf.extract_concepts(text, top_n=10)
        tfidf_words = {c['concept'] for c in tfidf_concepts}

        concept_set = set(c.lower() for c in concepts)
        direct_hits = len(concept_set & words) / max(len(concept_set), 1)
        tfidf_overlap = len(concept_set & tfidf_words) / max(len(concept_set), 1)

        return min(1.0, direct_hits * 0.6 + tfidf_overlap * 0.4 + 0.1)

    def _score_coherence(self, text: str) -> float:
        """
        Compute a coherence score for a candidate text based on Markov bigram transitions and simple heuristics.
        
        Evaluates how well the text's word transitions match the Markov chain stored in self.markov.chain, then adjusts that raw transition score with length-based adjustments, a repetition/uniqueness bonus, a small sentence-ending bonus, and a penalty for long gaps of unmatched transitions. Very short or unmatchable texts receive a low baseline score.
        
        Parameters:
            text (str): Candidate sentence to evaluate.
        
        Returns:
            float: Coherence score in the range 0.0–1.0 (`0.1` is used as a low baseline for very short or unmatchable texts).
        """
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

        gap_penalty = 0.0
        if max_consecutive_misses >= 4:
            gap_penalty = 0.2

        score = raw * 0.4 + length_penalty * 0.15 + repetition_bonus * 0.2 + sentence_bonus - gap_penalty
        return max(0.0, min(1.0, score))

    def _score_concept_coverage(self, text: str, concepts: List[str]) -> float:
        """
        Estimate how well the given text covers the provided concepts.
        
        Parameters:
            text (str): Candidate text to evaluate.
            concepts (List[str]): List of concept strings to check for as substrings in `text`.
        
        Returns:
            float: Coverage score between 0.0 and 1.0 where each concept found as a case-insensitive substring increments the score; final value is hits/len(concepts) plus 0.1, capped at 1.0. If `concepts` is empty, returns 0.5.
        """
        if not concepts:
            return 0.5
        text_lower = text.lower()
        hits = sum(1 for c in concepts if c.lower() in text_lower)
        return min(1.0, hits / len(concepts) + 0.1)

    def has_sufficient_states(self) -> bool:
        """
        Indicates whether the Markov model currently contains enough states for reliable generation.
        
        Returns:
            bool: `True` if the Markov chain has at least 30 states, `False` otherwise.
        """
        return len(self.markov.chain) >= 30

    def get_status(self) -> Dict:
        """
        Return a snapshot of the generator's runtime status and configuration.
        
        Returns:
            status (dict): A dictionary containing:
                - generations (int): Total number of generation calls performed.
                - num_candidates (int): Configured number of candidates produced per generation.
                - sufficient_states (bool): True if the Markov chain has at least 30 states.
                - markov_states (int): Current number of states in the Markov chain.
        """
        return {
            'generations': self.generation_count,
            'num_candidates': self.num_candidates,
            'sufficient_states': self.has_sufficient_states(),
            'markov_states': len(self.markov.chain),
        }
