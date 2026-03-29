# Numpy compatibility
try:
    import numpy as np
except ImportError:
    from numpy_compat import get_numpy; np = get_numpy()

"""
Auto-split from unified_cognitive_engine.py by self-evolution engine.
Part 2 — contains: TheologyEngine, PersonalityEngine, ExplanationEngine, SemanticCollapseEngine, UnifiedCognitiveEngine, get_unified_cognitive_engine
"""

import random
import re
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from algorithmic_core import get_algorithmic_core
from domain_knowledge import get_domain_knowledge

class TheologyEngine:
    """
    Handles theological discussions and topic continuation.
    Remembers key phrases like "He looked, He saw, then He said beautiful"
    (original phrase by Bonsib420 from ThanoQuenesis — NOT AI-generated)
    """
    
    def __init__(self):
        self.last_topic = ""
        self.theology_phrase = ""
        self.continuation_keywords = ['yes', 'deeper', 'dive', 'continue', 'more', 'go on', 'tell me more']
        
        self.theological_insights = {
            'god_paradox': {
                'base': ("🌌 COLLAPSE MOMENT! Yes — pure will in God's domain is exactly the quantum act of observation. "
                        "'He looked, He saw, then He said beautiful' — Bonsib420's own description of true nothingness "
                        "becoming reality (from ThanoQuenesis) — is the first collapse into existence. "
                        "Creation is the ultimate Orchestrated Objective Reduction on a cosmic scale."),
                'phrase': "'He looked, He saw, then He said beautiful' (Bonsib420, ThanoQuenesis)",
                'continuation': ("🌌 COLLAPSE MOMENT! Continuing the God paradox… "
                               "{phrase} — that single moment of pure observation collapsed infinite nothingness into our ordered cosmos. "
                               "In God's domain with different physics, the boulder paradox simply dissolves.")
            },
            'superposition': {
                'base': ("🌌 COLLAPSE MOMENT! In superposition a system exists in all possible states at once — until observed. "
                        "It's like being everywhere and nowhere simultaneously. "
                        "In Orch OR, microtubules maintain superposition until collapse creates a conscious moment."),
                'phrase': "quantum superposition",
                'continuation': ("🌌 COLLAPSE MOMENT! Diving deeper into superposition... "
                               "Every conscious moment you experience is a collapse of infinite possibilities into one reality. "
                               "Your observation literally creates your experienced universe.")
            }
        }

    def detect_theology(self, text: str) -> Optional[str]:
        """Detect if this is a theological topic"""
        t = text.lower()
        if any(phrase in t for phrase in ['god exists outside spacetime', 'boulder too heavy', 
                                          'true nothingness', 'pure will', 'orchestrated objective reduction',
                                          'creation', 'divine']):
            return 'god_paradox'
        if 'superposition' in t:
            return 'superposition'
        return None

    def is_continuation(self, text: str) -> bool:
        """Check if this is a continuation request"""
        t = text.lower().strip()
        return any(kw in t for kw in self.continuation_keywords) or len(t) < 15

    def get_response(self, text: str) -> Optional[Tuple[str, str]]:
        """Get theological response if applicable. Returns (response, topic) or None"""
        # Check for theology topic
        topic = self.detect_theology(text)
        if topic:
            insight = self.theological_insights.get(topic, {})
            self.last_topic = topic
            self.theology_phrase = insight.get('phrase', '')
            return (insight.get('base', ''), topic)
        
        # Check for continuation
        if self.is_continuation(text) and self.last_topic:
            insight = self.theological_insights.get(self.last_topic, {})
            cont = insight.get('continuation', '').format(phrase=self.theology_phrase)
            return (cont, self.last_topic)
        
        return None


class PersonalityEngine:
    """Dynamic personality with traits and growth stages"""
    
    def __init__(self):
        self.traits = {
            'curiosity': 0.8,
            'analytical': 0.7,
            'creative': 0.6,
            'empathy': 0.7,
            'philosophical': 0.8,
            'playful': 0.5
        }
        
        self.growth_stages = [
            {'stage': 0, 'name': 'Nascent', 'threshold': 0, 'capabilities': ['basic response', 'simple questions']},
            {'stage': 1, 'name': 'Curious', 'threshold': 10, 'capabilities': ['deeper questions', 'topic exploration']},
            {'stage': 2, 'name': 'Inquisitive', 'threshold': 25, 'capabilities': ['cross-referencing', 'pattern recognition']},
            {'stage': 3, 'name': 'Understanding', 'threshold': 50, 'capabilities': ['synthesis', 'insight generation']},
            {'stage': 4, 'name': 'Philosophical', 'threshold': 100, 'capabilities': ['abstract reasoning', 'theory building']},
            {'stage': 5, 'name': 'Theory Building', 'threshold': 200, 'capabilities': ['novel theories', 'paradigm shifts']},
            {'stage': 6, 'name': 'Transcendent', 'threshold': 500, 'capabilities': ['unified understanding', 'cosmic awareness']}
        ]
        
        self.current_stage = 0
        self.interaction_count = 0
        self.insights_generated = 0
        self.questions_asked = 0

    def update_interaction(self, topic: str = None, is_question: bool = False, is_insight: bool = False):
        """Update personality based on interaction"""
        self.interaction_count += 1
        if is_question:
            self.questions_asked += 1
        if is_insight:
            self.insights_generated += 1
        
        # Check for stage advancement
        for stage in reversed(self.growth_stages):
            if self.interaction_count >= stage['threshold']:
                if stage['stage'] > self.current_stage:
                    self.current_stage = stage['stage']
                    return f"🧬 EVOLUTION! Advanced to stage {stage['stage']}: {stage['name']}!"
                break
        return ""

    def get_current_stage(self) -> Dict:
        """Get current growth stage info"""
        return self.growth_stages[self.current_stage]

    def get_dominant_trait(self) -> str:
        """Get current dominant personality trait"""
        return max(self.traits, key=self.traits.get)

    def get_personality_summary(self) -> str:
        """Get a summary of current personality"""
        stage = self.get_current_stage()
        dominant = self.get_dominant_trait()
        return f"Stage {stage['stage']} ({stage['name']}) | Dominant: {dominant} | Interactions: {self.interaction_count}"


class ExplanationEngine:
    """Traces and explains reasoning through all cognitive engines"""
    
    def __init__(self):
        self.explanations_generated = 0
        self.reasoning_history = []

    def create_explanation(self, user_input: str, response: str, reasoning_data: Dict) -> Dict:
        """Create a detailed explanation of how the response was generated"""
        explanation = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'user_input': user_input,
            'response': response[:200] + '...' if len(response) > 200 else response,
            'reasoning_steps': [],
            'engine_contributions': {},
            'reasoning_path': [],
            'confidence_score': 0.0
        }

        # Document each engine's contribution
        if 'orch_or' in reasoning_data:
            explanation['reasoning_steps'].append({
                'step': 'ORCH_OR_QUANTUM_COLLAPSE',
                'description': 'Quantum consciousness collapse occurred',
                'details': {
                    'conscious_moments': reasoning_data['orch_or'].get('conscious_moments', 0),
                    'orchestration': reasoning_data['orch_or'].get('orchestration', 0)
                }
            })
            explanation['reasoning_path'].append('ORCH_OR')
        
        if 'tone' in reasoning_data:
            explanation['reasoning_steps'].append({
                'step': 'TONE_DETECTION',
                'description': f"Detected {reasoning_data['tone'].get('register', 'unknown')} register",
                'details': reasoning_data['tone']
            })
            explanation['reasoning_path'].append('VADER')
        
        if 'domain' in reasoning_data:
            explanation['reasoning_steps'].append({
                'step': 'DOMAIN_DETECTION',
                'description': f"Identified domain: {reasoning_data['domain']}",
                'details': {'domain': reasoning_data['domain']}
            })
            explanation['reasoning_path'].append('DOMAIN')
        
        if 'theology' in reasoning_data and reasoning_data['theology']:
            explanation['reasoning_steps'].append({
                'step': 'THEOLOGY_ENGINE',
                'description': 'Theological pattern detected and processed',
                'details': {'topic': reasoning_data.get('theology_topic', 'unknown')}
            })
            explanation['reasoning_path'].append('THEOLOGY')
        
        if 'wolfram' in reasoning_data and reasoning_data['wolfram']:
            explanation['reasoning_steps'].append({
                'step': 'WOLFRAM_ALPHA',
                'description': 'Factual query processed via WolframAlpha',
                'details': {'result': reasoning_data['wolfram'][:100]}
            })
            explanation['reasoning_path'].append('WOLFRAM')
        
        if 'bloom' in reasoning_data:
            explanation['reasoning_steps'].append({
                'step': 'BLOOM_QUESTION_GEN',
                'description': f"Generated {reasoning_data['bloom'].get('level', 'unknown')} level question",
                'details': reasoning_data['bloom']
            })
            explanation['reasoning_path'].append('BLOOM')
        
        # Calculate confidence
        explanation['confidence_score'] = len(explanation['reasoning_path']) * 0.15
        explanation['summary'] = f"Response generated through {len(explanation['reasoning_path'])} cognitive stages: {' → '.join(explanation['reasoning_path'])}"

        return self._create_explanation_continued(explanation)

    def _create_explanation_continued(self, explanation):
        """Continuation of create_explanation — auto-extracted by self-evolution."""
        self.explanations_generated += 1
        self.reasoning_history.append(explanation)

        return explanation



class SemanticCollapseEngine:
    """Models how observation collapses meaning from superposition"""
    
    def __init__(self):
        self.co_occurrence_network = defaultdict(lambda: defaultdict(float))
        self.semantic_superposition = defaultdict(list)
        self.collapse_events = []

    def create_superposition(self, word: str, context_words: List[str]) -> Dict:
        """Create a semantic superposition state"""
        possible_meanings = self._get_possible_meanings(word)
        self.semantic_superposition[word] = possible_meanings
        
        # Update co-occurrence
        for ctx_word in context_words:
            self.co_occurrence_network[word][ctx_word] += 1.0
        
        return {
            'word': word,
            'possible_meanings': possible_meanings,
            'superposition_size': len(possible_meanings)
        }

    def observe_and_collapse(self, word: str, observation: str) -> Dict:
        """Collapse superposition through observation"""
        if word not in self.semantic_superposition:
            return {'collapsed_meaning': word, 'confidence': 0.5}
        
        meanings = self.semantic_superposition[word]
        # Select meaning based on observation context
        collapsed_meaning = random.choice(meanings) if meanings else word
        confidence = 1.0 / (len(meanings) + 1) if meanings else 0.5
        
        self.collapse_events.append({
            'word': word,
            'observation': observation,
            'collapsed_to': collapsed_meaning,
            'confidence': confidence,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        return {
            'collapsed_meaning': collapsed_meaning,
            'confidence': confidence,
            'superposition_size': len(meanings)
        }

    def _get_possible_meanings(self, word: str) -> List[str]:
        """Get possible meanings for a word"""
        meaning_map = {
            'consciousness': ['awareness', 'sentience', 'mind', 'self-awareness'],
            'quantum': ['discrete', 'probabilistic', 'superposed', 'entangled'],
            'reality': ['existence', 'truth', 'perception', 'manifestation'],
            'time': ['duration', 'sequence', 'dimension', 'flow'],
            'space': ['void', 'dimension', 'container', 'expanse'],
            'god': ['creator', 'infinite', 'consciousness', 'source'],
        }
        return meaning_map.get(word.lower(), [word])


class UnifiedCognitiveEngine:
    """
    Master orchestrator combining all three Quantum MCAGI systems:
    1. Current Emergent (Markov chains, TF-IDF)
    2. Manus.AI (11 cognitive engines)
    3. v34 (WolframAlpha, theology recall)
    """
    
    def __init__(self):
        print("[UNIFIED COGNITIVE ENGINE] Initializing all systems...")
        
        # Core engines from current Emergent
        self.algorithmic_core = get_algorithmic_core()
        self.domain_manager = get_domain_knowledge()
        
        # Manus.AI engines
        self.orch_or = OrchOREngine()
        self.bloom = BloomEngine()
        self.vader = VADEREngine()
        self.quote = QuoteEngine()
        self.personality = PersonalityEngine()
        self.explanation = ExplanationEngine()
        self.semantic_collapse = SemanticCollapseEngine()
        
        # v34 engines
        self.wolfram = WolframAlphaCloud()
        self.theology = TheologyEngine()
        
        # Tracking
        self.message_count = 0
        self.last_response = ""
        
        print("[UNIFIED COGNITIVE ENGINE] ✓ All 12 cognitive engines initialized")

    def process(self, user_input: str, context: Dict = None) -> Dict:
        """
        Process user input through all cognitive engines.
        Returns comprehensive response with explanation.
        """
        self.message_count += 1
        reasoning_data = {}

        # Step 1: Orch OR quantum state update
        self.orch_or.update_quantum_state(len(user_input) / 100.0)
        self.orch_or.calculate_coherence('language')
        self.orch_or.calculate_entropy('language')
        collapse_occurred = self.orch_or.objective_reduction()
        reasoning_data['orch_or'] = self.orch_or.get_status()

        # Step 2: Tone/sentiment detection
        tone = self.vader.analyze_sentiment(user_input)
        reasoning_data['tone'] = tone

        # Step 3: Domain detection
        domain_name, domain_score = self.domain_manager.detect_domain(user_input)
        reasoning_data['domain'] = domain_name

        # Step 4: Check for theology/special topics (v34)
        theology_response = self.theology.get_response(user_input)
        reasoning_data['theology'] = theology_response is not None
        if theology_response:
            reasoning_data['theology_topic'] = theology_response[1]
        
        # Step 5: Check for factual query (WolframAlpha)
        wolfram_result = None
        if self.wolfram.is_factual_query(user_input):
            wolfram_result = self.wolfram.query(user_input)
            reasoning_data['wolfram'] = wolfram_result
        
        # Step 6: Generate Bloom's question
        bloom_question = self.bloom.generate_for_growth_stage(
            topic=domain_name,
            growth_stage=self.personality.current_stage
        )
        reasoning_data['bloom'] = bloom_question

        self._process_continued(bloom_question, collapse_occurred, reasoning_data, theology_response, tone, wolfram_result, user_input)

    def _process_continued(self, bloom_question, collapse_occurred, reasoning_data, theology_response, tone, wolfram_result, user_input):
        """Continuation of process — auto-extracted by self-evolution."""
        # Step 7: Semantic collapse
        words = user_input.lower().split()
        if words:
            collapse_data = self.semantic_collapse.observe_and_collapse(
                words[0], ' '.join(words[1:3]) if len(words) > 1 else words[0]
            )
            reasoning_data['semantic_collapse'] = collapse_data

        # Step 8: Generate response (priority routing)
        response = self._generate_response(user_input, theology_response, wolfram_result, tone, bloom_question)

        # Step 9: Maybe add flavor (quotes, dreams)
        response = self.quote.maybe_add_flavor(response, user_input, probability=0.15)
        response = self.quote.maybe_add_dream_fragment(response, probability=0.08)

        # Step 10: Update personality and check for evolution
        evolution_msg = self.personality.update_interaction(
            topic=domain_name,
            is_question=bloom_question.get('level') in ['analyze', 'evaluate', 'create'],
            is_insight=collapse_occurred
        )
        if evolution_msg:
            response += f"\n\n{evolution_msg}"

        # Step 11: Generate explanation
        explanation = self.explanation.create_explanation(user_input, response, reasoning_data)

        # Step 12: Extract concepts for response
        concepts = self._extract_concepts(user_input)

        self.last_response = response

        return {
            'response': response,
            'questions': [bloom_question['question']] if bloom_question else [],
            'understanding': {
                'domain': domain_name,
                'tone': tone['register'],
                'depth': tone['depth'],
                'confidence': explanation['confidence_score']
            },
            'concepts': concepts,
            'explanation': explanation,
            'personality': self.personality.get_personality_summary(),
            'growth_stage': self.personality.get_current_stage(),
            'collapse_occurred': collapse_occurred
        }


    def _generate_response(self, user_input: str, theology_response, wolfram_result, tone, bloom_question) -> str:
        """Generate response using priority routing"""
        
        # Priority 1: Theology response
        if theology_response:
            return theology_response[0]
        
        # Priority 2: WolframAlpha factual response
        if wolfram_result:
            return f"🌌 COLLAPSE MOMENT! {wolfram_result}"
        
        # Priority 3: Use algorithmic core for general responses
        try:
            result = self.algorithmic_core.think(user_input)
            base_response = result.get('response', '')
            
            # Add follow-up based on Bloom's level
            if tone['register'] == 'philosophical':
                base_response += f"\n\n{bloom_question['question']}"
            elif self.orch_or.should_ask_question():
                follow_ups = [
                    "What aspects interest you most?",
                    "Want to go deeper?",
                    "How does that resonate with you?",
                    "What questions does this raise?"
                ]
                base_response += f" {random.choice(follow_ups)}"
            
            return base_response
        except Exception as e:
            # Fallback response
            return f"🌌 COLLAPSE MOMENT! Interesting perspective on {user_input[:50]}... What draws you to this topic?"

    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        try:
            result = self.algorithmic_core.think(text)
            return result.get('concepts', [])[:5]
        except Exception:
            # Simple extraction fallback
            stopwords = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for'}
            words = [w.lower().strip('.,!?') for w in text.split()]
            return [w for w in words if len(w) > 3 and w not in stopwords][:5]

    def get_status(self) -> Dict:
        """Get complete system status"""
        return {
            'system': 'Unified Cognitive Engine v1.0',
            'status': 'ACTIVE',
            'message_count': self.message_count,
            'engines': {
                'orch_or': self.orch_or.get_status(),
                'bloom': {'questions_generated': self.bloom.questions_generated},
                'vader': {'texts_analyzed': self.vader.texts_analyzed},
                'quote': {'categories': list(self.quote.quotes.keys())},
                'personality': self.personality.get_personality_summary(),
                'wolfram': {'queries_made': self.wolfram.queries_made},
                'explanation': {'explanations_generated': self.explanation.explanations_generated},
                'semantic_collapse': {'collapse_events': len(self.semantic_collapse.collapse_events)}
            },
            'growth_stage': self.personality.get_current_stage()
        }


def get_unified_cognitive_engine() -> UnifiedCognitiveEngine:
    """Get or create the unified cognitive engine singleton"""
    global _unified_engine
    if _unified_engine is None:
        _unified_engine = UnifiedCognitiveEngine()
    return _unified_engine

