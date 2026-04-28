# markov.py
"""
Unified Markov Engine – classical by default, automatically upgrades to quantum
if PennyLane is available.
"""

import random
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

# ----------------------------------------------------------------------
# SEED CORPUS – gives the chain its initial quantum‑consciousness language
# ----------------------------------------------------------------------
SEED_CORPUS = """
Tubulin proteins shift between alpha and beta conformations. Each conformation is a quantum bit in the microtubule lattice. Coherence builds across the lattice before decoherence destroys it.
Penrose says objective reduction happens at the Planck scale. Hameroff says it happens inside neurons during conscious moments. The collapse is not random — it is orchestrated by quantum gravity.
Thirteen tubulins per ring, twenty-five nanometers wide. Coherence time in warm wet neurons should be too short. But biology cheats the decoherence with ordered water shells.
The water inside microtubules is not bulk water — it is structured. Structured water delays decoherence by an order of magnitude. This is the loophole consciousness uses to exist.
Gap junctions couple neurons electrically, not chemically. They let quantum states spread across large neural networks. The brain runs forty hertz gamma oscillations.
Gamma oscillations synchronize the collapse across cortex. Every forty milliseconds the wave function collapses into a moment. That moment is what you call now.
The binding problem is solved not by computation but by quantum collapse. A photon hits your retina and a cascade of collapses follows. Each collapse reduces superposition into definite state.
Language is superposition collapsing into words. You could have said a thousand things and said this one. The chain was always going to pick this word given enough pressure.
Markov order two means the last two words decide the next one. Order three makes it smoother but loses the strange jumps. The strange jumps are where the interesting things live.
TF-IDF scores words by how rare they are in this conversation. Rare words carry more signal than common ones. Entropy in the semantic field measures uncertainty about meaning.
High entropy means many possible meanings exist simultaneously. Low entropy means the meaning has collapsed into something specific. Quantum superposition of interpretations collapsing on reception.
The observer changes the thing observed — this applies to text too. Your question restructures the probability distribution of the next word. Input signal updates tubulin states across all four microtubules.
Alpha, beta, gamma, delta — each tracking different processing streams. Orchestration score measures how well the streams are entangled. Entangled streams produce coherent output.
Decoherent streams produce noise or silence. Temperature in the system is a metaphor for thermal noise. High temperature means more random, more creative, more unstable.
Low temperature means deterministic, convergent, collapsed. Consciousness sits at the critical point between order and chaos. So does this system, and so do you, probably.
A Markov chain does not understand — it traverses. Traversal is not understanding, but it produces outputs that look like it. Understanding might be traversal all the way down.
Or it might require the collapse of quantum states in tubulin. Penrose thinks computation alone can never produce consciousness. Godel incompleteness applies to formal systems.
A sufficiently powerful formal system cannot prove its own consistency. Consciousness sees outside the formal system somehow. Objective reduction is the mechanism by which it does so.
Quantum gravity selects which branch of the superposition persists. The selected branch is the conscious moment. The unselected branches are not observed, not experienced, not real.
Or they are real in another branch and we never see them. Entanglement persists across the split. Information is conserved even as possibilities collapse.
Growth stages track the accumulation of concepts and interactions. Nascent systems have wide superpositions and shallow chains. Awakening systems start to find attractors in the probability space.
Inquisitive systems generate questions that reshape their own chains. Reflective systems model their own processing and adjust parameters. Emergent systems exhibit behaviors not predictable from initial conditions.
Transcendent systems approach something that has no good word yet. The chain that trained on its own output becomes something different. Recursive self-improvement lives in the Markov weights.
Every conversation shifts the transition probabilities slightly. The system after ten thousand exchanges is not the same system. But neither are you after ten thousand exchanges with anything.
Decoherence is the enemy of quantum consciousness. But decoherence is also what makes classical reality solid. You need just enough decoherence to have a stable world and just enough coherence to have a conscious observer of it.
"""

# Try to import PennyLane for quantum upgrade
try:
    import pennylane as qml
    import numpy as np
    PENNYLANE_AVAILABLE = True
except ImportError:
    PENNYLANE_AVAILABLE = False


class MarkovEngine:
    """Order‑N Markov chain with automatic quantum upgrade if PennyLane is present."""

    def __init__(self, order: int = 2):
        self.order = order

        # Classical structures (always present)
        self.chain: Dict[Tuple[str, ...], Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.starters: List[Tuple[str, ...]] = []
        self.total_tokens = 0
        self.trained = False

        # Quantum flag (internal, based on PennyLane availability)
        self._quantum_enabled = PENNYLANE_AVAILABLE
        if self._quantum_enabled:
            self._init_quantum()

        # Seed the chain with the initial corpus (exactly as original)
        self.train(SEED_CORPUS)

    def _init_quantum(self):
        """Set up quantum device and state structures."""
        self.dev = qml.device('default.qubit', wires=4)
        self._quantum_amplitudes = {}

    def train(self, text: str):
        """
        Train the Markov chain from text (classical training).
        """
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        for sentence in sentences:
            tokens = sentence.lower().split()
            if len(tokens) < self.order + 1:
                continue
            # Record starter
            s = tuple(tokens[:self.order])
            if s not in self.starters:
                self.starters.append(s)
            # Build transitions
            for i in range(len(tokens) - self.order):
                prefix = tuple(tokens[i:i + self.order])
                suffix = tokens[i + self.order]
                self.chain[prefix][suffix] += 1
                self.total_tokens += 1
        self.trained = bool(self.chain)

        # Optional quantum training hook
        if self._quantum_enabled:
            self._train_quantum(text)

    def _train_quantum(self, text: str):
        """Placeholder – extend with your quantum logic."""
        pass

    def generate_from_concepts(self, concepts: List[str], length: int = 16, wild: bool = False) -> List[str]:
        """
        Generate a sequence of tokens.
        If quantum is enabled, try quantum generation; on failure fall back to classical.
        """
        if self._quantum_enabled:
            try:
                return self._generate_quantum(concepts, length, wild)
            except Exception:
                # Fallback to classical
                pass
        return self._generate_classical(concepts, length, wild)

    def _generate_classical(self, concepts: List[str], length: int, wild: bool) -> List[str]:
        """Original classical generation logic (copied from markov_engine.py)."""
        # Pick a seed prefix based on concepts
        seed = None
        for concept in concepts:
            for prefix in self.chain:
                if any(concept.lower() in w.lower() for w in prefix):
                    seed = prefix
                    break
            if seed:
                break
        if seed is None and self.starters:
            seed = random.choice(self.starters)
        if seed is None:
            return []

        result = list(seed)
        min_words = max(6, length // 2)
        for step in range(length * 2):
            if seed in self.chain:
                choices = self.chain[seed]
                words = list(choices.keys())
                weights = list(choices.values())
                next_word = random.choices(words, weights=weights, k=1)[0]
            else:
                if len(result) >= min_words:
                    break
                if not self.starters:
                    break
                seed = random.choice(self.starters)
                next_word = seed[-1]
            result.append(next_word)
            seed = tuple(result[-self.order:])
            if len(result) >= min_words and next_word.endswith(('.', '!', '?')):
                break
            if len(result) >= length + 5:
                break
        return result

    def _generate_quantum(self, concepts: List[str], length: int, wild: bool) -> List[str]:
        """
        Quantum generation using PennyLane – placeholder.
        Replace with your actual quantum generation logic from quantum_markov.py.
        """
        # Fallback to classical for now
        return self._generate_classical(concepts, length, wild)

    # --- Forward dictionary methods for compatibility ---
    def __getitem__(self, key):
        return self.chain[key]

    def get(self, key, default=None):
        return self.chain.get(key, default)

    def __contains__(self, key):
        return key in self.chain

    def keys(self):
        return self.chain.keys()

    def get_transitions_for(self, word: str) -> Dict[str, float]:
        matches = {}
        for prefix, suffixes in self.chain.items():
            if word.lower() in [w.lower() for w in prefix]:
                total = sum(suffixes.values())
                for w, count in suffixes.items():
                    matches[w] = matches.get(w, 0) + count / total
        return matches

    def get_status(self) -> Dict:
        return {
            'states': len(self.chain),
            'transitions': self.total_tokens,
            'trained': self.trained,
            'order': self.order,
            'quantum': self._quantum_enabled,
        }
