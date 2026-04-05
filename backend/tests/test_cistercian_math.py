"""
Tests for cistercian_math.py — math detection, evaluation, and ASCII rendering.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cistercian_math import (
    detect_math, evaluate_math, format_math_response,
    render_cistercian_ascii, render_expression_ascii,
)


# ============================================================================
# detect_math tests
# ============================================================================

class TestDetectMath:
    """Test arithmetic expression detection."""

    def test_simple_addition(self):
        r = detect_math("50 + 20")
        assert r is not None
        assert r['a'] == 50 and r['b'] == 20 and r['op'] == '+'

    def test_simple_subtraction(self):
        r = detect_math("50 - 20")
        assert r is not None
        assert r['a'] == 50 and r['b'] == 20 and r['op'] == '-'

    def test_simple_multiplication(self):
        r = detect_math("6 * 7")
        assert r is not None
        assert r['a'] == 6 and r['b'] == 7 and r['op'] == '*'

    def test_simple_division(self):
        r = detect_math("100 / 4")
        assert r is not None
        assert r['a'] == 100 and r['b'] == 4 and r['op'] == '/'

    def test_with_equals(self):
        r = detect_math("50 - 20 =")
        assert r is not None
        assert r['a'] == 50 and r['b'] == 20

    def test_with_question_mark(self):
        r = detect_math("50 + 20?")
        assert r is not None
        assert r['a'] == 50 and r['b'] == 20

    def test_what_is_prefix(self):
        r = detect_math("what is 42 + 73")
        assert r is not None
        assert r['a'] == 42 and r['b'] == 73

    def test_calculate_prefix(self):
        r = detect_math("calculate 100 * 3")
        assert r is not None
        assert r['a'] == 100 and r['b'] == 3

    def test_no_spaces(self):
        r = detect_math("50-20")
        assert r is not None
        assert r['a'] == 50 and r['b'] == 20

    def test_cistercian_notation(self):
        """Test 𝕮(50) - 𝕮(20) detection."""
        r = detect_math("𝕮(50) - 𝕮(20)")
        assert r is not None
        assert r['a'] == 50 and r['b'] == 20
        assert r['cistercian_input'] is True

    def test_cist_notation(self):
        r = detect_math("cist(42) + cist(73)")
        assert r is not None
        assert r['a'] == 42 and r['b'] == 73
        assert r['cistercian_input'] is True

    def test_not_math_plain_text(self):
        assert detect_math("hello world") is None

    def test_not_math_sentence(self):
        assert detect_math("I have 50 cats and 20 dogs") is None

    def test_not_math_question(self):
        assert detect_math("what is consciousness") is None

    def test_empty(self):
        assert detect_math("") is None

    def test_unicode_operators(self):
        r = detect_math("50 × 20")
        assert r is not None
        assert r['op'] == '×'

        r = detect_math("100 ÷ 4")
        assert r is not None
        assert r['op'] == '÷'


# ============================================================================
# evaluate_math tests
# ============================================================================

class TestEvaluateMath:
    """Test arithmetic evaluation."""

    def test_addition(self):
        ev = evaluate_math({'a': 50, 'op': '+', 'b': 20, 'cistercian_input': False})
        assert ev['result'] == 70
        assert ev['error'] is None

    def test_subtraction(self):
        ev = evaluate_math({'a': 50, 'op': '-', 'b': 20, 'cistercian_input': False})
        assert ev['result'] == 30

    def test_multiplication(self):
        ev = evaluate_math({'a': 6, 'op': '*', 'b': 7, 'cistercian_input': False})
        assert ev['result'] == 42

    def test_integer_division(self):
        ev = evaluate_math({'a': 100, 'op': '/', 'b': 4, 'cistercian_input': False})
        assert ev['result'] == 25

    def test_division_by_zero(self):
        ev = evaluate_math({'a': 50, 'op': '/', 'b': 0, 'cistercian_input': False})
        assert ev['error'] is not None
        assert "zero" in ev['error'].lower()

    def test_cistercian_range(self):
        ev = evaluate_math({'a': 50, 'op': '+', 'b': 20, 'cistercian_input': False})
        assert ev['cistercian_range'] is True

    def test_overflow_clamped(self):
        ev = evaluate_math({'a': 9999, 'op': '+', 'b': 9999, 'cistercian_input': False})
        assert ev['result'] == 19998
        assert ev['clamped'] == 9999
        assert ev['overflow'] is True

    def test_negative_result(self):
        ev = evaluate_math({'a': 20, 'op': '-', 'b': 50, 'cistercian_input': False})
        assert ev['result'] == -30
        assert ev['clamped'] == 0
        assert ev['overflow'] is True

    def test_op_display(self):
        ev = evaluate_math({'a': 1, 'op': '-', 'b': 1, 'cistercian_input': False})
        assert ev['op_display'] == '−'  # minus sign, not hyphen

    def test_unicode_op_normalized(self):
        ev = evaluate_math({'a': 6, 'op': '×', 'b': 7, 'cistercian_input': False})
        assert ev['result'] == 42

        ev = evaluate_math({'a': 100, 'op': '÷', 'b': 4, 'cistercian_input': False})
        assert ev['result'] == 25


# ============================================================================
# format_math_response tests
# ============================================================================

class TestFormatMathResponse:
    """Test response formatting."""

    def test_basic_format(self):
        ev = evaluate_math({'a': 50, 'op': '-', 'b': 20, 'cistercian_input': False})
        text = format_math_response(ev, show_ascii=False)
        assert "50" in text
        assert "20" in text
        assert "30" in text
        assert "🧮" in text

    def test_cistercian_notation_in_output(self):
        ev = evaluate_math({'a': 50, 'op': '-', 'b': 20, 'cistercian_input': False})
        text = format_math_response(ev, show_ascii=False)
        assert "𝕮(50)" in text
        assert "𝕮(20)" in text
        assert "𝕮(30)" in text

    def test_error_format(self):
        ev = evaluate_math({'a': 50, 'op': '/', 'b': 0, 'cistercian_input': False})
        text = format_math_response(ev)
        assert "zero" in text.lower()
        assert "🧮" in text

    def test_ascii_art_included(self):
        ev = evaluate_math({'a': 50, 'op': '-', 'b': 20, 'cistercian_input': False})
        text = format_math_response(ev, show_ascii=True)
        assert "│" in text  # staff character from ASCII art

    def test_overflow_warning(self):
        ev = evaluate_math({'a': 9999, 'op': '+', 'b': 9999, 'cistercian_input': False})
        text = format_math_response(ev)
        assert "⚠️" in text or "clamped" in text.lower()


# ============================================================================
# render_cistercian_ascii tests
# ============================================================================

class TestRenderCistercianASCII:
    """Test ASCII art rendering."""

    def test_zero_is_bare_staff(self):
        art = render_cistercian_ascii(0)
        lines = art.split('\n')
        assert len(lines) == 7
        for line in lines:
            assert '│' in line

    def test_has_seven_lines(self):
        for n in [0, 1, 42, 365, 1234, 9999]:
            art = render_cistercian_ascii(n)
            assert len(art.split('\n')) == 7, f"Failed for {n}"

    def test_nonzero_has_decorations(self):
        art_0 = render_cistercian_ascii(0)
        art_1 = render_cistercian_ascii(1)
        assert art_0 != art_1  # 1 should have extra decorations

    def test_different_numbers_different_art(self):
        assert render_cistercian_ascii(42) != render_cistercian_ascii(73)

    def test_clamps_to_range(self):
        # Should not crash on out-of-range
        art = render_cistercian_ascii(99999)
        assert '│' in art
        art = render_cistercian_ascii(-5)
        assert '│' in art

    def test_all_digits_render(self):
        """Every single-digit number should produce unique art."""
        arts = set()
        for d in range(10):
            art = render_cistercian_ascii(d)
            arts.add(art)
        assert len(arts) == 10  # all unique

    def test_9999_symmetric(self):
        """9999 should have decorations in all four quadrants."""
        art = render_cistercian_ascii(9999)
        lines = art.split('\n')
        # Top-left and top-right should both have content
        assert lines[0].strip() != '│'
        # Bottom should also have content
        assert lines[6].strip() != '│'


# ============================================================================
# render_expression_ascii tests
# ============================================================================

class TestRenderExpressionASCII:
    """Test full expression ASCII art."""

    def test_renders_three_glyphs(self):
        art = render_expression_ascii(50, '-', 20, 30)
        # Should contain the header with all three numbers
        assert '𝕮(50)' in art
        assert '𝕮(20)' in art
        assert '𝕮(30)' in art

    def test_operator_shown(self):
        art = render_expression_ascii(50, '-', 20, 30)
        assert '−' in art  # minus sign

    def test_equals_shown(self):
        art = render_expression_ascii(50, '-', 20, 30)
        assert '=' in art
