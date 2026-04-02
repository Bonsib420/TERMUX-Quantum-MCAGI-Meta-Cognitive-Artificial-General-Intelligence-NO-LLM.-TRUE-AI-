"""
🧠 Unified Word-by-Word Generator
====================================
Every word position goes through the full pipeline:

1. WordNet generates the candidate pool (semantically valid words)
2. TF-IDF weights candidates by topical relevance
3. Markov transitions weight by grammatical likelihood
4. Orch OR collapses the combined probability into a selection

The pool starts wide and narrows with each word chosen.
Minimum 10 words per response. No templates. No random.choice
on a hardcoded list. Every word is earned.

This is how a brain picks words:
- Dictionary = vocabulary
- Markov = grammar
- TF-IDF = topic
- Orch OR = consciousness deciding
"""

import math
import random
import logging
from typing import List, Dict, Tuple, Optional

try:
    import numpy as np
except ImportError:
    np = None

try:
    import nltk
    from nltk.corpus import wordnet as wn
    HAS_WORDNET = True
except ImportError:
    HAS_WORDNET = False

logger = logging.getLogger("quantum_ai")


class UnifiedGenerator:
    """
    Word-by-word generation with full pipeline at each position.
    
    At each word position:
    1. Build candidate pool from WordNet + Markov + vocabulary
    2. Score each candidate: TF-IDF relevance × Markov transition × semantic fit
    3. Feed scores into Orch OR as tubulin weights
    4. Collapse selects the word
    5. Chosen word constrains next position
    
    The superposition starts maximal and collapses with each word.
    """

    def __init__(self, markov, extractor, orch_or=None):
        """
        Args:
            markov: MarkovChain instance (for transition probabilities)
            extractor: ConceptExtractor instance (for TF-IDF scoring)
            orch_or: OrchORProcessor instance (for quantum collapse)
        """
        self.markov = markov
        self.extractor = extractor
        self.orch_or = orch_or
        
        # WordNet initialization
        if HAS_WORDNET:
            try:
                wn.synsets('test')
                self._has_wordnet = True
            except Exception:
                try:
                    nltk.download('wordnet', quiet=True)
                    nltk.download('omw-1.4', quiet=True)
                    self._has_wordnet = True
                except Exception:
                    self._has_wordnet = False
        else:
            self._has_wordnet = False
        
        # Fallback vocabulary from Markov chain
        self._build_vocab_from_markov()
        
        # Common sentence starters for position 0
        self.starters = [
            'the', 'this', 'what', 'how', 'there', 'it', 'perhaps',
            'every', 'when', 'if', 'our', 'that', 'each', 'between',
            'understanding', 'consciousness', 'reality', 'knowledge',
            'something', 'nothing', 'within', 'beyond', 'through',
        ]
        
        # Common structure words to keep grammar flowing
        self.structure_words = {
            'determiners': ['the', 'a', 'an', 'this', 'that', 'these', 'those', 'each', 'every', 'some'],
            'prepositions': ['of', 'in', 'to', 'for', 'with', 'from', 'by', 'at', 'on', 'through',
                           'between', 'within', 'beyond', 'into', 'across', 'along', 'about'],
            'conjunctions': ['and', 'but', 'or', 'yet', 'so', 'while', 'when', 'where', 'because',
                           'although', 'unless', 'until', 'since', 'if', 'as'],
            'verbs_common': ['is', 'are', 'was', 'has', 'have', 'does', 'can', 'may', 'might',
                           'reveals', 'suggests', 'creates', 'becomes', 'emerges', 'exists',
                           'connects', 'transforms', 'contains', 'shapes', 'defines',
                           'requires', 'produces', 'generates', 'maintains', 'involves'],
        }

    def _build_vocab_from_markov(self):
        """Extract known vocabulary from Markov chain transitions."""
        self.markov_vocab = set()
        for prefix, suffixes in self.markov.chain.items():
            for word in prefix:
                self.markov_vocab.add(word.lower().strip('.,;:!?'))
            for word in suffixes:
                self.markov_vocab.add(word.lower().strip('.,;:!?'))

    def _wordnet_related(self, concept, max_words=30):
        """
        Get all semantically related words from WordNet for a concept.
        Returns words with semantic distance scores.
        """
        if not self._has_wordnet:
            return {}
        
        related = {}
        try:
            synsets = wn.synsets(concept)
            for syn in synsets[:3]:  # Top 3 senses
                # Synonyms (closest)
                for lemma in syn.lemmas():
                    word = lemma.name().replace('_', ' ').lower()
                    if len(word) > 2 and ' ' not in word:
                        related[word] = max(related.get(word, 0), 0.9)
                
                # Hypernyms (broader — "animal" for "dog")
                for hyper in syn.hypernyms():
                    for lemma in hyper.lemmas():
                        word = lemma.name().replace('_', ' ').lower()
                        if len(word) > 2 and ' ' not in word:
                            related[word] = max(related.get(word, 0), 0.7)
                
                # Hyponyms (narrower — "poodle" for "dog")
                for hypo in syn.hyponyms()[:5]:
                    for lemma in hypo.lemmas():
                        word = lemma.name().replace('_', ' ').lower()
                        if len(word) > 2 and ' ' not in word:
                            related[word] = max(related.get(word, 0), 0.6)
                
                # Also-sees and similar-tos
                for also in syn.also_sees()[:3]:
                    for lemma in also.lemmas():
                        word = lemma.name().replace('_', ' ').lower()
                        if len(word) > 2 and ' ' not in word:
                            related[word] = max(related.get(word, 0), 0.5)
            
        except Exception:
            pass
        
        # Sort by score, limit
        sorted_related = sorted(related.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_related[:max_words])

    def _build_candidate_pool(self, position, prev_words, input_concepts,
                              concept_scores, chosen_so_far):
        """
        Build the candidate word pool for this position.
        
        Position 0: Wide open — starters + concept words + WordNet related
        Position 1+: Markov transitions + WordNet expansions + structure words
        
        Returns: dict of {word: base_score}
        """
        candidates = {}

        return self.__build_candidate_pool_continued(candidates, position, prev_words, input_concepts, chosen_so_far)

    def __build_candidate_pool_continued(self, candidates, position, prev_words, input_concepts, chosen_so_far):
        """Continuation of _build_candidate_pool — auto-extracted by self-evolution."""
        if position == 0:
            # First word — broadest pool
            # Starters
            for w in self.starters:
                candidates[w] = 0.3

            # Input concepts themselves (high weight)
            for concept in input_concepts:
                candidates[concept] = 0.8

            # WordNet related to input concepts
            for concept in input_concepts[:3]:
                related = self._wordnet_related(concept, max_words=15)
                for word, score in related.items():
                    candidates[word] = max(candidates.get(word, 0), score * 0.6)

            # Markov starters
            if self.markov.trained and self.markov.starters:
                for starter in self.markov.starters[:20]:
                    candidates[starter[0].lower()] = max(
                        candidates.get(starter[0].lower(), 0), 0.4
                    )

        else:
            # Subsequent positions — Markov transitions are PRIMARY
            if self.markov.trained and len(prev_words) >= self.markov.order:
                prefix = tuple(prev_words[-self.markov.order:])
                if prefix in self.markov.chain:
                    transitions = self.markov.chain[prefix]
                    total = sum(transitions.values())
                    for word, count in transitions.items():
                        candidates[word] = (count / total) * 1.5  # Strong Markov priority

            # If Markov gave few results, try order-1 (last word only)
            if len(candidates) < 3 and prev_words:
                last = prev_words[-1].lower().strip('.,;:!?')
                for prefix, transitions in self.markov.chain.items():
                    if prefix[-1].lower().strip('.,;:!?') == last:
                        total = sum(transitions.values())
                        for word, count in list(transitions.items())[:10]:
                            if word not in candidates:
                                candidates[word] = (count / total) * 0.4

            # WordNet expansions of the last meaningful word
            last_meaningful = None
            for w in reversed(prev_words):
                if len(w) > 3 and w.lower() not in self.extractor.STOPWORDS:
                    last_meaningful = w.lower()
                    break

            if last_meaningful:
                related = self._wordnet_related(last_meaningful, max_words=10)
                for word, score in related.items():
                    if word not in chosen_so_far:
                        candidates[word] = max(candidates.get(word, 0), score * 0.3)

            # Input concepts can re-enter at any position (with decay)
            position_decay = max(0.1, 1.0 - position * 0.05)
            for concept in input_concepts:
                if concept not in chosen_so_far:
                    candidates[concept] = max(
                        candidates.get(concept, 0), 0.4 * position_decay
                    )

            # Structure words available but low priority (grammar glue)
            for category, words in self.structure_words.items():
                for w in words:
                    if w not in candidates:  # Only add if not already from Markov
                        candidates[w] = 0.05

            # Markov vocab as background only if pool is too small
            if len(candidates) < 3:
                for w in random.sample(list(self.markov_vocab),
                                       min(20, len(self.markov_vocab))):
                    if w not in candidates:
                        candidates[w] = 0.05

        # Remove empty strings and very short words (except structure words)
        cleaned = {}
        all_structure = set()
        for words in self.structure_words.values():
            all_structure.update(words)

        for word, score in candidates.items():
            if word and (len(word) >= 2 or word in all_structure):
                cleaned[word] = score

        return cleaned


    def _apply_tfidf_weights(self, candidates, concept_scores):
        """
        Apply TF-IDF relevance weighting to candidates.
        Words that are topically relevant get boosted.
        """
        # Build a quick lookup of concept relevance
        concept_relevance = {}
        for cs in concept_scores:
            if isinstance(cs, dict):
                concept_relevance[cs['concept']] = cs.get('score', 0.5)
        
        max_relevance = max(concept_relevance.values()) if concept_relevance else 1.0
        
        weighted = {}
        for word, base_score in candidates.items():
            # Direct concept match
            if word in concept_relevance:
                tfidf_boost = concept_relevance[word] / max_relevance
                weighted[word] = base_score + tfidf_boost * 0.5
            else:
                # Check if word is in the TF-IDF vocabulary at all
                word_freq = self.extractor.word_frequencies.get(word, 0)
                if word_freq > 0 and self.extractor.total_words > 0:
                    # Known word — slight boost based on information content
                    ic = -math.log(max(word_freq / self.extractor.total_words, 1e-10))
                    ic_normalized = min(1.0, ic / 15.0)  # Normalize to 0-1
                    weighted[word] = base_score + ic_normalized * 0.1
                else:
                    # Unknown word — keep base score
                    weighted[word] = base_score
        
        return weighted

    def _apply_orch_or_collapse(self, candidates, position):
        """
        Use Orch OR to collapse the candidate probabilities.
        The microtubule collapse pattern biases the selection.
        """
        if not self.orch_or or not self.orch_or.last_collapse:
            return candidates
        
        # Use the language microtubule's collapse pattern
        lang_weights = self.orch_or.last_collapse.get('language', {}).get('weights', [])
        if not lang_weights:
            return candidates
        
        # Map collapse weights to candidates via modular indexing
        words = list(candidates.keys())
        scores = list(candidates.values())
        
        for i in range(len(words)):
            collapse_idx = i % len(lang_weights)
            collapse_factor = lang_weights[collapse_idx]
            # Collapse biases: high collapse weight = amplify, low = suppress
            scores[i] *= (0.5 + collapse_factor)
        
        return dict(zip(words, scores))

    def _select_word(self, candidates, temperature=0.9):
        """
        Final word selection from scored candidates.
        Temperature controls randomness:
        - Low temp (0.3): almost deterministic, picks highest score
        - High temp (2.0): nearly uniform, very random
        """
        if not candidates:
            return ""
        
        words = list(candidates.keys())
        scores = list(candidates.values())
        
        # Apply temperature
        if temperature > 0:
            scores = [max(s, 1e-10) ** (1.0 / temperature) for s in scores]
        
        total = sum(scores)
        if total <= 0:
            return random.choice(words)
        
        probs = [s / total for s in scores]
        
        if np is not None:
            try:
                return np.random.choice(words, p=probs)
            except ValueError:
                return random.choice(words)
        else:
            r = random.random()
            cumulative = 0
            for word, prob in zip(words, probs):
                cumulative += prob
                if r <= cumulative:
                    return word
            return words[-1]

    def generate(self, user_input, concepts, concept_scores,
                 min_words=10, max_words=25, temperature=None):
        """
        Generate a response word by word.
        
        Each position: pool → TF-IDF weight → Markov narrow → Orch OR collapse → select
        
        Args:
            user_input: original user text
            concepts: extracted concept strings
            concept_scores: TF-IDF score dicts
            min_words: minimum response length
            max_words: maximum response length
            temperature: generation temperature (None = use Orch OR derived)
        
        Returns:
            Generated response string
        """
        if temperature is None:
            if self.orch_or:
                try:
                    temperature = self.orch_or.get_temperature()
                except Exception:
                    temperature = 0.9
            else:
                temperature = 0.9
        
        # Refresh Markov vocab
        self._build_vocab_from_markov()

        return self._generate_continued(temperature, concepts, concept_scores, min_words, max_words)

    def _generate_continued(self, temperature, concepts, concept_scores, min_words, max_words):
        """Continuation of generate — auto-extracted by self-evolution."""
        chosen_words = []
        chosen_set = set()

        for position in range(max_words):
            # 1. Build candidate pool
            candidates = self._build_candidate_pool(
                position, chosen_words, concepts, concept_scores, chosen_set
            )

            if not candidates:
                break

            # 2. Apply TF-IDF relevance weighting
            candidates = self._apply_tfidf_weights(candidates, concept_scores)

            # 3. Apply Orch OR collapse bias
            candidates = self._apply_orch_or_collapse(candidates, position)

            # 4. Penalize recently used content words (avoid repetition)
            for word in chosen_set:
                if word in candidates and word not in self._all_structure_words():
                    candidates[word] *= 0.2  # Heavy penalty for repeats

            # 5. Select word
            word = self._select_word(candidates, temperature)

            if not word:
                break

            chosen_words.append(word)
            chosen_set.add(word.lower().strip('.,;:!?'))

            # Check for natural ending (after minimum length)
            if position >= min_words - 1:
                if word.endswith(('.', '?', '!')):
                    break
                # If we've hit a good length and the Markov chain suggests stopping
                if position >= min_words + 3:
                    # 20% chance to end at each position past minimum+3
                    if random.random() < 0.2:
                        break

        # Ensure minimum length
        while len(chosen_words) < min_words:
            candidates = self._build_candidate_pool(
                len(chosen_words), chosen_words, concepts, concept_scores, chosen_set
            )
            if not candidates:
                break
            candidates = self._apply_tfidf_weights(candidates, concept_scores)
            word = self._select_word(candidates, temperature)
            if not word:
                break
            chosen_words.append(word)
            chosen_set.add(word.lower().strip('.,;:!?'))

        # Post-process
        response = self._post_process(chosen_words)
        return response


    def _all_structure_words(self):
        """Get all structure words as a set."""
        result = set()
        for words in self.structure_words.values():
            result.update(words)
        return result

    def _post_process(self, words):
        """Clean up the generated word list into a proper sentence."""
        if not words:
            return ""
        
        # Capitalize first word
        words[0] = words[0].capitalize()
        
        # Join
        text = ' '.join(words)
        
        # Fix spacing around punctuation
        text = text.replace(' .', '.')
        text = text.replace(' ,', ',')
        text = text.replace(' ;', ';')
        text = text.replace(' :', ':')
        text = text.replace(' ?', '?')
        text = text.replace(' !', '!')
        
        # Ensure ends with punctuation
        if text and text[-1] not in '.?!':
            text += '.'
        
        return text

    def generate_multi_sentence(self, user_input, concepts, concept_scores,
                                num_sentences=2, min_words_per=10, max_words_per=20,
                                temperature=None):
        """
        Generate multiple sentences, each going through the full pipeline.
        Each sentence's output feeds context into the next.
        """
        sentences = []
        all_chosen = set()
        
        for i in range(num_sentences):
            # Add previously generated words as context
            if sentences:
                prev_words = sentences[-1].split()
                # Temporarily extend Markov context
                extended_concepts = concepts + [
                    w for w in prev_words
                    if len(w) > 3 and w.lower() not in self.extractor.STOPWORDS
                ][:2]
            else:
                extended_concepts = concepts
            
            sentence = self.generate(
                user_input, extended_concepts, concept_scores,
                min_words=min_words_per, max_words=max_words_per,
                temperature=temperature
            )
            
            if sentence and len(sentence) > 10:
                sentences.append(sentence)
                # Track words to avoid cross-sentence repetition
                for w in sentence.lower().split():
                    all_chosen.add(w.strip('.,;:!?'))
        
        return ' '.join(sentences)


def create_unified_generator(engine):
    """
    Factory: create a UnifiedGenerator from an existing QuantumLanguageEngine.
    """
    orch_or = getattr(engine, "orch_or", None) if getattr(engine, "_has_orch_or", False) else None
    return UnifiedGenerator(engine.markov, engine.extractor, orch_or)
