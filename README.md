# Quantum Image Generator

**From-scratch procedural image generator — zero external dependencies.**

Built entirely on the Python standard library (`math`, `struct`, `zlib`, `random`, `colorsys`).
No PIL, no NumPy, no ML models — every pixel is computed from pure mathematics.

## Features

| Technique | Description |
|---|---|
| **Perlin Noise** | Classic gradient noise with quintic interpolation |
| **Fractal Brownian Motion** | Multi-octave layered noise for natural textures |
| **Domain Warping** | Two-level coordinate distortion for flowing, organic shapes |
| **Ridge Noise** | Sharp ridge-like features for energy patterns |
| **Voronoi Noise** | Cellular patterns for quantum-field visualisation |
| **Gravitational Lensing** | Radial + tangential pixel displacement simulating light-bending |
| **Blackbody Colours** | Physically-based star and accretion-disk colouring |
| **Logarithmic Spirals** | Keplerian-inspired spiral arm rendering |
| **Separable Gaussian Bloom** | Efficient two-pass glow around bright regions |
| **ACES Tone Mapping** | Filmic HDR-to-SDR conversion |
| **Cinematic Colour Grading** | Tint, contrast, saturation, shadow-colour adjustments |

## Quick Start

```bash
# Generate a cosmic vortex (default 512×512 PNG)
python -m quantum_image_generator --preset cosmic_vortex -o vortex.png

# Generate a nebula at 1024×1024
python -m quantum_image_generator --preset nebula --width 1024 --height 1024

# Generate all presets
python -m quantum_image_generator --all

# Use a custom seed for unique results
python -m quantum_image_generator --preset galaxy --seed 99 -o galaxy.png

# Output BMP instead of PNG
python -m quantum_image_generator --preset quantum_field --format bmp
```

## Presets

| Preset | Description |
|---|---|
| `cosmic_vortex` | Black hole with swirling accretion disk and gravitational lensing |
| `nebula` | Colourful interstellar gas cloud with emission layers |
| `galaxy` | Spiral galaxy with central bulge |
| `quantum_field` | Abstract quantum energy-field with Voronoi cells and ridges |

## CLI Options

```
--preset PRESET     Scene preset (default: cosmic_vortex)
--width  WIDTH      Image width in pixels (default: 512)
--height HEIGHT     Image height in pixels (default: 512)
--seed   SEED       Random seed for reproducibility (default: 42)
-o, --output FILE   Output filename (default: <preset>.png)
--format {png,bmp}  Output format (default: png)
--all               Generate every preset
```

## Python API

```python
from quantum_image_generator import create_cosmic_vortex, PerlinNoise, PixelBuffer

# Use a preset
buf = create_cosmic_vortex(width=512, height=512, seed=42)
buf.save("vortex.png")

# Build a custom scene
from quantum_image_generator import (
    render_starfield, render_nebula_layer, render_spiral_arms,
    apply_bloom, apply_vignette, apply_tone_mapping,
)

buf = PixelBuffer(512, 512)
noise = PerlinNoise(seed=7)
render_nebula_layer(buf, noise, scale=3.0, opacity=0.8, warp_strength=2.0)
render_starfield(buf, density=0.005)
apply_bloom(buf, radius=8, threshold=0.6, intensity=0.4)
apply_tone_mapping(buf)
buf.save("custom_scene.png")
```

## Architecture

```
quantum_image_generator/
├── __init__.py     # Public API
├── __main__.py     # CLI entry-point
├── core.py         # PixelBuffer, image I/O (BMP + PNG), colour math
├── noise.py        # Perlin noise, fBm, turbulence, ridges, Voronoi
└── renderer.py     # Scene generators, compositing, post-processing
```

Every module uses **only the Python standard library**.
No `pip install` required — clone and run.

## Performance

| Resolution | cosmic_vortex | nebula | galaxy | quantum_field |
|---|---|---|---|---|
| 64×64 | ~0.5 s | ~0.5 s | ~0.1 s | ~0.3 s |
| 256×256 | ~8 s | ~6 s | ~3 s | ~5 s |
| 512×512 | ~30 s | ~25 s | ~12 s | ~20 s |

*(Times approximate — pure Python, single-threaded)*

## How It Works

1. **HDR Rendering** — All computation happens in unbounded floating-point.
   Pixels can exceed 1.0, enabling realistic bright regions.

2. **Layered Compositing** — Background → nebula clouds → spiral arms →
   accretion glow → light streaks → gravitational lensing → stars.

3. **Post-Processing Pipeline** — Bloom extracts bright pixels, applies
   separable Gaussian blur, and adds the glow back. Vignette darkens edges.
   ACES tone mapping compresses HDR to displayable range. Colour grading
   adds the final cinematic feel.

4. **Deterministic Seeds** — Every `--seed` value produces the exact same
   image, making results fully reproducible and shareable.
