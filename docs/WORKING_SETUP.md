# Working PennyLane Setup in Termux

## Versions That Work Together

```bash
# System packages (Termux)
pkg install python-scipy  # provides scipy 1.17.1

# Python packages (pip) - install in this exact order:
pip install --no-deps pennylane==0.36.0
pip install --no-deps pennylane-lightning==0.36.0
pip install "autoray==0.6.11" appdirs cachetools "gast==0.5.4" networkx tomlkit
```

**Important**: Use `--no-deps` for PennyLane to avoid SciPy rebuild attempt.

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
  - Line 50: `self.pennylane = get_pennylane_quantum()`
  - Line 99-127: `_get_quantum_random()`
  - Line 114-127: `_quantum_choice()`
  - Line 163-170: Quantum randomness applied to thinking
  - Line 375-389: Semantic quantum enhancement of concepts
  - Line 455, 462, 483: Quantum choice for UI elements
  - Line 390: `explanation["engines_used"].append("PennyLaneQuantum")`

## Fallback Behavior

If PennyLane import fails at module load time, `PENNYLANE_AVAILABLE=False` and:
- `_get_quantum_random()` → `random.random()`
- `_quantum_choice()` → `random.choice()`
- Semantic amplification → skipped
- System continues working with classical randomness

Thus the code is robust whether PennyLane works or not.

---

**CRITICAL**: Install order matters. Use `--no-deps` on PennyLane to prevent SciPy rebuild. The prebuilt SciPy from Termux (`python-scipy`) is used at runtime.
