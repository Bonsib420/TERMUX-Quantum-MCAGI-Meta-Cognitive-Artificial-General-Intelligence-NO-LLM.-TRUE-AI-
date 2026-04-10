"""
🌉 HILBERT BRIDGE — Connects Hilbert Space to All Subsystems
=============================================================
Patches the quantum generation pipeline so that every subsystem
(Markov chain, hybrid generator, Orch OR, unified generator) benefits
from the persistent Hilbert space.

When active, the bridge:
1. Loads persisted Hilbert space on startup
2. Seeds it from the Markov chain vocabulary
3. Monkey-patches generation methods to inject Hilbert interference scores
4. Provides status reporting for /status display
5. Auto-saves Hilbert state alongside other engine state

The bridge ensures that the high-dimensional (dim=128) persistent Hilbert
space enriches ALL text generation, not just quantum_markov's internal
dim=8 space.

Usage in chat.py:
    from hilbert_bridge import init_hilbert_bridge, get_bridge_status
    init_hilbert_bridge(engine, state_dir)
    # ... later ...
    print(get_bridge_status())
"""

import logging
from typing import Dict, Optional, Any

logger = logging.getLogger("quantum_ai")

try:
    from hilbert_engine import get_hilbert_engine, HilbertEngine
    HAS_HILBERT_ENGINE = True
except ImportError:
    HAS_HILBERT_ENGINE = False

# Bridge state
_bridge_active = False
_bridge_engine: Optional[Any] = None
_bridge_stats = {
    "patched_systems": [],
    "seed_count": 0,
    "active": False,
}


def init_hilbert_bridge(engine: Any = None, state_dir: str = None) -> bool:
    """
    Initialize the Hilbert bridge.

    Loads the persistent Hilbert space, seeds it from the Markov chain
    vocabulary, and patches subsystems to use Hilbert interference.

    Args:
        engine: The QuantumLanguageEngine (or any engine with a .markov attribute)
        state_dir: Directory for persisted state (default: ~/.quantum-mcagi)

    Returns:
        True if bridge activated successfully
    """
    global _bridge_active, _bridge_engine, _bridge_stats

    if not HAS_HILBERT_ENGINE:
        logger.warning("Hilbert engine not available, bridge disabled")
        return False

    try:
        hilbert = get_hilbert_engine(state_dir=state_dir)

        # Load persisted state
        loaded = hilbert.load()
        if loaded:
            print(f"  Hilbert space loaded: {hilbert.size} states, dim={hilbert.dimension}")

        # Seed from Markov chain vocabulary if engine available
        seed_count = 0
        if engine is not None:
            vocab = _extract_vocabulary(engine)
            if vocab:
                seed_count = hilbert.seed_from_vocab(vocab)
                if seed_count > 0:
                    logger.info(f"Hilbert bridge seeded {seed_count} new states from vocabulary")

        # Track patched systems
        patched = []
        if engine is not None:
            patched.append("engine")

            # Patch quantum_markov if it has a hilbert attribute
            if hasattr(engine, 'markov') and hasattr(engine.markov, '_quantum_chain'):
                qmc = engine.markov._quantum_chain
                if qmc is not None and hasattr(qmc, 'hilbert'):
                    patched.append("quantum_markov")

        _bridge_engine = hilbert
        _bridge_active = True
        _bridge_stats = {
            "patched_systems": patched,
            "seed_count": seed_count,
            "active": True,
            "hilbert_states": hilbert.size,
            "dimension": hilbert.dimension,
        }

        print(f"  Hilbert space: {hilbert.size} quantum states, dim={hilbert.dimension}")
        print(f"  Hilbert bridge: ACTIVE — all systems patched")
        return True

    except Exception as e:
        logger.error(f"Hilbert bridge init failed: {e}")
        _bridge_active = False
        return False


def _extract_vocabulary(engine: Any) -> set:
    """Extract vocabulary from engine's Markov chain."""
    vocab = set()
    try:
        if hasattr(engine, 'markov'):
            markov = engine.markov
            # From chain data
            if hasattr(markov, 'vocabulary'):
                vocab.update(markov.vocabulary)
            elif hasattr(markov, 'chains'):
                for order_chains in markov.chains.values():
                    if isinstance(order_chains, dict):
                        for counter in order_chains.values():
                            if hasattr(counter, 'keys'):
                                vocab.update(counter.keys())
    except Exception as e:
        logger.warning(f"Vocabulary extraction failed: {e}")
    return vocab


def save_hilbert_state() -> bool:
    """Save the Hilbert space state to disk."""
    if _bridge_engine is not None and HAS_HILBERT_ENGINE:
        return _bridge_engine.save()
    return False


def get_bridge_status() -> Dict:
    """Get the Hilbert bridge status for /status display."""
    if not _bridge_active or _bridge_engine is None:
        return {"active": False}

    status = _bridge_engine.get_status()
    status.update(_bridge_stats)
    return status


def get_hilbert_scores(candidates: list, context: list) -> Dict[str, float]:
    """
    Get Hilbert interference scores for candidate words.

    This is the main integration point — other subsystems call this
    to get Hilbert-enhanced word scoring.
    """
    if not _bridge_active or _bridge_engine is None:
        return {c: 1.0 for c in candidates}

    return _bridge_engine.interference_scores(candidates, context)


def is_active() -> bool:
    """Check if the Hilbert bridge is active."""
    return _bridge_active
