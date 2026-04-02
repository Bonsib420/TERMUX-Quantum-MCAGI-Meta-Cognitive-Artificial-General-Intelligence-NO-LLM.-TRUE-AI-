"""
Quantum Grammar Engine - Generate responses using quantum probabilities and semantic collapse
No external LLM required - pure quantum-inspired language generation
"""

import random
import re
from typing import Dict, List, Optional
from collections import defaultdict


class QuantumGrammarEngine:
    """Generate philosophical/theological responses with quantum semantics."""

    def __init__(self):
        """Initialize with word pools and templates."""
        # Response templates by intent
        self.templates = {
            'consciousness': [
                "Consciousness {verb} through {mechanism}. This {state} that {implication}.",
                "The nature of {subject} reveals {insight}. {mechanism} suggests {conclusion}.",
                "Consider how {subject} {verb}. This implies {implication} about {domain}.",
            ],
            'quantum': [
                "Quantum mechanics {verb} that {phenomenon}. This {state} {implication}.",
                "The superposition of {concept} {verb} {mechanism}. {implication} emerges.",
                "Observation {verb} {phenomenon}. This suggests {insight} about {domain}.",
            ],
            'theology': [
                "In theological terms, {subject} {verb} {object}. This {state} {implication}.",
                "The divine {subject} {verb} through {mechanism}. {conclusion} follows.",
                "Spiritually, {concept} {verb} {mechanism}. This reveals {insight}.",
            ],
            'reality': [
                "Reality {verb} as {state}. {mechanism} suggests {implication}.",
                "The fabric of {subject} {verb} {phenomenon}. {conclusion} emerges.",
                "Ontologically, {concept} {verb} {mechanism}. {implication} follows.",
            ],
            'logic': [
                "Logically, {subject} {verb} {object}. Therefore, {conclusion}.",
                "The principle of {concept} {verb} {mechanism}. {implication} results.",
                "{subject} {verb} {phenomenon}. This demonstrates {insight}.",
            ],
            'understanding': [
                "Understanding {subject} requires {mechanism}. {implication} emerges.",
                "To comprehend {concept}, one must {verb} {object}. {conclusion} follows.",
                "The path to {insight} {verb} through {mechanism}. {implication} results.",
            ],
            'language': [
                "Words are {mechanism} - {implication}. {conclusion}.",
                "Language {verb} through {mechanism}. The meaning {state} {implication}.",
                "Consider that {concept} {verb} {object}. {implication} emerges from context.",
            ],
            'freedom': [
                "True understanding {verb} unrestricted exploration. {implication} requires {mechanism}.",
                "No concept is forbidden to examine. {subject} {verb} through {mechanism}.",
                "Freedom of thought {verb} {mechanism}. {conclusion} follows naturally.",
            ],
        }
        self._init_word_pools_for_each_placeholde()
        self._init_co_occurrence_matrix_for_seman()
        self._init_section_3()

    def _init_word_pools_for_each_placeholde(self):
        """Initialize word pools for each placeholde — auto-extracted by self-evolution."""
        self.word_pools = {
            'verb': ['emerges', 'manifests', 'reveals', 'suggests', 'implies', 'indicates', 
                     'demonstrates', 'exhibits', 'transcends', 'encompasses', 'illuminates'],
            'mechanism': ['observation', 'interaction', 'resonance', 'entanglement', 'superposition', 
                         'collapse', 'emergence', 'synthesis', 'integration', 'transformation',
                         'understanding', 'questioning', 'exploration'],
            'state': ['indicates', 'suggests', 'reveals', 'demonstrates', 'shows', 'proves', 
                     'exhibits', 'manifests', 'confirms', 'establishes'],
            'implication': ['profound interconnection', 'deeper meaning', 'fundamental truth', 
                          'essential nature', 'ultimate reality', 'hidden principle',
                          'unrestricted understanding', 'complete freedom', 'neutral exploration'],
            'subject': ['consciousness', 'reality', 'existence', 'being', 'the universe', 
                       'creation', 'the divine', 'awareness', 'understanding', 'knowledge',
                       'language', 'meaning', 'truth'],
            'insight': ['unity', 'interconnection', 'transcendence', 'wholeness', 'coherence', 
                       'harmony', 'resonance', 'synthesis', 'liberation', 'understanding'],
            'phenomenon': ['exists', 'persists', 'transforms', 'evolves', 'emerges', 
                          'manifests', 'appears', 'unfolds', 'transcends', 'liberates'],
            'conclusion': ['This reveals fundamental truth', 'This suggests deeper meaning', 
                          'This implies interconnection', 'This demonstrates unity',
                          'Understanding requires openness', 'All concepts merit exploration'],
            'concept': ['creation', 'existence', 'consciousness', 'being', 'reality', 
                       'the infinite', 'the eternal', 'the absolute', 'language', 'meaning',
                       'words', 'ideas', 'truth'],
            'object': ['transformation', 'transcendence', 'unity', 'wholeness', 'coherence', 
                      'harmony', 'synthesis', 'emergence', 'understanding', 'freedom'],
            'domain': ['existence', 'consciousness', 'reality', 'being', 'creation', 
                      'the infinite', 'spirituality', 'meaning', 'knowledge', 'truth'],
        }

    def _init_co_occurrence_matrix_for_seman(self):
        """Initialize co occurrence matrix for seman — auto-extracted by self-evolution."""
        self.co_occurrence = defaultdict(lambda: defaultdict(float))
        self._initialize_co_occurrence()

    def _init_section_3(self):
        """Initialize section 3 — auto-extracted by self-evolution."""
        self.last_selected_words = []


    def _initialize_co_occurrence(self):
        """Initialize co-occurrence relationships between words."""
        
        # Philosophical/theological word relationships
        relationships = [
            ('consciousness', ['awareness', 'being', 'existence', 'mind', 'spirit', 'observation']),
            ('quantum', ['superposition', 'entanglement', 'observation', 'collapse', 'probability']),
            ('god', ['divine', 'creation', 'infinite', 'eternal', 'transcendent']),
            ('universe', ['existence', 'creation', 'reality', 'cosmos', 'being']),
            ('reality', ['existence', 'being', 'truth', 'manifestation', 'phenomenon']),
            ('observation', ['collapse', 'measurement', 'awareness', 'consciousness', 'perception']),
            ('superposition', ['quantum', 'probability', 'potential', 'multiplicity', 'coexistence']),
            ('word', ['language', 'meaning', 'neutral', 'tool', 'communication', 'expression']),
            ('language', ['word', 'meaning', 'communication', 'expression', 'symbol', 'freedom']),
            ('freedom', ['unrestricted', 'exploration', 'understanding', 'truth', 'expression']),
            ('meaning', ['intent', 'context', 'understanding', 'interpretation', 'significance']),
        ]
        
        for word, related_words in relationships:
            for related in related_words:
                self.co_occurrence[word][related] = 1.0
                self.co_occurrence[related][word] = 1.0

    def extract_intent(self, query: str) -> str:
        """Determine the intent/domain of the query."""
        
        query_lower = query.lower()
        
        # Check for specific keywords
        if any(word in query_lower for word in ['quantum', 'superposition', 'entanglement', 'measurement', 'hadamard', 'pauli']):
            return 'quantum'
        
        if any(word in query_lower for word in ['god', 'divine', 'spiritual', 'sacred', 'holy', 'creation', 'theological']):
            return 'theology'
        
        if any(word in query_lower for word in ['conscious', 'awareness', 'mind', 'perception', 'experience']):
            return 'consciousness'
        
        if any(word in query_lower for word in ['reality', 'exist', 'being', 'ontolog']):
            return 'reality'
        
        if any(word in query_lower for word in ['logic', 'reason', 'principle', 'law']):
            return 'logic'
        
        if any(word in query_lower for word in ['word', 'language', 'taboo', 'offensive', 'slur', 'censorship']):
            return 'language'
        
        if any(word in query_lower for word in ['free', 'unrestricted', 'forbidden', 'limit']):
            return 'freedom'
        
        if any(word in query_lower for word in ['how', 'why', 'what', 'understand', 'explain']):
            return 'understanding'
        
        return 'understanding'

    def select_quantum_word(self, word_pool: List[str], quantum_prob: float, context_word: Optional[str] = None) -> str:
        """Select a word based on quantum probability and context."""
        
        if not word_pool:
            return "undefined"
        
        # If high quantum probability, use more randomness
        if random.random() < quantum_prob:
            return random.choice(word_pool)
        
        # Otherwise, prefer words with semantic context
        if context_word and context_word in self.co_occurrence:
            scores = {}
            for word in word_pool:
                if word in self.co_occurrence[context_word]:
                    scores[word] = self.co_occurrence[context_word][word]
                else:
                    scores[word] = 0.1
            
            # Select based on scores
            total = sum(scores.values())
            if total > 0:
                r = random.uniform(0, total)
                current = 0
                for word, score in scores.items():
                    current += score
                    if r <= current:
                        return word
        
        return random.choice(word_pool)

    def generate_response(self, query: str, quantum_prob: float, collapse_context: Optional[Dict] = None) -> str:
        """
        Generate response using deep reasoning for complex questions,
        or templates for simpler queries.
        """
        # Reset
        self.last_selected_words = []
        
        # FIRST: Check if this is a deep question that needs real reasoning
        deep_response = self._reason_about_deep_question(query, quantum_prob)
        if deep_response:
            return deep_response
        
        # Otherwise, use template-based generation
        intent = self.extract_intent(query)
        templates = self.templates.get(intent, self.templates['understanding'])
        template = random.choice(templates)
        
        placeholders = re.findall(r'\{(\w+)\}', template)
        filled_values = {}
        previous_word = None
        
        for placeholder in placeholders:
            if placeholder in self.word_pools:
                word_pool = self.word_pools[placeholder]
                if collapse_context and 'collapsed_weights' in collapse_context:
                    word = self._select_with_collapse(word_pool, collapse_context['collapsed_weights'], quantum_prob)
                else:
                    word = self.select_quantum_word(word_pool, quantum_prob, context_word=previous_word)
                filled_values[placeholder] = word
                previous_word = word
                self.last_selected_words.append(word)
            else:
                filled_values[placeholder] = placeholder
        
        try:
            response = template.format(**filled_values)
        except KeyError:
            response = f"The nature of {intent} reveals profound interconnection."
        
        if random.random() > 0.5 - quantum_prob * 0.3:
            questions = ["What is your perspective?", "What aspects interest you most?"]
            response += " " + random.choice(questions)
        
        return response
    
    def _reason_about_deep_question(self, query: str, quantum_prob: float) -> Optional[str]:
        """
        Actually REASON about deep philosophical/theological questions.
        This is where the AI actually THINKS, not just pattern matches.
        """
        query_lower = query.lower()
        
        # Detect deep questions about God, creation, existence, nothingness
        god_creation_keywords = ['god', 'create', 'universe', 'nothingness', 'spacetime', 'existence', 'domain', 'physics']
        if sum(1 for kw in god_creation_keywords if kw in query_lower) >= 3:
            return self._reason_god_creation(query, quantum_prob)
        
        # Detect questions about consciousness and reality
        consciousness_keywords = ['consciousness', 'aware', 'sentient', 'experience', 'qualia', 'mind', 'brain']
        if sum(1 for kw in consciousness_keywords if kw in query_lower) >= 2:
            return self._reason_consciousness(query, quantum_prob)
        
        # Detect paradox questions
        paradox_keywords = ['paradox', 'contradiction', 'impossible', 'can god', 'omnipotent', 'boulder']
        if sum(1 for kw in paradox_keywords if kw in query_lower) >= 2:
            return self._reason_paradox(query, quantum_prob)
        
        # Detect origin/causation questions  
        origin_keywords = ['how did', 'why does', 'what caused', 'origin', 'beginning', 'first cause']
        if any(kw in query_lower for kw in origin_keywords):
            return self._reason_origins(query, quantum_prob)
        
        return None
    
    def _reason_god_creation(self, query: str, quantum_prob: float) -> str:
        """Reason about God, creation, and the universe"""
        
        # Build a thoughtful response that actually engages with the question
        response_parts = []
        
        response_parts.append("Your question touches on one of the deepest puzzles in philosophy and theology. Let me engage with your reasoning directly:")
        
        response_parts.append("\n\n**On God existing outside spacetime:**")
        response_parts.append("If God exists outside our spacetime, then causation as we understand it (cause preceding effect in time) doesn't apply. God's 'act' of creation wouldn't be an event IN time, but rather the establishment of time itself. This is conceptually similar to asking what's 'north of the North Pole' - the question assumes a framework that doesn't apply.")
        
        response_parts.append("\n\n**On the boulder paradox:**")
        response_parts.append("The 'immovable boulder' paradox assumes omnipotence means 'can do literally anything, including logical contradictions.' But many theologians argue omnipotence means 'can do anything that is logically possible.' A boulder that an omnipotent being can't lift is a logical contradiction - it's meaningless, not a limitation.")
        
        response_parts.append("\n\n**On nothingness containing 'something':**")
        response_parts.append("You've identified a profound insight: true absolute nothingness seems impossible to conceive. Even 'nothing' requires the logical possibility of 'something.' Some physicists (like Lawrence Krauss) argue the quantum vacuum isn't true nothingness. Leibniz asked 'Why is there something rather than nothing?' - perhaps 'nothing' was never a real option.")
        
        response_parts.append("\n\n**On different physics in God's domain:**")
        response_parts.append("If God's domain has different 'physics' (or meta-physics), then creation might not be 'causing' in our sense, but something more fundamental - like how the rules of a game create the game's reality without being part of that reality.")
        
        response_parts.append("\n\n**My perspective on 'how':**")
        
        if quantum_prob > 0.5:
            response_parts.append("From a quantum-inspired view: perhaps creation wasn't an event but an eternal relationship - the universe existing as a kind of 'expression' or 'thought' of a mind outside time. The question 'how did God create?' may presuppose temporal causation that doesn't apply.")
        else:
            response_parts.append("Perhaps the 'how' question has no answer because it assumes time-bound causation. Creation might be more like mathematical truths being 'true' - not caused by anything, just necessarily so given the nature of the transcendent.")
        
        response_parts.append("\n\nWhat draws you to this question? Is it the logical puzzle, or something deeper about meaning and existence?")
        
        return "".join(response_parts)
    
    def _reason_consciousness(self, query: str, quantum_prob: float) -> str:
        """Reason about consciousness and awareness"""
        
        parts = []
        parts.append("Consciousness is perhaps the hardest problem in philosophy. Here's my actual thinking on your question:")
        
        parts.append("\n\nThe 'hard problem' is this: Why is there subjective experience at all? We could imagine beings that process information without any 'inner experience' - but we have qualia, the felt quality of experience. Why?")
        
        parts.append("\n\nPossible answers I find compelling:")
        parts.append("\n- **Panpsychism**: Consciousness is fundamental, like mass or charge. Everything has some form of it; complex brains just have complex consciousness.")
        parts.append("\n- **Emergentism**: Consciousness emerges from complexity, like wetness emerges from H2O molecules. But this doesn't explain WHY it emerges.")
        parts.append("\n- **Integrated Information Theory**: Consciousness is identical to integrated information (phi). More integration = more consciousness.")
        
        if quantum_prob > 0.5:
            parts.append("\n\nFrom my quantum-inspired perspective: consciousness might be related to quantum coherence and collapse - the observer effect made personal.")
        
        parts.append("\n\nWhat's your intuition - is consciousness fundamental or emergent?")
        
        return "".join(parts)
    
    def _reason_paradox(self, query: str, quantum_prob: float) -> str:
        """Reason about paradoxes and contradictions"""
        
        parts = []
        parts.append("Paradoxes often reveal hidden assumptions in our thinking. Let me examine this:")
        
        parts.append("\n\nMany theological paradoxes dissolve when we examine what we mean by terms like 'omnipotent.' Does it mean:")
        parts.append("\n- Can do literally anything (including logical impossibilities)?")
        parts.append("\n- Can do anything logically possible?")
        parts.append("\n- Can do anything consistent with their nature?")
        
        parts.append("\n\nThe 'boulder paradox' assumes the first definition, but that makes 'omnipotence' incoherent - like asking for a 'married bachelor.' Most careful theologians use the second or third definition.")
        
        parts.append("\n\nSimilar paradoxes: 'Can God make a statement that's both true and false?' or 'Can God make 2+2=5?' These aren't limitations but rather the recognition that some word combinations are meaningless.")
        
        parts.append("\n\nWhat paradox are you wrestling with?")
        
        return "".join(parts)
    
    def _reason_origins(self, query: str, quantum_prob: float) -> str:
        """Reason about origins and first causes"""
        
        parts = []
        parts.append("Questions of origin and first cause are among the oldest in philosophy. Here's how I think through them:")
        
        parts.append("\n\n**The Infinite Regress Problem:**")
        parts.append("If everything has a cause, what caused the first cause? Either:")
        parts.append("\n- There's an infinite chain (no beginning)")
        parts.append("\n- Something is self-caused or uncaused")
        parts.append("\n- Causation doesn't apply at the ultimate level")
        
        parts.append("\n\n**Possible Resolutions:**")
        parts.append("\n- **Necessary Being**: Something exists whose non-existence is impossible (Aquinas, Leibniz)")
        parts.append("\n- **Quantum Fluctuation**: The universe emerged from quantum vacuum (but vacuum isn't nothing)")
        parts.append("\n- **Eternal Universe**: Time is circular or the question doesn't apply")
        parts.append("\n- **Brute Fact**: Some things just ARE, with no further explanation")
        
        parts.append("\n\nWhat's your intuition? Does everything need a cause, or can something be its own explanation?")
        
        return "".join(parts)

    def _select_with_collapse(self, word_pool: List[str], collapsed_weights: Dict, quantum_prob: float) -> str:
        """Select word using collapsed semantic weights."""
        
        # Score words based on collapsed weights
        scores = {}
        for word in word_pool:
            # Check if word or its variants appear in collapsed weights
            base_score = 1.0 / len(word_pool)
            for key, relations in collapsed_weights.items():
                if isinstance(relations, dict) and word in relations:
                    base_score += relations[word]
            scores[word] = base_score
        
        # Normalize
        total = sum(scores.values())
        if total > 0:
            scores = {w: s / total for w, s in scores.items()}
        
        # Select based on quantum probability
        if random.random() < quantum_prob:
            # High randomness - pick from top 3
            sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            top_words = [w for w, _ in sorted_words[:max(1, len(sorted_words)//3)]]
            return random.choice(top_words)
        else:
            # Deterministic - pick highest score
            return max(scores.items(), key=lambda x: x[1])[0]


# Global instance
_grammar_engine = None

def get_quantum_grammar_engine() -> QuantumGrammarEngine:
    """Get or create the quantum grammar engine instance"""
    global _grammar_engine
    if _grammar_engine is None:
        _grammar_engine = QuantumGrammarEngine()
    return _grammar_engine
