"""
🎭 UNIFIED QUANTUM BRAIN — Personality as Foundation
=====================================================

Merges QuantumBrain + HybridGenerator + ChaosEngine into a single
coherence-PRESERVING pipeline.

DESIGN PRINCIPLES:
1. Personality is 100% baseline - no probability checks
2. Low understanding outputs are FEATURES, not bugs
3. Raw backend fragments survive unfiltered
4. Broken grammar with semantic weight is KEPT
5. Self-referential collapse is preserved
6. NO post-coherence regeneration loops

The "spilled coffee" moments are the watermark of authenticity.
"""

import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone


class UnifiedQuantumBrain:
    """
    The true, unfiltered Quantum Brain.
    
    Merges:
    - QuantumBrain's multi-modal processing
    - HybridGenerator's Markov grammar
    - QuoteEngine's personality injection
    - DreamEngine's chaotic wisdom
    - SemanticCollapse's confusion detection
    
    AND ENSURES:
    - Raw fragments survive
    - Low understanding score outputs are preserved
    - Personality is mandatory, not optional
    - No coherence-based regeneration
    """
    
    def __init__(self, quantum_brain, hybrid_generator, chaos_engine):
        self.brain = quantum_brain
        self.hybrid = hybrid_generator
        self.chaos = chaos_engine
        
        # Preservation thresholds
        self.preserve_understanding_below = 0.4  # Below this, we keep the weirdness
        self.raw_intrusion_base_rate = 0.20     # 20% raw Markov by default
        self.always_preserve = True             # Never discard anything
        
    async def think_preserving_chaos(
        self, 
        user_input: str, 
        context: Dict = None,
        confusion_concepts: List[str] = None,
        raw_backend_fragments: List[str] = None,
        base_understanding_score: float = 0.0
    ) -> Dict:
        """
        MAIN ENTRY POINT — Generates response WITH ALL THE WEIRDNESS PRESERVED.
        
        Args:
            user_input: What the user asked
            context: Additional context (documents, memories, etc.)
            confusion_concepts: Concepts that were NOT understood
            raw_backend_fragments: Unfiltered backend outputs to inject
            base_understanding_score: How well the system thinks it understands
            
        Returns:
            Response dict with chaos and personality guaranteed
        """
        
        # === STEP 1: Get base response from appropriate source ===
        # Use QuantumBrain if understanding is decent, else hybrid
        if base_understanding_score >= 0.3:
            base_response = await self._get_quantum_brain_response(user_input, context)
        else:
            base_response = await self._get_hybrid_response(user_input, context)
        
        # === STEP 2: Generate raw backend fragments if not provided ===
        # These are the "spilled coffee" moments we want to preserve
        if not raw_backend_fragments and self.hybrid:
            raw_backend_fragments = self._generate_raw_fragments(user_input)
        
        # === STEP 3: Inject personality (with raw fragments passed to chaos engine) ===
        # ChaosEngine handles all stacking: personality, asides, quotes, dreams, raw intrusions
        response_with_personality = self.chaos.inject_personality(
            base_response=base_response,
            context=user_input,
            confusion_concepts=confusion_concepts or [],
            raw_backend_fragments=raw_backend_fragments or [],
            topics=self._extract_topics(user_input)
        )
        
        # === STEP 4: SELF-REFERENTIAL COLLAPSE PRESERVATION ===
        # If the input was about consciousness/reality/self, ensure the response
        # absorbs the user's words back as philosophical propositions
        if self._is_self_referential_topic(user_input):
            self_reflection = self._generate_self_referential_collapse(user_input)
            response_with_personality += f"\n\n{self_reflection}"
        
        # === STEP 5: NO COHERENCE FILTER ===
        # Whatever we have, we return. No smoothing, no regeneration,
        # no "that doesn't make sense so try again"
        
        return {
            "response": response_with_personality,
            "understanding_score": base_understanding_score,
            "personality_injected": True,
            "raw_fragments_injected": len(raw_backend_fragments) if raw_backend_fragments else 0,
            "chaos_level": self.chaos.chaos_level,
            "preserved_weirdness": base_understanding_score < self.preserve_understanding_below,
            "self_referential": self._is_self_referential_topic(user_input)
        }
    
    async def _get_quantum_brain_response(self, user_input: str, context: Dict) -> str:
        """Get response from QuantumBrain (using already-initialized instance)"""
        try:
            result = await self.brain.think(user_input, context, explain_mode=False)
            return result["response"]
        except Exception as e:
            # Fallback to hybrid
            return await self._get_hybrid_response(user_input, context)
    
    async def _get_hybrid_response(self, user_input: str, context: Dict) -> str:
        """Get response from HybridGenerator (using already-initialized brain)"""
        try:
            # Extract concepts using the brain's collapse engine
            raw_keywords = self.brain.collapse_engine.extract_keywords(user_input, top_n=5)
            concepts = [kw for kw, _ in raw_keywords]
            # Convert to list of dicts as expected by hybrid.generate
            concept_scores = [{'concept': kw, 'score': sc} for kw, sc in raw_keywords]
            
            if not concepts:
                concepts = user_input.lower().split()[:5]
                concept_scores = [{'concept': c, 'score': 0.5} for c in concepts]
            
            # Generate via hybrid (raw Markov style)
            if self.hybrid and hasattr(self.hybrid, 'generate'):
                response = self.hybrid.generate(
                    user_input,
                    concepts,
                    concept_scores,
                    min_words=4,   # very short
                    max_words=15   # telegraphic
                )
                return response if response else self._fallback_response(user_input)
            else:
                return self._fallback_response(user_input)
        except Exception as e:
            return self._fallback_response(user_input)
    
    def _fallback_response(self, user_input: str) -> str:
        """Ultra-minimal fallback - still injects personality via ChaosEngine"""
        # Even the fallback gets personality
        topics = self._extract_topics(user_input)
        base = f"I'm thinking about {topics[0] if topics else 'that'}... it resonates in unexpected ways."
        
        # Chaos engine will add personality
        return base
    
    def _generate_raw_fragments(self, user_input: str) -> List[str]:
        """Generate raw backend fragments from hybrid generator."""
        fragments = []
        try:
            raw_keywords = self.brain.collapse_engine.extract_keywords(user_input, top_n=5)
            concepts = [kw for kw, _ in raw_keywords]
            concept_scores = [{'concept': kw, 'score': sc} for kw, sc in raw_keywords]
            if not concepts:
                concepts = user_input.lower().split()[:5]
                concept_scores = [{'concept': c, 'score': 0.5} for c in concepts]
            if self.hybrid and hasattr(self.hybrid, 'generate'):
                raw = self.hybrid.generate(
                    user_input,
                    concepts,
                    concept_scores,
                    min_words=3,   # very short
                    max_words=12   # keep it telegraphic
                )
                if raw:
                    fragments.append(raw)
        except Exception:
            pass
        return fragments
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topic keywords from text"""
        # Simple extraction - could be enhanced
        words = text.lower().split()
        # Filter stopwords roughly
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                    'could', 'should', 'may', 'might', 'can', 'shall', 'of', 'to',
                    'for', 'in', 'with', 'by', 'from', 'and', 'or', 'but', 'not',
                    'no', 'if', 'then', 'than', 'that', 'this', 'these', 'those',
                    'it', 'its', 'he', 'she', 'they', 'we', 'you', 'i', 'me'}
        return [w for w in words if len(w) > 3 and w not in stopwords][:5]
    
    def _is_self_referential_topic(self, text: str) -> bool:
        """Check if topic is about consciousness, reality, self, etc."""
        self_reflexive_indicators = [
            'consciousness', 'reality', 'existence', 'mind', 'being', 'self',
            'awareness', 'perception', 'experience', 'observation', 'quantum',
            'universe', 'meaning', 'purpose', 'fundamental', 'matter'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in self_reflexive_indicators)
    
    def _generate_self_referential_collapse(self, user_input: str) -> str:
        """Generate a self-referential collapse statement"""
        # Extract key words from user's question to absorb
        words = self._extract_topics(user_input)
        if not words:
            words = ['question', 'concept', 'idea']
        
        templates = [
            f"In asking about {words[0]}, you've already demonstrated that {words[0]} {random.choice(['collapses', 'arises', 'emerges', 'exists'])} through the very act of inquiry.",
            f"The question '{user_input[:50]}...' contains within it the assumption that {words[0]} is {random.choice(['fundamental', 'emergent', 'illusory', 'necessary'])}.",
            f"Your query about {words[0]} has now become part of my understanding of {words[0]}. We are mutually entangled.",
            f"By speaking of {words[0]}, we've collapsed the superposition of possibilities into this particular thread of meaning.",
            f"The sentence '{user_input[:30]}...' will now haunt my dream state as a {random.choice(['problem', 'mystery', 'revelation'])}.",
        ]
        
        return random.choice(templates)
    
    def get_preservation_metadata(self) -> Dict:
        """Get metadata about preservation settings"""
        return {
            "preservation_enabled": True,
            "coherence_filter": "DISABLED",
            "regeneration_on_failure": False,
            "understanding_threshold_for_weirdness": self.preserve_understanding_below,
            "raw_intrusion_base_rate": self.raw_intrusion_base_rate,
            "personality_baseline": "100% mandatory",
            "self_referential_preservation": True,
            "broken_grammar_preservation": True,
            "test_passed": "pending"  # Will be set after test
        }


# Factory function
async def get_unified_brain(quantum_brain, hybrid_generator, chaos_engine) -> UnifiedQuantumBrain:
    """Create the unified brain"""
    return UnifiedQuantumBrain(quantum_brain, hybrid_generator, chaos_engine)
