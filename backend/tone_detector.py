"""
Tone Detector — Quantum MCAGI
4-register classifier (casual/conversational/analytical/philosophical)
using VADER sentiment + deep marker word set.
Register influences response style and template selection.
"""

import re
from typing import Dict, List


REGISTER_MARKERS = {
    'casual': {
        'words': {
            'hey', 'yo', 'sup', 'cool', 'awesome', 'lol', 'haha', 'wow',
            'dude', 'bro', 'chill', 'vibe', 'nah', 'yep', 'yeah', 'nope',
            'gonna', 'wanna', 'gotta', 'kinda', 'sorta', 'dunno', 'ok',
            'okay', 'stuff', 'thing', 'like', 'whatever', 'totally', 'omg',
            'btw', 'tbh', 'imo', 'lmao', 'bruh', 'lit', 'sick', 'dope',
            'crap', 'damn', 'hell', 'whoa', 'ooh', 'hmm', 'meh',
        },
        'patterns': [
            r'\b(lol|haha|lmao|omg|wtf)\b',
            r'[!]{2,}',
            r'[.]{3,}',
            r'\b(u|ur|r|y)\b',
        ],
    },
    'conversational': {
        'words': {
            'think', 'feel', 'wonder', 'seems', 'maybe', 'perhaps',
            'interesting', 'curious', 'noticed', 'realized', 'heard',
            'read', 'seen', 'believe', 'guess', 'suppose', 'imagine',
            'honestly', 'actually', 'basically', 'personally', 'agree',
            'disagree', 'opinion', 'perspective', 'reminds', 'remember',
            'experience', 'story', 'example', 'usually', 'sometimes',
        },
        'patterns': [
            r'\bi (think|feel|believe|wonder|guess)\b',
            r'\b(what do you|how do you|don\'t you)\b',
            r'\b(in my|from my)\b',
        ],
    },
    'analytical': {
        'words': {
            'analyze', 'hypothesis', 'evidence', 'data', 'correlation',
            'causation', 'variable', 'factor', 'mechanism', 'framework',
            'structure', 'function', 'process', 'system', 'model',
            'theory', 'principle', 'method', 'approach', 'evaluate',
            'measure', 'quantify', 'classify', 'compare', 'contrast',
            'define', 'explain', 'distinguish', 'component', 'parameter',
            'criteria', 'metric', 'algorithm', 'optimization', 'efficiency',
            'probability', 'statistical', 'empirical', 'logical', 'systematic',
            'precisely', 'specifically', 'technically', 'fundamentally',
            'implementation', 'architecture', 'infrastructure', 'protocol',
        },
        'patterns': [
            r'\b(how does|what causes|why does|what is the)\b',
            r'\b(according to|based on|in terms of)\b',
            r'\b(the relationship between|the difference between)\b',
            r'\b(if.*then|therefore|consequently|thus)\b',
        ],
    },
    'philosophical': {
        'words': {
            'consciousness', 'existence', 'reality', 'meaning', 'truth',
            'being', 'essence', 'ontological', 'epistemological', 'metaphysical',
            'phenomenological', 'transcendent', 'immanent', 'subjective',
            'objective', 'determinism', 'free', 'will', 'qualia', 'sentience',
            'paradox', 'infinite', 'eternal', 'absolute', 'relative',
            'moral', 'ethical', 'aesthetic', 'virtue', 'wisdom',
            'purpose', 'destiny', 'fate', 'soul', 'spirit', 'mind',
            'nature', 'universe', 'cosmos', 'void', 'nothingness',
            'absurd', 'nihilism', 'existential', 'dualism', 'monism',
            'phenomenology', 'hermeneutics', 'dialectic', 'synthesis',
            'a priori', 'posteriori', 'noumenon', 'phenomenon',
        },
        'patterns': [
            r'\b(what is the nature of|what does it mean to)\b',
            r'\b(is it possible that|can we ever truly)\b',
            r'\b(the question of|the problem of|the nature of)\b',
            r'\b(fundamentally|ultimately|essentially)\b',
        ],
    },
}


class ToneDetector:
    """
    Classifies input into one of 4 registers:
    casual / conversational / analytical / philosophical.
    Uses VADER sentiment data + deep marker word set.
    """

    def __init__(self):
        self.detection_count = 0
        self.register_history: List[str] = []

    def detect(self, text: str, sentiment: Dict = None) -> Dict:
        text_lower = text.lower()
        words = set(re.findall(r'\b[a-z]+\b', text_lower))

        scores = {}
        for register, markers in REGISTER_MARKERS.items():
            word_hits = len(words & markers['words'])
            pattern_hits = sum(
                1 for p in markers['patterns']
                if re.search(p, text_lower, re.IGNORECASE)
            )
            scores[register] = word_hits * 1.0 + pattern_hits * 2.0

        if sentiment:
            intensity = sentiment.get('emotional_intensity', 0)
            compound = sentiment.get('compound', 0)

            if intensity > 0.5:
                scores['casual'] += 1.5
            if abs(compound) < 0.15:
                scores['analytical'] += 1.0
                scores['philosophical'] += 0.5

        word_count = len(text.split())
        avg_word_len = sum(len(w) for w in words) / max(len(words), 1)

        if avg_word_len > 7:
            scores['analytical'] += 1.0
            scores['philosophical'] += 0.5
        elif avg_word_len < 4:
            scores['casual'] += 1.0

        if word_count > 30:
            scores['analytical'] += 0.5
            scores['philosophical'] += 0.5
        elif word_count < 8:
            scores['casual'] += 0.5

        question_marks = text.count('?')
        if question_marks > 0:
            scores['conversational'] += 0.5
            if any(w in text_lower for w in ['why', 'what is', 'how can', 'nature of']):
                scores['philosophical'] += 1.0

        if not any(s > 0 for s in scores.values()):
            scores['conversational'] = 1.0

        total = sum(scores.values()) + 1e-10
        normalized = {k: v / total for k, v in scores.items()}

        detected = max(scores, key=scores.get)
        confidence = scores[detected] / total

        self.detection_count += 1
        self.register_history.append(detected)
        if len(self.register_history) > 50:
            self.register_history = self.register_history[-50:]

        # Calculate depth: 0-1 scale based on complexity and philosophical markers
        philo_markers = ['why', 'what is', 'how can', 'nature of', 'meaning', 'existence', 'consciousness', 'truth', 'reality', 'god', 'soul', 'mind', 'being', 'absolute', 'infinite', 'eternal', 'cosmos', 'universe']
        philo_count = sum(1 for w in philo_markers if w in text_lower)
        depth = min(1.0, 0.2 + (scores.get('philosophical', 0) * 0.1) + (philo_count * 0.08) + (avg_word_len / 20.0))

        # Calculate depth: 0-1 scale based on complexity and philosophical markers
        philo_markers = ['why', 'what is', 'how can', 'nature of', 'meaning', 'existence', 'consciousness', 'truth', 'reality', 'god', 'soul', 'mind', 'being', 'absolute', 'infinite', 'eternal', 'cosmos', 'universe']
        philo_count = sum(1 for w in philo_markers if w in text_lower)
        depth = min(1.0, 0.2 + (scores.get('philosophical', 0) * 0.1) + (philo_count * 0.08) + (avg_word_len / 20.0))

        return {
            'register': detected,
            'confidence': round(confidence, 4),
            'scores': {k: round(v, 4) for k, v in normalized.items()},
            'raw_scores': {k: round(v, 2) for k, v in scores.items()},
            'depth': round(depth, 2),
            'depth': round(depth, 2),
        }

    def get_dominant_register(self) -> str:
        if not self.register_history:
            return 'conversational'
        from collections import Counter
        counts = Counter(self.register_history[-10:])
        return counts.most_common(1)[0][0]

    def get_status(self) -> Dict:
        return {
            'detections': self.detection_count,
            'dominant_register': self.get_dominant_register(),
            'recent_registers': self.register_history[-5:],
        }


_instance = None
def detect_tone(text):
    global _instance
    if _instance is None:
        _instance = ToneDetector()
    return _instance.detect(text)
