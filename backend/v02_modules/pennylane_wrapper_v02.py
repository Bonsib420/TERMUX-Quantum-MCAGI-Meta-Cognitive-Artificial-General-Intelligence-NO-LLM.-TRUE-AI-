"""Wrapper to make pennylane_quantum compatible with orch_or_engine.py"""
from pennylane_quantum_v02 import PennyLaneQuantum, PENNYLANE_AVAILABLE
class PennyLaneQuantumEngine:
    """Wrapper that provides the interface orch_or_engine.py expects."""
    
    def __init__(self):
        self.quantum = PennyLaneQuantum() if PENNYLANE_AVAILABLE else None
    
    def encode_and_evolve(self, concepts=None, steps=3):
        if not self.quantum:
            return {'evolution': {}, 'collapses': {}, 'orchestration': 0.5}
        evolution = {}
        for i, c in enumerate((concepts or [])[:4]):
            evolution[c] = {
                'coherence': self.quantum.measure_coherence(),
                'entropy': __import__('random').uniform(0.1, 0.9)
            }
        return {'evolution': evolution, 'collapses': {}, 'orchestration': 0.5}
    
    def get_collapse_weights(self, num_candidates=8):
        if not self.quantum:
            import random
            w = [random.random() for _ in range(num_candidates)]
            s = sum(w)
            return [x/s for x in w]
        return self.quantum.get_collapse_weights(num_candidates)
    
    def get_coherence(self, system=None):
        return self.quantum.measure_coherence() if self.quantum else 0.5
    
    def get_entropy(self, system=None):
        if not self.quantum:
            return 0.5
        return 1.0 - self.quantum.measure_coherence()
    
    def get_temperature(self):
        if not self.quantum:
            return 1.0
        return 1.0 - self.quantum.measure_coherence()
    
    def get_status(self):
        if not self.quantum:
            return {'status': 'INACTIVE', 'pennylane': False}
        return {'status': 'ACTIVE', 'pennylane': True}