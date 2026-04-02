"""
?? Orch OR Integration — Quantum Consciousness Meets Language
==============================================================
Wires the Penrose-Hameroff Orch OR model into Quantum MCAGI's
communication pipeline.

How it works:
1. User input arrives
2. Concepts are extracted (TF-IDF) and encoded as tubulin states
3. Microtubule lattices evolve via quantum walks + gap junctions
4. When Penrose threshold is reached, Objective Reduction fires
5. The collapse pattern determines word selection, question depth,
   response structure, and insight generation

This replaces random.choice() and template-filling with actual
quantum-inspired computation where the "decision" emerges from
the physics of the system rather than from hardcoded rules.

The key insight from Orch OR: consciousness is NOT computation.
It's the COLLAPSE of computation — the moment possibilities
become actuality. That's what this module does for the AI.
"""

import random
import logging
from typing import List, Dict, Tuple, Optional

import numpy as np

from orch_or_core import (
    TubulinQubit, Microtubule, OrchestratedConsciousness
)

logger = logging.getLogger("quantum_ai")


class OrchORLanguageBridge:
    """
    Bridges Orch OR quantum collapse with language generation.
    
    Instead of randomly selecting words or filling templates,
    this encodes concepts into microtubule states, evolves them
    with quantum walks and inter-module coupling, then uses the
    collapse pattern to drive every linguistic decision.
    """

    def __init__(self, n_tubulins: int = 26):
        self.consciousness = OrchestratedConsciousness(n_tubulins)
        self.n_tubulins = n_tubulins

    def concept_weights_from_scores(self, concept_scores: List[Dict],
                                    n_slots: int = 26) -> List[float]:
        """
        Convert TF-IDF concept scores into tubulin weights.
        Higher score = stronger superposition bias toward |1>.
        
        Maps concept importance to quantum rotation angle:
        score 0 -> weight 0 -> tubulin stays |0>
        score max -> weight 1 -> tubulin rotates to |1>
        """
        if not concept_scores:
            return [0.5] * n_slots  # All in equal superposition

        scores = [c.get('score', 0) if isinstance(c, dict) else 0.5
                  for c in concept_scores]
        max_score = max(scores) if scores else 1.0
        
        # Normalize to 0-1
        weights = [s / max_score if max_score > 0 else 0.5 for s in scores]
        
        # Pad with superposition states
        while len(weights) < n_slots:
            weights.append(0.5)
        
        return weights[:n_slots]

    def encode_input_to_system(self, concepts: List[str],
                               concept_scores: List[Dict],
                               understanding_score: float,
                               growth_stage: int):
        """
        Encode the full input context into the Orch OR system.
        
        - Language MT: concept importance weights
        - Memory MT: understanding depth (how well-known each concept is)
        - Question MT: novelty/gap signal (unknown = high superposition)
        - Insight MT: cross-concept interference pattern
        """
        n = self.n_tubulins
        
        # Language: direct concept weights
        lang_weights = self.concept_weights_from_scores(concept_scores, n)
        
        # Memory: understanding score spreads across lattice
        # Known concepts get high weight (close to |1>), unknown stay in superposition
        mem_weights = [understanding_score * 0.8 + 0.1] * min(len(concepts), n)
        while len(mem_weights) < n:
            mem_weights.append(0.3)  # Unknown = partial superposition
        
        # Question: inverse of understanding — gaps drive questions
        q_weights = [1.0 - w for w in mem_weights]
        
        # Insight: interference between concept pairs
        insight_weights = []
        for i in range(n):
            if i < len(lang_weights) and i < len(mem_weights):
                # XOR-like: high when language and memory disagree
                diff = abs(lang_weights[i] - mem_weights[i])
                insight_weights.append(diff * 0.8 + 0.1)
            else:
                insight_weights.append(0.5)
        
        # Growth stage affects decoherence resistance
        # Higher stage = more coherent = quantum effects last longer
        # (Models: more developed consciousness maintains coherence better)
        
        self.consciousness.encode_input({
            'language': lang_weights,
            'memory': mem_weights,
            'question': q_weights,
            'insight': insight_weights,
        })

    def collapse_to_decision(self, max_steps: int = 50) -> Dict:
        """
        Run the Orch OR evolution and collapse.
        Returns the conscious moment outcomes mapped to linguistic decisions.
        """
        # Decoherence rate decreases with growth (more mature = more coherent)
        decoherence = 0.03  # Base rate
        
        outcomes = self.consciousness.conscious_moment(
            max_steps=max_steps,
            decoherence_rate=decoherence
        )
        
        # Convert binary patterns to decision weights
        decisions = {}
        for module, pattern in outcomes.items():
            decisions[module] = {
                'pattern': pattern,
                'weights': self.consciousness.outcome_to_probabilities(pattern),
                'ones_ratio': sum(pattern) / len(pattern) if pattern else 0,
                'energy': sum(p for p in pattern) / len(pattern),
            }
        
        return decisions

    def select_from_options(self, options: List[str],
                           collapse_weights: List[float]) -> Tuple[str, float]:
        """
        Select from a list of options using collapse weights.
        Maps the N tubulin outcomes to M options via modular indexing.
        """
        if not options:
            return "", 0.0
        
        n_opts = len(options)
        n_weights = len(collapse_weights)
        
        # Map weights to options (may have more weights than options)
        option_scores = [0.0] * n_opts
        for i, w in enumerate(collapse_weights):
            option_scores[i % n_opts] += w
        
        # Normalize
        total = sum(option_scores)
        if total > 0:
            probs = [s / total for s in option_scores]
        else:
            probs = [1.0 / n_opts] * n_opts
        
        # Select via probability
        idx = np.random.choice(n_opts, p=probs)
        return options[idx], probs[idx]


class OrchORProcessor:
    """
    High-level processor that integrates Orch OR with the full
    Quantum MCAGI communication pipeline.
    
    Drop-in enhancement for QuantumLanguageEngine:
    - extract_concepts stays TF-IDF (classical preprocessing)
    - word/concept SELECTION uses Orch OR collapse
    - question GENERATION uses question-MT collapse pattern
    - response COMPOSITION uses language+insight MT interaction
    """

    def __init__(self, n_tubulins: int = 26):
        self.bridge = OrchORLanguageBridge(n_tubulins)
        self.last_collapse = None
        self.total_moments = 0

    def process(self, concepts: List[str],
                concept_scores: List[Dict],
                understanding_score: float,
                growth_stage: int) -> Dict:
        """
        Full Orch OR processing cycle.
        
        Returns a decision dict with weights for:
        - language: word/phrase selection weights
        - memory: which memories to surface
        - question: what Bloom's level to target
        - insight: how novel/creative to be
        """
        # Encode
        self.bridge.encode_input_to_system(
            concepts, concept_scores, understanding_score, growth_stage
        )
        
        # Evolve and collapse
        decisions = self.bridge.collapse_to_decision(max_steps=50)
        self.last_collapse = decisions
        self.total_moments += 1
        
        # Derive high-level parameters from collapse
        result = {
            'raw_decisions': decisions,
            'language_weights': decisions.get('language', {}).get('weights', []),
            'memory_weights': decisions.get('memory', {}).get('weights', []),
            'question_weights': decisions.get('question', {}).get('weights', []),
            'insight_weights': decisions.get('insight', {}).get('weights', []),
        }
        
        # Derive Bloom's level from question pattern
        q_energy = decisions.get('question', {}).get('ones_ratio', 0.5)
        # Higher energy = higher Bloom's level
        result['bloom_level'] = min(5, int(q_energy * 6))
        
        # Derive creativity/novelty from insight pattern
        i_energy = decisions.get('insight', {}).get('ones_ratio', 0.5)
        result['creativity'] = i_energy
        
        # Derive response complexity from language pattern
        l_energy = decisions.get('language', {}).get('ones_ratio', 0.5)
        result['complexity'] = l_energy
        
        # Derive memory recall depth
        m_energy = decisions.get('memory', {}).get('ones_ratio', 0.5)
        result['recall_depth'] = m_energy
        
        return result

    def quantum_select(self, options: List[str], module: str = 'language',
                       fallback_weights: List[float] = None) -> Tuple[str, float]:
        """
        Select from options using the most recent Orch OR collapse.
        
        module: which microtubule's collapse to use
        fallback_weights: if no collapse available, use these
        """
        if self.last_collapse and module in self.last_collapse:
            weights = self.last_collapse[module].get('weights', [])
        elif fallback_weights:
            weights = fallback_weights
        else:
            weights = [1.0 / len(options)] * len(options)
        
        return self.bridge.select_from_options(options, weights)

    def get_temperature(self) -> float:
        """
        Derive Markov chain temperature from the quantum state.
        High coherence before collapse = low temperature (more deterministic)
        Low coherence = high temperature (more random)
        """
        if not self.last_collapse:
            return 0.9  # Default
        
        # Average energy across all modules
        energies = [d.get('ones_ratio', 0.5) 
                   for d in self.last_collapse.values()]
        avg_energy = sum(energies) / len(energies) if energies else 0.5
        
        # Map: high energy -> low temp (confident), low energy -> high temp
        temperature = 1.5 - avg_energy
        return max(0.3, min(2.0, temperature))

    def should_ask_question(self) -> bool:
        """
        Orch OR determines whether to ask a question.
        If the question-MT collapsed with high |1> ratio,
        the system is "curious" — it should ask.
        """
        if not self.last_collapse:
            return True
        q = self.last_collapse.get('question', {})
        return q.get('ones_ratio', 0.5) > 0.4

    def get_insight_strength(self) -> float:
        """How strongly to push for novel connections in the response."""
        if not self.last_collapse:
            return 0.5
        return self.last_collapse.get('insight', {}).get('ones_ratio', 0.5)

    def get_status(self) -> Dict:
        """Get Orch OR system status for /status command."""
        state = self.bridge.consciousness.get_system_state()
        return {
            'conscious_moments': self.total_moments,
            'microtubules': {
                name: {
                    'coherence': mt['coherence'],
                    'entropy': mt['entropy'],
                    'collapses': mt['total_collapses'],
                }
                for name, mt in state['microtubules'].items()
            },
            'gap_junctions': state['gap_junctions'],
            'last_temperature': self.get_temperature(),
        }


# Singleton
_orch_or = None

def get_orch_or_processor() -> OrchORProcessor:
    """Get or create the Orch OR processor singleton."""
    global _orch_or
    if _orch_or is None:
        _orch_or = OrchORProcessor(n_tubulins=26)
        logger.info("Orch OR processor initialized: 4 microtubules x 26 tubulins")
    return _orch_or
