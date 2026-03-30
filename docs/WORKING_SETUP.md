# Working PennyLane Setup in Termux

## Install

```bash
# PennyLane hard-depends on pennylane-lightning which requires scipy-openblas32
# (no Android wheel). Use --no-deps to skip the uninstallable sub-dependency:
pip install --no-deps PennyLane>=0.44.1
```

**Important**: Use `--no-deps` to prevent the pennylane-lightning → scipy-openblas32 build failure on Termux.
PennyLane works without Lightning — it falls back to the `default.qubit` simulator.

## Verified Working

- ✅ `import pennylane as qml` succeeds
- ✅ `qml.device('default.qubit', wires=2)` works
- ✅ Quantum circuits execute (superposition, entanglement)
- ✅ `pennylane_quantum.PennyLaneQuantum` class functions
- ✅ `QuantumBrain` detects `pennylane_available=True`
- ✅ `_get_quantum_random()` returns quantum randomness
- ✅ `semantic_quantum_circuit()` amplifies concepts
- ✅ `explanation["engines_used"]` includes `"PennyLaneQuantum"`

## Test Script

```bash
cd backend
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from pennylane_quantum import get_pennylane_quantum

pq = get_pennylane_quantum()
print("PennyLane available:", pq.pennylane_available)

if pq.pennylane_available:
    superposition = pq.create_superposition_circuit()
    print("Superposition:", superposition)
    
    weights = {'a': 1.0, 'b': 0.5}
    enhanced = pq.semantic_quantum_circuit(weights)
    print("Enhanced:", enhanced)
    print("✅ ALL GOOD")
else:
    print("❌ Not available")
EOF
```

## Integration Points in Code

- `backend/quantum_brain.py`:
  - Line 55: `self.pennylane = get_pennylane_quantum()` (inside try block)
  - Line 423: `engines.append("PennyLaneQuantum")` for philosophical/topic/quantum methods
  - Line 434: Quantum superposition step inserted into explanation trace
  - Line 117: `think()` — main entry point that routes to method-specific generators

## Fallback Behavior

If PennyLane import fails at module load time, `PENNYLANE_AVAILABLE=False` and:
- `_get_quantum_random()` → `random.random()`
- `_quantum_choice()` → `random.choice()`
- Semantic amplification → skipped
- System continues working with classical randomness

Thus the code is robust whether PennyLane works or not.

---

**CRITICAL**: Use `--no-deps` on PennyLane to prevent the pennylane-lightning build failure on Termux. The `default.qubit` simulator is used at runtime.
