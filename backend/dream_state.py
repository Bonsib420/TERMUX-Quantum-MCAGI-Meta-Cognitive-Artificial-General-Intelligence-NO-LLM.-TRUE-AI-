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
        """
        Initialize a DreamStateEngine instance and its runtime state.
        
        Attributes:
            fragments (List[str]): Reference corpus of dream fragments used to compose outputs.
            depth (float): Current dream depth level, starts at 0.0 and increases up to 1.0.
            dreams_generated (int): Count of dreams produced by this instance, starts at 0.
            active (bool): Whether the engine is currently generating a dream, starts as False.
        """
        self.fragments = DREAM_FRAGMENTS
        self.depth = 0.0
        self.dreams_generated = 0
        self.active = False

    def enter_dream(self, concepts: List[str]) -> str:
        """
        Compose a short associative "dream" sentence from stored fragments, optionally incorporating one of the provided concepts.
        
        Increases the engine's depth by 0.1 (capped at 1.0), increments `dreams_generated`, and briefly marks the engine active while generating the sentence.
        
        Parameters:
        	concepts (List[str]): Candidate concept strings; if non-empty one will be inserted into the generated sentence.
        
        Returns:
        	dream (str): A single composed dream sentence built from fragments, a connector, and optionally a chosen concept.
        """
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
        """
        Decides whether the engine should initiate a dream-state.
        
        The decision is made by sampling a uniform random value against a fixed 35% chance. The parameters are accepted for signature compatibility but are ignored.
        
        Parameters:
            growth_stage (int): Ignored.
            interaction_count (int): Ignored.
        
        Returns:
            `true` if a dream should occur, `false` otherwise.
        """
        return random.random() < self.DREAM_CHANCE

    def get_status(self) -> Dict:
        """
        Return the current status of the dream engine.
        
        The returned mapping contains three fields describing the engine's observable state.
        
        Returns:
            dict: {
                'depth': float — current dream depth rounded to three decimal places (typically between 0.0 and 1.0),
                'dreams_generated': int — total number of dreams generated,
                'active': bool — whether the engine is currently active
            }
        """
        return {
            'depth': round(self.depth, 3),
            'dreams_generated': self.dreams_generated,
            'active': self.active,
        }
