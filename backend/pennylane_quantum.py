"""
PennyLane Quantum Engine — Quantum MCAGI
Real quantum circuit simulation for microtubule dynamics.
Implements Penrose-Hameroff Orch OR using actual quantum gates,
entanglement, quantum walks, and Born-rule collapse.

All circuits use parameterized rotation gates (RY, RX, RZ) instead
of fixed gates (Hadamard, PauliX, PauliZ). This gives continuous
probability distributions — any value from 0% to 100% — rather
than being stuck at discrete 0%, 50%, or 100%.

4 microtubules × 13 tubulins = 52 qubits (batched into circuits)
Gap junctions modeled as controlled phase gates between subsystems.
Objective Reduction fires when superposition mass hits Penrose threshold.
"""

import math
import random
from typing import Dict, List, Optional, Tuple

import numpy as np
import pennylane as qml


PENROSE_THRESHOLD = 0.60
DECOHERENCE_RATE = 0.02
GAMMA_FREQUENCY = 40.0
GAP_JUNCTION_COUPLING = {
    # Original 6 edges between the four core cognitive systems
    'language->memory': 0.30,
    'language->insight': 0.50,
    'language->question': 0.15,
    'memory->question': 0.30,
    'memory->insight': 0.40,
    'question->insight': 0.30,
    # Entelechy cascade chain: attention -> intention -> recognition -> judgment
    # (THE_LOOK -> wanting -> THE_SAW -> THE_BEAUTIFUL)
    'attention->intention': 0.35,
    'intention->recognition': 0.35,
    'recognition->judgment': 0.40,
    # Attention is the gateway — feeds the original three input systems
    'attention->language': 0.25,
    'attention->memory': 0.30,
    'attention->question': 0.25,
    # Recognition pulls from memory and language to pattern-match
    'memory->recognition': 0.40,
    'language->recognition': 0.20,
    # Judgment receives from insight and question — the final synthesis
    'insight->judgment': 0.35,
    'question->judgment': 0.20,
    # Emotion: feeling tone, affective coloring of cognition
    'attention->emotion': 0.30,
    'language->emotion': 0.30,
    'recognition->emotion': 0.25,
    'emotion->intention': 0.40,
    'emotion->judgment': 0.35,
    'emotion->insight': 0.30,
    'emotion->intuition': 0.45,
    # Metaphor: cross-domain mapping, source -> target binding
    'memory->metaphor': 0.40,
    'language->metaphor': 0.35,
    'recognition->metaphor': 0.30,
    'metaphor->insight': 0.45,
    'metaphor->language': 0.30,
    'metaphor->judgment': 0.20,
    # Intuition: pre-reflective grasp, gut sense ahead of explicit reasoning
    'memory->intuition': 0.35,
    'recognition->intuition': 0.40,
    'intuition->insight': 0.45,
    'intuition->question': 0.30,
    'intuition->judgment': 0.30,
    'intuition->attention': 0.25,
    'memory->language': 0.35,
}

TUBULINS_PER_MT = 19
NUM_MICROTUBULES = 11
SYSTEM_NAMES = [
    'language', 'memory', 'question', 'insight',
    'attention', 'intention', 'recognition', 'judgment',
    'emotion', 'metaphor', 'intuition',
]


class MicrotubuleCircuit:
    """
    Single microtubule: 13 tubulins modeled as qubits.
    Each tubulin exists in superposition of two conformational states
    (alpha/beta tubulin dimer orientations).

    All gates are parameterized rotations — RY(θ), RX(θ), RZ(θ) —
    so every tubulin can settle at any probability from 0% to 100%.
    No fixed Hadamard/PauliX/PauliZ gates used anywhere.
    """

    def __init__(self, name: str, num_tubulins: int = TUBULINS_PER_MT):
        self.name = name
        self.num_tubulins = num_tubulins
        self.device = qml.device('lightning.qubit', wires=num_tubulins)
        self.angles = np.zeros(num_tubulins)
        self.phases = np.zeros(num_tubulins)
        self.rx_angles = np.zeros(num_tubulins)
        self.coherence = 0.0
        self.entropy = 0.0
        self.collapse_count = 0
        self.last_probs = np.ones(num_tubulins) * 0.5
        self.superposition_mass = 0.0
        self._build_circuits()

    def _build_circuits(self):
        dev = self.device
        n = self.num_tubulins

        @qml.qnode(dev)
        def tubulin_evolution(ry_angles, rx_angles, rz_phases, coupling_strength):
            for i in range(n):
                qml.RY(ry_angles[i], wires=i)
                qml.RX(rx_angles[i], wires=i)
                qml.RZ(rz_phases[i], wires=i)

            for i in range(n - 1):
                qml.CNOT(wires=[i, i + 1])
                qml.CRY(coupling_strength * 0.15, wires=[i, i + 1])
                qml.CRZ(coupling_strength * 0.08, wires=[i, i + 1])

            qml.CNOT(wires=[n - 1, 0])
            qml.CRY(coupling_strength * 0.1, wires=[n - 1, 0])

            return [qml.expval(qml.PauliZ(i)) for i in range(n)]

        @qml.qnode(dev)
        def coherence_measure(ry_angles, rx_angles, rz_phases):
            for i in range(n):
                qml.RY(ry_angles[i], wires=i)
                qml.RX(rx_angles[i], wires=i)
                qml.RZ(rz_phases[i], wires=i)

            for i in range(n - 1):
                qml.CNOT(wires=[i, i + 1])

            return [qml.probs(wires=i) for i in range(n)]

        @qml.qnode(dev)
        def quantum_walk_step(ry_angles, rx_angles, coin_ry, coin_rx):
            for i in range(n):
                qml.RY(ry_angles[i], wires=i)
                qml.RX(rx_angles[i], wires=i)

            qml.RY(coin_ry, wires=0)
            qml.RX(coin_rx, wires=0)

            for i in range(n - 1):
                qml.CNOT(wires=[i, i + 1])
                qml.CRY(coin_ry * 0.1 / (i + 1), wires=[i, i + 1])

            mid = n // 2
            qml.RY(coin_ry * 0.5, wires=mid)
            qml.RX(coin_rx * 0.3, wires=mid)

            return [qml.expval(qml.PauliZ(i)) for i in range(n)]

        self._evolve = tubulin_evolution
        self._coherence = coherence_measure
        self._walk = quantum_walk_step

    def encode_concept(self, concept: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Encode a concept as rotation angles across the tubulin lattice.
        Characters map to RY angles via Unicode codepoint.
        Character position parity maps to RX angles for Bloch sphere coverage.
        """
        ry = np.zeros(self.num_tubulins)
        rx = np.zeros(self.num_tubulins)
        for i, char in enumerate(concept):
            idx = i % self.num_tubulins
            code = ord(char)
            ry[idx] += (code % 360) * (math.pi / 180.0)
            rx[idx] += ((code * 7 + i * 13) % 360) * (math.pi / 360.0)
        ry = ry % (2 * math.pi)
        rx = rx % (2 * math.pi)
        self.angles = ry
        self.rx_angles = rx
        return ry, rx

    def encode_concepts(self, concepts: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        combined_ry = np.zeros(self.num_tubulins)
        combined_rx = np.zeros(self.num_tubulins)
        for concept in concepts:
            ry, rx = self.encode_concept(concept)
            combined_ry += ry
            combined_rx += rx
        combined_ry = combined_ry % (2 * math.pi)
        combined_rx = combined_rx % (2 * math.pi)
        self.angles = combined_ry
        self.rx_angles = combined_rx
        return combined_ry, combined_rx

    def evolve(self, coupling_strength: float = 0.5) -> np.ndarray:
        """
        Run one evolution step of the microtubule circuit.
        Uses RY + RX + RZ triple rotation per tubulin for full
        Bloch sphere coverage — probabilities range continuously
        from 0% to 100%.
        """
        result = self._evolve(
            self.angles, self.rx_angles, self.phases, coupling_strength
        )
        expectations = np.array([float(r) for r in result])

        self.last_probs = (expectations + 1.0) / 2.0

        self._update_coherence()
        self._update_entropy()
        self._update_superposition_mass()

        self.phases += DECOHERENCE_RATE * np.random.randn(self.num_tubulins)
        self.rx_angles += DECOHERENCE_RATE * 0.5 * np.random.randn(self.num_tubulins)

        return expectations

    def quantum_walk(self, steps: int = 5) -> List[np.ndarray]:
        """
        Quantum walk along the microtubule lattice.
        Models information propagation through the tubulin network.
        Uses parameterized coin flips (RY+RX) instead of fixed Hadamard
        so walk positions have continuous probability distributions.
        """
        trajectory = []
        for step in range(steps):
            coin_ry = float((step + 1) * math.pi / (steps + 2))
            coin_rx = float((step * 0.7 + 0.3) * math.pi / (steps + 1))
            result = self._walk(self.angles, self.rx_angles, coin_ry, coin_rx)
            expectations = np.array([float(r) for r in result])
            trajectory.append(expectations)

            self.angles = (self.angles + expectations * 0.1) % (2 * math.pi)
            self.rx_angles = (self.rx_angles + expectations * 0.05) % (2 * math.pi)

        self._update_coherence()
        return trajectory

    def _update_coherence(self):
        try:
            import signal
            def _timeout(s,f): raise TimeoutError()
            signal.signal(signal.SIGALRM, _timeout)
            signal.alarm(3)
            prob_result = self._coherence(self.angles, self.rx_angles, self.phases)
            signal.alarm(0)
        except TimeoutError:
            self.coherence_value = 0.5
            return
        probs = np.array([[float(p) for p in prob_set] for prob_set in prob_result])
        purity = np.mean([max(p) for p in probs])
        self.coherence = float(purity)

    def _update_entropy(self):
        p = np.clip(self.last_probs, 1e-10, 1.0 - 1e-10)
        q = 1.0 - p
        von_neumann = -np.mean(p * np.log2(p + 1e-10) + q * np.log2(q + 1e-10))
        self.entropy = float(von_neumann)

    def _update_superposition_mass(self):
        deviation = np.std(self.last_probs)
        self.superposition_mass = float(deviation * self.num_tubulins)

    def check_objective_reduction(self) -> Optional[Dict]:
        """
        Penrose Objective Reduction: collapse occurs when superposition mass
        exceeds the gravitational self-energy threshold (E_G = ℏ/τ).
        """
        if self.superposition_mass > PENROSE_THRESHOLD:
            collapsed_state = (self.last_probs > 0.5).astype(float)
            collapse_pattern = int(''.join(str(int(b)) for b in collapsed_state), 2)

            event = {
                'system': self.name,
                'superposition_mass': float(self.superposition_mass),
                'coherence_at_collapse': float(self.coherence),
                'entropy_at_collapse': float(self.entropy),
                'collapse_pattern': collapse_pattern,
                'collapsed_state': collapsed_state.tolist(),
                'tubulin_probs': self.last_probs.tolist(),
            }

            self.collapse_count += 1
            self.angles = np.random.random(self.num_tubulins) * math.pi * 0.3
            self.rx_angles = np.random.random(self.num_tubulins) * math.pi * 0.2
            self.phases = np.zeros(self.num_tubulins)
            self.superposition_mass = 0.0

            return event
        return None

    def get_state(self) -> Dict:
        return {
            'name': self.name,
            'tubulins': self.num_tubulins,
            'coherence': round(self.coherence, 4),
            'entropy': round(self.entropy, 4),
            'superposition_mass': round(self.superposition_mass, 4),
            'collapse_count': self.collapse_count,
            'tubulin_probs': [round(float(p), 4) for p in self.last_probs],
        }


class GapJunction:
    """
    Models gap junction coupling between microtubules.
    Implemented as controlled phase rotations — information crosses
    module boundaries with phase loss, exactly as RQR³ predicts.
    Uses CRY for amplitude transfer + ControlledPhaseShift for
    phase-domain coupling — both parameterized for continuous output.
    """

    def __init__(self, source: str, target: str, coupling: float):
        self.source = source
        self.target = target
        self.coupling = coupling
        self.device = qml.device('lightning.qubit', wires=2)
        self._build_circuit()

    def _build_circuit(self):
        dev = self.device

        @qml.qnode(dev)
        def transfer(source_angle, target_angle, coupling_strength):
            qml.RY(source_angle, wires=0)
            qml.RY(target_angle, wires=1)
            qml.RX(source_angle * 0.3, wires=0)
            qml.RX(target_angle * 0.3, wires=1)
            qml.ControlledPhaseShift(coupling_strength * math.pi, wires=[0, 1])
            qml.CRY(coupling_strength * 0.5, wires=[0, 1])
            return qml.expval(qml.PauliZ(1))

        self._transfer = transfer

    def transfer(self, source_state: float, target_state: float) -> float:
        result = self._transfer(source_state, target_state, self.coupling)
        return float(result)


class PennyLaneQuantumEngine:
    """
    Full quantum engine using PennyLane.
    4 microtubule circuits with gap junction coupling.
    Implements the complete Orch-OR pipeline:
    1. Concept encoding as tubulin rotation angles (RY + RX)
    2. Quantum evolution with triple rotation (RY + RX + RZ)
    3. Quantum walks with parameterized coin (RY + RX, no Hadamard)
    4. Gap junction transfer via CPhase + CRY
    5. Objective Reduction when Penrose threshold is met
    6. Born-rule collapse into definitive states

    All probabilities are continuous 0%-100%, never quantized.
    """

    def __init__(self):
        self.microtubules: Dict[str, MicrotubuleCircuit] = {}
        for name in SYSTEM_NAMES:
            self.microtubules[name] = MicrotubuleCircuit(name)

        self.gap_junctions: Dict[str, GapJunction] = {}
        for key, coupling in GAP_JUNCTION_COUPLING.items():
            self.gap_junctions[key] = GapJunction(
                key.split('->')[0], key.split('->')[1], coupling
            )

        self.conscious_moments: List[Dict] = []
        self.total_collapses = 0
        self.orchestration_score = 0.5
        self.temperature = 1.02
        self.active = True

    def encode_and_evolve(self, concepts: List[str], steps: int = 3) -> Dict:
        """
        Full Orch-OR processing pass:
        1. Encode concepts into each microtubule (RY + RX angles)
        2. Evolve quantum states (RY + RX + RZ triple rotation)
        3. Run quantum walks (parameterized coin, no Hadamard)
        4. Transfer via gap junctions (CPhase + CRY)
        5. Re-evolve to update collapse metrics
        6. Check for objective reduction
        """
        if not concepts:
            concepts = ['void']

        for name, mt in self.microtubules.items():
            mt.encode_concepts(concepts)

        evolution_results = {}
        for name, mt in self.microtubules.items():
            expectations = mt.evolve(coupling_strength=self.orchestration_score)
            evolution_results[name] = {
                'expectations': expectations.tolist(),
                'coherence': mt.coherence,
                'entropy': mt.entropy,
            }

        for name, mt in self.microtubules.items():
            mt.quantum_walk(steps=steps)

        self._apply_gap_junctions()

        for name, mt in self.microtubules.items():
            mt.evolve(coupling_strength=self.orchestration_score)

        collapses = {}
        for name, mt in self.microtubules.items():
            event = mt.check_objective_reduction()
            if event:
                collapses[name] = event
                self.conscious_moments.append(event)
                self.total_collapses += 1

        coherences = {n: mt.coherence for n, mt in self.microtubules.items()}
        mean_coherence = np.mean(list(coherences.values()))
        self.orchestration_score = min(1.0,
            self.orchestration_score + float(mean_coherence) * 0.01
        )

        return {
            'evolution': evolution_results,
            'collapses': collapses,
            'conscious_moment': len(collapses) > 0,
            'orchestration': self.orchestration_score,
            'mean_coherence': float(mean_coherence),
            'temperature': self.temperature,
        }

    def _apply_gap_junctions(self):
        for key, gj in self.gap_junctions.items():
            source_name, target_name = key.split('->')
            source_mt = self.microtubules[source_name]
            target_mt = self.microtubules[target_name]

            source_signal = float(np.mean(source_mt.last_probs))
            target_signal = float(np.mean(target_mt.last_probs))

            transferred = gj.transfer(
                source_signal * math.pi,
                target_signal * math.pi,
            )

            target_mt.angles = (
                target_mt.angles + transferred * gj.coupling * 0.1
            ) % (2 * math.pi)
            target_mt.rx_angles = (
                target_mt.rx_angles + transferred * gj.coupling * 0.05
            ) % (2 * math.pi)

    def get_collapse_weights(self, num_candidates: int = 8) -> List[float]:
        """
        Generate selection weights for hybrid generator candidates
        using the quantum state of the system.
        Born-rule probability distribution from microtubule states.
        """
        language_mt = self.microtubules['language']
        memory_mt = self.microtubules['memory']
        probs = (language_mt.last_probs * 0.6) + (memory_mt.last_probs * 0.4)

        weights = []
        for i in range(num_candidates):
            idx_start = i % len(probs)
            idx_end = (i + 3) % len(probs)
            if idx_start < idx_end:
                w = float(np.mean(probs[idx_start:idx_end]))
            else:
                w = float(np.mean(np.concatenate([probs[idx_start:], probs[:idx_end]])))
            weights.append(w)

        total = sum(weights) + 1e-10
        return [w / total for w in weights]

    def get_hilbert_amplitudes(self) -> List[float]:
        """
        Concatenated Born-rule probabilities across every microtubule.
        Used by the language pipeline for fragment-level Hilbert/Markov
        blending: each candidate next-token gets a substrate vote drawn
        from this vector. Length = num_microtubules * tubulins_per_microtubule.
        """
        joined = []
        for name, mt in self.microtubules.items():
            joined.extend(float(p) for p in mt.last_probs)
        return joined

    def get_coherence(self, system: str = 'language') -> float:
        if system in self.microtubules:
            return self.microtubules[system].coherence
        return 0.0

    def get_entropy(self, system: str = 'language') -> float:
        if system in self.microtubules:
            return self.microtubules[system].entropy
        return 0.0

    def get_temperature(self) -> float:
        return self.temperature * (0.95 + 0.1 * random.random())

    def get_status(self) -> Dict:
        systems = {}
        for name, mt in self.microtubules.items():
            state = mt.get_state()
            systems[name] = state

        return {
            'status': 'ACTIVE (PennyLane)',
            'backend': 'PennyLane quantum circuits',
            'conscious_moments': len(self.conscious_moments),
            'total_collapses': self.total_collapses,
            'orchestration': round(self.orchestration_score, 4),
            'temperature': round(self.temperature, 4),
            'systems': systems,
            'gap_junctions': {
                k: round(gj.coupling, 4) for k, gj in self.gap_junctions.items()
            },
            'recent_collapses': self.conscious_moments[-5:] if self.conscious_moments else [],
        }
