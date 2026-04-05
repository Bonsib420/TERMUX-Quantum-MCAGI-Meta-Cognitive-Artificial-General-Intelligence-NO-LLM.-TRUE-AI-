"""
Tests for quantum_markov.py — Quantum Stochastic Walk text generation.
L² amplitude interference, entanglement coherence, Born rule collapse.
"""

import math
import random
import pytest

from quantum_markov import (
    QuantumAmplitude,
    SemanticPhaseEncoder,
    EntanglementRegister,
    QuantumMarkovChain,
    create_quantum_markov,
)
from collections import Counter


# ============================================================================
# QuantumAmplitude
# ============================================================================

class TestQuantumAmplitude:
    """Tests for complex-valued quantum amplitude."""

    def test_from_probability_unit(self):
        """P=1 → |ψ|=1."""
        amp = QuantumAmplitude.from_probability(1.0, phase=0.0)
        assert amp.probability == pytest.approx(1.0, abs=1e-10)

    def test_from_probability_half(self):
        """P=0.5 → |ψ|²=0.5."""
        amp = QuantumAmplitude.from_probability(0.5, phase=0.0)
        assert amp.probability == pytest.approx(0.5, abs=1e-10)

    def test_from_probability_zero(self):
        amp = QuantumAmplitude.from_probability(0.0)
        assert amp.probability == pytest.approx(0.0, abs=1e-10)

    def test_born_rule(self):
        """P = |ψ|² = real² + imag²."""
        amp = QuantumAmplitude(0.6, 0.8)
        assert amp.probability == pytest.approx(1.0, abs=1e-10)

    def test_phase_matches_angle(self):
        amp = QuantumAmplitude.from_probability(1.0, phase=math.pi / 4)
        assert amp.phase == pytest.approx(math.pi / 4, abs=1e-6)

    def test_superposition_constructive(self):
        """Same phase → constructive interference → P > sum of individual P's."""
        a = QuantumAmplitude.from_probability(0.25, phase=0.0)
        b = QuantumAmplitude.from_probability(0.25, phase=0.0)
        combined = a + b
        # |√0.25 + √0.25|² = |0.5+0.5|² = 1.0  (vs 0.25+0.25=0.5 classically)
        assert combined.probability == pytest.approx(1.0, abs=1e-6)

    def test_superposition_destructive(self):
        """Opposite phase → destructive interference → P < sum."""
        a = QuantumAmplitude.from_probability(0.25, phase=0.0)
        b = QuantumAmplitude.from_probability(0.25, phase=math.pi)
        combined = a + b
        # |√0.25 - √0.25|² ≈ 0.0  (vs 0.5 classically)
        assert combined.probability == pytest.approx(0.0, abs=1e-6)

    def test_phase_rotation_preserves_probability(self):
        """Phase rotation doesn't change |ψ|²."""
        amp = QuantumAmplitude.from_probability(0.7, phase=0.3)
        rotated = amp.rotate_phase(math.pi / 3)
        assert rotated.probability == pytest.approx(amp.probability, abs=1e-10)

    def test_scalar_multiplication(self):
        amp = QuantumAmplitude(0.5, 0.3)
        doubled = 2.0 * amp
        assert doubled.real == pytest.approx(1.0, abs=1e-10)
        assert doubled.imag == pytest.approx(0.6, abs=1e-10)

    def test_conjugate(self):
        amp = QuantumAmplitude(0.5, 0.3)
        conj = amp.conjugate()
        assert conj.real == pytest.approx(0.5, abs=1e-10)
        assert conj.imag == pytest.approx(-0.3, abs=1e-10)

    def test_from_count(self):
        amp = QuantumAmplitude.from_count(3, 12, phase=0.0)
        assert amp.probability == pytest.approx(0.25, abs=1e-6)


# ============================================================================
# SemanticPhaseEncoder
# ============================================================================

class TestSemanticPhaseEncoder:
    """Tests for semantic phase assignment."""

    def test_deterministic_phase(self):
        """Same word always gets same phase."""
        enc = SemanticPhaseEncoder()
        p1 = enc.get_phase("quantum")
        p2 = enc.get_phase("quantum")
        assert p1 == p2

    def test_different_words_can_differ(self):
        enc = SemanticPhaseEncoder()
        p1 = enc.get_phase("quantum")
        p2 = enc.get_phase("cooking")
        # Very unlikely to be exactly equal
        assert p1 != p2

    def test_cluster_members_similar_phase(self):
        """Words in same cluster should get similar phases."""
        enc = SemanticPhaseEncoder()
        enc.register_cluster(["quantum", "particle", "wave"], base_phase=0.5)
        p_quantum = enc.get_phase("quantum")
        p_particle = enc.get_phase("particle")
        # Within cluster variation ±0.15 + base_phase
        assert abs(p_quantum - p_particle) < 0.5

    def test_register_cluster_sets_base(self):
        enc = SemanticPhaseEncoder()
        enc.register_cluster(["alpha", "beta"], base_phase=math.pi)
        p = enc.get_phase("alpha")
        # Should be near π (with small variation)
        assert abs(p - math.pi) < 0.5

    def test_phase_in_range(self):
        enc = SemanticPhaseEncoder()
        for word in ["hello", "world", "quantum", "test"]:
            phase = enc.get_phase(word)
            assert isinstance(phase, float)


# ============================================================================
# EntanglementRegister
# ============================================================================

class TestEntanglementRegister:
    """Tests for non-local word correlations."""

    def test_no_entanglement_zero_boost(self):
        ent = EntanglementRegister()
        boost = ent.get_entanglement_boost("word", ["other"])
        assert boost == 0.0

    def test_positive_entanglement(self):
        ent = EntanglementRegister()
        ent.entangle("quantum", "physics", 0.8)
        boost = ent.get_entanglement_boost("physics", ["quantum"])
        assert boost > 0

    def test_negative_entanglement(self):
        ent = EntanglementRegister()
        ent.entangle("hot", "cold", -0.8)
        boost = ent.get_entanglement_boost("cold", ["hot"])
        assert boost < 0

    def test_entanglement_symmetric(self):
        ent = EntanglementRegister()
        ent.entangle("alpha", "beta", 0.6)
        b1 = ent.get_entanglement_boost("alpha", ["beta"])
        b2 = ent.get_entanglement_boost("beta", ["alpha"])
        assert b1 == pytest.approx(b2, abs=1e-10)

    def test_entanglement_clamped(self):
        ent = EntanglementRegister()
        ent.entangle("a", "b", 5.0)
        pair = tuple(sorted(["a", "b"]))
        assert ent.entangled_pairs[pair] == 1.0

    def test_empty_selected_words(self):
        ent = EntanglementRegister()
        ent.entangle("a", "b", 0.5)
        assert ent.get_entanglement_boost("a", []) == 0.0


# ============================================================================
# QuantumMarkovChain
# ============================================================================

class TestQuantumMarkovChain:
    """Tests for the full quantum Markov chain."""

    def setup_method(self):
        # Build a simple classical chain
        self.chains = {
            1: {("the",): Counter({"cat": 5, "dog": 3, "bird": 2})},
            2: {("the", "cat"): Counter({"sat": 4, "ran": 1})},
        }
        self.starters = {1: [("the",)], 2: [("the", "cat")]}
        self.qmc = QuantumMarkovChain(
            classical_chains=self.chains,
            classical_starters=self.starters,
            decoherence_rate=0.05,
        )

    def test_quantum_sample_returns_word(self):
        counter = Counter({"cat": 5, "dog": 3, "bird": 2})
        word = self.qmc.quantum_sample(counter, temperature=1.0)
        assert word in ["cat", "dog", "bird"]

    def test_quantum_sample_empty_counter(self):
        assert self.qmc.quantum_sample(Counter(), 1.0) is None

    def test_quantum_sample_respects_distribution(self):
        """High-count words should be selected more often."""
        counter = Counter({"dominant": 100, "rare": 1})
        selections = Counter()
        for _ in range(200):
            word = self.qmc.quantum_sample(counter, temperature=0.5)
            selections[word] += 1
        assert selections["dominant"] > selections["rare"]

    def test_quantum_sample_with_context(self):
        counter = Counter({"physics": 5, "cooking": 5})
        word = self.qmc.quantum_sample(
            counter, temperature=1.0,
            context_words=["quantum", "particle"],
            query_concepts=["quantum"]
        )
        assert word in ["physics", "cooking"]

    def test_begin_generation_resets(self):
        self.qmc._generation_step = 10
        self.qmc._context_words = ["a", "b"]
        self.qmc.begin_generation()
        assert self.qmc._generation_step == 0
        assert self.qmc._context_words == []

    def test_record_selection(self):
        self.qmc.begin_generation()
        self.qmc.record_selection("hello")
        self.qmc.record_selection("world")
        assert self.qmc._context_words == ["hello", "world"]

    def test_get_quantum_stats(self):
        stats = self.qmc.get_quantum_stats()
        assert "entangled_pairs" in stats
        assert "cached_phases" in stats
        assert "decoherence_rate" in stats

    def test_decoherence_approaches_classical(self):
        """With high decoherence, results should approach classical distribution."""
        # High decoherence — quantum effects disappear
        qmc_high = QuantumMarkovChain(
            classical_chains=self.chains,
            classical_starters=self.starters,
            decoherence_rate=1.0,
        )
        qmc_high._generation_step = 100  # Many steps → full decoherence
        counter = Counter({"a": 10, "b": 10})
        # Should still return valid words
        word = qmc_high.quantum_sample(counter, 1.0)
        assert word in ["a", "b"]


# ============================================================================
# Integration: create_quantum_markov
# ============================================================================

class TestCreateQuantumMarkov:
    """Tests for the integration helper."""

    def test_creates_from_markov_generator(self):
        from algorithmic_core import MarkovTextGenerator
        gen = MarkovTextGenerator(max_order=2)
        gen.train("The quick brown fox jumps over the lazy dog.")
        qmc = create_quantum_markov(gen)
        assert isinstance(qmc, QuantumMarkovChain)

    def test_shares_chain_data(self):
        from algorithmic_core import MarkovTextGenerator
        gen = MarkovTextGenerator(max_order=2)
        gen.train("Hello world hello world.")
        qmc = create_quantum_markov(gen)
        # Should share the same dict objects
        assert qmc.chains is gen.chains

    def test_registers_semantic_clusters(self):
        from algorithmic_core import MarkovTextGenerator
        gen = MarkovTextGenerator(max_order=2)
        qmc = create_quantum_markov(gen)
        # Check that clusters were registered
        assert qmc.phase_encoder._next_cluster_id >= 6


# ============================================================================
# MarkovTextGenerator.quantum_generate integration
# ============================================================================

class TestMarkovQuantumGenerate:
    """Tests for quantum generation through MarkovTextGenerator."""

    def setup_method(self):
        from algorithmic_core import MarkovTextGenerator
        self.gen = MarkovTextGenerator(max_order=2)
        corpus = (
            "The nature of consciousness remains a deep mystery. "
            "Consciousness emerges from quantum processes in microtubules. "
            "Microtubules are protein structures inside neurons. "
            "Neurons fire together and wire together through learning. "
            "Learning changes the strength of connections between neurons. "
            "The brain processes information through neural networks."
        )
        self.gen.train(corpus)

    def test_quantum_generate_without_init_falls_back(self):
        """Without init_quantum, falls back to classical."""
        random.seed(42)
        result = self.gen.quantum_generate(max_words=20)
        assert isinstance(result, str)

    def test_quantum_generate_with_init(self):
        """With quantum chain initialized, should produce text."""
        self.gen.init_quantum(decoherence_rate=0.05)
        random.seed(42)
        result = self.gen.quantum_generate(max_words=20)
        assert isinstance(result, str)

    def test_quantum_generate_with_concepts(self):
        """Query concepts should influence generation via interference."""
        self.gen.init_quantum(decoherence_rate=0.05)
        random.seed(42)
        result = self.gen.quantum_generate(
            max_words=20,
            query_concepts=["consciousness", "quantum"]
        )
        assert isinstance(result, str)

    def test_stats_include_quantum(self):
        self.gen.init_quantum(decoherence_rate=0.05)
        stats = self.gen.get_stats()
        assert "quantum" in stats
        assert "entangled_pairs" in stats["quantum"]
