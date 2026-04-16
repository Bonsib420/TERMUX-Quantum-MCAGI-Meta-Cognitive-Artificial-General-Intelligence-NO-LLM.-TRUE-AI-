"""
🔮 Rclone Cloud Provider — Google Drive sync for Quantum MCAGI

Uses rclone (https://rclone.org) to sync brain data between Termux and
Google Drive. This is the primary cloud sync method since rclone is already
configured and working on the user's Termux.

Cloud structure on Google Drive:
  QuantumMCAGI/
    state.json       — core memory (growth, concepts, session_state)
    brain.json        — full brain snapshot (research + dreams + concepts)
    shared/           — shared knowledge across instances
    users/            — per-user namespaced data
    nodes/            — per-node state for distributed expansion

Setup (one-time on Termux):
  pkg install rclone
  rclone config
  # Create remote named 'gdrive' (or whatever you prefer)
  # Set RCLONE_REMOTE=gdrive in ~/.quantum-mcagi/.env or export it

Usage in chat:
  /rclone-setup   — Check rclone config and test connection
  /rclone-status  — Show what's on Google Drive
  /cloud-save     — Save (auto-uses rclone if available)
  /cloud-load     — Load (auto-uses rclone if available)
  /cloud-pull     — Pull from all providers including rclone
"""

import json
import logging
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("quantum_ai")

# Default rclone remote name and base path on that remote
_DEFAULT_REMOTE = "gdrive"
_DEFAULT_BASE_PATH = "QuantumMCAGI"


def _get_rclone_remote() -> str:
    """Get the rclone remote name from environment or default."""
    return os.environ.get("RCLONE_REMOTE", _DEFAULT_REMOTE)


def _get_rclone_base() -> str:
    """Get the base path on the remote."""
    return os.environ.get("RCLONE_BASE_PATH", _DEFAULT_BASE_PATH)


def _rclone_available() -> bool:
    """Check if rclone binary is on PATH."""
    return shutil.which("rclone") is not None


def _run_rclone(args: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
    """Run an rclone command, returning the CompletedProcess."""
    cmd = ["rclone"] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _remote_path(logical_path: str) -> str:
    """Convert a logical path like 'QuantumMCAGI/brain' to 'gdrive:QuantumMCAGI/brain.json'."""
    remote = _get_rclone_remote()
    # Ensure .json extension for data files
    if not logical_path.endswith(".json"):
        logical_path = f"{logical_path}.json"
    return f"{remote}:{logical_path}"


def _local_cache_dir() -> Path:
    """Local cache directory for rclone sync staging."""
    cache = Path(os.path.expanduser("~/.quantum-mcagi-rclone-cache"))
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def _local_cache_path(logical_path: str) -> Path:
    """Get local cache file path for a logical path."""
    safe = logical_path.replace("..", "").lstrip("/")
    if not safe.endswith(".json"):
        safe = f"{safe}.json"
    target = (_local_cache_dir() / safe).resolve()
    # Security: ensure target stays within cache directory
    if not str(target).startswith(str(_local_cache_dir().resolve())):
        raise ValueError(f"Path traversal blocked: {logical_path}")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _serialize_dates(obj):
    """Recursively convert datetime objects to ISO strings."""
    if isinstance(obj, dict):
        return {k: _serialize_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_dates(v) for v in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj


# ── Public functions (standalone, no class needed) ───────────────────────────


def rclone_check() -> Dict[str, Any]:
    """
    Check rclone installation and remote configuration.
    Returns a status dict.
    """
    result = {
        "rclone_installed": False,
        "remote_configured": False,
        "remote_name": _get_rclone_remote(),
        "base_path": _get_rclone_base(),
        "test_ok": False,
        "error": None,
    }

    if not _rclone_available():
        result["error"] = "rclone not found. Install: pkg install rclone"
        return result
    result["rclone_installed"] = True

    # Check if remote is configured
    try:
        proc = _run_rclone(["listremotes"], timeout=10)
        if proc.returncode == 0:
            remotes = [r.strip().rstrip(":") for r in proc.stdout.strip().split("\n") if r.strip()]
            result["configured_remotes"] = remotes
            if _get_rclone_remote() in remotes:
                result["remote_configured"] = True
            else:
                result["error"] = (
                    f"Remote '{_get_rclone_remote()}' not found. "
                    f"Available: {remotes}. "
                    f"Set RCLONE_REMOTE=<name> or run: rclone config"
                )
                return result
        else:
            result["error"] = f"rclone listremotes failed: {proc.stderr}"
            return result
    except subprocess.TimeoutExpired:
        result["error"] = "rclone listremotes timed out"
        return result
    except Exception as e:
        result["error"] = str(e)
        return result

    # Test connectivity by listing the base path
    try:
        remote = _get_rclone_remote()
        base = _get_rclone_base()
        proc = _run_rclone(["lsjson", f"{remote}:{base}", "--max-depth", "1"], timeout=30)
        if proc.returncode == 0:
            result["test_ok"] = True
            items = json.loads(proc.stdout) if proc.stdout.strip() else []
            result["objects"] = len(items)
        elif "directory not found" in proc.stderr.lower() or proc.stdout.strip() == "[]":
            # Directory doesn't exist yet — that's fine, we'll create it on first save
            result["test_ok"] = True
            result["objects"] = 0
            result["note"] = f"{base}/ will be created on first save"
        else:
            result["error"] = f"rclone test failed: {proc.stderr}"
    except subprocess.TimeoutExpired:
        result["error"] = "Connection test timed out (30s)"
    except Exception as e:
        result["error"] = str(e)

    return result


def rclone_save(logical_path: str, data: dict) -> bool:
    """
    Save JSON data to Google Drive via rclone.
    Writes to local cache first, then copies to remote.
    """
    if not _rclone_available():
        logger.warning("[Rclone] rclone not installed")
        return False

    try:
        # Write to local cache
        local_file = _local_cache_path(logical_path)
        serialized = _serialize_dates(data)
        with open(local_file, "w") as f:
            json.dump(serialized, f, indent=2, default=str)

        # Copy to remote
        remote = _remote_path(logical_path)
        proc = _run_rclone(["copyto", str(local_file), remote], timeout=60)
        if proc.returncode == 0:
            logger.info(f"[Rclone] Saved {logical_path} → {remote}")
            return True
        else:
            logger.warning(f"[Rclone] save failed: {proc.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.warning(f"[Rclone] save timed out for {logical_path}")
        return False
    except Exception as e:
        logger.warning(f"[Rclone] save error: {e}")
        return False


def rclone_load(logical_path: str) -> Optional[dict]:
    """
    Load JSON data from Google Drive via rclone.
    Copies from remote to local cache, then reads.
    """
    if not _rclone_available():
        return None

    try:
        remote = _remote_path(logical_path)
        local_file = _local_cache_path(logical_path)

        # Copy from remote to local cache
        proc = _run_rclone(["copyto", remote, str(local_file)], timeout=60)
        if proc.returncode != 0:
            # File might not exist on remote
            if "not found" in proc.stderr.lower() or "no such" in proc.stderr.lower():
                return None
            logger.warning(f"[Rclone] load failed: {proc.stderr}")
            return None

        # Read local cache
        if local_file.exists():
            with open(local_file) as f:
                return json.load(f)
    except subprocess.TimeoutExpired:
        logger.warning(f"[Rclone] load timed out for {logical_path}")
    except json.JSONDecodeError as e:
        logger.warning(f"[Rclone] invalid JSON in {logical_path}: {e}")
    except Exception as e:
        logger.warning(f"[Rclone] load error: {e}")
    return None


def rclone_list(prefix: str) -> List[str]:
    """
    List objects under a prefix on Google Drive.
    Returns list of logical paths (without .json extension).
    """
    if not _rclone_available():
        return []

    try:
        remote = _get_rclone_remote()
        proc = _run_rclone(
            ["lsjson", f"{remote}:{prefix}", "--recursive", "--files-only"],
            timeout=30,
        )
        if proc.returncode != 0:
            return []
        items = json.loads(proc.stdout) if proc.stdout.strip() else []
        paths = []
        for item in items:
            p = item.get("Path", "")
            if p.endswith(".json"):
                p = p[:-5]  # Strip .json
            full = f"{prefix.rstrip('/')}/{p}" if p else prefix.rstrip("/")
            paths.append(full)
        return paths
    except Exception as e:
        logger.warning(f"[Rclone] list error: {e}")
        return []


def rclone_delete(logical_path: str) -> bool:
    """Delete a file from Google Drive via rclone."""
    if not _rclone_available():
        return False

    try:
        remote = _remote_path(logical_path)
        proc = _run_rclone(["deletefile", remote], timeout=30)
        if proc.returncode == 0:
            # Also remove local cache
            local_file = _local_cache_path(logical_path)
            if local_file.exists():
                local_file.unlink()
            return True
        return False
    except Exception as e:
        logger.warning(f"[Rclone] delete error: {e}")
        return False


# ── CloudProvider implementation (for registry integration) ──────────────────

try:
    from cloud_provider import CloudProvider
except ImportError:
    CloudProvider = None


if CloudProvider is not None:
    class RcloneProvider(CloudProvider):
        """
        Google Drive cloud provider via rclone.
        Implements the CloudProvider ABC so it plugs into CloudProviderRegistry.
        """

        @property
        def name(self) -> str:
            return f"Rclone ({_get_rclone_remote()}:)"

        def save(self, path: str, data: dict) -> bool:
            return rclone_save(path, data)

        def load(self, path: str) -> Optional[dict]:
            return rclone_load(path)

        def list_objects(self, prefix: str) -> List[str]:
            return rclone_list(prefix)

        def delete(self, path: str) -> bool:
            return rclone_delete(path)

        def status(self) -> Dict[str, Any]:
            check = rclone_check()
            return {
                "provider": self.name,
                "connected": check.get("test_ok", False),
                "rclone_installed": check.get("rclone_installed", False),
                "remote_configured": check.get("remote_configured", False),
                "objects": check.get("objects", 0),
                "error": check.get("error"),
            }
else:
    # Standalone mode — no CloudProvider base class available
    RcloneProvider = None
