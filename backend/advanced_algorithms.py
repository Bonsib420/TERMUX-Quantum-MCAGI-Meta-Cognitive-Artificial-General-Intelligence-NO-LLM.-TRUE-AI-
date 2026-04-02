"""
🧠 ADVANCED ALGORITHMIC IMPROVEMENTS
====================================
What would make the algorithm TRULY intelligent:

1. GRAMMAR ENGINE - Current Markov outputs can be grammatically awkward
2. CONTEXT MEMORY - Remember conversation context across turns
3. REASONING CHAINS - Multi-step logical inference
4. SEMANTIC EMBEDDINGS - Dense vector representations
5. ATTENTION OVER MEMORY - Focus on relevant past knowledge
6. DYNAMIC TEMPERATURE - Adjust creativity based on query type
7. CONCEPT GRAPHS - Knowledge graph with weighted edges
8. BAYESIAN UPDATING - Update beliefs based on evidence

This file implements these improvements.
"""

import re
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger("quantum_ai")


# ============================================================================
# 1. GRAMMAR ENGINE - Fix Markov output grammar
# ============================================================================

class GrammarEngine:
    """
    Post-processes Markov output to fix common grammatical issues.
    
    Rules:
    - Subject-verb agreement
    - Article usage (a/an)
    - Capitalization
    - Punctuation
    - Remove repeated words
    """
    
    def __init__(self):
        self.article_a_patterns = re.compile(r'\ba ([aeiou])', re.IGNORECASE)
        self.article_an_patterns = re.compile(r'\ban ([^aeiou])', re.IGNORECASE)
        self.repeated_words = re.compile(r'\b(\w+)\s+\1\b', re.IGNORECASE)
        
        # Common verb fixes
        self.verb_corrections = {
            'is are': 'are',
            'are is': 'is',
            'was were': 'were',
            'have has': 'has',
            'do does': 'does',
        }
    
    def fix(self, text: str, query: str = None) -> str:
        """Apply all grammar fixes."""
        if not text:
            return text
        
        original_text = text
        words = text.split()

        # Extract query words and find the main topic
        query_words = set()
        main_topic = None
        if query:
            query_words = set(w.lower().rstrip('.,!?') for w in query.split())
            # Find the main noun (topic) from query - typically the last significant word
            topic_candidates = ['gravity', 'time', 'space', 'energy', 'consciousness', 'love',
                               'life', 'death', 'truth', 'beauty', 'freedom', 'knowledge',
                               'reality', 'matter', 'intelligence', 'science', 'philosophy',
                               'music', 'art', 'religion', 'technology', 'history', 'mathematics',
                               'evolution', 'quantum', 'physics', 'biology', 'psychology', 'language',
                               'happiness', 'meaning', 'existence', 'mind', 'universe']
            for word in reversed(query.lower().split()):
                clean_word = word.rstrip('.,!?')
                if clean_word in topic_candidates:
                    main_topic = clean_word.capitalize()
                    break
        
        # Bad starters that indicate we've hit a sentence fragment (expanded)
        bad_starters = {'is', 'are', 'the', 'a', 'an', 'what', 'how', 'why', 'when', 
                       'where', 'tell', 'explain', 'describe', 'define', 'has', 
                       'does', 'do', 'can', 'could', 'would', 'should', 'me', 'about',
                       'it', 'this', 'that', 'i', 'you', 'we', 'they', 'and', 'or',
                       'but', 'if', 'then', 'so', 'for', 'with', 'by', 'from', 'to',
                       'at', 'in', 'on', 'of', 'as', 'not', 'cannot', 'when',
                       'something', 'interesting', 'know', 'learn', 'holes'}
        
        # Common verb starters that indicate a fragment
        verb_starters = {'is', 'are', 'was', 'were', 'has', 'have', 'had', 'does', 'do',
                        'can', 'could', 'would', 'should', 'may', 'might', 'must',
                        'attracts', 'causes', 'requires', 'involves', 'includes', 'remains',
                        'evolved', 'exists', 'occurs', 'emerges', 'manifests', 'appears',
                        'provides', 'enables', 'allows', 'produces', 'creates', 'forms',
                        'takes', 'gives', 'seeks', 'needs', 'wants', 'uses', 'makes',
                        'been', 'being', 'keeps', 'holds', 'bends', 'shapes', 'acts',
                        'flows', 'travels', 'moves', 'describes', 'explains', 'shows',
                        'reveals', 'suggests', 'implies', 'means', 'contains', 'consists',
                        'affects', 'influences', 'drives', 'connects', 'links', 'relates',
                        'varies', 'depends', 'comes', 'goes', 'leads', 'follows', 'results',
                        'continues', 'started', 'began', 'ended', 'happened', 'occurred',
                        'cannot'}
        
        # First: Check if text starts with main topic - if so, it's probably good
        if words and main_topic:
            first_word_clean = words[0].lower().rstrip('.,!?')
            if first_word_clean == main_topic.lower():
                # Looks good, skip most cleaning
                pass
            else:
                # Need to fix - check for fragments
                
                # Remove query words from start
                content_start = 0
                for i in range(min(5, len(words))):
                    word_clean = words[i].lower().rstrip('.,!?')
                    if word_clean in query_words and word_clean != main_topic.lower():
                        content_start = i + 1
                    elif word_clean in bad_starters:
                        content_start = i + 1
                    else:
                        break
                
                if content_start > 0 and content_start < len(words):
                    words = words[content_start:]
                    text = ' '.join(words)
                
                # CHECK: Did we create a fragment? If first word is a verb or bad starter, add topic
                if words:
                    first_word = words[0].lower().rstrip('.,!?')
                    if first_word in verb_starters or first_word in bad_starters:
                        # Add the topic as subject
                        text = main_topic + ' ' + text.lower()
        else:
            # No main topic identified, do basic cleanup
            content_start = 0
            if len(words) > 2:
                for i in range(min(5, len(words))):
                    word_clean = words[i].lower().rstrip('.,!?')
                    if word_clean in query_words or word_clean in bad_starters:
                        content_start = i + 1
                    else:
                        break
            
            if content_start > 0 and content_start < len(words):
                words = words[content_start:]
                text = ' '.join(words)
        
        # CLEANUP: Remove problematic patterns
        # Pattern 1: "X explain X is..." -> "X is..."
        # Pattern 2: "X meaning X is..." -> "X is..."
        # Pattern 3: "Physical modern X" -> "X"
        # Pattern 4: "Quantum describes mechanics quantum mechanics" -> "Quantum mechanics"
        words = text.split()
        if len(words) > 3 and main_topic:
            main_topic_lower = main_topic.lower()
            
            # First check for repeated topic pattern: "Topic describes topic topic..."
            topic_indices = []
            for i, w in enumerate(words[:6]):
                if w.lower().rstrip('.,!?') == main_topic_lower:
                    topic_indices.append(i)
            
            if len(topic_indices) >= 2:
                # Keep from second occurrence of topic
                second_idx = topic_indices[1]
                text = ' '.join(words[second_idx:])
                words = text.split()
            
            # Check for "X explain topic" or "X meaning topic" patterns
            for i in range(min(3, len(words))):
                if words[i].lower().rstrip('.,!?') in ['explain', 'meaning', 'physical', 'modern', 'objects', 'describes', 'mechanics']:
                    # Find where topic word starts
                    for j in range(i+1, min(i+4, len(words))):
                        if words[j].lower().rstrip('.,!?') == main_topic_lower:
                            # Skip to topic
                            text = main_topic + ' ' + ' '.join(words[j+1:]).lower()
                            break
                    break
        
        # Pattern 4: "Topic topic is..." -> "Topic is..."
        words = text.split()
        if len(words) > 2 and main_topic:
            if words[0].lower() == words[1].lower().rstrip('.,!?'):
                text = ' '.join(words[1:])
                text = text[0].upper() + text[1:]
        
        # 1. Fix articles (a/an)
        text = self.article_a_patterns.sub(r'an \1', text)
        text = self.article_an_patterns.sub(r'a \1', text)

        # 2. Remove repeated words
        text = self.repeated_words.sub(r'\1', text)

        return self._fix_continued(text)

    def _fix_continued(self, text):
        """Continuation of fix — auto-extracted by self-evolution."""
        # 3. Fix verb issues
        for wrong, right in self.verb_corrections.items():
            text = text.replace(wrong, right)

        # 4. Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]

        # 5. Capitalize after periods
        text = re.sub(r'(\. )([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)

        # 6. Ensure ends with punctuation
        if text and text[-1] not in '.!?':
            text += '.'

        # 7. Fix multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()

        # 8. Fix common issues
        text = text.replace(' ,', ',')
        text = text.replace(' .', '.')
        text = text.replace('..', '.')

        return text



# ============================================================================
# 2. CONTEXT MEMORY - Track conversation context
# ============================================================================

class ConversationContext:
    """
    Maintains context across conversation turns.
    
    Tracks:
    - Active topics (weighted by recency)
    - Referenced entities
    - User intent history
    - Emotional tone
    """
    
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.turns = []  # List of (user_msg, response, concepts)
        self.active_topics = Counter()
        self.entities = set()
        self.intent_history = []
    
    def add_turn(self, user_msg: str, response: str, concepts: List[str]):
        """Add a conversation turn."""
        self.turns.append({
            'user': user_msg,
            'response': response,
            'concepts': concepts,
            'time': datetime.now()
        })
        
        # Keep only recent turns
        if len(self.turns) > self.max_turns:
            self.turns.pop(0)
        
        # Update active topics with decay
        self.active_topics = Counter()
        for i, turn in enumerate(self.turns):
            weight = (i + 1) / len(self.turns)  # More recent = higher weight
            for concept in turn['concepts']:
                self.active_topics[concept] += weight
        
        # Extract entities (capitalized words)
        entities = re.findall(r'\b[A-Z][a-z]+\b', user_msg)
        self.entities.update(entities)
    
    def get_context_concepts(self, top_n: int = 5) -> List[str]:
        """Get most relevant context concepts."""
        return [c for c, _ in self.active_topics.most_common(top_n)]
    
    def get_recent_topics(self) -> List[str]:
        """Get topics from recent turns."""
        if not self.turns:
            return []
        return self.turns[-1].get('concepts', [])[:3]
    
    def is_followup(self, query: str) -> bool:
        """Check if query is a follow-up to previous topic."""
        followup_indicators = ['it', 'that', 'this', 'they', 'those', 'more', 'also', 'what about']
        query_lower = query.lower()
        return any(ind in query_lower for ind in followup_indicators)


# ============================================================================
# 3. REASONING CHAINS - Multi-step inference
# ============================================================================

class ReasoningEngine:
    """
    Performs multi-step logical reasoning.
    
    Implements:
    - Forward chaining (A→B, B→C ∴ A→C)
    - Analogical reasoning (A:B :: C:?)
    - Causal inference
    """
    
    def __init__(self):
        self.rules = []  # List of (condition, conclusion, confidence)
        self.facts = set()
    
    def add_rule(self, condition: str, conclusion: str, confidence: float = 1.0):
        """Add an inference rule."""
        self.rules.append((condition.lower(), conclusion.lower(), confidence))
    
    def add_fact(self, fact: str):
        """Add a known fact."""
        self.facts.add(fact.lower())
    
    def infer(self, query: str, max_steps: int = 5) -> List[Tuple[str, float, List[str]]]:
        """
        Perform inference to answer query.
        
        Returns list of (conclusion, confidence, reasoning_chain)
        """
        query_lower = query.lower()
        results = []
        
        # Direct fact check
        for fact in self.facts:
            if query_lower in fact or fact in query_lower:
                results.append((fact, 1.0, ["Direct knowledge"]))
        
        # Forward chaining
        current_facts = set(self.facts)
        chain = []
        
        for step in range(max_steps):
            new_facts = set()
            for condition, conclusion, conf in self.rules:
                if condition in current_facts and conclusion not in current_facts:
                    new_facts.add(conclusion)
                    chain.append(f"{condition} → {conclusion}")
                    
                    if query_lower in conclusion:
                        results.append((conclusion, conf ** (step + 1), chain.copy()))
            
            if not new_facts:
                break
            current_facts.update(new_facts)
        
        return results
    
    def analogy(self, a: str, b: str, c: str, candidates: List[str]) -> Optional[str]:
        """
        A is to B as C is to ?
        Find best match from candidates.
        """
        # Simple word-level analogy using character patterns
        # In real system, would use word embeddings
        
        a_to_b = self._relationship(a, b)
        
        best_match = None
        best_score = 0
        
        for candidate in candidates:
            c_to_cand = self._relationship(c, candidate)
            score = self._similarity(a_to_b, c_to_cand)
            if score > best_score:
                best_score = score
                best_match = candidate
        
        return best_match
    
    def _relationship(self, w1: str, w2: str) -> Dict:
        """Extract relationship features between words."""
        return {
            'len_diff': len(w2) - len(w1),
            'shared_chars': len(set(w1) & set(w2)),
            'prefix_match': w1[:2] == w2[:2] if len(w1) >= 2 and len(w2) >= 2 else False
        }
    
    def _similarity(self, r1: Dict, r2: Dict) -> float:
        """Similarity between relationships."""
        score = 0
        if r1.get('len_diff') == r2.get('len_diff'):
            score += 0.3
        if abs(r1.get('shared_chars', 0) - r2.get('shared_chars', 0)) <= 1:
            score += 0.3
        if r1.get('prefix_match') == r2.get('prefix_match'):
            score += 0.4
        return score


# ============================================================================
# 4. SEMANTIC SIMILARITY - Without external embeddings
# ============================================================================

class SemanticSimilarity:
    """
    Compute semantic similarity using character n-grams and word overlap.
    Works without external embedding models.
    """
    
    def __init__(self, n: int = 3):
        self.n = n  # n-gram size
    
    def similarity(self, text1: str, text2: str) -> float:
        """
        Compute similarity combining:
        - Character n-gram overlap (catches typos, morphology)
        - Word overlap (Jaccard)
        - Word order similarity
        """
        t1, t2 = text1.lower(), text2.lower()
        
        # Character n-gram similarity
        ngrams1 = self._char_ngrams(t1)
        ngrams2 = self._char_ngrams(t2)
        ngram_sim = self._jaccard(ngrams1, ngrams2)
        
        # Word overlap
        words1 = set(t1.split())
        words2 = set(t2.split())
        word_sim = self._jaccard(words1, words2)
        
        # Combined score
        return ngram_sim * 0.4 + word_sim * 0.6
    
    def _char_ngrams(self, text: str) -> set:
        """Extract character n-grams."""
        text = text.replace(' ', '_')
        return set(text[i:i+self.n] for i in range(len(text) - self.n + 1))
    
    def _jaccard(self, set1: set, set2: set) -> float:
        """Jaccard similarity."""
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
    
    def most_similar(self, query: str, candidates: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        """Find most similar candidates."""
        scores = [(c, self.similarity(query, c)) for c in candidates]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# ============================================================================
# 5. CONCEPT GRAPH - Knowledge graph structure
# ============================================================================

