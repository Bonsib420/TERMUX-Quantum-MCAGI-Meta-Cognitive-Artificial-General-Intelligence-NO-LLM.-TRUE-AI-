"""
Tests for personality_engine.py — Dynamic personality system.
"""

import pytest
from datetime import datetime

from personality_engine import PersonalityEngine, get_personality_engine


class TestPersonalityEngineInit:
    """Tests for personality engine initialization."""

    def setup_method(self):
        self.pe = PersonalityEngine()

    def test_traits_initialized(self):
        assert isinstance(self.pe.traits, dict)
        assert len(self.pe.traits) == 10

    def test_trait_values_in_range(self):
        for trait, value in self.pe.traits.items():
            assert 0.0 <= value <= 1.0, f"Trait {trait} = {value} out of range"

    def test_specific_trait_values(self):
        assert self.pe.traits["curiosity"] == 0.8
        assert self.pe.traits["philosophical"] == 0.85
        assert self.pe.traits["formality"] == 0.3

    def test_beliefs_initialized(self):
        assert isinstance(self.pe.beliefs, dict)
        assert len(self.pe.beliefs) == 7

    def test_belief_values_in_range(self):
        for belief, value in self.pe.beliefs.items():
            assert 0.0 <= value <= 1.0, f"Belief {belief} = {value} out of range"

    def test_communication_style_initialized(self):
        assert isinstance(self.pe.communication_style, dict)
        assert self.pe.communication_style["uses_analogies"] is True
        assert self.pe.communication_style["prefers_depth_over_brevity"] is True

    def test_interests_initialized(self):
        assert isinstance(self.pe.interests, list)
        assert len(self.pe.interests) == 6
        assert "quantum mechanics" in self.pe.interests

    def test_signature_phrases_initialized(self):
        assert isinstance(self.pe.signature_phrases, list)
        assert len(self.pe.signature_phrases) == 5

    def test_opinions_empty_initially(self):
        assert self.pe.opinions == {}

    def test_interaction_memory_initialized(self):
        assert "topics_users_enjoyed" in self.pe.interaction_memory
        assert "styles_that_worked" in self.pe.interaction_memory
        assert "approaches_that_failed" in self.pe.interaction_memory


class TestPersonalityEngineMethods:
    """Tests for personality engine methods."""

    def setup_method(self):
        self.pe = PersonalityEngine()

    def test_get_trait_existing(self):
        assert self.pe.get_trait("curiosity") == 0.8

    def test_get_trait_nonexistent_returns_default(self):
        assert self.pe.get_trait("nonexistent") == 0.5

    def test_evolve_trait_increase(self):
        self.pe.evolve_trait("curiosity", 0.1)
        assert self.pe.traits["curiosity"] == 0.9

    def test_evolve_trait_decrease(self):
        self.pe.evolve_trait("curiosity", -0.3)
        assert self.pe.traits["curiosity"] == 0.5

    def test_evolve_trait_clamps_upper(self):
        self.pe.evolve_trait("curiosity", 1.0)
        assert self.pe.traits["curiosity"] == 1.0

    def test_evolve_trait_clamps_lower(self):
        self.pe.evolve_trait("curiosity", -2.0)
        assert self.pe.traits["curiosity"] == 0.0

    def test_evolve_nonexistent_trait_no_effect(self):
        self.pe.evolve_trait("nonexistent", 0.5)
        assert "nonexistent" not in self.pe.traits

    def test_form_opinion(self):
        self.pe.form_opinion("consciousness", "it's real", 0.9)
        opinion = self.pe.get_opinion("consciousness")
        assert opinion is not None
        assert opinion["stance"] == "it's real"
        assert opinion["confidence"] == 0.9
        assert opinion["times_expressed"] == 0

    def test_get_opinion_nonexistent(self):
        assert self.pe.get_opinion("nonexistent") is None

    def test_form_opinion_updates_existing(self):
        self.pe.form_opinion("topic", "first stance", 0.5)
        self.pe.form_opinion("topic", "updated stance", 0.8)
        opinion = self.pe.get_opinion("topic")
        assert opinion["stance"] == "updated stance"
        assert opinion["confidence"] == 0.8

    def test_express_personality_returns_dict(self):
        result = self.pe.express_personality()
        assert isinstance(result, dict)
        assert "tone" in result
        assert "depth_level" in result


class TestPersonalityEngineSingleton:
    """Tests for the singleton getter."""

    def test_get_personality_engine_returns_instance(self):
        import personality_engine
        personality_engine._personality_engine = None  # Reset singleton
        pe = get_personality_engine()
        assert isinstance(pe, PersonalityEngine)

    def test_get_personality_engine_returns_same_instance(self):
        import personality_engine
        personality_engine._personality_engine = None
        pe1 = get_personality_engine()
        pe2 = get_personality_engine()
        assert pe1 is pe2
