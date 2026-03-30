"""
🧠 Hybrid Quantum Generator v3
================================
The right approach: grammar comes from Markov (full sentences).
Intelligence comes from the quantum pipeline (which sentence wins,
which words get swapped for better ones).

Pipeline per response:
1. Markov generates N candidate sentences (grammar guaranteed)
2. TF-IDF scores each for topical relevance
3. WordNet finds better synonyms for key content words
4. Orch OR collapses to pick the winning sentence + best swaps
5. Result: coherent grammar with quantum-selected word choices

This is how the brain works:
- You don't pick words one at a time in a vacuum
- You generate candidate phrasings in parallel
- The best one "wins" (collapses into speech)
- Sometimes a better word swaps in at the last moment
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
    from nltk.corpus import wordnet as wn
    wn.synsets('test')
    HAS_WORDNET = True
except Exception:
    HAS_WORDNET = False

logger = logging.getLogger("quantum_ai")


# Real quantum circuits available
try:
    from pennylane_quantum import get_pennylane_quantum
    _pennylane = get_pennylane_quantum()
    HAS_PENNYLANE = True
except Exception:
    _pennylane = None
    HAS_PENNYLANE = False

class HybridGenerator:
    """
    Generates responses by:
    1. Producing multiple Markov candidate sentences
    2. Scoring them with TF-IDF for topic relevance
    3. Enhancing the winner with WordNet synonym swaps
    4. Using Orch OR to drive all selection decisions
    """

    def __init__(self, markov, extractor, orch_or=None):
        self.markov = markov
        self.extractor = extractor
        self.orch_or = orch_or
        self._has_wordnet = HAS_WORDNET

        # Words that should never be swapped (grammar glue)
        self.no_swap = frozenset({
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'shall', 'of', 'to',
            'for', 'in', 'with', 'by', 'from', 'and', 'or', 'but', 'not',
            'no', 'if', 'then', 'than', 'that', 'this', 'these', 'those',
            'it', 'its', 'he', 'she', 'they', 'we', 'you', 'i', 'me',
            'my', 'his', 'her', 'our', 'your', 'their', 'at', 'on', 'as',
            'so', 'yet', 'nor', 'each', 'every', 'some', 'all', 'any',
        })

    def generate(self, user_input, concepts, concept_scores,
                 num_candidates=8, min_words=10, max_words=25,
                 temperature=None):
        """
        Full hybrid generation pipeline.

        1. Generate candidates via Markov
        2. Score with TF-IDF
        3. Pick winner via Orch OR or scoring
        4. Enhance with WordNet swaps
        5. Return the best response
        """
        if not self.markov.trained or not self.markov.starters:
            return "I need more training data to generate responses."

        if temperature is None:
            if self.orch_or:
                try:
                    temperature = self.orch_or.get_temperature()
                except Exception:
                    temperature = 0.9
            else:
                temperature = 0.9

        # Build topic relevance map
        topic_words = set()
        topic_boost = {}
        for cs in concept_scores:
            if isinstance(cs, dict):
                topic_words.add(cs['concept'])
                topic_boost[cs['concept']] = cs.get('score', 0.5)
        # Add WordNet relatives of concepts
        wordnet_relatives = self._get_concept_relatives(concepts)
        topic_words.update(wordnet_relatives.keys())

        # === STEP 1: Generate candidate sentences ===
        candidates = self._generate_candidates(
            concepts, topic_words, num_candidates, max_words, temperature
        )

        if not candidates:
            return "I need more training data on this topic."

        # === STEP 2: Score each candidate ===
        scored = []
        for sentence in candidates:
            score = self._score_sentence(sentence, topic_boost, topic_words, concepts)
            scored.append((sentence, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        return self._generate_continued(score, scored, sentence, temperature, topic_boost, topic_words, concepts, min_words, max_words)

    def _generate_continued(self, score, scored, sentence, temperature, topic_boost, topic_words, concepts, min_words, max_words):
        """Continuation of generate — auto-extracted by self-evolution."""
        # === STEP 3: Select winner via Orch OR or top score ===
        winner = self._select_winner(scored, temperature)

        # === STEP 4: Enhance with WordNet swaps ===
        enhanced = self._enhance_with_synonyms(
            winner, concepts, topic_words, topic_boost
        )

        # === STEP 5: Enforce minimum length ===
        words = enhanced.split()
        if len(words) < min_words:
            # Append another generated sentence
            extra = self._generate_candidates(
                concepts, topic_words, 4, max_words, temperature
            )
            if extra:
                extra_scored = [(s, self._score_sentence(s, topic_boost, topic_words, concepts))
                               for s in extra]
                extra_scored.sort(key=lambda x: x[1], reverse=True)
                enhanced = enhanced.rstrip('.?!') + '. ' + extra_scored[0][0]

        return enhanced


    def _generate_candidates(self, concepts, topic_words, n, max_words, temperature):
        """Generate N Markov candidate sentences, biased toward topic starters."""
        candidates = []
        seen_starts = set()

        return self.__generate_candidates_continued(candidates, seen_starts, concepts, topic_words, n, max_words, temperature)

    def __generate_candidates_continued(self, candidates, seen_starts, concepts, topic_words, n, max_words, temperature):
        """Continuation of _generate_candidates — auto-extracted by self-evolution."""
        # Sort starters by topic relevance
        starter_scores = []
        for starter in self.markov.starters:
            score = 0
            for word in starter:
                wl = word.lower().strip('.,;:!?')
                if wl in topic_words:
                    score += 2.0
                if wl in [c.lower() for c in concepts]:
                    score += 3.0
            score += random.random() * 0.5  # Variety factor
            starter_scores.append((starter, score))

        starter_scores.sort(key=lambda x: x[1], reverse=True)
        top_starters = [s for s, _ in starter_scores[:n * 3]]

        # Generate from top starters
        attempts = 0
        while len(candidates) < n and attempts < n * 5:
            attempts += 1

            if top_starters and random.random() < 0.7:
                # Use a topic-relevant starter
                starter = random.choice(top_starters[:max(3, len(top_starters) // 2)])
                seed = list(starter)
            else:
                # Random starter for variety
                seed = None

            sent = self.markov.generate(
                max_words=max_words,
                seed_words=seed,
                temperature=temperature
            )

            if not sent or len(sent) < 15:
                continue

            # Skip near-duplicates
            start_key = ' '.join(sent.split()[:3]).lower()
            if start_key in seen_starts:
                continue
            seen_starts.add(start_key)

            candidates.append(sent)

        return candidates


    def _score_sentence(self, sentence, topic_boost, topic_words, concepts):
        """
        Score a sentence for quality:
        - Topic relevance (TF-IDF concept overlap)
        - Perplexity (lower = more coherent under model)
        - Length (prefer 10-25 words)
        - Concept coverage (how many input concepts appear)
        """
        words = sentence.lower().split()
        word_set = set(w.strip('.,;:!?') for w in words)

        # Topic relevance: what fraction of content words are topic-related
        content_words = [w for w in word_set if len(w) > 3]
        if content_words:
            topic_overlap = sum(1 for w in content_words if w in topic_words)
            relevance = topic_overlap / len(content_words)
        else:
            relevance = 0

        # Concept coverage: how many input concepts appear
        concept_hits = sum(1 for c in concepts if c.lower() in word_set)
        coverage = concept_hits / max(len(concepts), 1)

        # Perplexity (invert — lower perplexity = higher score)
        perplexity = self.markov.get_perplexity(sentence)
        if perplexity < float('inf'):
            coherence = 1.0 / (1.0 + math.log(max(perplexity, 1)))
        else:
            coherence = 0.1

        # Length preference (sweet spot 10-20 words)
        n_words = len(words)
        if 10 <= n_words <= 20:
            length_score = 1.0
        elif n_words < 10:
            length_score = n_words / 10
        else:
            length_score = max(0.5, 1.0 - (n_words - 20) * 0.05)

        # Combined score
        score = (relevance * 0.35 +
                 coverage * 0.25 +
                 coherence * 0.25 +
                 length_score * 0.15)

        return score

    def _select_winner(self, scored_candidates, temperature):
        """
        Select winning sentence using Orch OR or temperature-weighted selection.
        """
        if not scored_candidates:
            return ""

        sentences = [s for s, _ in scored_candidates]
        scores = [sc for _, sc in scored_candidates]

        # Use Orch OR collapse weights if available
        if self.orch_or and getattr(self.orch_or, "last_collapse", None):
            lang_weights = getattr(self.orch_or, "last_collapse", None).get(
                'language', {}
            ).get('weights', [])
            if lang_weights:
                for i in range(len(scores)):
                    idx = i % len(lang_weights)
                    scores[i] *= (0.5 + lang_weights[idx])

        # Temperature-weighted selection
        if temperature > 0:
            scores = [max(s, 1e-10) ** (1.0 / temperature) for s in scores]

        total = sum(scores)
        if total <= 0:
            return sentences[0]

        probs = [s / total for s in scores]

        if np is not None:
            try:
                idx = np.random.choice(len(sentences), p=probs)
                return sentences[idx]
            except ValueError:
                return sentences[0]
        else:
            r = random.random()
            cumulative = 0
            for sent, prob in zip(sentences, probs):
                cumulative += prob
                if r <= cumulative:
                    return sent
            return sentences[0]

    def _get_concept_relatives(self, concepts, max_per=8):
        """Get WordNet relatives for input concepts."""
        relatives = {}
        if not self._has_wordnet:
            return relatives

        for concept in concepts[:4]:
            try:
                for syn in wn.synsets(concept)[:2]:
                    for lemma in syn.lemmas():
                        w = lemma.name().replace('_', ' ').lower()
                        if ' ' not in w and len(w) > 2 and w != concept:
                            relatives[w] = max(relatives.get(w, 0), 0.7)
                    for hyper in syn.hypernyms()[:2]:
                        for lemma in hyper.lemmas():
                            w = lemma.name().replace('_', ' ').lower()
                            if ' ' not in w and len(w) > 2:
                                relatives[w] = max(relatives.get(w, 0), 0.5)
            except Exception:
                pass

        return dict(sorted(relatives.items(), key=lambda x: x[1], reverse=True)[:max_per * len(concepts)])

    def _enhance_with_synonyms(self, sentence, concepts, topic_words, topic_boost):
        """
        Replace 1-2 content words with better synonyms from WordNet.
        Only swaps if the synonym is more topic-relevant AND Markov knows it.
        """
        if not self._has_wordnet:
            return sentence

        words = sentence.split()
        if len(words) < 5:
            return sentence

        # Find swappable positions (content words, not grammar glue)
        swappable = []
        for i, word in enumerate(words):
            clean = word.lower().strip('.,;:!?')
            if (len(clean) > 3 and
                clean not in self.no_swap and
                clean not in [c.lower() for c in concepts]):  # Don't swap the actual concepts
                swappable.append(i)

        if not swappable:
            return sentence

        # Try swapping 1-2 words
        swaps_made = 0
        random.shuffle(swappable)

        return self.__enhance_with_synonyms_continued(clean, swappable, swaps_made, words, topic_words, topic_boost)

    def __enhance_with_synonyms_continued(self, clean, swappable, swaps_made, words, topic_words, topic_boost):
        """Continuation of _enhance_with_synonyms — auto-extracted by self-evolution."""
        for pos in swappable[:3]:  # Try up to 3 positions
            if swaps_made >= 2:
                break

            original = words[pos]
            clean = original.lower().strip('.,;:!?')
            punct = original[len(clean):] if len(original) > len(clean) else ''

            # Get synonyms
            try:
                synonyms = set()
                for syn in wn.synsets(clean)[:2]:
                    for lemma in syn.lemmas():
                        s = lemma.name().replace('_', ' ').lower()
                        if ' ' not in s and s != clean and len(s) > 2:
                            synonyms.add(s)
            except Exception:
                continue

            if not synonyms:
                continue

            # Score each synonym
            best_syn = None
            best_score = 0

            for syn in synonyms:
                score = 0
                # Must be in Markov vocabulary
                markov_vocab = set()
                for prefix in self.markov.chain.keys():
                    for w in prefix:
                        markov_vocab.add(w.lower().strip('.,;:!?'))
                for suffixes in self.markov.chain.values():
                    for w in suffixes:
                        markov_vocab.add(w.lower().strip('.,;:!?'))

                if syn not in markov_vocab:
                    continue

                # Topic relevance boost
                if syn in topic_words:
                    score += 2.0
                if syn in topic_boost:
                    score += topic_boost[syn]

                # Prefer words the original doesn't already cover
                if score > best_score:
                    best_score = score
                    best_syn = syn

            # Only swap if the synonym is actually better
            original_topic = 1.0 if clean in topic_words else 0.0
            if best_syn and best_score > original_topic + 0.5:
                # Preserve capitalization
                if original[0].isupper():
                    best_syn = best_syn.capitalize()
                words[pos] = best_syn + punct
                swaps_made += 1

        return ' '.join(words)


    def generate_multi(self, user_input, concepts, concept_scores,
                       num_sentences=2, min_words=10, max_words=20,
                       temperature=None):
        """Generate multiple sentences with cross-sentence coherence."""
        sentences = []

        for i in range(num_sentences):
            # Add previous output concepts as additional context
            if sentences:
                prev_words = sentences[-1].lower().split()
                extra_concepts = [w.strip('.,;:!?') for w in prev_words
                                 if len(w) > 4 and w.strip('.,;:!?') not in self.extractor.STOPWORDS][:2]
                round_concepts = concepts + extra_concepts
            else:
                round_concepts = concepts

            sent = self.generate(
                user_input, round_concepts, concept_scores,
                num_candidates=8, min_words=min_words, max_words=max_words,
                temperature=temperature
            )

            if sent and len(sent) > 15:
                # Avoid starting consecutive sentences the same way
                if sentences:
                    prev_start = ' '.join(sentences[-1].split()[:2]).lower()
                    new_start = ' '.join(sent.split()[:2]).lower()
                    if new_start == prev_start:
                        # Regenerate with higher temperature
                        sent = self.generate(
                            user_input, round_concepts, concept_scores,
                            num_candidates=6, min_words=min_words, max_words=max_words,
                            temperature=(temperature or 0.9) + 0.3
                        )

                sentences.append(sent)

        return ' '.join(sentences)


def create_hybrid_generator(engine):
    """Factory: create HybridGenerator from existing engine."""
    orch_or = getattr(engine, "orch_or", None) if getattr(engine, "_has_orch_or", False) else None
    return HybridGenerator(engine.markov, engine.extractor, orch_or)
