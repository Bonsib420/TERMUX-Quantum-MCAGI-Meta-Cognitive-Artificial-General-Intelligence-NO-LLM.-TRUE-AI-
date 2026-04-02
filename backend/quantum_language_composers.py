"""
?? QUANTUM LANGUAGE ENGINE — Real Algorithms
=============================================
Replaces template-based generation with:
- Markov chain text generation (variable order 1-3)
- TF-IDF concept extraction
- Information-theoretic word selection
- Coherence scoring via PMI

Zero new dependencies required (uses numpy + stdlib).
Optional: markovify, nltk for enhanced generation.
"""

import re
import math
import random
import json
import os
import logging
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional

try:
    import numpy as np
except ImportError:
    np = None

logger = logging.getLogger("quantum_ai")


# ============================================================================
# MARKOV CHAIN ENGINE
# ============================================================================

class MarkovChain:
    """
    Variable-order Markov chain for text generation.
    
    Builds transition probability tables from training text.
    Generates novel sentences by walking the chain with weighted
    random selection. Supports orders 1-3 (bigram to 4-gram).
    
    Math: P(w_n | w_{n-1}, ..., w_{n-k}) = count(w_{n-k}...w_n) / count(w_{n-k}...w_{n-1})
    """
    
    def __init__(self, order: int = 2):
        self.order = min(max(order, 1), 3)
        self.chain = defaultdict(Counter)  # {prefix_tuple: Counter({suffix: count})}
        self.starters = []  # Sentence-starting prefixes
        self.trained = False
        self.total_tokens = 0
    
    def train(self, text: str):
        """Train the Markov chain on a corpus of text."""
        sentences = self._split_sentences(text)
        
        for sentence in sentences:
            words = sentence.split()
            if len(words) < self.order + 1:
                continue
            
            # Record sentence starter
            starter = tuple(words[:self.order])
            self.starters.append(starter)
            
            # Build transition table
            for i in range(len(words) - self.order):
                prefix = tuple(words[i:i + self.order])
                suffix = words[i + self.order]
                self.chain[prefix][suffix] += 1
                self.total_tokens += 1
        
        self.trained = len(self.chain) > 0
        logger.info(f"Markov chain trained: {len(self.chain)} states, {self.total_tokens} transitions")
    
    def generate(self, max_words: int = 30, seed_words: List[str] = None,
                 temperature: float = 1.0) -> str:
        """
        Generate a sentence by walking the Markov chain.
        
        Args:
            max_words: Maximum sentence length
            seed_words: Optional starting words (will find nearest prefix)
            temperature: Controls randomness (0.1=deterministic, 2.0=chaotic)
        
        Returns:
            Generated sentence string
        """
        if not self.trained or not self.starters:
            return ""
        
        # Pick starting prefix
        if seed_words and len(seed_words) >= self.order:
            prefix = tuple(seed_words[:self.order])
            if prefix not in self.chain:
                # Find closest matching prefix
                prefix = self._find_nearest_prefix(seed_words)
        else:
            prefix = random.choice(self.starters)
        
        words = list(prefix)
        
        for _ in range(max_words - self.order):
            current_prefix = tuple(words[-self.order:])
            
            if current_prefix not in self.chain:
                break
            
            # Get candidates and apply temperature
            candidates = self.chain[current_prefix]
            next_word = self._weighted_select(candidates, temperature)
            words.append(next_word)
            
            # Stop at sentence boundaries
            if next_word.endswith(('.', '?', '!')):
                break
        
        sentence = ' '.join(words)
        # Clean up punctuation spacing
        sentence = re.sub(r'\s+([.,;:!?])', r'\1', sentence)
        
        # Capitalize first letter
        if sentence:
            sentence = sentence[0].upper() + sentence[1:]
        
        return sentence
    
    def _weighted_select(self, candidates: Counter, temperature: float) -> str:
        """Select next word with temperature-controlled randomness."""
        words = list(candidates.keys())
        counts = list(candidates.values())
        
        if temperature == 0 or len(words) == 1:
            return words[counts.index(max(counts))]
        
        # Apply temperature: higher = more uniform, lower = more peaked
        weights = [c ** (1.0 / temperature) for c in counts]
        total = sum(weights)
        probs = [w / total for w in weights]
        
        if np is not None:
            return np.random.choice(words, p=probs)
        else:
            r = random.random()
            cumulative = 0
            for word, prob in zip(words, probs):
                cumulative += prob
                if r <= cumulative:
                    return word
            return words[-1]
    
    def _find_nearest_prefix(self, seed_words: List[str]) -> tuple:
        """Find the prefix in the chain most similar to seed words."""
        seed_set = set(w.lower() for w in seed_words)
        best_prefix = random.choice(self.starters)
        best_overlap = 0
        
        for prefix in self.chain.keys():
            prefix_set = set(w.lower().strip('.,;:!?') for w in prefix)
            overlap = len(seed_set & prefix_set)
            if overlap > best_overlap:
                best_overlap = overlap
                best_prefix = prefix
        
        return best_prefix
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Split on sentence-ending punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Clean and filter
        cleaned = []
        for s in sentences:
            s = s.strip()
            s = re.sub(r'\s+', ' ', s)
            if len(s.split()) >= 3:
                cleaned.append(s)
        return cleaned
    
    def get_perplexity(self, sentence: str) -> float:
        """
        Calculate perplexity of a sentence under this model.
        Lower = more likely under the model = more coherent.
        
        Math: PP = exp(-1/N * Σ log P(w_i | context))
        """
        words = sentence.split()
        if len(words) <= self.order:
            return float('inf')
        
        log_prob_sum = 0.0
        n_transitions = 0
        
        for i in range(len(words) - self.order):
            prefix = tuple(words[i:i + self.order])
            suffix = words[i + self.order]
            
            if prefix in self.chain:
                total = sum(self.chain[prefix].values())
                count = self.chain[prefix].get(suffix, 0)
                if count > 0:
                    log_prob_sum += math.log(count / total)
                else:
                    log_prob_sum += math.log(1e-10)  # Smoothing
            else:
                log_prob_sum += math.log(1e-10)
            n_transitions += 1
        
        if n_transitions == 0:
            return float('inf')
        
        return math.exp(-log_prob_sum / n_transitions)
    
    def save(self, filepath: str):
        """Serialize chain to JSON."""
        data = {
            'order': self.order,
            'chain': {' '.join(k): dict(v) for k, v in self.chain.items()},
            'starters': [' '.join(s) for s in self.starters],
            'total_tokens': self.total_tokens
        }
        with open(filepath, 'w') as f:
            json.dump(data, f)
    
    def load(self, filepath: str):
        """Load chain from JSON."""
        if not os.path.exists(filepath):
            return False
        with open(filepath, 'r') as f:
            data = json.load(f)
        self.order = data['order']
        self.chain = defaultdict(Counter)
        for k, v in data['chain'].items():
            self.chain[tuple(k.split())] = Counter(v)
        self.starters = [tuple(s.split()) for s in data['starters']]
        self.total_tokens = data.get('total_tokens', 0)
        self.trained = len(self.chain) > 0
        return True


# ============================================================================
# TF-IDF CONCEPT EXTRACTOR
# ============================================================================

class ConceptExtractor:
    """
    Extracts key concepts using TF-IDF scoring.
    
    Math: TF-IDF(t,d) = tf(t,d) × log(N / df(t))
    where tf = term frequency in document, N = total docs, df = docs containing term
    
    Also computes information content: IC(w) = -log P(w)
    Words with higher IC are more informative (rarer = more interesting).
    """
    
    # Common English stopwords — not concepts
    STOPWORDS = frozenset({
        'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was', 'were',
        'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'can', 'shall', 'of', 'to',
        'for', 'in', 'with', 'by', 'from', 'and', 'or', 'but', 'not', 'no', 'nor',
        'so', 'yet', 'both', 'either', 'neither', 'each', 'every', 'all', 'any',
        'few', 'more', 'most', 'other', 'some', 'such', 'than', 'too', 'very',
        'just', 'about', 'above', 'after', 'again', 'also', 'am', 'because',
        'before', 'between', 'come', 'did', 'down', 'during', 'get', 'go', 'got',
        'here', 'him', 'her', 'his', 'how', 'i', 'if', 'into', 'it', 'its',
        'know', 'let', 'like', 'make', 'me', 'much', 'my', 'new', 'now', 'off',
        'only', 'our', 'out', 'over', 'own', 'put', 'say', 'she', 'still',
        'take', 'tell', 'that', 'their', 'them', 'then', 'there', 'these', 'they',
        'this', 'those', 'through', 'under', 'up', 'us', 'use', 'want', 'way',
        'we', 'what', 'when', 'where', 'who', 'why', 'you', 'your',
        'good', 'bad', 'said', 'well', 'back', 'even', 'give', 'going', 'look',
        'right', 'think', 'yeah', 'yes', 'really', 'thing', 'things', 'something',
    })
    
    def __init__(self):
        self.document_frequencies = Counter()  # How many docs each word appears in
        self.total_documents = 0
        self.word_frequencies = Counter()  # Global word frequency for IC
        self.total_words = 0
    
    def update_corpus_stats(self, text: str):
        """Update corpus statistics with a new document."""
        words = self._tokenize(text)
        unique_words = set(words)
        
        self.total_documents += 1
        for word in unique_words:
            self.document_frequencies[word] += 1
        for word in words:
            self.word_frequencies[word] += 1
            self.total_words += 1
    
    def extract_concepts(self, text: str, max_concepts: int = 5) -> List[Dict]:
        """
        Extract key concepts from text using TF-IDF + information content.
        
        Returns list of {concept, score, ic} sorted by score descending.
        """
        words = self._tokenize(text)
        if not words:
            return []
        
        # Calculate TF for this text
        word_counts = Counter(words)
        total_words_in_doc = len(words)
        
        scored_concepts = []
        
        for word, count in word_counts.items():
            if word in self.STOPWORDS or len(word) < 3:
                continue
            
            # Term frequency (normalized)
            tf = count / total_words_in_doc
            
            # Inverse document frequency
            df = self.document_frequencies.get(word, 0)
            if self.total_documents > 0 and df > 0:
                idf = math.log(self.total_documents / df)
            else:
                idf = math.log(max(self.total_documents, 1) + 1)  # Novel word bonus
            
            tfidf = tf * idf
            
            # Information content: IC(w) = -log P(w)
            word_prob = self.word_frequencies.get(word, 1) / max(self.total_words, 1)
            ic = -math.log(max(word_prob, 1e-10))
            
            # Combined score: TF-IDF weighted by information content
            score = tfidf * (1 + 0.3 * ic / 10)
            
            scored_concepts.append({
                'concept': word,
                'score': score,
                'ic': ic,
                'tf': tf,
                'idf': idf
            })
        
        # Sort by score, return top N
        scored_concepts.sort(key=lambda x: x['score'], reverse=True)
        return scored_concepts[:max_concepts]
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercase words."""
        return re.findall(r'\b[a-z]+\b', text.lower())


# ============================================================================
# QUESTION GENERATION — Real Algorithms
# ============================================================================

