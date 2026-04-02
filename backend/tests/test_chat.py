"""
Tests for chat.py — LocalMemory domain classification and growth stages.
"""

import pytest

from chat import LocalMemory


class TestLocalMemoryDomainClassification:
    """Tests for the domain keyword classifier."""

    def test_classify_exact_keyword(self):
        """Exact keyword match should return correct domain."""
        assert LocalMemory._classify_domain("quantum") == "physics"
        assert LocalMemory._classify_domain("consciousness") == "philosophy"
        assert LocalMemory._classify_domain("algorithm") == "computer_science"
        assert LocalMemory._classify_domain("cell") == "biology"
        assert LocalMemory._classify_domain("equation") == "mathematics"
        assert LocalMemory._classify_domain("emotion") == "psychology"
        assert LocalMemory._classify_domain("grammar") == "language"

    def test_classify_case_insensitive(self):
        assert LocalMemory._classify_domain("QUANTUM") == "physics"
        assert LocalMemory._classify_domain("Consciousness") == "philosophy"

    def test_classify_unknown_returns_general(self):
        assert LocalMemory._classify_domain("xyzzy") == "general"

    def test_classify_partial_match(self):
        """Partial matches (substring) should still classify."""
        result = LocalMemory._classify_domain("thermodynamics")
        assert result == "physics"

    def test_classify_empty_string(self):
        result = LocalMemory._classify_domain("")
        assert result == "general"

    def test_all_domains_covered(self):
        """Every domain in DOMAIN_KEYWORDS should be reachable."""
        domains_found = set()
        for domain, keywords in LocalMemory.DOMAIN_KEYWORDS.items():
            for kw in keywords:
                result = LocalMemory._classify_domain(kw)
                domains_found.add(result)
        expected = set(LocalMemory.DOMAIN_KEYWORDS.keys())
        assert expected.issubset(domains_found)


class TestLocalMemoryDomainKeywords:
    """Tests for the DOMAIN_KEYWORDS constant."""

    def test_is_dict(self):
        assert isinstance(LocalMemory.DOMAIN_KEYWORDS, dict)

    def test_has_expected_domains(self):
        expected = {
            "philosophy", "physics", "computer_science",
            "biology", "mathematics", "psychology", "language",
        }
        assert set(LocalMemory.DOMAIN_KEYWORDS.keys()) == expected

    def test_all_values_are_sets(self):
        for domain, keywords in LocalMemory.DOMAIN_KEYWORDS.items():
            assert isinstance(keywords, set), f"{domain} keywords is not a set"

    def test_keywords_are_lowercase(self):
        for domain, keywords in LocalMemory.DOMAIN_KEYWORDS.items():
            for kw in keywords:
                assert kw == kw.lower(), f"Keyword '{kw}' in {domain} is not lowercase"

    def test_minimum_keywords_per_domain(self):
        for domain, keywords in LocalMemory.DOMAIN_KEYWORDS.items():
            assert len(keywords) >= 10, f"{domain} has too few keywords: {len(keywords)}"


class TestLocalMemoryGrowthStages:
    """Tests for growth stage definitions."""

    def test_stages_defined(self):
        assert isinstance(LocalMemory.GROWTH_STAGES, list)
        assert len(LocalMemory.GROWTH_STAGES) > 0

    def test_stages_ordered(self):
        for i in range(len(LocalMemory.GROWTH_STAGES)):
            assert LocalMemory.GROWTH_STAGES[i]["stage"] == i

    def test_stages_have_names(self):
        for stage in LocalMemory.GROWTH_STAGES:
            assert "name" in stage
            assert isinstance(stage["name"], str)
            assert len(stage["name"]) > 0

    def test_stages_have_thresholds(self):
        for stage in LocalMemory.GROWTH_STAGES:
            assert "threshold" in stage
            threshold = stage["threshold"]
            assert "connections" in threshold
            assert "concepts" in threshold

    def test_nascent_stage_zero_thresholds(self):
        nascent = LocalMemory.GROWTH_STAGES[0]
        assert nascent["name"] == "Nascent"
        assert nascent["threshold"]["connections"] == 0
        assert nascent["threshold"]["concepts"] == 0

    def test_thresholds_increase_monotonically(self):
        """Each successive stage should have higher or equal thresholds."""
        for i in range(1, len(LocalMemory.GROWTH_STAGES)):
            prev = LocalMemory.GROWTH_STAGES[i - 1]["threshold"]
            curr = LocalMemory.GROWTH_STAGES[i]["threshold"]
            assert curr["connections"] >= prev["connections"]
            assert curr["concepts"] >= prev["concepts"]
