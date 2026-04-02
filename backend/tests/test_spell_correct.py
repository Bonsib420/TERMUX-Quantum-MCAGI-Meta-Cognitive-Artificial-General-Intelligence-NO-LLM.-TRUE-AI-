"""
Tests for spell_correct.py — Levenshtein distance and spell correction.
"""

import pytest

from spell_correct import levenshtein, build_corrector, correct_word, correct_text


class TestLevenshtein:
    """Tests for Levenshtein edit distance."""

    def test_identical_strings(self):
        assert levenshtein("hello", "hello") == 0

    def test_empty_strings(self):
        assert levenshtein("", "") == 0

    def test_one_empty(self):
        assert levenshtein("hello", "") == 5
        assert levenshtein("", "hello") == 5

    def test_single_insertion(self):
        assert levenshtein("cat", "cats") == 1

    def test_single_deletion(self):
        assert levenshtein("cats", "cat") == 1

    def test_single_substitution(self):
        assert levenshtein("cat", "bat") == 1

    def test_symmetric(self):
        assert levenshtein("abc", "xyz") == levenshtein("xyz", "abc")

    def test_known_distance(self):
        assert levenshtein("kitten", "sitting") == 3

    def test_single_char(self):
        assert levenshtein("a", "b") == 1
        assert levenshtein("a", "a") == 0


class TestBuildCorrector:
    """Tests for vocabulary builder."""

    def test_filters_short_words(self):
        markov = {"a": 1, "an": 1, "the": 1, "quantum": 1}
        vocab = build_corrector(markov)
        assert "a" not in vocab
        assert "an" not in vocab
        assert "the" in vocab
        assert "quantum" in vocab

    def test_filters_non_alpha(self):
        markov = {"hello": 1, "world!": 1, "123": 1}
        vocab = build_corrector(markov)
        assert "hello" in vocab
        assert "world!" not in vocab
        assert "123" not in vocab

    def test_empty_chain(self):
        assert build_corrector({}) == set()


class TestCorrectWord:
    """Tests for single word correction."""

    def setup_method(self):
        self.vocab = {
            "consciousness", "quantum", "reality", "perceive",
            "superposition", "experience", "existence", "spacetime",
        }

    def test_correct_word_already_correct(self):
        assert correct_word("quantum", self.vocab) == "quantum"

    def test_short_word_unchanged(self):
        assert correct_word("hi", self.vocab) == "hi"

    def test_non_alpha_unchanged(self):
        assert correct_word("123abc", self.vocab) == "123abc"

    def test_corrects_typo(self):
        result = correct_word("quantm", self.vocab)
        assert result == "quantum"

    def test_corrects_consciousness_typo(self):
        result = correct_word("consciousnes", self.vocab)
        assert result == "consciousness"

    def test_no_match_returns_original(self):
        result = correct_word("zzzzzzzzz", self.vocab)
        assert result == "zzzzzzzzz"

    def test_respects_max_dist(self):
        result = correct_word("quantm", self.vocab, max_dist=1)
        assert result == "quantum"

    def test_first_letter_must_match(self):
        # "bonsciousness" starts with 'b', won't match "consciousness"
        result = correct_word("bonsciousness", self.vocab)
        assert result == "bonsciousness"


class TestCorrectText:
    """Tests for full text correction."""

    def setup_method(self):
        self.vocab = {
            "consciousness", "quantum", "reality", "perceive",
            "superposition", "experience",
        }

    def test_correct_text_no_changes(self):
        text = "quantum consciousness reality"
        corrected, fixes = correct_text(text, self.vocab)
        assert corrected == text
        assert fixes == []

    def test_correct_text_with_fix(self):
        text = "quantm consciousnes"
        corrected, fixes = correct_text(text, self.vocab)
        assert "quantum" in corrected
        assert len(fixes) > 0

    def test_correct_text_preserves_punctuation(self):
        text = "quantm, hello!"
        corrected, _ = correct_text(text, self.vocab)
        # Punctuation should be preserved around corrected words
        assert "," in corrected

    def test_fixes_list_tracks_changes(self):
        text = "quantm"
        _, fixes = correct_text(text, self.vocab)
        assert len(fixes) == 1
        assert fixes[0] == ("quantm", "quantum")
