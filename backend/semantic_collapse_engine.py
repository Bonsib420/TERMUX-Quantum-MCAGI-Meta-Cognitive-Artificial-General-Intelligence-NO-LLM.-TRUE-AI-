"""
Semantic Collapse / Observation Engine for Quantum AI
Simulates quantum superposition collapse through semantic analysis

When user asks a question, the engine "observes" key concepts and
collapses the infinite semantic possibilities into focused responses.
"""

import re
import random
from typing import Dict, List, Tuple, Set, Optional


class SemanticCollapseEngine:
    """
    Collapses semantic superposition based on input observation (keywords).
    When user asks a question, the engine "observes" key concepts and
    collapses the infinite semantic possibilities into focused responses.
    """
    
    def __init__(self, co_occurrence_weights: Dict = None):
        """
        Initialize with co-occurrence weights from grammar engine
        
        Args:
            co_occurrence_weights: Dict of word -> {related_word: weight}
        """
        self.co_occurrence = co_occurrence_weights or self._default_co_occurrence()
        self.keyword_clusters = self._build_keyword_clusters()
        self.decay_rate = 0.3  # How much non-relevant weights decay
        self.observation_history = []
    
    def _default_co_occurrence(self) -> Dict:
        """Default co-occurrence weights for philosophical/quantum concepts"""
        return {
            'consciousness': {'awareness': 0.9, 'being': 0.8, 'existence': 0.8, 'mind': 0.7, 'spirit': 0.7, 'observation': 0.6},
            'quantum': {'superposition': 0.9, 'entanglement': 0.9, 'observation': 0.8, 'collapse': 0.8, 'probability': 0.7, 'measurement': 0.7},
            'god': {'divine': 0.9, 'creation': 0.9, 'infinite': 0.8, 'eternal': 0.8, 'transcendent': 0.9, 'omnipotent': 0.7},
            'universe': {'existence': 0.9, 'creation': 0.8, 'reality': 0.8, 'cosmos': 0.8, 'spacetime': 0.9, 'being': 0.7},
            'reality': {'existence': 0.9, 'being': 0.8, 'truth': 0.8, 'manifestation': 0.7, 'phenomenon': 0.7},
            'observation': {'collapse': 0.9, 'measurement': 0.9, 'awareness': 0.8, 'consciousness': 0.8, 'perception': 0.7},
            'superposition': {'quantum': 0.9, 'probability': 0.8, 'potential': 0.8, 'multiplicity': 0.7, 'coexistence': 0.7},
            'creation': {'god': 0.8, 'universe': 0.8, 'existence': 0.7, 'emergence': 0.7, 'origin': 0.8},
            'spacetime': {'dimension': 0.9, 'physical': 0.8, 'universe': 0.8, 'relativity': 0.8, 'continuum': 0.7},
            'philosophy': {'wisdom': 0.8, 'truth': 0.8, 'knowledge': 0.8, 'existence': 0.7, 'meaning': 0.8},
            'word': {'language': 0.9, 'meaning': 0.9, 'neutral': 0.7, 'tool': 0.7, 'communication': 0.8},
            'language': {'word': 0.9, 'meaning': 0.8, 'communication': 0.9, 'expression': 0.8, 'symbol': 0.7},
        }
        
    def _build_keyword_clusters(self) -> Dict[str, Set[str]]:
        """Build semantic clusters from co-occurrence weights"""
        clusters = {}
        for word, relations in self.co_occurrence.items():
            clusters[word] = set(relations.keys())
        return clusters
    
    def extract_keywords(self, text: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Extract primary keywords from input text.
        Keywords are words that appear in co-occurrence network.
        
        Returns:
            List of (keyword, importance_score) tuples
        """
        # Normalize text
        text_lower = text.lower()
        words = re.findall(r'\b[a-z]+\b', text_lower)
        
        # Score words by co-occurrence network presence
        keyword_scores = {}
        for word in set(words):
            if word in self.co_occurrence:
                # Weight by number of relations (importance in network)
                score = len(self.co_occurrence[word]) / 10.0
                keyword_scores[word] = score
            elif word in self._flatten_all_related_words():
                # Secondary importance for related words
                keyword_scores[word] = 0.5
        
        # Return top keywords
        sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_keywords[:top_n]
    
    def _flatten_all_related_words(self) -> Set[str]:
        """Get all words mentioned in co-occurrence network"""
        all_words = set(self.co_occurrence.keys())
        for relations in self.co_occurrence.values():
            all_words.update(relations.keys())
        return all_words
    
    def collapse_weights(self, input_text: str) -> Dict[str, Dict[str, float]]:
        """
        OBSERVATION COLLAPSE: Narrow co-occurrence weights based on input keywords.
        
        This simulates quantum measurement:
        - Before observation: infinite semantic possibilities (full co-occurrence)
        - Observation (keywords extracted): collapses to relevant meanings
        - After collapse: weights decay for non-relevant concepts
        
        Args:
            input_text: User's query
            
        Returns:
            Collapsed co-occurrence weights focused on query semantics
        """
        # Extract observation (keywords)
        keywords = self.extract_keywords(input_text)
        keyword_set = {kw for kw, _ in keywords}
        
        if not keyword_set:
            # No observation possible, return original
            return self.co_occurrence
        
        # Collapse: Create new weights focused on keywords
        collapsed = {}
        
        for word, relations in self.co_occurrence.items():
            collapsed[word] = {}
            
            for related_word, original_weight in relations.items():
                # If related word is in keyword set, AMPLIFY
                if related_word in keyword_set:
                    new_weight = min(1.0, original_weight * 1.5)  # Amplify
                # If word itself is keyword, PRESERVE
                elif word in keyword_set:
                    new_weight = original_weight
                # Otherwise, DECAY (non-relevant concepts fade)
                else:
                    new_weight = original_weight * (1 - self.decay_rate)
                
                collapsed[word][related_word] = new_weight
        
        return collapsed
    
    def get_semantic_context(self, input_text: str) -> Dict:
        """
        Get semantic context after collapse.
        Returns the "collapsed state" information for response generation.
        """
        keywords = self.extract_keywords(input_text)
        collapsed_weights = self.collapse_weights(input_text)
        
        # Find strongest semantic paths from keywords
        semantic_paths = {}
        for keyword, _ in keywords:
            if keyword in collapsed_weights:
                # Get strongest related words
                relations = collapsed_weights[keyword]
                strongest = sorted(relations.items(), key=lambda x: x[1], reverse=True)[:3]
                semantic_paths[keyword] = strongest
        
        return {
            'keywords': keywords,
            'collapsed_weights': collapsed_weights,
            'semantic_paths': semantic_paths,
            'collapse_strength': len(keywords) / 5.0  # Measure of how focused
        }
    
    def select_word_from_collapsed(self, 
                                   word_pool: List[str], 
                                   context: Dict,
                                   quantum_probability: float = 0.5) -> str:
        """
        Select a word from pool using collapsed weights + quantum randomness.
        
        Args:
            word_pool: Available words to choose from
            context: Semantic context from collapse
            quantum_probability: Quantum state probability (0-1)
            
        Returns:
            Selected word
        """

        return self._select_word_from_collapsed_continued(word_pool, context, quantum_probability)

    def _select_word_from_collapsed_continued(self, word_pool, context, quantum_probability):
        """Continuation of select_word_from_collapsed — auto-extracted by self-evolution."""
        collapsed_weights = context.get('collapsed_weights', {})

        # Score each word in pool based on collapsed weights
        word_scores = {}
        for word in word_pool:
            score = 0.0

            # Check if word appears in collapsed network
            if word in collapsed_weights:
                # Sum of all its relations (how connected it is)
                score += sum(collapsed_weights[word].values())

            # Check if word is related to keywords
            for keyword, _ in context.get('keywords', []):
                if keyword in collapsed_weights and word in collapsed_weights.get(keyword, {}):
                    score += collapsed_weights[keyword][word] * 2  # Boost

            word_scores[word] = score

        # Normalize scores
        total_score = sum(word_scores.values())
        if total_score > 0:
            word_scores = {w: s/total_score for w, s in word_scores.items()}
        else:
            # Fallback: uniform distribution
            word_scores = {w: 1/len(word_pool) for w in word_pool}

        # Apply quantum randomness
        if random.random() < quantum_probability:
            # Quantum: select from top choices
            sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
            top_words = [w for w, _ in sorted_words[:max(1, len(sorted_words)//3)]]
            return random.choice(top_words)
        else:
            # Classical: select highest probability
            return max(word_scores.items(), key=lambda x: x[1])[0]

    
    def observe(self, input_text: str, response: str):
        """Record an observation for learning"""
        self.observation_history.append({
            'input': input_text,
            'response': response,
            'keywords': self.extract_keywords(input_text)
        })
        # Keep history manageable
        if len(self.observation_history) > 100:
            self.observation_history.pop(0)
    
    def reset(self):
        """Reset the collapse engine state"""
        self.observation_history = []
    
    def evaluate_collapse_quality(self, input_text: str, response: str) -> float:
        """
        Evaluate how well the collapse worked.
        Higher score = better semantic coherence between input and output.
        
        Returns:
            Quality score 0-1
        """
        input_keywords = set(kw for kw, _ in self.extract_keywords(input_text))
        response_words = set(re.findall(r'\b[a-z]+\b', response.lower()))
        
        # Check if response contains related words
        related_count = 0
        for keyword in input_keywords:
            if keyword in self.co_occurrence:
                related = self.co_occurrence[keyword].keys()
                related_count += len(response_words & set(related))
        
        # Normalize
        max_possible = len(input_keywords) * 5
        if max_possible == 0:
            return 0.5
        
        return min(1.0, related_count / max_possible)
