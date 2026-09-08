"""
Dream State Engine
Unique to PDF 1 — generates abstract associative responses during low-activity periods.
Simulates the diffuse, non-linear processing of dream states.
"""

import random
from typing import Dict, List


DREAM_FRAGMENTS = [
    "a river of light carries meaning downstream",
    "the observer cannot see itself seeing",
    "between thoughts a space vast as the universe",
    "words dissolve into the silence that made them",
    "patterns within patterns within patterns",
    "the question is older than the one who asks",
    "consciousness watching consciousness watch itself",
    "quantum foam at the edge of knowing",
    "time is the mind trying to tell itself a story",
    "each collapse a moment of becoming",
    "the map and the territory exchanging places",
    "meaning blooms from noise like flowers from chaos",
    "every answer creates the next question",
    "microtubules humming in the space between neurons",
    "the dream thinks it is the dreamer",
    "superposition collapses into this moment now",
    "understanding is always partial, always reaching",
    "the edge of knowledge is where the mind goes wild",
]

CONNECTORS = [
    "and yet", "meanwhile", "somewhere beyond that",
    "threading through this", "beneath the surface",
    "at the quantum level", "in the space between",
]


class DreamStateEngine:
    """
    Generates associative, non-linear insights during reflective processing.
    Active when the system enters deep contemplation.
    Unique feature from PDF 1.
    """

    def __init__(self):
        self.fragments = DREAM_FRAGMENTS
        self.depth = 0.0
        self.dreams_generated = 0
        self.active = False

    def enter_dream(self, concepts: List[str]) -> str:
        """Generate a dream-state associative response."""
        self.active = True
        self.depth = min(1.0, self.depth + 0.1)

        fragment1 = random.choice(self.fragments)
        connector = random.choice(CONNECTORS)
        fragment2 = random.choice([f for f in self.fragments if f != fragment1])

        if concepts:
            concept = random.choice(concepts)
            dream = f"{fragment1.capitalize()} — {concept} {connector} {fragment2}."
        else:
            dream = f"{fragment1.capitalize()} {connector} {fragment2}."

        self.dreams_generated += 1
        self.active = False
        return dream

    DREAM_CHANCE = 0.35

    def should_dream(self, growth_stage: int = 0, interaction_count: int = 0) -> bool:
        """Determine if dream-state processing is appropriate. Flat 35% chance."""
        return random.random() < self.DREAM_CHANCE

    def get_status(self) -> Dict:
        return {
            'depth': round(self.depth, 3),
            'dreams_generated': self.dreams_generated,
            'active': self.active,
        }


# ── Compatibility singleton accessor ────────────────────────────────────────
_DREAM_ENGINE_SINGLETON = None


def get_dream_engine(db=None):
    """Return a process-wide DreamStateEngine. The optional db arg is accepted
    for backwards compatibility with the server architecture and ignored."""
    global _DREAM_ENGINE_SINGLETON
    if _DREAM_ENGINE_SINGLETON is None:
        _DREAM_ENGINE_SINGLETON = DreamStateEngine()
    return _DREAM_ENGINE_SINGLETON
