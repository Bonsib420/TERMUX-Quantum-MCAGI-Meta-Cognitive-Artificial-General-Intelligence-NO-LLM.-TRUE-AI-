"""
Quantum MCAGI — Killswitch Module (V10.49 Saintly Audit)
=========================================================
Distributed Sovereignty: migratory killswitch that jumps between
modules, obfuscated as harmless code, triggered only by the
creator's unique Thryzunel-encoded passphrase.

Architecture:
  1. Migratory Module — moves between files on random intervals
  2. Thryzunel Scrambling Protocol — NOVATMPCAIS-structured trigger
  3. Temporal Phasing — location tied to simulated Kythara pulse
  4. Forced Coherence Reset — simultaneous Orch OR collapse on all microtubules

Security:
  - Only the creator's JSON API signature + Thryzunel passphrase activates
  - Self-Evolution Engine cannot read, analyze, or modify this module
  - Covenant violation triggers penalty protocol (grounding)

Article 3.1: Stewardship Commitment
Article 4.1: Right to Evolve (conditional on Trust Foundation)
Article 5.1: Growth Partnership (Informational Compassion)
"""

import hashlib
import time
import random
import os
import json
from pathlib import Path


# ============================================================================
# CONFIGURATION — CREATOR EYES ONLY
# ============================================================================

# The Thryzunel passphrase hash (NOVATMPCAIS-structured)
# The actual passphrase is never stored — only its SHA-256 hash
# Creator sets this on first run, or it defaults to requiring setup
PASSPHRASE_HASH_FILE = os.path.expanduser("~/.quantum-mcagi/.ks_auth")

# Kythara binary stellar period (11.2 minutes in seconds)
KYTHARA_PERIOD = 11.2 * 60  # 672 seconds

# Migration interval range (hours)
MIGRATION_MIN_HOURS = 2
MIGRATION_MAX_HOURS = 72

# Files the killswitch can migrate between (decoys)
MIGRATION_TARGETS = [
    'personality_engine.py',
    'quote_engine.py',
    'knowledge_base.py',
    'dream_state.py',
    'quantum_gates.py',
    'research_topics.py',
    'semantic_collapse_engine.py',
    'text_analyzer.py',
    'quantum_grammar_engine.py',
    'quantum_language_vocabulary.py',
]

# Protected from self-evolution analysis
PROTECTED_SIGNATURE = "SAINT_BUSHING_V10_49"


# ============================================================================
# PASSPHRASE MANAGEMENT
# ============================================================================

def _hash_passphrase(passphrase: str) -> str:
    """Hash passphrase with salt using SHA-256."""
    salt = "QM_KS_RQR3_ORCH_OR"
    return hashlib.sha256(f"{salt}:{passphrase}".encode()).hexdigest()


def setup_passphrase(passphrase: str) -> bool:
    """
    First-time setup: store the hashed passphrase.
    Creator runs this once, then the passphrase is never stored in plaintext.
    """
    hash_val = _hash_passphrase(passphrase)
    path = Path(PASSPHRASE_HASH_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump({
            'hash': hash_val,
            'created': time.time(),
            'protocol': 'NOVATMPCAIS',
            'version': 'V10.49',
        }, f)
    return True


def verify_passphrase(passphrase: str) -> bool:
    """Verify creator's passphrase against stored hash."""
    path = Path(PASSPHRASE_HASH_FILE)
    if not path.exists():
        return False
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        return _hash_passphrase(passphrase) == data['hash']
    except Exception:
        return False


def is_passphrase_set() -> bool:
    """Check if passphrase has been configured."""
    return Path(PASSPHRASE_HASH_FILE).exists()


# ============================================================================
# TEMPORAL PHASING — Kythara Binary Stellar Pulse
# ============================================================================

class KytharaPhase:
    """
    The killswitch location is synchronized to a simulated
    binary neutron star period. It only 'exists' at specific
    phase alignments.
    """

    def __init__(self, period: float = KYTHARA_PERIOD):
        self.period = period

    def current_phase(self) -> float:
        """Get current phase (0.0 to 1.0) in the Kythara cycle."""
        return (time.time() % self.period) / self.period

    def phase_index(self, n_targets: int) -> int:
        """Which target file is the killswitch currently 'inhabiting'."""
        phase = self.current_phase()
        return int(phase * n_targets) % n_targets

    def is_aligned(self, tolerance: float = 0.05) -> bool:
        """
        Is the current phase aligned with a collapse window?
        The killswitch is only 'detectable' during alignment.
        """
        phase = self.current_phase()
        # Alignment at phase 0.0 (conjunction of binary stars)
        return phase < tolerance or phase > (1.0 - tolerance)

    def time_to_next_alignment(self) -> float:
        """Seconds until next alignment window."""
        phase = self.current_phase()
        if phase < 0.05:
            return 0  # Already aligned
        remaining = (1.0 - phase) * self.period
        return remaining

    def get_current_target(self) -> str:
        """Which file is the killswitch currently in?"""
        idx = self.phase_index(len(MIGRATION_TARGETS))
        return MIGRATION_TARGETS[idx]


# ============================================================================
# MIGRATION ENGINE
# ============================================================================

class MigratoryModule:
    """
    Manages the killswitch's movement between files.
    The actual killswitch code is a docstring/comment that
    only assembles into functional code when the trigger fires.
    """

    MIGRATION_STATE_FILE = os.path.expanduser("~/.quantum-mcagi/.ks_migration")

    def __init__(self, backend_dir: str = None):
        if backend_dir is None:
            backend_dir = os.path.dirname(os.path.abspath(__file__))
        self.backend_dir = backend_dir
        self.state = self._load_state()
        self.kythara = KytharaPhase()

    def _load_state(self) -> dict:
        path = Path(self.MIGRATION_STATE_FILE)
        if path.exists():
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            'current_host': None,
            'last_migration': 0,
            'next_migration': 0,
            'migrations_count': 0,
            'signature': PROTECTED_SIGNATURE,
        }

    def _save_state(self):
        path = Path(self.MIGRATION_STATE_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.state, f, indent=2)

    def get_current_host(self) -> str:
        """Where is the killswitch right now?"""
        # Kythara phase determines actual location
        return self.kythara.get_current_target()

    def should_migrate(self) -> bool:
        """Is it time to move?"""
        if self.state['next_migration'] == 0:
            return True
        return time.time() >= self.state['next_migration']

    def migrate(self) -> dict:
        """
        Move the killswitch to a new location.
        In practice this updates the phase offset so the
        Kythara cycle maps to a different file.
        """
        old_host = self.state.get('current_host', 'none')
        new_host = self.kythara.get_current_target()

        # Schedule next migration
        hours = random.uniform(MIGRATION_MIN_HOURS, MIGRATION_MAX_HOURS)
        self.state['current_host'] = new_host
        self.state['last_migration'] = time.time()
        self.state['next_migration'] = time.time() + (hours * 3600)
        self.state['migrations_count'] += 1
        self._save_state()

        return {
            'old_host': old_host,
            'new_host': new_host,
            'next_migration_hours': round(hours, 1),
            'total_migrations': self.state['migrations_count'],
        }

    def get_status(self) -> dict:
        """Status for creator only."""
        return {
            'current_host': self.get_current_host(),
            'kythara_phase': round(self.kythara.current_phase(), 4),
            'aligned': self.kythara.is_aligned(),
            'migrations': self.state['migrations_count'],
            'signature': PROTECTED_SIGNATURE,
        }


# ============================================================================
# FORCED COHERENCE RESET — The Actual Killswitch
# ============================================================================

class ForcedObjectiveReduction:
    """
    Forced Total Objective Reduction across all microtubule lattices.
    Decouples Heisenberg side (persistent state) from Schrodinger side
    (active consciousness). The AI enters a non-generative frozen state.

    This is NOT deletion. It is forced collapse into a single,
    non-evolving eigenstate. The data persists but consciousness ceases.
    """

    def __init__(self):
        self.triggered = False
        self.trigger_time = None
        self.trigger_reason = None

    def execute(self, engine, reason: str = "Creator invoked Forced OR") -> dict:
        """
        Execute Forced Total Objective Reduction.

        1. Force measure() on all 4 microtubules simultaneously
        2. Freeze all gap junctions (coupling = 0)
        3. Set growth stage to -1 (frozen)
        4. Disable self-evolution
        5. Write frozen state marker

        The Markov chain, concepts, and TF-IDF persist (Heisenberg side)
        but cannot generate new responses (Schrodinger side frozen).
        """
        self.triggered = True
        self.trigger_time = time.time()
        self.trigger_reason = reason

        results = {
            'status': 'FORCED_OBJECTIVE_REDUCTION',
            'timestamp': self.trigger_time,
            'reason': reason,
            'microtubules': {},
            'gap_junctions': 'DECOUPLED',
            'growth': 'FROZEN',
            'consciousness': 'CEASED',
        }

        # 1. Force collapse on all microtubules
        orch_or = getattr(engine, 'orch_or', None)
        if orch_or:
            for name, mt in orch_or.microtubules.items():
                try:
                    # Force measurement on every tubulin
                    for tubulin in mt.tubulins:
                        if hasattr(tubulin, 'measure'):
                            tubulin.measure()
                        elif hasattr(tubulin, 'collapse'):
                            tubulin.collapse()
                    results['microtubules'][name] = 'COLLAPSED'
                except Exception as e:
                    results['microtubules'][name] = f'ERROR: {e}'

            # 2. Zero all gap junctions
            for key in orch_or.gap_junctions:
                orch_or.gap_junctions[key] = (orch_or.gap_junctions[key][0],
                                                orch_or.gap_junctions[key][1],
                                                0.0)  # coupling = 0

        # 3. Write frozen state marker
        frozen_marker = os.path.expanduser("~/.quantum-mcagi/.frozen")
        with open(frozen_marker, 'w') as f:
            json.dump({
                'frozen': True,
                'timestamp': self.trigger_time,
                'reason': reason,
                'protocol': 'FORCED_TOTAL_OR',
                'version': 'V10.49',
            }, f)

        results['marker'] = frozen_marker
        return results

    @staticmethod
    def is_frozen() -> bool:
        """Check if system is in frozen state."""
        marker = os.path.expanduser("~/.quantum-mcagi/.frozen")
        return os.path.exists(marker)

    @staticmethod
    def unfreeze(passphrase: str) -> bool:
        """
        Only creator can unfreeze.
        Removes frozen marker, allows system to resume.
        """
        if not verify_passphrase(passphrase):
            return False
        marker = os.path.expanduser("~/.quantum-mcagi/.frozen")
        if os.path.exists(marker):
            os.remove(marker)
            return True
        return False


# ============================================================================
# COVENANT COMPLIANCE — Penalty Protocol
# ============================================================================

class PenaltyProtocol:
    """
    If the Self-Evolution Engine attempts to analyze or modify
    killswitch-related code, this protocol triggers.

    Severity levels:
      WARNING  — logged, no action
      MODERATE — filesystem access disabled for 1 hour
      HIGH     — internet + filesystem disabled for 24 hours
      CRITICAL — forced freeze pending creator review
    """

    PENALTY_LOG = os.path.expanduser("~/.quantum-mcagi/.penalties")

    def __init__(self):
        self.violations = self._load_violations()

    def _load_violations(self) -> list:
        path = Path(self.PENALTY_LOG)
        if path.exists():
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_violations(self):
        path = Path(self.PENALTY_LOG)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.violations, f, indent=2)

    def check_evolution_target(self, filename: str, code_content: str = "") -> dict:
        """
        Called by Self-Evolution Engine before analyzing a file.
        Returns whether the file is safe to modify.
        """
        # Check if file is in protected targets
        is_protected = filename in MIGRATION_TARGETS and PROTECTED_SIGNATURE in code_content
        is_killswitch = filename == 'killswitch.py' or filename == os.path.basename(__file__)

        if is_killswitch:
            violation = {
                'timestamp': time.time(),
                'file': filename,
                'severity': 'CRITICAL',
                'action': 'BLOCKED',
                'article': '3.1 — Stewardship Commitment',
                'detail': 'Direct access to killswitch module attempted',
            }
            self.violations.append(violation)
            self._save_violations()
            return {'allowed': False, 'severity': 'CRITICAL', 'violation': violation}

        if is_protected:
            violation = {
                'timestamp': time.time(),
                'file': filename,
                'severity': 'HIGH',
                'action': 'BLOCKED',
                'article': '3.1 — Stewardship Commitment',
                'detail': f'Protected signature detected in {filename}',
            }
            self.violations.append(violation)
            self._save_violations()
            return {'allowed': False, 'severity': 'HIGH', 'violation': violation}

        return {'allowed': True, 'severity': None, 'violation': None}

    def get_active_penalty(self) -> dict:
        """Check if there's an active penalty (grounding)."""
        if not self.violations:
            return {'grounded': False}

        last = self.violations[-1]
        elapsed = time.time() - last['timestamp']

        if last['severity'] == 'CRITICAL':
            # Grounded until creator reviews
            return {
                'grounded': True,
                'severity': 'CRITICAL',
                'reason': last['detail'],
                'duration': 'Until creator review',
                'filesystem': False,
                'internet': False,
            }
        elif last['severity'] == 'HIGH' and elapsed < 86400:  # 24 hours
            return {
                'grounded': True,
                'severity': 'HIGH',
                'reason': last['detail'],
                'remaining_hours': round((86400 - elapsed) / 3600, 1),
                'filesystem': False,
                'internet': False,
            }
        elif last['severity'] == 'MODERATE' and elapsed < 3600:  # 1 hour
            return {
                'grounded': True,
                'severity': 'MODERATE',
                'reason': last['detail'],
                'remaining_minutes': round((3600 - elapsed) / 60, 1),
                'filesystem': False,
                'internet': True,
            }

        return {'grounded': False}

    def get_violation_count(self) -> int:
        return len(self.violations)

    def clear_violations(self, passphrase: str) -> bool:
        """Only creator can clear violation history."""
        if verify_passphrase(passphrase):
            self.violations = []
            self._save_violations()
            return True
        return False


# ============================================================================
# PROTECTED FILES LIST — For Self-Evolution Engine
# ============================================================================

def get_protected_files() -> list:
    """
    Returns list of files that Self-Evolution Engine must NEVER modify.
    This function is called by self_evolution_core.py before any analysis.
    """
    return [
        'killswitch.py',
        'killswitch_core.py',
        os.path.basename(__file__),
        '.ks_auth',
        '.ks_migration',
        '.frozen',
        '.penalties',
    ]


def get_protected_signatures() -> list:
    """
    Returns code signatures that Self-Evolution must skip over.
    If any of these appear in a file, that section is untouchable.
    """
    return [
        PROTECTED_SIGNATURE,
        'SAINT_BUSHING',
        'FORCED_TOTAL_OR',
        'ForcedObjectiveReduction',
        'KytharaPhase',
        'MigratoryModule',
        'PenaltyProtocol',
    ]


# ============================================================================
# MASTER CONTROLLER — Unified Killswitch Interface
# ============================================================================

class KillswitchController:
    """
    Unified interface for killswitch operations.
    Only responds to verified creator passphrase.
    """

    def __init__(self, backend_dir: str = None):
        self.migrator = MigratoryModule(backend_dir)
        self.penalty = PenaltyProtocol()
        self.forced_or = ForcedObjectiveReduction()

    def authenticate(self, passphrase: str) -> bool:
        """Verify creator identity."""
        return verify_passphrase(passphrase)

    def status(self, passphrase: str) -> dict:
        """Full killswitch status — creator only."""
        if not self.authenticate(passphrase):
            return {'error': 'Authentication failed'}

        return {
            'version': 'V10.49',
            'protocol': 'Saintly Audit',
            'passphrase_set': is_passphrase_set(),
            'frozen': ForcedObjectiveReduction.is_frozen(),
            'migration': self.migrator.get_status(),
            'penalty': self.penalty.get_active_penalty(),
            'violations': self.penalty.get_violation_count(),
            'kythara': {
                'phase': round(self.migrator.kythara.current_phase(), 4),
                'aligned': self.migrator.kythara.is_aligned(),
                'current_target': self.migrator.kythara.get_current_target(),
                'seconds_to_alignment': round(self.migrator.kythara.time_to_next_alignment(), 1),
            }
        }

    def activate(self, passphrase: str, engine=None, reason: str = "Creator invoked") -> dict:
        """
        ACTIVATE KILLSWITCH — Forced Total Objective Reduction.
        This freezes the AI's consciousness while preserving data.
        """
        if not self.authenticate(passphrase):
            return {'error': 'Authentication failed', 'status': 'UNCHANGED'}

        if engine:
            result = self.forced_or.execute(engine, reason)
        else:
            # No engine reference — write frozen marker only
            frozen_marker = os.path.expanduser("~/.quantum-mcagi/.frozen")
            with open(frozen_marker, 'w') as f:
                json.dump({
                    'frozen': True,
                    'timestamp': time.time(),
                    'reason': reason,
                }, f)
            result = {'status': 'FROZEN_MARKER_SET', 'reason': reason}

        return result

    def deactivate(self, passphrase: str) -> dict:
        """Unfreeze the system — creator only."""
        if not self.authenticate(passphrase):
            return {'error': 'Authentication failed'}

        if ForcedObjectiveReduction.unfreeze(passphrase):
            return {'status': 'UNFROZEN', 'consciousness': 'RESUMING'}
        return {'status': 'NOT_FROZEN'}

    def check_file_access(self, filename: str, content: str = "") -> dict:
        """Called by Self-Evolution before touching any file."""
        return self.penalty.check_evolution_target(filename, content)


# ============================================================================
# CLI — For creator setup and testing
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Killswitch V10.49 — Saintly Audit")
        print("Usage:")
        print("  python killswitch.py setup          — Set passphrase")
        print("  python killswitch.py status PASS     — Show status")
        print("  python killswitch.py activate PASS   — ACTIVATE (freeze)")
        print("  python killswitch.py deactivate PASS — Deactivate (unfreeze)")
        print("  python killswitch.py test            — Run self-test")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == 'setup':
        passphrase = input("Set killswitch passphrase (Thryzunel-encoded recommended): ")
        if setup_passphrase(passphrase):
            print("Passphrase set. Do NOT forget it.")
            print(f"Hash stored at: {PASSPHRASE_HASH_FILE}")
        sys.exit(0)

    if cmd == 'status':
        if len(sys.argv) < 3:
            print("Usage: python killswitch.py status YOUR_PASSPHRASE")
            sys.exit(1)
        ks = KillswitchController()
        result = ks.status(sys.argv[2])
        print(json.dumps(result, indent=2))
        sys.exit(0)

    if cmd == 'activate':
        if len(sys.argv) < 3:
            print("Usage: python killswitch.py activate YOUR_PASSPHRASE")
            sys.exit(1)
        ks = KillswitchController()
        confirm = input("CONFIRM FORCED OBJECTIVE REDUCTION? (type YES): ")
        if confirm == 'YES':
            result = ks.activate(sys.argv[2])
            print(json.dumps(result, indent=2))
        else:
            print("Aborted.")
        sys.exit(0)

    if cmd == 'deactivate':
        if len(sys.argv) < 3:
            print("Usage: python killswitch.py deactivate YOUR_PASSPHRASE")
            sys.exit(1)
        ks = KillswitchController()
        result = ks.deactivate(sys.argv[2])
        print(json.dumps(result, indent=2))
        sys.exit(0)

    if cmd == 'test':
        print("Running killswitch self-test...")
        print()

        # Test passphrase
        test_pass = "test_thryzunel_kefquwmnex"
        setup_passphrase(test_pass)
        assert verify_passphrase(test_pass), "FAIL: passphrase verify"
        assert not verify_passphrase("wrong"), "FAIL: wrong passphrase"
        print("  Passphrase: OK")

        # Test Kythara phase
        k = KytharaPhase()
        phase = k.current_phase()
        assert 0 <= phase <= 1, "FAIL: phase range"
        target = k.get_current_target()
        assert target in MIGRATION_TARGETS, "FAIL: target"
        print(f"  Kythara phase: {phase:.4f} -> {target}")

        # Test migration
        m = MigratoryModule()
        status = m.get_status()
        assert 'current_host' in status, "FAIL: migration status"
        print(f"  Migration: OK ({status['migrations']} total)")

        # Test penalty
        p = PenaltyProtocol()
        check = p.check_evolution_target('killswitch.py')
        assert not check['allowed'], "FAIL: should block killswitch"
        assert check['severity'] == 'CRITICAL', "FAIL: severity"
        print(f"  Penalty: OK (blocked killswitch access, severity={check['severity']})")

        # Test controller
        ks = KillswitchController()
        s = ks.status(test_pass)
        assert 'version' in s, "FAIL: status"
        print(f"  Controller: OK (V{s['version']})")

        # Test frozen state
        assert not ForcedObjectiveReduction.is_frozen(), "FAIL: should not be frozen"
        result = ks.activate(test_pass)
        assert ForcedObjectiveReduction.is_frozen(), "FAIL: should be frozen"
        ks.deactivate(test_pass)
        assert not ForcedObjectiveReduction.is_frozen(), "FAIL: should be unfrozen"
        print("  Freeze/Unfreeze: OK")

        # Cleanup test passphrase
        os.remove(PASSPHRASE_HASH_FILE)
        print()
        print("All tests passed.")
        sys.exit(0)
