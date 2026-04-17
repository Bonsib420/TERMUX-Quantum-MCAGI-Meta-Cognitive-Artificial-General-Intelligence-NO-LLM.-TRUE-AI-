"""
Hilbert Integration Bridge
One call wires the Hilbert Semantic Engine into the full MCAGI pipeline.

In chat.py, after engine = QuantumLanguageEngine(), add:
    from hilbert_bridge import wire_hilbert
    wire_hilbert(engine)

That's it. Everything else is automatic:
    - learn_from_text() trains both Markov AND Hilbert
    - generate_response() uses Hilbert concept weighting
    - save_state() / load_state() includes Hilbert data
    - /ingest trains both systems
    - /status shows Hilbert stats
"""

import os
import numpy as np
from functools import wraps
from collections import defaultdict

try:
    from hilbert_engine import HilbertEngine
    HAS_HILBERT = True
except ImportError:
    HAS_HILBERT = False


def wire_hilbert(engine, dim=128):
    """
    Wire Hilbert engine into a live QuantumLanguageEngine instance.
    Patches: learn, save, load, generate_response, extract_concepts.
    """
    if not HAS_HILBERT:
        print("  Hilbert: unavailable (hilbert_engine.py missing)")
        return False

    # ── Initialize ──
    hilbert_dir = os.path.expanduser('~/.quantum-mcagi/hilbert')
    os.makedirs(hilbert_dir, exist_ok=True)

    engine.hilbert = HilbertEngine(dim=dim, data_dir=hilbert_dir)
    engine._has_hilbert = True

    state_path = os.path.join(hilbert_dir, 'hilbert_state.npz')
    if os.path.exists(state_path):
        engine.hilbert.load_state(state_path)
        print(f"  Hilbert space: {engine.hilbert.space.vocab_size} quantum states, dim={dim}")
    else:
        print(f"  Hilbert space: fresh, dim={dim}")

    # ── Patch learn_from_text ──
    # Every /ingest and /learn now trains both Markov and Hilbert
    _original_learn = engine.learn_from_text

    @wraps(_original_learn)
    def _patched_learn(text, *args, **kwargs):
        result = _original_learn(text, *args, **kwargs)
        try:
            engine.hilbert.learn(text)
        except Exception:
            pass
        return result

    engine.learn_from_text = _patched_learn

    # ── Patch save_state ──
    _original_save = engine.save_state

    @wraps(_original_save)
    def _patched_save(path, *args, **kwargs):
        result = _original_save(path, *args, **kwargs)
        try:
            engine.hilbert.save_state()
        except Exception:
            pass
        return result

    engine.save_state = _patched_save

    # ── Patch load_state ──
    _original_load = engine.load_state

    @wraps(_original_load)
    def _patched_load(path, *args, **kwargs):
        result = _original_load(path, *args, **kwargs)
        try:
            engine.hilbert.load_state()
        except Exception:
            pass
        return result

    engine.load_state = _patched_load

    # ── Patch generate_response ──
    # Hilbert provides concept weights that influence word selection
    _original_generate = engine.generate_response

    @wraps(_original_generate)
    def _patched_generate(user_input, questions, understanding_or_context,
                          concepts, *args, **kwargs):
        # Get Hilbert concept scores for the input
        try:
            input_tokens = engine.hilbert._tokenize(user_input)
            rho = engine.hilbert.encoder.encode(input_tokens)
            rho_evolved = engine.hilbert.context.evolve(rho)

            # Score known concepts against the evolved state
            hilbert_scores = {}
            if isinstance(concepts, list):
                for c in concepts:
                    c_str = c if isinstance(c, str) else str(c)
                    score = engine.hilbert.interference.interference_score(
                        rho_evolved, c_str.lower()
                    )
                    hilbert_scores[c_str] = score

            # Get entangled concepts not in the input
            entangled = engine.hilbert.entanglement.get_entangled_candidates(
                input_tokens, top_n=10
            )

            # Inject top entangled concepts into the concept list
            if isinstance(concepts, list):
                for token, score in entangled[:5]:
                    if token not in [c.lower() if isinstance(c, str) else str(c).lower()
                                     for c in concepts]:
                        concepts.append(token)

            # Store scores on engine for hybrid_generator to use
            engine._hilbert_scores = hilbert_scores
            engine._hilbert_coherence = float(np.real(np.trace(rho_evolved @ rho_evolved)))

        except Exception:
            engine._hilbert_scores = {}
            engine._hilbert_coherence = 0.0

        # Hilbert does NOT generate text — it only scores concepts
        # Always use the structured composer/Markov for generation
        result = _original_generate(user_input, questions, understanding_or_context, concepts, *args, **kwargs)

        # Post-generation: update Hilbert context from the exchange
        try:
            if result and isinstance(result, str):
                response_tokens = engine.hilbert._tokenize(result)
                if response_tokens:
                    response_rho = engine.hilbert.encoder.encode(response_tokens)
                    engine.hilbert.context.update_from_exchange(rho, response_rho)
        except Exception:
            pass

        return result

    engine.generate_response = _patched_generate

    # ── Add Hilbert-enhanced concept extraction ──
    if hasattr(engine, 'extract_concepts'):
        _original_extract = engine.extract_concepts

        @wraps(_original_extract)
        def _patched_extract(text, *args, **kwargs):
            # Get original TF-IDF concepts
            concepts = _original_extract(text, *args, **kwargs)

            pass  # Hilbert enhancement done at generation time, not extraction

            return concepts

        engine.extract_concepts = _patched_extract

    # ── Add scored concept extraction ──
    if hasattr(engine, 'extract_concepts_scored'):
        _original_scored = engine.extract_concepts_scored

        @wraps(_original_scored)
        def _patched_scored(text, *args, **kwargs):
            scored = _original_scored(text, *args, **kwargs)

            # Enhance scores with Hilbert interference
            try:
                tokens = engine.hilbert._tokenize(text)
                rho = engine.hilbert.encoder.encode(tokens)

                if isinstance(scored, list):
                    for i, item in enumerate(scored):
                        if isinstance(item, dict) and 'concept' in item:
                            h_score = engine.hilbert.interference.interference_score(
                                rho, item['concept'].lower()
                            )
                            item['hilbert_score'] = h_score
                            # Blend: 60% original + 40% Hilbert
                            if 'score' in item:
                                item['score'] = 0.6 * item['score'] + 0.4 * h_score
                        elif isinstance(item, tuple) and len(item) == 2:
                            concept, score = item
                            h_score = engine.hilbert.interference.interference_score(
                                rho, concept.lower()
                            )
                            scored[i] = (concept, 0.6 * score + 0.4 * h_score)
            except Exception:
                pass

            return scored

        engine.extract_concepts_scored = _patched_scored

    # ── Add stats method ──
    def get_hilbert_stats():
        if not engine._has_hilbert:
            return {}
        stats = engine.hilbert.get_stats()
        stats['coherence'] = getattr(engine, '_hilbert_coherence', 0.0)
        return stats

    engine.get_hilbert_stats = get_hilbert_stats

    print(f"  Hilbert bridge: ACTIVE — all systems patched")
    return True


def get_hilbert_status_string(engine):
    """Format Hilbert stats for /status display."""
    if not getattr(engine, '_has_hilbert', False):
        return "  --- HILBERT SPACE ---\n  Status: INACTIVE\n"

    stats = engine.get_hilbert_stats()
    lines = [
        "  --- HILBERT SPACE (Quantum Semantic Engine) ---",
        f"  Status: ACTIVE",
        f"  Dimension: {stats.get('dim', '?')}",
        f"  Quantum states: {stats.get('vocab_size', 0)}",
        f"  Tokens trained: {stats.get('total_tokens_trained', 0):,}",
        f"  Documents: {stats.get('total_documents', 0)}",
        f"  Coherence: {stats.get('coherence', 0):.4f}",
    ]

    top = stats.get('top_tokens', [])[:10]
    if top:
        lines.append(f"  Top states: {', '.join(t for t, c in top)}")

    return '\n'.join(lines) + '\n'
