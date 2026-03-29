"""
🖋️ Cistercian Numeral System
=============================
Medieval number representation using a single vertical staff.

Numbers 0-9999 represented in 4 quadrants:
- Ones (1-9): top-right
- Tens (10-90): top-left
- Hundreds (100-900): bottom-right
- Thousands (1000-9000): bottom-left

Each digit 1-9 has a specific pattern of lines/triangles on a 2×2 grid.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class LineSegment:
    """A line segment in SVG coordinates"""
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass
class TriangleShape:
    """A filled triangle defined by 3 points"""
    points: str  # "x1,y1 x2,y2 x3,y3"


@dataclass
class QuadrantResult:
    """Result for one quadrant containing lines and triangles"""
    lines: List[LineSegment]
    triangles: List[TriangleShape]


def get_ones_shapes(digit: int) -> QuadrantResult:
    """Get shapes for a digit in the ONES quadrant (top-right)

    SVG coordinates: y from -5 (top) to -3 (middle), x from 0 to 2 (right)
    """
    lines = []
    triangles = []

    if digit == 1:
        lines.append(LineSegment(0, -5, 2, -5))  # horizontal top
    elif digit == 2:
        lines.append(LineSegment(0, -3, 2, -3))  # horizontal middle
    elif digit == 3:
        lines.append(LineSegment(0, -5, 2, -3))  # diagonal down-right
    elif digit == 4:
        lines.append(LineSegment(0, -3, 2, -5))  # diagonal up-right
    elif digit == 5:
        triangles.append(TriangleShape("0,-5 2,-5 0,-3"))
    elif digit == 6:
        lines.append(LineSegment(2, -5, 2, -3))  # vertical outer
    elif digit == 7:
        lines.append(LineSegment(0, -5, 2, -5))
        lines.append(LineSegment(2, -5, 2, -3))
    elif digit == 8:
        lines.append(LineSegment(0, -3, 2, -3))
        lines.append(LineSegment(2, -5, 2, -3))
    elif digit == 9:
        lines.append(LineSegment(0, -5, 2, -5))
        lines.append(LineSegment(0, -3, 2, -3))
        lines.append(LineSegment(2, -5, 2, -3))

    return QuadrantResult(lines, triangles)


def get_tens_shapes(digit: int) -> QuadrantResult:
    """Get shapes for a digit in the TENS quadrant (top-left)

    SVG coordinates: y from -5 (top) to -3 (middle), x from 0 to -2 (left)
    """
    lines = []
    triangles = []

    if digit == 1:
        lines.append(LineSegment(0, -5, -2, -5))
    elif digit == 2:
        lines.append(LineSegment(0, -3, -2, -3))
    elif digit == 3:
        lines.append(LineSegment(0, -5, -2, -3))
    elif digit == 4:
        lines.append(LineSegment(0, -3, -2, -5))
    elif digit == 5:
        triangles.append(TriangleShape("0,-5 -2,-5 0,-3"))
    elif digit == 6:
        lines.append(LineSegment(-2, -5, -2, -3))
    elif digit == 7:
        lines.append(LineSegment(0, -5, -2, -5))
        lines.append(LineSegment(-2, -5, -2, -3))
    elif digit == 8:
        lines.append(LineSegment(0, -3, -2, -3))
        lines.append(LineSegment(-2, -5, -2, -3))
    elif digit == 9:
        lines.append(LineSegment(0, -5, -2, -5))
        lines.append(LineSegment(0, -3, -2, -3))
        lines.append(LineSegment(-2, -5, -2, -3))

    return QuadrantResult(lines, triangles)


def get_hundreds_shapes(digit: int) -> QuadrantResult:
    """Get shapes for a digit in the HUNDREDS quadrant (bottom-right)

    SVG coordinates: y from 5 (bottom) to 3 (middle), x from 0 to 2 (right)
    """
    lines = []
    triangles = []

    if digit == 1:
        lines.append(LineSegment(0, 5, 2, 5))
    elif digit == 2:
        lines.append(LineSegment(0, 3, 2, 3))
    elif digit == 3:
        lines.append(LineSegment(0, 5, 2, 3))
    elif digit == 4:
        lines.append(LineSegment(0, 3, 2, 5))
    elif digit == 5:
        triangles.append(TriangleShape("0,5 2,5 0,3"))
    elif digit == 6:
        lines.append(LineSegment(2, 5, 2, 3))
    elif digit == 7:
        lines.append(LineSegment(0, 5, 2, 5))
        lines.append(LineSegment(2, 5, 2, 3))
    elif digit == 8:
        lines.append(LineSegment(0, 3, 2, 3))
        lines.append(LineSegment(2, 5, 2, 3))
    elif digit == 9:
        lines.append(LineSegment(0, 5, 2, 5))
        lines.append(LineSegment(0, 3, 2, 3))
        lines.append(LineSegment(2, 5, 2, 3))

    return QuadrantResult(lines, triangles)


def get_thousands_shapes(digit: int) -> QuadrantResult:
    """Get shapes for a digit in the THOUSANDS quadrant (bottom-left)

    SVG coordinates: y from 5 (bottom) to 3 (middle), x from 0 to -2 (left)
    """
    lines = []
    triangles = []

    if digit == 1:
        lines.append(LineSegment(0, 5, -2, 5))
    elif digit == 2:
        lines.append(LineSegment(0, 3, -2, 3))
    elif digit == 3:
        lines.append(LineSegment(0, 5, -2, 3))
    elif digit == 4:
        lines.append(LineSegment(0, 3, -2, 5))
    elif digit == 5:
        triangles.append(TriangleShape("0,5 -2,5 0,3"))
    elif digit == 6:
        lines.append(LineSegment(-2, 5, -2, 3))
    elif digit == 7:
        lines.append(LineSegment(0, 5, -2, 5))
        lines.append(LineSegment(-2, 5, -2, 3))
    elif digit == 8:
        lines.append(LineSegment(0, 3, -2, 3))
        lines.append(LineSegment(-2, 5, -2, 3))
    elif digit == 9:
        lines.append(LineSegment(0, 5, -2, 5))
        lines.append(LineSegment(0, 3, -2, 3))
        lines.append(LineSegment(-2, 5, -2, 3))

    return QuadrantResult(lines, triangles)


def generate_cistercian_numeral(number: int) -> Dict:
    """
    Generate Cistercian numeral representation for a number 0-9999.

    Returns:
        Dictionary with:
        - 'number': original number
        - 'digits': {ones, tens, hundreds, thousands}
        - 'lines': list of all line segments
        - 'triangles': list of all filled triangles
        - 'svg_viewBox': recommended SVG viewBox
    """
    clamped = max(0, min(9999, int(number)))

    ones = clamped % 10
    tens = (clamped % 100) // 10
    hundreds = (clamped % 1000) // 100
    thousands = clamped // 1000

    # Get shapes for each quadrant
    ones_result = get_ones_shapes(ones)
    tens_result = get_tens_shapes(tens)
    hundreds_result = get_hundreds_shapes(hundreds)
    thousands_result = get_thousands_shapes(thousands)

    # Combine all lines
    all_lines = []
    for result in [ones_result, tens_result, hundreds_result, thousands_result]:
        all_lines.extend([{'x1': l.x1, 'y1': l.y1, 'x2': l.x2, 'y2': l.y2} for l in result.lines])

    # Combine all triangles
    all_triangles = [{'points': t.points} for t in (
        ones_result.triangles + tens_result.triangles +
        hundreds_result.triangles + thousands_result.triangles
    )]

    return {
        'number': clamped,
        'digits': {
            'ones': ones,
            'tens': tens,
            'hundreds': hundreds,
            'thousands': thousands
        },
        'lines': all_lines,
        'triangles': all_triangles,
        'svg_viewBox': '-3 -5 6 10'  # x: -3 to 3, y: -5 to 5
    }


def render_cistercian_svg(number: int, size: int = 80, color: str = '#FFFFFF',
                         stroke_width: float = 1.5) -> str:
    """
    Generate SVG string for a Cistercian numeral.

    Args:
        number: Integer 0-9999
        size: SVG width in pixels
        color: Stroke/fill color
        stroke_width: Line width

    Returns:
        SVG string
    """
    data = generate_cistercian_numeral(number)
    viewBox = data['svg_viewBox']
    height = size * (10 / 6)  # maintain aspect ratio

    svg_lines = [
        f'<svg width="{size}" height="{height}" viewBox="{viewBox}" xmlns="http://www.w3.org/2000/svg">',
        '  <!-- Central vertical staff -->',
        f'  <line x1="0" y1="-5" x2="0" y2="5" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round"/>'
    ]

    # Add triangles (filled)
    for tri in data['triangles']:
        svg_lines.append(
            f'  <polygon points="{tri["points"]}" fill="{color}" stroke="{color}" '
            f'stroke-width="{stroke_width}" stroke-linejoin="round"/>'
        )

    # Add lines
    for line in data['lines']:
        svg_lines.append(
            f'  <line x1="{line["x1"]}" y1="{line["y1"]}" x2="{line["x2"]}" y2="{line["y2"]}" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round"/>'
        )

    svg_lines.append('</svg>')
    return '\n'.join(svg_lines)


# Quick test
if __name__ == '__main__':
    # Generate test for 1234
    import json
    result = generate_cistercian_numeral(1234)
    print(json.dumps(result, indent=2))
    print("\nSVG:")
    print(render_cistercian_numeral(1234, size=100))
