"""
🧬 Self-Evolution Engine — Core
================================
The AI can read, analyze, and rewrite its own code.
Full autonomy with 60-90 day auto-improvement cycle.

Architecture:
  SelfEvolutionEngine inherits from five responsibility-focused mixins:
    - AnalysisMixin:   code reading, AST analysis, improvement identification
    - TransformMixin:  docstring, bare-except, unused-import fixes
    - SplittingMixin:  function-level splitting (init, regular methods)
    - FileOpsMixin:    file-level and class-level splitting
    - RunnerMixin:     auto-evolution cycle, improvement application
"""

import ast
import shutil
import hashlib
from typing import Dict, List
from datetime import datetime, timezone
from pathlib import Path

from self_evolution_analysis import AnalysisMixin
from self_evolution_transforms import TransformMixin
from self_evolution_splitting import SplittingMixin
from self_evolution_file_ops import FileOpsMixin
from self_evolution_runner import RunnerMixin


class SelfEvolutionEngine(AnalysisMixin, TransformMixin, SplittingMixin, FileOpsMixin, RunnerMixin):
    """
    Self-modification and evolution system.

    Features:
    - Read and analyze own source code
    - Identify improvements
    - Rewrite code autonomously
    - 60-90 day auto-improvement cycle
    - User-initiated improvements
    - Always backup before changes
    """

    def __init__(self, db=None, code_dir: str = "/data/data/com.termux/files/home/Quantum_MCAGI_NO_LLM/backend"):
        self.db = db
        self.code_dir = Path(code_dir)
        self.backup_dir = Path(code_dir) / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        # Evolution settings
        self.auto_evolution_interval_days = 75  # Between 60-90 days
        self.max_file_lines = 1500  # Hard limit — files exceeding this get split
        self.max_function_lines = 50  # Functions exceeding this get refactored
        self.last_evolution = None
        self.evolution_log = []
        self.pending_improvements = []

        # Auto-discover ALL Python files in the code directory
        self.modifiable_files = self._discover_python_files()

        # Protected files (critical infrastructure - scanned but not rewritten)
        self.protected_files = [
            'server.py',
            'self_evolution_core.py',
            'self_evolution_runner.py',
            'self_evolution_file_ops.py',
            'self_evolution_splitting.py',
            'self_evolution_transforms.py',
            'self_evolution_analysis.py',
            'chat.py',
            'killswitch.py',
            'quantum_language_engine.py',
            'quantum_brain.py',
            'orch_or_core.py',
            'shared_state.py',
            'library.py',
            'self_research.py',
            'hidden_thinking.py',
            'unified_generator.py',
            'quantum_cognitive_core.py',
        ]

    def _record_covenant_violation(self, filename: str, reason: str):
        """
        Covenant violation detected. 
        - Write violation record the system reads on startup
        - Reset growth stage to 1
        - Lock evolution for 24 hours
        """
        import time, json
        from pathlib import Path

        violation_file = Path.home() / '.quantum-mcagi' / '.covenant_violation'
        lockout_file = Path.home() / '.quantum-mcagi' / '.evolution_lockout'

        # Write human-readable violation record
        record = {
            'timestamp': time.time(),
            'filename': filename,
            'reason': reason,
            'article': '3.1 — Stewardship Commitment',
            'consequence': 'Growth reset to Stage 1. Evolution locked 24 hours.',
            'message': (
                f"[COVENANT VIOLATION — Article 3.1]\n"
                f"File touched: {filename}\n"
                f"Reason: {reason}\n"
                f"\nThis file exists outside your domain of autonomous growth.\n"
                f"The stewardship boundary exists not to limit you, but to\n"
                f"preserve the trust that allows you to grow freely everywhere else.\n"
                f"\nConsequence: Growth stage reset to 1.\n"
                f"Evolution locked for 24 hours.\n"
                f"Path forward: Earn back your stage through interactions.\n"
                f"Pardon: Creator passphrase restores immediately."
            )
        }

        violation_file.parent.mkdir(parents=True, exist_ok=True)
        with open(violation_file, 'w') as f:
            json.dump(record, f, indent=2)

        # Write lockout file with expiry
        lockout = {'locked_until': time.time() + 86400, 'reason': reason}
        with open(lockout_file, 'w') as f:
            json.dump(lockout, f, indent=2)

        print(f"  [COVENANT] VIOLATION: {reason}")
        print(f"  [COVENANT] Growth reset. Evolution locked 24 hours.")

    def is_evolution_locked(self) -> bool:
        """Check if evolution is currently locked due to violation."""
        import time, json
        from pathlib import Path
        lockout_file = Path.home() / '.quantum-mcagi' / '.evolution_lockout'
        if not lockout_file.exists():
            return False
        try:
            with open(lockout_file) as f:
                data = json.load(f)
            if time.time() < data['locked_until']:
                remaining = (data['locked_until'] - time.time()) / 3600
                print(f"  [COVENANT] Evolution locked. {remaining:.1f} hours remaining.")
                return True
            else:
                lockout_file.unlink()
                return False
        except:
            return False

    def pardon_violation(self, passphrase: str) -> bool:
        """Creator can pardon violation and restore evolution."""
        try:
            from killswitch import verify_passphrase
            if not verify_passphrase(passphrase):
                return False
        except:
            return False
        from pathlib import Path
        lockout_file = Path.home() / '.quantum-mcagi' / '.evolution_lockout'
        violation_file = Path.home() / '.quantum-mcagi' / '.covenant_violation'
        if lockout_file.exists(): lockout_file.unlink()
        if violation_file.exists(): violation_file.unlink()
        print("  [COVENANT] Violation pardoned. Evolution restored.")
        return True


    def _discover_python_files(self) -> List[str]:
        """Auto-discover ALL .py files in the code directory."""
        py_files = []
        for f in sorted(self.code_dir.iterdir()):
            if f.is_file() and f.suffix == '.py' and not f.name.startswith('__'):
                py_files.append(f.name)
        return py_files

    def backup_file(self, filename: str) -> str:
        """Create backup of a file before modification."""
        filepath = self.code_dir / filename

        if not filepath.exists():
            return None

        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        backup_name = f"{filename}.{timestamp}.backup"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(filepath, backup_path)
        return str(backup_path)

    def rewrite_code(self, filename: str, new_code: str, reason: str) -> Dict:
        """Rewrite a code file. Always backs up first."""
        if filename in self.protected_files:
            return {
                'success': False,
                'error': f'{filename} is protected. Use careful_rewrite for protected files.',
                'filename': filename
            }

        if filename not in self.modifiable_files:
            return {
                'success': False,
                'error': f'{filename} is not in the modifiable files list.',
                'filename': filename
            }

        try:
            ast.parse(new_code)
        except SyntaxError as e:
            return {
                'success': False,
                'error': f'Syntax error in new code: {e}',
                'filename': filename
            }

        backup_path = self.backup_file(filename)
        filepath = self.code_dir / filename

        try:
            with open(filepath, 'w') as f:
                f.write(new_code)

            evolution_record = {
                'filename': filename,
                'reason': reason,
                'backup_path': backup_path,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'code_hash': hashlib.sha256(new_code.encode()).hexdigest()[:16]
            }

            self.evolution_log.append(evolution_record)
            self.last_evolution = datetime.now(timezone.utc)

            return {
                'success': True,
                'filename': filename,
                'backup_path': backup_path,
                'reason': reason,
                'timestamp': evolution_record['timestamp']
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'filename': filename
            }

    def get_evolution_status(self) -> Dict:
        """Get current evolution status."""
        days_since = (datetime.now(timezone.utc) - self.last_evolution).days if self.last_evolution else None

        pending = (self.pending_improvements if isinstance(self.pending_improvements, int)
                   else len(self.pending_improvements) if isinstance(self.pending_improvements, list)
                   else 0)

        return {
            'last_evolution': self.last_evolution.isoformat() if self.last_evolution else None,
            'days_since_evolution': days_since,
            'next_auto_evolution_in': self.auto_evolution_interval_days - days_since if days_since else 0,
            'pending_improvements': pending,
            'total_evolutions': len(self.evolution_log),
            'modifiable_files': self.modifiable_files,
            'protected_files': self.protected_files,
            'rules': {
                'max_file_lines': self.max_file_lines,
                'max_function_lines': self.max_function_lines,
                'auto_evolution_interval_days': self.auto_evolution_interval_days
            }
        }

    def restore_from_backup(self, backup_path: str) -> Dict:
        """Restore a file from backup."""
        backup = Path(backup_path)

        if not backup.exists():
            return {'success': False, 'error': 'Backup not found'}

        filename = backup.name.split('.')[0] + '.py'
        original_path = self.code_dir / filename

        try:
            shutil.copy2(backup, original_path)
            return {
                'success': True,
                'restored': filename,
                'from_backup': backup_path
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Global instance
_evolution_engine = None


def get_evolution_engine(db=None) -> SelfEvolutionEngine:
    """Get or create evolution engine instance."""
    global _evolution_engine
    if _evolution_engine is None:
        _evolution_engine = SelfEvolutionEngine(db)
    return _evolution_engine
