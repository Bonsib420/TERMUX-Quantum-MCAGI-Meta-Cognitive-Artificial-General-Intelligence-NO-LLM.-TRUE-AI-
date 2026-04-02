"""
Tests for text_analyzer.py — Human vs LLM text analysis.
"""

import pytest

from text_analyzer import TextAnalyzer, get_text_analyzer


class TestTextAnalyzerInit:
    """Tests for TextAnalyzer initialization."""

    def test_llm_phrases_loaded(self):
        analyzer = TextAnalyzer()
        assert isinstance(analyzer.llm_phrases, list)
        assert len(analyzer.llm_phrases) > 0

    def test_human_phrases_loaded(self):
        analyzer = TextAnalyzer()
        assert isinstance(analyzer.human_phrases, list)
        assert len(analyzer.human_phrases) > 0

    def test_llm_patterns_loaded(self):
        analyzer = TextAnalyzer()
        assert isinstance(analyzer.llm_patterns, list)
        assert len(analyzer.llm_patterns) > 0


class TestTextAnalyzerAnalyze:
    """Tests for the analyze method."""

    def setup_method(self):
        self.analyzer = TextAnalyzer()

    def test_returns_dict(self):
        result = self.analyzer.analyze("Hello world")
        assert isinstance(result, dict)

    def test_required_keys(self):
        result = self.analyzer.analyze("Hello world")
        expected_keys = {
            "text_length", "word_count", "sentence_count",
            "llm_score", "human_score", "indicators", "verdict", "confidence",
        }
        assert expected_keys.issubset(set(result.keys()))

    def test_word_count(self):
        result = self.analyzer.analyze("one two three four five")
        assert result["word_count"] == 5

    def test_sentence_count(self):
        result = self.analyzer.analyze("First sentence. Second one! Third?")
        assert result["sentence_count"] == 3

    def test_llm_text_detected(self):
        llm_text = (
            "Certainly! That's a great question! Let me break this down for you. "
            "Firstly, it's important to note that consciousness is complex. "
            "Secondly, I'd be happy to help you understand. "
            "I hope this helps! Feel free to ask more."
        )
        result = self.analyzer.analyze(llm_text)
        assert result["llm_score"] > result["human_score"]

    def test_human_text_detected(self):
        human_text = (
            "honestly idk what consciousness even is. like, basically it's "
            "kinda weird right? i mean, you know... hmm. anyway so yeah."
        )
        result = self.analyzer.analyze(human_text)
        assert result["human_score"] > result["llm_score"]

    def test_scores_sum_to_one(self):
        result = self.analyzer.analyze("Some normal text here")
        total = result["llm_score"] + result["human_score"]
        assert total == pytest.approx(1.0, abs=0.01)

    def test_verdict_values(self):
        result = self.analyzer.analyze("Some text here")
        assert result["verdict"] in ("Likely Human", "Likely LLM", "Uncertain")

    def test_confidence_range(self):
        result = self.analyzer.analyze("Some text here")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_llm_indicators_populated(self):
        llm_text = "Certainly! That's a great question! It's important to note this."
        result = self.analyzer.analyze(llm_text)
        assert len(result["indicators"]["llm"]) > 0

    def test_human_indicators_populated(self):
        human_text = "honestly i mean kinda like tbh you know"
        result = self.analyzer.analyze(human_text)
        assert len(result["indicators"]["human"]) > 0

    def test_empty_text(self):
        result = self.analyzer.analyze("")
        assert result["word_count"] == 0

    def test_neutral_text(self):
        """Neutral text should have scores that sum to 1."""
        result = self.analyzer.analyze("The sky is blue today.")
        assert result["llm_score"] + result["human_score"] == pytest.approx(1.0, abs=0.01)


class TestTextAnalyzerSuggestions:
    """Tests for improvement suggestions."""

    def setup_method(self):
        self.analyzer = TextAnalyzer()

    def test_returns_list(self):
        suggestions = self.analyzer.get_improvement_suggestions("Some text")
        assert isinstance(suggestions, list)

    def test_max_five_suggestions(self):
        llm_text = (
            "Certainly! Absolutely! Great question! "
            "It's important to note that this is worth noting! "
            "Firstly, secondly, thirdly, furthermore, moreover."
        )
        suggestions = self.analyzer.get_improvement_suggestions(llm_text)
        assert len(suggestions) <= 5

    def test_llm_text_gets_suggestions(self):
        llm_text = (
            "Certainly! That's a great question! Let me break this down. "
            "Firstly, it's important to note this. I hope this helps!"
        )
        suggestions = self.analyzer.get_improvement_suggestions(llm_text)
        assert len(suggestions) > 0


class TestTextAnalyzerMakeHuman:
    """Tests for the make_more_human transformation."""

    def setup_method(self):
        self.analyzer = TextAnalyzer()

    def test_contracts_formal_phrases(self):
        text = "I am thinking that I have found the answer."
        result = self.analyzer.make_more_human(text)
        assert "I'm" in result
        assert "I've" in result

    def test_removes_llm_isms(self):
        text = "Certainly! The answer is quantum."
        result = self.analyzer.make_more_human(text)
        assert "Certainly!" not in result

    def test_removes_great_question(self):
        text = "Great question! Let me explain."
        result = self.analyzer.make_more_human(text)
        assert "Great question!" not in result

    def test_preserves_normal_text(self):
        text = "Consciousness is a deep mystery."
        result = self.analyzer.make_more_human(text)
        assert "mystery" in result


class TestTextAnalyzerSingleton:
    """Tests for the singleton getter."""

    def test_returns_instance(self):
        import text_analyzer
        text_analyzer._text_analyzer = None
        analyzer = get_text_analyzer()
        assert isinstance(analyzer, TextAnalyzer)

    def test_returns_same_instance(self):
        import text_analyzer
        text_analyzer._text_analyzer = None
        a1 = get_text_analyzer()
        a2 = get_text_analyzer()
        assert a1 is a2
