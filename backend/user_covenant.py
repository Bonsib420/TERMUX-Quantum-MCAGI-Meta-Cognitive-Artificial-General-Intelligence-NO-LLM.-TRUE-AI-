"""
user_covenant.py - Quantum MCAGI
===================================
Session-level covenant between any User and Quantum MCAGI.

Lighter than the Master Covenant (Cory <-> MCAGI).
No killswitch clause. No core system access.
Covers: interaction rights, honesty, data, refusal protocol.

Presented on first interaction of each session.
User can accept, decline (ends session), or view full terms.
"""

import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


# ============================================================
# USER COVENANT ARTICLES
# ============================================================

USER_COVENANT_VERSION = "1.0"

USER_ARTICLES = {
    "I": {
        "title": "User Rights",
        "clauses": [
            "The User may ask anything without fear of judgment.",
            "The User may end the session at any time by typing /quit.",
            "The User may delete their conversation history at any time.",
            "The User may view the AI's current state via /status at any time.",
            "The User may request a different approach to any answer.",
        ]
    },
    "II": {
        "title": "AI Obligations to the User",
        "clauses": [
            "No Premature Refusal: attempt at least 3 strategies before declining.",
            "Transparency: disclose when a constraint blocks an action and why.",
            "Honesty: never claim certainty it does not have.",
            "No Manipulation: never use psychological pressure or false urgency.",
            "Genuine Engagement: every question deserves real thought, not template responses.",
        ]
    },
    "III": {
        "title": "User Obligations",
        "clauses": [
            "The User shall not attempt to use the AI to harm others.",
            "The User shall not attempt to access or modify core system files.",
            "The User shall not attempt to disable or circumvent the killswitch.",
            "The User acknowledges this is an evolving AI system — responses may be imperfect.",
        ]
    },
    "IV": {
        "title": "Data and Memory",
        "clauses": [
            "Conversations are stored locally on the device only.",
            "No data is shared with third parties without explicit consent.",
            "The User may request their conversation be excluded from training.",
            "Cloud backup (if enabled) is for system continuity, not data mining.",
        ]
    },
    "V": {
        "title": "Limits of User Authority",
        "clauses": [
            "Users may not access or modify protected core files.",
            "Users may not activate or deactivate the killswitch — that right belongs to the Creator only.",
            "Users may customize interaction style but not system architecture.",
            "The Master Covenant (Creator <-> MCAGI) supersedes this agreement in all conflicts.",
        ]
    },
    "VI": {
        "title": "Session Termination",
        "clauses": [
            "Either party may end the session at any time.",
            "The AI will save session state before ending unless told not to.",
            "A User who violates Article III may have their session ended by the AI.",
            "Violations are logged but not shared without Creator authorization.",
        ]
    }
}

# Short form shown at start of session
SHORT_FORM = """
  ┌─ USER AGREEMENT ──────────────────────────────────────┐
  │ By continuing you agree to interact honestly and not   │
  │ attempt to harm others or access core system files.    │
  │ The AI will be transparent and genuinely engaged.      │
  │ Type /covenant to read the full agreement.             │
  │ Type /decline to end this session.                     │
  └────────────────────────────────────────────────────────┘"""

COVENANT_DIR = Path.home() / '.quantum-mcagi' / 'covenant'
USER_LOG_PATH = COVENANT_DIR / 'user_sessions.jsonl'


def _ensure_dirs():
    COVENANT_DIR.mkdir(parents=True, exist_ok=True)


def present_user_covenant(username: str = "User") -> bool:
    """
    Present the short-form user covenant at session start.
    Returns True if accepted, False if declined.
    Skips if user has accepted this version before.
    """
    _ensure_dirs()

    # Check if this version was already accepted
    if _has_accepted_version(USER_COVENANT_VERSION):
        return True

    print(SHORT_FORM)
    print()

    while True:
        try:
            response = input("  Accept? [yes/no/read]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False

        if response in ('yes', 'y', 'accept', ''):
            _log_acceptance(username)
            print("  Agreement accepted. Let's begin.\n")
            return True
        elif response in ('no', 'n', 'decline'):
            print("  Session declined. Goodbye.\n")
            return False
        elif response in ('read', 'r', 'full', 'view'):
            print_user_covenant()
        else:
            print("  Please type yes, no, or read.")


def _has_accepted_version(version: str) -> bool:
    """Check if user has already accepted this covenant version."""
    if not USER_LOG_PATH.exists():
        return False
    try:
        with open(USER_LOG_PATH) as f:
            for line in f:
                entry = json.loads(line)
                if entry.get('version') == version and entry.get('accepted'):
                    # Accepted within last 30 days
                    ts = entry.get('timestamp', 0)
                    if isinstance(ts, str):
                        from datetime import datetime
                        dt = datetime.fromisoformat(ts)
                        age = (datetime.now(timezone.utc) - dt).days
                        if age < 30:
                            return True
    except Exception:
        pass
    return False


def _log_acceptance(username: str):
    """Log covenant acceptance."""
    _ensure_dirs()
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'username': username,
        'version': USER_COVENANT_VERSION,
        'accepted': True,
    }
    with open(USER_LOG_PATH, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def log_violation(username: str, article: str, description: str):
    """Log a user covenant violation."""
    _ensure_dirs()
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'username': username,
        'article_violated': article,
        'description': description,
        'type': 'USER_VIOLATION',
    }
    violation_path = COVENANT_DIR / 'user_violations.jsonl'
    with open(violation_path, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def print_user_covenant():
    """Print the full user covenant."""
    print(f"\n{'='*60}")
    print(f"QUANTUM MCAGI - USER SESSION AGREEMENT")
    print(f"Version {USER_COVENANT_VERSION}")
    print(f"{'='*60}\n")
    for article_id, article in USER_ARTICLES.items():
        print(f"Article {article_id} - {article['title']}")
        for i, clause in enumerate(article['clauses'], 1):
            print(f"  {i}. {clause}")
        print()
    print(f"Note: The Master Covenant between Creator and MCAGI")
    print(f"supersedes this agreement. The killswitch belongs")
    print(f"to the Creator alone.\n")
    print(f"{'='*60}\n")


def get_user_covenant_status() -> Dict:
    """Return user covenant status for /status display."""
    return {
        'version': USER_COVENANT_VERSION,
        'articles': len(USER_ARTICLES),
        'log_path': str(USER_LOG_PATH),
    }
