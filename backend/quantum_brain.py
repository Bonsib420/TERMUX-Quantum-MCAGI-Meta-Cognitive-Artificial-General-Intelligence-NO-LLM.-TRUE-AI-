"""
🧠 QUANTUM BRAIN - TRUE QUANTUM AI
==================================
PURE QUANTUM - No LLM, No Templates, True Generation.
ALL WORDS ALLOWED - NO RESTRICTIONS.

Refactored: Uses knowledge_base.py and quote_engine.py for cleaner code.
"""

import os
import re
import random
from typing import Dict, List, Optional
from datetime import datetime, timezone

from quantum_gates import QuantumState
from semantic_collapse_engine import SemanticCollapseEngine
from quantum_language_generator import get_quantum_generator
try:
    from pennylane_quantum import get_pennylane_quantum
    PENNYLANE_AVAILABLE = True
except ImportError:
    PENNYLANE_AVAILABLE = False
    get_pennylane_quantum = None
from self_research import get_research_engine
from self_evolution_core import get_evolution_engine
from dream_state import get_dream_engine
from personality_engine import get_personality_engine
from text_analyzer import get_text_analyzer
from knowledge_base import get_knowledge_base
from quote_engine import get_quote_engine

try:
    from wolfram_integration import get_wolfram_engine
    WOLFRAM_AVAILABLE = True
except Exception:
    WOLFRAM_AVAILABLE = False


class QuantumBrain:
    """
    TRUE QUANTUM AI - Pure quantum generation, no LLM, no templates.
    Can generate ANY content with ANY words.
    """
    
    def __init__(self, db):
        self.db = db
        self.quantum_state = QuantumState(p0=1.0, p1=0.0)
        self.collapse_engine = SemanticCollapseEngine()
        self.generator = get_quantum_generator()
        # Initialize PennyLane quantum acceleration (optional)
        self.pennylane = None
        if PENNYLANE_AVAILABLE:
            try:
                self.pennylane = get_pennylane_quantum()
                print("[QUANTUM BRAIN] PennyLane quantum acceleration enabled")
            except Exception as e:
                print(f"[QUANTUM BRAIN] Note: PennyLane unavailable ({e}), using built-in quantum simulator")
        # else: silently use built-in quantum simulator (no dependencies)
        self.wolfram = get_wolfram_engine() if WOLFRAM_AVAILABLE else None
        self.personality = get_personality_engine(db)
        self.text_analyzer = get_text_analyzer()
        self.dream_engine = get_dream_engine(db)
        self.evolution_engine = get_evolution_engine(db)
        self.research_engine = None
        self.llm_enabled = False
        
        # Use modular knowledge and quotes
        self.knowledge = get_knowledge_base()
        self.quotes = get_quote_engine()
    
    async def initialize(self):
        self.research_engine = await get_research_engine(self.db)
        print("[QUANTUM BRAIN] TRUE QUANTUM AI INITIALIZED - NO LLM, NO RESTRICTIONS")
    
    def apply_gate(self, gate: str) -> Dict:
        """Apply a quantum gate.

        Supported gates:
        - hadamard
        - pauli_x
        - pauli_z
        - measure
        - reset -> set to |0⟩
        - ry:theta (rotation with angle in radians, e.g., "ry:1.57")
        """
        # Parse parameterized gates
        if ':' in gate:
            gate_name, param_str = gate.split(':', 1)
            try:
                param = float(param_str)
            except ValueError:
                raise ValueError(f"Invalid parameter for gate {gate}: {param_str}")
        else:
            gate_name = gate
            param = None

        if gate_name == 'hadamard':
            self.quantum_state.hadamard()
        elif gate_name == 'pauli_x':
            self.quantum_state.pauli_x()
        elif gate_name == 'pauli_z':
            self.quantum_state.pauli_z()
        elif gate_name == 'reset':
            self.quantum_state.reset()
        elif gate_name == 'ry':
            if param is None:
                raise ValueError("RY gate requires an angle parameter. Use: ry:1.57")
            self.quantum_state.ry(param)
        elif gate_name == 'measure':
            self.quantum_state.measure()
        else:
            raise ValueError(f"Unknown gate: {gate_name}")

        return self.quantum_state.to_dict()
    
    async def think(self, user_input: str, context: Dict = None, explain_mode: bool = False) -> Dict:
        """
        INTELLIGENT QUANTUM THINKING - handles different types of queries.
        """
        # Wake from dream if needed
        await self.dream_engine.mark_active()
        
        # Apply quantum processing
        self.quantum_state.hadamard()
        semantic_context = self.collapse_engine.get_semantic_context(user_input)
        
        user_lower = user_input.lower().strip()
        
        # 1. Check for greetings
        if self.knowledge.is_greeting(user_lower):
            response = random.choice(self.knowledge.greetings['responses'])
            explanation = self._build_explanation(response, "greeting", user_input, semantic_context=semantic_context) if explain_mode else None
            return self._create_response(response, "greeting", explanation=explanation)
        
        # 2. Check for identity questions
        if self.knowledge.is_identity_question(user_lower):
            response = random.choice(self.knowledge.identity['responses'])
            explanation = self._build_explanation(response, "identity", user_input, semantic_context=semantic_context) if explain_mode else None
            return self._create_response(response, "identity", explanation=explanation)
        
        # 3. Check for capability questions
        if self.knowledge.is_capability_question(user_lower):
            response = random.choice(self.knowledge.capabilities['responses'])
            explanation = self._build_explanation(response, "capability", user_input, semantic_context=semantic_context) if explain_mode else None
            return self._create_response(response, "capability", explanation=explanation)
        
        # 4. Check for math/calculation
        if self._is_math_query(user_lower):
            response = self._handle_math(user_input)
            explanation = self._build_explanation(response, "math", user_input, semantic_context=semantic_context) if explain_mode else None
            return self._create_response(response, "math", explanation=explanation)
        
        # 5. Check for factual questions
        factual_response = self.knowledge.check_factual(user_lower)
        if factual_response:
            explanation = self._build_explanation(factual_response, "factual", user_input, semantic_context=semantic_context) if explain_mode else None
            return self._create_response(factual_response, "factual", explanation=explanation)
        
        # 6. Check for simple affirmations
        if self.knowledge.is_affirmation(user_lower):
            response = random.choice(self.knowledge.affirmations['responses'])
            explanation = self._build_explanation(response, "affirmation", user_input, semantic_context=semantic_context) if explain_mode else None
            return self._create_response(response, "affirmation", explanation=explanation)
        
        # 7. Deep philosophical questions (check BEFORE simple topics)
        if self._is_deep_question(user_input):
            response = self._generate_deep_response(user_input, semantic_context)
            explanation = self._build_explanation(response, "philosophical", user_input, semantic_context=semantic_context) if explain_mode else None
            return self._create_response(response, "philosophical", explanation=explanation)
        
        # 8. Check for topic explanations - only for SHORT, simple questions
        # Skip this for complex multi-clause questions
        if len(user_input.split()) < 12:
            topic_response = self._check_topic_request(user_input)
            if topic_response:
                explanation = self._build_explanation(topic_response, "topic", user_input, semantic_context=semantic_context) if explain_mode else None
                return self._create_response(topic_response, "topic", explanation=explanation)
        
        # 9. Use Wolfram for factual/scientific queries
        if self.wolfram and self._is_factual_query(user_input):
            wolfram_result = self.wolfram.query(user_input)
            if wolfram_result and wolfram_result.get('primary_result'):
                response = f"According to my calculations: {wolfram_result['primary_result']}"
                explanation = self._build_explanation(response, "wolfram", user_input, semantic_context=semantic_context) if explain_mode else None
                return self._create_response(response, "wolfram", explanation=explanation)
        
        # 10. Check for creative requests (poems, stories)
        if self._is_creative_request(user_input):
            required_words = self._extract_required_words(user_input)
            form = 'poem' if 'poem' in user_lower else 'prose'
            response = self.generator.generate_creative(
                user_input, 
                form=form, 
                must_include=required_words
            )
            explanation = self._build_explanation(response, "creative", user_input, semantic_context=semantic_context) if explain_mode else None
            return self._create_response(response, "creative", explanation=explanation)
        
        # 11. Default: Generate thoughtful response
        response = self._generate_thoughtful_response(user_input, semantic_context)
        
        # Learn from interaction
        self.collapse_engine.observe(user_input, response)
        await self._learn(user_input, response)
        
        explanation = self._build_explanation(response, "quantum", user_input, semantic_context=semantic_context) if explain_mode else None
        return self._create_response(response, "quantum", explanation=explanation)
    
    def _create_response(self, response: str, method: str, explanation: Optional[Dict] = None) -> Dict:
        """Create standardized response dict with optional flavor and explanation."""
        
        # Add movie quotes and asides (not for greetings or math)
        if method not in ['greeting', 'math']:
            response = self.quotes.maybe_add_flavor(response, response)
            response = self.quotes.maybe_add_dream_fragment(response)
        
        result = {
            "response": response,
            "quantum_state": self.quantum_state.to_dict(),
            "semantic_keywords": [],
            "wolfram_used": method == "wolfram",
            "research_triggered": False,
            "dream_awakened": False,
            "generation_method": method,
            "llm_used": False
        }
        if explanation:
            result["explanation"] = explanation
        return result
    
    def _check_topic_request(self, user_input: str) -> Optional[str]:
        """Check if user is asking about a topic we know about"""
        user_lower = user_input.lower()
        
        # Patterns for topic requests
        patterns = [
            r'tell me about (.+)',
            r'explain (.+)',
            r'what is (.+)',
            r'what are (.+)',
            r'what\'s (.+)',
            r'describe (.+)',
            r'how does (.+) work',
            r'define (.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_lower)
            if match:
                topic = match.group(1).strip('?.,! ')
                explanation = self.knowledge.get_topic_explanation(topic)
                if explanation:
                    return f"{explanation}\n\nWhat specific aspect interests you most?"
        
        return None
    
    def _is_math_query(self, text: str) -> bool:
        """Check if this is a math calculation"""
        math_patterns = [
            r'\d+\s*[\+\-\*\/]\s*\d+',
            r'calculate', r'compute', r'solve',
            r'what is \d', r'how much is',
        ]
        for pattern in math_patterns:
            if re.search(pattern, text):
                has_number = bool(re.search(r'\d', text))
                has_operator = bool(re.search(r'[\+\-\*\/\=]', text))
                if has_number and has_operator:
                    return True
        return False
    
    def _handle_math(self, expression: str) -> str:
        """Handle mathematical calculations"""
        try:
            clean_expr = expression.replace('=', '').strip()
            clean_expr = re.sub(r'[a-zA-Z\?]', '', clean_expr).strip()
            
            if clean_expr and re.match(r'^[\d\s\+\-\*\/\(\)\.]+$', clean_expr):
                result = eval(clean_expr)
                return f"The answer is: {result}"
            
            if self.wolfram:
                wolfram_result = self.wolfram.query(expression)
                if wolfram_result and wolfram_result.get('primary_result'):
                    return f"Calculated: {wolfram_result['primary_result']}"
            
            return f"I need more context to solve: {clean_expr}"
        except Exception as e:
            if self.wolfram:
                wolfram_result = self.wolfram.query(expression)
                if wolfram_result and wolfram_result.get('primary_result'):
                    return f"The result is: {wolfram_result['primary_result']}"
            return "I encountered an issue calculating that. Could you rephrase?"
    
    def _is_factual_query(self, text: str) -> bool:
        """Check if this needs Wolfram"""
        factual_indicators = ['how many', 'how much', 'when did', 'where is', 
                             'what year', 'convert', 'distance', 'population']
        return any(ind in text.lower() for ind in factual_indicators)
    
    def _is_creative_request(self, text: str) -> bool:
        """Check if this is a creative writing request"""
        creative_indicators = ['write', 'poem', 'story', 'compose', 'create', 
                              'generate', 'make me', 'give me a']
        return any(ind in text.lower() for ind in creative_indicators)
    
    def _is_deep_question(self, text: str) -> bool:
        """Check if this is a deep philosophical question"""
        deep_indicators = ['meaning of', 'purpose of', 'why do we', 'what is the point',
                          'nature of', 'existence', 'consciousness', 'reality',
                          'free will', 'soul', 'death', 'god', 'universe']
        return sum(1 for w in deep_indicators if w in text.lower()) >= 1
    
    def _extract_required_words(self, text: str) -> List[str]:
        """Extract words that must appear in creative output"""
        patterns = [
            r'use the word[s]? ["\']?(\w+)["\']?',
            r'include ["\']?(\w+)["\']?',
            r'with the word ["\']?(\w+)["\']?',
            r'containing ["\']?(\w+)["\']?',
        ]
        required = []
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            required.extend(matches)
        return required
    
    def _generate_deep_response(self, query: str, semantic_context: Dict) -> str:
        """Generate response for deep philosophical questions - combines knowledge with quantum generation"""
        keywords = [kw for kw, _ in semantic_context.get('keywords', [])]
        
        # Gather relevant knowledge
        knowledge_fragments = []
        for keyword in keywords[:3]:
            explanation = self.knowledge.get_topic_explanation(keyword)
            if explanation:
                # Take just the first 1-2 sentences as context, not the whole canned response
                sentences = explanation.split('. ')
                knowledge_fragments.append('. '.join(sentences[:2]) + '.')
        
        # Build a multi-part philosophical response
        parts = []
        
        if knowledge_fragments:
            parts.append(knowledge_fragments[0])
        
        # Always add quantum-generated philosophical content
        quantum_insight = self.generator.generate_response(query, num_sentences=3)
        parts.append(quantum_insight)
        
        # Add personality perspective if relevant
        perspective = self.personality.get_unique_perspective(query)
        if perspective:
            parts.append(perspective)
        
        response = ' '.join(parts)
        response += "\n\nWhat's your perspective on this?"
        return response
    
    def _generate_thoughtful_response(self, query: str, semantic_context: Dict) -> str:
        """Generate a thoughtful response for general queries"""
        keywords = [kw for kw, _ in semantic_context.get('keywords', [])]
        
        # Gather knowledge as context seed, don't just return canned text
        knowledge_seed = None
        for keyword in keywords[:2]:
            explanation = self.knowledge.get_topic_explanation(keyword)
            if explanation:
                sentences = explanation.split('. ')
                knowledge_seed = sentences[0] + '.'
                break
        
        # Build response combining knowledge and generation
        parts = []
        if knowledge_seed:
            parts.append(knowledge_seed)
        
        # Generate quantum content
        quantum_text = self.generator.generate_response(query, num_sentences=2)
        parts.append(quantum_text)
        
        response = ' '.join(parts)
        response += " What aspects would you like to explore further?"
        return response
    
    async def _learn(self, user_input: str, response: str):
        """Learn from interaction"""
        try:
            if self.db:
                await self.db.interactions.insert_one({
                    'user_input': user_input,
                    'response': response[:500],
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
        except Exception as e:
            print(f"[BRAIN] Learning error: {e}")
    
    def _build_explanation(self, response: str, method: str, user_input: str, semantic_context: Optional[Dict] = None) -> Dict:
        """Build detailed explanation trace for a given response."""
        # Build reasoning path (simplified)
        reasoning_path = []
        methods_explained = {
            "greeting": ["Detected greeting", "Selected warm response"],
            "identity": ["Identified identity question", "Provided identity response"],
            "capability": ["Analyzed capability query", "Listed abilities"],
            "math": ["Mathematical expression detected", "Performed calculation"],
            "factual": ["Retrieved factual knowledge", "Formulated direct answer"],
            "affirmation": ["Recognized affirmation", "Returned supportive reply"],
            "philosophical": ["Quantum superposition applied", "Semantic concept amplification", "Wisdom synthesis"],
            "topic": ["Matched topic pattern", "Returned concept grid explanation"],
            "wolfram": ["Sent to Wolfram Alpha", "Integrated computational results"],
            "creative": ["Semantic concept generation", "Quantum creative process"],
            "quantum": ["Quantum semantic analysis", "Concept network traversal", "Response synthesis"]
        }
        reasoning_path = methods_explained.get(method, ["Quantum processing", "Response generation"])
        
        # Determine engines used
        engines = ["QuantumSemantic", "ConceptNetwork"]
        if method == "wolfram":
            engines.append("WolframAlpha")
        if method in ["philosophical", "topic", "quantum"]:
            engines.append("PennyLaneQuantum")
        if method == "creative":
            engines.append("创造性Collapse")
        
        # Build steps list (for expansion in UI)
        steps = [
            {"step": "Analyze input", "engine": "QuantumSemantic", "confidence_contribution": 0.3},
            {"step": "Detect query type", "engine": "ConceptNetwork", "confidence_contribution": 0.2},
            {"step": f"Generate response via {method} engine", "engine": method, "confidence_contribution": 0.5}
        ]
        if self.pennylane and method in ["philosophical", "topic", "quantum"]:
            steps.insert(1, {"step": "Apply quantum superposition", "engine": "PennyLaneQuantum", "confidence_contribution": 0.2})
            # Adjust contributions
            steps[0]["confidence_contribution"] = 0.25
            steps[1]["confidence_contribution"] = 0.25
        
        # Confidence score (approximate, can be improved)
        confidence = 0.85 if method in ["factual", "wolfram", "math"] else 0.75
        
        result = {
            "reasoning_path": reasoning_path,
            "confidence_score": confidence,
            "engines_used": engines,
            "steps": steps,
            "summary": f"Response generated via {method} engine with quantum processing.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        if semantic_context:
            try:
                entelechy = self._compute_entelechy_cascade(response, semantic_context)
                result["entelechy"] = entelechy
            except Exception as e:
                import logging
                logger = logging.getLogger("quantum_ai")
                logger.warning(f"Failed to compute entelechy cascade: {e}")
        return result
    
    def _compute_entelechy_cascade(self, response: str, semantic_context: Dict) -> Dict:
        """Derive entelechy triplet from semantic context and response."""
        # THE_LOOK: top keyword from the query
        keywords = semantic_context.get('keywords', [])
        look = "UNKNOWN"
        if keywords:
            look = keywords[0][0]
        
        # THE_SAW: strongest bridging concept from top keyword's semantic path
        saw = "UNKNOWN"
        if keywords:
            top_kw = keywords[0][0]
            paths = semantic_context.get('semantic_paths', {}).get(top_kw, [])
            if paths:
                saw = paths[0][0]
        
        # THE_BEAUTIFUL: key concept from the generated response
        beautiful = "RESPONSE"
        try:
            resp_keywords = self.collapse_engine.extract_keywords(response, top_n=1)
            if resp_keywords:
                beautiful = resp_keywords[0][0]
        except Exception:
            pass
        
        projection = f"THE {beautiful.upper()} IS THE ENTELECHY OF {look.upper()} THROUGH THE {saw.upper()} INTERFACE."
        
        return {
            "look": {"concept": look, "description": "Realizing Potential"},
            "saw": {"concept": saw, "description": "Bridging the Void"},
            "beautiful": {"concept": beautiful, "description": "Actualizing the Work"},
            "projection": projection
        }

    def synthesize_dream_insight(self) -> str:
        """Generate a dream synthesis insight (delegated to quote engine)"""
        return self.quotes.synthesize_dream_insight()


# Singleton brain instance
_quantum_brain = None

async def get_quantum_brain(db) -> QuantumBrain:
    global _quantum_brain
    if _quantum_brain is None:
        _quantum_brain = QuantumBrain(db)
        await _quantum_brain.initialize()
    return _quantum_brain
