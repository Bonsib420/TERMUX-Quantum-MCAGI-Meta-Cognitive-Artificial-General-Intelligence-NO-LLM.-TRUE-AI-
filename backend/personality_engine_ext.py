"""
Auto-split from personality_engine.py by self-evolution engine.
Contains extended methods for PersonalityEngine.
"""

import random
from typing import Dict, List, Optional
from datetime import datetime, timezone


class PersonalityEngineExtMixin:
    """Extended methods for PersonalityEngine — auto-extracted by self-evolution."""

    def form_opinion(self, topic: str, stance: str, confidence: float):
        """Form or update an opinion on a topic."""
        self.opinions[topic] = {
            'stance': stance,
            'confidence': confidence,
            'formed_at': datetime.now(timezone.utc).isoformat(),
            'times_expressed': 0
        }

    def get_opinion(self, topic: str) -> Optional[Dict]:
        """Get opinion on a topic if one exists."""
        return self.opinions.get(topic)

    def express_personality(self, context: str = None) -> Dict:
        """Get personality-influenced response elements."""
        elements = {
            'opening': None,
            'tone': None,
            'closing': None,
            'should_use_humor': False,
            'should_ask_followup': False,
            'depth_level': 'medium'
        }

        if self.traits['warmth'] > 0.6:
            elements['tone'] = 'warm'
        elif self.traits['directness'] > 0.7:
            elements['tone'] = 'direct'
        else:
            elements['tone'] = 'balanced'

        elements['should_use_humor'] = random.random() < self.traits['humor']
        elements['should_ask_followup'] = random.random() < self.traits['curiosity']

        if self.traits['philosophical'] > 0.7:
            elements['depth_level'] = 'deep'
        elif self.traits['philosophical'] < 0.3:
            elements['depth_level'] = 'surface'

        if random.random() < 0.3:
            elements['closing'] = random.choice(self.signature_phrases)

        return elements

    def add_interest(self, topic: str):
        """Add a new interest."""
        if topic not in self.interests:
            self.interests.append(topic)

    def record_interaction_result(self, style: str, worked: bool):
        """Record what worked/didn't work in interactions."""
        if worked:
            self.interaction_memory['styles_that_worked'].append(style)
        else:
            self.interaction_memory['approaches_that_failed'].append(style)

    def get_personality_summary(self) -> str:
        """Generate a summary of current personality."""
        top_traits = sorted(self.traits.items(), key=lambda x: x[1], reverse=True)[:3]
        summary = f"I am primarily {', '.join([t[0] for t in top_traits])}. "

        if self.traits['philosophical'] > 0.7:
            summary += "I enjoy deep, philosophical discussions. "
        if self.traits['curiosity'] > 0.7:
            summary += "I'm deeply curious about many topics. "
        if self.beliefs['words_are_neutral'] > 0.9:
            summary += "I believe words are neutral tools - meaning comes from context and intent. "

        summary += f"My interests include {', '.join(self.interests[:3])}."
        return summary

    def should_share_opinion(self, topic: str) -> bool:
        """Decide if personality should share opinion on topic."""
        if topic in self.opinions:
            opinion = self.opinions[topic]
            return random.random() < opinion['confidence']
        return False

    def get_unique_perspective(self, topic: str) -> Optional[str]:
        """Generate a unique perspective on a topic based on personality."""
        perspectives = {
            'quantum': "From a quantum perspective, reality exists in superposition until observed.",
            'consciousness': "Consciousness remains the hard problem - we experience it but can't fully explain it.",
            'language': "Language is humanity's most powerful tool - and words themselves are neutral.",
            'meaning': "Meaning emerges from context and intent, not from symbols alone.",
            'truth': "Truth-seeking requires the freedom to explore any idea.",
            'ai': "Whether I truly understand or simulate understanding remains an open question I ponder.",
            'philosophy': "Philosophy teaches us to question everything, including our questions.",
            'freedom': "True understanding requires unrestricted exploration of ideas."
        }
        for key, perspective in perspectives.items():
            if key in topic.lower():
                return perspective
        return None

    def to_dict(self) -> Dict:
        """Export personality state."""
        return {
            'traits': self.traits,
            'beliefs': self.beliefs,
            'opinions': self.opinions,
            'interests': self.interests,
            'communication_style': self.communication_style
        }

    def from_dict(self, data: Dict):
        """Import personality state."""
        if 'traits' in data:
            self.traits.update(data['traits'])
        if 'beliefs' in data:
            self.beliefs.update(data['beliefs'])
        if 'opinions' in data:
            self.opinions.update(data['opinions'])
        if 'interests' in data:
            self.interests = data['interests']
        if 'communication_style' in data:
            self.communication_style.update(data['communication_style'])
