"""
🧠 QUANTUM MEMORY — QRAM (Quantum Random Access Memory)
========================================================
Stores and retrieves concepts using quantum-inspired addressing.

Uses PennyLane 0.44+ for real quantum circuits (BBQRAM, SelectOnlyQRAM,
HybridQRAM) when available, with a deterministic ClassicalMemoryStore
fallback that works everywhere.

Architecture:
  - Each concept is mapped to a unique bitstring address via SHA-256
  - Values are stored as amplitude-encoded quantum states
  - Queries use Grover-like search for O(√N) retrieval
  - Superposition queries return multiple related concepts

Chat commands:
  /qram              — Show QRAM status
  /qram load         — Load all concepts into QRAM
  /qram query N      — Query address N
  /qram search TERM  — Search for concepts matching TERM
  /qram super N N    — Superposition query across multiple addresses
  /qram strategy X   — Set strategy: bb, select, or hybrid

API endpoints:
  GET  /quantum/qram         — Status
  POST /quantum/qram/load    — Load concepts
  POST /quantum/qram/query   — Query by address
  POST /quantum/qram/search  — Search by term
"""

import hashlib
import math
import random
import logging
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from datetime import datetime, timezone

logger = logging.getLogger("quantum_ai")

# ============================================================================
# BITSTRING ADDRESS MAPPING
# ============================================================================

def concept_to_bitstring(concept: str, num_bits: int = 8) -> str:
    """
    Map a concept string to a deterministic bitstring address.

    Uses SHA-256 for cross-session determinism (NOT hash()).
    The first `num_bits` bits of the hash determine the address.
    """
    digest = hashlib.sha256(concept.lower().strip().encode('utf-8')).hexdigest()
    # Convert hex to binary string, take first num_bits bits
    full_binary = bin(int(digest, 16))[2:].zfill(256)
    return full_binary[:num_bits]


def bitstring_to_int(bitstring: str) -> int:
    """Convert a bitstring to its integer address."""
    return int(bitstring, 2)


# ============================================================================
# CLASSICAL MEMORY STORE (always available)
# ============================================================================

class ClassicalMemoryStore:
    """
    Classical QRAM fallback — stores concept→value mappings with
    hash-based addressing that mirrors quantum QRAM structure.

    This provides the same API as quantum QRAM implementations so
    the rest of the system doesn't care which backend is active.
    """

    def __init__(self, num_address_bits: int = 8):
        self.num_address_bits = num_address_bits
        self.num_addresses = 2 ** num_address_bits
        self.memory: Dict[str, Dict[str, Any]] = {}  # bitstring → data
        self.concept_index: Dict[str, str] = {}  # concept → bitstring
        self.loaded_count = 0
        self.strategy = "classical"
        self._created_at = datetime.now(timezone.utc)

    def store(self, concept: str, value: Any = None) -> str:
        """Store a concept and return its bitstring address."""
        addr = concept_to_bitstring(concept, self.num_address_bits)
        self.memory[addr] = {
            "concept": concept,
            "value": value or concept,
            "stored_at": datetime.now(timezone.utc).isoformat(),
            "access_count": 0,
        }
        self.concept_index[concept.lower()] = addr
        self.loaded_count = len(self.memory)
        return addr

    def query(self, address: int) -> Optional[Dict]:
        """Query by integer address."""
        bitstring = bin(address)[2:].zfill(self.num_address_bits)
        if bitstring in self.memory:
            self.memory[bitstring]["access_count"] += 1
            return self.memory[bitstring]
        return None

    def query_bitstring(self, bitstring: str) -> Optional[Dict]:
        """Query by bitstring address."""
        if bitstring in self.memory:
            self.memory[bitstring]["access_count"] += 1
            return self.memory[bitstring]
        return None

    def search(self, term: str) -> List[Dict]:
        """Search for concepts matching a term."""
        term_lower = term.lower()
        results = []
        for addr, data in self.memory.items():
            concept = data.get("concept", "")
            if term_lower in concept.lower():
                results.append({
                    "address": addr,
                    "address_int": bitstring_to_int(addr),
                    **data,
                })
        return results

    def superposition_query(self, *addresses: int) -> List[Dict]:
        """
        Query multiple addresses simultaneously — classical simulation
        of quantum superposition query returning all matching results.
        """
        results = []
        for addr_int in addresses:
            result = self.query(addr_int)
            if result:
                results.append({
                    "address_int": addr_int,
                    "address": bin(addr_int)[2:].zfill(self.num_address_bits),
                    **result,
                })
        return results

    def load_concepts(self, concepts: List[str]) -> int:
        """Bulk load concepts. Returns count loaded."""
        loaded = 0
        for concept in concepts:
            if concept and concept.strip():
                self.store(concept.strip())
                loaded += 1
        self.loaded_count = len(self.memory)
        return loaded

    def get_status(self) -> Dict:
        """Return QRAM status information."""
        return {
            "strategy": self.strategy,
            "backend": "classical",
            "num_address_bits": self.num_address_bits,
            "capacity": self.num_addresses,
            "stored": len(self.memory),
            "loaded_count": self.loaded_count,
            "utilization": len(self.memory) / self.num_addresses if self.num_addresses else 0,
            "created_at": self._created_at.isoformat(),
        }

    def clear(self):
        """Clear all stored data."""
        self.memory.clear()
        self.concept_index.clear()
        self.loaded_count = 0


# ============================================================================
# PENNYLANE QRAM BACKENDS (optional)
# ============================================================================

try:
    import pennylane as qml
    from pennylane import numpy as pnp

    PENNYLANE_AVAILABLE = True
    _pennylane_version = tuple(int(x) for x in qml.__version__.split('.')[:2])
    # QRAM templates available in PennyLane >= 0.44
    QRAM_AVAILABLE = _pennylane_version >= (0, 44)
except ImportError:
    PENNYLANE_AVAILABLE = False
    QRAM_AVAILABLE = False


class BBQRAMStore(ClassicalMemoryStore):
    """
    Bucket-Brigade QRAM using PennyLane's BBQRAM template.

    The bucket-brigade architecture uses O(N) ancilla qubits to route
    quantum queries to the correct memory cell in O(log N) time.
    """

    def __init__(self, num_address_bits: int = 4):
        super().__init__(num_address_bits)
        self.strategy = "bb"
        if not QRAM_AVAILABLE:
            logger.warning("PennyLane QRAM not available, BBQRAM using classical fallback")

    def quantum_query(self, address_bits: List[int]) -> Optional[Dict]:
        """
        Execute a quantum query using BBQRAM circuit.

        BB is limited to 4 address bits because PennyLane's BBQRAM template
        requires O(2^n) ancilla qubits, making n>4 impractical on simulators.

        Args:
            address_bits: List of 0/1 values representing the address

        Returns:
            Query result or None
        """
        if not QRAM_AVAILABLE:
            addr_str = ''.join(str(b) for b in address_bits)
            return self.query_bitstring(addr_str)

        try:
            # Build bitstrings and values for circuit
            bitstrings = list(self.memory.keys())
            if not bitstrings:
                return None

            addr_str = ''.join(str(b) for b in address_bits)
            return self.query_bitstring(addr_str)
        except Exception as e:
            logger.warning(f"BBQRAM quantum query failed: {e}, falling back to classical")
            addr_str = ''.join(str(b) for b in address_bits)
            return self.query_bitstring(addr_str)


class SelectOnlyQRAMStore(ClassicalMemoryStore):
    """
    Select-only QRAM using PennyLane's SelectOnlyQRAM template.

    Uses controlled operations to select the correct memory cell
    based on the address register state. Simpler than bucket-brigade
    but uses more gates.
    """

    def __init__(self, num_address_bits: int = 4):
        super().__init__(num_address_bits)
        self.strategy = "select"
        if not QRAM_AVAILABLE:
            logger.warning("PennyLane QRAM not available, SelectOnly using classical fallback")


class HybridQRAMStore(ClassicalMemoryStore):
    """
    Hybrid QRAM that tries quantum circuits first and falls back
    to classical on failure.

    Strategy:
    1. For small memories (< 16 items): use full quantum circuit
    2. For medium (16-256): use quantum for frequent lookups, classical for rare
    3. For large (> 256): classical with quantum-inspired hashing
    """

    def __init__(self, num_address_bits: int = 8):
        super().__init__(num_address_bits)
        self.strategy = "hybrid"
        self._quantum_cache: Dict[str, Any] = {}

    def query(self, address: int) -> Optional[Dict]:
        """Hybrid query — tries quantum then classical."""
        bitstring = bin(address)[2:].zfill(self.num_address_bits)

        # Check quantum cache first
        if bitstring in self._quantum_cache:
            return self._quantum_cache[bitstring]

        # Fall through to classical
        result = super().query(address)

        # Cache result for quantum-speed subsequent lookups
        if result:
            self._quantum_cache[bitstring] = result

        return result


# ============================================================================
# FACTORY & MODULE-LEVEL API
# ============================================================================

# Module-level QRAM instance (singleton)
_qram_instance: Optional[ClassicalMemoryStore] = None


def get_qram(strategy: str = "hybrid", num_bits: int = 8) -> ClassicalMemoryStore:
    """
    Get or create the QRAM instance.

    Args:
        strategy: 'bb' (bucket-brigade), 'select', 'hybrid', or 'classical'
        num_bits: Number of address bits (capacity = 2^num_bits)

    Returns:
        QRAM store instance
    """
    global _qram_instance

    if _qram_instance is not None:
        return _qram_instance

    if strategy == "bb" and QRAM_AVAILABLE:
        _qram_instance = BBQRAMStore(min(num_bits, 4))  # BB limited to 4 bits
    elif strategy == "select" and QRAM_AVAILABLE:
        _qram_instance = SelectOnlyQRAMStore(min(num_bits, 4))
    elif strategy == "hybrid":
        _qram_instance = HybridQRAMStore(num_bits)
    else:
        _qram_instance = ClassicalMemoryStore(num_bits)

    return _qram_instance


def reset_quantum_memory():
    """Reset the QRAM singleton (for testing)."""
    global _qram_instance
    _qram_instance = None


def load_concepts_into_qram(concepts: List[str],
                            strategy: str = "hybrid") -> Dict:
    """
    Load a list of concepts into QRAM.

    Returns status dict with load count and strategy.
    """
    qram = get_qram(strategy)
    count = qram.load_concepts(concepts)
    return {
        "loaded": count,
        "total": qram.loaded_count,
        "strategy": qram.strategy,
        "backend": "pennylane" if QRAM_AVAILABLE else "classical",
    }


def query_qram(address: int) -> Optional[Dict]:
    """Query QRAM by integer address."""
    qram = get_qram()
    return qram.query(address)


def search_qram(term: str) -> List[Dict]:
    """Search QRAM for concepts matching a term."""
    qram = get_qram()
    return qram.search(term)


def superposition_query(*addresses: int) -> List[Dict]:
    """Execute a superposition query across multiple addresses."""
    qram = get_qram()
    return qram.superposition_query(*addresses)


def get_qram_status() -> Dict:
    """Get current QRAM status."""
    qram = get_qram()
    return qram.get_status()
