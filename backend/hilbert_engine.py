"""
Quantum Semantic Engine (QSE)
Hilbert space language generation — replaces Markov chain surface.

Architecture:
  Layer 1: Hilbert Space — tokens as quantum states in C^dim
  Layer 2: Density Matrix Encoding — sentences as mixed states
  Layer 3: Context Evolution — unitary operators from conversation history
  Layer 4: Entanglement — concept relationships as tensor products
  Layer 5: Interference — coherence scoring replaces PMI
  Layer 6: Measurement — Born-rule collapse selects words

No LLM. No API. Pure quantum mechanics applied to language.

Usage:
    from hilbert_engine import HilbertEngine
    engine = HilbertEngine(dim=128)
    engine.learn("The universe is vast and mysterious")
    response = engine.generate("What is the universe?")
"""

import numpy as np
import math
import hashlib
import json
import os
import time
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


# ============================================================================
# LAYER 1: HILBERT SPACE — Semantic Field
# ============================================================================

class HilbertSpace:
    """
    Maps tokens to vectors in a complex Hilbert space.
    Each word lives as a quantum state |ψ⟩ ∈ C^dim.
    Similar words should have similar states (via training).
    """

    def __init__(self, dim=128):
        self.dim = dim
        self.basis = {}          # token -> complex vector
        self.token_counts = defaultdict(int)
        self.cooccurrence = defaultdict(lambda: defaultdict(int))
        self._rng = np.random.RandomState(42)

    def get_state(self, token: str) -> np.ndarray:
        """Get or create quantum state for a token."""
        token = token.lower().strip()
        if token not in self.basis:
            # Initialize with deterministic hash-seeded random state
            seed = int(hashlib.sha256(token.encode()).hexdigest()[:8], 16)
            rng = np.random.RandomState(seed)
            vec = rng.randn(self.dim) + 1j * rng.randn(self.dim)
            vec /= np.linalg.norm(vec)
            self.basis[token] = vec
        return self.basis[token]

    def update_state(self, token: str, context_tokens: List[str], learning_rate=0.01):
        """
        Shift token's state toward its context (skip-gram style).
        Tokens that appear together become more similar in Hilbert space.
        """
        token = token.lower().strip()
        psi = self.get_state(token)

        for ctx in context_tokens:
            ctx = ctx.lower().strip()
            if ctx == token:
                continue
            ctx_psi = self.get_state(ctx)

            # Move token toward context
            shift = learning_rate * ctx_psi
            psi = psi + shift
            psi /= np.linalg.norm(psi)

            # Track cooccurrence
            self.cooccurrence[token][ctx] += 1
            self.cooccurrence[ctx][token] += 1

        self.basis[token] = psi
        self.token_counts[token] += 1

    def similarity(self, t1: str, t2: str) -> float:
        """Quantum fidelity between two token states."""
        psi1 = self.get_state(t1)
        psi2 = self.get_state(t2)
        return float(np.abs(np.vdot(psi1, psi2)) ** 2)

    @property
    def vocab_size(self):
        return len(self.basis)


# ============================================================================
# LAYER 2: DENSITY MATRIX ENCODING — Sentences as States
# ============================================================================

class DensityEncoder:
    """
    Encodes a sequence of tokens into a density matrix ρ.
    ρ = (1/N) Σ |ψ_i⟩⟨ψ_i|
    Mixed state captures the "meaning distribution" of the input.
    """

    def __init__(self, space: HilbertSpace):
        self.space = space

    def encode(self, tokens: List[str]) -> np.ndarray:
        """Encode token list into density matrix."""
        dim = self.space.dim
        rho = np.zeros((dim, dim), dtype=complex)

        if not tokens:
            return rho

        for t in tokens:
            psi = self.space.get_state(t)
            rho += np.outer(psi, np.conj(psi))

        return rho / len(tokens)

    def encode_weighted(self, tokens: List[str], weights: List[float]) -> np.ndarray:
        """Encode with TF-IDF or importance weights."""
        dim = self.space.dim
        rho = np.zeros((dim, dim), dtype=complex)

        if not tokens:
            return rho

        total_weight = sum(weights) + 1e-10
        for t, w in zip(tokens, weights):
            psi = self.space.get_state(t)
            rho += (w / total_weight) * np.outer(psi, np.conj(psi))

        return rho


# ============================================================================
# LAYER 3: CONTEXT EVOLUTION — Memory as Unitary Operators
# ============================================================================

class ContextEvolution:
    """
    Context transforms meaning through unitary evolution.
    U_context * ρ * U_context†
    
    The unitary is built from conversation history,
    rotating the semantic space to favor contextually relevant words.
    """

    def __init__(self, dim: int):
        self.dim = dim
        self.U = np.eye(dim, dtype=complex)  # Start with identity
        self._history = []

    def update_from_exchange(self, input_rho: np.ndarray, response_rho: np.ndarray,
                              learning_rate=0.05):
        """
        Learn a context operator from an input-response pair.
        The unitary should map input meaning toward response meaning.
        """
        # Compute the "rotation" that maps input to response
        # Using polar decomposition: response_rho ≈ U * input_rho * U†
        try:
            # Small perturbation toward the desired transformation
            delta = response_rho @ np.linalg.pinv(input_rho + 1e-6 * np.eye(self.dim))
            
            # Make it unitary via QR decomposition
            Q, R = np.linalg.qr(delta)
            
            # Blend with current U
            self.U = (1 - learning_rate) * self.U + learning_rate * Q
            
            # Re-orthogonalize
            self.U, _ = np.linalg.qr(self.U)
        except np.linalg.LinAlgError:
            pass

    def evolve(self, rho: np.ndarray) -> np.ndarray:
        """Apply context evolution to a density matrix."""
        return self.U @ rho @ self.U.conj().T

    def reset(self):
        """Reset to identity (no context bias)."""
        self.U = np.eye(self.dim, dtype=complex)


# ============================================================================
# LAYER 4: ENTANGLEMENT — Concept Relationships
# ============================================================================

class EntanglementLayer:
    """
    Models relationships between concepts as entangled states.
    |ψ_AB⟩ = |ψ_A⟩ ⊗ |ψ_B⟩ for independent concepts
    Entangled pairs share a joint state that can't be factored.
    """

    def __init__(self, space: HilbertSpace):
        self.space = space
        self.entangled_pairs = {}  # (t1, t2) -> entanglement strength

    def measure_entanglement(self, t1: str, t2: str) -> float:
        """
        Measure entanglement between two tokens based on cooccurrence.
        High cooccurrence = high entanglement.
        """
        t1, t2 = t1.lower(), t2.lower()
        co = self.space.cooccurrence[t1].get(t2, 0)
        c1 = self.space.token_counts.get(t1, 1)
        c2 = self.space.token_counts.get(t2, 1)

        # PMI-inspired but quantum: higher cooccurrence = more entangled
        if co == 0:
            return 0.0

        if not hasattr(self.space, "_tc_sum"):
            self.space._tc_sum = sum(self.space.token_counts.values())
        pmi = math.log2((co * self.space._tc_sum) / (c1 * c2 + 1e-10) + 1e-10)
        return max(0.0, min(1.0, pmi / 10.0))

    def get_entangled_candidates(self, tokens: List[str], top_n=20) -> List[Tuple[str, float]]:
        """Get tokens most entangled with the input tokens."""
        scores = defaultdict(float)

        for t in tokens:
            t = t.lower()
            for other, count in self.space.cooccurrence[t].items():
                if other not in [tk.lower() for tk in tokens]:
                    ent = self.measure_entanglement(t, other)
                    scores[other] = max(scores[other], ent)

        ranked = sorted(scores.items(), key=lambda x: -x[1])
        return ranked[:top_n]


# ============================================================================
# LAYER 5: INTERFERENCE — Coherence Scoring
# ============================================================================

class InterferenceLayer:
    """
    Quantum interference determines which candidate words
    constructively or destructively interfere with the current state.
    Replaces PMI/coherence scoring.
    """

    def __init__(self, space: HilbertSpace):
        self.space = space

    def coherence(self, rho: np.ndarray) -> float:
        """
        Measure coherence of a density matrix.
        Tr(ρ²) = 1 for pure states, < 1 for mixed states.
        High coherence = aligned meaning. Low = ambiguity.
        """
        return float(np.real(np.trace(rho @ rho)))

    def interference_score(self, rho: np.ndarray, candidate: str) -> float:
        """
        How much does adding this candidate constructively interfere
        with the current state?
        """
        psi = self.space.get_state(candidate)
        proj = np.outer(psi, np.conj(psi))

        # Probability of measuring this state given ρ
        prob = float(np.real(np.trace(rho @ proj)))
        return max(0.0, prob)

    def phase_alignment(self, rho: np.ndarray, candidates: List[str]) -> List[Tuple[str, float]]:
        """
        Score all candidates by phase alignment with current state.
        Returns sorted list of (candidate, score).
        """
        scored = []
        for c in candidates:
            score = self.interference_score(rho, c)
            scored.append((c, score))
        return sorted(scored, key=lambda x: -x[1])


# ============================================================================
# LAYER 6: MEASUREMENT — Born-Rule Collapse
# ============================================================================

class QuantumMeasurement:
    """
    Selects output words via Born rule.
    P(word) = Tr(ρ * |ψ_word⟩⟨ψ_word|)
    Each word selection collapses the state.
    """

    def __init__(self, space: HilbertSpace):
        self.space = space

    def measure(self, rho: np.ndarray, candidates: List[str],
                temperature=1.0) -> str:
        """
        Select a word from candidates using Born-rule probabilities.
        Temperature controls randomness (lower = more deterministic).
        """
        if not candidates:
            return ""

        probs = []
        for c in candidates:
            psi = self.space.get_state(c)
            proj = np.outer(psi, np.conj(psi))
            p = float(np.real(np.trace(rho @ proj)))
            probs.append(max(p, 1e-10))

        probs = np.array(probs)

        # Temperature scaling
        if temperature != 1.0:
            probs = np.power(probs, 1.0 / temperature)

        # Normalize
        total = probs.sum()
        if total > 0:
            probs /= total
        else:
            probs = np.ones(len(candidates)) / len(candidates)

        # Born-rule collapse
        try:
            chosen = np.random.choice(candidates, p=probs)
        except ValueError:
            chosen = np.random.choice(candidates)

        return chosen

    def measure_sequence(self, rho: np.ndarray, candidates: List[str],
                         length: int, temperature=0.8) -> List[str]:
        """
        Generate a sequence of words via successive measurements.
        Each measurement collapses the state, influencing the next.
        """
        sequence = []
        current_rho = rho.copy()

        for _ in range(length):
            word = self.measure(current_rho, candidates, temperature)
            sequence.append(word)

            # Post-measurement state update
            psi = self.space.get_state(word)
            proj = np.outer(psi, np.conj(psi))

            # Partial collapse: blend current state with measured state
            current_rho = 0.6 * current_rho + 0.4 * proj

            # Re-normalize
            trace = np.real(np.trace(current_rho))
            if trace > 0:
                current_rho /= trace

        return sequence


# ============================================================================
# HILBERT ENGINE — Full Pipeline
# ============================================================================

class HilbertEngine:
    """
    Complete Quantum Semantic Engine.
    
    Pipeline:
        input tokens → density matrix → context evolution →
        entangled candidates → interference scoring →
        Born-rule collapse → output sequence
    """

    def __init__(self, dim=128, data_dir=None):
        self.dim = dim
        self.space = HilbertSpace(dim)
        self.encoder = DensityEncoder(self.space)
        self.context = ContextEvolution(dim)
        self.entanglement = EntanglementLayer(self.space)
        self.interference = InterferenceLayer(self.space)
        self.measurement = QuantumMeasurement(self.space)

        # Training stats
        self.total_tokens_trained = 0
        self.total_documents = 0
        self.training_start = None

        # Data directory
        if data_dir is None:
            data_dir = os.path.expanduser('~/.quantum-mcagi/hilbert')
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    # ── Training ──

    def learn(self, text: str, window_size=5):
        """
        Train the Hilbert space from text.
        Builds token states and cooccurrence via sliding window.
        """
        if self.training_start is None:
            self.training_start = time.time()

        # Tokenize
        tokens = self._tokenize(text)
        if len(tokens) < 2:
            return

        # Sliding window context learning
        for i, token in enumerate(tokens):
            start = max(0, i - window_size)
            end = min(len(tokens), i + window_size + 1)
            context = [tokens[j] for j in range(start, end) if j != i]
            self.space.update_state(token, context)

        self.total_tokens_trained += len(tokens)
        self.total_documents += 1

    def learn_from_file(self, filepath: str):
        """Learn from a text file."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            self.learn(text)
            return len(text.split())
        except Exception as e:
            print(f"  Error learning from {filepath}: {e}")
            return 0

    # ── Generation ──

    def generate(self, input_text: str, min_words=8, max_words=30,
                 temperature=0.8) -> str:
        """
        Generate a response using the full quantum pipeline.
        
        1. Tokenize input
        2. Encode as density matrix
        3. Apply context evolution
        4. Find entangled candidates
        5. Score by interference
        6. Measure (Born-rule collapse) word by word
        """
        start = time.time()

        # Step 1: Tokenize
        input_tokens = self._tokenize(input_text)
        if not input_tokens:
            return "I need more experience to respond to that."

        # Step 2: Encode input as density matrix
        rho = self.encoder.encode(input_tokens)

        # Step 3: Context evolution
        rho_evolved = self.context.evolve(rho)

        # Step 4: Build candidate pool
        candidates = self._build_candidate_pool(input_tokens)
        if len(candidates) < 5:
            return "My vocabulary is still growing. Feed me more text."

        # Step 5: Score by interference (only score candidates, not full vocab)
        scored = self.interference.phase_alignment(rho_evolved, candidates[:100])

        # Step 6: Generate via successive measurements
        # Use top candidates weighted by interference
        top_candidates = [c for c, s in scored[:200]]  # Top 200 by phase alignment

        target_length = min_words + np.random.randint(0, max_words - min_words + 1)
        words = self.measurement.measure_sequence(
            rho_evolved, top_candidates, target_length, temperature
        )

        # Step 7: Post-process
        response = self._post_process(words, input_tokens)

        # Step 8: Update context from this exchange
        response_tokens = self._tokenize(response)
        if response_tokens:
            response_rho = self.encoder.encode(response_tokens)
            self.context.update_from_exchange(rho, response_rho)

        elapsed = time.time() - start

        return response

    def _build_candidate_pool(self, input_tokens):
        candidates = set()
        for t in input_tokens:
            t = t.lower()
            neighbors = self.space.cooccurrence.get(t, {})
            for token in sorted(neighbors, key=neighbors.get, reverse=True)[:30]:
                if len(token) > 2:
                    candidates.add(token)
            candidates.add(t)
        if len(candidates) < 50:
            if not hasattr(self, '_tc'):
                self._tc = sorted(self.space.token_counts.items(), key=lambda x: -x[1])[:200]
            for token, _ in self._tc:
                if len(token) > 2:
                    candidates.add(token)
                if len(candidates) >= 200:
                    break
        return list(candidates)


    def _post_process(self, words: List[str], input_tokens: List[str]) -> str:
        """Clean up generated word sequence into readable text."""
        if not words:
            return ""

        # Remove consecutive duplicates
        cleaned = [words[0]]
        for w in words[1:]:
            if w != cleaned[-1]:
                cleaned.append(w)

        # Capitalize first word
        if cleaned:
            cleaned[0] = cleaned[0].capitalize()

        # Join
        text = ' '.join(cleaned)

        # Basic punctuation
        if not text.endswith(('.', '?', '!')):
            text += '.'

        return text

    def _tokenize(self, text: str) -> List[str]:
        """Simple whitespace + punctuation tokenizer."""
        import re
        # Remove punctuation, lowercase, split
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        tokens = [t.strip() for t in text.split() if len(t.strip()) > 1]
        return tokens

    # ── State Management ──

    def save_state(self, filepath=None):
        """Save the Hilbert space to disk."""
        if filepath is None:
            filepath = os.path.join(self.data_dir, 'hilbert_state.npz')

        # Save basis vectors
        tokens = list(self.space.basis.keys())
        vectors = np.array([self.space.basis[t] for t in tokens])

        # Save counts
        counts = {t: self.space.token_counts[t] for t in tokens}

        # Save cooccurrence (sparse)
        cooc = {}
        for t1, neighbors in self.space.cooccurrence.items():
            cooc[t1] = dict(neighbors)

        # Save context evolution
        U = self.context.U

        # Bundle metadata
        meta = {
            'dim': self.dim,
            'total_tokens_trained': self.total_tokens_trained,
            'total_documents': self.total_documents,
            'vocab_size': len(tokens),
        }

        np.savez_compressed(
            filepath,
            tokens=np.array(tokens, dtype=object),
            vectors=vectors,
            U=U,
        )

        # Save JSON metadata separately (cooc is too complex for npz)
        json_path = filepath.replace('.npz', '.json')
        with open(json_path, 'w') as f:
            json.dump({
                'meta': meta,
                'counts': counts,
                'cooccurrence': cooc,
            }, f)

        return filepath

    def load_state(self, filepath=None):
        """Load the Hilbert space from disk."""
        if filepath is None:
            filepath = os.path.join(self.data_dir, 'hilbert_state.npz')

        if not os.path.exists(filepath):
            return False

        try:
            data = np.load(filepath, allow_pickle=True)
            tokens = data['tokens']
            vectors = data['vectors']
            U = data['U']

            # Rebuild space
            self.space.basis = {}
            for t, v in zip(tokens, vectors):
                self.space.basis[str(t)] = v

            # Rebuild context
            self.context.U = U

            # Load JSON metadata
            json_path = filepath.replace('.npz', '.json')
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    jdata = json.load(f)
                meta = jdata.get('meta', {})
                self.total_tokens_trained = meta.get('total_tokens_trained', 0)
                self.total_documents = meta.get('total_documents', 0)
                self.dim = meta.get('dim', self.dim)

                # Rebuild counts
                for t, c in jdata.get('counts', {}).items():
                    self.space.token_counts[t] = c

                # Rebuild cooccurrence
                for t1, neighbors in jdata.get('cooccurrence', {}).items():
                    for t2, count in neighbors.items():
                        self.space.cooccurrence[t1][t2] = count

            print(f"  Hilbert space loaded: {len(self.space.basis)} states, dim={self.dim}")
            return True

        except Exception as e:
            print(f"  Hilbert load error: {e}")
            return False

    def get_stats(self) -> dict:
        """Return engine statistics."""
        return {
            'dim': self.dim,
            'vocab_size': self.space.vocab_size,
            'total_tokens_trained': self.total_tokens_trained,
            'total_documents': self.total_documents,
            'context_coherence': float(np.real(np.trace(
                self.context.U @ self.context.U.conj().T))) / self.dim,
            'top_tokens': sorted(
                self.space.token_counts.items(),
                key=lambda x: -x[1]
            )[:20],
        }


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys

    print("Quantum Semantic Engine — Hilbert Space Language Generator")
    print("No LLM. No API. Pure quantum mechanics.\n")

    engine = HilbertEngine(dim=128)

    # Quick test
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_texts = [
            "Consciousness is the fundamental mystery of existence.",
            "Quantum mechanics describes reality at the smallest scales.",
            "The universe began with a singularity of infinite density.",
            "Philosophy asks questions that science cannot answer.",
            "Time flows forward but physics works the same in reverse.",
            "The mind and brain are not the same thing.",
            "Dark energy accelerates the expansion of the universe.",
            "Free will may be an illusion created by deterministic processes.",
            "Mathematics is the language in which the universe is written.",
            "God exists outside of space and time as we understand them.",
        ]

        print("Training on test corpus...")
        for text in test_texts:
            engine.learn(text)
            print(f"  Learned: {text[:50]}...")

        stats = engine.get_stats()
        print(f"\nVocab: {stats['vocab_size']}")
        print(f"Tokens trained: {stats['total_tokens_trained']}")

        print("\nGenerating responses:")
        prompts = [
            "What is consciousness?",
            "Tell me about the universe.",
            "Does God exist?",
        ]
        for prompt in prompts:
            start = time.time()
            response = engine.generate(prompt)
            elapsed = (time.time() - start) * 1000
            print(f"\n  Q: {prompt}")
            print(f"  A: {response}")
            print(f"  ({elapsed:.0f}ms)")

    elif len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        print("Interactive mode. Type 'quit' to exit.\n")
        print("Feed text with: /learn <text>")
        print("Or just type to generate responses.\n")

        while True:
            try:
                user = input("You: ").strip()
                if not user:
                    continue
                if user.lower() == 'quit':
                    break
                if user.startswith('/learn '):
                    text = user[7:]
                    engine.learn(text)
                    print(f"  Learned {len(text.split())} words. Vocab: {engine.space.vocab_size}")
                    continue
                if user == '/stats':
                    stats = engine.get_stats()
                    print(f"  Vocab: {stats['vocab_size']}")
                    print(f"  Trained: {stats['total_tokens_trained']} tokens")
                    print(f"  Documents: {stats['total_documents']}")
                    continue

                start = time.time()
                response = engine.generate(user)
                elapsed = (time.time() - start) * 1000
                print(f"  AI: {response}")
                print(f"  ({elapsed:.0f}ms)")
            except KeyboardInterrupt:
                break
            except EOFError:
                break

        print("\nSaving state...")
        engine.save_state()
        print("Done.")

    else:
        print("Usage:")
        print("  python hilbert_engine.py --test          # Run test corpus")
        print("  python hilbert_engine.py --interactive   # Interactive mode")
