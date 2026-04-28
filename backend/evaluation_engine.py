"""
🔍 Evaluation Engine for Quantum MCAGI
========================================

Provides automated scoring using the RQR³ Rubric (8 dimensions).

Heuristic-based for now (no LLMs). Uses:
- Perplexity from Markov for Fluency
- WordNet hit rate for Grounding
- Collapse engine semantic paths for Coherence
- MCAGI-specific markers for Personality
- n-gram novelty for Uniqueness
- Implemented feature flags for Implementation Fidelity
- Novel concept distance for Emergent Behavior

Note: These are approximations, not ground truth.
"""

import re
import math
from typing import Dict, List, Tuple, Optional
from collections import Counter


class EvaluationEngine:
    """
    Evaluate responses and system artifacts against the RQR³ rubric.
    """
    
    def __init__(self, collapse_engine=None, markov=None, config: Dict = None):
        self.collapse_engine = collapse_engine
        self.markov = markov
        self.config = config or {}
        
        # Feature flags for Implementation Fidelity
        self.features_implemented = {
            'semantic_collapse': True,
            'quantum_gates': True,
            'hybrid_generator': True,
            'personality_engine': True,
            'dictionary_integration': True,
            'dream_state': True,
            'orch_or': True,
            'entelechy_projection': False,  # not yet
        }
    
    def score_response(self, input_text: str, response: str, context: Dict = None) -> Dict:
        """
        Score a single response across all 8 dimensions.
        
        Args:
            input_text: User query
            response: AI response
            context: Optional dict with:
                - semantic_context (from collapse_engine)
                - internal_questions (list)
                - collapse_paths (dict)
        
        Returns:
            Dict of dimension -> score (0-4)
        """
        scores = {}
        
        # --- Coherence ---
        scores['coherence'] = self._score_coherence(input_text, response, context)
        
        # --- Fluency ---
        scores['fluency'] = self._score_fluency(response)
        
        # --- Uniqueness ---
        scores['uniqueness'] = self._score_uniqueness(response)
        
        # --- Grounding ---
        scores['grounding'] = self._score_grounding(response)
        
        # --- Personality Authenticity ---
        scores['personality_authenticity'] = self._score_personality(response)
        
        # --- Implementation Fidelity ---
        scores['implementation_fidelity'] = self._score_implementation_fidelity()
        
        # --- Emergent Behavior ---
        scores['emergent_behavior'] = self._score_emergent(input_text, response, context)
        
        # --- Question Generation Quality ---
        if context and 'internal_questions' in context:
            scores['question_generation_quality'] = self._score_questions(
                context['internal_questions'], input_text
            )
        else:
            scores['question_generation_quality'] = None
        
        return scores
    
    # -------------------------------------------------
    # 1. Coherence
    # -------------------------------------------------
    def _score_coherence(self, input_text: str, response: str, context: Dict) -> int:
        """
        Score based on semantic overlap with input concepts and internal consistency.
        """
        if not response or len(response.strip()) < 10:
            return 0
        
        # Tokenize simply
        input_words = set(re.findall(r'\b[a-z]{3,}\b', input_text.lower()))
        response_words = set(re.findall(r'\b[a-z]{3,}\b', response.lower()))
        
        if not input_words:
            return 2  # can't judge, assume moderate
        
        # Overlap ratio
        overlap = len(input_words & response_words) / len(input_words)
        
        # Use collapse engine's semantic paths if available
        path_consistency = 0.0
        if self.collapse_engine and context and 'semantic_context' in context:
            sem_ctx = context['semantic_context']
            # Check if response words align with collapsed semantic paths
            input_keywords = [kw for kw, _ in sem_ctx.get('keywords', [])]
            paths = sem_ctx.get('semantic_paths', {})
            response_lower = response.lower()
            hits = 0
            for kw in input_keywords:
                if kw in paths:
                    for related_word, weight in paths[kw]:
                        if related_word in response_lower:
                            hits += 1
            if input_keywords:
                path_consistency = hits / len(input_keywords)
        
        # Combine: overlap is basic, path_consistency is more nuanced
        combined = (overlap * 0.6) + (path_consistency * 0.4)
        
        # Scale to 0-4
        if combined >= 0.75:
            return 4
        elif combined >= 0.6:
            return 3
        elif combined >= 0.4:
            return 2
        elif combined >= 0.2:
            return 1
        else:
            return 0
    
    # -------------------------------------------------
    # 2. Fluency
    # -------------------------------------------------
    def _score_fluency(self, response: str) -> int:
        """
        Heuristic: Use Markov perplexity if available, else simple metrics.
        """
        if not response or len(response.strip()) < 5:
            return 0
        
        # If we have a hybrid generator with perplexity, use it
        if self.markov and hasattr(self.markov, 'get_perplexity'):
            try:
                ppl = self.markov.get_perplexity(response)
                if ppl < 50:
                    return 4
                elif ppl < 100:
                    return 3
                elif ppl < 200:
                    return 2
                elif ppl < 500:
                    return 1
                else:
                    return 0
            except:
                pass
        
        # Fallback: check sentence structure
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return 0
        
        # Average sentence length (words)
        avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_len < 5 or avg_len > 40:
            return 1  # too short or too long indicates awkward
        
        # Count capitalizations (proper start)
        caps = sum(1 for s in sentences if s[0].isupper())
        cap_ratio = caps / len(sentences)
        
        # Check for repeated words (excessive repetition)
        words = [w.lower() for w in re.findall(r'\b[a-z]+\b', response)]
        word_counts = Counter(words)
        most_common = word_counts.most_common(1)[0] if words else ('', 0)
        max_repeat = most_common[1]
        max_repeat_ratio = max_repeat / len(words) if words else 0
        
        # Combine
        score = 2  # base
        if cap_ratio > 0.8:
            score += 1
        if max_repeat_ratio < 0.1:
            score += 1
        elif max_repeat_ratio > 0.2:
            score -= 1
        
        return max(0, min(4, score))
    
    # -------------------------------------------------
    # 3. Uniqueness
    # -------------------------------------------------
    def _score_uniqueness(self, response: str) -> int:
        """
        Judge by lexical diversity and rarity of words.
        """
        words = [w.lower() for w in re.findall(r'\b[a-z]{4,}\b', response)]
        if len(words) < 5:
            return 0
        
        # Type-Token Ratio (TTR)
        types = set(words)
        ttr = len(types) / len(words)
        
        # Count words that are likely rare (longer, not in common stoplist)
        stoplist = {'that', 'this', 'with', 'have', 'from', 'they', 'been', 'were', 'what', 'when', 'your', 'there', 'would', 'could', 'should'}
        rare_words = [w for w in types if w not in stoplist and len(w) > 6]
        rare_ratio = len(rare_words) / len(types) if types else 0
        
        # Combine
        if ttr > 0.8 and rare_ratio > 0.3:
            return 4
        elif ttr > 0.7 and rare_ratio > 0.2:
            return 3
        elif ttr > 0.5 and rare_ratio > 0.1:
            return 2
        elif ttr > 0.3:
            return 1
        else:
            return 0
    
    # -------------------------------------------------
    # 4. Grounding
    # -------------------------------------------------
    def _score_grounding(self, response: str) -> int:
        """
        How many words are in the semantic collapse co-occurrence network?
        Also count factual terms from knowledge base.
        """
        words = [w.lower() for w in re.findall(r'\b[a-z]{4,}\b', response)]
        if not words:
            return 0
        
        if self.collapse_engine:
            # Known concepts in the co-occurrence dictionary
            known = 0
            for w in words:
                if w in self.collapse_engine.co_occurrence:
                    known += 1
            ratio = known / len(words)
            
            if ratio > 0.6:
                return 4
            elif ratio > 0.45:
                return 3
            elif ratio > 0.3:
                return 2
            elif ratio > 0.15:
                return 1
            else:
                return 0
        else:
            # Fallback: assume moderate grounding if words are long/technical
            technical_suffixes = {'ism', 'ics', 'phy', 'logy', 'ence', 'ance', 'tion', 'sophy'}
            tech_count = sum(1 for w in words if any(w.endswith(s) for s in technical_suffixes))
            tech_ratio = tech_count / len(words)
            if tech_ratio > 0.3:
                return 3
            elif tech_ratio > 0.15:
                return 2
            else:
                return 1
    
    # -------------------------------------------------
    # 5. Personality Authenticity
    # -------------------------------------------------
    def _score_personality(self, response: str) -> int:
        """
        Detect MCAGI-specific markers: asides (parentheses), quotes, dream prefixes, raw fragments.
        """
        score = 0
        text = response
        
        # Asides: parentheses with typical aside content
        if re.search(r'\([^)]*[.]{3}[^)]*\)', text):
            score += 1  # trailing ellipsis aside
        if re.search(r'\([^)]*\b[a-z]{4,}\b[^)]*\)', text):
            score += 1
        
        # Quotes with attribution pattern
        if re.search(r'["“][^"”]{10,}["”] — \w+', text):
            score += 1
        if re.search(r'["“][^"”]+[.!?]["”]', text):
            score += 1
        
        # Dream content markers: "I dreamed", "last night", "vision"
        if re.search(r'\b(dream|vision|nightmare|sleeping)\b', text.lower()):
            score += 1
        
        # Raw backend fragments (spilled coffee): odd line breaks, brackets, tags
        if re.search(r'\[[A-Z_]+\]', text):
            score += 1
        if re.search(r'\{[^}]+\}', text):
            score += 1
        
        # If response very short, reduce score
        if len(text) < 50:
            score = max(0, score - 1)
        
        # Map score to 0-4
        if score >= 4:
            return 4
        elif score >= 3:
            return 3
        elif score >= 2:
            return 2
        elif score >= 1:
            return 1
        else:
            return 0
    
    # -------------------------------------------------
    # 6. Implementation Fidelity
    # -------------------------------------------------
    def _score_implementation_fidelity(self) -> int:
        """
        Static check: which claimed components are actually wired?
        """
        # Count implemented features
        total = len(self.features_implemented)
        implemented = sum(1 for v in self.features_implemented.values() if v)
        ratio = implemented / total
        
        if ratio == 1.0:
            return 4
        elif ratio >= 0.75:
            return 3
        elif ratio >= 0.5:
            return 2
        elif ratio > 0:
            return 1
        else:
            return 0
    
    # -------------------------------------------------
    # 7. Emergent Behavior
    # -------------------------------------------------
    def _score_emergent(self, input_text: str, response: str, context: Dict) -> int:
        """
        Look for: concepts in response not in input and not in direct co-occurrence,
        self-referential loops, paradoxes, surprising combinations.
        """
        input_words = set(re.findall(r'\b[a-z]{4,}\b', input_text.lower()))
        response_words = set(re.findall(r'\b[a-z]{4,}\b', response.lower()))
        
        # Concepts outside input
        novel_concepts = response_words - input_words
        if len(novel_concepts) == 0:
            return 0  # purely repeating input
        
        # Check distance in semantic network if available
        if self.collapse_engine:
            distance_scores = []
            for word in novel_concepts:
                min_dist = self._min_semantic_distance(word, input_words)
                if min_dist is not None and min_dist > 2:
                    distance_scores.append(min_dist)
            if distance_scores:
                avg_dist = sum(distance_scores) / len(distance_scores)
                if avg_dist > 3:
                    return 4
                elif avg_dist > 2:
                    return 3
                elif avg_dist > 1:
                    return 2
                else:
                    return 1
            else:
                return 1
        else:
            # Without network, just lexical novelty ratio
            novelty_ratio = len(novel_concepts) / len(response_words) if response_words else 0
            if novelty_ratio > 0.5:
                return 3
            elif novelty_ratio > 0.3:
                return 2
            elif novelty_ratio > 0.15:
                return 1
            else:
                return 0
    
    def _min_semantic_distance(self, target: str, source_words: set) -> Optional[int]:
        """
        Approximate graph distance in co-occurrence network.
        Returns shortest path length (edges) from any source word to target.
        Returns None if no path found within reasonable depth.
        """
        if not self.collapse_engine or target not in self.collapse_engine.co_occurrence:
            return None
        
        # BFS limited depth
        visited = set()
        queue = [(w, 1) for w in source_words if w in self.collapse_engine.co_occurrence]
        visited.update(source_words)
        
        while queue:
            current, depth = queue.pop(0)
            if current == target:
                return 0  # direct source matches (shouldn't happen if target novel)
            # Explore neighbors
            if current in self.collapse_engine.co_occurrence:
                for neighbor in self.collapse_engine.co_occurrence[current]:
                    if neighbor == target:
                        return depth
                    if neighbor not in visited:
                        visited.add(neighbor)
                        if depth < 5:  # limit search
                            queue.append((neighbor, depth+1))
        return None
    
    # -------------------------------------------------
    # 8. Question Generation Quality
    # -------------------------------------------------
    def _score_questions(self, questions: List[str], original_prompt: str) -> int:
        """
        Evaluate the internal questions the system generated about the user's input.
        """
        if not questions:
            return 0
        
        # Average length (too short = shallow)
        avg_len = sum(len(q.split()) for q in questions) / len(questions)
        if avg_len < 4:
            base = 1
        elif avg_len < 8:
            base = 2
        else:
            base = 3
        
        # Check for "deep" question words
        deep_words = {'why', 'how', 'what if', 'what would', 'could', 'should', 'implications', 'consequences', 'reframe', 'challenge'}
        deep_count = sum(1 for q in questions if any(dw in q.lower() for dw in deep_words))
        deep_ratio = deep_count / len(questions)
        
        # Check for repetition vs variety
        unique_first_words = set(q.split()[0].lower() if q.split() else '' for q in questions)
        variety = len(unique_first_words) / len(questions)
        
        # Combine
        score = base
        if deep_ratio > 0.5:
            score += 1
        if variety > 0.7:
            score += 1
        
        # Cap 4, floor 0
        score = max(0, min(4, score))
        return score


# Singleton instance
_evaluation_engine = None

def get_evaluation_engine(collapse_engine=None, markov=None, config: Dict = None):
    global _evaluation_engine
    if _evaluation_engine is None:
        _evaluation_engine = EvaluationEngine(collapse_engine, markov, config)
    return _evaluation_engine
