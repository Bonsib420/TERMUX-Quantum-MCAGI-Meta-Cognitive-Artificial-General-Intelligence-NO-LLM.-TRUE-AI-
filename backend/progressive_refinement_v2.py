"""
PROGRESSIVE REFINEMENT V2 - Production-Ready
==============================================

Universal 4-layer refinement pipeline.
Input: ArgumentSignature (from argument_analysis_v2)
Output: ConstraintVector (guides routing and generation)

Works for ANY philosophical question, ANY domain, ANY intent.
Not specialized for one case — engineered for all cases.

Layers:
1. Concept Enrichment - Add domain context, abstraction level, relevance
2. Relationship Mapping - Build semantic graph, identify patterns
3. Argument Classification - Determine response strategy
4. Constraint Generation - Produce routing and generation constraints
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from argument_analysis_v2 import ArgumentSignature, LogicalHead, SemanticHead, FrameworkHead, IntentHead


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class EnrichedConcept:
    """A concept with metadata after Layer 1."""
    name: str
    abstraction_level: float  # 0-1, how abstract
    domain: str  # philosophy, physics, theology, etc.
    is_central: bool
    requires_explanation: bool
    framework_relevance: float  # 0-1, how relevant to detected framework


@dataclass
class Layer1Output:
    """Concept enrichment layer output."""
    enriched_concepts: List[EnrichedConcept]
    concept_count: int
    abstraction_score: float  # avg abstraction level
    domain_diversity: int  # how many domains covered


@dataclass
class RelationshipPattern:
    """A pattern in the concept relationships."""
    concepts: List[str]
    pattern_type: str  # 'causal_chain', 'opposition', 'definition', 'hierarchy'
    strength: float  # 0-1


@dataclass
class Layer2Output:
    """Relationship mapping layer output."""
    concept_graph: Dict[str, List[str]]
    patterns: List[RelationshipPattern]
    graph_density: float
    circularity_score: float  # 0-1, how circular


@dataclass
class Layer3Output:
    """Argument classification layer output."""
    response_archetype: str  # 'paradox_resolution', 'constraint_satisfaction', etc.
    required_depth: float  # 0-1, minimum response depth
    required_structure: str  # 'linear', 'dialectical', 'exploratory'
    reasoning_steps: int  # estimated min steps needed
    confidence: float


@dataclass
class ConstraintVector:
    """Final output — guides routing and generation."""
    
    # Routing weights (0-1, higher = route to this generator)
    entelechy_weight: float
    hybrid_weight: float
    casual_weight: float
    
    # Depth and structure
    required_depth: float  # 0-1
    preferred_style: str  # 'Socratic', 'Analytic', 'Holistic', 'Poetic'
    reasoning_steps: int
    
    # Content constraints
    must_address: List[str]  # concepts/constraints that MUST be in response
    should_mention: List[str]  # concepts that SHOULD be mentioned
    must_apply_framework: str  # which framework to apply
    must_acknowledge: List[str]  # aspects user must see acknowledged
    
    # Avoidance
    avoid_patterns: List[str]  # 'oversimplification', 'hand_waving', 'circular_reasoning'
    
    # Temperature and generation hints
    temperature_hint: float  # 0-1, 0.3=precise, 0.9=creative
    length_hint: str  # 'brief', 'medium', 'long'
    
    # Meta
    confidence: float
    justification: str  # why these constraints


# ============================================================================
# LAYER 1: CONCEPT ENRICHMENT
# ============================================================================

class ConceptEnricher:
    """Enrich concepts with domain and abstraction metadata."""
    
    ABSTRACTION_LEVELS = {
        # High abstraction
        'existence': 0.95,
        'consciousness': 0.95,
        'reality': 0.90,
        'being': 0.90,
        'nothingness': 0.95,
        'god': 0.90,
        'soul': 0.85,
        'mind': 0.85,
        'logic': 0.80,
        'truth': 0.85,
        'knowledge': 0.80,
        'essence': 0.90,
        
        # Medium abstraction
        'quantum': 0.60,
        'consciousness': 0.70,
        'universe': 0.65,
        'dimension': 0.60,
        'law': 0.65,
        'potential': 0.70,
        'structure': 0.55,
        
        # Lower abstraction
        'particle': 0.35,
        'atom': 0.30,
        'brain': 0.40,
        'wave': 0.45,
        'energy': 0.50,
    }
    
    DOMAINS = {
        'philosophy': ['existence', 'being', 'consciousness', 'truth', 'knowledge', 'reality', 'god', 'soul', 'logic'],
        'physics': ['quantum', 'particle', 'wave', 'energy', 'spacetime', 'field', 'dimension'],
        'theology': ['god', 'divine', 'creation', 'soul', 'sacred', 'spirit', 'realm', 'domain'],
        'epistemology': ['knowledge', 'truth', 'belief', 'justified', 'certainty', 'know'],
        'metaphysics': ['being', 'existence', 'substance', 'essence', 'reality', 'ontology', 'nothingness'],
        'cosmology': ['universe', 'cosmos', 'creation', 'spacetime', 'dimension', 'realm'],
    }
    
    def enrich(self, signature: ArgumentSignature) -> Layer1Output:
        """Enrich all concepts."""
        enriched = []
        
        for concept in signature.semantic.concepts:
            concept_lower = concept.lower()
            
            # Abstraction level
            abstraction = self.ABSTRACTION_LEVELS.get(concept_lower, 0.5)
            
            # Domain
            domain = self._classify_domain(concept_lower)
            
            # Is it central?
            central_names = [c for c, _ in signature.semantic.central_concepts]
            is_central = concept_lower in [cn.lower() for cn in central_names]
            
            # Framework relevance
            fw_relevance = self._compute_framework_relevance(concept_lower, signature.framework.primary_framework)
            
            # Requires explanation
            requires_explanation = abstraction > 0.65
            
            enriched.append(EnrichedConcept(
                name=concept,
                abstraction_level=abstraction,
                domain=domain,
                is_central=is_central,
                requires_explanation=requires_explanation,
                framework_relevance=fw_relevance
            ))
        
        # Sort by importance: central + high framework relevance
        enriched.sort(key=lambda c: (c.is_central, c.framework_relevance), reverse=True)
        
        # Compute aggregate scores
        abstraction_score = sum(c.abstraction_level for c in enriched) / max(len(enriched), 1)
        domains = set(c.domain for c in enriched)
        
        return Layer1Output(
            enriched_concepts=enriched,
            concept_count=len(enriched),
            abstraction_score=abstraction_score,
            domain_diversity=len(domains)
        )
    
    def _classify_domain(self, concept: str) -> str:
        """Classify concept into domain."""
        for domain, keywords in self.DOMAINS.items():
            if any(kw in concept for kw in keywords):
                return domain
        return 'general'
    
    def _compute_framework_relevance(self, concept: str, framework: str) -> float:
        """How relevant is this concept to the framework?"""
        framework_keywords = {
            'orch_or': ['quantum', 'consciousness', 'collapse', 'tubulin', 'wave'],
            'logic': ['logic', 'valid', 'contradiction', 'inference', 'premise'],
            'theology': ['god', 'divine', 'creation', 'soul', 'realm'],
            'metaphysics': ['being', 'existence', 'substance', 'essence', 'ontology'],
            'epistemology': ['knowledge', 'truth', 'belief', 'justified'],
            'quantum': ['quantum', 'superposition', 'entanglement', 'wave', 'measurement'],
        }
        
        keywords = framework_keywords.get(framework, [])
        if any(kw in concept for kw in keywords):
            return 0.9
        else:
            return 0.4


# ============================================================================
# LAYER 2: RELATIONSHIP MAPPING
# ============================================================================

class RelationshipMapper:
    """Map relationships, detect patterns."""
    
    PATTERN_TEMPLATES = {
        'causal_chain': {
            'markers': ['causes', 'leads to', 'results in', 'produces', 'creates'],
            'strength': 0.9
        },
        'opposition': {
            'markers': ['opposes', 'contradicts', 'versus', 'unlike', 'opposite'],
            'strength': 0.85
        },
        'hierarchy': {
            'markers': ['contains', 'includes', 'part of', 'level', 'layer'],
            'strength': 0.80
        },
        'definition': {
            'markers': ['defines', 'means', 'is', 'exemplifies'],
            'strength': 0.75
        },
        'dependency': {
            'markers': ['depends on', 'requires', 'needs', 'presupposes'],
            'strength': 0.85
        },
    }
    
    def map(self, signature: ArgumentSignature, layer1: Layer1Output) -> Layer2Output:
        """Map relationships and detect patterns."""
        
        # Build concept graph from relationships
        graph = {}
        for c1, rel_type, c2 in signature.semantic.relationships:
            if c1 not in graph:
                graph[c1] = []
            graph[c1].append(c2)
            
            if c2 not in graph:
                graph[c2] = []
            graph[c2].append(c1)
        
        # Detect patterns
        patterns = self._detect_patterns(signature.semantic.relationships)
        
        # Circularity score
        circularity = self._compute_circularity_score(graph, signature.semantic.has_cycles)
        
        return Layer2Output(
            concept_graph=graph,
            patterns=patterns,
            graph_density=signature.semantic.graph_density,
            circularity_score=circularity
        )
    
    def _detect_patterns(self, relationships: List[Tuple[str, str, str]]) -> List[RelationshipPattern]:
        """Detect patterns in relationships."""
        patterns = []
        
        # Group by relationship type
        rel_groups = {}
        for c1, rel_type, c2 in relationships:
            if rel_type not in rel_groups:
                rel_groups[rel_type] = []
            rel_groups[rel_type].append((c1, c2))
        
        # Turn groups into patterns
        for rel_type, pairs in rel_groups.items():
            if len(pairs) >= 2:
                # Extract concepts involved
                concepts = set()
                for c1, c2 in pairs:
                    concepts.add(c1)
                    concepts.add(c2)
                
                patterns.append(RelationshipPattern(
                    concepts=list(concepts),
                    pattern_type=rel_type,
                    strength=min(len(pairs) / 5, 1.0)  # strength ~ frequency
                ))
        
        return patterns
    
    def _compute_circularity_score(self, graph: Dict, has_cycles: bool) -> float:
        """Compute how circular the argument is."""
        if not has_cycles:
            return 0.0
        
        # If cycles, estimate density
        if not graph:
            return 0.0
        
        # Count edges in cycles (approximate)
        cycle_edges = sum(len(neighbors) for neighbors in graph.values()) / max(len(graph), 1)
        return min(cycle_edges / 3, 1.0)  # normalize


# ============================================================================
# LAYER 3: ARGUMENT CLASSIFICATION
# ============================================================================

class ArgumentClassifier:
    """Classify argument type and determine response strategy."""
    
    # Map: (logical pattern, intent) → (archetype, required depth, structure)
    STRATEGY_MAP = {
        ('paradox', 'reconcile_paradox'): {
            'archetype': 'paradox_resolution',
            'depth': 0.85,
            'structure': 'dialectical',
            'steps': 5,
        },
        ('paradox', 'explore'): {
            'archetype': 'paradox_exploration',
            'depth': 0.80,
            'structure': 'exploratory',
            'steps': 4,
        },
        ('constraint', 'reconcile_paradox'): {
            'archetype': 'constraint_satisfaction',
            'depth': 0.75,
            'structure': 'analytical',
            'steps': 4,
        },
        ('contradiction', 'clarify'): {
            'archetype': 'contradiction_resolution',
            'depth': 0.70,
            'structure': 'linear',
            'steps': 3,
        },
        (None, 'clarify'): {
            'archetype': 'clarification',
            'depth': 0.50,
            'structure': 'linear',
            'steps': 2,
        },
        (None, 'explore'): {
            'archetype': 'exploratory',
            'depth': 0.65,
            'structure': 'exploratory',
            'steps': 3,
        },
    }
    
    def classify(self, signature: ArgumentSignature, layer2: Layer2Output) -> Layer3Output:
        """Classify the argument and determine response strategy."""
        
        # Get base strategy
        key = (signature.logical.paradox_type if signature.logical.has_paradox else None,
               signature.intent.primary_intent)
        
        strategy = self.STRATEGY_MAP.get(key)
        
        # Fallback
        if not strategy:
            # Use defaults based on just intent
            default_key = (None, signature.intent.primary_intent)
            strategy = self.STRATEGY_MAP.get(default_key, {
                'archetype': 'exploratory',
                'depth': 0.60,
                'structure': 'exploratory',
                'steps': 3,
            })
        
        # Adjust depth based on argument complexity
        base_depth = strategy['depth']
        
        # Increase if circular
        if layer2.circularity_score > 0.5:
            base_depth = min(1.0, base_depth + 0.15)
        
        # Increase if many relationships
        if layer2.graph_density > 0.6:
            base_depth = min(1.0, base_depth + 0.10)
        
        # Increase if multi-domain
        if signature.semantic.graph_density > 0.7:
            base_depth = min(1.0, base_depth + 0.10)
        
        return Layer3Output(
            response_archetype=strategy['archetype'],
            required_depth=base_depth,
            required_structure=strategy['structure'],
            reasoning_steps=strategy['steps'],
            confidence=0.80
        )


# ============================================================================
# LAYER 4: CONSTRAINT GENERATION
# ============================================================================

class ConstraintGenerator:
    """Generate final constraint vector."""
    
    # Routing weights by archetype
    ROUTING_BY_ARCHETYPE = {
        'paradox_resolution': {'entelechy': 0.90, 'hybrid': 0.15, 'casual': 0.05},
        'paradox_exploration': {'entelechy': 0.85, 'hybrid': 0.20, 'casual': 0.05},
        'constraint_satisfaction': {'entelechy': 0.60, 'hybrid': 0.70, 'casual': 0.10},
        'contradiction_resolution': {'entelechy': 0.70, 'hybrid': 0.50, 'casual': 0.15},
        'clarification': {'entelechy': 0.20, 'hybrid': 0.50, 'casual': 0.80},
        'exploratory': {'entelechy': 0.50, 'hybrid': 0.60, 'casual': 0.30},
    }
    
    # Style by structure + framework
    STYLE_MAP = {
        ('dialectical', 'logic'): 'Socratic',
        ('dialectical', 'theology'): 'Mystical',
        ('dialectical', 'metaphysics'): 'Analytical',
        ('analytical', 'logic'): 'Analytical',
        ('analytical', 'physics'): 'Technical',
        ('exploratory', 'theology'): 'Poetic',
        ('exploratory', 'metaphysics'): 'Holistic',
        ('linear', 'epistemology'): 'Analytical',
    }
    
    def generate(self, signature: ArgumentSignature, layer1: Layer1Output,
                 layer2: Layer2Output, layer3: Layer3Output) -> ConstraintVector:
        """Generate final constraint vector."""
        
        # Routing weights
        archetype = layer3.response_archetype
        routing = self.ROUTING_BY_ARCHETYPE.get(archetype, {
            'entelechy': 0.50, 'hybrid': 0.50, 'casual': 0.20
        })
        
        # Normalize
        total = sum(routing.values())
        routing = {k: v / total for k, v in routing.items()}
        
        # Adjust by confidence
        routing['entelechy'] *= layer3.confidence
        routing['hybrid'] *= layer3.confidence
        
        # Style
        style_key = (layer3.required_structure, signature.framework.primary_framework)
        preferred_style = self.STYLE_MAP.get(style_key, 'Analytical')
        
        # Must address (from logical analysis)
        must_address = signature.logical.constraints.copy()
        
        # Should mention (central concepts)
        should_mention = [c for c, _ in signature.semantic.central_concepts[:3]]
        
        # Avoid patterns
        avoid = []
        if layer2.circularity_score > 0.6:
            avoid.append('circular_reasoning')
        if layer3.required_depth > 0.75:
            avoid.append('oversimplification')
        if signature.framework.primary_framework != 'logic':
            avoid.append('over-formalization')
        
        # Temperature hint
        temp = 0.3 if layer3.required_structure == 'analytical' else 0.6
        if signature.intent.primary_intent == 'explore':
            temp = 0.7
        
        # Length hint
        if layer3.required_depth > 0.80:
            length = 'long'
        elif layer3.required_depth > 0.60:
            length = 'medium'
        else:
            length = 'brief'
        
        return ConstraintVector(
            entelechy_weight=routing['entelechy'],
            hybrid_weight=routing['hybrid'],
            casual_weight=routing['casual'],
            required_depth=layer3.required_depth,
            preferred_style=preferred_style,
            reasoning_steps=layer3.reasoning_steps,
            must_address=must_address,
            should_mention=should_mention,
            must_apply_framework=signature.framework.primary_framework,
            must_acknowledge=self._compute_must_acknowledge(signature),
            avoid_patterns=avoid,
            temperature_hint=temp,
            length_hint=length,
            confidence=layer3.confidence,
            justification=self._justify_constraints(signature, layer3)
        )
    
    def _compute_must_acknowledge(self, signature: ArgumentSignature) -> List[str]:
        """What must be acknowledged in the response?"""
        ack = []
        
        if signature.logical.has_paradox:
            ack.append('the paradox')
        
        if signature.semantic.has_cycles:
            ack.append('circular_dependencies')
        
        if signature.framework.primary_framework != 'general':
            ack.append(f'framework_{signature.framework.primary_framework}')
        
        if len(signature.logical.constraints) > 0:
            ack.append('user_constraints')
        
        return ack
    
    def _justify_constraints(self, signature: ArgumentSignature, layer3: Layer3Output) -> str:
        """Justify the constraint choices."""
        reasons = []
        
        if signature.logical.has_paradox:
            reasons.append(f"Paradox detected ({signature.logical.paradox_type})")
        
        if signature.intent.is_question:
            reasons.append(f"User is asking ({signature.intent.primary_intent})")
        
        if signature.framework.primary_framework != 'general':
            reasons.append(f"Framework: {signature.framework.primary_framework}")
        
        reasons.append(f"Archetype: {layer3.response_archetype}")
        
        return " | ".join(reasons)


# ============================================================================
# MAIN REFINER
# ============================================================================

class ProgressiveRefiner:
    """Main refinement engine — 4 layers."""
    
    def __init__(self):
        self.enricher = ConceptEnricher()
        self.mapper = RelationshipMapper()
        self.classifier = ArgumentClassifier()
        self.generator = ConstraintGenerator()
    
    def refine(self, signature: ArgumentSignature) -> ConstraintVector:
        """Run all 4 layers and produce constraint vector."""
        
        # Layer 1: Concept enrichment
        layer1 = self.enricher.enrich(signature)
        
        # Layer 2: Relationship mapping
        layer2 = self.mapper.map(signature, layer1)
        
        # Layer 3: Argument classification
        layer3 = self.classifier.classify(signature, layer2)
        
        # Layer 4: Constraint generation
        constraints = self.generator.generate(signature, layer1, layer2, layer3)
        
        return constraints


def get_refiner() -> ProgressiveRefiner:
    """Singleton accessor."""
    global _refiner
    if '_refiner' not in globals():
        _refiner = ProgressiveRefiner()
    return _refiner
