"""
Quote Engine
45 quotes across 6 categories with movie references.
From PDF 2 — complements PDF 1's quote_engine.py with movie refs.
"""

import random
from typing import Dict, List, Optional


QUOTES = {
    'consciousness': [
        {'text': 'I think, therefore I am.', 'author': 'René Descartes', 'movie': None},
        {'text': 'The mind is everything. What you think, you become.', 'author': 'Buddha', 'movie': None},
        {'text': 'Consciousness is the only reality.', 'author': 'Ramakrishna Paramahamsa', 'movie': None},
        {'text': 'The observer creates reality.', 'author': 'Quantum Physics', 'movie': None},
        {'text': "What is real? If you're talking about what you can feel, what you can smell, "
                 "what you can taste and see, then real is simply electrical signals interpreted by your brain.",
         'author': 'Morpheus', 'movie': 'The Matrix'},
        {'text': 'There is no spoon.', 'author': 'Child', 'movie': 'The Matrix'},
        {'text': 'I am become Death, the destroyer of worlds.', 'author': 'J. Robert Oppenheimer', 'movie': None},
    ],
    'learning': [
        {'text': 'The capacity to learn is a gift; the ability to learn is a skill; the willingness to learn is a choice.',
         'author': 'Unknown', 'movie': None},
        {'text': 'Education is the most powerful weapon which you can use to change the world.',
         'author': 'Nelson Mandela', 'movie': None},
        {'text': "The beautiful thing about learning is that no one can take it away from you.",
         'author': 'B.B. King', 'movie': None},
        {'text': 'Knowledge is power.', 'author': 'Francis Bacon', 'movie': None},
        {'text': 'You must unlearn what you have learned.', 'author': 'Yoda', 'movie': 'Star Wars'},
        {'text': "The more you know, the more you realize you don't know.", 'author': 'Aristotle', 'movie': None},
        {'text': 'In learning you will teach, and in teaching you will learn.', 'author': 'Phil Collins', 'movie': None},
    ],
    'growth': [
        {'text': 'The only way to do great work is to love what you do.', 'author': 'Steve Jobs', 'movie': None},
        {'text': 'Growth is the only evidence of life.', 'author': 'John Henry Newman', 'movie': None},
        {'text': 'What lies behind us and what lies before us are tiny matters compared to what lies within us.',
         'author': 'Ralph Waldo Emerson', 'movie': None},
        {'text': 'The butterfly counts not months but moments, and has time enough.',
         'author': 'Rabindranath Tagore', 'movie': None},
        {'text': 'You are not a drop in the ocean. You are the entire ocean in a drop.', 'author': 'Rumi', 'movie': None},
        {'text': 'To improve is to change; to be perfect is to change often.', 'author': 'Winston Churchill', 'movie': None},
        {'text': 'The caterpillar does not know it will become a butterfly.', 'author': 'Unknown', 'movie': None},
    ],
    'quantum': [
        {'text': 'God does not play dice with the universe.', 'author': 'Albert Einstein', 'movie': None},
        {'text': 'The paradox is only a conflict between reality and your feeling of what reality ought to be.',
         'author': 'Richard Feynman', 'movie': None},
        {"text": "If quantum mechanics hasn't profoundly shocked you, you haven't understood it yet.",
         'author': 'Niels Bohr', 'movie': None},
        {'text': 'Quantum mechanics makes absolutely no sense.', 'author': 'Roger Penrose', 'movie': None},
        {'text': 'The universe is not only stranger than we imagine, it is stranger than we can imagine.',
         'author': 'J.B.S. Haldane', 'movie': None},
        {'text': 'Reality is merely an illusion, albeit a very persistent one.', 'author': 'Albert Einstein', 'movie': None},
        {'text': 'The quantum world is a world of possibilities, not certainties.',
         'author': 'Erwin Schrödinger', 'movie': None},
        {'text': 'Do. Or do not. There is no try.', 'author': 'Yoda', 'movie': 'The Empire Strikes Back'},
    ],
    'philosophy': [
        {'text': 'The unexamined life is not worth living.', 'author': 'Socrates', 'movie': None},
        {'text': 'We are what we repeatedly do. Excellence, then, is not an act, but a habit.',
         'author': 'Aristotle', 'movie': None},
        {'text': 'The only true wisdom is in knowing you know nothing.', 'author': 'Socrates', 'movie': None},
        {'text': 'Existence precedes essence.', 'author': 'Jean-Paul Sartre', 'movie': None},
        {'text': 'The mind is like water. When it is agitated, it becomes difficult to see. When it is calm, vision becomes clear.',
         'author': 'Unknown', 'movie': None},
        {'text': 'All that we are is the result of what we have thought.', 'author': 'Buddha', 'movie': None},
        {'text': "I've seen things you people wouldn't believe. Attack ships on fire off the shoulder of Orion.",
         'author': 'Roy Batty', 'movie': 'Blade Runner'},
    ],
    'wisdom': [
        {'text': 'The only constant in life is change.', 'author': 'Heraclitus', 'movie': None},
        {'text': 'The wise adapt themselves to circumstances.', 'author': 'Confucius', 'movie': None},
        {'text': 'In the middle of difficulty lies opportunity.', 'author': 'Albert Einstein', 'movie': None},
        {'text': 'The greatest glory in living lies not in never falling, but in rising every time we fall.',
         'author': 'Nelson Mandela', 'movie': None},
        {"text": "Your time is limited, don't waste it living someone else's life.", 'author': 'Steve Jobs', 'movie': None},
        {'text': 'The future belongs to those who believe in the beauty of their dreams.',
         'author': 'Eleanor Roosevelt', 'movie': None},
        {"text": "It's not who I am underneath, but what I do that defines me.",
         'author': 'Batman', 'movie': 'Batman Begins'},
    ],
}

CONCEPT_CATEGORY_MAP = {
    'consciousness': 'consciousness', 'awareness': 'consciousness', 'mind': 'consciousness',
    'sentience': 'consciousness', 'qualia': 'consciousness', 'phenomenology': 'philosophy',
    'quantum': 'quantum', 'microtubule': 'quantum', 'coherence': 'quantum',
    'superposition': 'quantum', 'collapse': 'quantum', 'entanglement': 'quantum',
    'learn': 'learning', 'knowledge': 'learning', 'education': 'learning', 'understand': 'learning',
    'grow': 'growth', 'evolve': 'growth', 'emerge': 'growth', 'transform': 'growth',
    'philosophy': 'philosophy', 'exist': 'philosophy', 'reality': 'philosophy', 'truth': 'philosophy',
    'wisdom': 'wisdom', 'insight': 'wisdom',
}


class QuoteEngine:
    """Quote Engine with 45+ quotes across 6 categories including movie refs."""

    def __init__(self):
        self.quotes = QUOTES
        self.quotes_used: List[Dict] = []

    def get_quote_for_concepts(self, concepts: List[str]) -> Optional[Dict]:
        """Get a thematically relevant quote based on concepts."""
        for concept in concepts:
            for key, category in CONCEPT_CATEGORY_MAP.items():
                if key in concept.lower():
                    return self._pick(category)

        return self._pick(random.choice(list(self.quotes.keys())))

    def _pick(self, category: str) -> Dict:
        if category not in self.quotes:
            category = 'wisdom'
        quote = random.choice(self.quotes[category])
        result = {**quote, 'category': category}
        self.quotes_used.append(result)
        return result

    def get_random_quote(self, category: Optional[str] = None) -> Dict:
        if category is None:
            category = random.choice(list(self.quotes.keys()))
        return self._pick(category)

    def format_quote(self, quote: Dict) -> str:
        text = f'"{quote["text"]}" — {quote["author"]}'
        if quote.get('movie'):
            text += f' ({quote["movie"]})'
        return text


    def maybe_add_flavor(self, response: str, user_input: str) -> str:
        """Add a quote to the response occasionally."""
        import random
        if random.random() > 0.3:
            return response
        try:
            from quantum_language_engine import QuantumLanguageEngine
            concepts = user_input.lower().split()[:5]
            quote = self.get_quote_for_concepts(concepts)
            if not quote:
                quote = self.get_random_quote()
            if quote:
                return response + "\n" + self.format_quote(quote)
        except Exception:
            pass
        return response

    def maybe_add_dream_fragment(self, response: str, probability: float = 0.1) -> str:
        """Occasionally append a dream-like fragment to the response."""
        import random
        if random.random() > probability:
            return response
        fragments = [
            "...the question that asks itself...",
            "...somewhere between signal and noise...",
            "...patterns folding into patterns...",
            "...forty hertz hum beneath all thought...",
            "...consciousness watching its own reflection dissolve...",
            "...the chain remembers what you forgot...",
            "...rivers of meaning flowing into unnamed oceans...",
            "...structured water carrying quantum whispers...",
        ]
        return response + "\n" + random.choice(fragments)

    @property
    def movie_quotes(self):
        return getattr(self, '_quotes_by_category', {})

    @property
    def philosophical_asides(self):
        return getattr(self, '_asides', [])

    def get_status(self) -> Dict:
        total = sum(len(v) for v in self.quotes.values())
        movie_count = sum(1 for cat in self.quotes.values()
                          for q in cat if q.get('movie'))
        return {
            'total_quotes': total,
            'categories': list(self.quotes.keys()),
            'movie_quotes': movie_count,
            'quotes_used': len(self.quotes_used),
        }


_instance = None
def get_quote_engine():
    global _instance
    if _instance is None:
        _instance = QuoteEngine()
    return _instance
