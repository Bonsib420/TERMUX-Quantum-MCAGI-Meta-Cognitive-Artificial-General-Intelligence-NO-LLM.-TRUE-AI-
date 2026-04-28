"""
Function Word Engine — Tier‑2 of the two‑tier meaning system.

For stopwords / function words, this engine builds a structural dossier:
  • frequency
  • typical preceding words (what tends to come before)
  • typical following words (what tends to come after)
  • sentence‑position distribution (start, middle, end)
  • inferred grammatical "job"

This runs alongside the content‑word tier (ConceptExtractor) and makes
the black‑box Markov transitions inspectable.

API:
  engine = FunctionWordEngine(stopwords_set)
  engine.update_from_sentence(list_of_words)
  dossier = engine.get_dossier("the")
  engine.save(path) / engine.load(path)
"""

import json
import os
from collections import defaultdict, Counter
from typing import Dict, List, Optional


class FunctionWordEngine:
    """Tracks structural statistics for function words."""

    def __init__(self, stopwords_set: Optional[set] = None):
        # If no stopwords provided, we'll use a default set (same as ConceptExtractor)
        if stopwords_set is None:
            from quantum_language_engine import ConceptExtractor
            stopwords_set = ConceptExtractor.STOPWORDS
        self.stopwords = stopwords_set
        self.stats = defaultdict(lambda: {
            'freq': 0,
            'preceding': Counter(),
            'following': Counter(),
            'position': Counter(),  # 'start', 'middle', 'end'
        })
        self.total_function_words = 0

    def update_from_sentence(self, words: List[str]):
        """Update statistics from a single sentence (list of words, lower‑cased)."""
        for i, word in enumerate(words):
            w_low = word.lower()
            if w_low not in self.stopwords:
                continue
            entry = self.stats[w_low]
            entry['freq'] += 1
            self.total_function_words += 1

            # Preceding word
            if i > 0:
                prev = words[i-1].lower()
                entry['preceding'][prev] += 1
            # Following word
            if i < len(words) - 1:
                nxt = words[i+1].lower()
                entry['following'][nxt] += 1
            # Position in sentence
            if i == 0:
                entry['position']['start'] += 1
            elif i == len(words) - 1:
                entry['position']['end'] += 1
            else:
                entry['position']['middle'] += 1

    def update_from_text(self, text: str):
        """Split text into sentences and update from each sentence."""
        # Simple sentence split
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        for sent in sentences:
            words = sent.split()
            if words:
                self.update_from_sentence(words)

    def get_dossier(self, word: str) -> Optional[Dict]:
        """Return a structured dossier for a function word."""
        w_low = word.lower()
        if w_low not in self.stats:
            return None
        entry = self.stats[w_low]
        return {
            'word': w_low,
            'role': 'function',
            'frequency': entry['freq'],
            'preceding_neighbors': dict(entry['preceding'].most_common(10)),
            'following_neighbors': dict(entry['following'].most_common(10)),
            'position_distribution': dict(entry['position']),
            'notes': self._infer_job(w_low),
        }

    def _infer_job(self, word: str) -> str:
        """Return a simple rule‑based description of the word's grammatical job."""
        if word in ('the', 'a', 'an'):
            return "Determiner: precedes noun phrases."
        if word in ('in', 'on', 'at', 'by', 'for', 'with', 'from', 'to'):
            return "Preposition: indicates spatial/temporal relation."
        if word in ('and', 'but', 'or', 'nor'):
            return "Conjunction: connects words or phrases."
        if word in ('not', 'no', 'never'):
            return "Negation: inverts the meaning of the following word/phrase."
        if word in ('is', 'are', 'was', 'were', 'be', 'been', 'being'):
            return "Copula: links subject to predicate."
        if word in ('will', 'would', 'could', 'should', 'may', 'might', 'can'):
            return "Modal verb: indicates modality (possibility, necessity, etc.)."
        return "Function word."

    def save(self, filepath: str):
        """Persist statistics to JSON."""
        data = {}
        for word, entry in self.stats.items():
            data[word] = {
                'freq': entry['freq'],
                'preceding': dict(entry['preceding']),
                'following': dict(entry['following']),
                'position': dict(entry['position']),
            }
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self, filepath: str) -> bool:
        """Load statistics from JSON. Returns True if successful."""
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            for word, d in data.items():
                entry = self.stats[word]
                entry['freq'] = d.get('freq', 0)
                entry['preceding'] = Counter(d.get('preceding', {}))
                entry['following'] = Counter(d.get('following', {}))
                entry['position'] = Counter(d.get('position', {}))
                self.total_function_words += entry['freq']
            return True
        except Exception:
            return False
