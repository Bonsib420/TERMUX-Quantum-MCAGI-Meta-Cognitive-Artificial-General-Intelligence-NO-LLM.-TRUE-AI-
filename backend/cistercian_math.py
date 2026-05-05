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
    """
    Provide a 3-row ASCII-art pattern for a digit in the ones (top-right) quadrant.
    
    Parameters:
        d (int): Digit 0–9 to render. Values outside this range fall back to the pattern for 0.
    
    Returns:
        List[str]: Three 3-character strings representing the top, middle, and bottom rows of the quadrant.
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
    """
    Return a 3-row ASCII-art pattern for a digit placed in the tens (top-left) quadrant, mirrored for the Cistercian layout.
    
    Parameters:
        d (int): Digit value expected in the range 0–9. Values outside this range will be treated as 0.
    
    Returns:
        List[str]: Three 3-character strings representing the top-left quadrant rows for the digit.
    """
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
    """
    Return a 3-row ASCII-art pattern for a digit placed in the bottom-right (hundreds) quadrant.
    
    Parameters:
        d (int): Digit 0–9; values outside this range return the pattern for 0.
    
    Returns:
        List[str]: Three strings (one per row) representing the bottom-right quadrant glyph.
    """
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
    """
    Return a 3-row ASCII-art representation of a single digit (0–9) for the thousands (bottom-left) quadrant.
    
    Parameters:
        d (int): Digit in the range 0–9; values outside this range fall back to the representation for 0.
    
    Returns:
        List[str]: A list of three strings, each representing a row of the 3x3 quadrant for the thousands place.
    """
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
    
    Clamps the input to the range 0–9999 and renders the corresponding glyph as a 7×7 layout
    consisting of four quadrant digit patterns separated by a central vertical staff.
    
    Parameters:
        number (int): The value to render; will be clamped to 0–9999.
    
    Returns:
        str: A multi-line string (7 lines of 7 characters) representing the Cistercian glyph,
             with the staff on the fourth column (middle row is the staff line).
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
    Render an arithmetic expression as side-by-side Cistercian ASCII art including an operator and equals sign.
    
    Produces a header line like "𝕮(a) op 𝕮(b) = 𝕮(result)" followed by a 7-row ASCII-art block that places the three Cistercian glyphs side-by-side; the operator and equals sign are centered on the middle row.
    
    Returns:
        str: A multi-line string containing the header and the 7-row ASCII-art representation.
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
    """
    Return the first capture group that can be parsed as an integer.
    
    Parameters:
        match_groups (tuple): Sequence of regex capture group values (strings or None).
    
    Returns:
        int or None: The integer parsed from the first convertible group, or None if no group can be parsed.
    """
    for g in match_groups:
        if g is not None:
            try:
                return int(g)
            except (ValueError, TypeError):
                pass
    return None


def detect_math(text: str) -> Optional[Dict]:
    """
    Detect simple two-operand arithmetic expressions in the given text.
    
    Recognizes plain Arabic forms like "50 - 20", optional prefixed prompts like "what is 42 + 73", and Cistercian forms such as "𝕮(50) - 𝕮(20)" / "cist(42) + cist(73)". Operators supported: + - * / and the Unicode × ÷.
    
    Returns:
        dict: A mapping with keys:
            - 'a' (int): left operand
            - 'op' (str): operator token as found (one of '+', '-', '*', '/', '×', '÷')
            - 'b' (int): right operand
            - 'cistercian_input' (bool): True if both operands were written in Cistercian form, False otherwise
        None: if no supported expression is detected.
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
    Evaluate a detected two-operand arithmetic expression and normalize its result for Cistercian display.
    
    Parameters:
        expr (dict): Detection result from `detect_math` containing keys:
            - a (int): left operand
            - op (str): operator token as detected (one of "+ - * / × ÷")
            - b (int): right operand
            - cistercian_input (bool, optional): whether the input used Cistercian notation
    
    Returns:
        dict: Evaluation summary with keys:
            - a (int): left operand (copied)
            - b (int): right operand (copied)
            - op (str): normalized operator ("+", "-", "*", "/")
            - op_display (str): operator for display ("+", "−", "×", "÷")
            - result (int): computed integer result (uses floor division for "/"); 0 when an error occurred
            - clamped (int): `result` clamped to the Cistercian range 0..9999 (or 0 if an error)
            - error (str | None): error message on failure (e.g., division by zero), otherwise None
            - cistercian_range (bool): True if both operands fall within 0..9999
            - overflow (bool): True if `result` differed from `clamped` (indicates clamping occurred)
            - cistercian_input (bool): copied from input (defaults to False if absent)
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
    Format an evaluated arithmetic result into a human-readable terminal string with optional Cistercian notation and ASCII art.
    
    Parameters:
        ev (Dict): Evaluation dictionary produced by `evaluate_math`. Expected keys used here include:
            - 'a', 'b' (int): operands
            - 'op' (str): raw operator for ASCII rendering
            - 'op_display' (str): operator formatted for human display
            - 'result' (int): computed result (unclamped)
            - 'clamped' (int): result clamped to 0..9999
            - 'cistercian_range' (bool): whether operands are within 0..9999
            - 'overflow' (bool): whether the result was clamped
            - 'error' (Optional[str]): error message, if any
        show_ascii (bool): If True, include the combined Cistercian ASCII-art rendering when applicable.
    
    Returns:
        str: A multi-line string suitable for terminal output. If `ev['error']` is set, the string contains the error message; otherwise it contains a human-readable equation, optional Cistercian notation and, when enabled and applicable, ASCII-art rendering.
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
    """
    Detects a simple arithmetic expression in `text`, evaluates it, and returns a formatted response.
    
    If an expression is found, evaluates it (with Cistercian range handling) and returns the human-readable response; otherwise returns `None`.
    
    Parameters:
        text (str): Input text to scan for an arithmetic expression.
        show_ascii (bool): Whether to include Cistercian ASCII-art rendering when applicable.
    
    Returns:
        str or None: Formatted result string when an expression was detected, `None` if no expression was found.
    """
    detected = detect_math(text)
    if not detected:
        return None
    ev = evaluate_math(detected)
    if not ev:
        return None
    return format_math_response(ev, show_ascii=show_ascii)

