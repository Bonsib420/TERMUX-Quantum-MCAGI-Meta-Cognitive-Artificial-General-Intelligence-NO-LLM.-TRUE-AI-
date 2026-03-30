"""
🔬 QUANTUM INTEGRATION MODULE
Enhances the procedural image generator with real quantum computing via PennyLane.
Provides quantum random number generation, quantum noise patterns, and hybrid quantum-classical rendering.
"""

import numpy as np
try:
    import pennylane as qml
    PENNYLANE_AVAILABLE = True
except ImportError:
    qml = None
    PENNYLANE_AVAILABLE = False
from typing import Optional, Tuple, List, Callable
import hashlib
import math

# ============ Quantum Device Setup ============

def available_quantum_devices() -> List[str]:
    """Return list of available quantum devices"""
    devices = []
    try:
        # Default.qubit is always available (simulator)
        devices.append("default.qubit")
        # Try Lightning if available
        import pennylane_lightning
        devices.append("lightning.qubit")
    except ImportError:
        pass
    # Add more devices as they become available
    return devices


def get_quantum_device(device_name: str = "default.qubit", wires: int = 4):
    """Get a quantum device instance"""
    try:
        if device_name == "default.qubit":
            return qml.device("default.qubit", wires=wires)
        elif device_name == "lightning.qubit":
            return qml.device("lightning.qubit", wires=wires)
        else:
            return qml.device(device_name, wires=wires)
    except Exception as e:
        print(f"Warning: Could not load {device_name}, falling back to default.qubit: {e}")
        return qml.device("default.qubit", wires=wires)


# ============ Quantum Random Number Generation ============

def quantum_random_bits(seed: Optional[int] = None, n_bits: int = 8, device_name: str = "default.qubit") -> int:
    """
    Generate random bits using a quantum circuit.
    Measures qubits in superposition to get truly random (or simulated random) values.

    Args:
        seed: Optional seed for reproducibility (applied classically)
        n_bits: Number of random bits to generate
        device_name: Quantum device to use

    Returns:
        Integer value from the measured bits
    """
    wires = min(n_bits, 8)  # Limit to 8 wires for performance
    dev = get_quantum_device(device_name, wires=wires)

    # Use seed if provided to create a deterministic circuit
    if seed is not None:
        np.random.seed(seed % (2**32))

    # Set shots if device supports it, default.qubit analytic mode uses probs
    shots = 1024

    @qml.qnode(dev)
    def circuit():
        # Apply Hadamard to all qubits to create superposition
        for i in range(wires):
            qml.Hadamard(wires=i)
        # Optionally add some entanglement for more "quantum" behavior
        if wires > 1:
            for i in range(wires - 1):
                qml.CNOT(wires=[i, i + 1])
        # Return probabilities for computational basis states
        return qml.probs(wires=range(wires))

    # Execute circuit
    try:
        probs = circuit()
        # Convert probability distribution to sample by inverse transform sampling
        # Generate a random number from seed to pick a basis state
        if seed is not None:
            rng = np.random.RandomState(seed % (2**32))
            rand_val = rng.random()
        else:
            rand_val = np.random.random()

        # Cumulative distribution
        cum_probs = np.cumsum(probs)
        state_idx = np.searchsorted(cum_probs, rand_val)

        # Convert to binary
        bits_str = format(state_idx, f'0{wires}b')
        bits = bits_str[:n_bits].ljust(n_bits, '0')
        return int(bits, 2)
    except Exception as e:
        # Fallback to classical random
        if seed is not None:
            rng = np.random.RandomState(seed % (2**32))
            return rng.randint(0, 2**n_bits)
        else:
            return np.random.randint(0, 2**n_bits)


def quantum_seed_from_prompt(prompt: str, device_name: str = "default.qubit") -> int:
    """
    Generate a seed from prompt using both classical hashing and quantum enhancement.
    Creates a hybrid classical-quantum seed.

    Args:
        prompt: Input text prompt
        device_name: Quantum device to use

    Returns:
        Integer seed
    """
    # Classical hash component
    classical_hash = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)

    # Quantum enhancement: Use prompt hash to determine circuit parameters
    # This ensures same prompt gives same "quantum" result (reproducibility)
    np.random.seed(classical_hash % (2**32))

    # Generate quantum random bits to mix in
    quantum_bits = quantum_random_bits(seed=classical_hash, n_bits=16, device_name=device_name)

    # Combine classical and quantum
    hybrid_seed = (classical_hash ^ quantum_bits) % (2**31)
    return hybrid_seed


# ============ Quantum-Inspired Noise Patterns ============

def quantum_wavefunction_grid(w: int, h: int, seed: Optional[int] = None,
                              n_qubits: int = 6, device_name: str = "default.qubit") -> np.ndarray:
    """
    Generate a 2D probability grid from a quantum circuit's wavefunction.
    Simulates quantum state distribution across a grid.

    Args:
        w: Width
        h: Height
        seed: Random seed
        n_qubits: Number of qubits in circuit
        device_name: Quantum device

    Returns:
        2D array representing probability amplitudes
    """
    if seed is not None:
        np.random.seed(seed)

    dev = get_quantum_device(device_name, wires=n_qubits)

    # Use amplitude embedding to encode position into quantum state
    @qml.qnode(dev)
    def amplitude_circuit(x_amp, y_amp):
        # Encode x and y amplitudes using angle encoding
        qml.RX(x_amp * math.pi, wires=0)
        qml.RY(y_amp * math.pi, wires=1)

        # Create entanglement to spread information
        for i in range(min(3, n_qubits - 1)):
            qml.CNOT(wires=[i, i + 1])

        # Additional rotations to create complex interference
        for i in range(2, n_qubits):
            qml.RZ(np.random.random() * math.pi, wires=i)

        # Return probability amplitudes for a subset of basis states
        return qml.probs(wires=range(min(4, n_qubits)))

    # Generate grid of amplitudes
    grid = np.zeros((h, w), dtype=np.float64)

    # Sample grid points
    n_samples = min(w * h, 256)  # Limit samples for performance
    ys = np.linspace(0, 1, min(h, 16))
    xs = np.linspace(0, 1, min(w, 16))

    for y_i, y_val in enumerate(ys):
        for x_i, x_val in enumerate(xs):
            # Map grid position to amplitude parameters
            x_amp = x_val
            y_amp = y_val

            probs = amplitude_circuit(x_amp, y_amp)
            # Use the sum of some probabilities as the grid value
            grid[y_i * (h // len(ys)), x_i * (w // len(xs))] = np.sum(probs[:len(probs)//2])

    # Upsample to full grid size
    from scipy.ndimage import zoom
    zoom_factors = (h / grid.shape[0], w / grid.shape[1])
    grid = zoom(grid, zoom_factors, order=3)
    grid = grid[:h, :w]

    # Normalize
    grid = (grid - grid.min()) / (grid.max() - grid.min() + 1e-8)
    return grid


def quantum_entanglement_pattern(w: int, h: int, seed: Optional[int] = None,
                                 n_qubits: int = 4) -> np.ndarray:
    """
    Generate a pattern inspired by quantum entanglement correlations.
    Creates a field with quantum-like non-local correlations.

    Args:
        w: Width
        h: Height
        seed: Random seed
        n_qubits: Number of qubits

    Returns:
        2D array with entanglement-inspired values
    """
    if seed is not None:
        np.random.seed(seed)

    dev = get_quantum_device("default.qubit", wires=n_qubits)

    @qml.qnode(dev)
    def bell_state_circuit():
        # Create Bell state (maximally entangled)
        qml.Hadamard(wires=0)
        qml.CNOT(wires=[0, 1])
        # Additional entanglement in chain
        for i in range(1, min(3, n_qubits - 1)):
            qml.CNOT(wires=[i, i + 1])
        return qml.state()

    state = bell_state_circuit()
    # Probability distribution from state
    probs = np.abs(state) ** 2

    # Create a 2D pattern that reflects this distribution
    y, x = np.mgrid[0:h, 0:w]
    norm_x = x / max(w, 1)
    norm_y = y / max(h, 1)

    # Map 2D coordinates to basis state probabilities
    pattern = np.zeros((h, w), dtype=np.float64)

    # Use the first n basis states to create a pattern
    n_states = len(probs)
    for i in range(n_states):
        # Convert state index to binary pattern
        bits = format(i, f'0{int(math.ceil(math.log2(n_states)))}b')
        # Create a checkerboard-like pattern based on bit parity
        mask = np.ones((h, w), dtype=bool)
        for j, bit in enumerate(bits):
            if bit == '1':
                # Create alternating regions
                mask = mask & (((x + y) % 2) == (j % 2))
        pattern[mask] += probs[i]

    return pattern / (pattern.max() + 1e-8)


# ============ Quantum Parameter Enhancement ============

def quantum_parameter_bias(prompt: str, n_params: int = 5,
                          device_name: str = "default.qubit") -> List[float]:
    """
    Generate quantum-influenced parameters for rendering.
    Creates a parameter set that can be used to tune renderer behavior.

    Args:
        prompt: Input prompt (seeds the quantum circuit)
        n_params: Number of parameters to generate
        device_name: Quantum device

    Returns:
        List of floats in [0, 1] range
    """
    seed = _seed_from_prompt(prompt) if hasattr(quantum_parameter_bias, '_seed_from_prompt') else hash(prompt) % (2**32)
    np.random.seed(seed % (2**32))

    dev = get_quantum_device(device_name, wires=min(n_params, 8))

    @qml.qnode(dev)
    def param_circuit():
        # Encode prompt influence via rotation angles
        for i in range(min(8, n_params)):
            angle = (seed % 360) * math.pi / 180 * (i + 1) / 4
            qml.RX(angle, wires=i)
            if i > 0:
                qml.CNOT(wires=[i - 1, i])
            qml.RY(np.random.random() * math.pi, wires=i)

        return qml.sample(wires=range(min(4, n_params)))

    samples = param_circuit()
    if isinstance(samples, np.ndarray):
        # Convert binary samples to continuous values via averaging
        params = []
        for i in range(n_params):
            if i < samples.shape[1] if samples.ndim > 1 else 1:
                vals = samples[:, i] if samples.ndim > 1 else [samples[i]]
                params.append(np.mean(vals))
            else:
                params.append(np.random.random())
    else:
        params = [np.random.random() for _ in range(n_params)]

    return params


def _seed_from_prompt(prompt: str) -> int:
    """Helper: deterministic seed from prompt"""
    return int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)


# ============ Quantum Renderer Enhancements ============

def enhance_renderer_with_quantum(renderer_func: Callable, prompt: str,
                                 quantum_intensity: float = 0.3) -> Callable:
    """
    Wrap a renderer function to add quantum-enhanced variations.

    Args:
        renderer_func: Original renderer function (w, h, seed, params) -> array
        prompt: Input prompt for quantum seeding
        quantum_intensity: How much quantum influence (0-1)

    Returns:
        Wrapped renderer function
    """
    def quantum_enhanced_renderer(w: int, h: int, seed: int, params: Optional[dict] = None):
        # Get base render
        base_img = renderer_func(w, h, seed, params)

        # Generate quantum modulation pattern
        q_seed = _seed_from_prompt(prompt + str(seed))
        q_pattern = quantum_wavefunction_grid(w, h, seed=q_seed, n_qubits=4)

        # Apply quantum modulation as color tint/shift
        quantum_img = base_img.astype(np.float64)
        for c in range(3):
            quantum_img[..., c] = quantum_img[..., c] * (1 - quantum_intensity) + \
                                 quantum_img[..., c] * q_pattern * quantum_intensity

        quantum_img = np.clip(quantum_img, 0, 255).astype(np.uint8)
        return quantum_img

    return quantum_enhanced_renderer


# ============ Quantum Scene Classification ============

def quantum_scene_scoring(prompt: str, scene_keywords: dict,
                          device_name: str = "default.qubit") -> Tuple[str, dict]:
    """
    Use a quantum circuit to help classify the scene type from the prompt.
    Creates a hybrid classical-quantum text classifier.

    Args:
        prompt: Input text prompt
        scene_keywords: Dictionary mapping scenes to keywords
        device_name: Quantum device

    Returns:
        (best_scene, params) tuple
    """
    # Lazy import
    try:
        from .image_generator_advanced import SCENE_KEYWORDS as CLASSICAL_SCENES
        classical_keywords = CLASSICAL_SCENES
    except ImportError:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from image_generator_advanced import SCENE_KEYWORDS as CLASSICAL_SCENES
        classical_keywords = CLASSICAL_SCENES

    # Classical keyword scoring as baseline
    prompt_lower = prompt.lower()
    classical_scores = {}
    for scene, keywords in classical_keywords.items():
        score = sum(len(kw) for kw in keywords if kw in prompt_lower)
        if score > 0:
            classical_scores[scene] = score

    if not classical_scores:
        return 'nebula', {}

    # Quantum enhancement: Use quantum circuit to slightly perturb scores
    # based on semantic "distance" in a simulated quantum feature space
    dev = get_quantum_device(device_name, wires=4)

    @qml.qnode(dev)
    def scoring_circuit(embedding: list):
        # Encode prompt embedding into circuit
        for i, val in enumerate(embedding[:4]):
            qml.RY(val * math.pi, wires=i)
        # Entangle
        for i in range(3):
            qml.CNOT(wires=[i, i + 1])
        # Measure
        return qml.sample(wires=range(4))

    # Create a simple embedding from prompt features
    prompt_features = [
        len([w for w in prompt_lower.split() if any(kw in w for kw in classical_keywords.get(s, []))])
        for s in classical_scores.keys()
    ]
    # Normalize
    if max(prompt_features) > 0:
        prompt_features = [f / max(prompt_features) for f in prompt_features]

    # Pad to 4 features
    while len(prompt_features) < 4:
        prompt_features.append(0.0)

    # Run quantum circuit to get "quantum bias"
    try:
        samples = scoring_circuit(prompt_features[:4])
        quantum_bias = np.mean(samples, axis=0) if isinstance(samples, np.ndarray) else np.zeros(4)
    except:
        quantum_bias = np.zeros(4)

    # Apply quantum bias to classical scores (additive perturbation)
    scenes = list(classical_scores.keys())
    for i, scene in enumerate(scenes[:4]):
        bias = quantum_bias[i % len(quantum_bias)] * 10  # Scale factor
        classical_scores[scene] += bias

    # Pick best scene
    best = max(classical_scores, key=classical_scores.get)

    # Extract parameters (same as original _detect_scene logic)
    params = {}
    prompt_lower = prompt.lower()

    if best == 'black_hole':
        if 'merg' in prompt_lower:
            params['merging'] = True
        if 'jet' in prompt_lower:
            params['jets'] = True
    elif best == 'nebula':
        for name in ['fire', 'ice', 'cosmic', 'emerald', 'plasma', 'void']:
            if name in prompt_lower:
                params['palette'] = name
                break
    elif best == 'planet':
        for ptype in ['gas', 'ice', 'lava', 'rocky']:
            if ptype in prompt_lower:
                params['type'] = ptype
                break
    elif best == 'galaxy':
        if 'barred' in prompt_lower:
            params['arms'] = 2

    return best, params


# ============ Quantum-Enhanced Image Generation ============

def generate_quantum_image(prompt: str, width: int = 512, height: int = 512,
                          variation_seed: Optional[int] = None,
                          quantum_mode: str = "hybrid",
                          device_name: str = "default.qubit") -> np.ndarray:
    """
    Generate an image using quantum-enhanced procedures.

    Args:
        prompt: Text description
        width: Output width
        height: Output height
        variation_seed: Optional seed modifier
        quantum_mode: "hybrid", "full", or "classic"
            - "hybrid": Use quantum for seed generation and minor pattern modulation
            - "full": Use quantum for many aspects (more experimental)
            - "classic": Disable quantum features (fallback)
        device_name: Quantum device to use

    Returns:
        Numpy array (H, W, 3) with RGB image
    """
    # Lazy import to handle both package and standalone usage
    try:
        from .image_generator_advanced import (
            _seed_from_prompt, _detect_scene, RENDERERS, render_nebula
        )
    except ImportError:
        # Standalone mode - direct import
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from image_generator_advanced import (
            _seed_from_prompt, _detect_scene, RENDERERS, render_nebula
        )

    if quantum_mode == "classic":
        # Use original non-quantum version
        seed = _seed_from_prompt(prompt)
        if variation_seed is not None:
            seed = (seed + variation_seed) % (2**31)
        scene, params = _detect_scene(prompt)
        renderer = RENDERERS.get(scene, render_nebula)
        img_array = renderer(width, height, seed, params)
        return img_array

    # Quantum-enhanced seed generation
    seed = quantum_seed_from_prompt(prompt, device_name=device_name)
    if variation_seed is not None:
        seed = (seed + variation_seed) % (2**31)

    # Quantum scene classification (optional enhancement)
    try:
        from .image_generator_advanced import SCENE_KEYWORDS
    except ImportError:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from image_generator_advanced import SCENE_KEYWORDS

    scene, params = quantum_scene_scoring(prompt, SCENE_KEYWORDS, device_name)

    # Get renderer
    renderer = RENDERERS.get(scene, render_nebula)

    # Generate base image
    img_array = renderer(width, height, seed, params)

    # Apply quantum modulation if hybrid or full mode
    if quantum_mode in ["hybrid", "full"]:
        q_intensity = 0.2 if quantum_mode == "hybrid" else 0.5
        q_pattern = quantum_wavefunction_grid(width, height, seed=seed,
                                              n_qubits=6, device_name=device_name)

        # Apply as color modulation
        img_float = img_array.astype(np.float64)
        for c in range(3):
            channel_mod = q_pattern * 50  # Modulation strength
            img_float[..., c] = np.clip(
                img_float[..., c] + (channel_mod - 25) * q_intensity,
                0, 255
            )
        img_array = img_float.astype(np.uint8)

        # Add quantum noise texture in full mode
        if quantum_mode == "full":
            q_noise = (q_pattern - 0.5) * 30 * q_intensity
            img_float = img_array.astype(np.float64)
            for c in range(3):
                img_float[..., c] = np.clip(img_float[..., c] + q_noise, 0, 255)
            img_array = img_float.astype(np.uint8)

    return img_array


# ============ Quantum Presets ============

QUANTUM_PRESETS = {
    "consciousness_field": {
        "description": "Quantum visualization of consciousness/orchestrated objective reduction (Orch-OR)",
        "prompts": ["quantum consciousness", "orchestrated objective reduction", "tubulin quantum state",
                    "penrose hameroff theory", "cosmic mind field"],
        "renderer": "consciousness",
        "quantum_mode": "full",
        "params": {"n_tubes": 8, "quantum_coherence": 0.7}
    },
    "quantum_nebula": {
        "description": "Nebula with quantum wavefunction modulation",
        "prompts": ["quantum nebula", "entangled gas cloud", "superposition nebula"],
        "renderer": "nebula",
        "quantum_mode": "hybrid",
        "params": {"palette": "cosmic"}
    },
    "wormhole_tunneling": {
        "description": "Wormhole with quantum tunneling visual effects",
        "prompts": ["quantum wormhole", "tunneling bridge", "heisenberg uncertainty portal"],
        "renderer": "wormhole",
        "quantum_mode": "full",
        "params": {}
    },
    "quantum_fractal": {
        "description": "Fractal with quantum-influenced iteration parameters",
        "prompts": ["quantum fractal", "superposition mandelbrot", "entangled julia set"],
        "renderer": "fractal",
        "quantum_mode": "hybrid",
        "params": {}
    }
}


def get_quantum_preset(name: str) -> dict:
    """Get a quantum preset configuration"""
    return QUANTUM_PRESETS.get(name, QUANTUM_PRESETS["consciousness_field"])


def list_quantum_presets() -> List[str]:
    """List available quantum presets"""
    return list(QUANTUM_PRESETS.keys())


# ============ Quick Test ============

if __name__ == "__main__":
    print("🔬 Quantum Integration Module Test")
    print("=" * 50)
    print("Available devices:", available_quantum_devices())

    print("\nTesting quantum seed generation...")
    seed1 = quantum_seed_from_prompt("quantum black hole", device_name="default.qubit")
    seed2 = quantum_seed_from_prompt("quantum black hole", device_name="default.qubit")
    print(f"Quantum seed 1: {seed1}")
    print(f"Quantum seed 2 (same prompt): {seed2}")
    print(f"Seeds equal (deterministic): {seed1 == seed2}")

    print("\nGenerating quantum wavefunction grid...")
    grid = quantum_wavefunction_grid(256, 256, seed=42, n_qubits=4)
    print(f"Grid shape: {grid.shape}, min: {grid.min():.4f}, max: {grid.max():.4f}")

    print("\nAvailable quantum presets:")
    for preset in list_quantum_presets():
        print(f"  - {preset}: {QUANTUM_PRESETS[preset]['description']}")

    print("\n✅ Quantum module ready!")
