"""
chat_support.py — Quantum MCAGI
=================================
Lightweight chat support utilities.
Replaces: chat_helpers.py, chat_models.py, thinking_commands.py

All conversation history and session persistence is handled by memory.py.
This module provides thinking mode control and response formatting only.
"""

from typing import Dict, Optional, List
from datetime import datetime, timezone


# ── Thinking mode ─────────────────────────────────────────────────────────

class ThinkingMode:
    """Controls verbose thinking output during response generation."""

    def __init__(self):
        self.enabled = False
        self.show_concepts = True
        self.show_collapse = True
        self.show_timing = True

    def enable(self):
        self.enabled = True
        print("  [THINKING] Internal reasoning visible")

    def disable(self):
        self.enabled = False
        print("  [THINKING] Internal reasoning hidden")

    def toggle(self):
        if self.enabled:
            self.disable()
        else:
            self.enable()

    def status(self) -> str:
        return "ON" if self.enabled else "OFF"

    def handle_command(self, cmd: str) -> Optional[str]:
        """
        Handle thinking mode commands.
        Returns response string or None if not a thinking command.
        """
        cmd_lower = cmd.strip().lower()
        if cmd_lower in ('!thinking on', '/thinking on'):
            self.enable()
            return "Thinking mode: ON"
        elif cmd_lower in ('!thinking off', '/thinking off'):
            self.disable()
            return "Thinking mode: OFF"
        elif cmd_lower in ('!thinking', '!thinking status', '/thinking'):
            return f"Thinking mode: {self.status()}"
        return None


# ── Response formatting ────────────────────────────────────────────────────

def format_for_copy(response: str, width: int = 60) -> str:
    """Format a response in a bordered box for easy copying."""
    border = "─" * width
    lines = [f"  ╔{border}╗"]
    for line in response.split('\n'):
        while len(line) > width - 2:
            lines.append(f"  ║ {line[:width-2]} ║")
            line = line[width-2:]
        lines.append(f"  ║ {line:<{width-2}} ║")
    lines.append(f"  ╚{border}╝")
    return '\n'.join(lines)


def format_export_header(conversations: List[Dict], title: str = "Quantum MCAGI Export") -> str:
    """Format a markdown export header."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    return (
        f"# {title}\n"
        f"**Exported:** {now}\n"
        f"**Interactions:** {len(conversations)}\n"
        f"**System:** Quantum MCAGI — No LLM. Real algorithms. True AI.\n\n"
        f"> This conversation is from Quantum MCAGI, a system built on\n"
        f"> Penrose-Hameroff Orchestrated Objective Reduction (Orch OR),\n"
        f"> operating without any LLM dependencies.\n\n---\n"
    )


def format_math_response(result: Dict) -> str:
    """Format a math engine result for display."""
    if not result:
        return "No result"
    output = []
    if 'result' in result:
        output.append(f"  = {result['result']}")
    if 'steps' in result:
        for step in result['steps']:
            output.append(f"  {step}")
    if 'cistercian' in result:
        output.append(f"  Cistercian: {result['cistercian']}")
    return '\n'.join(output) if output else str(result)


# ── Session stats ──────────────────────────────────────────────────────────

def get_session_summary(memory) -> Dict:
    """Get a summary of the current session."""
    return {
        'total_interactions': len(getattr(memory, 'conversations', [])),
        'lifetime_interactions': memory.session_state.get('total_lifetime_interactions', 0) if hasattr(memory, 'session_state') else 0,
        'total_sessions': memory.session_state.get('total_sessions', 0) if hasattr(memory, 'session_state') else 0,
        'concepts': len(getattr(memory, 'concepts', {})),
        'growth_stage': memory.growth.get('stage', 0) if hasattr(memory, 'growth') else 0,
    }


# ── Singleton ──────────────────────────────────────────────────────────────

_thinking_mode = None


def get_thinking_mode() -> ThinkingMode:
    global _thinking_mode
    if _thinking_mode is None:
        _thinking_mode = ThinkingMode()
    return _thinking_mode
