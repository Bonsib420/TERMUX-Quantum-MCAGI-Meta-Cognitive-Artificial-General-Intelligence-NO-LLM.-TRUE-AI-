"""
🔤 Quantum Language Generator — Vocabulary & Generation Methods
===============================================================
Word selection, sentence/response generation, creative output.
"""

import random
from typing import Dict, List, Tuple, Optional


class QuantumLanguageGeneratorExtMixin:
    """Extended methods for QuantumLanguageGenerator — auto-extracted by self-evolution."""

    def _get_word_by_type(self, word_type: str, context: List[str] = None) -> str:
        """Get a word of specific type, influenced by context"""
        
        # Collect all words of this type
        words = []
        
        if word_type == 'noun':
            for category in self.vocabulary['nouns'].values():
                words.extend(category)
        elif word_type == 'verb':
            for category in self.vocabulary['verbs'].values():
                words.extend(category)
        elif word_type == 'adjective':
            for category in self.vocabulary['adjectives'].values():
                words.extend(category)
        elif word_type == 'connector':
            for category in self.vocabulary['connectors'].values():
                words.extend(category)
        else:
            for category in self.vocabulary['nouns'].values():
                words.extend(category)
        
        # Safety check - must have words
        if not words:
            return "existence"
        
        # Calculate weights - MUST match words length
        weights = [1.0] * len(words)
        
        if context:
            for i, word in enumerate(words):
                for ctx_word in context[-5:]:
                    if ctx_word in self.semantics:
                        for related, strength in self.semantics[ctx_word]:
                            if word == related or related in word or word in related:
                                weights[i] += strength * 2
        
        # Ensure weights match words length before calling _quantum_select
        if len(weights) != len(words):
            weights = [1.0] * len(words)
        
        return self._quantum_select(words, weights)

    def generate_sentence(self, topic: str = None, include_words: List[str] = None, 
                          style: str = 'philosophical') -> str:
        """
        Generate a complete sentence using quantum word selection.
        
        Args:
            topic: Optional topic to focus on
            include_words: Words that MUST be included (no restrictions)
            style: Generation style
        """
        
        # Select grammar pattern
        pattern = random.choice(self.grammar_patterns)
        
        # Build context from topic
        context = []
        if topic:
            context.extend(topic.lower().split()[:3])
        
        # Generate words following pattern
        sentence_words = []
        
        for word_type in pattern:
            word = self._get_word_by_type(word_type, context + sentence_words)
            sentence_words.append(word)
            context.append(word)
        
        # Insert required words if specified
        if include_words:
            for req_word in include_words:
                if req_word.lower() not in [w.lower() for w in sentence_words]:
                    # Insert at quantum-selected position
                    pos = random.randint(0, len(sentence_words))
                    sentence_words.insert(pos, req_word)
        
        # Capitalize first word and add period
        if sentence_words:
            sentence_words[0] = sentence_words[0].capitalize()
        
        sentence = ' '.join(sentence_words)
        if not sentence.endswith('.') and not sentence.endswith('?'):
            sentence += '.'
        
        return sentence

    def generate_response(self, query: str, num_sentences: int = 3, 
                          required_words: List[str] = None) -> str:
        """
        Generate a multi-sentence response using quantum selection.
        Uses philosophical templates for coherent output.
        """
        query_words = query.lower().split()
        topic_words = [w for w in query_words if len(w) > 3]
        
        sentences = []
        used_required = []
        
        for i in range(num_sentences):
            # Use philosophical template for coherent output
            template = random.choice(self.philosophical_templates)
            sentence = self._fill_template(template, topic_words + [w.lower() for w in (required_words or [])])
            
            # Insert a required word if needed
            if required_words:
                remaining = [w for w in required_words if w not in used_required]
                if remaining:
                    word = remaining[0]
                    used_required.append(word)
                    if word.lower() not in sentence.lower():
                        sentence = sentence.rstrip('.') + f', through the lens of {word}.'
            
            sentences.append(sentence)
        
        return ' '.join(sentences)

    def _fill_template(self, template: str, context_words: List[str] = None) -> str:
        """Fill a philosophical template with quantum-selected words."""
        context = context_words or []
        result = template
        
        # Count how many of each placeholder we need
        noun_count = result.count('{noun}')
        verb_count = result.count('{verb}')
        adj_count = result.count('{adj}')
        conn_count = result.count('{connector}')
        
        # Select words with context influence
        for _ in range(noun_count):
            word = self._get_word_by_type('noun', context)
            result = result.replace('{noun}', word, 1)
            context.append(word)
        
        for _ in range(verb_count):
            word = self._get_word_by_type('verb', context)
            result = result.replace('{verb}', word, 1)
            context.append(word)
        
        for _ in range(adj_count):
            word = self._get_word_by_type('adjective', context)
            result = result.replace('{adj}', word, 1)
            context.append(word)
        
        for _ in range(conn_count):
            word = self._get_word_by_type('connector', context)
            result = result.replace('{connector}', word.capitalize(), 1)
            context.append(word)
        
        return result

    def generate_creative(self, prompt: str, form: str = 'prose', 
                          must_include: List[str] = None) -> str:
        """
        Generate creative content with ZERO restrictions.
        
        Args:
            prompt: Creative prompt
            form: 'prose', 'poem', 'dialogue'
            must_include: Words that MUST appear - ANY words, no restrictions
        """
        
        if form == 'poem':
            return self._generate_poem(prompt, must_include)
        elif form == 'dialogue':
            return self._generate_dialogue(prompt, must_include)
        else:
            return self.generate_response(prompt, num_sentences=5, required_words=must_include)

    def _generate_poem(self, prompt: str, must_include: List[str] = None) -> str:
        """Generate a poem - with ANY words requested"""
        
        lines = []
        topic_words = prompt.lower().split()
        
        # Ensure required words are distributed across lines
        required = must_include or []
        required_per_line = {}
        for i, word in enumerate(required):
            line_num = i % 4  # Distribute across 4 lines
            if line_num not in required_per_line:
                required_per_line[line_num] = []
            required_per_line[line_num].append(word)
        
        for i in range(4):  # 4 lines
            # Get words to include in this line
            line_required = required_per_line.get(i, [])
            
            # Generate line
            line_words = []
            
            # Start with topic-related word
            if topic_words:
                line_words.append(self._get_word_by_type('adjective', topic_words))
            
            # Add required words
            for req in line_required:
                line_words.append(req)
            
            # Fill with quantum-selected words
            while len(line_words) < 5:
                word_type = random.choice(['noun', 'verb', 'adjective'])
                line_words.append(self._get_word_by_type(word_type, line_words + topic_words))
            
            # Arrange into line
            random.shuffle(line_words[1:])  # Keep first word, shuffle rest
            line = ' '.join(line_words)
            line = line.capitalize()
            
            lines.append(line)
        
        return '\n'.join(lines)

    def _generate_dialogue(self, prompt: str, must_include: List[str] = None) -> str:
        """Generate dialogue"""
        
        lines = []
        speakers = ['A', 'B']
        required = must_include or []
        
        for i in range(4):
            speaker = speakers[i % 2]
            include = [required[i]] if i < len(required) else None
            
            sentence = self.generate_sentence(topic=prompt, include_words=include)
            lines.append(f"{speaker}: {sentence}")
        
        return '\n'.join(lines)
