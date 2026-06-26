"""Math engine — direct symbolic arithmetic evaluator.

Detects math intent in user input, parses to a safe expression, evaluates
with Python's AST in arithmetic-only mode (no ``eval``, no shell access),
and optionally renders the result as a Cistercian glyph (0-9999).
"""
from __future__ import annotations

import ast
import math
import operator
import re
from typing import Dict, List, Optional


_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_WORD_OPS = [
    ('multiplied by', '*'),
    ('divided by', '/'),
    ('to the power of', '**'),
    ('raised to', '**'),
    ('squared', '**2'),
    ('cubed', '**3'),
    ('plus', '+'),
    ('minus', '-'),
    ('times', '*'),
    ('multiply', '*'),
    ('divide', '/'),
    ('over', '/'),
    ('mod', '%'),
    ('modulo', '%'),
    ('add', '+'),
    ('subtract', '-'),
    ('and', '+'),
]

_WORD_NUMBERS = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
    'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
    'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
    'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
    'eighteen': 18, 'nineteen': 19, 'twenty': 20, 'thirty': 30,
    'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
    'eighty': 80, 'ninety': 90, 'hundred': 100, 'thousand': 1000,
}

_ROMAN = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}


def _roman_to_int(s: str) -> Optional[int]:
    if not re.fullmatch(r'[IVXLCDMivxlcdm]+', s):
        return None
    s = s.upper()
    total = 0
    prev = 0
    for ch in reversed(s):
        v = _ROMAN.get(ch, 0)
        if v < prev:
            total -= v
        else:
            total += v
        prev = v
    return total if total > 0 else None


_MATH_TRIGGERS = re.compile(
    r'\d\s*[\+\-\*/%×÷\^]+\s*\d|\bsqrt\b|\bsquared\b|\bcubed\b',
    re.IGNORECASE,
)


class MathEngine:
    """Pure-arithmetic math evaluator with optional Cistercian visual."""

    def __init__(self):
        self.computations = 0
        self.last_result: Optional[Dict] = None

    def detect(self, text: str) -> bool:
        if not text:
            return False
        t = text.lower()
        if _MATH_TRIGGERS.search(text):
            return True
        if re.search(r'\d', t) and any(' ' + w + ' ' in ' ' + t + ' ' for w, _ in _WORD_OPS):
            return True
        words = set(re.findall(r'[a-z]+', t))
        if (words & set(_WORD_NUMBERS.keys())) and any(w in t for w, _ in _WORD_OPS):
            return True
        if re.search(r'\b[IVXLCDM]+\s*[\+\-\*/]\s*[IVXLCDM]+\b', text):
            return True
        # Roman numerals combined with a word-op (e.g. "XII times III")
        if re.search(r'\b[IVXLCDM]+\b', text) and any(' ' + w + ' ' in ' ' + t + ' ' for w, _ in _WORD_OPS):
            return True
        return False

    def normalize(self, text: str) -> Optional[str]:
        """Reduce a natural-language math question to a pure expression."""
        t = text
        t = t.replace('×', '*').replace('÷', '/').replace('^', '**')
        t = re.sub(r'\b([IVXLCDMivxlcdm]+)\b', lambda m: str(_roman_to_int(m.group(1)) or m.group(1)), t)
        t = t.lower()
        for word, op in _WORD_OPS:
            t = re.sub(r'\b' + re.escape(word) + r'\b', ' ' + op + ' ', t)
        for word, num in sorted(_WORD_NUMBERS.items(), key=lambda kv: -len(kv[0])):
            t = re.sub(r'\b' + re.escape(word) + r'\b', str(num), t)
        match = re.search(r'(?:\(|\d)[\d\s\+\-\*/%\.\(\)]*', t)
        if not match:
            return None
        expr = match.group(0).strip()
        expr = re.sub(r'\s+', '', expr)
        if not re.search(r'\d', expr):
            return None
        if not re.fullmatch(r'[\d\+\-\*/%\.\(\)]+', expr):
            return None
        return expr

    def _eval_node(self, node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return self._eval_node(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError('non-numeric constant')
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](self._eval_node(node.left), self._eval_node(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](self._eval_node(node.operand))
        raise ValueError(f'unsafe ast node: {type(node).__name__}')

    def evaluate(self, text: str) -> Optional[Dict]:
        if not self.detect(text):
            return None
        expr = self.normalize(text)
        if not expr:
            return None
        try:
            tree = ast.parse(expr, mode='eval')
            value = self._eval_node(tree)
        except ZeroDivisionError:
            return {'expression': expr, 'error': 'division by zero', 'result': None,
                    'cistercian_eligible': False}
        except Exception:
            return None

        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return None
            if value.is_integer():
                value = int(value)
            else:
                value = round(value, 6)

        eligible = isinstance(value, int) and 0 <= value <= 9999
        result = {
            'expression': expr,
            'result': value,
            'cistercian_eligible': eligible,
        }
        self.computations += 1
        self.last_result = result
        return result

    def render_cistercian(self, value: int) -> Optional[Dict]:
        """Return the structured Cistercian glyph for an integer 0-9999."""
        if not isinstance(value, int) or value < 0 or value > 9999:
            return None
        try:
            from cistercian_engine import generate_cistercian
            return generate_cistercian(value)
        except Exception:
            return None

    def format_response(self, ev: Dict) -> str:
        """Build the on-brand text answer for a chat reply."""
        if not ev:
            return ''
        if ev.get('error'):
            return f"🧮 {ev['expression']} → {ev['error']}"
        lines = [f"🧮 {ev['expression']} = {ev['result']}"]
        if ev.get('cistercian_eligible'):
            lines.append(f"🖋️ In Cistercian numerals: 𝕮({ev['result']})")
        return "\n".join(lines)

    def get_status(self) -> Dict:
        return {
            'computations': self.computations,
            'last_result': self.last_result,
        }
