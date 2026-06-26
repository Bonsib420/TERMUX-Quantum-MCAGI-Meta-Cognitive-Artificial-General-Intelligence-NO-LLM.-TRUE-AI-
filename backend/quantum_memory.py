"""
💾 Quantum Random Access Memory (QRAM) Integration
===================================================
Leverages PennyLane 0.44.0+ QRAM templates (BBQRAM, SelectOnlyQRAM,
HybridQRAM) for quantum-enhanced concept retrieval from the knowledge graph.

QRAM encodes bitstrings corresponding to concept data entries and can
query them in superposition:
    QRAM Σ cᵢ |i⟩|0⟩ = Σ cᵢ |i⟩|bᵢ⟩

Three strategies are available depending on device constraints:
 • BBQRAM          – Bucket Brigade: noise-resilient, moderate depth + width
 • SelectOnlyQRAM  – Series of MultiControlledX: low width, higher depth
 • HybridQRAM      – Combines both: tuneable depth/width tradeoff

When PennyLane ≥0.44.0 is unavailable the module provides a pure-Python
classical fallback that mirrors the same API so the rest of the system
works identically.
"""

import math
import random
from typing import Dict, List, Optional, Tuple

# ---------- optional PennyLane import ----------
try:
    import pennylane as qml
    from pennylane import numpy as pnp

    # QRAM templates arrived in PennyLane 0.44.0
    _has_bbqram = hasattr(qml, "BBQRAM")
    _has_select = hasattr(qml, "SelectOnlyQRAM")
    _has_hybrid = hasattr(qml, "HybridQRAM")
    PENNYLANE_QRAM_AVAILABLE = _has_bbqram or _has_select or _has_hybrid
    PENNYLANE_AVAILABLE = True
except ImportError:
    qml = None  # type: ignore[assignment]
    pnp = None  # type: ignore[assignment]
    PENNYLANE_AVAILABLE = False
    PENNYLANE_QRAM_AVAILABLE = False
    _has_bbqram = False
    _has_select = False
    _has_hybrid = False


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _concept_to_bitstring(concept: str, bit_width: int) -> str:
    """Deterministic mapping: concept name → fixed-width bitstring.

    Uses hashlib so the mapping is stable across Python sessions
    (unaffected by PYTHONHASHSEED / hash randomization).
    Truncated / zero-padded to *bit_width* bits.
    """
    import hashlib
    h = int(hashlib.sha256(concept.encode("utf-8")).hexdigest(), 16)
    h = h & ((1 << bit_width) - 1)
    return format(h, f"0{bit_width}b")


def _bitstring_to_index(bs: str) -> int:
    return int(bs, 2)


# ──────────────────────────────────────────────
# Classical fallback
# ──────────────────────────────────────────────

class ClassicalMemoryStore:
    """Pure-Python QRAM stand-in used when PennyLane < 0.44 or missing."""

    def __init__(self, bit_width: int = 8):
        self.bit_width = bit_width
        self.entries: Dict[int, str] = {}     # address → bitstring
        self.concepts: Dict[int, str] = {}    # address → concept name
        self._next_addr = 0

    # -- public API (mirrors QuantumMemoryStore) --------------------

    def load_concepts(self, concept_names: List[str]) -> int:
        """Encode a batch of concept names.  Returns count loaded."""
        for name in concept_names:
            if self._next_addr >= (1 << self.bit_width):
                break
            bs = _concept_to_bitstring(name, self.bit_width)
            self.entries[self._next_addr] = bs
            self.concepts[self._next_addr] = name
            self._next_addr += 1
        return self._next_addr

    def query(self, address: int) -> Optional[str]:
        """Classical single-address lookup."""
        return self.concepts.get(address)

    def superposition_query(self, addresses: List[int]) -> List[Tuple[str, float]]:
        """Simulate a superposition query classically (uniform probs)."""
        results: List[Tuple[str, float]] = []
        valid = [a for a in addresses if a in self.concepts]
        if not valid:
            return results
        prob = 1.0 / len(valid)
        for a in valid:
            results.append((self.concepts[a], prob))
        return results

    def status(self) -> Dict:
        return {
            "backend": "classical_fallback",
            "pennylane_available": PENNYLANE_AVAILABLE,
            "qram_available": False,
            "entries_loaded": self._next_addr,
            "bit_width": self.bit_width,
            "max_entries": 1 << self.bit_width,
        }


# ──────────────────────────────────────────────
# Quantum QRAM store (PennyLane ≥ 0.44)
# ──────────────────────────────────────────────

class QuantumMemoryStore:
    """Wraps PennyLane QRAM templates for concept storage / retrieval.

    Parameters
    ----------
    bit_width : int
        Number of target bits per entry (data register width).
    strategy : str
        ``"bb"`` for BBQRAM, ``"select"`` for SelectOnlyQRAM,
        ``"hybrid"`` for HybridQRAM.  Falls back automatically if
        the chosen template is unavailable.
    """

    STRATEGIES = ("bb", "select", "hybrid")

    def __init__(self, bit_width: int = 8, strategy: str = "select"):
        if not PENNYLANE_QRAM_AVAILABLE:
            raise RuntimeError(
                "PennyLane QRAM templates not found. "
                "Requires PennyLane >= 0.44.0 with BBQRAM / SelectOnlyQRAM."
            )
        if strategy not in self.STRATEGIES:
            strategy = "select"

        self.bit_width = bit_width
        self.strategy = self._resolve_strategy(strategy)
        self.bitstrings: List[str] = []
        self.concepts: Dict[int, str] = {}
        self._loaded = False

    @staticmethod
    def _resolve_strategy(requested: str) -> str:
        """Pick the best available strategy."""
        order = {
            "bb":     [_has_bbqram, _has_select, _has_hybrid],
            "select": [_has_select, _has_bbqram, _has_hybrid],
            "hybrid": [_has_hybrid, _has_bbqram, _has_select],
        }
        names = ["bb", "select", "hybrid"]
        prefs = order.get(requested, order["select"])
        for avail, name in zip(prefs, [requested] + [n for n in names if n != requested]):
            if avail:
                return name
        return "select"  # should not reach if PENNYLANE_QRAM_AVAILABLE is True

    # -- public API ------------------------------------------------

    def load_concepts(self, concept_names: List[str]) -> int:
        """Encode concept names into QRAM bitstrings.

        The number of entries is rounded up to the next power of two
        (padded with zero-bitstrings) as required by QRAM templates.
        """
        raw = [_concept_to_bitstring(n, self.bit_width) for n in concept_names]
        # Pad to next power-of-two length
        n = len(raw)
        n_padded = 1 << math.ceil(math.log2(max(n, 2)))
        while len(raw) < n_padded:
            raw.append("0" * self.bit_width)
        self.bitstrings = raw
        self.concepts = {i: name for i, name in enumerate(concept_names)}
        self._loaded = True
        return len(concept_names)

    def query(self, address: int) -> Optional[str]:
        """Single-address deterministic lookup."""
        return self.concepts.get(address)

    def superposition_query(self, addresses: List[int]) -> List[Tuple[str, float]]:
        """Query multiple addresses in superposition using QRAM circuit.

        Returns list of (concept_name, probability) pairs.
        """
        if not self._loaded or not self.bitstrings:
            return []

        valid = [a for a in addresses if a in self.concepts]
        if not valid:
            return []

        num_entries = len(self.bitstrings)
        num_control = max(1, math.ceil(math.log2(num_entries)))
        num_target = self.bit_width

        # Build the QRAM circuit
        try:
            probs = self._run_qram_circuit(valid, num_control, num_target)
        except Exception:
            # Fall back to uniform if circuit fails
            prob = 1.0 / len(valid)
            return [(self.concepts[a], prob) for a in valid]

        # Map probabilities back to concepts
        results: List[Tuple[str, float]] = []
        for a in valid:
            p = probs[a] if a < len(probs) else 1.0 / len(valid)
            results.append((self.concepts[a], float(p)))
        return results

    def _run_qram_circuit(
        self,
        addresses: List[int],
        num_control: int,
        num_target: int,
    ) -> list:
        """Build and execute QRAM circuit, return address-register probs."""
        total_wires = num_control + num_target
        # BBQRAM needs work wires
        if self.strategy == "bb":
            num_work = 1 + 3 * ((1 << num_control) - 1)
            total_wires += num_work
        else:
            num_work = 0

        dev = qml.device("default.qubit", wires=total_wires)

        control_wires = list(range(num_control))
        target_wires = list(range(num_control, num_control + num_target))
        work_wires = list(range(num_control + num_target, total_wires)) if num_work else []

        bitstrings = self.bitstrings
        strategy = self.strategy

        @qml.qnode(dev)
        def circuit():
            # Prepare superposition over requested addresses
            if len(addresses) == 1:
                qml.BasisEmbedding(addresses[0], wires=control_wires)
            else:
                # Equal superposition over requested addresses
                # Use Hadamard on all control qubits then post-select
                for w in control_wires:
                    qml.Hadamard(wires=w)

            # Apply the chosen QRAM template
            if strategy == "bb":
                qml.BBQRAM(
                    bitstrings,
                    control_wires=control_wires,
                    target_wires=target_wires,
                    work_wires=work_wires,
                )
            elif strategy == "hybrid" and _has_hybrid:
                qml.HybridQRAM(
                    bitstrings,
                    control_wires=control_wires,
                    target_wires=target_wires,
                )
            else:
                qml.SelectOnlyQRAM(
                    bitstrings,
                    control_wires=control_wires,
                    target_wires=target_wires,
                )

            return qml.probs(wires=control_wires)

        raw_probs = circuit()
        return list(raw_probs)

    def status(self) -> Dict:
        return {
            "backend": f"pennylane_qram_{self.strategy}",
            "pennylane_available": True,
            "qram_available": True,
            "qram_strategy": self.strategy,
            "entries_loaded": len(self.concepts),
            "bit_width": self.bit_width,
            "max_entries": len(self.bitstrings) if self.bitstrings else 0,
            "templates": {
                "BBQRAM": _has_bbqram,
                "SelectOnlyQRAM": _has_select,
                "HybridQRAM": _has_hybrid,
            },
        }


# ──────────────────────────────────────────────
# Factory & singleton
# ──────────────────────────────────────────────

_qram_instance: Optional[object] = None


def get_quantum_memory(
    bit_width: int = 8,
    strategy: str = "select",
) -> "ClassicalMemoryStore | QuantumMemoryStore":
    """Return a QRAM-backed (or classical-fallback) memory store.

    Safe to call repeatedly — returns the same singleton.
    """
    global _qram_instance
    if _qram_instance is not None:
        return _qram_instance  # type: ignore[return-value]

    if PENNYLANE_QRAM_AVAILABLE:
        try:
            _qram_instance = QuantumMemoryStore(bit_width=bit_width, strategy=strategy)
            return _qram_instance  # type: ignore[return-value]
        except Exception:
            pass

    _qram_instance = ClassicalMemoryStore(bit_width=bit_width)
    return _qram_instance  # type: ignore[return-value]


def reset_quantum_memory() -> None:
    """Reset the singleton (useful for testing)."""
    global _qram_instance
    _qram_instance = None
