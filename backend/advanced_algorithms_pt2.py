"""
Auto-split from advanced_algorithms.py by self-evolution engine.
Part 2 — contains: ConceptGraph, DynamicTemperature, BayesianBeliefs, AdvancedAlgorithmicEngine, get_advanced_engine
"""

import math
import re
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
from advanced_algorithms import GrammarEngine, ConversationContext, ReasoningEngine, SemanticSimilarity

# Singleton instance
_advanced_engine = None

class ConceptGraph:
    """
    Knowledge graph with weighted edges.
    
    Supports:
    - Adding concepts and relationships
    - Path finding between concepts
    - Spreading activation
    """
    
    def __init__(self):
        self.nodes = set()
        self.edges = defaultdict(dict)  # node -> {neighbor: weight}
    
    def add_concept(self, concept: str):
        """Add a concept node."""
        self.nodes.add(concept.lower())
    
    def add_relationship(self, concept1: str, concept2: str, 
                         relationship: str = "related", weight: float = 1.0):
        """Add weighted edge between concepts."""
        c1, c2 = concept1.lower(), concept2.lower()
        self.nodes.add(c1)
        self.nodes.add(c2)
        
        # Bidirectional
        self.edges[c1][c2] = max(self.edges[c1].get(c2, 0), weight)
        self.edges[c2][c1] = max(self.edges[c2].get(c1, 0), weight)
    
    def get_neighbors(self, concept: str, min_weight: float = 0.1) -> List[Tuple[str, float]]:
        """Get neighboring concepts above weight threshold."""
        c = concept.lower()
        if c not in self.edges:
            return []
        
        neighbors = [(n, w) for n, w in self.edges[c].items() if w >= min_weight]
        neighbors.sort(key=lambda x: x[1], reverse=True)
        return neighbors
    
    def spreading_activation(self, start: str, decay: float = 0.7, 
                            max_depth: int = 3) -> Dict[str, float]:
        """
        Spreading activation from start node.
        Returns activation levels for all reached nodes.
        """
        c = start.lower()
        if c not in self.nodes:
            return {c: 1.0}
        
        activations = {c: 1.0}
        current_level = {c}
        
        for depth in range(max_depth):
            next_level = set()
            current_activation = decay ** depth
            
            for node in current_level:
                for neighbor, weight in self.edges.get(node, {}).items():
                    if neighbor not in activations:
                        act = current_activation * weight
                        activations[neighbor] = act
                        if act > 0.1:  # Threshold
                            next_level.add(neighbor)
            
            if not next_level:
                break
            current_level = next_level
        
        return activations
    
    def path_between(self, start: str, end: str, max_depth: int = 5) -> Optional[List[str]]:
        """Find path between two concepts (BFS)."""
        s, e = start.lower(), end.lower()
        if s not in self.nodes or e not in self.nodes:
            return None
        
        if s == e:
            return [s]
        
        visited = {s}
        queue = [(s, [s])]
        
        while queue and len(visited) < 1000:
            current, path = queue.pop(0)
            
            for neighbor in self.edges.get(current, {}):
                if neighbor == e:
                    return path + [neighbor]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
            
            if len(path) >= max_depth:
                continue
        
        return None


class DynamicTemperature:
    """
    Adjusts generation temperature based on query characteristics.
    
    - Factual queries → low temperature (deterministic)
    - Creative queries → high temperature (diverse)
    - Follow-up queries → medium temperature (coherent)
    """
    
    def __init__(self):
        self.factual_keywords = {
            'what is', 'who is', 'when', 'where', 'how many', 'how much',
            'define', 'calculate', 'convert', 'distance', 'population'
        }
        self.creative_keywords = {
            'imagine', 'create', 'write', 'poem', 'story', 'invent',
            'suppose', 'what if', 'dream', 'fantasy', 'explore'
        }
        self.philosophical_keywords = {
            'why', 'meaning', 'purpose', 'consciousness', 'existence',
            'believe', 'think', 'feel', 'opinion', 'perspective'
        }
    
    def compute(self, query: str, is_followup: bool = False) -> float:
        """
        Compute optimal temperature for query.
        
        Returns float in [0.3, 1.5]
        """
        query_lower = query.lower()
        
        # Check query type
        is_factual = any(kw in query_lower for kw in self.factual_keywords)
        is_creative = any(kw in query_lower for kw in self.creative_keywords)
        is_philosophical = any(kw in query_lower for kw in self.philosophical_keywords)
        
        # Base temperature
        if is_factual:
            temp = 0.4  # Low - be precise
        elif is_creative:
            temp = 1.2  # High - be diverse
        elif is_philosophical:
            temp = 0.9  # Medium-high - thoughtful variation
        else:
            temp = 0.7  # Default
        
        # Adjust for follow-up
        if is_followup:
            temp *= 0.85  # Reduce to maintain coherence
        
        # Query length adjustment (longer = more complex = slightly higher)
        words = len(query.split())
        if words > 15:
            temp += 0.1
        
        # Clamp
        return max(0.3, min(1.5, temp))


class BayesianBeliefs:
    """
    Maintains beliefs about concepts using Bayesian updating.
    
    P(H|E) = P(E|H) × P(H) / P(E)
    """
    
    def __init__(self):
        self.beliefs = defaultdict(lambda: 0.5)  # Prior = 0.5 (uncertain)
        self.evidence_counts = defaultdict(lambda: {'positive': 0, 'negative': 0})
    
    def observe(self, concept: str, evidence: str, is_positive: bool):
        """Update belief based on evidence."""
        c = concept.lower()
        
        if is_positive:
            self.evidence_counts[c]['positive'] += 1
        else:
            self.evidence_counts[c]['negative'] += 1
        
        # Bayesian update
        pos = self.evidence_counts[c]['positive']
        neg = self.evidence_counts[c]['negative']
        total = pos + neg
        
        # Beta distribution mean
        # Prior: alpha=1, beta=1 (uniform)
        self.beliefs[c] = (pos + 1) / (total + 2)
    
    def get_belief(self, concept: str) -> float:
        """Get current belief strength."""
        return self.beliefs[concept.lower()]
    
    def get_confident_beliefs(self, threshold: float = 0.7) -> List[Tuple[str, float]]:
        """Get beliefs above confidence threshold."""
        confident = [(c, b) for c, b in self.beliefs.items() if b >= threshold]
        confident.sort(key=lambda x: x[1], reverse=True)
        return confident
    
    def uncertainty(self, concept: str) -> float:
        """Measure uncertainty about a concept (entropy)."""
        p = self.beliefs[concept.lower()]
        if p <= 0 or p >= 1:
            return 0
        return -p * math.log2(p) - (1-p) * math.log2(1-p)


class AdvancedAlgorithmicEngine:
    """
    Integrates all advanced improvements into cohesive system.
    """
    
    def __init__(self):
        self.grammar = GrammarEngine()
        self.context = ConversationContext()
        self.reasoning = ReasoningEngine()
        self.similarity = SemanticSimilarity()
        self.graph = ConceptGraph()
        self.temperature = DynamicTemperature()
        self.beliefs = BayesianBeliefs()
        
        # Initialize with some reasoning rules
        self._init_reasoning_rules()
    
    def _init_reasoning_rules(self):
        """Add basic reasoning rules."""
        rules = [
            ("consciousness exists", "experience is possible", 0.9),
            ("information is processed", "computation occurs", 0.95),
            ("learning occurs", "behavior changes", 0.85),
            ("observation happens", "knowledge increases", 0.8),
            ("questions are asked", "understanding deepens", 0.75),
        ]
        for cond, conc, conf in rules:
            self.reasoning.add_rule(cond, conc, conf)
    
    def enhance_response(self, response: str, query: str, concepts: List[str]) -> str:
        """Apply all enhancements to a response."""
        # 1. Grammar fix (pass query for better cleaning)
        response = self.grammar.fix(response, query=query)
        
        # 2. Update context
        self.context.add_turn(query, response, concepts)
        
        # 3. Update concept graph
        for i, c1 in enumerate(concepts):
            for c2 in concepts[i+1:]:
                self.graph.add_relationship(c1, c2, "co-occurred", 0.5)
        
        return response
    
    def get_temperature(self, query: str) -> float:
        """Get optimal temperature for query."""
        is_followup = self.context.is_followup(query)
        return self.temperature.compute(query, is_followup)
    
    def get_context_boost(self, concepts: List[str]) -> List[str]:
        """Get additional concepts from context and graph."""
        boosted = set(concepts)
        
        # From conversation context
        boosted.update(self.context.get_context_concepts(3))
        
        # From concept graph (spreading activation)
        for c in concepts[:2]:
            activations = self.graph.spreading_activation(c, max_depth=2)
            top_activated = sorted(activations.items(), key=lambda x: x[1], reverse=True)[:3]
            boosted.update(c for c, _ in top_activated)
        
        return list(boosted)
    
    def reason_about(self, query: str) -> List[str]:
        """Get reasoning chain for query."""
        results = self.reasoning.infer(query)
        chains = []
        for conclusion, conf, chain in results:
            if conf > 0.5:
                chains.extend(chain)
        return chains


def get_advanced_engine() -> AdvancedAlgorithmicEngine:
    """Get singleton advanced engine."""
    global _advanced_engine
    if _advanced_engine is None:
        _advanced_engine = AdvancedAlgorithmicEngine()
    return _advanced_engine

