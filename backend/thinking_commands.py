"""
🧠 Thinking Mode Commands
===========================
Command parsing for thinking mode control.
"""

from typing import Dict, Optional


class ThinkingModeCommands:
    """User commands for controlling thinking mode."""

    COMMANDS = {
        "!thinking on": "Show internal thinking process",
        "!thinking off": "Hide internal thinking process",
        "!thinking status": "Check current thinking mode",
        "!research": "Force deep research on topic",
        "!memory": "Show what AI has learned",
        "!read": "Read and process uploaded file",
        "!link": "Download and process file from URL",
        "!docs": "List all uploaded documents",
        "!speak": "Convert text to speech (TTS)",
        "!imagine": "Generate an image from description",
        "!export": "Export conversation or memory",
        "!graph": "Show knowledge graph",
        "!characters": "Extract characters from book/document",
        "!timeline": "Generate timeline from document",
        "!worldbuilding": "Extract world/setting details",
        "!feedback": "Get writing feedback on document",
        "!help": "Show all available commands"
    }

    @staticmethod
    def parse_command(message: str) -> Optional[Dict]:
        """Check if message is a command. Supports both ! and / prefixes."""
        message_lower = message.lower().strip()

        # Existing ! commands
        if message_lower == "!thinking on":
            return {"command": "thinking_on"}
        elif message_lower == "!thinking off":
            return {"command": "thinking_off"}
        elif message_lower == "!thinking status":
            return {"command": "thinking_status"}
        elif message_lower.startswith("!research"):
            return {"command": "research", "topic": message[9:].strip()}
        elif message_lower == "!memory":
            return {"command": "memory"}
        elif message_lower.startswith("!read"):
            return {"command": "read_file", "filename": message[5:].strip()}
        elif message_lower.startswith("!link"):
            return {"command": "link", "url": message[5:].strip()}
        elif message_lower == "!docs":
            return {"command": "docs"}
        elif message_lower.startswith("!speak"):
            return {"command": "speak", "text": message[6:].strip()}
        elif message_lower.startswith("!imagine"):
            return {"command": "imagine", "prompt": message[8:].strip()}
        elif message_lower.startswith("!export"):
            return {"command": "export", "target": message[7:].strip() or "chat"}
        elif message_lower == "!graph":
            return {"command": "graph"}
        elif message_lower == "!characters":
            return {"command": "characters"}
        elif message_lower == "!timeline":
            return {"command": "timeline"}
        elif message_lower == "!worldbuilding":
            return {"command": "worldbuilding"}
        elif message_lower == "!feedback":
            return {"command": "feedback"}
        elif message_lower == "!help":
            return {"command": "help"}

        # Slash commands (from chat.py)
        elif message_lower.startswith("/cloud-save"):
            return {"command": "cloud_save"}
        elif message_lower.startswith("/cloud-status"):
            return {"command": "cloud_status"}
        elif message_lower.startswith("/cloud-load"):
            return {"command": "cloud_load"}
        elif message_lower == "/save":
            return {"command": "save"}
        elif message_lower == "/status":
            return {"command": "status"}
        elif message_lower.startswith("/explain"):
            query = message[8:].strip()
            return {"command": "explain_query", "query": query} if query else {"command": "explain_help"}
        elif message_lower.startswith("/knowledge"):
            topic = message[10:].strip() if len(message) > 10 else ""
            return {"command": "knowledge", "topic": topic}
        elif message_lower.startswith("/analyze"):
            text = message[8:].strip() if len(message) > 8 else ""
            return {"command": "analyze", "text": text}
        elif message_lower == "/personality":
            return {"command": "personality"}
        elif message_lower.startswith("/collapse"):
            # /collapse <text>
            text = message[9:].strip() if len(message) > 9 else ""
            return {"command": "collapse", "text": text}
        elif message_lower.startswith("/hybrid") or message_lower.startswith("/unified"):
            # These require specialized generators; we may not have them in server mode.
            # We'll handle gracefully.
            cmd_name = message[1:].split()[0] if len(message) > 2 else ""
            args = message[len(cmd_name)+2:].strip() if cmd_name else ""
            return {"command": cmd_name, "text": args}

        return None
