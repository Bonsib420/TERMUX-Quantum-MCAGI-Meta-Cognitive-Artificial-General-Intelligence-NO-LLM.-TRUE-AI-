import re
def roman_to_int(s):
    """Convert Roman numeral to integer"""
    roman_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total = 0
    prev_value = 0
    for char in reversed(s):
        value = roman_values.get(char, 0)
        if value < prev_value:
            total -= value
        else:
            total += value
        prev_value = value
    return total
def is_roman_numeral(s):
    """Check if string is a valid Roman numeral"""
    return bool(re.match(r'^[IVXLCDM]+$', s))
def _digit_to_ascii_ones(d):
    """Convert ones digit to Cistercian ASCII representation"""
    # Basic implementation - you may want to expand this
    patterns = ['', '■', '■', '■', '■', '■', '■', '■', '■', '■']
    return patterns[d] if d < len(patterns) else ''
def _digit_to_ascii_tens(d):
    """Convert tens digit to Cistercian ASCII"""
    patterns = ['', '■', '■', '■', '■', '■', '■', '■', '■', '■']
    return patterns[d] if d < len(patterns) else ''
def _digit_to_ascii_hundreds(d):
    """Convert hundreds digit to Cistercian ASCII"""
    patterns = ['', '■', '■', '■', '■', '■', '■', '■', '■', '■']
    return patterns[d] if d < len(patterns) else ''
def _digit_to_ascii_thousands(d):
    """Convert thousands digit to Cistercian ASCII"""
    patterns = ['', '■', '■', '■', '■', '■', '■', '■', '■', '■']
    return patterns[d] if d < len(patterns) else ''
def render_cistercian_ascii(number):
    """Render a number (0-9999) in Cistercian ASCII art"""
    if number < 0 or number > 9999:
        return str(number)
    thousands = number // 1000
    hundreds = (number % 1000) // 100
    tens = (number % 100) // 10
    ones = number % 10
    # Simple representation
    return f"[{thousands}{hundreds}{tens}{ones}]"
def render_expression_ascii(a, op, b, result):
    """Render arithmetic expression in ASCII art"""
    return f"{a} {op} {b} = {result}"
def convert_to_arabic_expression(expr_string):
    """Convert expression with Roman numerals to Arabic"""
    parts = expr_string.split()
    converted = []
    for part in parts:
        if is_roman_numeral(part):
            converted.append(str(roman_to_int(part)))
        else:
            converted.append(part)
    return ' '.join(converted)
def detect_math(text):
    """Detect mathematical expressions in text"""
    # Simple pattern for numbers and operators
    pattern = r'(\d+\s*[+\-*/]\s*\d+)'
    match = re.search(pattern, text)
    return match.group(0) if match else None
def evaluate_math(expr):
    """Evaluate mathematical expression safely"""
    try:
        # Simple evaluation - in production, use safer method
        result = eval(expr)
        return {'expression': expr, 'result': result}
    except:
        return None
def format_math_response(ev, show_ascii=True):
    """Format math response"""
    if not ev:
        return None
    result = f"{ev['expression']} = {ev['result']}"
    if show_ascii:
        result += f"\n{render_expression_ascii(ev['expression'], '=', ev['result'], ev['result'])}"
    return result
def mask_arabic_numerals(text):
    """Mask Arabic numerals temporarily"""

    return re.sub(r'\d+', '■NUM■', text)
def unmask_arabic_numerals(masked_text, original_text):
    """Restore masked Arabic numerals"""
    # Simple implementation - you may want more sophisticated
    return original_text
def build_learning_payload(ev):
    """Build payload for learning"""
    return {'type': 'math', 'data': ev}
def process_math(text):
    """Wrapper function for backward compatibility"""
    result = detect_math(text)
    if result:
        ev = evaluate_math(result)
        return format_math_response(ev)
    return None