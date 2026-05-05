"""
🌀 Hilbert Engine
==================
Born-rule semantic sampler over a finite-dimensional Hilbert space.

Replaces classical Markov sampling with quantum-state sampling:
  • Each token in the vocabulary lives at a position in 128-dim Hilbert space.
  • A density matrix ρ encodes the current 'meaning state'.
  • Sampling a token = Born rule: P(t) = |⟨vᵗ | ψ⟩|².
  • After sampling, the state collapses (projects onto the chosen token).
  • Between samples, a unitary U evolves the state through context time.

The saved state file (hilbert_state.npz) contains:
  • tokens   — array of token strings (vocabulary)
  • vectors  — (vocab_size, dim) state embeddings, |tokenᵢ⟩ = vectors[i]
  • U        — (dim, dim) unitary evolution operator

Public API:
  HilbertEngine(dim=128)
  .load_state(path) / .save_state(path)
  .sample_token(context_tokens, temperature=1.0) -> str
  .evolve(token)                      # advance state with U after seeing token
  .reset_state()                      # reset to maximally-mixed ρ
  .get_status() -> dict
"""

import os
import json
import logging
from typing import List, Optional, Dict, Tuple

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

logger = logging.getLogger("hilbert_engine")


class HilbertEngine:
    """Quantum-state semantic sampler. See module docstring."""

    def __init__(self, dim: int = 128):
        """
        Initialize the HilbertEngine and its internal quantum state.
        
        Parameters:
            dim (int): Dimension of the Hilbert space used for token embeddings and the density matrix. Defaults to 128.
        
        Raises:
            RuntimeError: If NumPy is not available.
        
        Notes:
            - Creates empty vocabulary structures (`tokens`, `token_index`) and leaves `vectors` and `U` unset.
            - Initializes the density matrix `rho` to the maximally mixed state (identity / dim).
            - Initializes `loaded` to False and `sample_count` to 0.
        """
        if not HAS_NUMPY:
            raise RuntimeError("HilbertEngine requires numpy")
        self.dim = dim
        self.tokens: List[str] = []
        self.token_index: Dict[str, int] = {}
        self.vectors: Optional["np.ndarray"] = None    # (vocab, dim) complex
        self.U: Optional["np.ndarray"] = None          # (dim, dim) unitary
        # Current quantum state: density matrix ρ of shape (dim, dim).
        # Start maximally mixed (uniform over the Hilbert space).
        self.rho: "np.ndarray" = np.eye(self.dim, dtype=complex) / self.dim
        self.loaded = False
        self.sample_count = 0

    # ────────────────────────────────────────────────────────────────────
    # Persistence
    # ────────────────────────────────────────────────────────────────────
    def load_state(self, path: str) -> None:
        """
        Load a saved Hilbert engine state from a .npz file and initialize the engine's vocabulary, embeddings, and evolution operator.
        
        Parameters:
        	path (str): Path to a .npz file containing `tokens`, `vectors`, and optionally `U`. If the file does not exist, the method logs a warning and returns without modifying the engine state.
        
        Details:
        	- Loads `tokens` (string list) and rebuilds the internal token index.
        	- Loads `vectors` as complex-valued embeddings; if the saved embedding dimension differs from the current `dim`, updates `dim` and resets `rho` to the maximally mixed state I/dim.
        	- Loads `U` (unitary evolution). If `U` is absent in the archive, sets `U` to the identity operator (no evolution).
        	- Attempts to read an optional JSON sidecar (same path with .json extension) for metadata; any errors while reading the sidecar are ignored.
        	- Marks the engine as loaded and logs a summary of the loaded vocabulary size and dimension.
        """
        if not os.path.exists(path):
            logger.warning(f"Hilbert state not found: {path}")
            return

        # numpy >= 1.16 needs allow_pickle for object arrays (tokens stored as strings)
        data = np.load(path, allow_pickle=True)

        if "tokens" in data.files:
            self.tokens = [str(t) for t in data["tokens"]]
            self.token_index = {t: i for i, t in enumerate(self.tokens)}
        if "vectors" in data.files:
            self.vectors = np.asarray(data["vectors"], dtype=complex)
            # If the saved dim differs from constructor, follow the saved one.
            if self.vectors.ndim == 2 and self.vectors.shape[1] != self.dim:
                self.dim = self.vectors.shape[1]
                self.rho = np.eye(self.dim, dtype=complex) / self.dim
        if "U" in data.files:
            self.U = np.asarray(data["U"], dtype=complex)
        else:
            # No saved U → start with identity (no evolution between samples)
            self.U = np.eye(self.dim, dtype=complex)

        # Optional JSON sidecar with counts / metadata (currently unused but read for parity)
        sidecar = path.replace(".npz", ".json")
        if os.path.exists(sidecar):
            try:
                with open(sidecar) as f:
                    json.load(f)
            except Exception:
                pass

        self.loaded = True
        vocab = len(self.tokens)
        logger.info(f"HilbertEngine loaded: {vocab} tokens, dim={self.dim}")

    def save_state(self, path: str) -> None:
        """
        Persist the engine's vocabulary, embedding vectors, and evolution operator to a .npz file.
        
        If the engine has no vectors or no evolution operator, the method does nothing. The parent directory is created if it does not exist; the file at `path` will contain `tokens` (object array), `vectors`, and `U`.
        Parameters:
            path (str): Filesystem path where the .npz state file will be written.
        """
        if self.vectors is None or self.U is None:
            return
        os.makedirs(os.path.dirname(path), exist_ok=True)
        np.savez(
            path,
            tokens=np.array(self.tokens, dtype=object),
            vectors=self.vectors,
            U=self.U,
        )

    # ────────────────────────────────────────────────────────────────────
    # State preparation from context
    # ────────────────────────────────────────────────────────────────────
    def reset_state(self) -> None:
        """Reset to maximally mixed ρ = I/dim."""
        self.rho = np.eye(self.dim, dtype=complex) / self.dim

    def _prepare_state_from_context(self, context_tokens: List[str]) -> "np.ndarray":
        """
        Constructs a density matrix representing a pure state from the provided context tokens.
        
        Given known tokens, this builds ψ as the (complex) sum of their embedding vectors, normalizes ψ, and returns the pure-state density matrix |ψ⟩⟨ψ|. If no vectors are loaded, no context tokens are known, or the summed vector has near-zero norm, returns the maximally mixed state I/dim.
        
        Parameters:
            context_tokens (List[str]): Sequence of tokens to build the context state from; tokens not present in the engine's vocabulary are skipped.
        
        Returns:
            np.ndarray: A (dim x dim) complex-valued density matrix equal to |ψ⟩⟨ψ| for the normalized ψ, or I/dim when a pure state cannot be constructed.
        """
        if self.vectors is None or not context_tokens:
            return np.eye(self.dim, dtype=complex) / self.dim

        psi = np.zeros(self.dim, dtype=complex)
        hits = 0
        for tok in context_tokens:
            idx = self.token_index.get(tok.lower())
            if idx is None:
                continue
            psi += self.vectors[idx]
            hits += 1
        if hits == 0:
            return np.eye(self.dim, dtype=complex) / self.dim

        norm = np.linalg.norm(psi)
        if norm < 1e-12:
            return np.eye(self.dim, dtype=complex) / self.dim
        psi = psi / norm
        return np.outer(psi, np.conj(psi))   # |ψ⟩⟨ψ|

    # ────────────────────────────────────────────────────────────────────
    # Born-rule sampling — the core of the engine
    # ────────────────────────────────────────────────────────────────────
    def sample_token(
        self,
        context_tokens: Optional[List[str]] = None,
        temperature: float = 1.0,
        top_k: int = 0,
    ) -> Optional[str]:
        """
        Select a token from the engine's semantic state using Born-rule probabilities.
        
        When possible, computes probabilities from the current density matrix (or from a state prepared from `context_tokens`), optionally sharpens them by `temperature`, and optionally restricts to the top `top_k` candidates. After sampling, the engine collapses its internal density matrix to the chosen token's projector, applies the configured unitary evolution, and increments the sample counter.
        
        Parameters:
            context_tokens (Optional[List[str]]): If provided, build a temporary state from these tokens and sample from it; unknown tokens are ignored.
            temperature (float): Temperature > 0 that adjusts distribution sharpness (1.0 leaves probabilities unchanged).
            top_k (int): If > 0 and less than the vocabulary size, limit sampling to the top `top_k` tokens by probability.
        
        Returns:
            Optional[str]: The sampled token string, or `None` if sampling cannot be performed (for example, the engine is not loaded, no vectors are available, or probabilities are degenerate).
        """
        if not self.loaded or self.vectors is None or len(self.tokens) == 0:
            return None

        # Use seeded ρ if context provided, otherwise current self.rho
        if context_tokens:
            rho = self._prepare_state_from_context(context_tokens)
        else:
            rho = self.rho

        # Born rule: P(i) = ⟨vᵢ | ρ | vᵢ⟩, real and non-negative
        # Compute as einsum for vectorized speed: weights_i = vectors[i]† ρ vectors[i]
        weights = np.einsum("ij,jk,ik->i", np.conj(self.vectors), rho, self.vectors).real
        weights = np.clip(weights, 0.0, None)   # numerical floor
        total = weights.sum()
        if total < 1e-18:
            return None
        weights = weights / total

        # Temperature
        if temperature != 1.0 and temperature > 0.0:
            weights = np.power(weights, 1.0 / temperature)
            weights /= weights.sum()

        # Top-k filter
        if top_k and top_k < len(weights):
            cutoff_idx = np.argpartition(-weights, top_k)[:top_k]
            mask = np.zeros_like(weights)
            mask[cutoff_idx] = weights[cutoff_idx]
            s = mask.sum()
            if s < 1e-18:
                return None
            weights = mask / s

        # Sample
        idx = int(np.random.choice(len(weights), p=weights))
        token = self.tokens[idx]

        # Collapse: project ρ onto the chosen state |vᵢ⟩
        v = self.vectors[idx]
        v_norm = v / (np.linalg.norm(v) + 1e-12)
        self.rho = np.outer(v_norm, np.conj(v_norm))
        # Then evolve forward by U for the next sample
        if self.U is not None:
            self.rho = self.U @ self.rho @ np.conj(self.U.T)

        self.sample_count += 1
        return token

    # ────────────────────────────────────────────────────────────────────
    # External evolution — call after seeing an externally-supplied token
    # ────────────────────────────────────────────────────────────────────
    def evolve(self, token: str) -> None:
        """
        Collapse the internal density matrix to the projector for `token` and then apply the unitary evolution.
        
        Parameters:
            token (str): Token whose embedding will be used to set the state. The lookup is case-insensitive; if the token is unknown or embeddings are missing, the state is not modified.
        """
        idx = self.token_index.get(token.lower())
        if idx is None or self.vectors is None:
            return
        v = self.vectors[idx]
        v_norm = v / (np.linalg.norm(v) + 1e-12)
        self.rho = np.outer(v_norm, np.conj(v_norm))
        if self.U is not None:
            self.rho = self.U @ self.rho @ np.conj(self.U.T)

    # ────────────────────────────────────────────────────────────────────
    def get_status(self) -> Dict:
        """
        Report the engine's current status and metadata.
        
        Returns:
            status (dict): A mapping with keys:
                - "loaded": `True` if state was successfully loaded, `False` otherwise.
                - "dim": current Hilbert space dimension (int).
                - "vocab_size": number of tokens in the vocabulary (int).
                - "samples_drawn": number of tokens sampled so far (int).
                - "has_U": `True` if a unitary evolution operator is present, `False` otherwise.
        """
        return {
            "loaded": self.loaded,
            "dim": self.dim,
            "vocab_size": len(self.tokens),
            "samples_drawn": self.sample_count,
            "has_U": self.U is not None,
        }


# Singleton accessor for convenience
_INSTANCE: Optional[HilbertEngine] = None

def get_hilbert_engine(dim: int = 128) -> HilbertEngine:
    """
    Get the module-level singleton HilbertEngine instance, creating it if necessary.
    
    If no instance exists this constructs a new HilbertEngine with the given dimension; subsequent calls return the same instance and ignore the `dim` argument.
    
    Parameters:
        dim (int): Hilbert space dimension to use when creating the singleton (only used on first call).
    
    Returns:
        HilbertEngine: The shared HilbertEngine singleton.
    """
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = HilbertEngine(dim=dim)
    return _INSTANCE
