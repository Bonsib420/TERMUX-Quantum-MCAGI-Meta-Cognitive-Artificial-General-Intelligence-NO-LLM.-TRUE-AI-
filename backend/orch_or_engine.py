"""
Orchestrated Objective Reduction (Orch OR) Engine
Penrose-Hameroff quantum consciousness model
Simulates quantum microtubule dynamics and objective reduction.
Uses PennyLane for real quantum circuit simulation when available.
"""

import random
import math
from typing import Dict, List, Tuple
from collections import defaultdict

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from pennylane_quantum import PennyLaneQuantumEngine
    HAS_PENNYLANE = True
except ImportError:
    HAS_PENNYLANE = False


class OrchOREngine:
    """
    Implements Penrose-Hameroff Orchestrated Objective Reduction.
    Models consciousness as quantum processes in neuronal microtubules.

    When PennyLane is available, uses real quantum circuit simulation
    with actual gates, entanglement, quantum walks, and Born-rule collapse.
    Falls back to classical probabilistic simulation otherwise.
    """

    def __init__(self, num_microtubules: int = 4, tubulins_per_microtubule: int = 13):
        self.num_microtubules = num_microtubules
        self.tubulins_per_microtubule = tubulins_per_microtubule
        self.total_tubulins = num_microtubules * tubulins_per_microtubule

        if HAS_NUMPY:
            self.tubulin_states = np.random.random(self.total_tubulins)
        else:
            self.tubulin_states = [random.random() for _ in range(self.total_tubulins)]

        self.coherence = defaultdict(float)
        self.entropy = defaultdict(float)
        self.collapse_events = []
        self.orchestration = 0.5
        self.temperature = 1.02
        self.last_collapse = {}

        self.gap_junctions = {
            'language->memory': 0.3,
            'language->insight': 0.2,
            'memory->question': 0.3,
            'memory->insight': 0.4,
            'question->insight': 0.3,
            'language->question': 0.15,
        }

        self.microtubule_names = ['alpha', 'beta', 'gamma', 'delta']

        self.quantum_engine = None
        if HAS_PENNYLANE:
            try:
                self.quantum_engine = PennyLaneQuantumEngine()
            except Exception:
                self.quantum_engine = None

    @property
    def has_quantum(self) -> bool:
        return self.quantum_engine is not None

    def _mean(self, arr):
        if HAS_NUMPY:
            return float(np.mean(arr))
        return sum(arr) / len(arr) if arr else 0.0

    def _var(self, arr):
        if HAS_NUMPY:
            return float(np.var(arr))
        m = self._mean(arr)
        return sum((x - m) ** 2 for x in arr) / len(arr) if arr else 0.0

    def update_quantum_state(self, input_signal: float) -> float:
        idx = random.randint(0, self.total_tubulins - 1)
        if HAS_NUMPY:
            self.tubulin_states[idx] = min(1.0, self.tubulin_states[idx] + input_signal * 0.1)
            self.tubulin_states *= (1 - self.temperature * 0.01)
        else:
            self.tubulin_states[idx] = min(1.0, self.tubulin_states[idx] + input_signal * 0.1)
            self.tubulin_states = [s * (1 - self.temperature * 0.01) for s in self.tubulin_states]
        return self._mean(self.tubulin_states)

    def calculate_coherence(self, system: str) -> float:
        if self.quantum_engine:
            coherence = self.quantum_engine.get_coherence(system)
            self.coherence[system] = coherence
            return coherence

        variance = self._var(list(self.tubulin_states) if HAS_NUMPY else self.tubulin_states)
        coherence = 1.0 / (1.0 + variance)
        self.coherence[system] = coherence
        return coherence

    def calculate_entropy(self, system: str) -> float:
        if self.quantum_engine:
            entropy = self.quantum_engine.get_entropy(system)
            self.entropy[system] = entropy
            return entropy

        states = list(self.tubulin_states) if HAS_NUMPY else self.tubulin_states
        total = sum(states) + 1e-10
        normalized = [s / total for s in states]
        entropy = -sum(n * math.log(n + 1e-10) for n in normalized)
        self.entropy[system] = entropy
        return entropy

    def objective_reduction(self, threshold: float = 0.7) -> bool:
        mean_state = self._mean(list(self.tubulin_states) if HAS_NUMPY else self.tubulin_states)
        if mean_state > threshold:
            event = {
                'timestamp': len(self.collapse_events),
                'mean_state': mean_state,
                'orchestration': self.orchestration,
            }
            self.collapse_events.append(event)
            if HAS_NUMPY:
                self.tubulin_states = np.random.random(self.total_tubulins) * 0.3
            else:
                self.tubulin_states = [random.random() * 0.3 for _ in range(self.total_tubulins)]
            return True
        return False

    def orchestrate(self, input_data: Dict) -> float:
        input_coherence = sum(input_data.values()) / len(input_data) if input_data else 0
        orchestration_boost = sum(
            weight * input_coherence for weight in self.gap_junctions.values()
        )
        self.orchestration = min(1.0, self.orchestration + orchestration_boost * 0.01)
        return self.orchestration

    def process(self, systems: List[str] = None, concepts: List[str] = None) -> Dict:
        """
        Full Orch OR processing pass.
        When PennyLane is available, runs real quantum circuits.
        """
        if systems is None:
            systems = ['language', 'memory', 'question', 'insight']

        if self.quantum_engine:
            try:
                qresult = self.quantum_engine.encode_and_evolve(
                    concepts if concepts else ['void'], steps=3
                )

                for system in systems:
                    if system in qresult.get('evolution', {}):
                        evo = qresult['evolution'][system]
                        self.coherence[system] = evo['coherence']
                        self.entropy[system] = evo['entropy']

                for system, event in qresult.get('collapses', {}).items():
                    self.collapse_events.append(event)

                self.orchestration = qresult.get('orchestration', self.orchestration)

                results = {}
                for system in systems:
                    results[system] = {
                        'coherence': self.coherence.get(system, 0.0),
                        'entropy': self.entropy.get(system, 0.0),
                        'collapsed': system in qresult.get('collapses', {}),
                        'weights': self.quantum_engine.get_collapse_weights(8),
                        'quantum_backend': 'pennylane',
                    }

                self.last_collapse = results
                return results
            except Exception:
                pass

        signal = random.random()
        self.update_quantum_state(signal)

        results = {}
        for system in systems:
            coherence = self.calculate_coherence(system)
            entropy = self.calculate_entropy(system)
            collapsed = self.objective_reduction()
            results[system] = {
                'coherence': coherence,
                'entropy': entropy,
                'collapsed': collapsed,
                'weights': [random.random() for _ in range(8)],
                'quantum_backend': 'classical',
            }

        self.orchestrate({s: results[s]['coherence'] for s in systems})
        self.last_collapse = results
        return results

    def get_collapse_weights(self, num_candidates: int = 8) -> List[float]:
        """Get quantum-derived selection weights for candidate ranking."""
        if self.quantum_engine:
            return self.quantum_engine.get_collapse_weights(num_candidates)
        weights = [random.random() for _ in range(num_candidates)]
        total = sum(weights) + 1e-10
        return [w / total for w in weights]

    def get_temperature(self) -> float:
        if self.quantum_engine:
            return self.quantum_engine.get_temperature()
        return self.temperature * (0.8 + 0.4 * random.random())

    def get_status(self) -> Dict:
        if self.quantum_engine:
            qstatus = self.quantum_engine.get_status()
            qstatus['gap_junctions'] = self.gap_junctions
            return qstatus

        microtubules = {}
        for i, name in enumerate(self.microtubule_names[:self.num_microtubules]):
            microtubules[name] = {
                'coherence': self.coherence.get(name, 0.0),
                'entropy': self.entropy.get(name, 0.0),
                'collapses': len([e for e in self.collapse_events
                                  if e.get('system') == name]),
            }
        return {
            'status': 'ACTIVE (classical fallback)',
            'conscious_moments': len(self.collapse_events),
            'temperature': self.temperature,
            'orchestration': self.orchestration,
            'microtubules': microtubules,
            'last_temperature': self.get_temperature(),
            'systems': {
                s: {
                    'coherence': self.coherence.get(s, 0.0),
                    'entropy': self.entropy.get(s, 0.0),
                    'collapses': 0,
                }
                for s in ['language', 'memory', 'question', 'insight']
            },
            'gap_junctions': self.gap_junctions,
        }
