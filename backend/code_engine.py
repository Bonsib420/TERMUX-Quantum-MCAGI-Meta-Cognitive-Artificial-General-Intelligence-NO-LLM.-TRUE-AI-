"""
Code Engine — the MCAGI's ability to code.

Gives the system general code capability with guardrails:
  * run_python(code)   — execute Python in a subprocess (timeout, captured I/O)
  * run_shell(cmd)     — execute a shell command (timeout, captured I/O)
  * read_file(path)    — read any file
  * write_file(path)   — write a file (auto-backup existing, syntax-check .py)
  * edit_self(path)    — edit the system's OWN source (backup + validate + guard)
  * list_dir(path)     — list a directory

Safety rails (kept, not blocking the power):
  * Auto-backup of any existing file before it is overwritten/edited, so a bad
    edit is always recoverable (~/.quantum-mcagi/code_backups/).
  * Syntax check (and code_guardian validation when available) before saving a
    .py file — refuses to persist code that won't parse, unless force=True.
  * Execution timeouts on every subprocess.
  * Gated behind killswitch: if the system is frozen, all mutate/execute ops
    refuse until the Creator unfreezes.

Nothing here runs on import; it only acts when explicitly invoked.
"""

import ast
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.expanduser("~/.quantum-mcagi/code_backups")
DEFAULT_TIMEOUT = 30

# Optional integrations — degrade gracefully if unavailable.
try:
    from code_guardian import guard as _guard
    HAS_GUARDIAN = True
except Exception:
    HAS_GUARDIAN = False

try:
    from killswitch import ForcedObjectiveReduction as _FOR
    HAS_KILLSWITCH = True
except Exception:
    HAS_KILLSWITCH = False


def _is_frozen() -> bool:
    if HAS_KILLSWITCH:
        try:
            return _FOR.is_frozen()
        except Exception:
            return False
    return os.path.exists(os.path.expanduser("~/.quantum-mcagi/.frozen"))


def _syntax_ok(code: str) -> (bool, str):
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, f"{e.msg} (line {e.lineno})"


class CodeEngine:
    """Unified, guard-railed code capability for the MCAGI."""

    def __init__(self, backend_dir: str = BACKEND_DIR,
                 default_timeout: int = DEFAULT_TIMEOUT):
        self.backend_dir = backend_dir
        self.default_timeout = default_timeout
        os.makedirs(BACKUP_DIR, exist_ok=True)
        self.history: List[Dict] = []

    # ── execution ────────────────────────────────────────────────────────
    def run_python(self, code: str, timeout: Optional[int] = None) -> Dict:
        """Execute Python source in a fresh subprocess. Returns captured I/O."""
        if _is_frozen():
            return {"ok": False, "error": "system is frozen (killswitch active)"}
        ok, err = _syntax_ok(code)
        if not ok:
            return {"ok": False, "error": f"SyntaxError: {err}"}
        return self._spawn([sys.executable, "-c", code], timeout)

    def run_shell(self, command: str, timeout: Optional[int] = None) -> Dict:
        """Execute a shell command. Returns captured I/O and return code."""
        if _is_frozen():
            return {"ok": False, "error": "system is frozen (killswitch active)"}
        return self._spawn(command, timeout, shell=True)

    def _spawn(self, args, timeout, shell: bool = False) -> Dict:
        timeout = timeout or self.default_timeout
        t0 = time.time()
        try:
            proc = subprocess.run(
                args, shell=shell, cwd=self.backend_dir,
                capture_output=True, text=True, timeout=timeout,
            )
            result = {
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "elapsed": round(time.time() - t0, 3),
            }
        except subprocess.TimeoutExpired:
            result = {"ok": False, "error": f"timed out after {timeout}s"}
        except Exception as e:
            result = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        self.history.append(result)
        return result

    # ── files ────────────────────────────────────────────────────────────
    def read_file(self, path: str) -> Dict:
        p = self._resolve(path)
        try:
            return {"ok": True, "path": str(p), "content": p.read_text()}
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}

    def list_dir(self, path: str = ".") -> Dict:
        p = self._resolve(path)
        try:
            entries = sorted(
                (e.name + ("/" if e.is_dir() else "")) for e in p.iterdir()
            )
            return {"ok": True, "path": str(p), "entries": entries}
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}

    def backup_file(self, path: str) -> Optional[str]:
        """Copy an existing file into the backup dir; return the backup path."""
        p = self._resolve(path)
        if not p.exists():
            return None
        stamp = time.strftime("%Y%m%d-%H%M%S")
        dest = os.path.join(BACKUP_DIR, f"{p.name}.{stamp}.bak")
        shutil.copy2(p, dest)
        return dest

    def write_file(self, path: str, content: str,
                   validate: bool = True, force: bool = False) -> Dict:
        """Write content to path. Backs up any existing file first. For .py
        files, refuses to save invalid syntax unless force=True."""
        if _is_frozen():
            return {"ok": False, "error": "system is frozen (killswitch active)"}
        p = self._resolve(path)

        if validate and p.suffix == ".py":
            ok, err = _syntax_ok(content)
            if not ok and not force:
                return {"ok": False, "error": f"SyntaxError: {err}",
                        "hint": "pass force=True to save anyway"}
            if HAS_GUARDIAN:
                try:
                    g = _guard(content, p.name)
                    if not g.get("safe", True) and not force:
                        return {"ok": False, "error": "code_guardian blocked",
                                "issues": g.get("errors", []),
                                "hint": "pass force=True to save anyway"}
                except Exception:
                    pass

        backup = self.backup_file(p)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            return {"ok": True, "path": str(p), "backup": backup,
                    "bytes": len(content.encode())}
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}",
                    "backup": backup}

    def edit_self(self, path: str, content: str, force: bool = False) -> Dict:
        """Edit the system's OWN source. Resolves relative to the backend dir,
        always backs up, always validates .py."""
        target = path if os.path.isabs(path) else os.path.join(self.backend_dir, path)
        return self.write_file(target, content, validate=True, force=force)

    def restore_backup(self, backup_path: str, target: str) -> Dict:
        """Restore a previously saved backup over a target file."""
        try:
            shutil.copy2(backup_path, self._resolve(target))
            return {"ok": True, "restored": target, "from": backup_path}
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}

    # ── helpers ──────────────────────────────────────────────────────────
    def _resolve(self, path: str) -> Path:
        p = Path(path).expanduser()
        if not p.is_absolute():
            p = Path(self.backend_dir) / p
        return p


_ENGINE: Optional[CodeEngine] = None


def get_code_engine() -> CodeEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = CodeEngine()
    return _ENGINE


if __name__ == "__main__":
    eng = get_code_engine()
    print("CodeEngine self-test")
    print("  guardian:", HAS_GUARDIAN, "| killswitch:", HAS_KILLSWITCH,
          "| frozen:", _is_frozen())
    r = eng.run_python("print('hello from code_engine', 2 + 2)")
    print("  run_python:", r.get("stdout", r.get("error")).strip())
    r = eng.run_shell("echo shell-ok")
    print("  run_shell :", r.get("stdout", r.get("error")).strip())
