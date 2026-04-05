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

        # Hilbert space for DisCoCat-inspired word states
        self.hilbert = HilbertSpace(dimension=8)

        # Unitary transition operator (built lazily from chain data)
        self.unitary_op = UnitaryTransitionOperator(self.phase_encoder)
        self._unitary_built = False

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

        # ── Step 3b: Hilbert space interference (DisCoCat) ──
        # Words represented as quantum states in Hilbert space.
        # Context collapses meaning via measurement — constructive/destructive
        # interference adjusts amplitudes based on semantic overlap.
        if context_words and len(context_words) >= 2:
            h_scores = self.hilbert.interference_score(words, context_words[-5:])
            for word in words:
                factor = h_scores.get(word, 1.0)
                if abs(factor - 1.0) > 0.01:
                    amplitudes[word] = amplitudes[word] * float(factor)

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

    def build_unitary_operator(self):
        """
        Build the unitary transition operator from order-1 chain data.

        Converts classical transition counts into a unitary-like operator
        where transitions are complex amplitudes preserving L² norm.
        """
        if 1 not in self.chains:
            return

        # Convert {prefix_tuple: Counter} → {word: Counter}
        transition_counts = {}
        for prefix_tuple, counter in self.chains[1].items():
            if len(prefix_tuple) == 1:
                transition_counts[prefix_tuple[0]] = counter

        if transition_counts:
            self.unitary_op.build_from_counts(transition_counts)
            self._unitary_built = True

    def get_quantum_stats(self) -> Dict:
        """Get statistics about the quantum state."""
        stats = {
            "entangled_pairs": len(self.entanglement.entangled_pairs),
            "cached_phases": len(self.phase_encoder._phase_cache),
            "semantic_clusters": self.phase_encoder._next_cluster_id,
            "decoherence_rate": self.decoherence_rate,
            "generation_step": self._generation_step,
            "context_length": len(self._context_words),
            "has_hilbert_space": True,
            "hilbert_vocabulary": len(self.hilbert._words),
            "hilbert_dimension": self.hilbert.dimension,
            "unitary_operator_built": self._unitary_built,
        }
        return stats


# ============================================================================
# UNITARY TRANSITION OPERATOR
# ============================================================================

class UnitaryTransitionOperator:
    """
    Represents a word-to-word transition as a unitary operator U.

    Classical Markov: T[i,j] = P(j|i)        (stochastic, L¹ norm preserving)
    Quantum Markov:   U[i,j] = ψ(j|i)        (unitary, L² norm preserving)

    A unitary operator satisfies U†U = I (preserves total probability).
    Word transitions become rotations in Hilbert space rather than
    probability redistributions.

    The transition from word i to word j is:
        U[i,j] = √(T[i,j]) · e^{i·φ(i,j)}

    where T is the classical transition matrix and φ encodes semantic
    relationships between the words.

    References:
        [1] Whitfield et al., Phys Rev A 81, 022323 (2010) — QSW
        [2] Coecke et al., Lambek Festschrift (2010) — DisCoCat
    """

    def __init__(self, phase_encoder: SemanticPhaseEncoder = None):
        self.phase_encoder = phase_encoder or SemanticPhaseEncoder()
        # Sparse representation: {(from_word, to_word): QuantumAmplitude}
        self._matrix: Dict[Tuple[str, str], QuantumAmplitude] = {}
        self._row_words: Set[str] = set()  # Words that appear as "from"
        self._col_words: Set[str] = set()  # Words that appear as "to"

    def build_from_counts(self, transition_counts: Dict[str, Counter]):
        """
        Build unitary-like transition operator from classical counts.

        Args:
            transition_counts: {from_word: Counter({to_word: count})}

        The operator is constructed as:
            U[i,j] = √(count(i→j) / Σ_k count(i→k)) · e^{iφ(i,j)}

        This is not strictly unitary (would require Gram-Schmidt), but
        preserves L² norm per row, which is sufficient for the Born rule
        sampling in our quantum walk.
        """
        self._matrix.clear()
        self._row_words.clear()
        self._col_words.clear()

        for from_word, targets in transition_counts.items():
            total = sum(targets.values())
            if total == 0:
                continue

            self._row_words.add(from_word)

            for to_word, count in targets.items():
                self._col_words.add(to_word)
                # Phase encodes semantic relationship between from and to
                phase_from = self.phase_encoder.get_phase(from_word)
                phase_to = self.phase_encoder.get_phase(to_word)
                # Related words: small phase diff → constructive
                # Unrelated words: large phase diff → destructive
                transition_phase = (phase_to - phase_from) % (2 * math.pi)

                self._matrix[(from_word, to_word)] = QuantumAmplitude.from_count(
                    count, total, transition_phase
                )

    def apply(self, state: Dict[str, QuantumAmplitude]) -> Dict[str, QuantumAmplitude]:
        """
        Apply the unitary transition operator to a quantum state.

        |ψ'⟩ = U |ψ⟩

        The input state is a superposition over words (Hilbert space basis).
        The output is the evolved state after one transition step.

        Args:
            state: {word: QuantumAmplitude} — current state vector

        Returns:
            New state vector after transition
        """
        new_state: Dict[str, QuantumAmplitude] = defaultdict(lambda: QuantumAmplitude(0.0, 0.0))

        for from_word, from_amp in state.items():
            if from_amp.probability < 1e-15:
                continue
            # Find all transitions from this word
            for (fw, tw), trans_amp in self._matrix.items():
                if fw != from_word:
                    continue
                # Matrix multiplication: new[tw] += U[fw,tw] * state[fw]
                # Complex multiplication: (a+bi)(c+di) = (ac-bd) + (ad+bc)i
                a, b = from_amp.real, from_amp.imag
                c, d = trans_amp.real, trans_amp.imag
                product = QuantumAmplitude(a * c - b * d, a * d + b * c)
                old = new_state[tw]
                new_state[tw] = QuantumAmplitude(old.real + product.real,
                                                  old.imag + product.imag)

        return dict(new_state)

    def get_transition_amplitude(self, from_word: str, to_word: str) -> QuantumAmplitude:
        """Get the amplitude for a specific word transition."""
        return self._matrix.get((from_word, to_word), QuantumAmplitude(0.0, 0.0))


# ============================================================================
# HILBERT SPACE WORD REPRESENTATION
# ============================================================================

class HilbertSpaceWord:
    """
    Represents a word as a quantum state in a Hilbert space.

    In the DisCoCat framework, a word's meaning is a superposition of
    basis states. The word only "actualizes" into a concrete sense when
    measured in the context of a sentence (the "observer" effect).

    |word⟩ = Σ_i α_i |basis_i⟩

    where each basis state represents a different sense/context and
    α_i are complex amplitudes satisfying Σ|α_i|² = 1.

    This allows modeling polysemy (words with multiple meanings) and
    context-dependent meaning resolution through quantum measurement.

    References:
        [4] DisCoCat: Coecke et al., MDPI Applied Sciences 12(11), 5651
        [8] Quantum-Inspired Interference: arxiv.org/html/2504.13202v2
    """

    def __init__(self, word: str, dimension: int = 8):
        self.word = word
        self.dimension = dimension
        # State vector: list of complex amplitudes
        self.amplitudes: List[QuantumAmplitude] = []
        self._initialize_state()

    def _initialize_state(self):
        """
        Initialize word state based on word hash.
        Creates a deterministic superposition that is unique per word
        but consistent across runs.
        """
        # Use word hash to seed a deterministic state
        seed = hash(self.word) % (2**31)
        rng = random.Random(seed)

        raw = []
        for _ in range(self.dimension):
            # Random amplitude components
            r = rng.gauss(0, 1)
            i = rng.gauss(0, 1)
            raw.append(QuantumAmplitude(r, i))

        # Normalize so total probability = 1
        total_prob = sum(a.probability for a in raw)
        if total_prob > 0:
            scale = 1.0 / math.sqrt(total_prob)
            self.amplitudes = [QuantumAmplitude(a.real * scale, a.imag * scale) for a in raw]
        else:
            # Fallback: equal superposition
            val = 1.0 / math.sqrt(self.dimension)
            self.amplitudes = [QuantumAmplitude(val, 0.0) for _ in range(self.dimension)]

    def inner_product(self, other: 'HilbertSpaceWord') -> complex:
        """
        ⟨self|other⟩ — measures semantic similarity in Hilbert space.

        High |⟨a|b⟩|² → words are semantically related.
        Low  |⟨a|b⟩|² → words are semantically distant.

        This replaces classical cosine similarity with quantum overlap.
        """
        if len(self.amplitudes) != len(other.amplitudes):
            return complex(0, 0)

        result_real = 0.0
        result_imag = 0.0
        for a, b in zip(self.amplitudes, other.amplitudes):
            # ⟨a|b⟩ = a*.b (conjugate of a times b)
            conj_a = a.conjugate()
            result_real += conj_a.real * b.real - conj_a.imag * b.imag
            result_imag += conj_a.real * b.imag + conj_a.imag * b.real

        return complex(result_real, result_imag)

    def overlap_probability(self, other: 'HilbertSpaceWord') -> float:
        """
        |⟨self|other⟩|² — Born rule probability of similarity.
        """
        ip = self.inner_product(other)
        return ip.real ** 2 + ip.imag ** 2

    def measure_in_context(self, context_words: List['HilbertSpaceWord']) -> int:
        """
        Collapse the word state by "measuring" it in the context of
        surrounding words. Returns the collapsed basis state index.

        The measurement operator M is constructed from the context:
            M = Σ_i |context_i⟩⟨context_i|

        The word collapses to the basis state most aligned with context.
        """
        if not context_words or not self.amplitudes:
            # No context → collapse to highest-amplitude basis
            probs = [a.probability for a in self.amplitudes]
            return probs.index(max(probs))

        # Build context-modified probabilities
        modified_probs = []
        for dim_idx in range(self.dimension):
            base_prob = self.amplitudes[dim_idx].probability
            # Context boost: sum overlaps with context words in this dimension
            boost = 0.0
            for cw in context_words:
                if dim_idx < len(cw.amplitudes):
                    boost += cw.amplitudes[dim_idx].probability
            modified_probs.append(base_prob * (1.0 + boost))

        total = sum(modified_probs)
        if total <= 0:
            return 0

        # Born rule collapse
        r = random.random() * total
        cumsum = 0.0
        for idx, p in enumerate(modified_probs):
            cumsum += p
            if r <= cumsum:
                return idx

        return len(modified_probs) - 1

    def __repr__(self):
        total_p = sum(a.probability for a in self.amplitudes)
        return f"HilbertWord('{self.word}', dim={self.dimension}, ΣP={total_p:.4f})"


class HilbertSpace:
    """
    A Hilbert space for the vocabulary — maps words to quantum states
    and provides quantum-native similarity operations.

    This is the DisCoCat-inspired "meaning space" where:
    - Words are quantum states
    - Meaning is a superposition
    - Context collapses meaning via measurement
    - Similarity is quantum overlap (inner product)
    """

    def __init__(self, dimension: int = 8):
        self.dimension = dimension
        self._words: Dict[str, HilbertSpaceWord] = {}

    def get_word_state(self, word: str) -> HilbertSpaceWord:
        """Get or create the quantum state for a word."""
        w = word.lower()
        if w not in self._words:
            self._words[w] = HilbertSpaceWord(w, self.dimension)
        return self._words[w]

    def similarity(self, word_a: str, word_b: str) -> float:
        """Quantum overlap similarity: |⟨a|b⟩|²"""
        state_a = self.get_word_state(word_a)
        state_b = self.get_word_state(word_b)
        return state_a.overlap_probability(state_b)

    def context_resolve(self, word: str, context: List[str]) -> int:
        """
        Resolve a word's meaning given context.
        Returns the collapsed basis state index.
        """
        word_state = self.get_word_state(word)
        context_states = [self.get_word_state(c) for c in context]
        return word_state.measure_in_context(context_states)

    def interference_score(self, candidates: List[str],
                           context: List[str]) -> Dict[str, float]:
        """
        Score candidate words by quantum interference with context.

        Constructive interference boosts related candidates.
        Destructive interference suppresses unrelated ones.

        Returns: {word: interference_adjusted_score}
        """
        scores = {}
        context_states = [self.get_word_state(c) for c in context]

        for candidate in candidates:
            cand_state = self.get_word_state(candidate)
            # Sum interference with all context words
            total_interference = 0.0
            for ctx_state in context_states:
                ip = cand_state.inner_product(ctx_state)
                # Real part of inner product = interference term
                # Positive = constructive, Negative = destructive
                total_interference += ip.real

            # Normalize by context length
            if context_states:
                total_interference /= len(context_states)

            # Map to [0, 2] range: 1.0 = neutral, >1 = boosted, <1 = suppressed
            scores[candidate] = max(0.01, 1.0 + total_interference)

        return scores

    def get_stats(self) -> Dict:
        """Get Hilbert space statistics."""
        return {
            "dimension": self.dimension,
            "vocabulary_size": len(self._words),
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

    # Build the unitary transition operator from chain data
    qmc.build_unitary_operator()

    return qmc
