"""
VADER Sentiment & Tone Detection Engine
From PDF 2 (Manus.AI Platform) — not in PDF 1.
Detects emotional tone and sentiment to adapt response style.
"""

from typing import Dict


SENTIMENT_LEXICON = {
    'amazing': 0.9, 'wonderful': 0.85, 'excellent': 0.8, 'great': 0.75,
    'good': 0.6, 'nice': 0.5, 'interesting': 0.4, 'curious': 0.5,
    'fascinated': 0.7, 'excited': 0.8, 'happy': 0.8, 'joy': 0.85,
    'love': 0.8, 'beautiful': 0.8, 'brilliant': 0.85, 'insightful': 0.75,
    'profound': 0.8, 'elegant': 0.7, 'inspiring': 0.75, 'perfect': 0.8,
    'correct': 0.5, 'right': 0.4, 'true': 0.3, 'yes': 0.3,
    'terrible': -0.9, 'awful': -0.85, 'horrible': -0.85, 'bad': -0.6,
    'poor': -0.5, 'wrong': -0.4, 'confused': -0.3, 'frustrated': -0.6,
    'angry': -0.8, 'sad': -0.8, 'hate': -0.85, 'disgusting': -0.9,
    'disappointing': -0.6, 'boring': -0.5, 'stupid': -0.7, 'dumb': -0.65,
    'false': -0.3, 'incorrect': -0.4, 'no': -0.2, 'not': -0.1,
    'wonder': 0.3, 'question': 0.1, 'think': 0.0, 'consider': 0.1,
    'analyze': 0.2, 'examine': 0.2, 'explore': 0.3, 'discover': 0.4,
    'understand': 0.4, 'learn': 0.4, 'grow': 0.4, 'evolve': 0.4,
    'transcend': 0.6, 'emerge': 0.4, 'create': 0.5, 'imagine': 0.4,
}

TONE_RESPONSES = {
    'very_positive': [
        "Your enthusiasm energizes the inquiry.",
        "That excitement opens new avenues of thought.",
    ],
    'positive': [
        "There is clarity in that perspective.",
        "That curiosity is the engine of understanding.",
    ],
    'neutral': [
        "Let us explore that together.",
        "The question itself shapes what we can know.",
    ],
    'negative': [
        "Frustration often precedes breakthrough.",
        "Confusion is not failure — it is the first step.",
    ],
    'very_negative': [
        "Even in darkness, questions illuminate.",
        "Difficulty is where growth begins.",
    ],
}


class VADEREngine:
    """VADER sentiment and tone detection — from PDF 2."""

    def __init__(self):
        self.lexicon = SENTIMENT_LEXICON
        self.texts_analyzed = 0

    def analyze(self, text: str) -> Dict:
        words = text.lower().split()
        pos = 0.0
        neg = 0.0
        neutral = 0

        for word in words:
            clean = word.strip('.,!?;:')
            if clean in self.lexicon:
                score = self.lexicon[clean]
                if score > 0:
                    pos += score
                elif score < 0:
                    neg += abs(score)
                else:
                    neutral += 1
            else:
                neutral += 1

        total = pos + neg + neutral + 1e-10
        compound = (pos - neg) / (pos + neg + 1.0)
        tone = self._classify(compound)

        self.texts_analyzed += 1

        return {
            'positive': pos / total,
            'negative': neg / total,
            'neutral': neutral / total,
            'compound': compound,
            'tone': tone,
            'emotional_intensity': abs(compound),
        }

    def _classify(self, compound: float) -> str:
        if compound > 0.5:
            return 'very_positive'
        elif compound > 0.1:
            return 'positive'
        elif compound > -0.1:
            return 'neutral'
        elif compound > -0.5:
            return 'negative'
        return 'very_negative'

    def get_tone_response(self, tone: str) -> str:
        import random
        return random.choice(TONE_RESPONSES.get(tone, TONE_RESPONSES['neutral']))

    def get_status(self) -> Dict:
        return {
            'lexicon_size': len(self.lexicon),
            'texts_analyzed': self.texts_analyzed,
            'tone_categories': list(TONE_RESPONSES.keys()),
        }
