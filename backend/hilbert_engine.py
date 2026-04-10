"""
🌌 HILBERT ENGINE — Persistent Hilbert Space State Manager
==========================================================
Manages the Hilbert space vocabulary state across sessions.

The quantum_markov.py module defines HilbertSpace and HilbertSpaceWord
for in-memory word state representation. This engine:

1. Persists Hilbert space states to disk (save/load across restarts)
2. Provides a high-dimensional space (dim=128) for richer word states
3. Tracks statistics (total states, vocabulary growth over time)
4. Pre-seeds the space from Markov chain vocabulary for faster startup

The Hilbert space represents word meanings as quantum states in a
high-dimensional complex vector space. Context collapses superposition
into concrete meaning via Born-rule measurement.

Usage:
    engine = HilbertEngine(state_dir="~/.quantum-mcagi")
    engine.load()            # Load persisted state
    engine.seed_from_vocab(vocabulary_set)
    score = engine.similarity("quantum", "physics")
    engine.save()            # Persist to disk
"""

import os
import json
import math
import random
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger("quantum_ai")


class HilbertState:
    """
    A word's quantum state in the Hilbert space — a vector of
    complex amplitudes in dimension `dim`.

    |word⟩ = Σ_i α_i |i⟩  where Σ|α_i|² = 1
    """

    __slots__ = ('word', 'dimension', '_reals', '_imags')

    def __init__(self, word: str, dimension: int = 128, seed: int = None):
        self.word = word
        self.dimension = dimension
        self._reals: List[float] = []
        self._imags: List[float] = []

        if seed is None:
            # Deterministic seed from word content
            seed = int.from_bytes(
                word.lower().encode('utf-8')[:8].ljust(8, b'\x00'), 'big'
            ) % (2**31)
        self._initialize(seed)

    def _initialize(self, seed: int):
        """Initialize a normalized state vector from seed."""
        rng = random.Random(seed)
        raw_r = [rng.gauss(0, 1) for _ in range(self.dimension)]
        raw_i = [rng.gauss(0, 1) for _ in range(self.dimension)]

        # Normalize: Σ(r² + i²) = 1
        norm_sq = sum(r * r + i * i for r, i in zip(raw_r, raw_i))
        if norm_sq > 0:
            scale = 1.0 / math.sqrt(norm_sq)
            self._reals = [r * scale for r in raw_r]
            self._imags = [i * scale for i in raw_i]
        else:
            val = 1.0 / math.sqrt(self.dimension)
            self._reals = [val] * self.dimension
            self._imags = [0.0] * self.dimension

    def inner_product(self, other: 'HilbertState') -> complex:
        """⟨self|other⟩ — quantum overlap."""
        if self.dimension != other.dimension:
            return complex(0, 0)
        real_part = 0.0
        imag_part = 0.0
        for i in range(self.dimension):
            # ⟨a|b⟩ = Σ (a_i* · b_i)
            ar, ai = self._reals[i], -self._imags[i]  # conjugate of self
            br, bi = other._reals[i], other._imags[i]
            real_part += ar * br - ai * bi
            imag_part += ar * bi + ai * br
        return complex(real_part, imag_part)

    def overlap_probability(self, other: 'HilbertState') -> float:
        """|⟨self|other⟩|² — Born probability of semantic similarity."""
        ip = self.inner_product(other)
        return ip.real ** 2 + ip.imag ** 2

    def to_dict(self) -> Dict:
        """Serialize state for JSON storage."""
        return {
            "word": self.word,
            "dim": self.dimension,
            "r": self._reals,
            "i": self._imags,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'HilbertState':
        """Deserialize from JSON."""
        state = cls.__new__(cls)
        state.word = data["word"]
        state.dimension = data["dim"]
        state._reals = data["r"]
        state._imags = data["i"]
        return state


class HilbertEngine:
    """
    Persistent Hilbert space manager.

    Maintains a vocabulary of quantum word states and provides
    similarity, interference, and context resolution operations.
    """

    def __init__(self, state_dir: str = None, dimension: int = 128):
        self.dimension = dimension
        self._states: Dict[str, HilbertState] = {}
        self._state_dir = state_dir or os.path.expanduser("~/.quantum-mcagi")
        self._state_file = os.path.join(self._state_dir, "hilbert_space.json")
        self._loaded = False

    @property
    def size(self) -> int:
        """Number of word states in the space."""
        return len(self._states)

    def get_state(self, word: str) -> HilbertState:
        """Get or create the Hilbert state for a word."""
        w = word.lower().strip()
        if w not in self._states:
            self._states[w] = HilbertState(w, self.dimension)
        return self._states[w]

    def similarity(self, word_a: str, word_b: str) -> float:
        """Quantum overlap similarity between two words."""
        state_a = self.get_state(word_a)
        state_b = self.get_state(word_b)
        return state_a.overlap_probability(state_b)

    def interference_scores(self, candidates: List[str],
                            context: List[str]) -> Dict[str, float]:
        """
        Score candidates by quantum interference with context.
        Constructive interference boosts related words.
        """
        if not candidates:
            return {}

        context_states = [self.get_state(c) for c in context if c]
        if not context_states:
            return {c: 1.0 for c in candidates}

        scores = {}
        for word in candidates:
            cand_state = self.get_state(word)
            total = 0.0
            for ctx in context_states:
                ip = cand_state.inner_product(ctx)
                total += ip.real  # Real part = interference
            total /= len(context_states)
            scores[word] = max(0.01, 1.0 + total)

        return scores

    def seed_from_vocab(self, vocabulary: Set[str]) -> int:
        """
        Pre-seed Hilbert states from a vocabulary set.
        Returns count of new states created.
        """
        created = 0
        for word in vocabulary:
            w = word.lower().strip()
            if w and w not in self._states:
                self._states[w] = HilbertState(w, self.dimension)
                created += 1
        return created

    def save(self) -> bool:
        """Persist Hilbert space to disk."""
        try:
            os.makedirs(self._state_dir, exist_ok=True)
            data = {
                "dimension": self.dimension,
                "count": len(self._states),
                "states": {w: s.to_dict() for w, s in self._states.items()},
            }
            with open(self._state_file, 'w') as f:
                json.dump(data, f)
            logger.info(f"Hilbert space saved: {len(self._states)} states")
            return True
        except Exception as e:
            logger.error(f"Failed to save Hilbert space: {e}")
            return False

    def load(self) -> bool:
        """Load Hilbert space from disk."""
        if not os.path.exists(self._state_file):
            return False
        try:
            with open(self._state_file, 'r') as f:
                data = json.load(f)
            self.dimension = data.get("dimension", self.dimension)
            states_data = data.get("states", {})
            for word, state_dict in states_data.items():
                self._states[word] = HilbertState.from_dict(state_dict)
            self._loaded = True
            logger.info(
                f"Hilbert space loaded: {len(self._states)} states, dim={self.dimension}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to load Hilbert space: {e}")
            return False

    def get_status(self) -> Dict:
        """Return engine status."""
        return {
            "dimension": self.dimension,
            "states": len(self._states),
            "loaded_from_disk": self._loaded,
            "state_file": self._state_file,
        }


# Module-level singleton
_engine: Optional[HilbertEngine] = None


def get_hilbert_engine(state_dir: str = None,
                       dimension: int = 128) -> HilbertEngine:
    """Get or create the Hilbert engine singleton."""
    global _engine
    if _engine is None:
        _engine = HilbertEngine(state_dir=state_dir, dimension=dimension)
    return _engine
