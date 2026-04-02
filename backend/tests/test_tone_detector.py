"""
Tests for tone_detector.py — VADER sentiment and register classification.
"""

import pytest

from tone_detector import detect_tone, DEEP_MARKERS, QUESTION_WORDS


class TestDetectTone:
    """Tests for the tone detection function."""

    def test_returns_dict(self):
        result = detect_tone("hello")
        assert isinstance(result, dict)

    def test_required_keys(self):
        result = detect_tone("hello world")
        assert "register" in result
        assert "depth" in result
        assert "sentiment" in result
        assert "deep_markers" in result
        assert "word_count" in result

    def test_casual_greeting(self):
        result = detect_tone("hello")
        assert result["register"] == "casual"
        assert result["depth"] < 0.15

    def test_casual_short_text(self):
        result = detect_tone("hey what's up")
        assert result["register"] == "casual"

    def test_philosophical_deep_topic(self):
        result = detect_tone(
            "what is the nature of consciousness and how does quantum "
            "collapse relate to subjective experience?"
        )
        assert result["register"] == "philosophical"
        assert result["depth"] >= 0.65

    def test_analytical_moderate_depth(self):
        result = detect_tone(
            "can you explain how microtubules work in quantum consciousness?"
        )
        # Should be analytical or philosophical (moderate to high depth)
        assert result["register"] in ("analytical", "philosophical")
        assert result["depth"] >= 0.35

    def test_deep_markers_counted(self):
        result = detect_tone("quantum consciousness reality existence")
        assert result["deep_markers"] >= 3

    def test_no_deep_markers(self):
        result = detect_tone("hello there friend")
        assert result["deep_markers"] == 0

    def test_word_count_accurate(self):
        result = detect_tone("one two three four five")
        assert result["word_count"] == 5

    def test_depth_clamped_to_one(self):
        # Pack many deep markers to try to exceed 1.0
        markers = list(DEEP_MARKERS)[:15]
        text = " ".join(markers) + "? " * 5
        result = detect_tone(text)
        assert result["depth"] <= 1.0

    def test_depth_non_negative(self):
        result = detect_tone("")
        assert result["depth"] >= 0.0

    def test_question_mark_detection(self):
        """Questions about deep topics should boost depth."""
        without_q = detect_tone("consciousness reality")
        with_q = detect_tone("consciousness reality?")
        assert with_q["depth"] >= without_q["depth"]

    def test_longer_text_higher_depth(self):
        short = detect_tone("consciousness")
        long_text = "consciousness " + " ".join(["word"] * 25)
        long_result = detect_tone(long_text)
        assert long_result["depth"] >= short["depth"]

    def test_multiple_sentences_boost(self):
        """Multiple sentences suggest analytical thinking."""
        single = detect_tone("consciousness is mysterious")
        multi = detect_tone("consciousness is mysterious. reality is quantum. existence is puzzling.")
        assert multi["depth"] >= single["depth"]

    def test_register_values(self):
        """Register should be one of the four valid values."""
        for text in ["hi", "how are you doing today", "explain quantum mechanics",
                     "what is consciousness and how does quantum collapse relate?"]:
            result = detect_tone(text)
            assert result["register"] in ("casual", "conversational", "analytical", "philosophical")

    def test_depth_rounded(self):
        result = detect_tone("quantum consciousness reality")
        # Depth should be rounded to 3 decimal places
        depth_str = str(result["depth"])
        if "." in depth_str:
            decimals = len(depth_str.split(".")[1])
            assert decimals <= 3


class TestToneConstants:
    """Tests for module-level constants."""

    def test_deep_markers_is_set(self):
        assert isinstance(DEEP_MARKERS, set)
        assert len(DEEP_MARKERS) > 20

    def test_deep_markers_lowercase(self):
        for marker in DEEP_MARKERS:
            assert marker == marker.lower()

    def test_question_words_is_set(self):
        assert isinstance(QUESTION_WORDS, set)
        assert "what" in QUESTION_WORDS
        assert "why" in QUESTION_WORDS
        assert "how" in QUESTION_WORDS
