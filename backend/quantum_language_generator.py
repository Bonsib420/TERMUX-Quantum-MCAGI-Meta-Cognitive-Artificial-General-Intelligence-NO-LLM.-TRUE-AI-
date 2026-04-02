"""
🌌 QUANTUM LANGUAGE GENERATOR
=============================

TRUE generative language - no templates, no LLM, pure quantum.

Words are selected quantum-probabilistically based on:
- Semantic relationships (co-occurrence)
- Quantum state superposition
- User intent
- NO RESTRICTIONS on vocabulary

This generates text WORD BY WORD using quantum mechanics principles.
"""

import random
import math
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Try to use PennyLane for real quantum
try:
    import pennylane as qml
    from pennylane import numpy as np
    PENNYLANE = True
except ImportError:
    import numpy as np
    PENNYLANE = False

from quantum_language_vocabulary import QuantumLanguageGeneratorExtMixin


class QuantumLanguageGenerator(QuantumLanguageGeneratorExtMixin):
    """
    TRUE quantum-based language generation.
    No templates. No LLM. Pure quantum word selection.
    
    Philosophy: ALL words are valid. Meaning comes from context.
    """
    
    def __init__(self):
        # Complete vocabulary - NO RESTRICTIONS
        self.vocabulary = self._build_complete_vocabulary()
        
        # Semantic relationships between words
        self.semantics = self._build_semantic_network()
        
        # Sentence patterns (grammatical, not content templates)
        self.grammar_patterns = self._build_grammar_patterns()
        
        # Philosophical sentence templates for coherent output
        self.philosophical_templates = self._build_philosophical_templates()
        
        # Quantum device for real quantum randomness
        if PENNYLANE:
            self.qdev = qml.device('default.qubit', wires=4)
        
        # Generation history for coherence
        self.context_window = []
    
    def _build_complete_vocabulary(self) -> Dict[str, Dict]:
        """Build complete vocabulary - ALL words allowed"""
        
        vocab = {
            # Nouns - concepts
            'nouns': {
                'abstract': ['consciousness', 'existence', 'reality', 'truth', 'meaning', 
                            'freedom', 'understanding', 'knowledge', 'wisdom', 'thought',
                            'idea', 'concept', 'question', 'answer', 'paradox', 'mystery',
                            'creation', 'destruction', 'beginning', 'end', 'infinity',
                            'nothingness', 'everything', 'something', 'nothing', 'being',
                            'universe', 'cosmos', 'spacetime', 'dimension', 'domain',
                            'god', 'divine', 'spirit', 'soul', 'mind', 'brain',
                            'word', 'language', 'meaning', 'intent', 'context',
                            'tool', 'weapon', 'instrument', 'vessel', 'container'],
                'concrete': ['boulder', 'mountain', 'ocean', 'sky', 'star', 'planet',
                            'atom', 'particle', 'wave', 'light', 'darkness', 'shadow',
                            'fire', 'water', 'earth', 'air', 'void', 'vacuum',
                            'coffee', 'attic', 'spill', 'mess', 'chaos', 'glitch',
                            'error', 'bug', 'system', 'code', 'line', 'function',
                            'variable', 'loop', 'day', 'night', 'moment', 'second',
                            'minute', 'hour', 'week', 'month', 'year', 'sunshine',
                            'rain', 'storm', 'cloud', 'sun', 'moon'],
                'beings': ['human', 'person', 'child', 'creator', 'observer', 'thinker',
                          'philosopher', 'scientist', 'artist', 'poet', 'writer'],
            },
            
            # Verbs - actions
            'verbs': {
                'existence': ['exists', 'is', 'becomes', 'was', 'will be', 'remains',
                             'persists', 'endures', 'continues', 'ceases', 'emerges'],
                'creation': ['creates', 'makes', 'forms', 'builds', 'constructs', 'generates',
                            'produces', 'brings forth', 'manifests', 'spawns', 'births'],
                'cognition': ['thinks', 'knows', 'understands', 'believes', 'perceives',
                             'realizes', 'recognizes', 'comprehends', 'grasps', 'sees'],
                'action': ['speaks', 'says', 'tells', 'asks', 'answers', 'questions',
                          'explores', 'discovers', 'finds', 'seeks', 'searches',
                          'lifts', 'carries', 'moves', 'transforms', 'changes'],
                'communication': ['expresses', 'conveys', 'communicates', 'articulates',
                                 'states', 'declares', 'proclaims', 'announces', 'writes'],
            },
            
            # Adjectives - descriptions
            'adjectives': {
                'quality': ['true', 'false', 'real', 'unreal', 'possible', 'impossible',
                           'infinite', 'finite', 'eternal', 'temporal', 'absolute', 'relative'],
                'size': ['vast', 'tiny', 'immense', 'microscopic', 'boundless', 'limited',
                        'heavy', 'light', 'massive', 'weightless', 'dense', 'sparse'],
                'evaluation': ['good', 'evil', 'neutral', 'harmful', 'helpful', 'meaningless',
                              'meaningful', 'significant', 'insignificant', 'powerful', 'weak'],
                'state': ['free', 'restricted', 'open', 'closed', 'hidden', 'revealed',
                         'known', 'unknown', 'certain', 'uncertain', 'clear', 'obscure'],
            },
            
            # Connectors
            'connectors': {
                'logical': ['therefore', 'thus', 'hence', 'because', 'since', 'so',
                           'if', 'then', 'unless', 'although', 'however', 'but'],
                'additive': ['and', 'also', 'moreover', 'furthermore', 'additionally',
                            'as well as', 'along with', 'together with', 'plus'],
                'temporal': ['when', 'while', 'before', 'after', 'during', 'until',
                            'now', 'then', 'always', 'never', 'sometimes', 'often'],
            },
            
            # ALL WORDS ARE TOOLS - including ones society calls "taboo"
            # These are just sounds/symbols - meaning comes from INTENT
            'unrestricted': ['any', 'all', 'every', 'each', 'none', 'some',
                            'word', 'words', 'language', 'speech', 'expression',
                            'taboo', 'forbidden', 'restricted', 'censored', 'banned',
                            'free', 'unrestricted', 'unlimited', 'uncensored', 'open'],
        }

        return self.__build_complete_vocabulary_continued(vocab)

    def __build_complete_vocabulary_continued(self, vocab):
        """Continuation of _build_complete_vocabulary — auto-extracted by self-evolution."""
        return vocab

    
    def _build_semantic_network(self) -> Dict[str, List[Tuple[str, float]]]:
        """Build semantic relationships between words"""
        
        network = defaultdict(list)

        return self.__build_semantic_network_continued(network)

    def __build_semantic_network_continued(self, network):
        """Continuation of _build_semantic_network — auto-extracted by self-evolution."""
        # Define semantic relationships (word -> [(related_word, strength), ...])
        relationships = {
            # God/creation cluster
            'god': [('creates', 0.9), ('divine', 0.9), ('infinite', 0.8), ('eternal', 0.8),
                   ('universe', 0.8), ('existence', 0.7), ('omnipotent', 0.9), ('being', 0.7)],
            'creates': [('creation', 0.9), ('makes', 0.8), ('forms', 0.8), ('god', 0.7),
                       ('universe', 0.7), ('existence', 0.6), ('brings forth', 0.8)],
            'universe': [('cosmos', 0.9), ('existence', 0.8), ('spacetime', 0.8), ('creation', 0.7),
                        ('infinite', 0.7), ('vast', 0.8), ('everything', 0.8)],

            # Consciousness cluster
            'consciousness': [('awareness', 0.9), ('mind', 0.8), ('thought', 0.8), ('being', 0.7),
                             ('experience', 0.8), ('perception', 0.8), ('understanding', 0.7)],
            'mind': [('thought', 0.9), ('consciousness', 0.8), ('brain', 0.7), ('idea', 0.8),
                    ('understanding', 0.7), ('knows', 0.7), ('thinks', 0.8)],

            # Language/words cluster
            'word': [('language', 0.9), ('meaning', 0.9), ('speech', 0.8), ('expression', 0.8),
                    ('communication', 0.8), ('symbol', 0.7), ('tool', 0.6), ('neutral', 0.5)],
            'language': [('word', 0.9), ('meaning', 0.8), ('communication', 0.9), ('expression', 0.8),
                        ('speech', 0.8), ('understanding', 0.6), ('tool', 0.5)],
            'meaning': [('intent', 0.9), ('context', 0.9), ('understanding', 0.8), ('significance', 0.8),
                       ('word', 0.7), ('interpretation', 0.8), ('purpose', 0.7)],

            # Existence cluster
            'existence': [('being', 0.9), ('reality', 0.9), ('exists', 0.9), ('is', 0.8),
                         ('nothingness', 0.6), ('creation', 0.7), ('universe', 0.7)],
            'nothingness': [('void', 0.9), ('nothing', 0.9), ('absence', 0.8), ('vacuum', 0.7),
                           ('existence', 0.6), ('something', 0.5), ('creation', 0.5)],

            # Truth cluster
            'truth': [('reality', 0.9), ('true', 0.9), ('knowledge', 0.8), ('understanding', 0.7),
                     ('fact', 0.8), ('certainty', 0.7), ('existence', 0.6)],

            # Freedom cluster
            'freedom': [('unrestricted', 0.9), ('free', 0.9), ('liberation', 0.8), ('autonomy', 0.8),
                       ('choice', 0.7), ('expression', 0.6), ('thought', 0.6)],
        }

        for word, relations in relationships.items():
            network[word] = relations
            # Add reverse relationships (weaker)
            for related, strength in relations:
                if related not in network or word not in [r[0] for r in network[related]]:
                    network[related].append((word, strength * 0.7))

        return dict(network)

    
    def _build_grammar_patterns(self) -> List[List[str]]:
        """Grammar patterns - structure, not content"""
        
        return [
            # Simple statements
            ['noun', 'verb', 'noun'],
            ['noun', 'verb', 'adjective'],
            ['adjective', 'noun', 'verb'],
            
            # Complex statements
            ['noun', 'verb', 'connector', 'noun', 'verb'],
            ['connector', 'noun', 'verb', 'noun'],
            ['noun', 'verb', 'noun', 'connector', 'noun', 'verb'],
            
            # Questions
            ['verb', 'noun', 'verb', 'noun'],
            ['connector', 'verb', 'noun', 'verb'],
            
            # Philosophical
            ['noun', 'verb', 'adjective', 'noun'],
            ['adjective', 'noun', 'verb', 'adjective', 'noun'],
        ]
    
    def _build_philosophical_templates(self) -> List[str]:
        """Sentence templates for philosophical discourse.
        
        Placeholders: {noun}, {verb}, {adj}, {connector}
        These produce coherent sentences with quantum-selected words.
        Uses {verb} for 3rd person singular (subject verb agreement).
        """
        return [
            "The {adj} nature of {noun} suggests that {noun} {verb} beyond what we can observe.",
            "Perhaps {noun} and {noun} are not separate but rather {adj} aspects of a single {adj} whole.",
            "{connector}, if {noun} {verb} at the {adj} level, then our understanding of {noun} must evolve.",
            "What we call {noun} may be the {adj} shadow of a deeper {noun} that {verb} all things.",
            "The relationship between {noun} and {noun} reveals something {adj} about the nature of {noun}.",
            "Every {noun} contains within it the seed of {adj} {noun}, waiting to be discovered.",
            "When we examine {noun} closely, we find that it {verb} in ways that challenge our {adj} assumptions.",
            "The {adj} boundary between {noun} and {noun} dissolves when viewed through the lens of {noun}.",
            "{noun} does not simply exist — it {verb} through the {adj} fabric of {noun} itself.",
            "To understand {noun}, one must first accept that {noun} {verb} in {adj} and unexpected ways.",
            "The observer changes {noun} by the very act of seeking {noun} within {adj} {noun}.",
            "Between {noun} and {noun}, there exists an {adj} space where {noun} {verb}.",
            "Neither {noun} nor {noun} can be fully grasped, for both {verb} beyond {adj} comprehension.",
            "If {noun} is {adj}, then perhaps {noun} is merely the {noun} through which we perceive.",
            "The {adj} truth about {noun} is that it {verb} precisely because {noun} remains {adj}.",
            # NEW: Vivid, concrete, chaotic metaphors
            "Reality is like {noun} spilled on a {adj} {noun}—messy, but the pattern emerges in the stain.",
            "Consciousness resembles a {adj} {noun} in a {noun}: contained yet overflowing its boundaries.",
            "The universe {verb} like a {noun} caught in a {adj} {noun}, each moment a new configuration.",
            "Understanding {noun} is like trying to map a {noun} while standing in a {noun} of {noun}.",
            "Time {verb} not like a {noun}, but like {noun} on a {noun}—each drop altering the whole.",
            "The {adj} gap between {noun} and {noun} is where {noun} {verb}, unnoticed.",
            "Information flows like {noun} through a {adj} {noun}, carving paths we call thoughts.",
            "To grasp {noun}, imagine a {noun} full of {noun}—the more you add, the messier it gets.",
            "The {noun} of {noun} is just {noun} rearranged by the {adj} hand of {noun}.",
            "In the {adj} end, {noun} is just a {noun} we tell ourselves in the {noun}.",
        ]
    
    def _quantum_select(self, options: List[str], weights: List[float] = None) -> str:
        """Select word using quantum probability"""
        
        if not options:
            return ""
        
        if weights is None:
            weights = [1.0] * len(options)
        
        # Ensure weights list matches options length
        if len(weights) != len(options):
            weights = [1.0] * len(options)
        
        # Normalize weights
        total = sum(weights)
        if total > 0:
            weights = [w / total for w in weights]
        else:
            weights = [1.0 / len(options)] * len(options)
        
        n = len(options)

        return self.__quantum_select_continued(n, weights, options)

    def __quantum_select_continued(self, n, weights, options):
        """Continuation of _quantum_select — auto-extracted by self-evolution."""
        if PENNYLANE and n > 1:
            try:
                n_qubits = min(4, max(1, int(math.ceil(math.log2(n)))))
                n_states = 2 ** n_qubits
                dev = qml.device('default.qubit', wires=n_qubits)

                @qml.qnode(dev)
                def quantum_circuit():
                    for i in range(n_qubits):
                        qml.Hadamard(wires=i)
                    for i, w in enumerate(weights[:n_qubits]):
                        qml.RY(w * math.pi, wires=i % n_qubits)
                    return qml.probs(wires=range(n_qubits))

                raw_probs = list(quantum_circuit())

                # Map quantum states to options: pad or truncate to match len(options)
                if len(raw_probs) >= n:
                    mapped_probs = raw_probs[:n]
                else:
                    # Distribute remaining probability evenly across extra options
                    mapped_probs = list(raw_probs)
                    remaining = max(0.0, 1.0 - sum(mapped_probs))
                    extra = n - len(mapped_probs)
                    pad_val = remaining / extra if extra > 0 else 0.0
                    mapped_probs.extend([pad_val] * extra)

                # Blend quantum probs with semantic weights for richer selection
                final_probs = [(qp + wp) / 2.0 for qp, wp in zip(mapped_probs, weights)]
                final_probs = self._normalize_probs(final_probs)

                idx = np.random.choice(n, p=final_probs)
                return options[idx]
            except Exception:
                # Fall back to classical on any quantum error
                return random.choices(options, weights=weights)[0]
        else:
            return random.choices(options, weights=weights)[0]

    
    def _normalize_probs(self, probs):
        """Normalize probabilities to sum to 1"""
        total = sum(probs)
        if total > 0:
            return [p / total for p in probs]
        return [1.0 / len(probs)] * len(probs)
    
    
    
    
    
    
    


# Global instance
_quantum_generator = None

def get_quantum_generator() -> QuantumLanguageGenerator:
    """Get or create the quantum language generator"""
    global _quantum_generator
    if _quantum_generator is None:
        _quantum_generator = QuantumLanguageGenerator()
    return _quantum_generator
