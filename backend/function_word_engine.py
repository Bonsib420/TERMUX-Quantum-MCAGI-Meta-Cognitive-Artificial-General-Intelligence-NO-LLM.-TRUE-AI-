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
        """
        Initialize the FunctionWordEngine with an optional set of function/stop words and prepare internal statistics.
        
        Parameters:
            stopwords_set (Optional[set]): Set of words to track as function/stop words. If omitted, a default stopword set is loaded from ConceptExtractor.STOPWORDS.
        
        Notes:
            Initializes these instance attributes:
            - stopwords: the provided or default stopword set
            - stats: defaultdict mapping each tracked word to a dict with keys `freq`, `preceding`, `following`, and `position`
            - total_function_words: aggregate frequency of all tracked function words
        """
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
        """
        Update the engine's statistics using the tokens of a single sentence.
        
        Processes the provided list of tokens (case-insensitive) and, for each token that is in the engine's configured stopword set, increments that word's frequency, updates counters for the immediately preceding and following tokens when present, and records whether the token occurred at the start, middle, or end of the sentence. Also increments the engine's aggregate total of tracked function words.
        
        Parameters:
            words (List[str]): Tokens comprising a sentence; tokens may be in any case and will be normalized to lowercase before processing.
        """
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
        """
        Split input text on periods into sentence-like segments, tokenize each segment on whitespace, and update the engine's word statistics from each resulting sentence.
        
        Parameters:
            text (str): Raw text containing one or more sentences (sentences are identified by '.' separators).
        """
        # Simple sentence split
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        for sent in sentences:
            words = sent.split()
            if words:
                self.update_from_sentence(words)

    def get_dossier(self, word: str) -> Optional[Dict]:
        """
        Produce a structured dossier for a tracked function word.
        
        Returns:
            dict: Dossier containing:
                - 'word': lowercased word
                - 'role': fixed string 'function'
                - 'frequency': total occurrences (int)
                - 'preceding_neighbors': dict of up to 10 preceding tokens with counts
                - 'following_neighbors': dict of up to 10 following tokens with counts
                - 'position_distribution': dict with counts for 'start', 'middle', 'end'
                - 'notes': short grammatical role label
            None: If the word has no recorded statistics.
        """
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
        """
        Provide a short grammatical-function label for a function/stop word.
        
        If the word matches a known class (determiner, preposition, conjunction, negation, copula, modal) the label names that class and gives a brief description; otherwise returns "Function word.".
        
        Returns:
        	A short human-readable label (str) describing the word's grammatical role.
        """
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
        """
        Persist collected function-word statistics to a JSON file at the given path.
        
        Parameters:
        	filepath (str): Destination file path. The function will create parent directories if needed and write a JSON object mapping each tracked word to a dictionary with keys `freq`, `preceding`, `following`, and `position` (all serializable primitives).
        """
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
        """
        Load saved function-word statistics from a JSON file into the engine.
        
        Merges stored per-word counts into the engine's internal stats, updating each word's
        frequency, preceding/following neighbor counters, position distribution, and
        incrementing the engine's total function-word count.
        
        Parameters:
            filepath (str): Path to a JSON file previously written by save().
        
        Returns:
            bool: `True` if the file was found and successfully loaded, `False` if the
            file does not exist or an error occurred while reading/parsing the file.
        """
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
