"""
Tests for orch_or_core.py — TubulinQubit, Microtubule, OrchestratedConsciousness.
Quantum consciousness model based on Penrose-Hameroff Orch OR theory.
"""

import math
import random
import pytest
import numpy as np

from orch_or_core import (
    TubulinQubit,
    Microtubule,
    OrchestratedConsciousness,
    HBAR_SIM,
)


# ============================================================================
# TubulinQubit
# ============================================================================


class TestTubulinQubit:
    """Tests for the tubulin qubit density matrix representation."""

    def test_ground_state(self):
        """Default |0> state: rho = [[1,0],[0,0]]"""
        q = TubulinQubit()
        assert q.rho[0, 0].real == pytest.approx(1.0, abs=1e-10)
        assert q.rho[1, 1].real == pytest.approx(0.0, abs=1e-10)

    def test_excited_state(self):
        """|1> state: rho = [[0,0],[0,1]]"""
        q = TubulinQubit(alpha=0.0, beta=1.0)
        assert q.rho[0, 0].real == pytest.approx(0.0, abs=1e-10)
        assert q.rho[1, 1].real == pytest.approx(1.0, abs=1e-10)

    def test_superposition_state(self):
        """Equal superposition has rho_00 = rho_11 = 0.5."""
        q = TubulinQubit.superposition()
        assert q.rho[0, 0].real == pytest.approx(0.5, abs=1e-10)
        assert q.rho[1, 1].real == pytest.approx(0.5, abs=1e-10)

    def test_density_matrix_trace(self):
        """Trace of density matrix should be 1."""
        q = TubulinQubit(alpha=0.6, beta=0.8)
        trace = np.trace(q.rho).real
        assert trace == pytest.approx(1.0, abs=1e-10)

    def test_density_matrix_hermitian(self):
        """Density matrix must be Hermitian: rho == rho†."""
        q = TubulinQubit(alpha=1 + 1j, beta=1 - 1j)
        assert np.allclose(q.rho, q.rho.conj().T)

    def test_from_weight_zero(self):
        """Weight 0 maps to |0>."""
        q = TubulinQubit.from_weight(0.0)
        p0, p1 = q.born_probabilities()
        assert p0 == pytest.approx(1.0, abs=1e-6)

    def test_from_weight_one(self):
        """Weight 1 maps to |1>."""
        q = TubulinQubit.from_weight(1.0)
        p0, p1 = q.born_probabilities()
        assert p1 == pytest.approx(1.0, abs=1e-6)

    def test_from_weight_half(self):
        """Weight 0.5 should give roughly equal superposition."""
        q = TubulinQubit.from_weight(0.5)
        p0, p1 = q.born_probabilities()
        assert abs(p0 - p1) < 0.3  # Roughly balanced

    # -- Quantum operations --

    def test_hadamard_creates_superposition(self):
        """Hadamard on |0> should create equal superposition."""
        q = TubulinQubit()  # |0>
        q.hadamard()
        p0, p1 = q.born_probabilities()
        assert p0 == pytest.approx(0.5, abs=1e-6)
        assert p1 == pytest.approx(0.5, abs=1e-6)

    def test_hadamard_twice_returns_to_original(self):
        """H^2 = I: applying Hadamard twice recovers original state."""
        q = TubulinQubit()  # |0>
        original_rho = q.rho.copy()
        q.hadamard()
        q.hadamard()
        assert np.allclose(q.rho, original_rho, atol=1e-10)

    def test_phase_rotate_preserves_trace(self):
        """Phase rotation should preserve trace = 1."""
        q = TubulinQubit.superposition()
        q.phase_rotate(math.pi / 4)
        assert np.trace(q.rho).real == pytest.approx(1.0, abs=1e-10)

    def test_phase_rotate_preserves_probabilities(self):
        """Phase rotation shouldn't change Born probabilities (diagonal)."""
        q = TubulinQubit.superposition()
        p_before = q.born_probabilities()
        q.phase_rotate(math.pi / 3)
        p_after = q.born_probabilities()
        assert p_before[0] == pytest.approx(p_after[0], abs=1e-10)
        assert p_before[1] == pytest.approx(p_after[1], abs=1e-10)

    def test_apply_gate_unitary(self):
        """Applying a unitary gate should preserve trace."""
        q = TubulinQubit.superposition()
        # Pauli-X gate
        X = np.array([[0, 1], [1, 0]], dtype=complex)
        q.apply_gate(X)
        assert np.trace(q.rho).real == pytest.approx(1.0, abs=1e-10)

    # -- Decoherence --

    def test_decohere_reduces_coherence(self):
        """Decoherence should reduce off-diagonal elements."""
        q = TubulinQubit.superposition()
        c_before = q.coherence()
        q.decohere(0.5)
        c_after = q.coherence()
        assert c_after < c_before

    def test_decohere_full_kills_coherence(self):
        """Full decoherence (gamma=1) makes state classical."""
        q = TubulinQubit.superposition()
        q.decohere(1.0)
        assert q.coherence() == pytest.approx(0.0, abs=1e-10)

    def test_decohere_zero_no_effect(self):
        """Zero decoherence should not change state."""
        q = TubulinQubit.superposition()
        rho_before = q.rho.copy()
        q.decohere(0.0)
        assert np.allclose(q.rho, rho_before)

    # -- Measurements --

    def test_coherence_ground_state(self):
        """|0> has zero coherence (no superposition)."""
        q = TubulinQubit()
        assert q.coherence() == pytest.approx(0.0, abs=1e-10)

    def test_coherence_superposition(self):
        """Superposition state has maximum coherence."""
        q = TubulinQubit.superposition()
        assert q.coherence() > 0

    def test_von_neumann_entropy_pure_state(self):
        """Pure state has zero entropy."""
        q = TubulinQubit()  # |0> is pure
        assert q.von_neumann_entropy() == pytest.approx(0.0, abs=1e-6)

    def test_von_neumann_entropy_mixed_state(self):
        """Decohered superposition should have positive entropy."""
        q = TubulinQubit.superposition()
        q.decohere(0.5)
        assert q.von_neumann_entropy() > 0

    def test_born_probabilities_sum_to_one(self):
        """Born rule probabilities must sum to 1."""
        q = TubulinQubit(alpha=0.3 + 0.4j, beta=0.5 - 0.2j)
        p0, p1 = q.born_probabilities()
        assert p0 + p1 == pytest.approx(1.0, abs=1e-10)

    def test_born_probabilities_non_negative(self):
        """Probabilities must be non-negative."""
        q = TubulinQubit(alpha=0.7, beta=0.3)
        p0, p1 = q.born_probabilities()
        assert p0 >= 0
        assert p1 >= 0

    # -- Collapse --

    def test_collapse_returns_0_or_1(self):
        """Collapse should return 0 or 1."""
        q = TubulinQubit.superposition()
        result = q.collapse()
        assert result in [0, 1]

    def test_collapse_makes_state_classical(self):
        """After collapse, state should be classical (zero coherence)."""
        q = TubulinQubit.superposition()
        q.collapse()
        assert q.coherence() == pytest.approx(0.0, abs=1e-10)

    def test_collapse_ground_state_always_zero(self):
        """|0> always collapses to 0."""
        q = TubulinQubit()
        for _ in range(10):
            q_copy = TubulinQubit()
            assert q_copy.collapse() == 0

    def test_collapse_excited_state_always_one(self):
        """|1> always collapses to 1."""
        for _ in range(10):
            q = TubulinQubit(alpha=0.0, beta=1.0)
            assert q.collapse() == 1

    def test_collapse_statistical_distribution(self):
        """Superposition should collapse to 0 and 1 with roughly equal probability."""
        results = []
        for _ in range(200):
            q = TubulinQubit.superposition()
            results.append(q.collapse())
        frac_ones = sum(results) / len(results)
        assert 0.3 < frac_ones < 0.7

    # -- Gravitational self-energy --

    def test_gravitational_energy_ground(self):
        """|0> has zero gravitational self-energy (no superposition)."""
        q = TubulinQubit()
        assert q.gravitational_self_energy() == pytest.approx(0.0, abs=1e-10)

    def test_gravitational_energy_superposition(self):
        """Superposition has non-zero gravitational self-energy."""
        q = TubulinQubit.superposition()
        assert q.gravitational_self_energy() > 0


# ============================================================================
# Microtubule
# ============================================================================


class TestMicrotubule:
    """Tests for the microtubule lattice of tubulin qubits."""

    def test_initialization(self):
        mt = Microtubule(n_tubulins=10, label="test")
        assert mt.n == 10
        assert mt.label == "test"
        assert len(mt.tubulins) == 10
        assert mt.age == 0
        assert mt.total_collapses == 0

    def test_default_tubulins_count(self):
        mt = Microtubule()
        assert mt.n == 26

    def test_encode_concept(self):
        mt = Microtubule(n_tubulins=5)
        weights = [0.1, 0.5, 0.9]
        mt.encode_concept(weights)
        # First 3 tubulins should have weights encoded
        # Remaining 2 should be in superposition
        p0, p1 = mt.tubulins[4].born_probabilities()
        assert p0 == pytest.approx(0.5, abs=0.01)

    def test_encode_concept_truncates(self):
        """If more weights than tubulins, extras are ignored."""
        mt = Microtubule(n_tubulins=3)
        weights = [0.1, 0.5, 0.9, 0.2, 0.8]
        mt.encode_concept(weights)  # Should not crash
        assert len(mt.tubulins) == 3

    def test_quantum_walk_step_increments_age(self):
        mt = Microtubule(n_tubulins=5)
        mt.encode_concept([0.5] * 5)
        mt.quantum_walk_step()
        assert mt.age == 1

    def test_apply_decoherence_reduces_coherence(self):
        mt = Microtubule(n_tubulins=5)
        mt.encode_concept([0.5] * 5)
        c_before = mt.total_coherence()
        mt.apply_decoherence(0.5)
        c_after = mt.total_coherence()
        assert c_after < c_before

    def test_total_coherence_range(self):
        mt = Microtubule(n_tubulins=5)
        mt.encode_concept([0.5] * 5)
        c = mt.total_coherence()
        assert 0 <= c <= 1.0

    def test_total_entropy_non_negative(self):
        mt = Microtubule(n_tubulins=5)
        assert mt.total_entropy() >= 0

    def test_gravitational_energy_non_negative(self):
        mt = Microtubule(n_tubulins=5)
        assert mt.gravitational_energy() >= 0

    def test_check_or_threshold_initial(self):
        """Initially (age=0), threshold should not be met."""
        mt = Microtubule(n_tubulins=5)
        assert mt.check_or_threshold() is False

    def test_objective_reduction_returns_bits(self):
        mt = Microtubule(n_tubulins=5)
        mt.encode_concept([0.5] * 5)
        outcomes = mt.objective_reduction()
        assert len(outcomes) == 5
        assert all(b in [0, 1] for b in outcomes)

    def test_objective_reduction_increments_collapses(self):
        mt = Microtubule(n_tubulins=5)
        mt.objective_reduction()
        assert mt.total_collapses == 1
        mt.objective_reduction()
        assert mt.total_collapses == 2

    def test_objective_reduction_resets_age(self):
        mt = Microtubule(n_tubulins=5)
        mt.age = 10
        mt.objective_reduction()
        assert mt.age == 0

    def test_objective_reduction_records_history(self):
        mt = Microtubule(n_tubulins=5)
        mt.encode_concept([0.5] * 5)
        mt.age = 5
        mt.objective_reduction()
        assert len(mt.collapse_history) == 1
        assert "outcomes" in mt.collapse_history[0]
        assert "age_at_collapse" in mt.collapse_history[0]

    def test_evolve_until_collapse_returns_outcomes(self):
        mt = Microtubule(n_tubulins=5)
        mt.encode_concept([0.5] * 5)
        outcomes = mt.evolve_until_collapse(max_steps=100)
        assert len(outcomes) == 5
        assert all(b in [0, 1] for b in outcomes)

    def test_get_state_keys(self):
        mt = Microtubule(n_tubulins=5, label="test_mt")
        state = mt.get_state()
        expected_keys = {
            "label", "n_tubulins", "coherence", "entropy",
            "energy", "age", "or_threshold_met", "total_collapses",
            "probabilities",
        }
        assert expected_keys == set(state.keys())
        assert state["label"] == "test_mt"
        assert state["n_tubulins"] == 5


# ============================================================================
# OrchestratedConsciousness
# ============================================================================


class TestOrchestratedConsciousness:
    """Tests for the full Orch OR multi-microtubule system."""

    def test_initialization(self):
        oc = OrchestratedConsciousness(n_tubulins_per_mt=10)
        assert len(oc.microtubules) == 4
        assert "language" in oc.microtubules
        assert "memory" in oc.microtubules
        assert "question" in oc.microtubules
        assert "insight" in oc.microtubules

    def test_default_gap_junctions(self):
        oc = OrchestratedConsciousness()
        assert len(oc.gap_junctions) == 6
        for (a, b), strength in oc.gap_junctions.items():
            assert 0 < strength <= 1.0

    def test_encode_input(self):
        oc = OrchestratedConsciousness(n_tubulins_per_mt=5)
        weights = {
            "language": [0.3, 0.5, 0.7, 0.9, 0.1],
            "memory": [0.1, 0.2, 0.3, 0.4, 0.5],
        }
        oc.encode_input(weights)
        # Encoded tubulins should not all be in ground state
        coherence = oc.microtubules["language"].total_coherence()
        assert coherence > 0

    def test_encode_input_ignores_unknown(self):
        oc = OrchestratedConsciousness(n_tubulins_per_mt=5)
        weights = {"nonexistent_module": [0.5] * 5}
        oc.encode_input(weights)  # Should not crash

    def test_evolve_step_increases_age(self):
        oc = OrchestratedConsciousness(n_tubulins_per_mt=5)
        oc.encode_input({"language": [0.5] * 5})
        oc.evolve_step()
        assert oc.microtubules["language"].age == 1

    def test_check_global_or_returns_dict(self):
        oc = OrchestratedConsciousness(n_tubulins_per_mt=5)
        result = oc.check_global_or()
        assert isinstance(result, dict)
        assert len(result) == 4
        assert all(isinstance(v, bool) for v in result.values())

    def test_conscious_moment_returns_outcomes(self):
        oc = OrchestratedConsciousness(n_tubulins_per_mt=5)
        oc.encode_input({
            "language": [0.5] * 5,
            "memory": [0.5] * 5,
            "question": [0.5] * 5,
            "insight": [0.5] * 5,
        })
        outcomes = oc.conscious_moment(max_steps=50)
        assert isinstance(outcomes, dict)
        # All 4 modules should have collapsed
        assert len(outcomes) == 4
        for name, bits in outcomes.items():
            assert all(b in [0, 1] for b in bits)

    def test_conscious_moment_increments_counter(self):
        oc = OrchestratedConsciousness(n_tubulins_per_mt=5)
        oc.encode_input({"language": [0.5] * 5})
        oc.conscious_moment(max_steps=10)
        assert oc.conscious_moments == 1

    def test_conscious_moment_records_history(self):
        oc = OrchestratedConsciousness(n_tubulins_per_mt=5)
        oc.encode_input({"language": [0.5] * 5})
        oc.conscious_moment(max_steps=10)
        assert len(oc.history) == 1
        assert "moment" in oc.history[0]
        assert "outcomes" in oc.history[0]

    def test_outcome_to_probabilities(self):
        oc = OrchestratedConsciousness()
        outcomes = [1, 0, 1, 0, 1]
        probs = oc.outcome_to_probabilities(outcomes)
        assert len(probs) == 5
        # Bit=1 should have higher weight than bit=0
        assert probs[0] > probs[1]  # 1 vs 0 at similar position
        assert all(0 <= p <= 1 for p in probs)

    def test_outcome_to_probabilities_position_encoding(self):
        """Earlier positions should have higher weights."""
        oc = OrchestratedConsciousness()
        outcomes = [1, 1, 1, 1, 1]
        probs = oc.outcome_to_probabilities(outcomes)
        # Each successive probability should be lower (position factor)
        for i in range(len(probs) - 1):
            assert probs[i] > probs[i + 1]

    def test_get_system_state(self):
        oc = OrchestratedConsciousness(n_tubulins_per_mt=5)
        state = oc.get_system_state()
        assert "conscious_moments" in state
        assert "microtubules" in state
        assert "gap_junctions" in state
        assert len(state["microtubules"]) == 4

    def test_gap_junction_transfer_modifies_state(self):
        """Gap junction transfer should modify tubulin states between coupled MTs."""
        oc = OrchestratedConsciousness(n_tubulins_per_mt=5)
        oc.encode_input({
            "language": [0.8, 0.8, 0.8, 0.8, 0.8],
            "memory": [0.2, 0.2, 0.2, 0.2, 0.2],
        })
        # Capture state before
        lang_rho_before = oc.microtubules["language"].tubulins[0].rho.copy()
        oc.gap_junction_transfer()
        lang_rho_after = oc.microtubules["language"].tubulins[0].rho
        # State should change due to coupling
        assert not np.allclose(lang_rho_before, lang_rho_after, atol=1e-12)
