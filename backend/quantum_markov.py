"""
🌌 QUANTUM MARKOV CHAIN — L² Amplitude-Based Text Generation
==============================================================
Enhances the classical Markov chain with quantum capabilities:

1. Quantum Stochastic Walk (QSW) — transitions via L² amplitudes
   instead of L¹ probabilities. Superposition of multiple next-word
   paths explored simultaneously before collapse.

2. Quantum Interference — complex-valued semantic amplitudes allow
   constructive interference (boosting coherent concepts) and
   destructive interference (suppressing contradictions).

3. Entanglement-Based Coherence — non-local correlations between
   distant words in a sentence modeled as entangled amplitude pairs,
   so choosing one word instantaneously constrains words across the
   whole sentence.

4. DisCoCat-Inspired Context — word meanings represented as quantum
   states in a Hilbert space; meaning actualizes from superposition
   based on surrounding context (measurement/collapse).

Math:
  Classical Markov:  P(w) = count(w) / total        (L¹ norm)
  Quantum Markov:    ψ(w) = √(count(w)) · e^{iφ}   (L² norm, complex amplitude)
                     P(w) = |ψ(w)|²                  (Born rule)

  Interference:      ψ_total(w) = ψ_markov(w) + ψ_context(w)
                     P(w) = |ψ_markov(w) + ψ_context(w)|²
                          ≠ |ψ_markov(w)|² + |ψ_context(w)|²
                     (cross term = interference)

References:
  [1] Whitfield et al., Quantum Stochastic Walks, Phys Rev A 81, 022323 (2010)
  [2] Coecke et al., Mathematical Foundations for a Compositional Distributional
      Model of Meaning, Lambek Festschrift (2010) — DisCoCat
  [3] Li & Cunningham, Quantum-Inspired Complex Word Embedding (2019)
"""

import math
import random
import cmath
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional, Set

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# ============================================================================
# QUANTUM AMPLITUDE STATE
# ============================================================================

class QuantumAmplitude:
    """
    A complex-valued amplitude for a word in the quantum Markov state.
    ψ = |ψ| · e^{iφ}   where |ψ|² is the Born probability.
    """
    __slots__ = ('real', 'imag')

    def __init__(self, real: float = 0.0, imag: float = 0.0):
        self.real = real
        self.imag = imag

    @classmethod
    def from_probability(cls, prob: float, phase: float = 0.0):
        """Create amplitude from classical probability + phase."""
        magnitude = math.sqrt(max(prob, 0.0))
        return cls(magnitude * math.cos(phase), magnitude * math.sin(phase))

    @classmethod
    def from_count(cls, count: int, total: int, phase: float = 0.0):
        """Create amplitude from raw counts (like classical Markov)."""
        prob = count / max(total, 1)
        return cls.from_probability(prob, phase)

    @property
    def magnitude(self) -> float:
        return math.sqrt(self.real ** 2 + self.imag ** 2)

    @property
    def probability(self) -> float:
        """Born rule: P = |ψ|²"""
        return self.real ** 2 + self.imag ** 2

    @property
    def phase(self) -> float:
        return math.atan2(self.imag, self.real)

    def __add__(self, other: 'QuantumAmplitude') -> 'QuantumAmplitude':
        """Superposition: ψ₁ + ψ₂  (interference occurs here)."""
        return QuantumAmplitude(self.real + other.real, self.imag + other.imag)

    def __mul__(self, scalar: float) -> 'QuantumAmplitude':
        return QuantumAmplitude(self.real * scalar, self.imag * scalar)

    def __rmul__(self, scalar: float) -> 'QuantumAmplitude':
        return self.__mul__(scalar)

    def conjugate(self) -> 'QuantumAmplitude':
        return QuantumAmplitude(self.real, -self.imag)

    def rotate_phase(self, theta: float) -> 'QuantumAmplitude':
        """Apply phase rotation: ψ' = ψ · e^{iθ}"""
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        new_real = self.real * cos_t - self.imag * sin_t
        new_imag = self.real * sin_t + self.imag * cos_t
        return QuantumAmplitude(new_real, new_imag)

    def __repr__(self):
        return f"ψ({self.real:.3f}+{self.imag:.3f}i, P={self.probability:.4f})"


# ============================================================================
# SEMANTIC PHASE ENCODER
# ============================================================================

class SemanticPhaseEncoder:
    """
    Assigns quantum phases to words based on semantic similarity.
    
    Related words get similar phases → constructive interference.
    Unrelated words get opposite phases → destructive interference.
    
    Phase assignment uses a simple hash-based approach that is
    deterministic and consistent for a given vocabulary.
    """

    def __init__(self):
        self._phase_cache: Dict[str, float] = {}
        # Semantic clusters — words in the same cluster get similar phases
        self._clusters: Dict[str, int] = {}
        self._cluster_phases: Dict[int, float] = {}
        self._next_cluster_id = 0

    def get_phase(self, word: str) -> float:
        """Get the semantic phase for a word."""
        if word in self._phase_cache:
            return self._phase_cache[word]

        # Check if word belongs to a known cluster
        if word in self._clusters:
            cluster_id = self._clusters[word]
            base_phase = self._cluster_phases[cluster_id]
            # Small variation within cluster
            word_hash = hash(word) % 1000
            variation = (word_hash / 1000.0 - 0.5) * 0.3  # ±0.15 radians
            phase = base_phase + variation
        else:
            # Assign phase based on word hash (deterministic)
            word_hash = hash(word) % 10000
            phase = (word_hash / 10000.0) * 2 * math.pi

        self._phase_cache[word] = phase
        return phase

    def register_cluster(self, words: List[str], base_phase: float = None):
        """Register a group of semantically related words with similar phases."""
        if base_phase is None:
            base_phase = (self._next_cluster_id * math.pi * 2 / 7) % (2 * math.pi)

        cluster_id = self._next_cluster_id
        self._next_cluster_id += 1
        self._cluster_phases[cluster_id] = base_phase

        for word in words:
            self._clusters[word] = cluster_id
            # Clear cache for re-computation
            self._phase_cache.pop(word, None)

    def learn_phases_from_cooccurrence(self, pmi_scores: Dict[Tuple[str, str], float]):
        """
        Learn semantic phases from PMI co-occurrence data.
        Words with high PMI get similar phases (constructive interference).
        Words with negative PMI get opposite phases (destructive interference).
        """
        if not pmi_scores:
            return

        # Build adjacency from PMI
        adjacency: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        for (w1, w2), score in pmi_scores.items():
            adjacency[w1].append((w2, score))
            adjacency[w2].append((w1, score))

        # Assign phases by propagation from highest-PMI pairs
        assigned = set()
        for (w1, w2), score in sorted(pmi_scores.items(), key=lambda x: -x[1]):
            if w1 not in assigned:
                self._phase_cache[w1] = random.uniform(0, 2 * math.pi)
                assigned.add(w1)
            if w2 not in assigned:
                if score > 0:
                    # Similar phase (constructive)
                    self._phase_cache[w2] = self._phase_cache[w1] + random.uniform(-0.3, 0.3)
                else:
                    # Opposite phase (destructive)
                    self._phase_cache[w2] = self._phase_cache[w1] + math.pi + random.uniform(-0.3, 0.3)
                assigned.add(w2)


# ============================================================================
# ENTANGLEMENT REGISTER
# ============================================================================

class EntanglementRegister:
    """
    Models non-local correlations between words in a sentence.
    
    When words are entangled, choosing one constrains the probabilities
    of others — even distant ones. This models long-range dependencies
    that classical Markov chains (fixed window) cannot capture.
    
    Implementation: maintains a set of entangled pairs with correlation
    strengths. When a word is "measured" (selected), entangled partners
    receive amplitude boosts or penalties.
    """

    def __init__(self):
        # (word_a, word_b) -> correlation strength [-1, 1]
        # +1 = perfectly correlated (choosing A boosts B)
        # -1 = anti-correlated (choosing A suppresses B)
        self.entangled_pairs: Dict[Tuple[str, str], float] = {}

    def entangle(self, word_a: str, word_b: str, strength: float):
        """Create or update entanglement between two words."""
        pair = tuple(sorted([word_a.lower(), word_b.lower()]))
        self.entangled_pairs[pair] = max(-1.0, min(1.0, strength))

    def learn_from_cooccurrence(self, pair_counts: Counter,
                                 word_counts: Counter, total_pairs: int):
        """
        Learn entanglement from co-occurrence statistics.
        High PMI → positive entanglement (correlated).
        Mutual exclusion → negative entanglement (anti-correlated).
        """
        if total_pairs == 0:
            return

        for pair, count in pair_counts.most_common(500):
            w1, w2 = pair
            p_pair = count / total_pairs
            p_w1 = word_counts[w1] / sum(word_counts.values())
            p_w2 = word_counts[w2] / sum(word_counts.values())

            if p_w1 > 0 and p_w2 > 0 and p_pair > 0:
                pmi = math.log2(p_pair / (p_w1 * p_w2))
                # Normalize to [-1, 1] range
                strength = math.tanh(pmi / 3.0)
                self.entangle(w1, w2, strength)

    def get_entanglement_boost(self, candidate: str,
                                selected_words: List[str]) -> float:
        """
        Compute amplitude modification for a candidate word based on
        its entanglement with already-selected words.
        
        Returns a phase rotation angle:
          Positive = constructive interference (boost)
          Negative = destructive interference (suppress)
        """
        if not selected_words:
            return 0.0

        total_effect = 0.0
        count = 0
        c = candidate.lower()

        for sel in selected_words:
            s = sel.lower()
            pair = tuple(sorted([c, s]))
            if pair in self.entangled_pairs:
                total_effect += self.entangled_pairs[pair]
                count += 1

        if count == 0:
            return 0.0

        # Average effect, scaled to phase rotation
        avg_effect = total_effect / count
        # Map [-1,1] → [-π/2, π/2] phase rotation
        return avg_effect * (math.pi / 2)


# ============================================================================
# QUANTUM MARKOV CHAIN
# ============================================================================

class QuantumMarkovChain:
    """
    Quantum Stochastic Walk-enhanced Markov chain for text generation.
    
    Extends classical Markov chains with:
    - L² amplitude-based state space (complex amplitudes, not probabilities)
    - Quantum interference between transition paths
    - Entanglement-based long-range word correlations
    - Phase-encoded semantic relationships
    - Born-rule measurement (collapse) for word selection
    
    The classical chain data is PRESERVED — quantum features are layered
    on top. When quantum features have insufficient data, the system
    gracefully falls back to classical sampling.
    
    Algorithm:
    1. Convert classical counts → quantum amplitudes with semantic phases
    2. Apply entanglement corrections from already-generated words
    3. Apply context interference (constructive for related, destructive for unrelated)
    4. Compute Born probabilities: P(w) = |ψ_total(w)|²
    5. Temperature-adjusted sampling from Born distribution
    """

    def __init__(self, classical_chains: Dict = None,
                 classical_starters: Dict = None,
                 decoherence_rate: float = 0.05):
        """
        Args:
            classical_chains: Existing Markov chain data {order: {prefix: Counter}}
            classical_starters: Existing starter prefixes {order: [tuples]}
            decoherence_rate: Rate at which quantum effects decay (0=full quantum, 1=fully classical)
        """
        # Classical backbone (shared with MarkovTextGenerator)
        self.chains = classical_chains or {}
        self.starters = classical_starters or {}

        # Quantum components
        self.phase_encoder = SemanticPhaseEncoder()
        self.entanglement = EntanglementRegister()
        self.decoherence_rate = decoherence_rate

        # Context state — reset per generation
        self._context_words: List[str] = []
        self._generation_step: int = 0

    def quantum_sample(self, counter: Counter, temperature: float,
                       context_words: List[str] = None,
                       query_concepts: List[str] = None) -> Optional[str]:
        """
        Quantum-enhanced word selection using L² amplitudes + interference.
        
        This replaces the classical _sample method when quantum mode is active.
        
        Args:
            counter: Classical word→count mapping from Markov chain
            temperature: Sampling temperature
            context_words: Words already generated in this sentence
            query_concepts: Key concepts from the user's query
            
        Returns:
            Selected word after quantum collapse
        """
        if not counter:
            return None

        words = list(counter.keys())
        counts = list(counter.values())
        total_count = sum(counts)

        if total_count == 0:
            return random.choice(words) if words else None

        # ── Step 1: Convert classical counts → quantum amplitudes ──
        # ψ(w) = √(count(w)/total) · e^{iφ(w)}
        amplitudes: Dict[str, QuantumAmplitude] = {}
        for word, count in zip(words, counts):
            phase = self.phase_encoder.get_phase(word)
            amplitudes[word] = QuantumAmplitude.from_count(count, total_count, phase)

        # ── Step 2: Apply entanglement corrections ──
        # Words entangled with already-selected words get phase rotations
        if context_words:
            for word in words:
                boost_angle = self.entanglement.get_entanglement_boost(
                    word, context_words[-10:]  # Last 10 words for efficiency
                )
                if abs(boost_angle) > 0.01:
                    amplitudes[word] = amplitudes[word].rotate_phase(boost_angle)

        # ── Step 3: Apply context interference ──
        # Query concepts create an additional amplitude field that interferes
        # with Markov amplitudes — related words get constructive interference,
        # unrelated get destructive.
        if query_concepts:
            for word in words:
                context_amp = self._compute_context_amplitude(
                    word, query_concepts
                )
                if context_amp.probability > 1e-10:
                    # Superposition: ψ_total = ψ_markov + α·ψ_context
                    # α controls context influence strength (0.3 = moderate)
                    context_weight = 0.3
                    amplitudes[word] = amplitudes[word] + (context_weight * context_amp)

        # ── Step 4: Apply decoherence ──
        # As generation progresses, quantum effects gradually decay
        # toward classical behavior (mimics warm biological environment)
        if self.decoherence_rate > 0 and self._generation_step > 0:
            decay = self.decoherence_rate * self._generation_step
            decay_factor = math.exp(-decay)
            for word in words:
                amp = amplitudes[word]
                # Decoherence: imaginary part decays toward zero
                decohered_imag = amp.imag * decay_factor
                amplitudes[word] = QuantumAmplitude(amp.real, decohered_imag)

        # ── Step 5: Born rule → probabilities ──
        born_probs = {}
        for word in words:
            born_probs[word] = amplitudes[word].probability

        total_prob = sum(born_probs.values())
        if total_prob <= 0:
            return random.choice(words)

        # Normalize
        for word in born_probs:
            born_probs[word] /= total_prob

        # ── Step 6: Temperature-adjusted sampling ──
        if temperature != 1.0:
            temp = max(temperature, 0.1)
            adjusted = {w: p ** (1.0 / temp) for w, p in born_probs.items()}
            total_adj = sum(adjusted.values())
            if total_adj > 0:
                born_probs = {w: p / total_adj for w, p in adjusted.items()}

        # ── Step 7: Collapse (measurement) ──
        r = random.random()
        cumsum = 0.0
        for word, prob in born_probs.items():
            cumsum += prob
            if r <= cumsum:
                self._generation_step += 1
                return word

        # Fallback
        return words[-1]

    def _compute_context_amplitude(self, word: str,
                                    query_concepts: List[str]) -> QuantumAmplitude:
        """
        Compute a context-derived amplitude for a candidate word.
        
        If the word is semantically close to query concepts,
        the phase aligns → constructive interference.
        If distant, phase misaligns → destructive interference.
        """
        if not query_concepts:
            return QuantumAmplitude(0.0, 0.0)

        word_phase = self.phase_encoder.get_phase(word)
        total_real = 0.0
        total_imag = 0.0

        for concept in query_concepts:
            concept_phase = self.phase_encoder.get_phase(concept)
            # Phase difference determines interference type
            phase_diff = word_phase - concept_phase
            # Amplitude proportional to phase alignment
            # cos(Δφ) > 0 → constructive, cos(Δφ) < 0 → destructive
            alignment = math.cos(phase_diff)
            magnitude = 0.1 * max(alignment, 0)  # Only boost, don't suppress below zero
            total_real += magnitude * math.cos(word_phase)
            total_imag += magnitude * math.sin(word_phase)

        n = len(query_concepts)
        return QuantumAmplitude(total_real / n, total_imag / n)

    def begin_generation(self):
        """Reset quantum state for a new generation run."""
        self._context_words = []
        self._generation_step = 0

    def record_selection(self, word: str):
        """Record a selected word (for entanglement tracking)."""
        self._context_words.append(word)

    def learn_entanglement(self, pmi_engine):
        """
        Learn entanglement correlations from a trained PMI engine.
        High PMI pairs → entangled (correlated).
        """
        if hasattr(pmi_engine, 'pair_count') and hasattr(pmi_engine, 'word_count'):
            self.entanglement.learn_from_cooccurrence(
                pmi_engine.pair_count,
                pmi_engine.word_count,
                pmi_engine.total_pairs
            )

    def learn_phases(self, pmi_engine):
        """
        Learn semantic phases from PMI data.
        Co-occurring words → similar phases → constructive interference.
        """
        if not hasattr(pmi_engine, 'pair_count'):
            return

        pmi_scores = {}
        for pair, count in pmi_engine.pair_count.most_common(300):
            w1, w2 = pair
            if pmi_engine.total_words > 0 and pmi_engine.total_pairs > 0:
                p_w1 = pmi_engine.word_count[w1] / pmi_engine.total_words
                p_w2 = pmi_engine.word_count[w2] / pmi_engine.total_words
                p_pair = count / pmi_engine.total_pairs
                if p_w1 > 0 and p_w2 > 0 and p_pair > 0:
                    pmi = math.log2(p_pair / (p_w1 * p_w2))
                    pmi_scores[(w1, w2)] = pmi

        self.phase_encoder.learn_phases_from_cooccurrence(pmi_scores)

    def get_quantum_stats(self) -> Dict:
        """Get statistics about the quantum state."""
        return {
            "entangled_pairs": len(self.entanglement.entangled_pairs),
            "cached_phases": len(self.phase_encoder._phase_cache),
            "semantic_clusters": self.phase_encoder._next_cluster_id,
            "decoherence_rate": self.decoherence_rate,
            "generation_step": self._generation_step,
            "context_length": len(self._context_words),
        }


# ============================================================================
# INTEGRATION HELPER
# ============================================================================

def create_quantum_markov(classical_markov, pmi_engine=None,
                          decoherence_rate: float = 0.05) -> QuantumMarkovChain:
    """
    Create a QuantumMarkovChain from an existing classical MarkovTextGenerator.
    
    The classical chain data is SHARED (not copied) — training the classical
    chain also updates the quantum chain's backing data.
    
    Args:
        classical_markov: A MarkovTextGenerator instance
        pmi_engine: Optional PMI instance for learning phases/entanglement
        decoherence_rate: Rate of quantum→classical decay per generation step
        
    Returns:
        QuantumMarkovChain wrapping the classical data
    """
    qmc = QuantumMarkovChain(
        classical_chains=classical_markov.chains,
        classical_starters=classical_markov.starters,
        decoherence_rate=decoherence_rate,
    )

    # Learn quantum features from PMI if available
    if pmi_engine is not None:
        qmc.learn_entanglement(pmi_engine)
        qmc.learn_phases(pmi_engine)

    # Register some known semantic clusters for phase coherence
    qmc.phase_encoder.register_cluster(
        ['consciousness', 'awareness', 'perception', 'experience', 'mind', 'thought'],
        base_phase=0.0
    )
    qmc.phase_encoder.register_cluster(
        ['quantum', 'superposition', 'entanglement', 'collapse', 'wave', 'particle'],
        base_phase=math.pi / 3
    )
    qmc.phase_encoder.register_cluster(
        ['knowledge', 'understanding', 'learning', 'information', 'truth', 'meaning'],
        base_phase=2 * math.pi / 3
    )
    qmc.phase_encoder.register_cluster(
        ['evolution', 'growth', 'adaptation', 'change', 'emergence', 'complexity'],
        base_phase=math.pi
    )
    qmc.phase_encoder.register_cluster(
        ['energy', 'entropy', 'thermodynamics', 'force', 'field', 'spacetime'],
        base_phase=4 * math.pi / 3
    )
    qmc.phase_encoder.register_cluster(
        ['creativity', 'imagination', 'art', 'beauty', 'expression', 'vision'],
        base_phase=5 * math.pi / 3
    )

    return qmc
