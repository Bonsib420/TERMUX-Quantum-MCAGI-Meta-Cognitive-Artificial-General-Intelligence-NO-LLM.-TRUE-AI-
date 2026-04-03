"""
Tests for dream_state.py — DreamStateEngine background processing.
"""

import pytest

from dream_state import DreamStateEngine


class TestDreamStateEngineInit:
    """Tests for DreamStateEngine initialization."""

    def test_initialization_no_db(self):
        engine = DreamStateEngine()
        assert engine.is_dreaming is False
        assert engine.dream_log == []
        assert engine.current_dream is None

    def test_dream_activities_defined(self):
        engine = DreamStateEngine()
        assert isinstance(engine.dream_activities, list)
        assert len(engine.dream_activities) > 0

    def test_idle_threshold_set(self):
        engine = DreamStateEngine()
        assert engine.idle_threshold_minutes > 0


class TestDreamStateEngineEnter:
    """Tests for entering/exiting dream state."""

    def test_enter_dream_state(self):
        engine = DreamStateEngine()
        result = engine.enter_dream_state()
        assert engine.is_dreaming is True
        assert engine.current_dream is not None
        assert "started_at" in engine.current_dream

    def test_enter_dream_returns_status(self):
        engine = DreamStateEngine()
        result = engine.enter_dream_state()
        assert isinstance(result, dict)
        assert result.get("status") == "dreaming"

    def test_enter_dream_already_dreaming(self):
        engine = DreamStateEngine()
        engine.enter_dream_state()
        result = engine.enter_dream_state()
        # Should handle gracefully (already dreaming)
        assert engine.is_dreaming is True

    def test_dream_state_initializes_tracking(self):
        engine = DreamStateEngine()
        engine.enter_dream_state()
        dream = engine.current_dream
        assert "activities" in dream
        assert "insights" in dream
        assert "questions_formed" in dream
        assert "topics_explored" in dream


class TestDreamActivities:
    """Tests for dream activity types."""

    def test_known_activities(self):
        engine = DreamStateEngine()
        expected = {
            "memory_consolidation", "curiosity_research", "self_reflection",
            "idea_generation", "code_contemplation", "personality_development",
            "question_formation",
        }
        # At least these core activities should exist
        activity_set = set(engine.dream_activities)
        assert expected.issubset(activity_set)

    def test_activities_are_strings(self):
        engine = DreamStateEngine()
        for activity in engine.dream_activities:
            assert isinstance(activity, str)
            assert len(activity) > 0
