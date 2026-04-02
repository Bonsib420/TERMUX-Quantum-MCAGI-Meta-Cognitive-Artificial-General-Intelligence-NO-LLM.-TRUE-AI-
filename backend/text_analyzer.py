"""
🔍 Text Analyzer
Determines if text sounds human or LLM-generated.
Helps Quantum AI produce more authentic responses.
"""

import re
from typing import Dict, List, Tuple


class TextAnalyzer:
    """
    Analyzes text to determine if it sounds human or LLM-generated.
    
    LLM tells:
    - Overly formal language
    - Excessive hedging
    - Repetitive structures
    - Lack of personality
    - Too perfect grammar
    - Generic openings/closings
    - Excessive caveats
    """
    
    def __init__(self):
        # LLM-typical phrases
        self.llm_phrases = [
            "i cannot", "i can't", "as an ai",
            "i don't have personal", "i'm not able to",
            "it's important to note", "it's worth noting",
            "i'd be happy to help", "absolutely!",
            "great question", "that's a great question",
            "let me break this down", "here's what i can tell you",
            "i understand you're asking", "based on the information",
            "however, it's important", "while i can",
            "i hope this helps", "feel free to ask",
            "certainly!", "of course!",
            "firstly", "secondly", "thirdly",
            "in conclusion", "to summarize"
        ]
        
        # Human-like phrases
        self.human_phrases = [
            "honestly", "actually", "basically",
            "i mean", "you know", "like",
            "anyway", "so yeah", "right?",
            "kinda", "sorta", "pretty much",
            "tbh", "imo", "idk",
            "haha", "lol", "hmm",
            "oh", "well", "ah"
        ]
        
        # LLM structural patterns
        self.llm_patterns = [
            r'\b(firstly|secondly|thirdly|finally)\b',
            r'it\'s (important|worth) (to note|noting)',
            r'(however|additionally|furthermore|moreover)',
            r'\bI\'d be happy to\b',
            r'(certainly|absolutely)!',
            r'let me (explain|break|help)',
            r'(great|good|excellent) question',
        ]
    
    def analyze(self, text: str) -> Dict:
        """
        Analyze text for human vs LLM characteristics.
        
        Returns:
            Dict with scores and analysis
        """
        text_lower = text.lower()
        words = text_lower.split()
        sentences = re.split(r'[.!?]+', text)

        analysis = {
            'text_length': len(text),
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'llm_score': 0.0,
            'human_score': 0.0,
            'indicators': {
                'llm': [],
                'human': []
            },
            'verdict': '',
            'confidence': 0.0
        }

        return self._analyze_continued(analysis, sentences, text_lower, words, text)

    def _analyze_continued(self, analysis, sentences, text_lower, words, text):
        """Continuation of analyze — auto-extracted by self-evolution."""
        # Check for LLM phrases
        llm_phrase_count = 0
        for phrase in self.llm_phrases:
            if phrase in text_lower:
                llm_phrase_count += 1
                analysis['indicators']['llm'].append(f'Contains "{phrase}"')

        # Check for human phrases
        human_phrase_count = 0
        for phrase in self.human_phrases:
            if phrase in text_lower:
                human_phrase_count += 1
                analysis['indicators']['human'].append(f'Contains "{phrase}"')

        # Check for LLM patterns
        pattern_count = 0
        for pattern in self.llm_patterns:
            if re.search(pattern, text_lower):
                pattern_count += 1
                analysis['indicators']['llm'].append(f'Pattern: {pattern[:30]}...')

        # Check sentence structure variety
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        if sentence_lengths:
            length_variety = max(sentence_lengths) - min(sentence_lengths) if len(sentence_lengths) > 1 else 0
            if length_variety < 3:
                analysis['indicators']['llm'].append('Low sentence length variety')
            else:
                analysis['indicators']['human'].append('Good sentence length variety')

        # Check for contractions (humans use more)
        contractions = re.findall(r"\b\w+'\w+\b", text)
        if len(contractions) > len(words) * 0.05:
            analysis['indicators']['human'].append('Good use of contractions')

        # Check for exclamation overuse (LLM tendency)
        exclamation_count = text.count('!')
        if exclamation_count > 2:
            analysis['indicators']['llm'].append('Excessive exclamation marks')

        # Check for paragraph structure
        paragraphs = text.split('\n\n')
        if len(paragraphs) > 3 and all(len(p) > 100 for p in paragraphs if p.strip()):
            analysis['indicators']['llm'].append('Overly structured paragraphs')

        # Check for hedging
        hedging_words = ['perhaps', 'maybe', 'possibly', 'might', 'could be', 'it seems']
        hedge_count = sum(1 for h in hedging_words if h in text_lower)
        if hedge_count > 3:
            analysis['indicators']['llm'].append('Excessive hedging')

        # Calculate scores
        analysis['llm_score'] = min(1.0, (llm_phrase_count * 0.1 + pattern_count * 0.15))
        analysis['human_score'] = min(1.0, (human_phrase_count * 0.1 + len(contractions) * 0.02))

        return self.__analyze_continued_continued(analysis)

    def __analyze_continued_continued(self, analysis):
        """Continuation of _analyze_continued — auto-extracted by self-evolution."""
        # Adjust for indicators
        analysis['llm_score'] += len(analysis['indicators']['llm']) * 0.05
        analysis['human_score'] += len(analysis['indicators']['human']) * 0.05

        # Normalize
        total = analysis['llm_score'] + analysis['human_score']
        if total > 0:
            analysis['llm_score'] /= total
            analysis['human_score'] /= total
        else:
            analysis['llm_score'] = 0.5
            analysis['human_score'] = 0.5

        # Verdict
        if analysis['human_score'] > 0.6:
            analysis['verdict'] = 'Likely Human'
            analysis['confidence'] = analysis['human_score']
        elif analysis['llm_score'] > 0.6:
            analysis['verdict'] = 'Likely LLM'
            analysis['confidence'] = analysis['llm_score']
        else:
            analysis['verdict'] = 'Uncertain'
            analysis['confidence'] = max(analysis['llm_score'], analysis['human_score'])

        return analysis


    
    def get_improvement_suggestions(self, text: str) -> List[str]:
        """
        Get suggestions for making text sound more human.
        """
        analysis = self.analyze(text)
        suggestions = []
        
        for indicator in analysis['indicators']['llm']:
            if 'exclamation' in indicator.lower():
                suggestions.append('Reduce exclamation marks - they can seem overly enthusiastic')
            elif 'hedging' in indicator.lower():
                suggestions.append('Be more direct - less "perhaps" and "maybe"')
            elif 'pattern' in indicator.lower():
                suggestions.append('Vary your sentence structures more')
            elif 'structured' in indicator.lower():
                suggestions.append('Use more natural paragraph breaks')
        
        # Generic suggestions based on score
        if analysis['llm_score'] > 0.5:
            suggestions.extend([
                'Use contractions more (e.g., "I\'m" instead of "I am")',
                'Add conversational filler words occasionally',
                'Vary sentence length more dramatically',
                'Show uncertainty naturally rather than with caveats',
                'Use more direct, casual language'
            ])
        
        return suggestions[:5]  # Top 5 suggestions
    
    def make_more_human(self, text: str) -> str:
        """
        Attempt to make text sound more human.
        Note: This is a simple transformation, not AI-powered.
        """
        result = text
        
        # Expand contractions sometimes
        replacements = [
            ("I am", "I'm"),
            ("I have", "I've"),
            ("It is", "It's"),
            ("That is", "That's"),
            ("do not", "don't"),
            ("cannot", "can't"),
            ("will not", "won't"),
        ]
        
        for formal, casual in replacements:
            result = result.replace(formal, casual)
        
        # Remove some LLM-isms
        llm_removals = [
            ("Certainly! ", ""),
            ("Absolutely! ", ""),
            ("Great question! ", ""),
            ("It's important to note that ", ""),
            ("It's worth noting that ", ""),
        ]
        
        for phrase, replacement in llm_removals:
            result = result.replace(phrase, replacement)
        
        return result


# Global instance
_text_analyzer = None

def get_text_analyzer() -> TextAnalyzer:
    """Get or create text analyzer instance"""
    global _text_analyzer
    if _text_analyzer is None:
        _text_analyzer = TextAnalyzer()
    return _text_analyzer
