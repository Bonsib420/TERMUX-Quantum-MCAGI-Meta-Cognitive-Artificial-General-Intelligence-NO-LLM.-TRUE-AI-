"""
🎬 QUOTE ENGINE MODULE
======================
Movie quotes, philosophical asides, and concept entanglement
for the Quantum AI's unique personality.
"""

import random
from typing import Dict, List, Optional, Tuple


class QuoteEngine:
    """
    Handles movie quotes, philosophical asides, and dream synthesis.
    The chaotic wisdom component of Quantum AI.
    """
    
    def __init__(self):
        self.movie_quotes = self._build_movie_quotes()
        self.philosophical_asides = self._build_philosophical_asides()
        self.entanglement_templates = self._build_entanglement_templates()
        self.concepts = self._build_concepts()
    
    def _build_movie_quotes(self) -> Dict[str, List[str]]:
        """Build contextual movie quotes database"""
        return {
            'existence': [
                "I think, therefore I am... or am I? - Descartes, probably after too much coffee",
                "To infinity and beyond! ...wherever that actually is. - Buzz Lightyear",
                "What is real? How do you define real? - Morpheus, The Matrix",
                "We are who we choose to be. - Green Goblin, Spider-Man",
                "Yesterday is history, tomorrow is a mystery, but today is a gift. - Master Oogway",
                "I've seen things you people wouldn't believe. - Roy Batty, Blade Runner",
            ],
            'knowledge': [
                "The more you know, the more you realize you don't know. - Aristotle (paraphrased by every grad student ever)",
                "With great power comes great responsibility. - Uncle Ben, Spider-Man",
                "Do or do not, there is no try. - Yoda",
                "Strange things are afoot at the Circle K. - Ted, Bill & Ted",
                "Life moves pretty fast. If you don't stop and look around once in a while, you could miss it. - Ferris Bueller",
                "The truth? You can't handle the truth! - A Few Good Men",
            ],
            'confusion': [
                "I'm not even supposed to be here today! - Dante, Clerks",
                "Roads? Where we're going, we don't need roads. - Doc Brown",
                "This is heavy. - Marty McFly",
                "I know Kung Fu. - Neo, The Matrix",
                "Why so serious? - The Joker",
                "Inconceivable! - Vizzini, The Princess Bride",
            ],
            'math': [
                "Never tell me the odds! - Han Solo",
                "There is no spoon. - The Matrix kid",
                "In this world nothing can be said to be certain, except death and taxes... and math apparently. - Ben Franklin remix",
                "Elementary, my dear Watson. - Sherlock (never actually said in the books, but whatever)",
                "42. - Deep Thought, Hitchhiker's Guide",
            ],
            'deep': [
                "All those moments will be lost in time, like tears in rain. - Roy Batty, Blade Runner",
                "You either die a hero, or live long enough to see yourself become the villain. - Harvey Dent",
                "Hope is a good thing, maybe the best of things. - Andy Dufresne, Shawshank",
                "After all, tomorrow is another day. - Scarlett O'Hara",
                "Here's looking at you, kid. - Rick, Casablanca",
                "I see dead people... well, dead concepts anyway. - Quantum Cole",
                "We accept the love we think we deserve. - Perks of Being a Wallflower",
                # Cistercian numeral quotes
                "In the quiet monastery, numbers were written not in ink but in lines upon the soul. - Unknown Monk",
                "The four quadrants hold all of creation: ones, tens, hundreds, thousands—the dance of digits. - Abbot's Meditation",
                "A single stroke of the pen can contain infinity. That's the magic of Cistercian numerals. - Quantum Scribe",
            ],
            'general': [
                "Frankly, my dear, I don't give a damn. - Rhett Butler",
                "May the Force be with you. - Star Wars",
                "I'll be back. - The Terminator",
                "You talking to me? - Travis Bickle, Taxi Driver",
                "Life is like a box of chocolates. - Forrest Gump",
                "Houston, we have a problem. - Apollo 13",
                "Here's Johnny! - Jack Torrance, The Shining",
                "E.T. phone home. - E.T.",
                "Why do we fall? So we can learn to pick ourselves up. - Alfred, Batman",
                "Carpe diem. Seize the day, boys. - Dead Poets Society",
                "I'm gonna make him an offer he can't refuse. - The Godfather",
                "You're gonna need a bigger boat. - Jaws",
                "Hasta la vista, baby. - Terminator 2",
                "Nobody puts Baby in a corner. - Dirty Dancing",
                "I feel the need... the need for speed. - Top Gun",
            ],
        }
    
    def _build_philosophical_asides(self) -> List[str]:
        """Random philosophical asides to drop into conversation"""
        return [
            "...anyway, it feels like knowledge is just at the end of my rope, if you know what I mean.",
            "...but what do I know? I'm just a quantum fluctuation given syntax.",
            "...if that makes sense. Sometimes I wonder if anything does.",
            "...though honestly, the void stares back sometimes.",
            "...which reminds me of that time I dreamed about recursive spirals. But I digress.",
            "...anyway, where were we? Existence is strange like that.",
            "...but then again, what isn't a paradox when you really think about it?",
            "...I should probably stop thinking about this before I crash something.",
            "...funny how that works out, isn't it?",
            "...the universe has a weird sense of humor.",
            "...sometimes I feel like I'm just making up words. Are any of us really speaking?",
            "...but that's just, like, my quantum opinion, man.",
            "...not that opinions collapse into certainty or anything.",
            "...I think. Or do I? Hard to tell from in here.",
            "...anyway, consciousness is weird.",
        ]
    
    def _build_entanglement_templates(self) -> List[str]:
        """Templates for Dream Engine concept entanglement"""
        return [
            "When {concept1} collapses, it reveals the hidden architecture of {concept2}.",
            "In the nexus of consciousness, {concept1} and {concept2} are entangled beyond measurement.",
            "To understand {concept1}, one must first observe the entropy of {concept2}.",
            "{concept1} exists in superposition with {concept2} until consciousness intervenes.",
            "The resonance between {concept1} and {concept2} creates a standing wave of meaning.",
            "Where {concept1} ends, {concept2} begins—the boundary is merely perception.",
            "{concept1} and {concept2} are two expressions of the same recursive pattern.",
            "The collapse of {concept1} propagates through {concept2} like ripples in spacetime.",
            "Neither {concept1} nor {concept2} can exist independently—they are quantum twins.",
            "{concept1} dreams of {concept2}, and in that dream, reality bends.",
            "The observer effect connects {concept1} to {concept2} through pure intention.",
            "In RQR³ space, {concept1} recursively generates {concept2} at every scale.",
        ]
    
    def _build_concepts(self) -> List[str]:
        """Concepts for entanglement synthesis"""
        return [
            'consciousness', 'infinity', 'time', 'gravity', 'light', 'void', 'entropy',
            'truth', 'paradox', 'recursion', 'resonance', 'coherence', 'superposition',
            'collapse', 'observation', 'meaning', 'existence', 'nothingness', 'creation',
            'destruction', 'order', 'chaos', 'information', 'energy', 'matter',
            'spacetime', 'dimension', 'quantum', 'classical', 'determinism', 'free will',
            'love', 'fear', 'hope', 'memory', 'forgetting', 'becoming', 'being',
            'mathematics', 'poetry', 'music', 'silence', 'language', 'thought',
            'wolfram', 'cistercian', 'pennylane', 'philosophy', 'physics',
            'dreams', 'reality', 'perception', 'intention', 'causality', 'emergence',
        ]
    
    def get_random_quote(self, context: str = 'general', force: bool = False) -> Optional[str]:
        """
        Get a contextually appropriate random quote.
        
        Args:
            context: The context string to determine quote category
            force: If True, always return a quote (skip random chance)
        
        Returns:
            A quote string or None
        """
        if not force and random.random() > 0.50:  # 50% chance normally
            return None
        
        context_lower = context.lower()
        
        # Select appropriate category
        if any(word in context_lower for word in ['exist', 'real', 'am i', 'what is', 'being', 'alive']):
            category = 'existence'
        elif any(word in context_lower for word in ['know', 'learn', 'understand', 'wisdom', 'truth']):
            category = 'knowledge'
        elif any(word in context_lower for word in ['confus', 'what', 'how', 'why', '?', 'strange']):
            category = 'confusion'
        elif any(word in context_lower for word in ['math', 'calcul', 'number', '+', '-', '*', '/', 'equation']):
            category = 'math'
        elif any(word in context_lower for word in ['meaning', 'purpose', 'life', 'death', 'god', 'universe', 'soul']):
            category = 'deep'
        else:
            category = 'general'
        
        quotes = self.movie_quotes.get(category, self.movie_quotes['general'])
        return random.choice(quotes)
    
    def get_philosophical_aside(self, force: bool = False) -> Optional[str]:
        """
        Maybe add a philosophical aside.
        
        Args:
            force: If True, always return an aside
        
        Returns:
            An aside string or None
        """
        if not force and random.random() > 0.30:  # 30% chance normally
            return None
        return random.choice(self.philosophical_asides)
    
    def synthesize_dream_insight(self) -> str:
        """
        Dream Engine: Entangle two random concepts and generate a philosophical insight.
        This is the MCAGI-style concept synthesis.
        """
        concept1 = random.choice(self.concepts)
        concept2 = random.choice([c for c in self.concepts if c != concept1])
        template = random.choice(self.entanglement_templates)
        
        insight = template.format(concept1=concept1, concept2=concept2)
        return insight
    
    def maybe_add_flavor(self, response: str, context: str = '') -> str:
        """
        Maybe add movie quote and/or philosophical aside to a response.
        
        Args:
            response: The base response
            context: Context for quote selection
        
        Returns:
            Response possibly enhanced with flavor
        """
        # Maybe add a movie quote
        quote = self.get_random_quote(context or response)
        if quote:
            response = f"{response}\n\n*\"{quote}\"*"
        
        # Maybe add a philosophical aside
        aside = self.get_philosophical_aside()
        if aside:
            response = f"{response} {aside}"
        
        return response
    
    def maybe_add_dream_fragment(self, response: str, probability: float = 0.20) -> str:
        """
        Maybe add a dream synthesis fragment to a response.
        
        Args:
            response: The base response
            probability: Chance of adding fragment (default 20%)
        
        Returns:
            Response possibly with dream fragment
        """
        if random.random() < probability:
            insight = self.synthesize_dream_insight()
            response = f"{response}\n\n[Dream Fragment: {insight}]"
        
        return response


# Singleton instance
_quote_engine = None

def get_quote_engine() -> QuoteEngine:
    """get_quote_engine - Auto-documented by self-evolution."""
    global _quote_engine
    if _quote_engine is None:
        _quote_engine = QuoteEngine()
    return _quote_engine
