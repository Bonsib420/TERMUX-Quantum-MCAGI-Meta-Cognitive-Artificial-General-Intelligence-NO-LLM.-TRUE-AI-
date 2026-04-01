"""
Quantum Image Generator
=======================
A from-scratch procedural image generator. Zero external dependencies.
Built entirely on Python standard library.

Produces high-quality cosmic art: black holes, nebulae, galaxies,
and quantum field visualizations using procedural noise, domain warping,
physically-inspired rendering, and cinematic post-processing.

Usage:
    python -m quantum_image_generator --preset cosmic_vortex -o vortex.png
    python -m quantum_image_generator --all --width 512
"""

from .core import PixelBuffer, blackbody_color, gradient_sample, hsv_to_rgb
from .noise import PerlinNoise, VoronoiNoise
from .renderer import (
    create_cosmic_vortex,
    create_nebula,
    create_galaxy,
    create_quantum_field,
    create_deep_space,
    PRESETS,
    render_starfield,
    render_nebula_layer,
    render_spiral_arms,
    render_accretion_glow,
    render_black_hole_center,
    render_light_streaks,
    render_jet_streams,
    apply_bloom,
    apply_vignette,
    apply_tone_mapping,
    apply_color_grade,
    apply_gravitational_lensing,
    apply_chromatic_aberration,
    apply_film_grain,
)

__version__ = "1.1.0"
__all__ = [
    "PixelBuffer",
    "PerlinNoise",
    "VoronoiNoise",
    "create_cosmic_vortex",
    "create_nebula",
    "create_galaxy",
    "create_quantum_field",
    "create_deep_space",
    "PRESETS",
    "render_starfield",
    "render_nebula_layer",
    "render_spiral_arms",
    "render_accretion_glow",
    "render_black_hole_center",
    "render_light_streaks",
    "render_jet_streams",
    "apply_bloom",
    "apply_vignette",
    "apply_tone_mapping",
    "apply_color_grade",
    "apply_gravitational_lensing",
    "apply_chromatic_aberration",
    "apply_film_grain",
    "blackbody_color",
    "gradient_sample",
    "hsv_to_rgb",
    "soft_light_blend",
]
