"""
Tests for algorithmic_core.py — MarkovTextGenerator, TFIDF, PMI, BM25,
EntropyDecider, HebbianMemory, Attention.
"""

import math
import random
import pytest

from algorithmic_core import (
    MarkovTextGenerator,
    TFIDF,
    PMI,
    BM25,
    EntropyDecider,
    HebbianMemory,
    Attention,
)


# ============================================================================
# MarkovTextGenerator
# ============================================================================


class TestMarkovTextGenerator:
    """Tests for the Markov chain text generator."""

    def setup_method(self):
        self.gen = MarkovTextGenerator(max_order=3)

    # -- tokenizer --
    def test_tokenize_basic(self):
        tokens = self.gen._tokenize("Hello world, how are you?")
        assert "hello" in tokens
        assert "world," in tokens
        assert "you?" in tokens

    def test_tokenize_empty(self):
        assert self.gen._tokenize("") == []

    def test_tokenize_lowercases(self):
        tokens = self.gen._tokenize("HELLO World")
        assert all(t == t.lower() for t in tokens)

    # -- sentence splitting --
    def test_split_sentences(self):
        text = "First sentence. Second one! Third?"
        sentences = self.gen._split_sentences(text)
        assert len(sentences) == 3

    def test_split_sentences_short_filtered(self):
        text = "Hi. This is a longer sentence."
        sentences = self.gen._split_sentences(text)
        # "Hi" is <=5 chars and should be filtered
        assert all(len(s) > 5 for s in sentences)

    # -- formatting --
    def test_format_output_empty(self):
        assert self.gen._format_output([]) == ""

    def test_format_output_capitalizes(self):
        result = self.gen._format_output(["hello", "world"])
        assert result[0] == "H"

    def test_format_output_adds_period(self):
        result = self.gen._format_output(["hello", "world"])
        assert result.endswith(".")

    def test_format_output_keeps_existing_punctuation(self):
        result = self.gen._format_output(["hello", "world!"])
        assert result.endswith("!")
        assert not result.endswith("!.")

    # -- clean_text --
    def test_clean_text_removes_shell_prompts(self):
        text = "$ pip install numpy\nSome real content here."
        cleaned = MarkovTextGenerator._clean_text(text)
        assert "pip install numpy" not in cleaned
        assert "Some real content here." in cleaned

    def test_clean_text_removes_python_repl(self):
        text = ">>> print('hello')\nNormal text here."
        cleaned = MarkovTextGenerator._clean_text(text)
        assert "print('hello')" not in cleaned
        assert "Normal text here." in cleaned

    def test_clean_text_keeps_normal_text(self):
        text = "Consciousness is a fundamental mystery of existence."
        assert MarkovTextGenerator._clean_text(text) == text

    def test_clean_text_removes_decoration_lines(self):
        text = "=====\nContent\n-----"
        cleaned = MarkovTextGenerator._clean_text(text)
        assert "=====" not in cleaned
        assert "Content" in cleaned

    # -- training and stats --
    def test_train_updates_vocabulary(self):
        self.gen.train("The quick brown fox jumps over the lazy dog.")
        stats = self.gen.get_stats()
        assert stats["vocabulary_size"] > 0
        assert stats["total_tokens"] > 0

    def test_train_builds_chains(self):
        self.gen.train("Quantum consciousness emerges from microtubule collapse.")
        stats = self.gen.get_stats()
        # At least order-1 chain should have entries
        assert stats["chain_sizes"][1] > 0

    def test_get_stats_structure(self):
        stats = self.gen.get_stats()
        assert "vocabulary_size" in stats
        assert "total_tokens" in stats
        assert "chain_sizes" in stats
        assert "starter_counts" in stats

    # -- generation --
    def test_generate_empty_untrained(self):
        result = self.gen.generate()
        assert result == ""

    def test_generate_produces_text(self):
        corpus = (
            "The nature of consciousness remains a deep mystery. "
            "Consciousness emerges from quantum processes in microtubules. "
            "Microtubules are protein structures inside neurons. "
            "Neurons fire together and wire together through Hebbian learning."
        )
        self.gen.train(corpus)
        random.seed(42)
        result = self.gen.generate(max_words=20)
        assert len(result) > 0

    def test_generate_respects_max_words(self):
        corpus = "Word one two three four five six seven eight nine ten. " * 10
        self.gen.train(corpus)
        random.seed(42)
        result = self.gen.generate(max_words=10)
        # Result should not vastly exceed max_words (prefix + generated)
        word_count = len(result.split())
        assert word_count <= 20  # generous bound: prefix + max_words

    def test_generate_with_seed(self):
        corpus = "Quantum mechanics describes the behavior of particles at small scales."
        self.gen.train(corpus)
        random.seed(42)
        result = self.gen.generate(seed=["quantum"])
        assert len(result) > 0


# ============================================================================
# TFIDF
# ============================================================================


class TestTFIDF:
    """Tests for TF-IDF keyword extraction and similarity."""

    def setup_method(self):
        self.tfidf = TFIDF()

    def test_tokenize_lowercases(self):
        tokens = self.tfidf._tokenize("Hello World")
        assert all(t.islower() for t in tokens)

    def test_tokenize_filters_single_char(self):
        tokens = self.tfidf._tokenize("I a am the cat")
        # 'I' and 'a' are single char, should be filtered (min 2 chars)
        assert "i" not in tokens
        assert "a" not in tokens

    def test_add_document_increments_count(self):
        self.tfidf.add_document("test document")
        assert self.tfidf.doc_count == 1
        self.tfidf.add_document("another document")
        assert self.tfidf.doc_count == 2

    def test_extract_keywords_empty(self):
        result = self.tfidf.extract_keywords("")
        assert result == []

    def test_extract_keywords_filters_stopwords(self):
        self.tfidf.add_document("quantum consciousness reality")
        keywords = self.tfidf.extract_keywords("the and or quantum consciousness")
        keyword_terms = [k for k, _ in keywords]
        assert "the" not in keyword_terms
        assert "and" not in keyword_terms

    def test_extract_keywords_returns_top_n(self):
        text = "quantum consciousness reality emergence complexity information entropy"
        self.tfidf.add_document(text)
        keywords = self.tfidf.extract_keywords(text, top_n=3)
        assert len(keywords) <= 3

    def test_extract_keywords_returns_scores(self):
        self.tfidf.add_document("quantum physics experiment")
        keywords = self.tfidf.extract_keywords("quantum physics experiment")
        for term, score in keywords:
            assert isinstance(score, float)
            assert score > 0

    def test_similarity_identical_texts(self):
        text = "quantum consciousness reality"
        self.tfidf.add_document(text)
        sim = self.tfidf.similarity(text, text)
        assert sim == pytest.approx(1.0, abs=0.01)

    def test_similarity_empty_texts(self):
        sim = self.tfidf.similarity("", "")
        assert sim == 0.0

    def test_similarity_different_texts(self):
        self.tfidf.add_document("quantum physics experiment observation")
        self.tfidf.add_document("cooking recipe ingredient kitchen")
        sim = self.tfidf.similarity(
            "quantum physics experiment",
            "cooking recipe ingredient"
        )
        # Should be low since topics are different
        assert sim < 0.5

    def test_similarity_related_texts(self):
        self.tfidf.add_document("quantum physics particle wave")
        sim = self.tfidf.similarity(
            "quantum physics particle experiment",
            "quantum physics wave observation"
        )
        # Should be moderate to high since they share terms
        assert sim > 0.0

    def test_idf_boost_for_rare_terms(self):
        # Add many docs with "common" but few with "rare"
        for _ in range(10):
            self.tfidf.add_document("common word repeated frequently")
        self.tfidf.add_document("rare unique special")

        kw_common = dict(self.tfidf.extract_keywords("common frequent"))
        kw_rare = dict(self.tfidf.extract_keywords("rare unique"))
        # Rare terms should get higher IDF
        if "rare" in kw_rare and "common" in kw_common:
            assert kw_rare.get("rare", 0) > kw_common.get("common", 0)


# ============================================================================
# PMI
# ============================================================================


class TestPMI:
    """Tests for Pointwise Mutual Information."""

    def setup_method(self):
        self.pmi = PMI(window=5)

    def test_score_untrained(self):
        assert self.pmi.score("word1", "word2") == 0.0

    def test_train_updates_counts(self):
        self.pmi.train("the quick brown fox jumps over the lazy dog")
        assert self.pmi.total_words > 0
        assert self.pmi.total_pairs > 0

    def test_score_cooccurring_words(self):
        # Train on text where "quantum" and "consciousness" co-occur
        text = "quantum consciousness " * 20
        self.pmi.train(text)
        score = self.pmi.score("quantum", "consciousness")
        assert score != 0.0

    def test_score_case_insensitive(self):
        self.pmi.train("Quantum Consciousness quantum consciousness")
        s1 = self.pmi.score("quantum", "consciousness")
        s2 = self.pmi.score("Quantum", "Consciousness")
        assert s1 == s2

    def test_coherence_single_word(self):
        assert self.pmi.coherence("word") == 0.0

    def test_coherence_trained_text(self):
        corpus = "the cat sat on the mat. the cat sat on the mat."
        self.pmi.train(corpus)
        score = self.pmi.coherence("the cat sat")
        # Should return a number (could be positive or negative)
        assert isinstance(score, float)

    def test_related_words_empty(self):
        result = self.pmi.related_words("nonexistent")
        assert result == []

    def test_related_words_trained(self):
        self.pmi.train("quantum physics particle wave energy matter field force")
        related = self.pmi.related_words("quantum", top_n=3)
        assert len(related) <= 3
        for word, score in related:
            assert isinstance(word, str)
            assert isinstance(score, float)

    def test_symmetric_scoring(self):
        self.pmi.train("alpha beta gamma alpha beta gamma")
        s1 = self.pmi.score("alpha", "beta")
        s2 = self.pmi.score("beta", "alpha")
        assert s1 == s2


# ============================================================================
# BM25
# ============================================================================


class TestBM25:
    """Tests for BM25 information retrieval."""

    def setup_method(self):
        self.bm25 = BM25()

    def test_empty_search(self):
        results = self.bm25.search("anything")
        assert results == []

    def test_add_document(self):
        self.bm25.add_document("doc1", "quantum physics experiment")
        assert len(self.bm25.documents) == 1

    def test_add_document_updates_avg_len(self):
        self.bm25.add_document("doc1", "one two three")
        self.bm25.add_document("doc2", "one two three four five six")
        assert self.bm25.avg_doc_len > 0

    def test_search_finds_relevant(self):
        self.bm25.add_document("doc1", "quantum physics particle experiment")
        self.bm25.add_document("doc2", "cooking recipe kitchen food")
        self.bm25.add_document("doc3", "quantum mechanics wave function")

        results = self.bm25.search("quantum physics")
        assert len(results) > 0
        # The quantum-related docs should rank higher
        doc_ids = [r[0] for r in results]
        assert "doc1" in doc_ids

    def test_search_respects_top_k(self):
        for i in range(10):
            self.bm25.add_document(f"doc{i}", f"word{i} quantum physics")
        results = self.bm25.search("quantum", top_k=3)
        assert len(results) <= 3

    def test_search_returns_scores(self):
        self.bm25.add_document("doc1", "quantum physics")
        results = self.bm25.search("quantum")
        for doc_id, score, metadata in results:
            assert isinstance(score, float)
            assert score > 0

    def test_search_with_metadata(self):
        self.bm25.add_document("doc1", "quantum physics", metadata={"source": "test"})
        results = self.bm25.search("quantum")
        assert results[0][2] == {"source": "test"}

    def test_search_unmatched_query(self):
        self.bm25.add_document("doc1", "quantum physics")
        results = self.bm25.search("cooking recipes baking")
        assert results == []

    def test_bm25_ranking_order(self):
        # Document with more query term occurrences should rank higher
        self.bm25.add_document("doc1", "quantum")
        self.bm25.add_document("doc2", "quantum quantum quantum physics")
        results = self.bm25.search("quantum")
        assert results[0][0] == "doc2"


# ============================================================================
# EntropyDecider
# ============================================================================


class TestEntropyDecider:
    """Tests for entropy-based decision making."""

    def test_entropy_uniform(self):
        # Maximum entropy for uniform distribution
        probs = [0.25, 0.25, 0.25, 0.25]
        H = EntropyDecider.entropy(probs)
        assert H == pytest.approx(2.0, abs=0.001)

    def test_entropy_certain(self):
        # Zero entropy for certain outcome
        probs = [1.0]
        H = EntropyDecider.entropy(probs)
        assert H == pytest.approx(0.0, abs=0.001)

    def test_entropy_binary(self):
        # Binary entropy: -0.5*log2(0.5) - 0.5*log2(0.5) = 1.0
        probs = [0.5, 0.5]
        H = EntropyDecider.entropy(probs)
        assert H == pytest.approx(1.0, abs=0.001)

    def test_entropy_handles_zero(self):
        # Zero probabilities should be skipped
        probs = [0.5, 0.0, 0.5]
        H = EntropyDecider.entropy(probs)
        assert H == pytest.approx(1.0, abs=0.001)

    def test_select_by_entropy_empty(self):
        assert EntropyDecider.select_by_entropy([]) == ""

    def test_select_by_entropy_single(self):
        result = EntropyDecider.select_by_entropy([("only", 1.0)])
        assert result == "only"

    def test_select_by_entropy_returns_string(self):
        candidates = [("option_a", 0.8), ("option_b", 0.5), ("option_c", 0.3)]
        random.seed(42)
        result = EntropyDecider.select_by_entropy(candidates, target_entropy=0.5)
        assert result in ["option_a", "option_b", "option_c"]

    def test_information_gain(self):
        before = {"a": 0.5, "b": 0.5}
        after = {"a": 0.9, "b": 0.1}
        gain = EntropyDecider.information_gain(before, after)
        # Entropy should decrease (more certain), so gain > 0
        assert gain > 0

    def test_information_gain_empty(self):
        assert EntropyDecider.information_gain({}, {}) == 0.0

    def test_information_gain_no_change(self):
        dist = {"a": 0.5, "b": 0.5}
        gain = EntropyDecider.information_gain(dist, dist)
        assert gain == pytest.approx(0.0, abs=0.001)


# ============================================================================
# HebbianMemory
# ============================================================================


class TestHebbianMemory:
    """Tests for Hebbian associative learning."""

    def setup_method(self):
        self.hebb = HebbianMemory(learning_rate=0.1, decay=0.01)

    def test_initial_association_zero(self):
        assert self.hebb.get_association("a", "b") == 0.0

    def test_activate_strengthens(self):
        self.hebb.activate(["quantum", "consciousness"])
        assoc = self.hebb.get_association("quantum", "consciousness")
        assert assoc > 0.0

    def test_activate_symmetric(self):
        self.hebb.activate(["alpha", "beta"])
        a1 = self.hebb.get_association("alpha", "beta")
        a2 = self.hebb.get_association("beta", "alpha")
        assert a1 == a2

    def test_repeated_activation_grows(self):
        self.hebb.activate(["quantum", "consciousness"])
        first = self.hebb.get_association("quantum", "consciousness")
        self.hebb.activate(["quantum", "consciousness"])
        second = self.hebb.get_association("quantum", "consciousness")
        assert second > first

    def test_activate_multiple_concepts(self):
        self.hebb.activate(["a", "b", "c"])
        # All pairs should be connected
        assert self.hebb.get_association("a", "b") > 0
        assert self.hebb.get_association("a", "c") > 0
        assert self.hebb.get_association("b", "c") > 0

    def test_get_associated_empty(self):
        result = self.hebb.get_associated("nonexistent")
        assert result == []

    def test_get_associated_returns_sorted(self):
        self.hebb.activate(["center", "strong"])
        self.hebb.activate(["center", "strong"])
        self.hebb.activate(["center", "weak"])
        result = self.hebb.get_associated("center")
        if len(result) >= 2:
            assert result[0][1] >= result[1][1]

    def test_decay_reduces_weights(self):
        self.hebb.activate(["a", "b"])
        before = self.hebb.get_association("a", "b")
        self.hebb.decay_all()
        after = self.hebb.get_association("a", "b")
        assert after < before

    def test_decay_prunes_small_weights(self):
        self.hebb.activate(["x", "y"])
        # Decay many times until pruned
        for _ in range(1000):
            self.hebb.decay_all()
        assert self.hebb.get_association("x", "y") == 0.0

    def test_case_insensitive(self):
        self.hebb.activate(["Quantum", "Physics"])
        assert self.hebb.get_association("quantum", "physics") > 0

    def test_activation_counter(self):
        self.hebb.activate(["test"])
        self.hebb.activate(["test"])
        assert self.hebb.activations["test"] == 2


# ============================================================================
# Attention
# ============================================================================


class TestAttention:
    """Tests for the attention mechanism."""

    def test_softmax_empty(self):
        assert Attention.softmax([]) == []

    def test_softmax_sums_to_one(self):
        result = Attention.softmax([1.0, 2.0, 3.0])
        assert sum(result) == pytest.approx(1.0, abs=0.001)

    def test_softmax_all_equal(self):
        result = Attention.softmax([1.0, 1.0, 1.0])
        for v in result:
            assert v == pytest.approx(1.0 / 3.0, abs=0.001)

    def test_softmax_largest_gets_most(self):
        result = Attention.softmax([1.0, 5.0, 2.0])
        assert result[1] > result[0]
        assert result[1] > result[2]

    def test_softmax_numerical_stability(self):
        # Large values shouldn't cause overflow
        result = Attention.softmax([1000, 1001, 1002])
        assert sum(result) == pytest.approx(1.0, abs=0.001)

    def test_attend_empty_contexts(self):
        tfidf = TFIDF()
        result = Attention.attend("query", [], tfidf)
        assert result == []

    def test_attend_returns_weights(self):
        tfidf = TFIDF()
        tfidf.add_document("quantum physics")
        tfidf.add_document("cooking recipe")
        contexts = ["quantum physics experiment", "cooking recipe ingredient"]
        result = Attention.attend("quantum", contexts, tfidf)
        assert len(result) == 2
        weights = [w for _, w in result]
        assert sum(weights) == pytest.approx(1.0, abs=0.001)

    def test_weighted_combine_empty(self):
        tfidf = TFIDF()
        assert Attention.weighted_combine([], tfidf) == ""

    def test_weighted_combine_returns_keywords(self):
        tfidf = TFIDF()
        tfidf.add_document("quantum physics particle wave")
        items = [("quantum physics particle", 0.7), ("wave function collapse", 0.3)]
        result = Attention.weighted_combine(items, tfidf)
        assert isinstance(result, str)
