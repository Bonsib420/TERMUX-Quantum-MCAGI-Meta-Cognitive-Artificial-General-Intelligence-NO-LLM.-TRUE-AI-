"""
🔢 WORD EMBEDDINGS - Pure Python Implementation
===============================================
Word2Vec-style embeddings without external dependencies.

Implements Skip-gram with Negative Sampling (simplified).
Words are represented as dense vectors capturing semantic relationships.
Similar words have similar vectors.
"""

import math
import random
import re
import json
import os
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger("quantum_ai")


class WordEmbeddings:
    """
    Simple word embeddings trained on corpus.
    
    Uses co-occurrence matrix factorization (GloVe-style)
    which is more tractable than Skip-gram for CPU-only training.
    
    Algorithm:
    1. Build word co-occurrence matrix from corpus
    2. Apply PPMI (Positive PMI) weighting  
    3. Reduce dimensionality via truncated SVD approximation
    """
    
    def __init__(self, vector_size: int = 50, window: int = 5, min_count: int = 2):
        self.vector_size = vector_size
        self.window = window
        self.min_count = min_count
        
        self.word_to_id = {}
        self.id_to_word = {}
        self.vectors = {}  # word -> vector
        self.word_counts = Counter()
        self.cooccurrence = defaultdict(Counter)
        
        self.trained = False
        self.vocab_size = 0
    
    def build_vocab(self, texts: List[str]):
        """Build vocabulary from texts."""
        for text in texts:
            words = self._tokenize(text)
            self.word_counts.update(words)
        
        # Filter by min_count
        vocab = [w for w, c in self.word_counts.items() if c >= self.min_count]
        vocab.sort()
        
        self.word_to_id = {w: i for i, w in enumerate(vocab)}
        self.id_to_word = {i: w for w, i in self.word_to_id.items()}
        self.vocab_size = len(vocab)
        
        logger.info(f"Built vocabulary: {self.vocab_size} words")
    
    def build_cooccurrence(self, texts: List[str]):
        """Build co-occurrence matrix."""
        for text in texts:
            words = self._tokenize(text)
            words = [w for w in words if w in self.word_to_id]
            
            for i, center in enumerate(words):
                # Context window
                start = max(0, i - self.window)
                end = min(len(words), i + self.window + 1)
                
                for j in range(start, end):
                    if i != j:
                        context = words[j]
                        # Distance weighting (closer = higher weight)
                        distance = abs(i - j)
                        weight = 1.0 / distance
                        self.cooccurrence[center][context] += weight
        
        logger.info(f"Built co-occurrence matrix")
    
    def train(self, texts: List[str], iterations: int = 10):
        """
        Train embeddings using simplified GloVe-style algorithm.
        
        This is a lightweight approximation suitable for CPU training.
        """
        # Build vocab and co-occurrence
        self.build_vocab(texts)
        self.build_cooccurrence(texts)

        self._train_continued(iterations)

    def _train_continued(self, iterations):
        """Continuation of train — auto-extracted by self-evolution."""
        if self.vocab_size == 0:
            logger.warning("Empty vocabulary, cannot train")
            return

        # Initialize random vectors
        for word in self.word_to_id:
            self.vectors[word] = [random.gauss(0, 0.1) for _ in range(self.vector_size)]

        # Compute PPMI matrix and train
        total_count = sum(sum(v.values()) for v in self.cooccurrence.values())
        word_probs = {w: self.word_counts[w] / sum(self.word_counts.values()) 
                      for w in self.word_to_id}

        # Stochastic gradient descent on weighted least squares
        learning_rate = 0.05

        for iteration in range(iterations):
            total_loss = 0
            updates = 0

            for word_i, contexts in self.cooccurrence.items():
                if word_i not in self.vectors:
                    continue

                vec_i = self.vectors[word_i]

                for word_j, count in contexts.items():
                    if word_j not in self.vectors:
                        continue

                    vec_j = self.vectors[word_j]

                    # Compute PPMI target
                    p_ij = count / total_count
                    p_i = word_probs.get(word_i, 1e-10)
                    p_j = word_probs.get(word_j, 1e-10)
                    pmi = math.log(p_ij / (p_i * p_j) + 1e-10)
                    ppmi = max(0, pmi)

                    # Dot product prediction
                    dot = sum(a * b for a, b in zip(vec_i, vec_j))

                    # Error
                    error = dot - ppmi

                    # Weight by co-occurrence frequency
                    weight = min(1.0, (count / 100) ** 0.75)

                    # Gradient update
                    for k in range(self.vector_size):
                        grad_i = weight * error * vec_j[k]
                        grad_j = weight * error * vec_i[k]

                        vec_i[k] -= learning_rate * grad_i
                        vec_j[k] -= learning_rate * grad_j

                    total_loss += weight * error ** 2
                    updates += 1

            if updates > 0:
                avg_loss = total_loss / updates
                if iteration % 3 == 0:
                    logger.info(f"Embedding training iteration {iteration}: loss={avg_loss:.4f}")

        # Normalize vectors
        for word in self.vectors:
            vec = self.vectors[word]
            norm = math.sqrt(sum(x*x for x in vec))
            if norm > 0:
                self.vectors[word] = [x/norm for x in vec]

        self.trained = True
        logger.info(f"Trained {len(self.vectors)} word vectors")

    
    def get_vector(self, word: str) -> Optional[List[float]]:
        """Get vector for a word."""
        return self.vectors.get(word.lower())
    
    def similarity(self, word1: str, word2: str) -> float:
        """Compute cosine similarity between two words."""
        vec1 = self.get_vector(word1)
        vec2 = self.get_vector(word2)
        
        if vec1 is None or vec2 is None:
            return 0.0
        
        # Cosine similarity (vectors already normalized)
        return sum(a * b for a, b in zip(vec1, vec2))
    
    def most_similar(self, word: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """Find most similar words."""
        vec = self.get_vector(word)
        if vec is None:
            return []
        
        similarities = []
        for other_word, other_vec in self.vectors.items():
            if other_word != word.lower():
                sim = sum(a * b for a, b in zip(vec, other_vec))
                similarities.append((other_word, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_n]
    
    def analogy(self, a: str, b: str, c: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Solve analogy: a is to b as c is to ?
        
        Uses vector arithmetic: result = vec(b) - vec(a) + vec(c)
        """
        vec_a = self.get_vector(a)
        vec_b = self.get_vector(b)
        vec_c = self.get_vector(c)
        
        if any(v is None for v in [vec_a, vec_b, vec_c]):
            return []
        
        # Compute target vector
        target = [b_i - a_i + c_i for a_i, b_i, c_i in zip(vec_a, vec_b, vec_c)]
        
        # Normalize
        norm = math.sqrt(sum(x*x for x in target))
        if norm > 0:
            target = [x/norm for x in target]
        
        # Find closest words (excluding inputs)
        exclude = {a.lower(), b.lower(), c.lower()}
        similarities = []
        
        for word, vec in self.vectors.items():
            if word not in exclude:
                sim = sum(t * v for t, v in zip(target, vec))
                similarities.append((word, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_n]
    
    def sentence_vector(self, text: str) -> Optional[List[float]]:
        """Get average vector for a sentence."""
        words = self._tokenize(text)
        vectors = [self.get_vector(w) for w in words if self.get_vector(w)]
        
        if not vectors:
            return None
        
        # Average
        result = [0.0] * self.vector_size
        for vec in vectors:
            for i, v in enumerate(vec):
                result[i] += v
        
        n = len(vectors)
        result = [x / n for x in result]
        
        # Normalize
        norm = math.sqrt(sum(x*x for x in result))
        if norm > 0:
            result = [x/norm for x in result]
        
        return result
    
    def sentence_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity between two sentences."""
        vec1 = self.sentence_vector(text1)
        vec2 = self.sentence_vector(text2)
        
        if vec1 is None or vec2 is None:
            return 0.0
        
        return sum(a * b for a, b in zip(vec1, vec2))
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text to words."""
        return re.findall(r'\b[a-z]+\b', text.lower())
    
    def save(self, filepath: str):
        """Save embeddings to file."""
        data = {
            'vectors': self.vectors,
            'word_to_id': self.word_to_id,
            'vocab_size': self.vocab_size,
            'vector_size': self.vector_size
        }
        with open(filepath, 'w') as f:
            json.dump(data, f)
        logger.info(f"Saved embeddings to {filepath}")
    
    def load(self, filepath: str) -> bool:
        """Load embeddings from file."""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                self.vectors = data['vectors']
                self.word_to_id = data['word_to_id']
                self.id_to_word = {int(i): w for w, i in self.word_to_id.items()}
                self.vocab_size = data['vocab_size']
                self.vector_size = data['vector_size']
                self.trained = True
                logger.info(f"Loaded {len(self.vectors)} embeddings")
                return True
        except Exception as e:
            logger.warning(f"Could not load embeddings: {e}")
        return False
    
    def get_stats(self) -> Dict:
        """Get embedding statistics."""
        return {
            'vocab_size': self.vocab_size,
            'vector_size': self.vector_size,
            'trained': self.trained,
            'total_vectors': len(self.vectors)
        }


# Singleton with lazy initialization
_embeddings = None
_embeddings_file = "/app/backend/word_embeddings.json"

def get_embeddings() -> WordEmbeddings:
    """Get or create word embeddings."""
    global _embeddings
    if _embeddings is None:
        _embeddings = WordEmbeddings(vector_size=50, window=5, min_count=2)
        
        # Try to load pre-trained
        if not _embeddings.load(_embeddings_file):
            # Train on corpus
            from training_corpus import get_corpus_sentences
            sentences = get_corpus_sentences()
            if sentences:
                _embeddings.train(sentences, iterations=15)
                _embeddings.save(_embeddings_file)
    
    return _embeddings


def train_embeddings_on_text(text: str):
    """Add new text to embeddings training."""
    embeddings = get_embeddings()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s for s in sentences if len(s) > 20]
    
    if sentences:
        embeddings.train(sentences, iterations=5)
        embeddings.save(_embeddings_file)
