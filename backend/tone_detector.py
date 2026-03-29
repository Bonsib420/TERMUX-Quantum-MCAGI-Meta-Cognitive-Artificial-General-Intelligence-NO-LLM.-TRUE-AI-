"""
Tone Detection — VADER sentiment + register classification
Classifies input into 4 registers: casual, conversational, analytical, philosophical
"""

try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    _vader = SentimentIntensityAnalyzer()
    HAS_VADER = True
except ImportError:
    HAS_VADER = False


# Deep thinking markers
DEEP_MARKERS = {
    'consciousness', 'quantum', 'reality', 'existence', 'universe',
    'philosophy', 'metaphysics', 'ontology', 'epistemology', 'meaning',
    'truth', 'infinity', 'paradox', 'emergence', 'recursive', 'resonance',
    'collapse', 'superposition', 'entanglement', 'observation', 'identity',
    'perception', 'awareness', 'cognition', 'fundamental', 'abstract',
    'theoretical', 'mathematical', 'dimension', 'spacetime', 'entropy',
    'information', 'complexity', 'determinism', 'causality', 'axiom',
    'transcendent', 'phenomenal', 'subjective', 'objective', 'dualism',
    'monism', 'panpsychism', 'materialism', 'idealism', 'solipsism',
    'microtubule', 'tubulin', 'decoherence', 'wavefunction', 'eigenstate',
}

QUESTION_WORDS = {'what', 'why', 'how', 'when', 'where', 'who', 'which', 'is', 'are', 'do', 'does', 'can', 'could', 'would', 'should'}


def detect_tone(text: str) -> dict:
    """
    Detect tone and return register classification.
    
    Returns:
        dict with keys:
            register: 'casual' | 'conversational' | 'analytical' | 'philosophical'
            depth: float 0.0-1.0
            sentiment: dict with pos/neg/neu/compound (if VADER available)
    """
    words = text.lower().split()
    word_count = len(words)
    word_set = set(words)
    
    # VADER sentiment
    sentiment = {}
    if HAS_VADER:
        scores = _vader.polarity_scores(text)
        sentiment = {
            'positive': scores['pos'],
            'negative': scores['neg'],
            'neutral': scores['neu'],
            'compound': scores['compound'],
        }
    
    # Count deep markers
    deep_count = len(word_set & DEEP_MARKERS)
    
    # Check for question words
    has_question = bool(word_set & QUESTION_WORDS) or text.strip().endswith('?')
    
    # Calculate depth score
    depth = 0.0
    
    # Length contributes
    if word_count > 20:
        depth += 0.2
    elif word_count > 10:
        depth += 0.1
    
    # Deep markers
    depth += min(0.5, deep_count * 0.15)
    
    # Questions about deep topics
    if has_question and deep_count > 0:
        depth += 0.2
    
    # Multiple sentences suggest analytical
    sentence_count = text.count('.') + text.count('?') + text.count('!')
    if sentence_count > 2:
        depth += 0.1
    
    depth = min(1.0, depth)
    
    # Classify register
    if depth < 0.15:
        register = 'casual'
    elif depth < 0.35:
        register = 'conversational'
    elif depth < 0.65:
        register = 'analytical'
    else:
        register = 'philosophical'
    
    return {
        'register': register,
        'depth': round(depth, 3),
        'sentiment': sentiment,
        'deep_markers': deep_count,
        'word_count': word_count,
    }


if __name__ == "__main__":
    tests = [
        "hello",
        "hey what's up",
        "can you explain how microtubules work?",
        "what is the nature of consciousness and how does quantum collapse relate to subjective experience?",
    ]
    for t in tests:
        result = detect_tone(t)
        print(f"{t[:50]:50s} -> {result['register']:15s} depth={result['depth']}")
