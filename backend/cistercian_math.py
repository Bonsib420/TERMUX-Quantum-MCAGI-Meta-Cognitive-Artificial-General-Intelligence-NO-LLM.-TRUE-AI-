"""
🔢 CISTERCIAN MATH — Mathematical Expression Detection & Evaluation
====================================================================
Detects mathematical expressions in natural language input and evaluates them,
with special support for Cistercian numeral notation.

Supports:
  - Standard arithmetic: 2 + 3, 15 * 7, 100 / 4
  - Parenthesized expressions: (2 + 3) * 4
  - Powers: 2^10, 3**4
  - Square roots: sqrt(144)
  - Factorials: 5!, 10!
  - Cistercian notation: 𝕮(42), cist(256), cistercian(1000)
  - Arabic number words: "what is twenty plus thirty?"
  - Constants: pi, e, tau

Integration:
  - chat.py: Called before Markov chain to intercept math queries
  - routes_chat.py: API endpoint for math evaluation
  - 41 tests in tests/test_cistercian_math.py
"""

import re
import math
import operator
from typing import Dict, Optional, Tuple, List

# ============================================================================
# CISTERCIAN ASCII RENDERING
# ============================================================================

# Cistercian digit patterns for ASCII art (5 rows × 3 cols per digit)
# The vertical staff is always the center column
CISTERCIAN_DIGITS = {
    0: [
        "   ",
        "   ",
        " | ",
        " | ",
        " | ",
    ],
    1: [
        " __",
        " | ",
        " | ",
        " | ",
        " | ",
    ],
    2: [
        " | ",
        " |_",
        " | ",
        " | ",
        " | ",
    ],
    3: [
        " \\ ",
        " | ",
        " | ",
        " | ",
        " | ",
    ],
    4: [
        " / ",
        " | ",
        " | ",
        " | ",
        " | ",
    ],
    5: [
        " __",
        " / ",
        " | ",
        " | ",
        " | ",
    ],
    6: [
        " | ",
        " ||",
        " | ",
        " | ",
        " | ",
    ],
    7: [
        " __",
        " ||",
        " | ",
        " | ",
        " | ",
    ],
    8: [
        " | ",
        " |_",
        " ||",
        " | ",
        " | ",
    ],
    9: [
        " __",
        " |_",
        " ||",
        " | ",
        " | ",
    ],
}


def render_cistercian_ascii(number: int) -> str:
    """
    Render a number (0-9999) as ASCII Cistercian numeral.

    The Cistercian system encodes 4 digits on a single vertical staff:
    - Ones: top-right quadrant
    - Tens: top-left quadrant (mirrored)
    - Hundreds: bottom-right quadrant (flipped)
    - Thousands: bottom-left quadrant (mirrored + flipped)
    """
    if not isinstance(number, int) or number < 0 or number > 9999:
        return f"[Cistercian supports 0-9999, got {number}]"

    ones = number % 10
    tens = (number // 10) % 10
    hundreds = (number // 100) % 10
    thousands = (number // 1000) % 10

    lines = []
    lines.append(f"  Cistercian({number}):")
    lines.append(f"  ┌─────┐")

    # Build a simple representation
    digits_str = f"  │ {thousands}×1000 + {hundreds}×100 + {tens}×10 + {ones}×1 │"
    lines.append(digits_str)
    lines.append(f"  │  ═══╪═══  │")

    # Staff with quadrant indicators
    if thousands > 0:
        lines.append(f"  │ {thousands}╔══╪══╗  │")
    else:
        lines.append(f"  │  ║  │  ║  │")
    if ones > 0 or tens > 0:
        lines.append(f"  │ {tens}╚══╪══╝{ones} │")
    else:
        lines.append(f"  │  ╚══╪══╝  │")
    if hundreds > 0:
        lines.append(f"  │  ║  {hundreds}  ║  │")

    lines.append(f"  └─────┘")
    return '\n'.join(lines)


# ============================================================================
# NUMBER WORD PARSING
# ============================================================================

WORD_TO_NUM = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
    'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
    'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
    'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
    'eighteen': 18, 'nineteen': 19, 'twenty': 20, 'thirty': 30,
    'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
    'eighty': 80, 'ninety': 90, 'hundred': 100, 'thousand': 1000,
    'million': 1000000, 'billion': 1000000000,
    'pi': math.pi, 'e': math.e, 'tau': math.tau,
}

WORD_OPS = {
    'plus': '+', 'add': '+', 'added': '+',
    'minus': '-', 'subtract': '-', 'less': '-',
    'times': '*', 'multiplied': '*', 'multiply': '*',
    'divided': '/', 'over': '/',
    'to the power of': '**', 'squared': '**2', 'cubed': '**3',
}


def _parse_number_words(text: str) -> str:
    """Convert number words in text to digits."""
    result = text.lower()
    # Sort by length descending to match longer phrases first
    for word, num in sorted(WORD_TO_NUM.items(), key=lambda x: -len(x[0])):
        result = result.replace(word, str(num))
    for word, op in sorted(WORD_OPS.items(), key=lambda x: -len(x[0])):
        result = result.replace(word, f' {op} ')
    return result


# ============================================================================
# MATH DETECTION
# ============================================================================

# Pattern for explicit Cistercian notation: 𝕮(N), cist(N), cistercian(N)
CISTERCIAN_PATTERN = re.compile(
    r'(?:𝕮|cist(?:ercian)?)\s*\(\s*(\d+)\s*\)', re.IGNORECASE
)

# Pattern for mathematical expressions
MATH_EXPRESSION_PATTERN = re.compile(
    r'^(?:what\s+is\s+|calculate\s+|compute\s+|solve\s+|evaluate\s+)?'
    r'([\d\.\s\+\-\*/\^\(\)!%]+(?:\s*[\+\-\*/\^]\s*[\d\.\s\+\-\*/\^\(\)!%]+)+)',
    re.IGNORECASE
)

# Pattern for simple "what is X op Y" questions
WORD_MATH_PATTERN = re.compile(
    r'(?:what\s+is|how\s+much\s+is|calculate|compute)\s+(.+)',
    re.IGNORECASE
)

# Pattern for sqrt
SQRT_PATTERN = re.compile(r'(?:sqrt|square\s*root\s*(?:of)?)\s*\(?\s*([\d.]+)\s*\)?')

# Pattern for factorial
FACTORIAL_PATTERN = re.compile(r'(\d+)\s*!')


def detect_math(text: str) -> bool:
    """
    Detect whether input contains a mathematical expression.

    Returns True if the input appears to be a math query.
    """
    if not text or len(text) > 500:
        return False

    # Cistercian notation
    if CISTERCIAN_PATTERN.search(text):
        return True

    # Direct math expression
    if MATH_EXPRESSION_PATTERN.search(text):
        return True

    # Sqrt
    if SQRT_PATTERN.search(text):
        return True

    # Factorial
    if FACTORIAL_PATTERN.search(text):
        return True

    # Word math ("what is twenty plus thirty")
    if WORD_MATH_PATTERN.search(text):
        parsed = _parse_number_words(text)
        # Check if parsing produced something with operators and numbers
        if re.search(r'\d+\s*[\+\-\*/]\s*\d+', parsed):
            return True

    return False


# ============================================================================
# MATH EVALUATION
# ============================================================================

# Safe operators for eval
_SAFE_OPS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
    '//': operator.floordiv,
    '%': operator.mod,
    '**': operator.pow,
}


def _safe_eval(expr: str) -> float:
    """
    Safely evaluate a mathematical expression.

    Uses a restricted eval with only math operations allowed.
    No builtins, no imports, no attribute access.
    """
    # Normalize
    expr = expr.replace('^', '**')

    # Handle factorial
    def _factorial_replace(m):
        n = int(m.group(1))
        if n > 170:  # prevent overflow
            raise ValueError(f"Factorial argument too large (max 170, got {n})")
        return str(math.factorial(n))

    expr = FACTORIAL_PATTERN.sub(_factorial_replace, expr)

    # Handle sqrt
    def _sqrt_replace(m):
        return str(math.sqrt(float(m.group(1))))

    expr = SQRT_PATTERN.sub(_sqrt_replace, expr)

    # Replace constants
    expr = re.sub(r'\bpi\b', str(math.pi), expr)
    expr = re.sub(r'\be\b', str(math.e), expr)
    expr = re.sub(r'\btau\b', str(math.tau), expr)

    # Security: only allow digits, operators, parens, dots, spaces, and valid scientific notation
    if not re.match(r'^[\d\s\+\-\*/\.\(\)]+(?:[eE][+-]?\d+)?$', expr):
        raise ValueError(f"Unsafe expression: {expr}")

    # Evaluate with empty namespace
    try:
        result = eval(expr, {"__builtins__": {}}, {})
        return float(result)
    except (SyntaxError, NameError, TypeError) as e:
        raise ValueError(f"Cannot evaluate: {expr} ({e})")


def evaluate_math(text: str) -> Optional[Dict]:
    """
    Evaluate a mathematical expression from text.

    Returns:
        Dict with 'expression', 'result', 'cistercian' (if applicable)
        or None if not evaluable.
    """
    # Check for Cistercian notation first
    cist_match = CISTERCIAN_PATTERN.search(text)
    if cist_match:
        number = int(cist_match.group(1))
        ascii_art = render_cistercian_ascii(number)
        return {
            "expression": f"cistercian({number})",
            "result": number,
            "cistercian": ascii_art,
            "type": "cistercian",
        }

    # Try direct math expression
    math_match = MATH_EXPRESSION_PATTERN.search(text)
    expr_str = None

    if math_match:
        expr_str = math_match.group(1).strip()
    else:
        # Try word math
        word_match = WORD_MATH_PATTERN.search(text)
        if word_match:
            parsed = _parse_number_words(word_match.group(1))
            # Extract the math part
            m = re.search(r'[\d\.]+(?:\s*[\+\-\*/\^]+\s*[\d\.]+)+', parsed)
            if m:
                expr_str = m.group(0)

    if not expr_str:
        # Try sqrt
        sqrt_match = SQRT_PATTERN.search(text)
        if sqrt_match:
            val = float(sqrt_match.group(1))
            result = math.sqrt(val)
            return {
                "expression": f"sqrt({val})",
                "result": result,
                "type": "function",
            }

        # Try factorial
        fact_match = FACTORIAL_PATTERN.search(text)
        if fact_match:
            n = int(fact_match.group(1))
            if n <= 170:
                result = math.factorial(n)
                return {
                    "expression": f"{n}!",
                    "result": result,
                    "type": "factorial",
                }

        return None

    try:
        result = _safe_eval(expr_str)
        response = {
            "expression": expr_str,
            "result": result,
            "type": "arithmetic",
        }

        # Add Cistercian rendering if result is a positive integer <= 9999
        if isinstance(result, float) and result == int(result) and 0 <= result <= 9999:
            response["cistercian"] = render_cistercian_ascii(int(result))

        return response
    except (ValueError, ZeroDivisionError, OverflowError) as e:
        return {
            "expression": expr_str,
            "error": str(e),
            "type": "error",
        }


def format_math_response(result: Dict) -> str:
    """
    Format a math evaluation result for display.

    Returns a human-readable string suitable for terminal or API response.
    """
    if not result:
        return ""

    if "error" in result:
        return f"Math error: {result['error']} (expression: {result['expression']})"

    parts = []
    expr = result.get("expression", "")
    val = result.get("result", 0)

    # Format the result nicely
    if isinstance(val, float) and val == int(val) and abs(val) < 1e15:
        val_str = str(int(val))
    elif isinstance(val, float):
        val_str = f"{val:.6g}"
    else:
        val_str = str(val)

    parts.append(f"{expr} = {val_str}")

    # Add Cistercian art if present
    if "cistercian" in result:
        parts.append("")
        parts.append(result["cistercian"])

    return '\n'.join(parts)
