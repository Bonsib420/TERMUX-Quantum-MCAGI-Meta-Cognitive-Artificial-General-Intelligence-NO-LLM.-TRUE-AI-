"""
image_engine.py — Quantum MCAGI
=================================
Unified image generation engine.
Combines v1 scene types with v2 quality upgrades.

Available scenes:
  v2 (HDR, volumetric): black_hole, nebula, landscape, creature, structure, abstract, energy
  v1 (additional):       galaxy, quantum_state, wormhole, supernova, planet, fractal, neural, consciousness

Usage:
    from image_engine import generate_image
    img = generate_image("quantum black hole", width=512, height=512)
"""

# Try v2 first (higher quality), fall back to v1
try:
    from image_generator_v2 import (
        generate_image,
        render_black_hole,
        render_nebula,
        render_landscape,
        render_creature,
        render_structure,
        render_abstract,
        render_energy,
        _seed_from_prompt,
    )
    _v2_available = True
except Exception:
    _v2_available = False

# Import v1 scene types not in v2
try:
    from image_generator import (
        render_galaxy,
        render_quantum_state,
        render_wormhole,
        render_supernova,
        render_planet,
        render_fractal,
        render_neural,
        render_consciousness,
    )
    _v1_available = True
    if not _v2_available:
        from image_generator import generate_image, _seed_from_prompt
except Exception:
    _v1_available = False


# Scene registry — maps keywords to render functions
SCENE_MAP = {}

if _v2_available:
    SCENE_MAP.update({
        'black hole': 'render_black_hole',
        'blackhole': 'render_black_hole',
        'nebula': 'render_nebula',
        'landscape': 'render_landscape',
        'creature': 'render_creature',
        'structure': 'render_structure',
        'abstract': 'render_abstract',
        'energy': 'render_energy',
    })

if _v1_available:
    SCENE_MAP.update({
        'galaxy': 'render_galaxy',
        'quantum': 'render_quantum_state',
        'wormhole': 'render_wormhole',
        'supernova': 'render_supernova',
        'planet': 'render_planet',
        'fractal': 'render_fractal',
        'neural': 'render_neural',
        'consciousness': 'render_consciousness',
        'mind': 'render_consciousness',
    })


def get_available_scenes():
    """Return list of available scene types."""
    return sorted(SCENE_MAP.keys())


def get_status():
    """Return status of image generation capabilities."""
    return {
        'v2_available': _v2_available,
        'v1_available': _v1_available,
        'scenes': get_available_scenes(),
        'total_scenes': len(SCENE_MAP),
    }


if __name__ == '__main__':
    status = get_status()
    print(f"Image Engine Status:")
    print(f"  V2 (HDR): {status['v2_available']}")
    print(f"  V1 (extra scenes): {status['v1_available']}")
    print(f"  Available scenes: {', '.join(status['scenes'])}")
