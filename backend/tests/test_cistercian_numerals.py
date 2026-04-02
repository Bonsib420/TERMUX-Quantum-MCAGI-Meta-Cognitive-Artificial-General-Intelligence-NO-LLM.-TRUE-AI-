"""
Tests for cistercian_numerals.py — Medieval number representation.
"""

import pytest

from cistercian_numerals import (
    LineSegment,
    TriangleShape,
    QuadrantResult,
    get_ones_shapes,
    get_tens_shapes,
    get_hundreds_shapes,
    get_thousands_shapes,
    generate_cistercian_numeral,
    render_cistercian_svg,
)


# ============================================================================
# Quadrant shape functions
# ============================================================================


class TestQuadrantShapes:
    """Tests for individual digit shape generators."""

    # -- Ones quadrant (top-right) --

    def test_ones_zero_empty(self):
        result = get_ones_shapes(0)
        assert result.lines == []
        assert result.triangles == []

    @pytest.mark.parametrize("digit", range(1, 10))
    def test_ones_nonzero_has_shapes(self, digit):
        result = get_ones_shapes(digit)
        assert len(result.lines) > 0 or len(result.triangles) > 0

    def test_ones_digit_1_single_line(self):
        result = get_ones_shapes(1)
        assert len(result.lines) == 1
        assert len(result.triangles) == 0

    def test_ones_digit_5_has_triangle(self):
        result = get_ones_shapes(5)
        assert len(result.triangles) == 1

    def test_ones_digit_9_has_three_lines(self):
        result = get_ones_shapes(9)
        assert len(result.lines) == 3

    # -- Tens quadrant (top-left) --

    def test_tens_zero_empty(self):
        result = get_tens_shapes(0)
        assert result.lines == []
        assert result.triangles == []

    @pytest.mark.parametrize("digit", range(1, 10))
    def test_tens_nonzero_has_shapes(self, digit):
        result = get_tens_shapes(digit)
        assert len(result.lines) > 0 or len(result.triangles) > 0

    def test_tens_digit_5_has_triangle(self):
        result = get_tens_shapes(5)
        assert len(result.triangles) == 1

    def test_tens_uses_negative_x(self):
        """Tens quadrant should use negative x coordinates (left side)."""
        result = get_tens_shapes(1)
        line = result.lines[0]
        assert line.x2 < 0  # Extends to the left

    # -- Hundreds quadrant (bottom-right) --

    def test_hundreds_zero_empty(self):
        result = get_hundreds_shapes(0)
        assert result.lines == []
        assert result.triangles == []

    @pytest.mark.parametrize("digit", range(1, 10))
    def test_hundreds_nonzero_has_shapes(self, digit):
        result = get_hundreds_shapes(digit)
        assert len(result.lines) > 0 or len(result.triangles) > 0

    def test_hundreds_uses_positive_y(self):
        """Hundreds quadrant should use positive y coordinates (bottom)."""
        result = get_hundreds_shapes(1)
        line = result.lines[0]
        assert line.y1 > 0

    # -- Thousands quadrant (bottom-left) --

    def test_thousands_zero_empty(self):
        result = get_thousands_shapes(0)
        assert result.lines == []
        assert result.triangles == []

    @pytest.mark.parametrize("digit", range(1, 10))
    def test_thousands_nonzero_has_shapes(self, digit):
        result = get_thousands_shapes(digit)
        assert len(result.lines) > 0 or len(result.triangles) > 0

    def test_thousands_uses_negative_x_positive_y(self):
        """Thousands quadrant: negative x (left), positive y (bottom)."""
        result = get_thousands_shapes(1)
        line = result.lines[0]
        assert line.x2 < 0
        assert line.y1 > 0

    # -- Shape count symmetry across quadrants --

    @pytest.mark.parametrize("digit", range(0, 10))
    def test_same_shape_count_across_quadrants(self, digit):
        """Each digit should have the same number of lines+triangles in every quadrant."""
        ones = get_ones_shapes(digit)
        tens = get_tens_shapes(digit)
        hundreds = get_hundreds_shapes(digit)
        thousands = get_thousands_shapes(digit)
        count = lambda r: len(r.lines) + len(r.triangles)
        assert count(ones) == count(tens) == count(hundreds) == count(thousands)


# ============================================================================
# generate_cistercian_numeral
# ============================================================================


class TestGenerateCistercianNumeral:
    """Tests for the main numeral generation function."""

    def test_zero(self):
        result = generate_cistercian_numeral(0)
        assert result["number"] == 0
        assert result["digits"] == {"ones": 0, "tens": 0, "hundreds": 0, "thousands": 0}
        # Zero has no lines or triangles (just the staff)
        assert result["lines"] == []
        assert result["triangles"] == []

    def test_single_digit(self):
        result = generate_cistercian_numeral(7)
        assert result["number"] == 7
        assert result["digits"]["ones"] == 7
        assert result["digits"]["tens"] == 0
        assert result["digits"]["hundreds"] == 0
        assert result["digits"]["thousands"] == 0
        assert len(result["lines"]) > 0

    def test_two_digit(self):
        result = generate_cistercian_numeral(42)
        assert result["digits"]["ones"] == 2
        assert result["digits"]["tens"] == 4

    def test_three_digit(self):
        result = generate_cistercian_numeral(305)
        assert result["digits"]["ones"] == 5
        assert result["digits"]["tens"] == 0
        assert result["digits"]["hundreds"] == 3

    def test_four_digit(self):
        result = generate_cistercian_numeral(1234)
        assert result["digits"]["ones"] == 4
        assert result["digits"]["tens"] == 3
        assert result["digits"]["hundreds"] == 2
        assert result["digits"]["thousands"] == 1

    def test_max_value(self):
        result = generate_cistercian_numeral(9999)
        assert result["number"] == 9999
        assert result["digits"] == {"ones": 9, "tens": 9, "hundreds": 9, "thousands": 9}

    def test_clamps_above_max(self):
        result = generate_cistercian_numeral(10000)
        assert result["number"] == 9999

    def test_clamps_below_min(self):
        result = generate_cistercian_numeral(-5)
        assert result["number"] == 0

    def test_svg_viewbox_present(self):
        result = generate_cistercian_numeral(42)
        assert "svg_viewBox" in result
        assert result["svg_viewBox"] == "-3 -5 6 10"

    def test_all_lines_are_dicts(self):
        result = generate_cistercian_numeral(1234)
        for line in result["lines"]:
            assert "x1" in line
            assert "y1" in line
            assert "x2" in line
            assert "y2" in line

    def test_all_triangles_are_dicts(self):
        result = generate_cistercian_numeral(5555)
        for tri in result["triangles"]:
            assert "points" in tri


# ============================================================================
# render_cistercian_svg
# ============================================================================


class TestRenderCistercianSVG:
    """Tests for SVG rendering."""

    def test_returns_svg_string(self):
        svg = render_cistercian_svg(42)
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")

    def test_contains_staff_line(self):
        """Every numeral has a central vertical staff."""
        svg = render_cistercian_svg(0)
        assert 'x1="0" y1="-5" x2="0" y2="5"' in svg

    def test_custom_color(self):
        svg = render_cistercian_svg(1, color="#FF0000")
        assert "#FF0000" in svg

    def test_custom_size(self):
        svg = render_cistercian_svg(1, size=120)
        assert 'width="120"' in svg

    def test_digit_5_has_polygon(self):
        """Digit 5 uses a triangle (polygon)."""
        svg = render_cistercian_svg(5)
        assert "<polygon" in svg

    def test_nonzero_has_extra_lines(self):
        """Non-zero numeral should have more lines than just the staff."""
        svg = render_cistercian_svg(1234)
        line_count = svg.count("<line")
        assert line_count > 1  # At least staff + digit lines
