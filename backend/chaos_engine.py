"""
Chaos Engine — Quantum MCAGI
Personality injection layer with configurable chaos level.
Injects raw Markov intrusions, dream fragments, quotes, and asides.
Personality is always present, never optional. Chaos level controls intensity.
"""

import random
from typing import Dict, List, Optional


PERSONALITY_ASIDES = []  # removed — use Markov generation instead

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

DREAM_FRAGMENTS = []  # removed — use Markov generation instead


class ChaosEngine:
    """
    Injects personality elements into responses.
    Chaos level (0.0–1.0) controls intensity.
    Always adds personality substrate; chaos controls how much raw
    intrusion, dream fragments, and quotes appear.
    """

    def __init__(self, chaos_level: float = 0.3):
        self.chaos_level = max(0.0, min(1.0, chaos_level))
        self.injection_count = 0
        self.last_injection_type = None

    ASIDE_CHANCE = 0.30
    QUOTE_CHANCE = 0.30
    DREAM_FRAGMENT_CHANCE = 0.25

    def inject(
        self,
        response: str,
        markov_engine=None,
        quote_engine=None,
        dream_engine=None,
        concepts: List[str] = None,
        growth_stage: int = 0,
    ) -> str:
        concepts = concepts or []

        candidates = []

        if markov_engine:
            aside_tokens = markov_engine.generate_from_concepts(
                concepts if concepts else ['consciousness'], length=6, wild=False
            )
            if aside_tokens:
                aside_text = ' '.join(aside_tokens).strip()
                if aside_text and len(aside_text) > 5:
                    candidates.append(('aside', self.ASIDE_CHANCE, aside_text))

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

        if markov_engine:
            dream_tokens = markov_engine.generate_from_concepts(
                concepts if concepts else ['reality'], length=10, wild=True
            )
            if dream_tokens:
                dream_text = ' '.join(dream_tokens).strip()
                if dream_text and len(dream_text) > 10:
                    candidates.append(('dream_fragment', self.DREAM_FRAGMENT_CHANCE * 0.6, f"...{dream_text}..."))

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
        self.chaos_level = max(0.0, min(1.0, level))

    def get_status(self) -> Dict:
        return {
            'chaos_level': round(self.chaos_level, 3),
            'injections': self.injection_count,
            'last_type': self.last_injection_type,
        }
