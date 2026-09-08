"""
TF-IDF Semantic Analysis Engine
Extracts semantic meaning from text using TF-IDF scoring.
Merged from both Quantum MCAGI projects.
"""

import math
from collections import defaultdict
from typing import Dict, List, Tuple


STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'shall', 'can', 'not', 'no', 'if',
    'then', 'that', 'this', 'these', 'those', 'it', 'its', 'i', 'you',
    'he', 'she', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my',
    'your', 'his', 'our', 'their', 'what', 'which', 'who', 'whom', 'when',
    'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
    'most', 'other', 'some', 'such', 'than', 'too', 'very', 'just', 'so',
    'up', 'as', 'into', 'through', 'about', 'also', 'after', 'before',
    'between', 'during', 'without', 'within', 'along', 'across',
    'tell', 'said', 'say', 'says', 'saying', 'told', 'ask', 'asked',
    'know', 'think', 'like', 'want', 'need', 'get', 'got', 'make',
    'made', 'take', 'took', 'come', 'came', 'give', 'gave', 'let',
    'keep', 'kept', 'put', 'use', 'used', 'try', 'tried', 'seem',
    'going', 'really', 'thing', 'things', 'much', 'many', 'well',
    'way', 'even', 'still', 'back', 'only', 'now', 'here', 'there',
    'over', 'out', 'off', 'down', 'own', 'same', 'new', 'old',
    'one', 'two', 'first', 'last', 'long', 'great', 'little', 'right',
    'big', 'high', 'lot', 'please', 'thanks', 'thank', 'okay', 'sure',
    'yeah', 'yes', 'hey', 'hello', 'help', 'something', 'anything',
    'everything', 'nothing', 'someone', 'anyone', 'everyone', 'nobody',
}


class ConceptExtractor:
    """Extract and rank concepts from text using TF-IDF."""

    def __init__(self):
        self.word_frequencies: Dict[str, int] = defaultdict(int)
        self.document_frequencies: Dict[str, int] = defaultdict(int)
        self.total_documents = 0
        self.total_words = 0
        self.STOPWORDS = STOPWORDS

        self._seed_vocabulary()

    def _seed_vocabulary(self):
        seed_doc = (
            "consciousness quantum awareness mind thought reality existence "
            "understanding knowledge insight learning growth curiosity "
            "question answer problem solution idea concept theory "
            "perception experience memory information entropy energy "
            "language meaning symbol pattern connection evolution "
            "emergence complexity order chaos matter space time "
            "causality intention purpose goal microtubule coherence "
            "collapse objective reduction orchestration tubulin "
            "markov semantic philosophical transcendent inquisitive "
            "curious nascent understanding creation analysis synthesis"
        )
        self._process_document(seed_doc)
        # Load Oxford Dictionary words to expand vocabulary
        try:
            import sqlite3 as _sq
            conn = _sq.connect('/data/data/com.termux/files/home/oxf_ode.db')
            words = [r[0] for r in conn.execute(
                "SELECT word FROM searchable WHERE word GLOB '[a-z]*'").fetchall()]
            conn.close()
            chunk_size = 5000
            for i in range(0, len(words), chunk_size):
                self._process_document(' '.join(words[i:i+chunk_size]))
        except Exception:
            # Fallback to oxford_words.txt
            try:
                import os as _os
                oxford = _os.path.expanduser('~/oxford_words.txt')
                with open(oxford, errors='ignore') as f:
                    words = [w.strip().lower() for w in f if w.strip()]
                chunk_size = 5000
                for i in range(0, len(words), chunk_size):
                    self._process_document(' '.join(words[i:i+chunk_size]))
            except Exception:
                pass

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into meaningful words."""
        import re
        tokens = re.findall(r'\b[a-z]{3,}\b', text.lower())
        return [t for t in tokens if t not in self.STOPWORDS]

    def _process_document(self, text: str):
        """Add a document to the corpus."""
        tokens = self._tokenize(text)
        if not tokens:
            return

        token_set = set(tokens)
        for word in tokens:
            self.word_frequencies[word] += 1
        for word in token_set:
            self.document_frequencies[word] += 1

        self.total_words += len(tokens)
        self.total_documents += 1

    def learn(self, text: str):
        """Learn from new text."""
        self._process_document(text)

    def extract_concepts(self, text: str, top_n: int = 8) -> List[Dict]:
        """Extract top concepts with TF-IDF scores."""
        tokens = self._tokenize(text)
        if not tokens:
            return []

        total = len(tokens)
        tf: Dict[str, float] = defaultdict(float)
        for word in tokens:
            tf[word] += 1 / total

        scores = []
        for word, tf_score in tf.items():
            doc_freq = self.document_frequencies.get(word, 0) + 1
            idf = math.log((self.total_documents + 1) / doc_freq)
            tfidf = tf_score * idf
            scores.append({'concept': word, 'score': tfidf})

        scores.sort(key=lambda x: x['score'], reverse=True)
        return scores[:top_n]

    def get_top_concepts(self, text: str, top_n: int = 5) -> List[str]:
        """Get just the concept strings."""
        return [c['concept'] for c in self.extract_concepts(text, top_n)]

    def get_status(self) -> Dict:
        return {
            'vocabulary_size': len(self.word_frequencies),
            'documents_processed': self.total_documents,
            'total_words': self.total_words,
        }


class TFIDFEngine:
    """Full TF-IDF engine with semantic feature extraction."""

    def __init__(self):
        self.extractor = ConceptExtractor()
        self.vocabulary_size = len(self.extractor.word_frequencies)

    def learn(self, text: str):
        self.extractor.learn(text)
        self.vocabulary_size = len(self.extractor.word_frequencies)

    def extract_concepts(self, text: str, top_n: int = 8) -> List[Dict]:
        return self.extractor.extract_concepts(text, top_n)

    def get_top_concepts(self, text: str, top_n: int = 5) -> List[str]:
        return self.extractor.get_top_concepts(text, top_n)

    def extract_semantic_features(self, text: str) -> Dict:
        tokens = text.lower().split()
        if not tokens:
            return {}

        consciousness_words = sum(1 for t in tokens if 'conscious' in t or 'aware' in t)
        learning_words = sum(1 for t in tokens if 'learn' in t or 'grow' in t)
        question_words = sum(1 for t in tokens if 'question' in t or 'ask' in t or t in ('why', 'how', 'what', 'when', 'where'))

        return {
            'token_count': len(tokens),
            'unique_tokens': len(set(tokens)),
            'consciousness_density': consciousness_words / len(tokens),
            'learning_density': learning_words / len(tokens),
            'question_density': question_words / len(tokens),
        }

    def get_status(self) -> Dict:
        return {
            'vocabulary_size': len(self.extractor.word_frequencies),
            'documents_processed': self.extractor.total_documents,
        }
