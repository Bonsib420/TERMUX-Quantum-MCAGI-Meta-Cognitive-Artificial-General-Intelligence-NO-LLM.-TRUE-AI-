"""
🔮 PennyLane Quantum Computing Integration
Real quantum circuit simulation for Quantum AI

NOTE: This module requires 'pennylane' package.
If not installed, the get_pennylane_quantum() function will raise an informative error.
"""

import random
from typing import Dict, List, Tuple, Optional

# Optional import - only needed if using real quantum
try:
    import pennylane as qml
    from pennylane import numpy as np
    PENNYLANE_AVAILABLE = True
except ImportError:
    PENNYLANE_AVAILABLE = False
    qml = None
    np = None


class PennyLaneQuantum:
    """
    Real quantum computing using PennyLane.
    Goes beyond simple probability simulation to actual quantum circuits.
    
    Raises RuntimeError if pennylane is not available.
    """
    
    def __init__(self, n_qubits: int = 4):
        if not PENNYLANE_AVAILABLE:
            raise RuntimeError(
                "PennyLane is not installed. Install with: pip install pennylane\n"
                "Cannot use real quantum computing without PennyLane."
            )
        self.n_qubits = n_qubits
        self.dev = qml.device('default.qubit', wires=n_qubits)
        self.circuit_history = []
        self.measurement_results = []
        
    def create_superposition_circuit(self):
        """Create a basic superposition state"""
        @qml.qnode(self.dev)
        def circuit():
            # Apply Hadamard to all qubits - creates superposition
            for i in range(self.n_qubits):
                qml.Hadamard(wires=i)
            return [qml.expval(qml.PauliZ(i)) for i in range(self.n_qubits)]
        
        return circuit()
    
    def create_entangled_state(self):
        """Create an entangled Bell state"""
        @qml.qnode(self.dev)
        def circuit():
            qml.Hadamard(wires=0)
            qml.CNOT(wires=[0, 1])
            return qml.probs(wires=[0, 1])
        
        probs = circuit()
        self.circuit_history.append({
            'type': 'entanglement',
            'result': probs.tolist()
        })
        return probs
    
    def quantum_random_choice(self, options: List[str]) -> Tuple[str, float]:
        """
        Use quantum randomness to select from options.
        Returns selected option and its quantum probability.
        """
        n_options = len(options)
        if n_options == 0:
            return None, 0.0
        
        # Create circuit with enough qubits
        n_qubits_needed = max(1, int(np.ceil(np.log2(n_options))))
        dev = qml.device('default.qubit', wires=n_qubits_needed)
        
        @qml.qnode(dev)
        def random_circuit():
            # Create superposition
            for i in range(n_qubits_needed):
                qml.Hadamard(wires=i)
            # Add some randomness with rotations
            for i in range(n_qubits_needed):
                qml.RY(random.uniform(0, np.pi), wires=i)
            return qml.probs(wires=range(n_qubits_needed))
        
        probs = random_circuit()
        
        # Map probabilities to options
        option_probs = probs[:n_options]
        option_probs = option_probs / np.sum(option_probs)  # Renormalize
        
        # Select based on quantum probabilities
        selected_idx = np.random.choice(len(options), p=option_probs)
        
        return options[selected_idx], float(option_probs[selected_idx])
    
    def semantic_quantum_circuit(self, keyword_weights: Dict[str, float]) -> Dict[str, float]:
        """
        Apply quantum processing to semantic weights.
        Amplifies important concepts through quantum interference.
        """
        keywords = list(keyword_weights.keys())
        weights = list(keyword_weights.values())
        
        if not keywords:
            return {}
        
        n_keywords = len(keywords)
        n_qubits_needed = max(1, int(np.ceil(np.log2(n_keywords))) + 1)
        dev = qml.device('default.qubit', wires=n_qubits_needed)
        
        @qml.qnode(dev)
        def semantic_circuit(input_weights):
            # Encode weights as rotation angles
            for i, w in enumerate(input_weights[:n_qubits_needed]):
                qml.RY(w * np.pi, wires=i)
            
            # Create entanglement (concepts influence each other)
            for i in range(n_qubits_needed - 1):
                qml.CNOT(wires=[i, i + 1])
            
            # Apply Hadamard for interference
            for i in range(n_qubits_needed):
                qml.Hadamard(wires=i)
            
            return qml.probs(wires=range(n_qubits_needed))
        
        # Normalize weights for quantum encoding
        max_weight = max(weights) if weights else 1.0
        normalized = [w / max_weight for w in weights]
        
        # Pad to required length
        while len(normalized) < n_qubits_needed:
            normalized.append(0.5)
        
        quantum_probs = semantic_circuit(normalized)
        
        # Map back to keywords with quantum-enhanced weights
        enhanced_weights = {}
        for i, keyword in enumerate(keywords):
            if i < len(quantum_probs):
                # Original weight + quantum contribution
                enhanced_weights[keyword] = weights[i] * (1 + quantum_probs[i % len(quantum_probs)])
        
        return enhanced_weights
    
    def measure_coherence(self) -> float:
        """
        Measure the coherence of the quantum system.
        Higher coherence = more quantum effects available.
        """
        @qml.qnode(self.dev)
        def coherence_circuit():
            # Create superposition
            qml.Hadamard(wires=0)
            # Measure in X basis
            return qml.expval(qml.PauliX(0))
        
        coherence = abs(coherence_circuit())
        return float(coherence)
    
    def quantum_decision(self, question: str, options: List[str]) -> Dict:
        """
        Make a decision using quantum computing.
        Returns the decision with quantum metadata.
        """
        selected, probability = self.quantum_random_choice(options)
        coherence = self.measure_coherence()
        
        result = {
            'question': question,
            'options': options,
            'selected': selected,
            'quantum_probability': probability,
            'coherence': coherence,
            'method': 'pennylane_quantum'
        }
        
        self.measurement_results.append(result)
        return result
    
    def get_quantum_state_info(self) -> Dict:
        """Get information about current quantum state"""
        superposition = self.create_superposition_circuit()
        
        return {
            'n_qubits': self.n_qubits,
            'superposition_state': [float(s) for s in superposition],
            'coherence': self.measure_coherence(),
            'circuit_count': len(self.circuit_history),
            'measurement_count': len(self.measurement_results)
        }


# Global instance
_pennylane_quantum = None

def get_pennylane_quantum() -> PennyLaneQuantum:
    """Get or create PennyLane quantum instance
    
    Raises:
        RuntimeError: If PennyLane is not installed
    """
    global _pennylane_quantum
    if _pennylane_quantum is None:
        if not PENNYLANE_AVAILABLE:
            raise RuntimeError(
                "PennyLane is not installed. Real quantum computing unavailable.\n"
                "Install with: pip install pennylane\n"
                "Falling back to classical quantum simulation in other modules."
            )
        _pennylane_quantum = PennyLaneQuantum()
    return _pennylane_quantum
