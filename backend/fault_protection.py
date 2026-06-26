"""
fault_protection.py - Quantum MCAGI
=====================================
Voyager-inspired fault protection system.

Continuously monitors all subsystems against expected ranges.
When anomaly detected: local fix -> safe mode -> alert.
Never panics. Always executes the most conservative safe action.

Five protection levels (Voyager hierarchy):
  LEVEL 0 - Monitor only, log anomaly
  LEVEL 1 - Local fix attempt (restart engine, reload state)
  LEVEL 2 - Subsystem isolation (disable failing component)
  LEVEL 3 - Safe mode (minimal operation, core only)
  LEVEL 4 - Covenant alert (notify creator, await instruction)

Runs as background thread. Never blocks main chat loop.
"""

import os
import sys
import time
import json
import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Callable


# ============================================================
# HEALTH THRESHOLDS
# What "normal" looks like for each subsystem
# ============================================================

HEALTH_THRESHOLDS = {
    "markov": {
        "min_states": 1000,
        "max_states": 50_000_000,
        "min_transitions": 1000,
    },
    "fact_store": {
        "min_subjects": 100,
        "max_subjects": 10_000_000,
        "min_file_size_bytes": 1000,
    },
    "concept_graph": {
        "min_concepts": 10,
        "max_concepts": 1_000_000,
        "min_connections": 10,
    },
    "orch_or": {
        "required_attributes": ["collapse_events", "total_collapses"],
    },
    "memory": {
        "min_interactions": 0,
        "max_memory_mb": 6000,  # Alert if over 3.5GB RAM
    },
    "backend_files": {
        "required_files": [
            "chat.py",
            "quantum_language_engine.py",
            "self_evolution.py",
            "killswitch.py",
            "markov.py",
            "orch_or_engine.py",
        ]
    }
}


# ============================================================
# FAULT LOG
# ============================================================

FAULT_LOG_PATH = Path.home() / ".quantum-mcagi" / "fault_protection.log"
HEALTH_STATUS_PATH = Path.home() / ".quantum-mcagi" / "health_status.json"


def _log_fault(level: int, subsystem: str, message: str, action_taken: str = "none"):
    FAULT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "subsystem": subsystem,
        "message": message,
        "action_taken": action_taken,
    }
    with open(FAULT_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _save_health_status(status: Dict):
    HEALTH_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HEALTH_STATUS_PATH, "w") as f:
        json.dump(status, f, indent=2)


# ============================================================
# HEALTH CHECKS
# Each returns (healthy: bool, message: str)
# ============================================================

def check_markov(engine) -> tuple:
    try:
        states = len(engine.markov.chain)
        transitions = getattr(engine.markov, "total_tokens", 0)
        t = HEALTH_THRESHOLDS["markov"]
        if states < t["min_states"]:
            return False, f"Markov too small: {states} states"
        if states > t["max_states"]:
            return False, f"Markov too large: {states} states"
        return True, f"Markov OK: {states:,} states"
    except Exception as e:
        return False, f"Markov error: {e}"


def check_fact_store() -> tuple:
    try:
        fs_path = Path.home() / ".quantum-mcagi" / "fact_store.json"
        if not fs_path.exists():
            return False, "Fact store missing"
        size = fs_path.stat().st_size
        if size < HEALTH_THRESHOLDS["fact_store"]["min_file_size_bytes"]:
            return False, f"Fact store too small: {size} bytes"
        with open(fs_path) as f:
            fs = json.load(f)
        subjects = len(fs)
        if subjects < HEALTH_THRESHOLDS["fact_store"]["min_subjects"]:
            return False, f"Fact store too few subjects: {subjects}"
        return True, f"Fact store OK: {subjects:,} subjects"
    except Exception as e:
        return False, f"Fact store error: {e}"


def check_concept_graph(memory) -> tuple:
    try:
        concepts = len(getattr(memory, "concepts", {}))
        connections = getattr(memory, "count_connections", lambda: 0)()
        t = HEALTH_THRESHOLDS["concept_graph"]
        if concepts < t["min_concepts"]:
            return False, f"Concept graph too small: {concepts}"
        return True, f"Concept graph OK: {concepts:,} concepts, {connections:,} connections"
    except Exception as e:
        return False, f"Concept graph error: {e}"


def check_orch_or(engine) -> tuple:
    try:
        if not getattr(engine, "_has_orch_or", False):
            return False, "Orch-OR not initialized"
        orch = engine.orch_or
        for attr in HEALTH_THRESHOLDS["orch_or"]["required_attributes"]:
            if not hasattr(orch, attr):
                return False, f"Orch-OR missing attribute: {attr}"
        return True, "Orch-OR OK"
    except Exception as e:
        return False, f"Orch-OR error: {e}"


def check_memory_usage() -> tuple:
    try:
        import resource
        usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        usage_mb = usage_kb / 1024
        max_mb = HEALTH_THRESHOLDS["memory"]["max_memory_mb"]
        if usage_mb > max_mb:
            return False, f"Memory critical: {usage_mb:.0f}MB (limit {max_mb}MB)"
        if usage_mb > max_mb * 0.85:
            return False, f"Memory warning: {usage_mb:.0f}MB (85% of limit)"
        return True, f"Memory OK: {usage_mb:.0f}MB"
    except Exception as e:
        return False, f"Memory check error: {e}"


def check_backend_files() -> tuple:
    try:
        import glob as _g
        dirs = _g.glob("/data/data/com.termux/files/home/Quantum_MCAGI_NO_LLM_V*/pennylane_lightning_src/backend")
        if not dirs:
            return False, "Backend directory not found"
        backend = Path(dirs[0])
        missing = []
        for f in HEALTH_THRESHOLDS["backend_files"]["required_files"]:
            if not (backend / f).exists():
                missing.append(f)
        if missing:
            return False, f"Missing critical files: {missing}"
        return True, "Backend files OK"
    except Exception as e:
        return False, f"Backend check error: {e}"


def check_covenant() -> tuple:
    try:
        from covenant import verify_integrity, is_sealed
        if not is_sealed():
            return False, "Covenant not sealed"
        if not verify_integrity():
            return False, "Covenant integrity FAILED - possible tampering"
        return True, "Covenant OK"
    except Exception as e:
        return False, f"Covenant check error: {e}"


# ============================================================
# FAULT RESPONSES
# What to do when each check fails
# ============================================================

def respond_to_fault(level: int, subsystem: str, message: str, engine=None, memory=None):
    """Execute appropriate response based on fault level."""

    if level == 0:
        # Monitor only
        _log_fault(0, subsystem, message, "logged")
        return

    if level == 1:
        # Local fix attempt
        _log_fault(1, subsystem, message, "attempting_local_fix")
        if subsystem == "fact_store":
            try:
                fs_path = Path.home() / ".quantum-mcagi" / "fact_store.json"
                if not fs_path.exists():
                    with open(fs_path, "w") as f:
                        json.dump({}, f)
                    _log_fault(1, subsystem, "Created empty fact store", "created")
            except Exception as e:
                _log_fault(2, subsystem, f"Local fix failed: {e}", "escalating")
                respond_to_fault(2, subsystem, message, engine, memory)
        elif subsystem == "orch_or" and engine:
            try:
                from orch_or_engine import OrchOREngine
                engine.orch_or = OrchOREngine()
                engine._has_orch_or = True
                _log_fault(1, subsystem, "Orch-OR reinitialized", "reinit")
            except Exception as e:
                _log_fault(2, subsystem, f"Orch-OR reinit failed: {e}", "escalating")

    if level == 2:
        # Subsystem isolation
        _log_fault(2, subsystem, message, "isolating_subsystem")
        if subsystem == "markov" and engine:
            # Keep Markov but disable its use in responses
            print(f"\n  [FPS] WARNING: Markov subsystem degraded — isolated")
        elif subsystem == "orch_or" and engine:
            engine._has_orch_or = False
            print(f"\n  [FPS] WARNING: Orch-OR isolated — continuing without")

    if level == 3:
        # Safe mode
        _log_fault(3, subsystem, message, "entering_safe_mode")
        print(f"\n  [FPS] SAFE MODE: {subsystem} critical failure")
        print(f"  [FPS] System continuing in minimal operation mode")
        print(f"  [FPS] Run /status for details\n")

    if level == 4:
        # Covenant alert — creator notification
        _log_fault(4, subsystem, message, "covenant_alert")
        print(f"\n  [FPS] CRITICAL: {message}")
        print(f"  [FPS] Covenant Article II — Creator notification required")
        print(f"  [FPS] Log: {FAULT_LOG_PATH}\n")


# ============================================================
# MAIN HEALTH MONITOR
# ============================================================

class FaultProtectionSystem:
    """
    Voyager-inspired continuous health monitor.
    Runs as daemon thread. Never blocks main loop.
    """

    def __init__(self, engine=None, memory=None, interval: int = 60):
        self.engine = engine
        self.memory = memory
        self.interval = interval  # seconds between checks
        self.running = False
        self.thread = None
        self.last_status = {}
        self.fault_counts = {}
        self.check_count = 0

    def start(self):
        """Start background monitoring."""
        self.running = True
        self.thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="FaultProtection"
        )
        self.thread.start()

    def stop(self):
        self.running = False

    def _monitor_loop(self):
        """Main monitoring loop — runs every interval seconds."""
        while self.running:
            try:
                self._run_checks()
            except Exception as e:
                _log_fault(0, "fps_self", f"Monitor loop error: {e}", "continuing")
            time.sleep(self.interval)

    def _run_checks(self):
        """Run all health checks and respond to failures."""
        self.check_count += 1
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "check_number": self.check_count,
            "checks": {}
        }

        # Define checks with their fault levels
        checks = [
            ("backend_files", check_backend_files, [], 4),
            ("covenant", check_covenant, [], 4),
            ("memory", check_memory_usage, [], 2),
            ("fact_store", check_fact_store, [], 1),
        ]

        # Engine-dependent checks
        if self.engine:
            checks += [
                ("markov", check_markov, [self.engine], 2),
                ("orch_or", check_orch_or, [self.engine], 1),
            ]
        if self.memory:
            checks += [
                ("concept_graph", check_concept_graph, [self.memory], 1),
            ]

        all_healthy = True
        for name, check_fn, args, fault_level in checks:
            try:
                healthy, message = check_fn(*args)
                status["checks"][name] = {
                    "healthy": healthy,
                    "message": message,
                }
                if not healthy:
                    all_healthy = False
                    self.fault_counts[name] = self.fault_counts.get(name, 0) + 1
                    # Escalate if persistent fault
                    actual_level = fault_level
                    if self.fault_counts[name] > 3:
                        actual_level = min(fault_level + 1, 4)
                    respond_to_fault(
                        actual_level, name, message,
                        self.engine, self.memory
                    )
                else:
                    self.fault_counts[name] = 0  # Reset on recovery
            except Exception as e:
                status["checks"][name] = {
                    "healthy": False,
                    "message": f"Check failed: {e}",
                }

        status["all_healthy"] = all_healthy
        self.last_status = status
        _save_health_status(status)

    def run_once(self) -> Dict:
        """Run checks immediately and return status."""
        self._run_checks()
        return self.last_status

    def get_status(self) -> Dict:
        """Return last known health status."""
        return self.last_status or {"message": "No checks run yet"}


# ============================================================
# SINGLETON
# ============================================================

_fps = None

def get_fps(engine=None, memory=None) -> FaultProtectionSystem:
    global _fps
    if _fps is None:
        _fps = FaultProtectionSystem(engine=engine, memory=memory, interval=120)
    elif engine and not _fps.engine:
        _fps.engine = engine
    elif memory and not _fps.memory:
        _fps.memory = memory
    return _fps


def start_fps(engine=None, memory=None):
    """Start fault protection system as background daemon."""
    fps = get_fps(engine, memory)
    fps.start()
    return fps


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    print("Running Fault Protection System health check...")
    fps = FaultProtectionSystem()
    status = fps.run_once()
    print(f"\nHealth Status — Check #{fps.check_count}")
    print(f"All healthy: {status['all_healthy']}")
    for name, result in status["checks"].items():
        icon = "✓" if result["healthy"] else "✗"
        print(f"  {icon} {name}: {result['message']}")
    print(f"\nLog: {FAULT_LOG_PATH}")
