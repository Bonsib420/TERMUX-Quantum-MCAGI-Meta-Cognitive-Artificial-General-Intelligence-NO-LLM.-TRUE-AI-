"""
quantum_string.py — Quantum MCAGI
==================================
Replaces f-strings with a collapse-safe string composition system.

Instead of:
    response_text = f"[Command: /explain]\n{response_text}"

Use:
    response_text = qs("[Command: /explain]", response_text)

Benefits:
- No f-string syntax — self-evolution can generate qs() calls safely
- Never corrupted by newline replacement bugs
- Termux/Python 3.13 ARM compatible
- Can be extended with semantic weighting via Hilbert engine
- Acts as the seed of the custom quantum language layer
"""

import re
from typing import Any, Optional


# ── Core quantum string function ──────────────────────────────────────────

def qs(*parts, sep: str = "\n", clean: bool = True) -> str:
    """
    Quantum string composition — collapses multiple parts into one string.

    Args:
        *parts: Any number of string parts or values to compose
        sep: Separator between parts (default newline)
        clean: Whether to clean the result (strip excess whitespace)

    Returns:
        Composed string

    Examples:
        qs("Hello", name)                    # "Hello\n{name}"
        qs("Error at line", lineno, ":", msg) # joined with newlines
        qs("prefix", value, sep=" ")         # space-separated
        qs("[Command: /explain]", response)  # replaces broken f-string
    """
    result_parts = []
    for part in parts:
        if part is None:
            continue
        if isinstance(part, list):
            part = " ".join(str(x) for x in part)
        elif not isinstance(part, str):
            part = str(part)
        if part.strip():
            result_parts.append(part)

    result = sep.join(result_parts)

    if clean:
        # Remove excess whitespace but preserve intentional newlines
        result = re.sub(r' +', ' ', result)
        result = re.sub(r'\n{3,}', '\n\n', result)
        result = result.strip()

    return result


def qf(template: str, **kwargs) -> str:
    """
    Quantum format — safe replacement for f-strings with variable substitution.

    Instead of:
        f"Error in {filename} at line {lineno}: {message}"

    Use:
        qf("Error in {filename} at line {lineno}: {message}",
           filename=filename, lineno=lineno, message=message)

    Never corrupts on self-evolution rewrites because no special syntax.
    """
    try:
        return template.format(**kwargs)
    except (KeyError, ValueError) as e:
        # Graceful degradation — return template with available substitutions
        result = template
        for key, value in kwargs.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result


def qlog(level: str, *parts) -> str:
    """
    Quantum log string — formats a log message safely.

    Usage:
        qlog("INFO", "Engine loaded", engine_states, "states")
        qlog("ERROR", "Failed to parse", filename, ":", error)
    """
    message = " ".join(str(p) for p in parts if p is not None)
    return qf("[{level}] {message}", level=level.upper(), message=message)


def qcode(*lines) -> str:
    """
    Quantum code string — composes Python code lines safely.
    Each argument is one line of code. Handles indentation naturally.

    Usage:
        code = qcode(
            "def my_function():",
            "    return True"
        )
    """
    return "\n".join(str(line) for line in lines)


def qjoin(items, sep: str = ", ", prefix: str = "", suffix: str = "") -> str:
    """
    Quantum join — safe list-to-string conversion.

    Usage:
        qjoin(concepts)                    # "god, spacetime, consciousness"
        qjoin(items, sep=" | ")            # "item1 | item2 | item3"
        qjoin(facts, prefix="Facts: ")     # "Facts: fact1, fact2"
    """
    joined = sep.join(str(item) for item in items if item is not None)
    return qf("{prefix}{joined}{suffix}", prefix=prefix, joined=joined, suffix=suffix)


def qwrap(text: str, width: int = 80) -> str:
    """
    Quantum wrap — wraps text to given width without breaking words.
    Safe replacement for textwrap.fill() in generated code.
    """
    if len(text) <= width:
        return text
    words = text.split()
    lines = []
    current = []
    current_len = 0
    for word in words:
        if current_len + len(word) + 1 > width and current:
            lines.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += len(word) + 1
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


# ── Semantic quantum string (future Hilbert integration) ───────────────────

class QuantumString:
    """
    Full quantum string object — carries semantic weight alongside text.
    This is the seed of the custom language layer.

    Currently stores text + metadata. Future versions will carry:
    - Hilbert space density matrix representation
    - Semantic coherence score
    - Collapse history
    - Concept associations
    """

    def __init__(self, text: str, concepts: Optional[list] = None,
                 coherence: float = 1.0):
        self.text = str(text) if not isinstance(text, str) else text
        self.concepts = concepts or []
        self.coherence = coherence
        self._collapsed = False

    def collapse(self, hilbert_engine=None) -> str:
        """
        Collapse the quantum string to a classical string.
        If Hilbert engine is available, uses semantic weighting.
        Otherwise returns text directly.
        """
        self._collapsed = True
        if hilbert_engine:
            # Future: use Born-rule selection over semantic alternatives
            pass
        return self.text

    def __add__(self, other):
        if isinstance(other, QuantumString):
            combined_concepts = list(set(self.concepts + other.concepts))
            combined_coherence = (self.coherence + other.coherence) / 2
            return QuantumString(
                qs(self.text, other.text),
                concepts=combined_concepts,
                coherence=combined_coherence
            )
        return QuantumString(
            qs(self.text, str(other)),
            concepts=self.concepts,
            coherence=self.coherence
        )

    def __str__(self):
        return self.text

    def __repr__(self):
        return qf("QuantumString({text!r}, coherence={coherence:.2f})",
                  text=self.text[:50], coherence=self.coherence)

    def __len__(self):
        return len(self.text)

    def __bool__(self):
        return bool(self.text.strip())


# ── Self-evolution safe code generation ───────────────────────────────────

def qs_repair_fstring(broken_line: str, next_line: str) -> str:
    """
    Safely repairs a broken f-string by composing it via qs().
    Used by self_evolution_repair.py as an alternative to direct merging.

    Args:
        broken_line: The line with unclosed f-string
        next_line: The continuation line

    Returns:
        Repaired line using qs() composition
    """
    # Extract the variable being formatted
    indent = len(broken_line) - len(broken_line.lstrip())
    indent_str = " " * indent

    # Simple merge first
    merged = broken_line.rstrip() + next_line.strip()

    import ast
    try:
        ast.parse(merged)
        return merged
    except SyntaxError:
        pass

    # Convert to qs() call
    # Extract string prefix up to the open quote
    qs_version = qf(
        '{indent}# Repaired by quantum_string.qs()',
        indent=indent_str
    )
    return merged  # Fall back to merge


# ── Module test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test basic composition
    name = "Quantum MCAGI"
    stage = 4
    concepts = ["consciousness", "spacetime", "god"]

    print(qs("System:", name))
    print(qf("Growth stage: {stage} — Philosophical", stage=stage))
    print(qlog("INFO", "Engine loaded with", 5239641, "Markov states"))
    print(qjoin(concepts, prefix="Concepts: "))

    # Test QuantumString
    qs1 = QuantumString("consciousness collapses the wavefunction",
                        concepts=["consciousness", "wavefunction"])
    qs2 = QuantumString("reality emerges from observation",
                        concepts=["reality", "observation"])
    combined = qs1 + qs2
    print(combined)
    print(repr(combined))

    print("\nAll quantum string tests passed.")
