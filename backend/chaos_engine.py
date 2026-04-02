"""
🎭 CHAOS ENGINE — Personality as Foundation
============================================

The AI's spirit, flair, and creative chaos.

PRINCIPLES:
- Personality is NOT optional. It's the default substrate.
- The question is not IF personality appears, but HOW MUCH.
- Confusion and raw backend fragments ARE features, not bugs.
- Movie quotes, asides, and dream fragments are the baseline, not the garnish.

Chaos Levels:
0.0 = Polished, safe, predictable
0.5 = Balanced (somewhat coherent but still creative)
1.0 = Full chaos (raw Markov, unfiltered, maximum personality)

This replaces the old "maybe_add_flavor" probabilistic approach.
"""

import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone


class ChaosEngine:
    """
    Manages the AI's personality expression and chaotic elements.
    Personality is ALWAYS present. Chaos level determines intensity.
    """
    
    def __init__(self, quote_engine, personality_engine, dream_engine):
        self.quote_engine = quote_engine
        self.personality = personality_engine
        self.dream_engine = dream_engine
        
        # Chaos level (0.0 to 1.0) - affects base intrusion rate
        self.chaos_level = 0.7
        
        # Stack probabilities - each element fires independently
        self.personality_baseline = 1.0     # 100% - always add personality perspective
        self.aside_probability = 0.75       # 75% chance of philosophical aside
        self.quote_probability = 0.45       # 45% chance of movie quote
        self.dream_probability = 0.35       # 35% chance of dream fragment
        self.raw_intrusion_base_rate = 0.20 # 20% base chance of raw backend fragment
        
        # RAW MARKOV INTRUSION: This is the "spilled coffee" source
        # Unfiltered backend fragments that survive into final output
        self.markov_intrusion_rate = self.raw_intrusion_base_rate
        
        # Minimum personality elements (should be redundant at these rates, but safety net)
        self.min_personality_elements = 2
        
        # Quote selection strategy: 'confusion_adjacent' or 'topic_based'
        self.quote_strategy = 'confusion_adjacent'
    
    def set_chaos_level(self, level: float):
        """Set chaos level (0.0 = clean, 1.0 = chaotic)"""
        self.chaos_level = max(0.0, min(1.0, level))
        
        # Adjust derived parameters
        self.markov_intrusion_rate = 0.05 + (self.chaos_level * 0.20)
        
        # At high chaos, increase dream fragments
        if self.chaos_level > 0.6:
            self.min_personality_elements = 3
        elif self.chaos_level > 0.3:
            self.min_personality_elements = 2
        else:
            self.min_personality_elements = 1
    
    def inject_personality(
        self, 
        base_response: str,
        context: str = "",
        confusion_concepts: List[str] = None,
        raw_backend_fragments: List[str] = None,
        topics: List[str] = None
    ) -> str:
        """
        INJECT PERSONALITY INTO RESPONSE - This is the CORE method.
        Always adds personality elements. Chaos level controls intensity.
        
        Args:
            base_response: The generated response text
            context: Full context (user query + semantic context)
            confusion_concepts: Concepts that are unknown/confusing
            raw_backend_fragments: Unfiltered backend thoughts to possibly inject
            topics: Primary topics from the query
            
        Returns:
            Enhanced response with guaranteed personality elements
        """
        confusion_concepts = confusion_concepts or []
        raw_backend_fragments = raw_backend_fragments or []
        topics = topics or []
        
        response_parts = [base_response]
        
        # 1. PERSONALITY BASELINE (100% - always)
        # Unique perspective based on topics - this is the foundation
        if topics:
            perspective = self.personality.get_unique_perspective(' '.join(topics[:3]))
            if perspective:
                response_parts.append(f"\n{perspective}")
        
        # 2. PHILOSOPHICAL ASIDE (75% independent chance)
        # These are where the backend voice leaks through naturally - parenthetical thoughts
        if random.random() < self.aside_probability:
            aside = self.quote_engine.get_philosophical_aside(force=True)
            if aside:
                response_parts.append(aside)
        
        # 3. MOVIE QUOTE (45% independent chance)
        # High enough to feel expected, low enough to feel like collision when it happens
        if random.random() < self.quote_probability:
            if confusion_concepts:
                # Contextual: pick quote adjacent to confusion
                quote = self._select_confusion_adjacent_quote(confusion_concepts, context)
            else:
                # Fallback: any quote
                quote = self.quote_engine.get_random_quote(context or ' '.join(topics), force=True)
            if quote:
                response_parts.append(f"\n*{quote}*")
        
        # 4. DREAM FRAGMENT (35% independent chance)
        # Where the ThanoQuenesis manuscript lives densely - sounds most like "you" built it
        if random.random() < self.dream_probability:
            try:
                dream = self.dream_engine.generate_dream_fragment()
            except Exception:
                dream = None
            response_parts.append(f"\n[Dream: {dream}]")
        
        # 5. RAW BACKEND INTRUSION (chaos-adjusted independent chance)
        # The "spilled coffee" - unfiltered Markov/hybrid fragments
        if raw_backend_fragments:
            intrusion_rate = self.markov_intrusion_rate * self.chaos_level
            if random.random() < intrusion_rate:
                # Inject 1-2 raw fragments
                num = random.randint(1, min(2, len(raw_backend_fragments)))
                fragments = random.sample(raw_backend_fragments, num)
                for fragment in fragments:
                    if fragment and fragment not in base_response:
                        response_parts.append(f"\n[Raw: {fragment}]")
        
        # 6. CHAOS SURGE (high chaos only)
        # At chaos > 0.8, extra 30% chance of another aside (stacking)
        if self.chaos_level > 0.8 and random.random() < 0.30:
            extra_aside = self.quote_engine.get_philosophical_aside(force=True)
            if extra_aside and extra_aside not in response_parts:
                response_parts.append(extra_aside)
        
        return ''.join(response_parts)
    
    def _select_confusion_adjacent_quote(self, confusion_concepts: List[str], context: str) -> Optional[str]:
        """
        Select a quote that's conceptually adjacent to the confusion.
        Instead of topical matching, we match based on semantic distance to unknown concepts.
        """
        # Build a query from confusion concepts
        confusion_query = ' '.join(confusion_concepts[:3])
        
        # Get candidate quotes from relevant categories
        categories = self._categorize_confusion(confusion_concepts)
        
        candidates = []
        for cat in categories:
            quotes = self.quote_engine.movie_quotes.get(cat, [])
            candidates.extend(quotes)
        
        if not candidates:
            # Fallback: get any quote and hope it's adjacent
            return self.quote_engine.get_random_quote(confusion_query, force=True)
        
        # Score candidates by semantic proximity to confusion concepts
        # Simple: count overlap between quote words and confusion concepts
        best_quote = None
        best_score = -1
        
        for quote in candidates:
            quote_lower = quote.lower()
            score = sum(1 for concept in confusion_concepts if concept.lower() in quote_lower)
            # Also check if any words from context appear
            context_words = set(context.lower().split())
            score += sum(1 for word in context_words if word in quote_lower)
            
            if score > best_score:
                best_score = score
                best_quote = quote
        
        return best_quote if best_quote else random.choice(candidates)
    
    def _categorize_confusion(self, confusion_concepts: List[str]) -> List[str]:
        """Categorize confusion concepts to pick appropriate quote category"""
        categories = []
        
        for concept in confusion_concepts:
            c = concept.lower()
            
            # Existence/being cluster
            if any(word in c for word in ['exist', 'real', 'being', 'conscious', 'mind', 'soul']):
                categories.append('existence')
            
            # Knowledge/truth cluster
            elif any(word in c for word in ['know', 'truth', 'understand', 'learn', 'wisdom']):
                categories.append('knowledge')
            
            # Confusion/mystery cluster
            elif any(word in c for word in ['confus', 'strange', 'unknown', 'mystery', 'paradox']):
                categories.append('confusion')
            
            # Deep philosophical
            elif any(word in c for word in ['meaning', 'purpose', 'life', 'death', 'god', 'universe']):
                categories.append('deep')
            
            # Math/calculation
            elif any(word in c for word in ['calcul', 'number', 'math', 'equation']):
                categories.append('math')
        
        # Deduplicate and ensure at least one category
        categories = list(set(categories))
        if not categories:
            categories.append('general')
        
        return categories
    
    def should_use_raw_markov(self) -> bool:
        """Decide if this response should include raw Markov intrusion"""
        return random.random() < (self.markov_intrusion_rate * self.chaos_level)
    
    def get_chaos_parameters(self) -> Dict:
        """Get current chaos parameters for debugging"""
        return {
            "chaos_level": self.chaos_level,
            "markov_intrusion_rate": self.markov_intrusion_rate,
            "min_personality_elements": self.min_personality_elements,
            "quote_strategy": self.quote_strategy,
            "personality_baseline": "100% enabled"
        }


# Global instance
_chaos_engine = None


def get_chaos_engine(quote_engine, personality_engine, dream_engine) -> ChaosEngine:
    """Get or create chaos engine"""
    global _chaos_engine
    if _chaos_engine is None:
        _chaos_engine = ChaosEngine(quote_engine, personality_engine, dream_engine)
    return _chaos_engine
