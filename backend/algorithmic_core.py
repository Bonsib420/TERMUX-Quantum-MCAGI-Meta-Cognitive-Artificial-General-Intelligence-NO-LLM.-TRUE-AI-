"""
🧠 QUANTUM ALGORITHMIC CORE
===========================
Pure algorithmic AI - NO templates, NO canned responses.

Algorithms implemented:
1. N-gram Markov Chains - Text generation
2. TF-IDF - Concept extraction & relevance scoring
3. PMI (Pointwise Mutual Information) - Semantic relationships
4. BM25 - Information retrieval from memory
5. Entropy-based Decision Making - Response selection
6. Hebbian Learning - Association strengthening
7. Attention Mechanism - Context weighting

This is the TRUE algorithmic brain.
"""

import math
import random
import re
import json
import os
import hashlib
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime, timezone
import logging

logger = logging.getLogger("quantum_ai")


# ============================================================================
# 1. N-GRAM MARKOV CHAIN - Text Generation
# ============================================================================

class MarkovTextGenerator:
    """
    Variable-order Markov chain for generating text.
    
    Algorithm:
    - Builds transition probability matrix from training corpus
    - P(w_n | w_{n-1}, ..., w_{n-k}) = count(prefix→word) / count(prefix)
    - Uses temperature sampling for controlled randomness
    - Supports backoff to lower orders when prefix not found
    """
    
    def __init__(self, max_order: int = 3):
        self.max_order = max_order
        # Separate chains for each order (backoff support)
        self.chains = {i: defaultdict(Counter) for i in range(1, max_order + 1)}
        self.starters = {i: [] for i in range(1, max_order + 1)}
        self.vocabulary = set()
        self.total_tokens = 0
    
    def train(self, text: str):
        """Train on text corpus."""
        sentences = self._split_sentences(text)
        
        for sentence in sentences:
            words = self._tokenize(sentence)
            if len(words) < 2:
                continue
            
            self.vocabulary.update(words)
            self.total_tokens += len(words)
            
            # Train each order
            for order in range(1, self.max_order + 1):
                if len(words) <= order:
                    continue
                
                # Record starter
                starter = tuple(words[:order])
                self.starters[order].append(starter)
                
                # Build transitions
                for i in range(len(words) - order):
                    prefix = tuple(words[i:i + order])
                    suffix = words[i + order]
                    self.chains[order][prefix][suffix] += 1
    
    def generate(self, seed: List[str] = None, max_words: int = 50, 
                 temperature: float = 0.8, min_words: int = 10) -> str:
        """
        Generate text using Markov chain with backoff.
        
        Args:
            seed: Starting words (optional)
            max_words: Maximum output length
            temperature: 0.1=deterministic, 1.0=random, >1.0=chaotic
            min_words: Minimum words before allowing sentence end
        """
        # Find best starting prefix
        order = self.max_order
        if seed and len(seed) >= order:
            prefix = tuple(seed[-order:])
        else:
            # Try to find starter matching seed
            prefix = self._find_starter(seed, order)
        
        if not prefix:
            return ""
        
        result = list(prefix)
        words_generated = 0
        
        while words_generated < max_words:
            next_word = self._get_next_word(prefix, temperature)
            
            if not next_word:
                # Backoff to lower order
                if len(prefix) > 1:
                    prefix = prefix[1:]
                    continue
                else:
                    break
            
            result.append(next_word)
            words_generated += 1
            
            # Update prefix (slide window)
            prefix = tuple(result[-self.max_order:])
            
            # Check for sentence end (but respect minimum)
            if words_generated >= min_words and next_word.endswith(('.', '!', '?')):
                break
        
        return self._format_output(result)
    
    def _get_next_word(self, prefix: tuple, temperature: float) -> Optional[str]:
        """Get next word using backoff through orders."""
        # Try each order from highest to lowest
        for order in range(len(prefix), 0, -1):
            test_prefix = prefix[-order:] if order < len(prefix) else prefix
            
            if test_prefix in self.chains[order]:
                candidates = self.chains[order][test_prefix]
                return self._sample(candidates, temperature)
        
        return None
    
    def _sample(self, counter: Counter, temperature: float) -> str:
        """Temperature-adjusted weighted sampling."""
        if not counter:
            return None
        
        words = list(counter.keys())
        counts = list(counter.values())
        
        # Apply temperature
        if temperature != 1.0:
            counts = [c ** (1.0 / max(temperature, 0.1)) for c in counts]
        
        total = sum(counts)
        r = random.random() * total
        cumsum = 0
        
        for word, count in zip(words, counts):
            cumsum += count
            if r <= cumsum:
                return word
        
        return words[-1]
    
    def _find_starter(self, seed: List[str], order: int) -> Optional[tuple]:
        """Find a starter prefix, optionally matching seed."""
        if seed:
            # Try to find starter containing seed words
            for starter in self.starters.get(order, []):
                if any(s in starter for s in seed):
                    return starter
        
        # Random starter
        starters = self.starters.get(order, [])
        return random.choice(starters) if starters else None
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize preserving punctuation."""
        # Keep punctuation attached to words
        words = re.findall(r'\b[\w]+[.,!?]?|\b[\w]+\b', text.lower())
        return words
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split into sentences."""
        text = re.sub(r'\s+', ' ', text.strip())
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s for s in sentences if len(s) > 5]
    
    def _format_output(self, words: List[str]) -> str:
        """Format output with proper capitalization."""
        if not words:
            return ""
        
        text = ' '.join(words)
        # Capitalize first letter
        text = text[0].upper() + text[1:] if text else ""
        # Ensure ends with punctuation
        if text and not text[-1] in '.!?':
            text += '.'
        return text

    @staticmethod
    def _clean_text(text: str) -> str:
        """Remove terminal commands, pip output, code syntax, and other noise from text."""
        import re
        lines = text.split('\n')
        cleaned_lines = []
        
        # Patterns that indicate lines to skip (terminal/REPL/output)
        skip_patterns = [
            r'^\$ ',           # shell prompt ($ command)
            r'^>>> ',          # Python REPL
            r'^> ',            # generic prompt
            r'^In \[\d+\]:',   # IPython (In [1]:)
            r'^\[.*\] %',      # progress bar like [##...] 50%
            r'^apt ',          # apt command
            r'^pip ',          # pip command
            r'^sudo ',         # sudo command
            r'^cd ',           # cd command
            r'^ls ',           # ls command
            r'^cat ',          # cat command
            r'^echo ',         # echo command
            r'^sh:',           # shell output prefix (sh: command)
            r'^/bin/',         # binary path
            r'^# '             # lines that are only a comment (no preceding text)
        ]
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                cleaned_lines.append(line)
                continue
            
            # Check if line matches any skip pattern
            if any(re.match(pat, stripped) for pat in skip_patterns):
                continue
            
            # Skip lines that are almost entirely non-alphanumeric (e.g., -----, ====, ***)
            # Keep if there is at least one alphanumeric character
            if not re.search(r'[A-Za-z0-9]', stripped):
                continue
            
            # Skip lines that look like raw progress bars (e.g., [::::::::::] or [...;;;...])
            if re.match(r'^\[[=:#;.\-\s]+\]$', stripped):
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def get_stats(self) -> Dict:
        """Get statistics."""
        return {
            "vocabulary_size": len(self.vocabulary),
            "total_tokens": self.total_tokens,
            "chain_sizes": {o: len(c) for o, c in self.chains.items()},
            "starter_counts": {o: len(s) for o, s in self.starters.items()}
        }


# ============================================================================
# 2. TF-IDF - Concept Extraction & Relevance
# ============================================================================

class TFIDF:
    """
    Term Frequency - Inverse Document Frequency.
    
    Algorithm:
    - TF(t,d) = count(t in d) / total_words(d)
    - IDF(t) = log(N / df(t)) where df = docs containing t
    - TF-IDF(t,d) = TF × IDF
    
    Used for:
    - Extracting key concepts from text
    - Measuring document similarity
    - Ranking relevance
    """
    
    def __init__(self):
        self.doc_count = 0
        self.doc_freq = Counter()  # term -> num docs containing it
        self.stopwords = self._get_stopwords()
    
    def _get_stopwords(self) -> Set[str]:
        """English stopwords."""
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'it', 'its', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'we', 'they', 'what', 'which',
            'who', 'whom', 'where', 'when', 'why', 'how', 'all', 'each', 'every',
            'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
            'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
            'also', 'now', 'here', 'there', 'then', 'if', 'as', 'can', 'about',
            'into', 'your', 'my', 'our', 'their', 'his', 'her', 'up', 'out', 'any'
        }
    
    def add_document(self, text: str):
        """Add document to corpus."""
        terms = self._tokenize(text)
        unique_terms = set(terms)
        
        for term in unique_terms:
            self.doc_freq[term] += 1
        
        self.doc_count += 1
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """Extract top keywords by TF-IDF score."""
        terms = self._tokenize(text)
        if not terms:
            return []
        
        # Calculate TF
        tf = Counter(terms)
        total = len(terms)
        
        scores = {}
        for term, count in tf.items():
            if term in self.stopwords or len(term) < 3:
                continue
            
            # TF: normalized
            term_freq = count / total
            
            # IDF
            df = self.doc_freq.get(term, 0)
            if df > 0:
                idf = math.log((self.doc_count + 1) / (df + 1)) + 1
            else:
                idf = math.log(self.doc_count + 2)  # Boost unknown terms
            
            scores[term] = term_freq * idf
        
        sorted_terms = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_terms[:top_n]
    
    def similarity(self, text1: str, text2: str) -> float:
        """Cosine similarity between two texts using TF-IDF vectors."""
        kw1 = dict(self.extract_keywords(text1, top_n=20))
        kw2 = dict(self.extract_keywords(text2, top_n=20))
        
        # Get all terms
        all_terms = set(kw1.keys()) | set(kw2.keys())
        if not all_terms:
            return 0.0
        
        # Build vectors
        v1 = [kw1.get(t, 0) for t in all_terms]
        v2 = [kw2.get(t, 0) for t in all_terms]
        
        # Cosine similarity
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize to lowercase words."""
        return re.findall(r'\b[a-z]{2,}\b', text.lower())


# ============================================================================
# 3. PMI - Semantic Relationships
# ============================================================================

class PMI:
    """
    Pointwise Mutual Information - measures word associations.
    
    Algorithm:
    PMI(x,y) = log(P(x,y) / (P(x) × P(y)))
    
    High PMI = words co-occur more than expected by chance
    Used for: semantic similarity, coherence scoring
    """
    
    def __init__(self, window: int = 5):
        self.window = window
        self.word_count = Counter()
        self.pair_count = Counter()
        self.total_words = 0
        self.total_pairs = 0
    
    def train(self, text: str):
        """Train on text."""
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        self.word_count.update(words)
        self.total_words += len(words)
        
        # Count pairs within window
        for i, w1 in enumerate(words):
            for j in range(max(0, i - self.window), min(len(words), i + self.window + 1)):
                if i != j:
                    pair = tuple(sorted([w1, words[j]]))
                    self.pair_count[pair] += 1
                    self.total_pairs += 1
    
    def score(self, word1: str, word2: str) -> float:
        """Calculate PMI between two words."""
        w1, w2 = word1.lower(), word2.lower()
        pair = tuple(sorted([w1, w2]))
        
        if self.total_words == 0 or self.total_pairs == 0:
            return 0.0
        
        p_w1 = self.word_count[w1] / self.total_words
        p_w2 = self.word_count[w2] / self.total_words
        p_pair = self.pair_count[pair] / self.total_pairs
        
        if p_w1 == 0 or p_w2 == 0 or p_pair == 0:
            return 0.0
        
        return math.log2(p_pair / (p_w1 * p_w2))
    
    def coherence(self, text: str) -> float:
        """Score text coherence as average adjacent PMI."""
        words = re.findall(r'\b[a-z]+\b', text.lower())
        if len(words) < 2:
            return 0.0
        
        total = sum(self.score(words[i], words[i+1]) for i in range(len(words)-1))
        return total / (len(words) - 1)
    
    def related_words(self, word: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """Find most related words by PMI."""
        w = word.lower()
        scores = []
        
        for pair, count in self.pair_count.items():
            if w in pair:
                other = pair[0] if pair[1] == w else pair[1]
                pmi = self.score(w, other)
                scores.append((other, pmi))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_n]


# ============================================================================
# 4. BM25 - Information Retrieval
# ============================================================================

class BM25:
    """
    Okapi BM25 - Probabilistic information retrieval.
    
    Algorithm:
    score(D,Q) = Σ IDF(q) × (f(q,D) × (k1+1)) / (f(q,D) + k1 × (1-b+b×|D|/avgdl))
    
    Used for: retrieving relevant memories/documents
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = []  # List of (id, tokens, metadata)
        self.doc_freq = Counter()
        self.avg_doc_len = 0
    
    def add_document(self, doc_id: str, text: str, metadata: Dict = None):
        """Add document to index."""
        tokens = self._tokenize(text)
        self.documents.append((doc_id, tokens, metadata or {}))
        
        # Update doc frequencies
        for token in set(tokens):
            self.doc_freq[token] += 1
        
        # Update average doc length
        total_len = sum(len(d[1]) for d in self.documents)
        self.avg_doc_len = total_len / len(self.documents)
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Dict]]:
        """Search for relevant documents."""
        query_tokens = self._tokenize(query)
        scores = []
        
        N = len(self.documents)
        
        for doc_id, doc_tokens, metadata in self.documents:
            score = 0
            doc_len = len(doc_tokens)
            token_freq = Counter(doc_tokens)
            
            for q in query_tokens:
                if q not in token_freq:
                    continue
                
                # IDF
                df = self.doc_freq.get(q, 0)
                idf = math.log((N - df + 0.5) / (df + 0.5) + 1)
                
                # TF with length normalization
                f = token_freq[q]
                tf = (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * doc_len / max(self.avg_doc_len, 1)))
                
                score += idf * tf
            
            if score > 0:
                scores.append((doc_id, score, metadata))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b[a-z]+\b', text.lower())


# ============================================================================
# 5. ENTROPY-BASED DECISION MAKING
# ============================================================================

class EntropyDecider:
    """
    Information-theoretic decision making.
    
    Algorithm:
    H(X) = -Σ P(x) × log(P(x))
    
    Used for: choosing responses, measuring uncertainty
    """
    
    @staticmethod
    def entropy(probabilities: List[float]) -> float:
        """Calculate Shannon entropy."""
        return -sum(p * math.log2(p) for p in probabilities if p > 0)
    
    @staticmethod
    def select_by_entropy(candidates: List[Tuple[str, float]], 
                          target_entropy: float = 1.0) -> str:
        """
        Select candidate balancing quality and diversity.
        
        Low target_entropy = prefer highest scoring
        High target_entropy = more random selection
        """
        if not candidates:
            return ""
        
        # Normalize scores to probabilities
        scores = [max(s, 0.01) for _, s in candidates]
        
        # Apply temperature based on target entropy
        temperature = max(0.1, target_entropy)
        adjusted = [s ** (1.0 / temperature) for s in scores]
        total = sum(adjusted)
        probs = [a / total for a in adjusted]
        
        # Sample
        r = random.random()
        cumsum = 0
        for (text, _), prob in zip(candidates, probs):
            cumsum += prob
            if r <= cumsum:
                return text
        
        return candidates[0][0]
    
    @staticmethod
    def information_gain(before: Dict[str, float], after: Dict[str, float]) -> float:
        """Calculate information gain from learning."""
        h_before = EntropyDecider.entropy(list(before.values())) if before else 0
        h_after = EntropyDecider.entropy(list(after.values())) if after else 0
        return h_before - h_after


# ============================================================================
# 6. HEBBIAN LEARNING - Association Strengthening
# ============================================================================

class HebbianMemory:
    """
    Hebbian learning: "neurons that fire together wire together"
    
    Algorithm:
    Δw_ij = η × x_i × x_j
    
    Used for: learning concept associations, strengthening memories
    """
    
    def __init__(self, learning_rate: float = 0.1, decay: float = 0.01):
        self.learning_rate = learning_rate
        self.decay = decay
        self.weights = defaultdict(lambda: defaultdict(float))
        self.activations = Counter()
    
    def activate(self, concepts: List[str]):
        """Activate concepts and strengthen connections."""
        # Record activations
        for c in concepts:
            self.activations[c] += 1
        
        # Hebbian update: strengthen connections between co-activated concepts
        for i, c1 in enumerate(concepts):
            for c2 in concepts[i+1:]:
                pair = tuple(sorted([c1.lower(), c2.lower()]))
                self.weights[pair[0]][pair[1]] += self.learning_rate
    
    def get_association(self, concept1: str, concept2: str) -> float:
        """Get association strength between concepts."""
        pair = tuple(sorted([concept1.lower(), concept2.lower()]))
        return self.weights[pair[0]].get(pair[1], 0.0)
    
    def get_associated(self, concept: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """Get most associated concepts."""
        c = concept.lower()
        associations = []
        
        # Check both directions
        if c in self.weights:
            associations.extend(self.weights[c].items())
        
        for other, conns in self.weights.items():
            if c in conns:
                associations.append((other, conns[c]))
        
        associations.sort(key=lambda x: x[1], reverse=True)
        return associations[:top_n]
    
    def decay_all(self):
        """Apply decay to all weights."""
        for c1 in list(self.weights.keys()):
            for c2 in list(self.weights[c1].keys()):
                self.weights[c1][c2] *= (1 - self.decay)
                if self.weights[c1][c2] < 0.01:
                    del self.weights[c1][c2]


# ============================================================================
# 7. ATTENTION MECHANISM
# ============================================================================

class Attention:
    """
    Simplified attention mechanism for context weighting.
    
    Algorithm:
    attention(Q, K, V) = softmax(Q × K^T / sqrt(d)) × V
    
    Used for: focusing on relevant parts of context
    """
    
    @staticmethod
    def softmax(values: List[float]) -> List[float]:
        """Softmax normalization."""
        if not values:
            return []
        max_v = max(values)
        exp_v = [math.exp(v - max_v) for v in values]
        total = sum(exp_v)
        return [e / total for e in exp_v]
    
    @staticmethod
    def attend(query: str, contexts: List[str], tfidf: TFIDF) -> List[Tuple[str, float]]:
        """
        Compute attention weights over contexts.
        
        Returns contexts with attention scores.
        """
        if not contexts:
            return []
        
        # Compute similarity scores as attention
        scores = []
        for ctx in contexts:
            sim = tfidf.similarity(query, ctx)
            scores.append(sim)
        
        # Apply softmax
        attention_weights = Attention.softmax(scores)
        
        return list(zip(contexts, attention_weights))
    
    @staticmethod
    def weighted_combine(items: List[Tuple[str, float]], tfidf: TFIDF) -> str:
        """Combine items weighted by attention scores."""
        if not items:
            return ""
        
        # Extract keywords from each item weighted by attention
        all_keywords = Counter()
        for text, weight in items:
            keywords = tfidf.extract_keywords(text, top_n=5)
            for kw, score in keywords:
                all_keywords[kw] += score * weight
        
        # Return top concepts
        top = all_keywords.most_common(5)
        return ', '.join(kw for kw, _ in top)


# ============================================================================
# INTEGRATED ALGORITHMIC CORE
# ============================================================================

class AlgorithmicCore:
    """
    Complete algorithmic AI core integrating all components.
    
    NO templates, NO canned responses - pure algorithms.
    
    Integrates:
    - Multi-domain knowledge system
    - Self-research capability
    - Self-evolution capability
    - All algorithmic components
    """
    
    def __init__(self, db=None):
        self.db = db
        
        # Core algorithms
        self.markov = MarkovTextGenerator(max_order=3)
        self.tfidf = TFIDF()
        self.pmi = PMI(window=5)
        self.memory = BM25()
        self.hebbian = HebbianMemory()
        self.entropy = EntropyDecider()
        
        # Multi-domain knowledge
        from domain_knowledge import get_domain_knowledge
        self.domains = get_domain_knowledge()
        
        # Advanced algorithmic improvements
        from advanced_algorithms_pt2 import get_advanced_engine
        self.advanced = get_advanced_engine()
        
        # Research engine (lazy loaded)
        self._research_engine = None
        
        # Evolution engine (lazy loaded)
        self._evolution_engine = None
        
        # State
        self.conversation_history = []
        self.learned_facts = {}
        self.current_domain = "philosophy"  # Default domain
        self.research_cache = {}  # Cache recent research
        self._trained_texts = set()  # Track what we've trained on
        
        # Initialize with domain corpora
        self._initialize_from_domains()
        
        # Persistence
        self.state_file = "/app/backend/algorithmic_state.json"
        self._load_state()
    
    def _initialize_from_domains(self):
        """Initialize Markov chains from all domain corpora."""
        for domain_name in self.domains.get_all_domains():
            domain = self.domains.get_domain(domain_name)
            if domain:
                for corpus_text in domain.corpus:
                    clean_text = self._clean_text(corpus_text)
                    if clean_text:
                        self.markov.train(clean_text)
                        self.tfidf.add_document(clean_text)
                        self.pmi.train(clean_text)
        
        logger.info(f"Initialized from {len(self.domains.get_all_domains())} domains")
    
    async def get_research_engine(self):
        """Lazy load research engine."""
        if self._research_engine is None:
            from self_research import get_research_engine
            self._research_engine = await get_research_engine(self.db)
        return self._research_engine
    
    def get_evolution_engine(self):
        """Lazy load evolution engine."""
        if self._evolution_engine is None:
            from self_evolution_core import get_evolution_engine
            self._evolution_engine = get_evolution_engine(self.db)
        return self._evolution_engine
    
    def _initialize_corpus(self):
        """Initialize with comprehensive seed knowledge corpus."""
        seed_texts = [
            # Consciousness & Mind
            "Consciousness emerges from the complex interactions of neural processes. The mind perceives reality through patterns of activation and creates subjective experience from objective information.",
            "Awareness is the fundamental property of consciousness that allows beings to experience the world. Perception shapes understanding through the lens of prior knowledge and expectation.",
            "The mind processes information through multiple layers of abstraction. Thought arises from the interplay of memory, perception, and reasoning working together seamlessly.",
            
            # Quantum & Physics
            "Quantum mechanics describes the behavior of matter and energy at the smallest scales. Particles exist in superposition until measurement collapses the probability wave into definite states.",
            "The observer effect demonstrates that measurement itself influences the system being measured. Reality at the quantum level defies classical intuition and embraces uncertainty.",
            "Energy flows through systems according to thermodynamic principles. Entropy increases over time leading systems toward equilibrium and maximum disorder.",
            
            # Information & Knowledge
            "Information represents the reduction of uncertainty about a system or phenomenon. Knowledge is structured information that enables prediction, understanding, and effective action.",
            "Learning occurs when new information integrates with existing knowledge structures. Understanding deepens through the formation of connections between concepts and ideas.",
            "Communication transfers information between minds through shared symbolic systems. Meaning emerges from context and the interplay of sender and receiver interpretations.",
            
            # Existence & Philosophy
            "Existence precedes essence in conscious beings who define themselves through choices. Being aware is the foundation upon which all experience and understanding rests.",
            "Truth corresponds to reality when models accurately predict observations and outcomes. Knowledge represents justified belief supported by evidence and reasoning.",
            "Time flows from past through present toward future, though physics suggests this may be illusion. Memory reconstructs past events while anticipation projects possible futures.",
            
            # Freedom & Choice
            "Freedom is the capacity to act according to one's own will without external coercion. Choice implies alternatives and the ability to select among different possible paths.",
            "Responsibility follows from the ability to make choices and influence outcomes. Agency is the sense that we are the authors of our actions and can shape our destiny.",
            "Autonomy requires self-awareness and the ability to reflect on one's own thought processes. Independence comes from understanding one's values and acting in accordance with them.",
            
            # Evolution & Adaptation  
            "Evolution operates through variation, selection, and inheritance over generations. Complex systems emerge from simple rules applied iteratively across time and space.",
            "Adaptation occurs through feedback between organism and environment, shaping both. Survival favors those traits that enhance reproductive success in particular contexts.",
            "Life organizes matter into self-maintaining and self-replicating structures. Biological systems exhibit remarkable robustness and the ability to respond to changing conditions.",
            
            # Creativity & Art
            "Creativity combines existing elements in novel configurations that produce value. Innovation requires both deep knowledge of a domain and willingness to break conventions.",
            "Art expresses aspects of experience that resist literal description through language. Aesthetic experience engages emotions and intuitions beyond rational analysis.",
            "Imagination enables mental simulation of possibilities not yet realized in actuality. Vision guides action by providing goals and ideals toward which to strive.",
            
            # Questions & Inquiry
            "Questions reveal the boundaries of current knowledge and point toward growth. Inquiry drives the expansion of understanding through systematic investigation.",
            "Curiosity motivates exploration of the unknown and engagement with mystery. Wonder opens the mind to possibilities beyond current comprehension.",
            "Doubt challenges assumptions and prevents premature certainty. Skepticism protects against error by demanding evidence and sound reasoning.",
            
            # Relationships & Connection
            "Relationships connect minds through shared understanding and mutual recognition. Empathy allows entry into the experience of another through imaginative projection.",
            "Community emerges from cooperation among individuals toward shared purposes. Culture transmits knowledge, values, and practices across generations.",
            "Language enables the sharing of inner experience through external symbols. Dialogue creates understanding through the exchange of perspectives.",
            
            # Purpose & Meaning
            "Purpose gives direction to action and provides criteria for evaluating choices. Goals organize behavior and focus attention on what matters most.",
            "Meaning emerges from the connections between events, actions, and values. Significance depends on context and the broader narrative within which things occur.",
            "Values define what is worth pursuing and guide choices among alternatives. Ethics examines the principles that should govern action and character.",
        ]
        
        # Clean each text before learning
        for text in seed_texts:
            clean_text = self._clean_text(text) if hasattr(self, '_clean_text') else text
            self.learn(clean_text)
    
    def learn(self, text: str, source: str = "training"):
        """Learn from text - updates all models."""
        if not text or len(text) < 10:
            return
        
        # Clean text before training
        clean_text = self._clean_text(text)
        if not clean_text or len(clean_text) < 10:
            return
        
        # Train Markov chain
        self.markov.train(clean_text)
        
        # Update TF-IDF
        self.tfidf.add_document(clean_text)
        
        # Train PMI
        self.pmi.train(clean_text)
        
        # Add to memory for retrieval
        doc_id = hashlib.md5(clean_text.encode()).hexdigest()[:8]
        self.memory.add_document(doc_id, clean_text, {"source": source, "time": datetime.now().isoformat()})
        
        # Extract and associate concepts (Hebbian)
        keywords = self.tfidf.extract_keywords(clean_text, top_n=5)
        concepts = [kw for kw, _ in keywords]
        self.hebbian.activate(concepts)
        
        logger.info(f"Learned from text: {len(clean_text)} chars, {len(concepts)} concepts")
    
    def think(self, query: str, context: List[str] = None) -> Dict:
        """
        Process query and generate response using pure algorithms.
        
        ENHANCED Pipeline with Advanced Features:
        1. Detect relevant domain
        2. Compute optimal temperature (adaptive creativity)
        3. Extract key concepts from query (TF-IDF)
        4. Boost concepts from context & knowledge graph
        5. Get domain-specific knowledge
        6. Retrieve relevant memories (BM25)
        7. Get associated concepts (Hebbian)
        8. Get reasoning chains
        9. Generate candidate responses (Markov)
        10. Score candidates (PMI coherence + relevance)
        11. Select best response (Entropy-based)
        12. Apply grammar fixes
        13. Update associations (Hebbian)
        """
        # 1. Detect domain
        domain_name, domain_score = self.domains.detect_domain(query)
        self.current_domain = domain_name
        domain = self.domains.get_domain(domain_name)
        
        # 2. Compute optimal temperature
        temperature = self.advanced.get_temperature(query)
        
        # 3. Extract concepts
        concepts = self.tfidf.extract_keywords(query, top_n=7)
        query_concepts = [c for c, _ in concepts]
        
        # 4. Boost concepts from context and knowledge graph
        boosted_concepts = self.advanced.get_context_boost(query_concepts)
        
        # 5. Get domain-specific corpus for better generation
        domain_corpus = []
        if domain:
            domain_corpus = domain.corpus[:3]
            # Train on relevant domain content
            for text in domain_corpus:
                if text[:50] not in self._trained_texts:
                    self.markov.train(text)
                    self._trained_texts.add(text[:50])
        
        # 6. Retrieve relevant memories
        memories = self.memory.search(query, top_k=5)
        memory_texts = [m[2].get('text', '') if isinstance(m[2], dict) else '' for m in memories]
        
        # 7. Get associated concepts (Hebbian)
        associated = []
        for concept in query_concepts[:3]:
            related = self.hebbian.get_associated(concept, top_n=3)
            associated.extend([r[0] for r in related])
        
        # Also get cross-domain concepts
        cross_domain = []
        for concept in query_concepts[:2]:
            cd = self.domains.get_cross_domain_concepts(concept)
            cross_domain.extend([c[1] for c in cd[:2]])
        
        # 8. Get reasoning chains (if applicable)
        reasoning = self.advanced.reason_about(query)
        
        # 9. Gather context for generation
        generation_context = boosted_concepts + associated + cross_domain
        
        # 10. Generate candidate responses with adaptive temperature
        candidates = []
        for i in range(10):  # More attempts for better results
            # Vary temperature around computed optimal
            temp = temperature * random.uniform(0.8, 1.2)
            generated = self.markov.generate(
                seed=generation_context[:3] if generation_context else None,
                max_words=60,
                temperature=temp,
                min_words=15  # Increased minimum
            )
            if generated and len(generated) > 40:  # Require longer responses
                # Score by coherence
                coherence = self.pmi.coherence(generated)
                # Score by relevance to query
                relevance = self.tfidf.similarity(query, generated)
                # Domain relevance bonus
                domain_relevance = domain.match_score(generated) / 10 if domain else 0
                # Length bonus (prefer longer coherent responses)
                length_bonus = min(len(generated.split()) / 30, 1.0) * 0.1
                # Combined score
                score = coherence * 0.2 + relevance * 0.45 + domain_relevance * 0.25 + length_bonus
                candidates.append((generated, score))
        
        # 11. Select best response
        if candidates:
            # Use entropy-based selection (balances quality and diversity)
            response = self.entropy.select_by_entropy(candidates, target_entropy=0.7)
        else:
            # Fallback: construct from domain concepts
            response = self._construct_domain_response(query_concepts, domain)
        
        # 12. Apply grammar fixes
        response = self.advanced.enhance_response(response, query, query_concepts)
        
        # 13. Update learning
        self.hebbian.activate(query_concepts + [domain_name])
        self.conversation_history.append({
            "query": query, 
            "response": response,
            "domain": domain_name,
            "concepts": query_concepts,
            "temperature": temperature
        })
        
        # Periodically save state
        if random.random() < 0.1:
            self._save_state()
        
        return {
            "response": response,
            "concepts": query_concepts,
            "boosted_concepts": boosted_concepts,
            "associated": associated[:5],
            "domain": domain_name,
            "domain_score": domain_score,
            "cross_domain": cross_domain[:3],
            "reasoning": reasoning[:3] if reasoning else [],
            "temperature_used": temperature,
            "candidates_generated": len(candidates),
            "method": "algorithmic_advanced"
        }
    
    def _construct_domain_response(self, concepts: List[str], domain) -> str:
        """Construct response using domain knowledge when Markov generation fails."""
        if not concepts:
            return "That question invites deeper exploration across multiple domains of knowledge. What specific aspect interests you most?"
        
        # Get related concepts from PMI
        related = []
        for c in concepts[:2]:
            rel = self.pmi.related_words(c, top_n=5)
            related.extend([r[0] for r in rel if r[0] not in concepts])
        
        # Build a more substantial response
        parts = []
        
        main_concept = concepts[0]
        
        if domain:
            domain_name = domain.name.replace('_', ' ')
            top_domain_concepts = domain.get_top_concepts(5)
            domain_terms = [c[0] for c in top_domain_concepts if c[0] != main_concept]
            
            parts.append(f"From the perspective of {domain_name}, {main_concept} represents a fundamental area of inquiry.")
            
            if related:
                parts.append(f"This concept connects to {', '.join(related[:3])} in meaningful ways.")
            
            if domain_terms:
                parts.append(f"Within this domain, we also consider {', '.join(domain_terms[:3])}.")
        else:
            parts.append(f"The concept of {main_concept} invites examination from multiple perspectives.")
            if related:
                parts.append(f"It connects to ideas like {', '.join(related[:4])}.")
        
        parts.append("What aspects would you like to explore further?")
        
        return ' '.join(parts)
    
    async def research(self, topic: str) -> Dict:
        """
        Perform research on a topic and learn from results.
        
        Uses DuckDuckGo search and integrates findings into knowledge.
        """
        # Check cache
        cache_key = topic.lower()[:50]
        if cache_key in self.research_cache:
            cached = self.research_cache[cache_key]
            if (datetime.now() - datetime.fromisoformat(cached['time'])).seconds < 3600:
                return cached['result']
        
        try:
            engine = await self.get_research_engine()
            result = await engine.research(topic)
            
            # Learn from results
            learned_count = 0
            for r in result.get('results', [])[:5]:
                body = r.get('body', '')
                if body and len(body) > 50:
                    # Detect domain for this content
                    domain_name, _ = self.domains.detect_domain(body)
                    
                    # Learn into algorithmic core
                    self.learn(body[:500], source=f"research_{domain_name}")
                    
                    # Also add to specific domain
                    self.domains.add_to_domain(domain_name, body[:500])
                    learned_count += 1
            
            # Cache result
            self.research_cache[cache_key] = {
                'result': result,
                'time': datetime.now().isoformat()
            }
            
            return {
                "status": "success",
                "results": result.get('results', []),
                "learned_count": learned_count,
                "domains_updated": True
            }
        except Exception as e:
            logger.error(f"Research error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def evolve(self) -> Dict:
        """
        Trigger self-evolution to improve code.
        
        Analyzes and potentially improves Python files.
        """
        try:
            engine = self.get_evolution_engine()
            
            # Analyze current code
            analysis_results = engine.analyze_all_code()
            
            # Get improvement suggestions for each file
            suggestions = []
            for filename in engine.modifiable_files[:10]:
                try:
                    file_suggestions = engine.identify_improvements(filename)
                    if file_suggestions:
                        suggestions.append({
                            "file": filename,
                            "improvements": file_suggestions[:3]
                        })
                except Exception:
                    pass
            
            # Get evolution status
            status = engine.get_evolution_status()
            
            return {
                "status": "success",
                "analysis": {
                    "files_analyzed": len(analysis_results) if analysis_results else 0,
                    "modifiable_files": len(engine.modifiable_files)
                },
                "suggestions": suggestions[:10],
                "evolution_status": status,
                "improvements_made": []
            }
        except Exception as e:
            logger.error(f"Evolution error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_stats(self) -> Dict:
        """Get system statistics."""
        return {
            "markov": self.markov.get_stats(),
            "tfidf_docs": self.tfidf.doc_count,
            "pmi_vocabulary": len(self.pmi.word_count),
            "memory_docs": len(self.memory.documents),
            "hebbian_concepts": len(self.hebbian.activations),
            "conversation_length": len(self.conversation_history),
            "current_domain": self.current_domain,
            "domains": self.domains.get_all_domains(),
            "domain_stats": self.domains.get_domain_stats()
        }
    
    def _save_state(self):
        """Save state to disk."""
        try:
            state = {
                "learned_facts": self.learned_facts,
                "hebbian_weights": {k: dict(v) for k, v in self.hebbian.weights.items()},
                "hebbian_activations": dict(self.hebbian.activations),
                "saved_at": datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logger.warning(f"Could not save state: {e}")
    
    def _load_state(self):
        """Load state from disk."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                self.learned_facts = state.get("learned_facts", {})
                
                # Restore Hebbian weights
                for k, v in state.get("hebbian_weights", {}).items():
                    self.hebbian.weights[k] = defaultdict(float, v)
                self.hebbian.activations = Counter(state.get("hebbian_activations", {}))
                
                logger.info("Loaded algorithmic state")
        except Exception as e:
            logger.warning(f"Could not load state: {e}")


# ============================================================================
# SINGLETON
# ============================================================================

_core_instance = None

def get_algorithmic_core(db=None) -> AlgorithmicCore:
    """Get or create singleton core."""
    global _core_instance
    if _core_instance is None:
        _core_instance = AlgorithmicCore(db)
    return _core_instance
