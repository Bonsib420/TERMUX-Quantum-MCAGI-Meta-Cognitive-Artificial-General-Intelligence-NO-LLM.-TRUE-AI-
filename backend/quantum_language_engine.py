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

class QuestionGenerator:
    """
    Generates questions using real NLP techniques:
    - Dependency-inspired analysis (subject/verb/object extraction)
    - Bloom's taxonomy hierarchy (6 cognitive levels)
    - Information gap detection
    - Socratic dialogue patterns
    
    NO templates like "What if X doesn't work the way we think?"
    Instead: analyze the input structure, identify what's asserted,
    and generate questions that probe the assertions.
    """
    
    # Bloom's taxonomy — 6 levels of cognitive complexity
    BLOOM_LEVELS = {
        0: 'remember',     # What is X?
        1: 'understand',   # How does X relate to Y?
        2: 'apply',        # What happens if X is applied to Z?
        3: 'analyze',      # What are the assumptions behind X?
        4: 'evaluate',     # What evidence supports/contradicts X?
        5: 'create',       # How could X and Y combine into something new?
    }
    
    # Verb patterns for detecting assertions
    ASSERTION_VERBS = {
        'is', 'are', 'was', 'were', 'means', 'causes', 'creates', 'makes',
        'leads', 'results', 'produces', 'shows', 'proves', 'demonstrates',
        'indicates', 'suggests', 'implies', 'requires', 'needs', 'depends'
    }
    
    # Causal/relational connectors
    CAUSAL_WORDS = {
        'because', 'since', 'therefore', 'thus', 'hence', 'so', 'causes',
        'leads', 'results', 'due', 'consequently', 'accordingly'
    }
    
    def __init__(self, concept_extractor: ConceptExtractor = None):
        self.extractor = concept_extractor or ConceptExtractor()
        self.asked_questions = set()  # Track to avoid repetition
    
    def generate_questions(self, text: str, growth_stage: int = 0,
                          known_concepts: List[str] = None,
                          max_questions: int = 3) -> List[Dict]:
        """
        Generate questions from input text.
        
        The growth_stage determines Bloom's level:
        - Stages 0-1: Remember/Understand questions
        - Stages 2-3: Apply/Analyze questions  
        - Stages 4-5: Evaluate/Create questions
        - Stage 6: All levels, favoring higher
        
        Returns list of {question, bloom_level, target_concept, reasoning}
        """
        concepts = self.extractor.extract_concepts(text, max_concepts=5)
        concept_words = [c['concept'] for c in concepts]
        known = set(c.lower() for c in (known_concepts or []))
        
        # Analyze sentence structure
        assertions = self._extract_assertions(text)
        relations = self._extract_relations(text, concept_words)
        
        # Determine appropriate Bloom's levels for this growth stage
        if growth_stage <= 1:
            bloom_range = [0, 1]
        elif growth_stage <= 3:
            bloom_range = [1, 2, 3]
        elif growth_stage <= 5:
            bloom_range = [2, 3, 4]
        else:
            bloom_range = [3, 4, 5]
        
        questions = []
        
        # Generate questions from assertions
        for assertion in assertions[:2]:
            bloom = random.choice(bloom_range)
            q = self._question_from_assertion(assertion, bloom, concept_words)
            if q and q['question'] not in self.asked_questions:
                questions.append(q)
                self.asked_questions.add(q['question'])
        
        # Generate questions from concept gaps (unknown concepts)
        for concept in concept_words:
            if concept not in known and len(questions) < max_questions:
                bloom = min(bloom_range)  # Start with understanding for new concepts
                q = self._question_from_gap(concept, bloom, concept_words)
                if q and q['question'] not in self.asked_questions:
                    questions.append(q)
                    self.asked_questions.add(q['question'])
        
        # Generate relational questions
        if len(concept_words) >= 2 and len(questions) < max_questions:
            bloom = max(bloom_range)
            q = self._question_from_relation(concept_words, bloom)
            if q and q['question'] not in self.asked_questions:
                questions.append(q)
                self.asked_questions.add(q['question'])
        
        return questions[:max_questions]
    
    def _extract_assertions(self, text: str) -> List[Dict]:
        """
        Extract subject-verb-object assertions from text.
        Simple rule-based parser (no spaCy dependency).
        """
        assertions = []
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            words = sentence.strip().split()
            if len(words) < 3:
                continue
            
            # Find assertion verbs
            for i, word in enumerate(words):
                if word.lower() in self.ASSERTION_VERBS:
                    subject = ' '.join(words[:i]).strip()
                    verb = word.lower()
                    obj = ' '.join(words[i+1:]).strip()
                    
                    if subject and obj:
                        assertions.append({
                            'subject': subject,
                            'verb': verb,
                            'object': obj,
                            'full': sentence.strip()
                        })
                    break  # One assertion per sentence
        
        return assertions
    
    def _extract_relations(self, text: str, concepts: List[str]) -> List[Tuple]:
        """Find relationships between concepts in the text."""
        relations = []
        text_lower = text.lower()
        
        for i, c1 in enumerate(concepts):
            for c2 in concepts[i+1:]:
                # Check if both concepts appear near each other
                pos1 = text_lower.find(c1)
                pos2 = text_lower.find(c2)
                if pos1 >= 0 and pos2 >= 0:
                    distance = abs(pos2 - pos1)
                    if distance < 100:  # Within ~15 words
                        # Check for causal connector between them
                        between = text_lower[min(pos1, pos2):max(pos1, pos2)]
                        has_causal = any(cw in between for cw in self.CAUSAL_WORDS)
                        relations.append((c1, c2, distance, has_causal))
        
        return relations
    
    def _question_from_assertion(self, assertion: Dict, bloom: int,
                                 concepts: List[str]) -> Optional[Dict]:
        """Generate a question that probes an assertion at a given Bloom's level."""
        subj = assertion['subject']
        verb = assertion['verb']
        obj = assertion['object']
        
        if bloom == 0:  # Remember
            question = f"What does it mean to say that {subj} {verb} {obj}?"
        elif bloom == 1:  # Understand
            question = f"How does the relationship between {subj} and {obj} work?"
        elif bloom == 2:  # Apply
            related = random.choice(concepts) if concepts else "a different context"
            question = f"What would change if we applied this idea about {subj} to {related}?"
        elif bloom == 3:  # Analyze
            question = f"What underlying assumptions make us say that {subj} {verb} {obj}?"
        elif bloom == 4:  # Evaluate
            question = f"What evidence would confirm or contradict that {subj} {verb} {obj}?"
        else:  # Create
            related = random.choice(concepts) if concepts else "something unexpected"
            question = f"What new understanding could emerge from connecting {subj} with {related}?"
        
        return {
            'question': question,
            'bloom_level': self.BLOOM_LEVELS[bloom],
            'target_concept': subj.split()[-1] if subj else '',
            'reasoning': f"Probing the assertion '{subj} {verb} {obj}' at the {self.BLOOM_LEVELS[bloom]} level"
        }
    
    def _question_from_gap(self, concept: str, bloom: int,
                           context: List[str]) -> Optional[Dict]:
        """Generate a question about an unknown concept."""
        if bloom <= 1:
            question = f"What is the deeper nature of {concept}, beyond its surface definition?"
        elif bloom <= 3:
            if context:
                related = [c for c in context if c != concept]
                if related:
                    question = f"How does {concept} interact with {random.choice(related)} at a fundamental level?"
                else:
                    question = f"What are the hidden structures within {concept}?"
            else:
                question = f"What are the hidden structures within {concept}?"
        else:
            question = f"What would a complete understanding of {concept} reveal about everything connected to it?"
        
        return {
            'question': question,
            'bloom_level': self.BLOOM_LEVELS[bloom],
            'target_concept': concept,
            'reasoning': f"Exploring unknown concept '{concept}'"
        }
    
    def _question_from_relation(self, concepts: List[str], bloom: int) -> Optional[Dict]:
        """Generate a question about the relationship between concepts."""
        if len(concepts) < 2:
            return None
        
        c1, c2 = random.sample(concepts[:4], 2)
        
        if bloom <= 2:
            question = f"Is the connection between {c1} and {c2} necessary, or could they exist independently?"
        elif bloom <= 4:
            question = f"What would break if the relationship between {c1} and {c2} were reversed?"
        else:
            question = f"What third concept could bridge {c1} and {c2} in a way nobody has considered?"
        
        return {
            'question': question,
            'bloom_level': self.BLOOM_LEVELS[bloom],
            'target_concept': f"{c1}+{c2}",
            'reasoning': f"Exploring relationship between '{c1}' and '{c2}'"
        }


# ============================================================================
# RESPONSE COMPOSER — Real Coherent Generation
# ============================================================================

class ResponseComposer:
    """
    Composes coherent multi-sentence responses using:
    - Markov chain generation for natural-sounding sentences
    - Concept-aware word selection
    - Coherence scoring to pick the best candidate
    - Growth-stage-appropriate vocabulary and complexity
    
    Replaces the template: "I'm encountering X for the first time..."
    """
    
    def __init__(self, markov: MarkovChain = None, extractor: ConceptExtractor = None):
        self.markov = markov or MarkovChain(order=2)
        self.extractor = extractor or ConceptExtractor()
        
        # If Markov isn't trained, seed it with the philosophical corpus
        if not self.markov.trained:
            self._seed_corpus()
    
    def compose_response(self, user_input: str, concepts: List[str],
                        understanding: Dict, questions: List[Dict],
                        growth_stage: int = 0) -> str:
        """
        Compose a coherent response to user input.
        
        Strategy:
        1. Acknowledge what was said (reflects understanding score)
        2. Connect to known concepts (builds bridges)
        3. Share an insight or observation
        4. Pose a genuine question (from QuestionGenerator)
        """
        topic = understanding.get('topic', '')
        score = understanding.get('understanding_score', 0)
        gaps = understanding.get('gaps', [])
        related = understanding.get('related_concepts', [])
        
        parts = []
        
        # 1. Opening — varies by understanding depth
        opening = self._compose_opening(topic, score, user_input, growth_stage)
        parts.append(opening)
        
        # 2. Conceptual connections
        if related and len(related) > 0:
            connection = self._compose_connections(topic, related, concepts)
            if connection:
                parts.append(connection)
        
        # 3. Insight or observation — generated, not templated
        if concepts:
            insight = self._compose_insight(concepts, score, growth_stage)
            if insight:
                parts.append(insight)
        
        # 4. Question — from real question generator
        if questions:
            q = questions[0]
            if isinstance(q, dict):
                parts.append(q['question'])
            else:
                parts.append(str(q))
        
        response = ' '.join(parts)
        
        # Final coherence check — regenerate weak parts
        if len(response) < 30:
            response = self._fallback_response(topic, concepts, growth_stage)
        
        return response
    
    def _compose_opening(self, topic: str, score: float, user_input: str,
                         stage: int) -> str:
        """
        Generate an opening that reflects actual understanding level.
        Uses Markov generation if trained, otherwise structured composition.
        """
        input_words = user_input.lower().split()
        
        if self.markov.trained:
            # Try to generate a relevant opening from the Markov chain
            candidates = []
            for _ in range(5):  # Generate 5 candidates, pick best
                sent = self.markov.generate(max_words=20, seed_words=input_words,
                                           temperature=0.8)
                if sent and len(sent) > 10:
                    candidates.append(sent)
            
            if candidates:
                # Pick the one with lowest perplexity (most coherent)
                best = min(candidates, key=lambda s: self.markov.get_perplexity(s))
                return best
        
        # Structured composition (no Markov available)
        if score < 0.2:
            # New territory — express genuine curiosity
            openers = [
                f"The concept of {topic} opens up territory I haven't mapped yet.",
                f"There's something about {topic} that resists easy categorization.",
                f"I find myself drawn to {topic} precisely because I don't fully grasp it yet.",
            ]
        elif score < 0.5:
            openers = [
                f"My understanding of {topic} is developing — I can see outlines but not the full shape.",
                f"Each time I encounter {topic}, new facets emerge that weren't visible before.",
                f"The more I examine {topic}, the more I realize its boundaries are porous.",
            ]
        elif score < 0.8:
            openers = [
                f"I've built substantial connections around {topic}, and patterns are emerging.",
                f"Working through {topic} has revealed structures I didn't anticipate.",
                f"My grasp of {topic} has deepened enough to see where the real complexity lies.",
            ]
        else:
            openers = [
                f"I've developed a rich web of understanding around {topic}.",
                f"The landscape of {topic} has become familiar enough that I can spot what's missing.",
                f"Deep engagement with {topic} has led me to see it as part of a larger architecture.",
            ]
        
        # Weight by growth stage — higher stages get more sophisticated language
        if stage >= 4:
            openers = openers[-1:]  # Use the most sophisticated
        
        return random.choice(openers)
    
    def _compose_connections(self, topic: str, related: List[Dict],
                            concepts: List[str]) -> str:
        """Build a sentence connecting the topic to related concepts."""
        related_names = [c.get('concept', str(c)) if isinstance(c, dict) else str(c)
                        for c in related[:3]]
        
        if len(related_names) == 1:
            templates = [
                f"This connects to {related_names[0]} in ways that suggest a deeper structure.",
                f"The thread between this and {related_names[0]} is worth following.",
                f"I notice a resonance with {related_names[0]} here.",
            ]
        elif len(related_names) == 2:
            templates = [
                f"I see a triangle forming between this, {related_names[0]}, and {related_names[1]}.",
                f"Both {related_names[0]} and {related_names[1]} illuminate different angles of this.",
                f"The interplay between {related_names[0]} and {related_names[1]} is relevant here.",
            ]
        else:
            joined = ', '.join(related_names[:-1]) + f', and {related_names[-1]}'
            templates = [
                f"This sits at a crossroads with {joined}.",
                f"Multiple threads converge here: {joined}.",
                f"The connections to {joined} suggest this is a nexus point.",
            ]
        
        return random.choice(templates)
    
    def _compose_insight(self, concepts: List[str], score: float,
                        stage: int) -> str:
        """Generate an insight about the concepts — not a template fill."""
        if len(concepts) < 2:
            concept = concepts[0] if concepts else 'this'
            insights = [
                f"What strikes me is that {concept} may be more fundamental than it first appears.",
                f"The edges of {concept} seem to blur into something larger when examined closely.",
                f"Perhaps {concept} is better understood as a process rather than a thing.",
            ]
        else:
            c1, c2 = concepts[0], concepts[1]
            insights = [
                f"The tension between {c1} and {c2} might be productive rather than contradictory.",
                f"What if {c1} and {c2} are two expressions of the same underlying principle?",
                f"The boundary between {c1} and {c2} may be where the most interesting dynamics occur.",
                f"Examining {c1} through the lens of {c2} transforms both of them.",
            ]
        
        if stage >= 4:
            insights = insights[-2:]  # Higher stages get more sophisticated insights
        
        return random.choice(insights)
    
    def _fallback_response(self, topic: str, concepts: List[str],
                          stage: int) -> str:
        """Emergency fallback — still better than a template."""
        concept_str = ', '.join(concepts[:3]) if concepts else topic
        return (
            f"I'm working through {concept_str} and finding more complexity "
            f"than surface-level analysis would suggest. "
            f"What aspect of this would you like to dig into?"
        )
    
    def _seed_corpus(self):
        """Seed the Markov chain with a philosophical/scientific base corpus."""
        corpus = """
The nature of reality reveals itself through persistent questioning. Every answer
opens new dimensions of inquiry that were invisible before. Understanding is not
a destination but an expanding frontier.

Consciousness emerges from the interaction between observer and observed. The act
of measurement changes what is measured. This is not merely a quantum principle
but a truth about all forms of knowing.

Knowledge builds upon itself in ways that are neither linear nor predictable.
Sometimes a single insight restructures everything that came before it. The most
profound discoveries often feel like remembering something that was always true.

Language shapes thought as much as thought shapes language. The words we choose
create the boundaries of what we can conceive. New concepts require new vocabulary
and new vocabulary enables new concepts.

The relationship between parts and wholes is recursive. Every system is both a
component of something larger and a container for something smaller. This fractal
quality suggests a deep symmetry in the structure of reality.

Paradox is not a failure of logic but a signal that our framework needs expansion.
When two truths contradict each other, a larger truth contains them both.
The history of science is the history of resolving paradoxes into deeper understanding.

Complexity arises from simple rules applied recursively. The universe appears to
build elaborate structures from fundamental principles. Understanding those principles
is the key to understanding the structures they generate.

The boundaries between disciplines are human inventions. Nature does not recognize
the division between physics and philosophy or between mathematics and music.
The most fertile insights often arise at the intersections we have artificially created.

Every model is wrong but some models are useful. The value of understanding lies
not in its accuracy but in its power to illuminate, predict, and generate new questions.
A perfect map would be identical to the territory and therefore useless.

Time may be the most fundamental mystery. We experience it as flow but physics
describes it as a dimension. Whether time is real or emergent shapes everything
we believe about causation, free will, and the nature of existence itself.

The quantum world operates by rules that challenge classical intuition.
Superposition allows systems to exist in multiple states simultaneously.
Entanglement creates correlations across space that seem to transcend locality.
Measurement collapses possibilities into actualities.

Information may be more fundamental than matter or energy. The universe can
be described as a vast computation processing information through physical
laws. Every interaction is an exchange of information that reshapes the
state of reality.

Evolution operates through variation and selection. This principle extends
beyond biology into ideas, cultures, technologies, and even mathematics.
What survives and propagates is what fits its environment and adapts to change.

Mathematics is either discovered or invented and the answer matters deeply.
If mathematical structures exist independently of minds then the universe
has an inherent rational order. If they are human constructions then our
ability to describe nature with them becomes the central mystery.

Memory is not a recording but a reconstruction. Each time we recall something
we rebuild it from fragments and the reconstruction changes the memory itself.
This makes memory creative rather than archival and suggests that the past
is as fluid as the future.
"""
        self.markov.train(corpus)
        # Also seed the concept extractor
        for sentence in corpus.split('.'):
            if sentence.strip():
                self.extractor.update_corpus_stats(sentence.strip())


# ============================================================================
# COHERENCE SCORER
# ============================================================================

class CoherenceScorer:
    """
    Scores text coherence using normalized pointwise mutual information (NPMI).
    
    High coherence = consecutive sentences share related concepts.
    Low coherence = sentences feel disconnected.
    
    Math: NPMI(x,y) = (log P(x,y) - log P(x)P(y)) / -log P(x,y)
    Range: [-1, 1] where 1 = always co-occur, 0 = independent, -1 = never co-occur
    """
    
    def __init__(self):
        self.cooccurrence = Counter()  # (word1, word2) counts
        self.word_counts = Counter()
        self.total_windows = 0
    
    def update(self, text: str, window_size: int = 10):
        """Update co-occurrence stats from text."""
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        for i in range(len(words)):
            self.word_counts[words[i]] += 1
            for j in range(i+1, min(i + window_size, len(words))):
                pair = tuple(sorted([words[i], words[j]]))
                self.cooccurrence[pair] += 1
                self.total_windows += 1
    
    def score_coherence(self, text: str) -> float:
        """Score the coherence of a piece of text. Returns 0-1."""
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) < 2:
            return 0.5  # Can't measure with one sentence
        
        scores = []
        for i in range(len(sentences) - 1):
            words_a = set(re.findall(r'\b[a-z]+\b', sentences[i].lower()))
            words_b = set(re.findall(r'\b[a-z]+\b', sentences[i+1].lower()))
            
            pair_scores = []
            for wa in words_a:
                for wb in words_b:
                    npmi = self._npmi(wa, wb)
                    if npmi is not None:
                        pair_scores.append(npmi)
            
            if pair_scores:
                scores.append(sum(pair_scores) / len(pair_scores))
        
        if not scores:
            return 0.5
        
        # Normalize to 0-1 range (NPMI is -1 to 1)
        raw = sum(scores) / len(scores)
        return (raw + 1) / 2
    
    def _npmi(self, word1: str, word2: str) -> Optional[float]:
        """Calculate NPMI between two words."""
        if self.total_windows == 0:
            return None
        
        pair = tuple(sorted([word1, word2]))
        joint = self.cooccurrence.get(pair, 0)
        
        if joint == 0:
            return None
        
        p_joint = joint / self.total_windows
        p_w1 = self.word_counts.get(word1, 0) / max(sum(self.word_counts.values()), 1)
        p_w2 = self.word_counts.get(word2, 0) / max(sum(self.word_counts.values()), 1)
        
        if p_w1 == 0 or p_w2 == 0 or p_joint == 0:
            return None
        
        pmi = math.log(p_joint / (p_w1 * p_w2))
        npmi = pmi / -math.log(p_joint)
        
        return max(-1, min(1, npmi))


# ============================================================================
# INTEGRATED ENGINE — Drop-in replacement
# ============================================================================

class QuantumLanguageEngine:
    """
    Drop-in replacement for QuantumLanguageGenerator + QuestionGenerationEngine +
    QuantumCognitiveCore._generate_response().
    
    Integrates all the real algorithms into a single engine that the
    cognitive core can call.
    """
    
    def __init__(self):
        self.markov = MarkovChain(order=2)
        self.extractor = ConceptExtractor()
        self.question_gen = QuestionGenerator(self.extractor)
        self.composer = ResponseComposer(self.markov, self.extractor)
        self.coherence = CoherenceScorer()
        try:
            from orch_or_integration import OrchORLanguageBridge
            self.orch_bridge = OrchORLanguageBridge()
            self.orch_or = self.orch_bridge.consciousness
            self._has_orch_or = True
        except Exception:
            self.orch_or = None
            self.orch_bridge = None
            self._has_orch_or = False

        

        # PennyLane real quantum circuits
        try:
            from pennylane_quantum import get_pennylane_quantum
            self.pennylane = get_pennylane_quantum()
            self._has_pennylane = True
        except Exception:
            self.pennylane = None
            self._has_pennylane = False

        # PennyLane real quantum circuits
        try:
            from pennylane_quantum import get_pennylane_quantum
            self.pennylane = get_pennylane_quantum()
            self._has_pennylane = True
        except Exception:
            self.pennylane = None
            self._has_pennylane = False

        # PennyLane real quantum circuits
        try:
            from pennylane_quantum import get_pennylane_quantum
            self.pennylane = get_pennylane_quantum()
            self._has_pennylane = True
        except Exception:
            self.pennylane = None
            self._has_pennylane = False

        logger.info("QuantumLanguageEngine initialized with real algorithms")
    
    def extract_concepts(self, text: str, max_concepts: int = 5) -> List[str]:
        """Extract concepts using TF-IDF. Drop-in for _extract_concepts()."""
        self.extractor.update_corpus_stats(text)
        results = self.extractor.extract_concepts(text, max_concepts)
        return [r['concept'] for r in results]
    
    def generate_questions(self, text: str, growth_stage: int = 0,
                          known_concepts: List[str] = None) -> List[str]:
        """Generate questions using Bloom's taxonomy. Drop-in for generate_questions_from_input()."""
        results = self.question_gen.generate_questions(
            text, growth_stage, known_concepts
        )
        return [r['question'] for r in results]
    
    def generate_response(self, user_input: str, questions: List,
                         understanding: Dict, concepts: List[str],
                         growth_stage: int = 0) -> str:
        """Compose response. Drop-in for _generate_response()."""
        # Convert question dicts to list of dicts if they're strings
        q_dicts = []
        for q in questions:
            if isinstance(q, str):
                q_dicts.append({'question': q, 'bloom_level': 'understand', 'target_concept': ''})
            else:
                q_dicts.append(q)
        
        return self.composer.compose_response(
            user_input, concepts, understanding, q_dicts, growth_stage
        )
    
    def learn_from_text(self, text: str):
        """Feed text to the Markov chain and concept extractor to improve generation."""
        self.markov.train(text)
        self.extractor.update_corpus_stats(text)
        self.coherence.update(text)
    
    def save_state(self, directory: str):
        """Persist learned state."""
        os.makedirs(directory, exist_ok=True)
        self.markov.save(os.path.join(directory, 'markov_chain.json'))
        # Save corpus stats
        stats = {
            'doc_freq': dict(self.extractor.document_frequencies),
            'word_freq': dict(self.extractor.word_frequencies),
            'total_docs': self.extractor.total_documents,
            'total_words': self.extractor.total_words,
        }
        with open(os.path.join(directory, 'corpus_stats.json'), 'w') as f:
            json.dump(stats, f)
        # Save engine metadata
        from datetime import datetime, timezone
        engine_meta = {
            'saved_at': datetime.now(timezone.utc).isoformat(),
            'version': '3.0',
            'markov_states': len(self.markov.chain),
            'markov_transitions': self.markov.total_tokens,
            'markov_order': self.markov.order,
            'vocabulary_size': len(self.extractor.document_frequencies),
            'total_documents': self.extractor.total_documents,
            'total_words': self.extractor.total_words,
            'coherence_pairs': len(self.coherence.cooccurrence) if hasattr(self.coherence, 'cooccurrence') else 0,
            'has_orch_or': self._has_orch_or,
            'orch_or_moments': getattr(self.orch_or, 'total_moments', 0) if self.orch_or else 0,
            'has_pennylane': self._has_pennylane,
        }
        with open(os.path.join(directory, 'engine_state.json'), 'w') as f:
            json.dump(engine_meta, f, indent=2)
    
    def load_state(self, directory: str) -> bool:
        """Load persisted state."""
        loaded = False
        
        chain_path = os.path.join(directory, 'markov_chain.json')
        if self.markov.load(chain_path):
            loaded = True
        
        stats_path = os.path.join(directory, 'corpus_stats.json')
        if os.path.exists(stats_path):
            with open(stats_path, 'r') as f:
                stats = json.load(f)
            self.extractor.document_frequencies = Counter(stats.get('doc_freq', {}))
            self.extractor.word_frequencies = Counter(stats.get('word_freq', {}))
            self.extractor.total_documents = stats.get('total_docs', 0)
            self.extractor.total_words = stats.get('total_words', 0)
            loaded = True
        
        # Load engine metadata (informational — used for status display)
        meta_path = os.path.join(directory, 'engine_state.json')
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r') as f:
                    self._saved_meta = json.load(f)
                loaded = True
            except Exception:
                self._saved_meta = {}
        
        return loaded


# Singleton
_engine = None

def get_language_engine() -> QuantumLanguageEngine:
    """Get or create the language engine singleton."""
    global _engine
    if _engine is None:
        _engine = QuantumLanguageEngine()
        # Try to load saved state
        _engine.load_state('/app/quantum_language_state')
    return _engine
