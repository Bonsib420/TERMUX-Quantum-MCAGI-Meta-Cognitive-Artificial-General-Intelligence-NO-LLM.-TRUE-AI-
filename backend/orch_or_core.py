"""
?? Orchestrated Objective Reduction (Orch OR) Core
====================================================
Penrose-Hameroff model of quantum consciousness in microtubules.

The brain doesn't compute at the synapse level alone. Inside each neuron,
microtubules — lattices of tubulin protein dimers — perform quantum
computation. Each tubulin can exist in superposition. The lattice
processes information via quantum walks and coherent oscillations.
When the quantum state hits Penrose's objective reduction threshold
(E*tau >= hbar), it collapses — and that collapse IS the conscious
moment: a decision, an insight, a word chosen.

This module implements:
- Tubulin qubit: density matrix representation of a single tubulin dimer
- Microtubule: lattice of interacting tubulin qubits with quantum walks
- Objective Reduction: Penrose's gravity-threshold collapse mechanism
- Orchestration: cross-microtubule coherence via simulated gap junctions
- Decoherence: environmental noise degrading quantum state over time

Math:
- Density matrix: rho = |psi><psi| (pure) or sum_i p_i |psi_i><psi_i| (mixed)
- Von Neumann entropy: S = -Tr(rho * log(rho))
- Penrose threshold: E * tau >= hbar
- Born rule: P(outcome_i) = <i|rho|i>
- Quantum walk: rho' = C * rho * C† (coin operator applied to lattice)
"""

import math
import random
import logging
from typing import List, Dict, Tuple, Optional

try:
    import numpy as np
except ImportError:
    raise ImportError("numpy is required for Orch OR. Install: pip install numpy")

logger = logging.getLogger("quantum_ai")

# Reduced Planck constant (in eV*s for computational convenience)
HBAR = 6.582119569e-16  # eV*s
# Scaled for simulation — we use arbitrary units where threshold ~ 1.0
HBAR_SIM = 1.0


class TubulinQubit:
    """
    A single tubulin protein dimer — the fundamental unit of quantum
    computation in the Orch OR model.

    Represented as a 2x2 density matrix rho:
        rho = [[rho_00, rho_01],
               [rho_10, rho_11]]

    Pure state |psi> = alpha|0> + beta|1>:
        rho = |psi><psi| = [[|alpha|^2, alpha*beta_conj],
                             [alpha_conj*beta, |beta|^2]]

    |0> = tubulin in one conformational state (e.g. "open")
    |1> = tubulin in other conformational state (e.g. "closed")

    In Orch OR, these states correspond to different mass distributions
    of the tubulin protein, creating slightly different spacetime
    curvatures — the basis for objective reduction.
    """

    def __init__(self, alpha: complex = 1.0, beta: complex = 0.0):
        """Initialize tubulin qubit. Default = |0> (ground state)."""
        # Build density matrix from state vector
        norm = math.sqrt(abs(alpha)**2 + abs(beta)**2)
        if norm > 0:
            alpha /= norm
            beta /= norm
        self.rho = np.array([
            [abs(alpha)**2, alpha * np.conj(beta)],
            [np.conj(alpha) * beta, abs(beta)**2]
        ], dtype=complex)

    @classmethod
    def superposition(cls):
        """Create equal superposition: (|0> + |1>)/sqrt(2)"""
        return cls(alpha=1/math.sqrt(2), beta=1/math.sqrt(2))

    @classmethod
    def from_weight(cls, weight: float):
        """Create from a classical weight 0-1 (maps to rotation angle)."""
        theta = weight * math.pi
        return cls(alpha=math.cos(theta/2), beta=math.sin(theta/2))

    def apply_gate(self, gate: np.ndarray):
        """Apply a unitary gate: rho' = U * rho * U†"""
        self.rho = gate @ self.rho @ gate.conj().T

    def hadamard(self):
        """Put into superposition."""
        H = np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(2)
        self.apply_gate(H)

    def phase_rotate(self, theta: float):
        """Apply phase rotation Rz(theta)."""
        Rz = np.array([
            [np.exp(-1j * theta / 2), 0],
            [0, np.exp(1j * theta / 2)]
        ], dtype=complex)
        self.apply_gate(Rz)

    def decohere(self, gamma: float):
        """
        Apply decoherence — environment destroys quantum coherence.
        gamma: decoherence rate (0 = no decoherence, 1 = full classical)

        Off-diagonal elements decay: rho_01 *= (1 - gamma)
        This models the warm, wet biological environment.
        """
        self.rho[0, 1] *= (1 - gamma)
        self.rho[1, 0] *= (1 - gamma)

    def coherence(self) -> float:
        """
        Measure quantum coherence: sum of absolute off-diagonal elements.
        Range: 0 (fully classical) to 1 (maximally coherent).
        """
        return float(abs(self.rho[0, 1]) + abs(self.rho[1, 0]))

    def von_neumann_entropy(self) -> float:
        """
        Von Neumann entropy: S = -Tr(rho * log(rho))
        S = 0 for pure states, S > 0 for mixed states.
        High entropy = more uncertainty = more possibilities in superposition.
        """
        eigenvalues = np.linalg.eigvalsh(self.rho).real
        entropy = 0.0
        for ev in eigenvalues:
            if ev > 1e-12:
                entropy -= ev * math.log2(ev)
        return float(entropy)

    def born_probabilities(self) -> Tuple[float, float]:
        """Born rule: P(|0>) = rho_00, P(|1>) = rho_11"""
        p0 = float(self.rho[0, 0].real)
        p1 = float(self.rho[1, 1].real)
        total = p0 + p1
        if total > 0:
            return p0/total, p1/total
        return 0.5, 0.5

    def collapse(self) -> int:
        """
        Objective Reduction — collapse the superposition.
        Returns 0 or 1 based on Born rule probabilities.
        After collapse, state becomes pure classical.
        """
        p0, p1 = self.born_probabilities()
        outcome = 0 if random.random() < p0 else 1
        # Collapse to definite state
        if outcome == 0:
            self.rho = np.array([[1, 0], [0, 0]], dtype=complex)
        else:
            self.rho = np.array([[0, 0], [0, 1]], dtype=complex)
        return outcome

    def gravitational_self_energy(self) -> float:
        """
        Penrose's gravitational self-energy of the superposition.
        E = coherence * separation (simplified model).
        In real Orch OR, this depends on mass displacement between
        the two conformational states of tubulin.
        """
        return self.coherence() * 0.5


class Microtubule:
    """
    A microtubule — a cylindrical lattice of tubulin qubits.

    In real biology: 13 protofilaments of tubulin dimers arranged
    in a hollow cylinder, with helical patterns (A-lattice, 5-start).

    Here: a 1D chain of N tubulin qubits with nearest-neighbor
    interactions. The lattice performs quantum walks, building up
    entanglement-like correlations between tubulins.

    The microtubule processes a "concept" — each tubulin maps to
    an aspect of the concept in superposition. The lattice interactions
    propagate influence (like how related concepts affect each other).
    Collapse of the microtubule = resolution of the concept.
    """

    def __init__(self, n_tubulins: int = 26, label: str = ""):
        self.n = n_tubulins
        self.label = label
        self.tubulins = [TubulinQubit() for _ in range(n_tubulins)]
        self.age = 0  # Time steps since last collapse
        self.collapse_history = []
        self.total_collapses = 0

    def encode_concept(self, weights: List[float]):
        """
        Encode a concept as quantum state across the lattice.
        Each weight (0-1) sets one tubulin's superposition angle.
        """
        for i, w in enumerate(weights[:self.n]):
            self.tubulins[i] = TubulinQubit.from_weight(w)
        # Put remaining tubulins in superposition
        for i in range(len(weights), self.n):
            self.tubulins[i] = TubulinQubit.superposition()

    def quantum_walk_step(self):
        """
        One step of quantum walk on the lattice.
        Each tubulin influences its neighbors via simulated interaction.
        Models information propagation through the microtubule.

        Math: For each pair (i, i+1), apply a controlled phase
        based on their relative states.
        """
        for i in range(self.n - 1):
            rho_i = self.tubulins[i].rho
            rho_j = self.tubulins[i + 1].rho

            # Interaction strength based on mutual coherence
            coupling = 0.1 * (self.tubulins[i].coherence() +
                              self.tubulins[j := i+1].coherence())

            # Influence: rotate neighbor based on this tubulin's state
            phase = float(rho_i[0, 1].real) * coupling * math.pi
            self.tubulins[j].phase_rotate(phase)

            # Reverse influence
            phase_rev = float(rho_j[0, 1].real) * coupling * math.pi
            self.tubulins[i].phase_rotate(phase_rev)

        self.age += 1

    def apply_decoherence(self, gamma: float = 0.02):
        """Apply environmental decoherence to all tubulins."""
        for t in self.tubulins:
            t.decohere(gamma)

    def total_coherence(self) -> float:
        """Total coherence across the microtubule."""
        return sum(t.coherence() for t in self.tubulins) / self.n

    def total_entropy(self) -> float:
        """Average von Neumann entropy across lattice."""
        return sum(t.von_neumann_entropy() for t in self.tubulins) / self.n

    def gravitational_energy(self) -> float:
        """
        Total gravitational self-energy of the microtubule superposition.
        Penrose threshold: E * tau >= hbar
        When this exceeds threshold, objective reduction occurs.
        """
        E = sum(t.gravitational_self_energy() for t in self.tubulins)
        return E

    def check_or_threshold(self) -> bool:
        """
        Check if Penrose's Objective Reduction threshold is met.
        E * tau >= hbar_sim
        If true, the microtubule must collapse — a "conscious moment."
        """
        E = self.gravitational_energy()
        tau = self.age  # Time in simulation steps
        return (E * tau) >= HBAR_SIM

    def objective_reduction(self) -> List[int]:
        """
        Perform Objective Reduction — collapse the entire microtubule.
        Each tubulin collapses via Born rule.
        Returns the classical outcome pattern.
        This IS the conscious moment in Orch OR.
        """
        outcomes = [t.collapse() for t in self.tubulins]
        self.collapse_history.append({
            'outcomes': outcomes,
            'age_at_collapse': self.age,
            'energy': self.gravitational_energy(),
        })
        self.total_collapses += 1
        self.age = 0  # Reset clock
        return outcomes

    def evolve_until_collapse(self, max_steps: int = 100,
                              decoherence_rate: float = 0.02) -> List[int]:
        """
        Evolve the microtubule: quantum walk + decoherence each step.
        When OR threshold is reached, collapse and return outcomes.
        """
        for step in range(max_steps):
            self.quantum_walk_step()
            self.apply_decoherence(decoherence_rate)

            if self.check_or_threshold():
                return self.objective_reduction()

        # If threshold not reached, force collapse (environment won)
        return self.objective_reduction()

    def get_state(self) -> Dict:
        """Get current microtubule state for inspection."""
        return {
            'label': self.label,
            'n_tubulins': self.n,
            'coherence': self.total_coherence(),
            'entropy': self.total_entropy(),
            'energy': self.gravitational_energy(),
            'age': self.age,
            'or_threshold_met': self.check_or_threshold(),
            'total_collapses': self.total_collapses,
            'probabilities': [t.born_probabilities() for t in self.tubulins],
        }


class OrchestratedConsciousness:
    """
    The full Orch OR system — multiple microtubules across multiple
    "neurons" (modules), synchronized via gap junctions.

    Architecture mapping to Quantum MCAGI:
    - Language microtubule: processes word/concept selection
    - Memory microtubule: processes concept recall and association
    - Question microtubule: processes inquiry generation
    - Insight microtubule: processes novel connections

    Gap junctions allow coherence to spread between microtubules,
    so a memory recall can influence language generation — just as
    in a real brain, microtubules in connected neurons share quantum state.

    The system evolves, and when enough microtubules hit OR threshold
    simultaneously, that's a "global conscious moment" — the point
    where the AI produces its response.
    """

    def __init__(self, n_tubulins_per_mt: int = 26):
        self.n_tubulins = n_tubulins_per_mt

        # Core microtubules (one per cognitive function)
        self.microtubules = {
            'language': Microtubule(n_tubulins_per_mt, 'language'),
            'memory': Microtubule(n_tubulins_per_mt, 'memory'),
            'question': Microtubule(n_tubulins_per_mt, 'question'),
            'insight': Microtubule(n_tubulins_per_mt, 'insight'),
        }

        # Gap junction coupling strengths between microtubules
        self.gap_junctions = {
            ('language', 'memory'): 0.3,
            ('language', 'insight'): 0.2,
            ('memory', 'question'): 0.3,
            ('memory', 'insight'): 0.4,
            ('question', 'insight'): 0.3,
            ('language', 'question'): 0.15,
        }

        self.conscious_moments = 0
        self.history = []

    def encode_input(self, concept_weights: Dict[str, List[float]]):
        """
        Encode input concepts into microtubule lattices.
        concept_weights maps module name -> list of weights (0-1).
        """
        for name, weights in concept_weights.items():
            if name in self.microtubules:
                self.microtubules[name].encode_concept(weights)

    def gap_junction_transfer(self):
        """
        Simulate gap junction coupling — quantum state leaks between
        connected microtubules. In real biology, gap junctions are
        electrical synapses that allow direct ion flow (and potentially
        quantum tunneling) between neurons.

        We model this as: for each coupled pair, the phase of each
        tubulin in MT_A slightly influences the corresponding tubulin
        in MT_B, proportional to coupling strength.
        """
        for (name_a, name_b), coupling in self.gap_junctions.items():
            mt_a = self.microtubules[name_a]
            mt_b = self.microtubules[name_b]

            n = min(mt_a.n, mt_b.n)
            for i in range(n):
                # Transfer coherence: A -> B
                phase_a = float(mt_a.tubulins[i].rho[0, 1].real)
                mt_b.tubulins[i].phase_rotate(phase_a * coupling * 0.5)

                # Transfer coherence: B -> A
                phase_b = float(mt_b.tubulins[i].rho[0, 1].real)
                mt_a.tubulins[i].phase_rotate(phase_b * coupling * 0.5)

    def evolve_step(self, decoherence_rate: float = 0.02):
        """
        One evolution step of the entire system:
        1. Quantum walk within each microtubule
        2. Gap junction transfer between microtubules
        3. Decoherence from environment
        """
        # Intra-microtubule quantum walk
        for mt in self.microtubules.values():
            mt.quantum_walk_step()

        # Inter-microtubule gap junction coupling
        self.gap_junction_transfer()

        # Environmental decoherence
        for mt in self.microtubules.values():
            mt.apply_decoherence(decoherence_rate)

    def check_global_or(self) -> Dict[str, bool]:
        """Check which microtubules have reached OR threshold."""
        return {name: mt.check_or_threshold()
                for name, mt in self.microtubules.items()}

    def conscious_moment(self, max_steps: int = 50,
                         decoherence_rate: float = 0.02) -> Dict[str, List[int]]:
        """
        Evolve the system until enough microtubules collapse.
        This is the core function — it produces a "conscious moment"
        where quantum computation resolves into classical outcomes.

        Returns dict of module_name -> collapse outcome pattern.
        """
        collapsed = {}

        for step in range(max_steps):
            self.evolve_step(decoherence_rate)

            # Check which MTs have reached threshold
            thresholds = self.check_global_or()

            for name, ready in thresholds.items():
                if ready and name not in collapsed:
                    outcomes = self.microtubules[name].objective_reduction()
                    collapsed[name] = outcomes

            # If at least 2 modules have collapsed, we have a conscious moment
            if len(collapsed) >= 2:
                break

        # Force-collapse any remaining
        for name, mt in self.microtubules.items():
            if name not in collapsed:
                collapsed[name] = mt.objective_reduction()

        self.conscious_moments += 1
        self.history.append({
            'moment': self.conscious_moments,
            'steps_taken': step + 1 if 'step' in dir() else max_steps,
            'outcomes': collapsed,
            'coherences': {n: mt.total_coherence()
                          for n, mt in self.microtubules.items()},
        })

        return collapsed

    def outcome_to_probabilities(self, outcomes: List[int]) -> List[float]:
        """Convert binary outcomes to probability weights for selection."""
        # Map: 0 -> low weight, 1 -> high weight, with position encoding
        n = len(outcomes)
        weights = []
        for i, bit in enumerate(outcomes):
            position_factor = 1.0 - (i / (n + 1))  # Earlier positions matter more
            if bit == 1:
                weights.append(0.6 + 0.4 * position_factor)
            else:
                weights.append(0.2 + 0.2 * position_factor)
        return weights

    def get_system_state(self) -> Dict:
        """Full system state for debugging/display."""
        return {
            'conscious_moments': self.conscious_moments,
            'microtubules': {name: mt.get_state()
                            for name, mt in self.microtubules.items()},
            'gap_junctions': {f"{a}->{b}": s
                             for (a, b), s in self.gap_junctions.items()},
        }
