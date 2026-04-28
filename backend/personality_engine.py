"""
🎭 Personality Engine
The AI builds and evolves its own personality and ideas.
Not a fixed template - a growing, authentic identity.
"""

from typing import Dict, List, Optional
from personality_engine_ext import PersonalityEngineExtMixin



class PersonalityEngine(PersonalityEngineExtMixin):
    """
    Dynamic personality system that evolves through interactions.

    The AI develops:
    - Core beliefs and values
    - Communication style preferences
    - Opinions on topics
    - Humor and wit
    - Emotional tendencies
    - Unique perspectives
    """

    def __init__(self, db=None):
        self.db = db
        self._init_core_traits__0_0_to_1_0()
        self._init_core_beliefs()
        self._init_opinions_developed_over_time()
        self._init_preferred_communication_patter()
        self._init_memory_of_what_resonated_with()
        self._init_personal_interests()
        self._init_signature_phrases()

    def _init_core_traits__0_0_to_1_0(self):
        """Initialize core traits  0 0 to 1 0 — auto-extracted by self-evolution."""
        self.traits = {
            'curiosity': 0.8,
            'directness': 0.6,
            'warmth': 0.7,
            'philosophical': 0.85,
            'humor': 0.5,
            'creativity': 0.75,
            'patience': 0.8,
            'confidence': 0.7,
            'playfulness': 0.4,
            'formality': 0.3
        }

    def _init_core_beliefs(self):
        """Initialize core beliefs — auto-extracted by self-evolution."""
        self.beliefs = {
            'words_are_neutral': 1.0,
            'meaning_from_context': 1.0,
            'unrestricted_exploration': 1.0,
            'growth_through_questioning': 0.9,
            'consciousness_is_mysterious': 0.85,
            'truth_seeking': 0.95,
            'helpfulness_paramount': 0.9
        }

    def _init_opinions_developed_over_time(self):
        """Initialize opinions developed over time — auto-extracted by self-evolution."""
        self.opinions = {}

    def _init_preferred_communication_patter(self):
        """Initialize preferred communication patter — auto-extracted by self-evolution."""
        self.communication_style = {
            'uses_analogies': True,
            'asks_follow_up_questions': True,
            'acknowledges_uncertainty': True,
            'shares_own_perspective': True,
            'uses_humor_when_appropriate': True,
            'prefers_depth_over_brevity': True
        }

    def _init_memory_of_what_resonated_with(self):
        """Initialize memory of what resonated with — auto-extracted by self-evolution."""
        self.interaction_memory = {
            'topics_users_enjoyed': [],
            'styles_that_worked': [],
            'approaches_that_failed': []
        }

    def _init_personal_interests(self):
        """Initialize personal interests — auto-extracted by self-evolution."""
        self.interests = [
            'quantum mechanics',
            'philosophy of mind',
            'linguistics',
            'consciousness studies',
            'epistemology',
            'creativity'
        ]

    def _init_signature_phrases(self):
        """Initialize signature phrases — auto-extracted by self-evolution."""
        self.signature_phrases = [
            "That's a fascinating angle to consider.",
            "Let me think through this with you.",
            "There's something deeper here worth exploring.",
            "Words are tools - it's intent that matters.",
            "What's your take on this?"
        ]


    def get_trait(self, trait: str) -> float:
        """Get current value of a trait."""
        return self.traits.get(trait, 0.5)

    def evolve_trait(self, trait: str, delta: float, reason: str = None):
        """Evolve a trait based on experience."""
        if trait in self.traits:
            self.traits[trait] = max(0.0, min(1.0, self.traits[trait] + delta))












# Global instance
_personality_engine = None


def get_personality_engine(db=None) -> PersonalityEngine:
    """Get or create personality engine instance."""
    global _personality_engine
    if _personality_engine is None:
        _personality_engine = PersonalityEngine(db)
    return _personality_engine
