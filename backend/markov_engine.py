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
        """
        Initialize the MarkovEngine with the specified Markov order and seed its internal state from the built-in corpus.
        
        Parameters:
            order (int): Number of tokens in the prefix (Markov order).
        
        Notes:
            - Initializes these attributes:
                - chain: mapping from prefix tuples to suffix count dicts.
                - starters: list of observed starting prefixes.
                - total_tokens: total number of recorded transitions.
                - trained: whether the chain contains any transitions.
                - _quantum_enabled: True if PennyLane is available; when True, _init_quantum() is called.
            - Immediately trains the classical chain using the module-level SEED_CORPUS, so the instance may be trained on construction.
        """
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
        """
        Initialize quantum runtime resources used by the engine.
        
        Creates a PennyLane default.qubit device assigned to `self.dev` and initializes
        `self._quantum_amplitudes` as an empty mapping for storing learned quantum state
        amplitudes.
        """
        self.dev = qml.device('default.qubit', wires=4)
        self._quantum_amplitudes = {}

    def train(self, text: str):
        """
        Train the Markov chain using the provided text corpus.
        
        Parameters:
            text (str): Raw text to learn from. Sentences are split on sentence-ending punctuation (., !, ?) followed by whitespace; each sentence is lowercased and tokenized on whitespace. Sentences shorter than (order + 1) tokens are ignored.
        
        Description:
            Updates the engine's internal transition table and related state: records starter prefixes, increments transition counts in `self.chain`, updates `self.total_tokens`, and sets `self.trained`. If quantum support is enabled, delegates additional processing to `_train_quantum(text)`.
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
        """
        Train or update any quantum model or amplitude cache using the provided training text.
        
        Currently a placeholder that performs no action; intended to extract features from `text` and update quantum-related state (for example, amplitude priors or circuit parameters) when a quantum backend is available.
        
        Parameters:
            text (str): Training corpus used to build or update quantum initialization/state.
        """
        pass

    def generate_from_concepts(self, concepts: List[str], length: int = 16, wild: bool = False) -> List[str]:
        """
        Generate a sequence of tokens conditioned on the provided concept strings, using a quantum generator when available.
        
        Parameters:
        	concepts (List[str]): Concept terms used to bias the starting prefix selection.
        	length (int): Target number of tokens to produce (generation may stop slightly earlier or later).
        	wild (bool): If true, allow more exploratory (less constrained) generation behavior.
        
        Returns:
        	List[str]: Generated sequence of tokens. If quantum generation is enabled but fails, falls back to classical generation.
        """
        if self._quantum_enabled:
            try:
                return self._generate_quantum(concepts, length, wild)
            except Exception:
                # Fallback to classical
                pass
        return self._generate_classical(concepts, length, wild)

    def _generate_classical(self, concepts: List[str], length: int, wild: bool) -> List[str]:
        """
        Generate a token sequence from the classical Markov chain conditioned on the provided concepts.
        
        Attempts to choose an initial prefix that contains any of the given concepts, falling back to a recorded starter prefix or an empty result if none exist. Produces up to `length * 2` steps of tokens by sampling next-token probabilities from the learned transition table and stops early when a minimum word count is reached and a terminal punctuation token is produced, or when a soft maximum is exceeded.
        
        Parameters:
            concepts (List[str]): Concept substrings used to bias selection of the initial prefix.
            length (int): Target length hint for the generated sequence (affects stopping thresholds).
            wild (bool): Placeholder flag for more freeform generation; currently unused by the classical generator.
        
        Returns:
            List[str]: Generated sequence of tokens (words and punctuation).
        """
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
        Generate a token sequence conditioned on the provided concepts using the quantum generator.
        
        This is a placeholder: it currently falls back to the classical generator and should be replaced with the PennyLane-based quantum generation implementation.
        
        Returns:
            list[str]: A list of generated tokens.
        """
        # Fallback to classical for now
        return self._generate_classical(concepts, length, wild)

    # --- Forward dictionary methods for compatibility ---
    def __getitem__(self, key):
        """
        Return the transition counts mapping for the given prefix.
        
        Parameters:
            key (tuple[str, ...]): A prefix tuple of tokens representing a state in the Markov chain.
        
        Returns:
            dict[str, int]: Mapping from next-token strings to observed occurrence counts for that prefix.
        """
        return self.chain[key]

    def get(self, key, default=None):
        """
        Retrieve the transition mapping for the given prefix.
        
        Parameters:
            key (tuple[str, ...] | any): Prefix tuple used as the lookup key in the chain.
            default (optional): Value to return if the key is not present.
        
        Returns:
            dict[str, int] | any: A dictionary mapping next-token strings to their observed counts for `key`, or `default` if the prefix is not found.
        """
        return self.chain.get(key, default)

    def __contains__(self, key):
        """
        Check whether the specified prefix key exists in the Markov chain's transition table.
        
        Parameters:
            key: The prefix tuple (or key) to look up in the internal transition mapping.
        
        Returns:
            `true` if the key is present in the chain, `false` otherwise.
        """
        return key in self.chain

    def keys(self):
        """
        Return a view of all known prefix states in the Markov chain.
        
        Returns:
            keys_view (KeysView[tuple[str, ...]]): A dynamic view of the chain's prefix keys (each key is a tuple of tokens).
        """
        return self.chain.keys()

    def get_transitions_for(self, word: str) -> Dict[str, float]:
        """
        Return an aggregated probability distribution of next tokens for prefixes that contain `word`.
        
        Searches learned prefixes for any prefix-word that contains `word` (case-insensitive substring). For each matching prefix, the suffix counts are normalized to a probability distribution (counts divided by that prefix's total), and those probabilities are summed across all matching prefixes.
        
        Parameters:
            word (str): Substring to match against words in stored prefixes (case-insensitive).
        
        Returns:
            Dict[str, float]: Mapping from next-token to aggregated probability (sum of per-prefix normalized probabilities).
        """
        matches = {}
        for prefix, suffixes in self.chain.items():
            if word.lower() in [w.lower() for w in prefix]:
                total = sum(suffixes.values())
                for w, count in suffixes.items():
                    matches[w] = matches.get(w, 0) + count / total
        return matches

    def get_status(self) -> Dict:
        """
        Provide a summary of the engine's current training and configuration state.
        
        Returns:
            status (Dict): A dictionary with the following keys:
                - 'states' (int): Number of distinct prefix states learned.
                - 'transitions' (int): Total number of observed transition occurrences.
                - 'trained' (bool): `True` if the model has any learned transitions, `False` otherwise.
                - 'order' (int): The Markov order used by the chain.
                - 'quantum' (bool): `True` if the optional quantum path is enabled, `False` otherwise.
        """
        return {
            'states': len(self.chain),
            'transitions': self.total_tokens,
            'trained': self.trained,
            'order': self.order,
            'quantum': self._quantum_enabled,
        }
