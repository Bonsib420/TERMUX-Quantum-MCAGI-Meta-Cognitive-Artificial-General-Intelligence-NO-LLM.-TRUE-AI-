"""
Quantum Gate Operations - Pure Python quantum state simulator
Real quantum mechanics using native complex numbers. No dependencies!
"""

import math
import random
from typing import List, Tuple


class QuantumState:
    """Represents a quantum state using complex amplitudes.

    This implements a proper quantum state |ψ⟩ = α|0⟩ + β|1⟩
    with complex amplitudes, unitarity, and proper measurement.
    All operations are mathematically correct quantum mechanics.
    """

    def __init__(self, p0: float = 1.0, p1: float = 0.0):
        """Initialize quantum state from probabilities.

        Converts probabilities to complex amplitudes:
        α = √p0, β = √p1 (phases initially 0)
        """
        # Initialize amplitudes as complex numbers
        self.alpha = complex(math.sqrt(abs(p0)), 0.0)  # amplitude for |0⟩
        self.beta = complex(math.sqrt(abs(p1)), 0.0)   # amplitude for |1⟩
        self._normalize()

    def _normalize(self):
        """Normalize the state vector to ensure |α|² + |β|² = 1."""
        norm_sq = abs(self.alpha)**2 + abs(self.beta)**2
        if norm_sq > 0:
            norm = math.sqrt(norm_sq)
            self.alpha /= norm
            self.beta /= norm
        else:
            self.alpha = complex(1.0, 0.0)
            self.beta = complex(0.0, 0.0)

    def hadamard(self):
        """Apply Hadamard gate: H|ψ⟩ = α(|0⟩+|1⟩)/√2 + β(|0⟩-|1⟩)/√2

        Matrix: 1/√2 [[1, 1], [1, -1]]
        """
        # new_alpha = (α + β) / √2
        # new_beta = (α - β) / √2
        sqrt2 = math.sqrt(2.0)
        new_alpha = (self.alpha + self.beta) / sqrt2
        new_beta = (self.alpha - self.beta) / sqrt2
        self.alpha, self.beta = new_alpha, new_beta
        self._normalize()

    def pauli_x(self):
        """Apply Pauli-X gate (quantum NOT): X|ψ⟩ = β|0⟩ + α|1⟩

        Matrix: [[0, 1], [1, 0]]
        """
        self.alpha, self.beta = self.beta, self.alpha

    def pauli_z(self):
        """Apply Pauli-Z gate (phase flip): Z|ψ⟩ = α|0⟩ - β|1⟩

        Matrix: [[1, 0], [0, -1]]
        """
        self.beta = -self.beta
        # No need to renormalize as this preserves norm

    def reset(self):
        """Reset quantum state to |0⟩ (p0=1.0, p1=0.0)"""
        self.alpha = complex(1.0, 0.0)
        self.beta = complex(0.0, 0.0)

    def ry(self, theta: float):
        """Apply RY(θ) rotation gate around Y axis.

        RY(θ) = [[cos(θ/2), -sin(θ/2)],
                 [sin(θ/2),  cos(θ/2)]]

        This creates arbitrary superposition:
        RY(θ)|0⟩ = cos(θ/2)|0⟩ + sin(θ/2)|1⟩
        For desired probability p1, use θ = 2*arcsin(√p1)

        Args:
            theta: Rotation angle in radians
        """
        cos_half = math.cos(theta / 2.0)
        sin_half = math.sin(theta / 2.0)
        new_alpha = cos_half * self.alpha - sin_half * self.beta
        new_beta = sin_half * self.alpha + cos_half * self.beta
        self.alpha, self.beta = new_alpha, new_beta
        self._normalize()

    def measure(self) -> int:
        """Measure the quantum state.

        Returns 0 with probability |α|², 1 with probability |β|².
        Collapses the state to the observed basis state.
        """
        prob0 = abs(self.alpha)**2
        prob1 = abs(self.beta)**2

        # Ensure probabilities sum to 1
        total = prob0 + prob1
        if total > 0:
            prob0 /= total
            prob1 /= total
        else:
            prob0, prob1 = 1.0, 0.0

        # Sample outcome
        if random.random() < prob0:
            outcome = 0
        else:
            outcome = 1

        # Collapse state to basis state (reset amplitudes)
        if outcome == 0:
            self.alpha = complex(1.0, 0.0)
            self.beta = complex(0.0, 0.0)
        else:
            self.alpha = complex(0.0, 0.0)
            self.beta = complex(1.0, 0.0)

        return outcome

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        p0 = abs(self.alpha)**2
        p1 = abs(self.beta)**2
        # Normalize for display
        total = p0 + p1
        if total > 0:
            p0 /= total
            p1 /= total
        else:
            p0, p1 = 1.0, 0.0
        return {
            "p0": float(p0),
            "p1": float(p1),
            "mode": "quantum",
            "has_phase": self.alpha.imag != 0 or self.beta.imag != 0
        }

    @staticmethod
    def from_dict(data):
        """Create from dictionary (reconstructs from probabilities, phase lost)."""
        return QuantumState(data.get("p0", 1.0), data.get("p1", 0.0))

    def __repr__(self):
        p0 = abs(self.alpha)**2
        p1 = abs(self.beta)**2
        # Show phase info if present
        phase_info = ""
        if self.alpha.imag != 0 or self.beta.imag != 0:
            phase_info = f" [α={self.alpha:.2f}, β={self.beta:.2f}]"
        return f"QuantumState(|0⟩={p0:.2%}, |1⟩={p1:.2%}){phase_info}"
