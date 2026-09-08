"""
ARGUMENT ANALYSIS V2 - Production-Ready
========================================

Multi-head argument analysis engine.
Detects: logical structure, semantic relationships, frameworks, intents.

Usage:
    from argument_analysis_v2 import ArgumentAnalyzer
    
    analyzer = ArgumentAnalyzer()
    analysis = analyzer.analyze(user_input, concepts)
    
Returns ArgumentSignature with 4 head outputs + synthesis.
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
import re


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class LogicalHead:
    """Output of Head 1: Logical Structure Analysis"""
    has_paradox: bool
    paradox_type: str  # 'self_reference', 'contradiction', 'infinite_regress', 'constraint'
    constraints: List[str]
    premises: List[str]
    conclusion: Optional[str]
    temporal_order: List[str]  # precedence relationships
    confidence: float


@dataclass
class SemanticHead:
    """Output of Head 2: Semantic Relationships"""
    concepts: List[str]
    central_concepts: List[Tuple[str, float]]  # (concept, importance)
    relationships: List[Tuple[str, str, str]]  # (c1, relation_type, c2)
    graph_density: float
    has_cycles: bool


@dataclass
class FrameworkHead:
    """Output of Head 3: Framework Detection"""
    primary_framework: str  # 'orch_or', 'logic', 'theology', 'metaphysics', 'epistemology'
    secondary_frameworks: List[str]
    framework_keywords: Dict[str, List[str]]  # framework → matching keywords
    confidence: float


@dataclass
class IntentHead:
    """Output of Head 4: Intent Extraction"""
    primary_intent: str  # 'reconcile_paradox', 'clarify', 'explore', 'justify', 'predict'
    is_question: bool
    core_question: Optional[str]
    target: str  # what is the intent directed at?
    urgency: float  # 0-1, how urgent/important


@dataclass
class ArgumentSignature:
    """Complete output of 4-head analysis"""
    logical: LogicalHead
    semantic: SemanticHead
    framework: FrameworkHead
    intent: IntentHead
    raw_text: str
    
    # Synthesis
    argument_type: str  # 'paradox_resolution', 'constraint_satisfaction', 'exploratory'
    is_paradigm_challenging: bool
    requires_careful_reasoning: bool
    
    def to_dict(self) -> Dict:
        return {
            'logical_pattern': self.logical.paradox_type,
            'has_paradox': self.logical.has_paradox,
            'constraints': self.logical.constraints,
            'concepts': self.semantic.concepts,
            'central_concepts': [c for c, _ in self.semantic.central_concepts],
            'primary_framework': self.framework.primary_framework,
            'intent': self.intent.primary_intent,
            'argument_type': self.argument_type,
        }


# ============================================================================
# HEAD 1: LOGICAL STRUCTURE ANALYSIS
# ============================================================================

class LogicalAnalyzer:
    """Detect paradoxes, constraints, temporal order."""
    
    PARADOX_PATTERNS = {
        'self_reference': [
            r'this statement',
            r'i cannot',
            r'logic.*cannot',
            r'god.*cannot.*god'
        ],
        'contradiction': [
            r'and\s+not\s+',
            r'both.*and',
            r'simultaneously',
            r'at\s+once'
        ],
        'infinite_regress': [
            r'caused by.*caused by',
            r'preceded by.*preceded',
            r'requires.*requires'
        ],
        'constraint': [
            r'how can.*both',
            r'how is it possible',
            r'if.*then.*but'
        ]
    }
    
    TEMPORAL_MARKERS = ['before', 'after', 'prior', 'precedes', 'follows', 'first', 'then']
    CONSTRAINT_MARKERS = ['must', 'cannot', 'impossible', 'necessarily', 'always', 'never', 'if.*then']
    
    def analyze(self, text: str) -> LogicalHead:
        """Detect logical structure."""
        text_lower = text.lower()
        
        # Detect paradox type
        paradox_type = self._detect_paradox_type(text_lower)
        has_paradox = paradox_type != 'none'
        
        # Extract constraints
        constraints = self._extract_constraints(text)
        
        # Extract premises
        premises = self._extract_premises(text)
        
        # Extract conclusion
        conclusion = self._extract_conclusion(text)
        
        # Temporal order
        temporal_order = self._extract_temporal_order(text)
        
        return LogicalHead(
            has_paradox=has_paradox,
            paradox_type=paradox_type,
            constraints=constraints,
            premises=premises,
            conclusion=conclusion,
            temporal_order=temporal_order,
            confidence=0.75
        )
    
    def _detect_paradox_type(self, text_lower: str) -> str:
        """Detect which type of paradox (if any)."""
        for ptype, patterns in self.PARADOX_PATTERNS.items():
            if any(re.search(p, text_lower) for p in patterns):
                return ptype
        return 'none'
    
    def _extract_constraints(self, text: str) -> List[str]:
        """Extract explicit constraints."""
        constraints = []
        
        # Look for "how can X and Y both..."
        match = re.search(r'how\s+(?:can|is)\s+(?:it\s+)?(?:possible\s+)?(.+?)\s+(?:both|and)\s+(.+?)[\?.]', text, re.IGNORECASE)
        if match:
            constraints.append(f"{match.group(1)} AND {match.group(2)}")
        
        # Look for "if X then Y but Z"
        match = re.search(r'if\s+(.+?)\s+then\s+(.+?)\s+but\s+(.+?)[\?.]', text, re.IGNORECASE)
        if match:
            constraints.append(f"IF {match.group(1)} THEN {match.group(2)} BUT {match.group(3)}")
        
        return constraints
    
    def _extract_premises(self, text: str) -> List[str]:
        """Extract logical premises."""
        premises = []
        
        for marker in ['since', 'because', 'given', 'assuming']:
            pattern = f'{marker}\\s+(.+?)(?:[.,;]|and|because)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            premises.extend(matches[:2])  # top 2
        
        return premises[:3]
    
    def _extract_conclusion(self, text: str) -> Optional[str]:
        """Extract likely conclusion."""
        for marker in ['therefore', 'thus', 'so', 'which means', 'implies']:
            pattern = f'{marker}\\s+(.+?)[\?.]'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_temporal_order(self, text: str) -> List[str]:
        """Extract temporal relationships (before, after, precedes)."""
        order = []
        text_lower = text.lower()
        
        for marker in self.TEMPORAL_MARKERS:
            if marker in text_lower:
                order.append(marker)
        
        return order


# ============================================================================
# HEAD 2: SEMANTIC RELATIONSHIPS
# ============================================================================

class SemanticAnalyzer:
    """Build concept graph, identify central concepts."""
    
    STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'of', 'for',
        'is', 'are', 'be', 'been', 'being', 'have', 'has', 'do', 'does', 'did',
        'that', 'this', 'these', 'those', 'it', 'its', 'as', 'with', 'by', 'from',
        'could', 'would', 'should', 'may', 'might', 'must', 'can', 'will', 'shall'
    }
    
    def analyze(self, text: str, extracted_concepts: List[str]) -> SemanticHead:
        """Build semantic graph."""
        
        # Use provided concepts + extract additional
        concepts = self._enrich_concepts(text, extracted_concepts)
        
        # Build relationships
        relationships = self._build_relationships(text, concepts)
        
        # Compute centrality
        central = self._compute_centrality(concepts, relationships)
        
        # Check for cycles
        has_cycles = self._detect_cycles(relationships)
        
        # Density
        if len(concepts) > 1:
            max_edges = len(concepts) * (len(concepts) - 1) / 2
            density = len(relationships) / max(max_edges, 1)
        else:
            density = 0.0
        
        return SemanticHead(
            concepts=concepts,
            central_concepts=central,
            relationships=relationships,
            graph_density=min(density, 1.0),
            has_cycles=has_cycles
        )
    
    def _enrich_concepts(self, text: str, extracted: List[str]) -> List[str]:
        """Combine provided concepts with extracted ones."""
        concepts = list(set(extracted))
        
        # Extract high-value nouns/proper nouns
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)  # Capitalized
        words.extend(re.findall(r'\b(?:god|god\'s|universe|reality|existence|consciousness|quantum|logic|being|nothingness|domain|realm)\b', text, re.IGNORECASE))
        
        concepts.extend(words)
        
        # Remove stopwords and duplicates
        concepts = [c.lower() for c in concepts if c.lower() not in self.STOPWORDS]
        concepts = list(dict.fromkeys(concepts))  # Preserve order, remove dups
        
        return concepts[:15]  # Cap at 15
    
    def _build_relationships(self, text: str, concepts: List[str]) -> List[Tuple[str, str, str]]:
        """Identify relationships between concepts."""
        relationships = []
        text_lower = text.lower()
        
        for i, c1 in enumerate(concepts):
            for c2 in concepts[i+1:]:
                if c1 in text_lower and c2 in text_lower:
                    # Find relationship type
                    rel_type = self._classify_relationship(text_lower, c1, c2)
                    relationships.append((c1, rel_type, c2))
        
        return relationships
    
    def _classify_relationship(self, text_lower: str, c1: str, c2: str) -> str:
        """Classify the type of relationship."""
        idx1 = text_lower.find(c1)
        idx2 = text_lower.find(c2)
        
        if idx1 > idx2:
            idx1, idx2 = idx2, idx1
            c1, c2 = c2, c1
        
        between = text_lower[idx1 + len(c1):idx2]
        
        if any(w in between for w in ['cause', 'create', 'produce', 'lead', 'result', 'implies', 'precedes']):
            return 'causal'
        elif any(w in between for w in ['vs', 'versus', 'instead', 'but', 'however', 'unlike', 'opposite']):
            return 'opposition'
        elif any(w in between for w in ['is', 'are', 'define', 'means', 'example', 'like']):
            return 'definition'
        elif any(w in between for w in ['and', 'both', 'together', 'with', ',']):
            return 'conjunction'
        else:
            return 'related'
    
    def _compute_centrality(self, concepts: List[str], relationships: List[Tuple[str, str, str]]) -> List[Tuple[str, float]]:
        """Compute concept importance (centrality)."""
        degree = {c: 0.0 for c in concepts}
        
        for c1, _, c2 in relationships:
            degree[c1] = degree.get(c1, 0.0) + 1
            degree[c2] = degree.get(c2, 0.0) + 1
        
        # Normalize
        if degree:
            max_deg = max(degree.values())
            if max_deg > 0:
                degree = {c: d / max_deg for c, d in degree.items()}
        
        return sorted([(c, s) for c, s in degree.items() if s > 0], key=lambda x: x[1], reverse=True)
    
    def _detect_cycles(self, relationships: List[Tuple[str, str, str]]) -> bool:
        """Detect circular references in relationship graph."""
        # Simple heuristic: if any concept appears in multiple relationships
        concept_count = {}
        for c1, _, c2 in relationships:
            concept_count[c1] = concept_count.get(c1, 0) + 1
            concept_count[c2] = concept_count.get(c2, 0) + 1
        
        # If many concepts appear 2+ times, likely has cycles
        return sum(1 for c in concept_count.values() if c >= 2) > len(concept_count) / 2


# ============================================================================
# HEAD 3: FRAMEWORK DETECTION
# ============================================================================

class FrameworkDetector:
    """Identify philosophical/theoretical frameworks."""
    
    FRAMEWORKS = {
        'orch_or': {
            'keywords': ['orchestrated', 'objective reduction', 'orch or', 'tubulin', 'microtubule', 'quantum consciousness', 'collapse', 'penrose', 'hameroff'],
            'concepts': ['quantum', 'consciousness', 'collapse', 'wave function'],
        },
        'logic': {
            'keywords': ['therefore', 'implies', 'contradiction', 'premise', 'deductive', 'logical', 'reasoning', 'inference', 'valid'],
            'concepts': ['logic', 'valid', 'contradiction', 'inference'],
        },
        'theology': {
            'keywords': ['god', 'divine', 'creation', 'soul', 'sacred', 'spirit', 'transcendent', 'realm', 'domain'],
            'concepts': ['god', 'creation', 'divine', 'realm'],
        },
        'metaphysics': {
            'keywords': ['being', 'existence', 'ontology', 'substance', 'essence', 'reality', 'nothingness', 'actual'],
            'concepts': ['existence', 'being', 'reality', 'ontology'],
        },
        'epistemology': {
            'keywords': ['knowledge', 'believe', 'justify', 'truth', 'certainty', 'know', 'epistemology'],
            'concepts': ['knowledge', 'truth', 'belief', 'justified'],
        },
        'quantum': {
            'keywords': ['quantum', 'superposition', 'entanglement', 'wave', 'measurement', 'probability', 'decoherence'],
            'concepts': ['quantum', 'wave', 'probability', 'measurement'],
        }
    }
    
    def analyze(self, text: str) -> FrameworkHead:
        """Detect frameworks."""
        text_lower = text.lower()
        
        scores = {}
        matched_keywords = {}
        
        for framework, data in self.FRAMEWORKS.items():
            score = 0
            keywords_matched = []
            
            for keyword in data['keywords']:
                if keyword in text_lower:
                    score += 1
                    keywords_matched.append(keyword)
            
            if score > 0:
                scores[framework] = score / len(data['keywords'])
                matched_keywords[framework] = keywords_matched
        
        if not scores:
            return FrameworkHead(
                primary_framework='general',
                secondary_frameworks=[],
                framework_keywords={},
                confidence=0.3
            )
        
        sorted_frameworks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_frameworks[0][0]
        secondary = [f for f, _ in sorted_frameworks[1:2]]
        
        return FrameworkHead(
            primary_framework=primary,
            secondary_frameworks=secondary,
            framework_keywords={f: matched_keywords.get(f, []) for f in [primary] + secondary},
            confidence=sorted_frameworks[0][1]
        )


# ============================================================================
# HEAD 4: INTENT EXTRACTION
# ============================================================================

class IntentExtractor:
    """Determine what the user is asking for."""
    
    INTENT_PATTERNS = {
        'reconcile_paradox': [
            r'how\s+(?:can|is)',
            r'both.*true',
            r'contradictory',
            r'reconcile'
        ],
        'clarify': [
            r'mean by',
            r'mean that',
            r'clarify',
            r'what do you',
            r'explain'
        ],
        'explore': [
            r'explore',
            r'think about',
            r'consider',
            r'what if',
            r'imagine'
        ],
        'justify': [
            r'why',
            r'justify',
            r'reason',
            r'support'
        ],
        'predict': [
            r'what would happen',
            r'predict',
            r'consequence',
            r'imply'
        ]
    }
    
    def analyze(self, text: str) -> IntentHead:
        """Extract user intent."""
        text_lower = text.lower()
        
        # Score intents
        intent_scores = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            score = sum(1 for p in patterns if re.search(p, text_lower, re.IGNORECASE))
            intent_scores[intent] = score
        
        if not intent_scores or max(intent_scores.values()) == 0:
            primary_intent = 'explore'
        else:
            primary_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
        
        # Is it a question?
        is_question = text.rstrip().endswith('?') or any(q in text_lower for q in ['what', 'why', 'how', 'is', 'does', 'can'])
        
        # Extract core question
        core_question = None
        if '?' in text:
            sentences = text.split('?')
            core_question = sentences[-2] if len(sentences) > 1 else None
        
        # Urgency (how many question marks, how complex)
        urgency = min(1.0, text.count('?') * 0.3 + (0.7 if is_question else 0))
        
        # Target
        target = self._extract_target(text)
        
        return IntentHead(
            primary_intent=primary_intent,
            is_question=is_question,
            core_question=core_question,
            target=target,
            urgency=urgency
        )
    
    def _extract_target(self, text: str) -> str:
        """What is the intent directed at?"""
        text_lower = text.lower()
        
        for word in ['god', 'consciousness', 'existence', 'reality', 'logic', 'universe', 'quantum']:
            if word in text_lower:
                return word
        
        return 'philosophical question'


# ============================================================================
# MAIN ANALYZER
# ============================================================================

class ArgumentAnalyzer:
    """Main entry point for 4-head analysis."""
    
    def __init__(self):
        self.logical_analyzer = LogicalAnalyzer()
        self.semantic_analyzer = SemanticAnalyzer()
        self.framework_detector = FrameworkDetector()
        self.intent_extractor = IntentExtractor()
    
    def analyze(self, user_input: str, concepts: List[str]) -> ArgumentSignature:
        """Run all 4 heads in parallel."""
        
        # All heads
        logical = self.logical_analyzer.analyze(user_input)
        semantic = self.semantic_analyzer.analyze(user_input, concepts)
        framework = self.framework_detector.analyze(user_input)
        intent = self.intent_extractor.analyze(user_input)
        
        # Synthesize
        argument_type = self._synthesize_argument_type(logical, intent, semantic)
        is_paradigm_challenging = logical.has_paradox or framework.primary_framework != 'general'
        requires_careful = logical.has_paradox or semantic.has_cycles or len(semantic.relationships) > 5
        
        return ArgumentSignature(
            logical=logical,
            semantic=semantic,
            framework=framework,
            intent=intent,
            raw_text=user_input,
            argument_type=argument_type,
            is_paradigm_challenging=is_paradigm_challenging,
            requires_careful_reasoning=requires_careful
        )
    
    def _synthesize_argument_type(self, logical: LogicalHead, intent: IntentHead, semantic: SemanticHead) -> str:
        """Determine overall argument type."""
        if logical.has_paradox:
            if intent.primary_intent == 'reconcile_paradox':
                return 'paradox_resolution'
            else:
                return 'paradox_exploration'
        elif intent.primary_intent == 'clarify':
            return 'clarification'
        elif len(semantic.relationships) > 5:
            return 'complex_relational'
        else:
            return 'exploratory'


def get_analyzer() -> ArgumentAnalyzer:
    """Singleton accessor."""
    global _analyzer
    if '_analyzer' not in globals():
        _analyzer = ArgumentAnalyzer()
    return _analyzer
