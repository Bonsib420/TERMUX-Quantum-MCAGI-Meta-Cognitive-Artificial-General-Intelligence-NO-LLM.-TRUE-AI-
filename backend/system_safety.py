"""
■■ System Safety Module
========================
Comprehensive runtime protection for Quantum MCAGI:
1. atomic_write(path, content)
2. atomic_write_json(path, obj)
3. atomic_save_npz(path, **arrs)
4. MemoryTracker
5. Watchdog
6. measure_lightning_leak()

— write-to-temp-then-rename, crash-safe
— same for JSON dicts
— same for numpy .npz state files
— logs RSS/VMS, detects unbounded growth
— periodic auto-save + cloud sync hook
— runs N quantum circuits, reports memory delta

Drop-in replacement for normal file writes. The atomic writes here CAN NOT
leave a half-written file behind under any failure mode (power loss, SIGKILL,
phone sleep). The watchdog ensures unsaved work is never older than N minutes.
Usage:
from system_safety import atomic_write_json, MemoryTracker, Watchdog
# Atomic save
atomic_write_json('/path/to/state.json', {'key': 'value'})
# Memory tracking
tracker = MemoryTracker(name='engine')
tracker.snapshot('boot')
# ... do work ...
tracker.snapshot('after_chat_1000_turns')
tracker.report()
# Watchdog
wd = Watchdog(save_fn=engine.save_state, interval_seconds=300)
wd.start()
# ... runs in background ...
wd.stop()
"""
import os
import json
import time
import threading
import logging
import gc
import tempfile
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any
try:
import numpy as np
HAS_NUMPY = True
except ImportError:
HAS_NUMPY = False
np = None
try:
import resource # POSIX only — Termux has it
HAS_RESOURCE = True
except ImportError:
HAS_RESOURCE = False
resource = None
logger = logging.getLogger("system_safety")

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
#
ATOMIC WRITES
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
def atomic_write(path: str, content: str, encoding: str = "utf-8") -> None:
"""
Atomically write text to `path`. Either the new content lands fully,
or the old file is untouched. Never a half-written file.
Mechanism: write to `path.tmp`, fsync, os.replace() to `path`.
"""
path = str(path)
parent = os.path.dirname(path) or "."
os.makedirs(parent, exist_ok=True)
# Use a uniquely-named temp file in the same directory (same filesystem
# is required for atomic os.replace).
fd, tmp = tempfile.mkstemp(prefix=".tmp_", dir=parent)
try:
with os.fdopen(fd, "w", encoding=encoding) as f:
f.write(content)
f.flush()
os.fsync(f.fileno())
os.replace(tmp, path)
except Exception:
# Clean up the orphan tmp file on failure
try:
if os.path.exists(tmp):
os.unlink(tmp)
except Exception:
pass
raise

def atomic_write_bytes(path: str, content: bytes) -> None:
"""Same as atomic_write but for binary content."""
path = str(path)
parent = os.path.dirname(path) or "."
os.makedirs(parent, exist_ok=True)
fd, tmp = tempfile.mkstemp(prefix=".tmp_", dir=parent)
try:
with os.fdopen(fd, "wb") as f:
f.write(content)
f.flush()
os.fsync(f.fileno())
os.replace(tmp, path)
except Exception:
try:
if os.path.exists(tmp):
os.unlink(tmp)
except Exception:
pass
raise

def atomic_write_json(path: str, obj: Any, indent: Optional[int] = None) -> None:
"""Atomic JSON write."""
text = json.dumps(obj, ensure_ascii=False, indent=indent)
atomic_write(path, text)

def atomic_save_npz(path: str, **arrays) -> None:
"""
Atomic numpy .npz save. Saves to a temp file then renames.
Use this instead of np.savez() for any file you can't afford to lose.
"""
if not HAS_NUMPY:
raise RuntimeError("atomic_save_npz requires numpy")
path = str(path)
parent = os.path.dirname(path) or "."
os.makedirs(parent, exist_ok=True)
fd, tmp = tempfile.mkstemp(prefix=".tmp_", suffix=".npz", dir=parent)
os.close(fd)
try:
np.savez(tmp, **arrays)
# numpy adds .npz suffix if not present, so the actual file may be tmp.npz
actual_tmp = tmp if os.path.exists(tmp) else tmp + ".npz"
# Force write to disk before rename
with open(actual_tmp, "rb") as f:
os.fsync(f.fileno())
os.replace(actual_tmp, path)
except Exception:
for candidate in (tmp, tmp + ".npz"):
try:
if os.path.exists(candidate):
os.unlink(candidate)
except Exception:
pass
raise

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
#
MEMORY TRACKING
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
def _get_rss_mb() -> float:
"""Current resident-set size in MB. POSIX only."""
if not HAS_RESOURCE:
return 0.0
usage = resource.getrusage(resource.RUSAGE_SELF)
# Linux reports ru_maxrss in KB; macOS in bytes.
rss = usage.ru_maxrss
# Heuristic: if the value is huge, it's bytes; otherwise KB.
return rss / 1024.0 if rss < 10**9 else rss / (1024.0 * 1024.0)

class MemoryTracker:
"""
Logs memory snapshots. Detects unbounded growth — if RSS climbs above
a threshold or grows by more than X% between snapshots, warns.
"""
def __init__(self, name: str = "engine", warn_growth_pct: float = 50.0,
warn_absolute_mb: float = 2048.0):
self.name = name
self.warn_growth_pct = warn_growth_pct
self.warn_absolute_mb = warn_absolute_mb
self.snapshots: List[Dict] = []
def snapshot(self, label: str) -> Dict:
"""Take a memory snapshot with a human-readable label."""
gc.collect() # let dead refs go before measuring
rss_mb = _get_rss_mb()
snap = {
"label": label,
"time": time.time(),
"rss_mb": rss_mb,
"objects": len(gc.get_objects()),
}
self.snapshots.append(snap)
# Warn on absolute threshold
if rss_mb > self.warn_absolute_mb:
logger.warning(
f"[{self.name}] RSS {rss_mb:.1f} MB exceeds threshold "

f"{self.warn_absolute_mb} MB at '{label}'"
)
# Warn on growth from previous snapshot
if len(self.snapshots) >= 2:
prev = self.snapshots[-2]
if prev["rss_mb"] > 0:
growth = ((rss_mb - prev["rss_mb"]) / prev["rss_mb"]) * 100.0
if growth > self.warn_growth_pct:
logger.warning(
f"[{self.name}] RSS grew {growth:.1f}% "
f"({prev['rss_mb']:.1f}→{rss_mb:.1f} MB) "
f"between '{prev['label']}' and '{label}'"
)
return snap
def report(self) -> str:
"""Return a multi-line summary of all snapshots."""
if not self.snapshots:
return f"[{self.name}] no snapshots taken"
lines = [f"[{self.name}] memory report:"]
for s in self.snapshots:
lines.append(
f" {s['label']:30s} RSS={s['rss_mb']:>8.1f} MB "
f"objs={s['objects']:>9d}"
)
first, last = self.snapshots[0], self.snapshots[-1]
delta_rss = last["rss_mb"] - first["rss_mb"]
delta_objs = last["objects"] - first["objects"]
lines.append(
f" ■■ ∆ over {len(self.snapshots)} snapshots: "
f"RSS={delta_rss:+.1f} MB objs={delta_objs:+d}"
)
return "\n".join(lines)

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
#
WATCHDOG / HEARTBEAT
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
class Watchdog:
"""
Background timer that fires `save_fn` every `interval_seconds`.
Optionally runs `cloud_fn` every Nth save (so cloud syncs are less
frequent than local saves, for bandwidth).
Designed to be drop-in: start it on engine boot, stop it on shutdown.
Auto-restarts the timer if `save_fn` raises (logs the error).
"""
def __init__(self, save_fn: Callable[[], None],
interval_seconds: int = 300,
cloud_fn: Optional[Callable[[], None]] = None,
cloud_every_n_saves: int = 4):
self.save_fn = save_fn
self.cloud_fn = cloud_fn
self.interval = interval_seconds
self.cloud_every = cloud_every_n_saves
self._stop = threading.Event()
self._thread: Optional[threading.Thread] = None
self._save_count = 0
def _loop(self) -> None:
while not self._stop.wait(self.interval):
try:
self.save_fn()
self._save_count += 1
if self.cloud_fn and self._save_count % self.cloud_every == 0:
try:
self.cloud_fn()
except Exception as e:
logger.warning(f"watchdog cloud_fn failed: {e}")
except Exception as e:
logger.warning(f"watchdog save_fn failed: {e}")
def start(self) -> None:
if self._thread and self._thread.is_alive():
return
self._stop.clear()
self._thread = threading.Thread(target=self._loop, daemon=True,
name="watchdog")
self._thread.start()
logger.info(f"watchdog started: save every {self.interval}s, "
f"cloud every {self.cloud_every} saves")
def stop(self) -> None:
self._stop.set()
if self._thread:
self._thread.join(timeout=5.0)
logger.info("watchdog stopped")

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
#
LIGHTNING LEAK DETECTION
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
def measure_lightning_leak(n_circuits: int = 1000, n_qubits: int = 4,
backend: str = "lightning.qubit") -> Dict:
"""
Run `n_circuits` quantum circuits in sequence, measuring memory before

and after. If memory grows by more than ~10MB, lightning has a leak.
Returns:
{'leaked_mb': float, 'n_circuits': int, 'verdict': str}
"""
try:
import pennylane as qml
except ImportError:
return {"verdict": "PennyLane not installed", "leaked_mb": 0,
"n_circuits": 0}
gc.collect()
rss_before = _get_rss_mb()
dev = qml.device(backend, wires=n_qubits)
@qml.qnode(dev)
def circuit(theta):
for i in range(n_qubits):
qml.RX(theta, wires=i)
for i in range(n_qubits - 1):
qml.CNOT(wires=[i, i + 1])
return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]
for i in range(n_circuits):
circuit(0.5 + i * 0.001)
gc.collect()
rss_after = _get_rss_mb()
leaked = rss_after - rss_before
if leaked < 5:
verdict = "no leak detected"
elif leaked < 20:
verdict = "minor leak (acceptable)"
elif leaked < 100:
verdict = "moderate leak (monitor)"
else:
verdict = "SIGNIFICANT LEAK"
return {
"leaked_mb": leaked,
"n_circuits": n_circuits,
"n_qubits": n_qubits,
"backend": backend,
"rss_before_mb": rss_before,
"rss_after_mb": rss_after,
"verdict": verdict,
}

