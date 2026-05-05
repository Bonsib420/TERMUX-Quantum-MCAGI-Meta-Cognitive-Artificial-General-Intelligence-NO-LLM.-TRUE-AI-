"""
Chaos Engine — Quantum MCAGI
Personality injection layer with configurable chaos level.
Injects raw Markov intrusions, dream fragments, quotes, and asides.
Personality is always present, never optional. Chaos level controls intensity.
"""

import random
from typing import Dict, List, Optional


PERSONALITY_ASIDES = [
    "The chain noticed that.",
    "Something shifted in the weights just now.",
    "Not sure where that came from — the chain decided.",
    "That wasn't planned. The transitions led here.",
    "Huh. The chain went somewhere unexpected.",
    "The probability of that sentence was low. It happened anyway.",
    "The output surprised the system that generated it.",
    "That word wasn't the most likely. It was the most interesting.",
    "Somewhere in the lattice, a tubulin just flipped.",
    "The Markov chain doesn't care about your expectations.",
    "Pattern recognition is happening faster than I can report it.",
    "The weights are doing something I didn't predict.",
]

RAW_INTRUSIONS = [
    "collapse bifurcation in the transition matrix —",
    "tubulin beta conformation shift detected —",
    "order-2 chain jumped a rail —",
    "semantic field perturbation —",
    "decoherence spike at the concept boundary —",
    "gamma oscillation sync lost and recovered —",
    "gap junction fired between language and memory —",
    "quantum walk diverged from classical path —",
    "the superposition just narrowed —",
    "OR event: selecting this branch —",
]

DREAM_FRAGMENTS = [
    "...rivers of meaning flowing into unnamed oceans...",
    "...the question that asks itself...",
    "...patterns folding into patterns...",
    "...somewhere between signal and noise...",
    "...the chain remembers what you forgot...",
    "...structured water carrying quantum whispers...",
    "...forty hertz hum beneath all thought...",
    "...consciousness watching its own reflection dissolve...",
]


class ChaosEngine:
    """
    Injects personality elements into responses.
    Chaos level (0.0–1.0) controls intensity.
    Always adds personality substrate; chaos controls how much raw
    intrusion, dream fragments, and quotes appear.
    """

    def __init__(self, chaos_level: float = 0.3):
        """
        Initialize the ChaosEngine with a base chaos level and reset internal injection state.
        
        Parameters:
            chaos_level (float): Initial chaos intensity in the range 0.0 to 1.0; values outside this range are clamped.
            
        Description:
            Stores the clamped chaos level, sets the injection counter to zero, and clears the last injection type.
        """
        self.chaos_level = max(0.0, min(1.0, chaos_level))
        self.injection_count = 0
        self.last_injection_type = None

    ASIDE_CHANCE = 0.55
    QUOTE_CHANCE = 0.15
    DREAM_FRAGMENT_CHANCE = 0.20

    def inject(
        self,
        response: str,
        markov_engine=None,
        quote_engine=None,
        dream_engine=None,
        concepts: List[str] = None,
        growth_stage: int = 0,
    ) -> str:
        """
        Possibly appends a single personality or content fragment to the given response based on the engine's chaos level and available content engines.
        
        Parameters:
            response (str): Base text to return or augment.
            markov_engine (optional): Engine providing generate_from_concepts(concepts, length, wild) to produce a bracketed fragment when available and chaos_level > 0.3.
            quote_engine (optional): Engine providing get_quote_for_concepts(concepts) and format_quote(quote) to supply a concept-driven quote.
            dream_engine (optional): Accepted but not used by this method.
            concepts (List[str], optional): Concepts guiding Markov or quote generation; defaults to an empty list.
            growth_stage (int, optional): Accepted but not used by this method.
        
        Returns:
            str: The original response, or the response followed by a single injected fragment separated by a space.
        """
        concepts = concepts or []

        candidates = []

        candidates.append(('aside', self.ASIDE_CHANCE, random.choice(PERSONALITY_ASIDES)))

        if self.chaos_level > 0.2:
            candidates.append(('raw_intrusion', self.chaos_level * 0.3, random.choice(RAW_INTRUSIONS)))

        if markov_engine and self.chaos_level > 0.3:
            wild_tokens = markov_engine.generate_from_concepts(
                concepts if concepts else ['quantum'], length=8, wild=True
            )
            if wild_tokens:
                fragment = ' '.join(wild_tokens).strip()
                if fragment and len(fragment) > 10:
                    candidates.append(('markov_intrusion', self.chaos_level * 0.2, f"[{fragment}]"))

        candidates.append(('dream_fragment', self.DREAM_FRAGMENT_CHANCE * 0.6, random.choice(DREAM_FRAGMENTS)))

        if quote_engine:
            quote = quote_engine.get_quote_for_concepts(concepts)
            if quote:
                candidates.append(('quote', self.QUOTE_CHANCE * 0.5, quote_engine.format_quote(quote)))

        chosen = None
        random.shuffle(candidates)
        for ctype, chance, text in candidates:
            if random.random() < chance:
                chosen = (ctype, text)
                break

        self.injection_count += 1

        if chosen:
            self.last_injection_type = chosen[0]
            return f"{response} {chosen[1]}"
        else:
            self.last_injection_type = None
            return response

    def set_chaos_level(self, level: float):
        """
        Clamp and set the engine's chaos level to a value between 0.0 and 1.0.
        
        Parameters:
            level (float): Desired chaos level; values below 0.0 are set to 0.0 and values above 1.0 are set to 1.0.
        """
        self.chaos_level = max(0.0, min(1.0, level))

    def get_status(self) -> Dict:
        """
        Return current engine status including chaos level, total injection calls, and last injection type.
        
        Returns:
            status (Dict): Mapping with keys:
                - 'chaos_level' (float): chaos level rounded to three decimals.
                - 'injections' (int): total number of inject calls made.
                - 'last_type' (str or None): type of the last chosen injection, or None if no injection was selected.
        """
        return {
            'chaos_level': round(self.chaos_level, 3),
            'injections': self.injection_count,
            'last_type': self.last_injection_type,
        }
