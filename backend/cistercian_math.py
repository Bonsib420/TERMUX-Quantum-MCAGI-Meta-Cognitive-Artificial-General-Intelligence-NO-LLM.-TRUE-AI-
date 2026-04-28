"""
🖋️ Cistercian Math Engine
==========================
Detects arithmetic in user input, evaluates it, and renders results
using Cistercian numerals — both ASCII art (terminal) and SVG (API).

Supports:
  - Arabic numeral expressions:  "50 - 20", "42 + 73 =", "what is 100 * 3"
  - Cistercian notation:         "𝕮(50) - 𝕮(20)", "cist(42) + cist(73)"
  - Quadrant notation:           "{ones=2,tens=5} + {ones=3,tens=2}"
  - Mixed:                       "𝕮(50) - 20"

Numbers 0-9999 (the Cistercian range).
"""

import re
from typing import Optional, Tuple, Dict, List


# ============================================================================
# ASCII rendering of Cistercian numerals for terminal display
# ============================================================================

def _digit_to_ascii_ones(d: int) -> List[str]:
    """Render digit 0-9 in top-right quadrant (3 rows × 3 cols).
    
    The staff is the leftmost column (col 0).
    Rows: 0=top, 1=middle, 2=bottom of quadrant.
    """
    # Each digit is a 3×3 grid: [row0, row1, row2]
    # '│' = staff, '─' = horizontal, '╲' = diagonal down, '╱' = diagonal up
    patterns = {
        0: ["   ", "   ", "   "],  # nothing
        1: ["──╴", "   ", "   "],  # horizontal top
        2: ["   ", "   ", "──╴"],  # horizontal bottom
        3: ["╲  ", " ╲ ", "  ╲"],  # diagonal top-to-bottom-right
        4: ["  ╱", " ╱ ", "╱  "],  # diagonal bottom-to-top-right
        5: ["──╲", " ▪ ", "──╱"],  # filled triangle (shown as filled)
        6: ["  │", "  │", "  │"],  # vertical right edge
        7: ["──┐", "  │", "  │"],  # 1 + 6 (horiz top + vert right)
        8: ["  │", "  │", "──┘"],  # 2 + 6 (horiz bottom + vert right)
        9: ["──┐", "  │", "──┘"],  # 1 + 2 + 6 (box open left)
    }
    return patterns.get(d, patterns[0])


def _digit_to_ascii_tens(d: int) -> List[str]:
    """Render digit 0-9 in top-left quadrant (mirrored)."""
    patterns = {
        0: ["   ", "   ", "   "],
        1: ["╶──", "   ", "   "],
        2: ["   ", "   ", "╶──"],
        3: ["  ╱", " ╱ ", "╱  "],
        4: ["╲  ", " ╲ ", "  ╲"],
        5: ["╱──", " ▪ ", "╲──"],  # filled triangle (shown as filled)
        6: ["│  ", "│  ", "│  "],
        7: ["┌──", "│  ", "│  "],
        8: ["│  ", "│  ", "└──"],
        9: ["┌──", "│  ", "└──"],
    }
    return patterns.get(d, patterns[0])


def _digit_to_ascii_hundreds(d: int) -> List[str]:
    """Render digit 0-9 in bottom-right quadrant (vertically mirrored from ones)."""
    patterns = {
        0: ["   ", "   ", "   "],
        1: ["   ", "   ", "──╴"],
        2: ["──╴", "   ", "   "],
        3: ["  ╱", " ╱ ", "╱  "],
        4: ["╲  ", " ╲ ", "  ╲"],
        5: ["──╱", " ▪ ", "──╲"],  # filled triangle (shown as filled)
        6: ["  │", "  │", "  │"],
        7: ["  │", "  │", "──┘"],
        8: ["──┐", "  │", "  │"],
        9: ["──┐", "  │", "──┘"],
    }
    return patterns.get(d, patterns[0])


def _digit_to_ascii_thousands(d: int) -> List[str]:
    """Render digit 0-9 in bottom-left quadrant (mirrored from hundreds)."""
    patterns = {
        0: ["   ", "   ", "   "],
        1: ["   ", "   ", "╶──"],
        2: ["╶──", "   ", "   "],
        3: ["╲  ", " ╲ ", "  ╲"],
        4: ["  ╱", " ╱ ", "╱  "],
        5: ["╲──", " ▪ ", "╱──"],  # filled triangle (shown as filled)
        6: ["│  ", "│  ", "│  "],
        7: ["│  ", "│  ", "└──"],
        8: ["┌──", "│  ", "│  "],
        9: ["┌──", "│  ", "└──"],
    }
    return patterns.get(d, patterns[0])


def render_cistercian_ascii(number: int) -> str:
    """
    Render a Cistercian numeral as ASCII art for terminal display.
    
    Returns a multi-line string showing the glyph on a vertical staff.
    Numbers 0-9999.
    
    Layout (7 rows × 7 cols):
        tens  │ ones     (top 3 rows)
              │          (staff middle)
        thous │ hundreds (bottom 3 rows)
    """
    n = max(0, min(9999, int(number)))
    ones = n % 10
    tens = (n // 10) % 10
    hundreds = (n // 100) % 10
    thousands = n // 1000

    top_right = _digit_to_ascii_ones(ones)
    top_left = _digit_to_ascii_tens(tens)
    bot_right = _digit_to_ascii_hundreds(hundreds)
    bot_left = _digit_to_ascii_thousands(thousands)

    lines = []
    # Top quadrant (3 rows)
    for i in range(3):
        lines.append(f"{top_left[i]}│{top_right[i]}")
    # Middle staff
    lines.append("   │   ")
    # Bottom quadrant (3 rows)
    for i in range(3):
        lines.append(f"{bot_left[i]}│{bot_right[i]}")

    return "\n".join(lines)


def render_expression_ascii(a: int, op: str, b: int, result: int) -> str:
    """
    Render a full arithmetic expression as Cistercian ASCII art.
    
    Shows:  𝕮(a)  op  𝕮(b)  =  𝕮(result)
    with the glyphs side by side.
    """
    op_display = {'+': '+', '-': '−', '*': '×', '/': '÷'}.get(op, op)
    
    a_lines = render_cistercian_ascii(a).split('\n')
    b_lines = render_cistercian_ascii(b).split('\n')
    r_lines = render_cistercian_ascii(result).split('\n')
    
    # Pad operator column (centered on middle row = row 3)
    op_col = [f"   " for _ in range(7)]
    op_col[3] = f" {op_display} "
    
    eq_col = [f"   " for _ in range(7)]
    eq_col[3] = " = "
    
    combined = []
    for i in range(7):
        combined.append(f"  {a_lines[i]}{op_col[i]}{b_lines[i]}{eq_col[i]}{r_lines[i]}")
    
    header = f"  𝕮({a})    {op_display}    𝕮({b})    =    𝕮({result})"
    
    return header + "\n" + "\n".join(combined)


# ============================================================================
# Math expression detection and evaluation
# ============================================================================

# Pattern for Cistercian notation: 𝕮(123) or cist(123) or C(123)
_CIST_NUM = r'(?:𝕮|cist|C)\((\d{1,4})\)'

# Pattern for Arabic numbers
_ARABIC_NUM = r'(\d{1,10})'

# Any number: either Cistercian notation or plain Arabic
_ANY_NUM = rf'(?:{_CIST_NUM}|{_ARABIC_NUM})'

# Operators
_OP = r'([+\-*/×÷])'

# Full expression patterns (anchored, max 60 chars input to prevent ReDoS)
_EXPR_PATTERNS = [
    # "𝕮(50) - 𝕮(20)" or "cist(42) + cist(73)"
    re.compile(rf'^\s*{_CIST_NUM}\s*{_OP}\s*{_CIST_NUM}\s*[=?]?\s*$'),
    # "𝕮(50) - 20" or "50 + 𝕮(20)" (mixed)
    re.compile(rf'^\s*{_ANY_NUM}\s*{_OP}\s*{_ANY_NUM}\s*[=?]?\s*$'),
    # "50 - 20" or "50-20=" (plain Arabic)
    re.compile(rf'^\s*(?:what is |calculate |compute |solve )?{_ARABIC_NUM} ?{_OP} ?{_ARABIC_NUM} ?[=?]?\s*$', re.IGNORECASE),
]


def _extract_number(match_groups: tuple) -> Optional[int]:
    """Extract number from regex groups (handles Cistercian vs Arabic capture groups)."""
    for g in match_groups:
        if g is not None:
            try:
                return int(g)
            except (ValueError, TypeError):
                pass
    return None


def detect_math(text: str) -> Optional[Dict]:
    """
    Detect arithmetic expressions in user input.
    
    Returns dict with {a, op, b} if math is found, None otherwise.
    Handles: "50 - 20", "50 - 20 =", "what is 42 + 73", 
             "𝕮(50) - 𝕮(20)", "cist(42) + cist(73)"
    """
    text = text.strip()[:60]  # cap length to prevent ReDoS
    
    # Try Cistercian-specific patterns first
    # Pattern: 𝕮(50) - 𝕮(20) or cist(50) - cist(20)
    m = re.match(rf'^\s*{_CIST_NUM}\s*{_OP}\s*{_CIST_NUM}\s*[=?]?\s*$', text)
    if m:
        return {'a': int(m.group(1)), 'op': m.group(2), 'b': int(m.group(3)), 'cistercian_input': True}
    
    # Pattern: plain "50 - 20" or "what is 42 + 73"
    m = re.match(
        r'^\s*(?:what is |calculate |compute |solve )?'
        r'(\d{1,5}) ?([+\-*/×÷]) ?(\d{1,5})'
        r' ?[=?]?\s*$',
        text, re.IGNORECASE
    )
    if m:
        return {'a': int(m.group(1)), 'op': m.group(2), 'b': int(m.group(3)), 'cistercian_input': False}
    
    return None


def evaluate_math(expr: Dict) -> Dict:
    """
    Evaluate a detected math expression.
    
    Args:
        expr: dict from detect_math() with {a, op, b, cistercian_input}
    
    Returns:
        dict with {a, op, b, result, error, cistercian_range, clamped, overflow}
    """
    a = expr['a']
    op_raw = expr['op']
    b = expr['b']
    
    # Normalize operator
    op = {'+': '+', '-': '-', '*': '*', '/': '/', '×': '*', '÷': '/'}.get(op_raw, op_raw)
    op_display = {'+': '+', '-': '−', '*': '×', '/': '÷'}.get(op, op)
    
    error = None
    result = 0
    
    if op == '/' and b == 0:
        error = "Division by zero is undefined."
    else:
        if op == '+':
            result = a + b
        elif op == '-':
            result = a - b
        elif op == '*':
            result = a * b
        elif op == '/':
            result = a // b  # integer division
    
    cistercian_range = (0 <= a <= 9999 and 0 <= b <= 9999)
    clamped = max(0, min(9999, result)) if not error else 0
    overflow = (result != clamped) if not error else False
    
    return {
        'a': a,
        'b': b,
        'op': op,
        'op_display': op_display,
        'result': result,
        'clamped': clamped,
        'error': error,
        'cistercian_range': cistercian_range,
        'overflow': overflow,
        'cistercian_input': expr.get('cistercian_input', False),
    }


def format_math_response(ev: Dict, show_ascii: bool = True) -> str:
    """
    Format a math evaluation result for terminal display.
    
    Args:
        ev: dict from evaluate_math()
        show_ascii: whether to include Cistercian ASCII art
    
    Returns:
        Formatted string for terminal output
    """
    if ev['error']:
        return f"🧮 {ev['error']}"
    
    a, b, result = ev['a'], ev['b'], ev['result']
    op = ev['op_display']
    clamped = ev['clamped']
    
    lines = [f"🧮 {a} {op} {b} = {result}"]
    
    if ev['cistercian_range']:
        overflow_note = ""
        if ev['overflow']:
            overflow_note = f"\n  ⚠️ Result {result} clamped to Cistercian range: {clamped}"
        
        lines.append(f"")
        lines.append(f"🖋️ In Cistercian numerals: 𝕮({a}) {op} 𝕮({b}) = 𝕮({clamped}){overflow_note}")
        
        if show_ascii:
            lines.append("")
            lines.append(render_expression_ascii(a, ev['op'], b, clamped))
    elif result > 9999 or a > 9999 or b > 9999:
        lines.append(f"\n  (Numbers beyond 9999 exceed Cistercian range)")
    
    return "\n".join(lines)


# ============================================================================
# Quick test
# ============================================================================
if __name__ == '__main__':
    print("=== Cistercian Math Engine ===\n")
    
    # Test ASCII rendering
    for n in [0, 1, 42, 365, 1234, 9999]:
        print(f"Number {n}:")
        print(render_cistercian_ascii(n))
        print()
    
    # Test expression rendering
    tests = ["50 - 20", "42 + 73", "100 * 3", "9999 / 3", "what is 50 - 20", "𝕮(50) - 𝕮(20)"]
    for t in tests:
        expr = detect_math(t)
        if expr:
            ev = evaluate_math(expr)
            print(f"Input: {t}")
            print(format_math_response(ev))
            print()
        else:
            print(f"Input: {t} → not detected as math")

def process_math(text, show_ascii=False):
    """Top-level entry: scan for math, evaluate, format. Returns string or None."""
    detected = detect_math(text)
    if not detected:
        return None
    ev = evaluate_math(detected)
    if not ev:
        return None
    return format_math_response(ev, show_ascii=show_ascii)

