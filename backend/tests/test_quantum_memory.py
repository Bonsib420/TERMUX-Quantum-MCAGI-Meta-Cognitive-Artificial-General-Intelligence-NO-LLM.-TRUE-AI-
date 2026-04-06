"""Tests for quantum_memory.py (QRAM integration)."""
import pytest
from quantum_memory import (
    ClassicalMemoryStore,
    _concept_to_bitstring,
    _bitstring_to_index,
    get_quantum_memory,
    reset_quantum_memory,
    PENNYLANE_QRAM_AVAILABLE,
)


# ── helpers ──────────────────────────────────────────────

class TestConceptBitstring:
    """Tests for the concept→bitstring mapping."""

    def test_deterministic(self):
        """Same concept always produces the same bitstring."""
        bs1 = _concept_to_bitstring("quantum", 8)
        bs2 = _concept_to_bitstring("quantum", 8)
        assert bs1 == bs2

    def test_correct_width(self):
        for width in (4, 8, 12, 16):
            bs = _concept_to_bitstring("test", width)
            assert len(bs) == width
            assert all(c in "01" for c in bs)

    def test_different_concepts_differ(self):
        """Different concepts should (almost certainly) produce different bits."""
        bs1 = _concept_to_bitstring("quantum", 16)
        bs2 = _concept_to_bitstring("philosophy", 16)
        assert bs1 != bs2

    def test_empty_string(self):
        bs = _concept_to_bitstring("", 8)
        assert len(bs) == 8

    def test_unicode_concept(self):
        bs = _concept_to_bitstring("意識", 8)
        assert len(bs) == 8


class TestBitstringToIndex:
    def test_roundtrip(self):
        assert _bitstring_to_index("0000") == 0
        assert _bitstring_to_index("0001") == 1
        assert _bitstring_to_index("1111") == 15

    def test_larger(self):
        assert _bitstring_to_index("11111111") == 255


# ── classical fallback ───────────────────────────────────

class TestClassicalMemoryStore:
    def setup_method(self):
        self.store = ClassicalMemoryStore(bit_width=8)

    def test_load_concepts(self):
        count = self.store.load_concepts(["quantum", "consciousness", "gravity"])
        assert count == 3

    def test_query_valid_address(self):
        self.store.load_concepts(["alpha", "beta", "gamma"])
        assert self.store.query(0) == "alpha"
        assert self.store.query(1) == "beta"
        assert self.store.query(2) == "gamma"

    def test_query_invalid_address(self):
        self.store.load_concepts(["alpha"])
        assert self.store.query(99) is None

    def test_superposition_query(self):
        self.store.load_concepts(["a", "b", "c"])
        results = self.store.superposition_query([0, 1])
        assert len(results) == 2
        names = [r[0] for r in results]
        assert "a" in names
        assert "b" in names
        # Uniform probabilities
        for _, p in results:
            assert abs(p - 0.5) < 1e-9

    def test_superposition_query_empty(self):
        results = self.store.superposition_query([0])
        assert results == []

    def test_superposition_query_invalid_addresses(self):
        self.store.load_concepts(["x"])
        results = self.store.superposition_query([99, 100])
        assert results == []

    def test_status(self):
        self.store.load_concepts(["a", "b"])
        s = self.store.status()
        assert s["backend"] == "classical_fallback"
        assert s["entries_loaded"] == 2
        assert s["bit_width"] == 8
        assert s["max_entries"] == 256
        assert s["qram_available"] is False

    def test_max_entries_respected(self):
        """Cannot exceed 2^bit_width entries."""
        store = ClassicalMemoryStore(bit_width=2)  # max 4
        names = [f"c{i}" for i in range(10)]
        count = store.load_concepts(names)
        assert count == 4  # capped at 2^2

    def test_load_empty_list(self):
        count = self.store.load_concepts([])
        assert count == 0

    def test_query_before_load(self):
        assert self.store.query(0) is None


# ── factory / singleton ──────────────────────────────────

class TestFactory:
    def setup_method(self):
        reset_quantum_memory()

    def teardown_method(self):
        reset_quantum_memory()

    def test_singleton_returns_same_instance(self):
        m1 = get_quantum_memory()
        m2 = get_quantum_memory()
        assert m1 is m2

    def test_reset_clears_singleton(self):
        m1 = get_quantum_memory()
        reset_quantum_memory()
        m2 = get_quantum_memory()
        assert m1 is not m2

    def test_factory_returns_store(self):
        store = get_quantum_memory()
        assert hasattr(store, "load_concepts")
        assert hasattr(store, "query")
        assert hasattr(store, "superposition_query")
        assert hasattr(store, "status")

    def test_status_has_required_keys(self):
        store = get_quantum_memory()
        s = store.status()
        for key in ("backend", "pennylane_available", "qram_available",
                     "entries_loaded", "bit_width", "max_entries"):
            assert key in s, f"Missing key: {key}"


# ── conditional quantum tests ────────────────────────────

@pytest.mark.skipif(
    not PENNYLANE_QRAM_AVAILABLE,
    reason="PennyLane QRAM templates not available",
)
class TestQuantumMemoryStore:
    """Only runs when PennyLane >= 0.44 with QRAM templates is installed."""

    def setup_method(self):
        reset_quantum_memory()

    def teardown_method(self):
        reset_quantum_memory()

    def test_quantum_store_created(self):
        from quantum_memory import QuantumMemoryStore
        store = QuantumMemoryStore(bit_width=4, strategy="select")
        assert "pennylane" in store.status()["backend"]

    def test_load_and_query(self):
        from quantum_memory import QuantumMemoryStore
        store = QuantumMemoryStore(bit_width=4, strategy="select")
        store.load_concepts(["alpha", "beta", "gamma", "delta"])
        assert store.query(0) == "alpha"
        assert store.query(3) == "delta"

    def test_superposition_query_returns_probs(self):
        from quantum_memory import QuantumMemoryStore
        store = QuantumMemoryStore(bit_width=3, strategy="select")
        store.load_concepts(["a", "b", "c", "d"])
        results = store.superposition_query([0, 1])
        assert len(results) == 2
        for name, prob in results:
            assert isinstance(prob, float)
            assert 0.0 <= prob <= 1.0

    def test_status_shows_templates(self):
        from quantum_memory import QuantumMemoryStore
        store = QuantumMemoryStore(bit_width=4)
        s = store.status()
        assert "templates" in s
        assert isinstance(s["templates"], dict)
