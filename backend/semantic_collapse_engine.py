"""
Semantic Collapse Engine
Combines meaning narrowing with quantum wave function collapse analogy.
Drawn from PDF 1's semantic_collapse_engine.py — unique feature not in PDF 2.
"""

import random
import math
from typing import Dict, List, Tuple
from collections import defaultdict


class SemanticCollapseEngine:
    """
    Narrows meaning through iterative collapse, analogous to quantum wave function collapse.
    Each observation (word/concept encountered) reduces the superposition of possible meanings.
    """

    def __init__(self):
        self.semantic_field: Dict[str, float] = {}
        self.collapse_history: List[Dict] = []
        self.entropy = 1.0
        self.collapses = 0

        self._build_semantic_field()

    def _build_semantic_field(self):
        """Initialize the semantic superposition space."""
        concept_clusters = {
            'existence': ['being', 'reality', 'existence', 'presence', 'substance'],
            'mind': ['thought', 'cognition', 'awareness', 'perception', 'consciousness'],
            'time': ['moment', 'duration', 'sequence', 'past', 'future'],
            'relation': ['connection', 'pattern', 'structure', 'network', 'system'],
            'change': ['transformation', 'evolution', 'emergence', 'flow', 'process'],
            'knowledge': ['understanding', 'insight', 'comprehension', 'wisdom', 'truth'],
            'quantum': ['superposition', 'collapse', 'entanglement', 'coherence', 'wave'],
        }

        for cluster, words in concept_clusters.items():
            for word in words:
                self.semantic_field[word] = random.uniform(0.3, 1.0)

    def observe(self, concept: str) -> Dict:
        """
        Observing a concept collapses part of the semantic superposition.
        Related meanings become more definite; unrelated meanings become less probable.
        """
        if not self.semantic_field:
            return {'collapsed': False, 'entropy': self.entropy}

        concept_lower = concept.lower()

        reinforced = []
        suppressed = []

        for term, amplitude in list(self.semantic_field.items()):
            similarity = self._semantic_similarity(concept_lower, term)
            if similarity > 0.3:
                new_amplitude = min(1.0, amplitude + similarity * 0.2)
                self.semantic_field[term] = new_amplitude
                reinforced.append(term)
            else:
                new_amplitude = max(0.0, amplitude - 0.05)
                self.semantic_field[term] = new_amplitude
                if new_amplitude < 0.1:
                    suppressed.append(term)

        self.entropy = self._calculate_entropy()
        collapsed = self.entropy < 0.4
        self.collapses += 1

        event = {
            'concept': concept,
            'entropy': self.entropy,
            'collapsed': collapsed,
            'reinforced': reinforced[:3],
            'suppressed': suppressed[:3],
        }
        self.collapse_history.append(event)

        return event

    def _semantic_similarity(self, a: str, b: str) -> float:
        """Simple character-level semantic similarity."""
        if a == b:
            return 1.0
        if a in b or b in a:
            return 0.7
        shared = set(a) & set(b)
        union = set(a) | set(b)
        return len(shared) / len(union) if union else 0.0

    def _calculate_entropy(self) -> float:
        """Calculate Shannon entropy of the semantic field."""
        values = [v for v in self.semantic_field.values() if v > 0]
        if not values:
            return 0.0
        total = sum(values)
        normalized = [v / total for v in values]
        return -sum(p * math.log(p + 1e-10) for p in normalized) / math.log(len(normalized) + 1)

    def get_dominant_meanings(self, top_n: int = 5) -> List[Tuple[str, float]]:
        """Get the highest-probability meanings after collapse."""
        sorted_field = sorted(self.semantic_field.items(), key=lambda x: x[1], reverse=True)
        return sorted_field[:top_n]

    def reset_superposition(self):
        """Reset to full superposition (new conversation)."""
        self._build_semantic_field()
        self.entropy = 1.0
        self.collapse_history = []

    def get_status(self) -> Dict:
        dominant = self.get_dominant_meanings(3)
        return {
            'entropy': round(self.entropy, 4),
            'field_size': len(self.semantic_field),
            'collapses': self.collapses,
            'dominant_meanings': [{'term': t, 'amplitude': round(a, 3)} for t, a in dominant],
        }
