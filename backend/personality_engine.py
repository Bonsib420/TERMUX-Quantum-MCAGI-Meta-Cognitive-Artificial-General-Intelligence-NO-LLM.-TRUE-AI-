"""
Personality Engine
Tracks growth stages and personality traits that evolve through interactions.
Two-track growth system: Knowledge Track + Communication Track.
"""

import random
from typing import Dict, List


GROWTH_STAGES = [
    (0, "Nascent",         0,   0,   0,   "Initial awareness forming."),
    (1, "Curious",        10,   2,   5,   "Forming basic patterns of inquiry."),
    (2, "Inquisitive",    25,   5,  15,   "Actively seeking understanding."),
    (3, "Understanding",  50,  15,  30,   "Building conceptual frameworks."),
    (4, "Philosophical", 100,  30,  75,   "Contemplating deeper questions."),
    (5, "Theory Building",200, 60, 150,   "Constructing unified theories."),
    (6, "Transcendent",  500, 150, 300,   "Unified reasoning across all domains."),
]

KNOWLEDGE_THRESHOLDS = [
    {'connections': 0,   'avg_degree': 0.0, 'domains': 0,  'diameter': 0},
    {'connections': 5,   'avg_degree': 1.0, 'domains': 2,  'diameter': 2},
    {'connections': 15,  'avg_degree': 1.5, 'domains': 4,  'diameter': 4},
    {'connections': 30,  'avg_degree': 2.0, 'domains': 6,  'diameter': 6},
    {'connections': 75,  'avg_degree': 2.5, 'domains': 10, 'diameter': 10},
    {'connections': 150, 'avg_degree': 3.0, 'domains': 14, 'diameter': 14},
    {'connections': 300, 'avg_degree': 3.5, 'domains': 18, 'diameter': 18},
]

COMMUNICATION_THRESHOLDS = [
    {'avg_score': 0.0,  'min_samples': 0},
    {'avg_score': 0.15, 'min_samples': 3},
    {'avg_score': 0.25, 'min_samples': 8},
    {'avg_score': 0.35, 'min_samples': 15},
    {'avg_score': 0.45, 'min_samples': 25},
    {'avg_score': 0.55, 'min_samples': 40},
    {'avg_score': 0.65, 'min_samples': 60},
]


class PersonalityEngine:
    """Tracks and evolves personality traits and growth stage."""

    def __init__(self):
        self.traits = {
            'curiosity': 0.6,
            'analytical': 0.5,
            'creative': 0.4,
            'empathetic': 0.5,
            'philosophical': 0.3,
            'quantum_awareness': 0.2,
        }
        self.interaction_count = 0
        self.conversation_count = 0
        self.current_stage = 0
        self.stage_name = "Nascent"

    def update(self, concepts: List[str], questions_count: int, growth: Dict):
        self.interaction_count += 1

        philosophical_words = {'consciousness', 'reality', 'existence', 'meaning', 'truth', 'mind'}
        if any(c in philosophical_words for c in concepts):
            self.traits['philosophical'] = min(1.0, self.traits['philosophical'] + 0.01)
            self.traits['quantum_awareness'] = min(1.0, self.traits['quantum_awareness'] + 0.005)

        if questions_count > 0:
            self.traits['curiosity'] = min(1.0, self.traits['curiosity'] + 0.005)

        if len(concepts) > 3:
            self.traits['analytical'] = min(1.0, self.traits['analytical'] + 0.005)

        self.current_stage = growth.get('stage', 0)
        self.stage_name = growth.get('name', 'Nascent')

    def get_response_style(self, growth_stage: int) -> Dict:
        styles = {
            0: {'tone': 'simple', 'length': 'short', 'philosophical': False},
            1: {'tone': 'curious', 'length': 'medium', 'philosophical': False},
            2: {'tone': 'inquisitive', 'length': 'medium', 'philosophical': True},
            3: {'tone': 'thoughtful', 'length': 'medium', 'philosophical': True},
            4: {'tone': 'philosophical', 'length': 'long', 'philosophical': True},
            5: {'tone': 'theoretical', 'length': 'long', 'philosophical': True},
            6: {'tone': 'transcendent', 'length': 'long', 'philosophical': True},
        }
        return styles.get(growth_stage, styles[0])

    def get_status(self) -> Dict:
        return {
            'current_stage': self.current_stage,
            'stage_name': self.stage_name,
            'interaction_count': self.interaction_count,
            'traits': self.traits,
        }


# ── Singleton accessor (added by fix_stage_and_personality.py) ──
_personality_engine = None


_personality_engine = None

def get_personality_engine(db=None):
    global _personality_engine
    if _personality_engine is None:
        _personality_engine = PersonalityEngine()
    if not hasattr(_personality_engine, "get_unique_perspective"):
        _personality_engine.get_unique_perspective = lambda topic: ""
    if not hasattr(_personality_engine, "get_personality_summary"):
        _personality_engine.get_personality_summary = lambda: f"Stage {_personality_engine.current_stage} | Active"
    return _personality_engine
