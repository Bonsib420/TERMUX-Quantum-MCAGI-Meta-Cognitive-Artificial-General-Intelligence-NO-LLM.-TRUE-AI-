"""
Quantum Image Generator — Noise Module
=======================================
From-scratch Perlin noise, fractal Brownian motion, turbulence,
ridge noise, domain warping, and Voronoi (Worley) cellular noise.
Zero external dependencies.
"""

import math
import random


# ------------------------------------------------------------------ #
#  Perlin Gradient Noise (2-D)                                        #
# ------------------------------------------------------------------ #

class PerlinNoise:
    """Classic 2-D Perlin gradient noise with fBm helpers."""

    def __init__(self, seed=0):
        self.seed = seed
        rng = random.Random(seed)
        p = list(range(256))
        rng.shuffle(p)
        self._perm = p + p                     # doubled for index wrapping
        # 8 unit-length gradient directions
        self._grads = (
            (1, 1), (-1, 1), (1, -1), (-1, -1),
            (1, 0), (-1, 0), (0, 1), (0, -1),
        )

    # -- internal helpers ------------------------------------------------

    @staticmethod
    def _fade(t):
        """Quintic smoothstep  6t^5 - 15t^4 + 10t^3"""
        return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

    def _grad(self, h, x, y):
        g = self._grads[h & 7]
        return g[0] * x + g[1] * y

    # -- public API ------------------------------------------------------

    def noise2d(self, x, y):
        """Evaluate 2-D Perlin noise.  Returns ≈ [-1, 1]."""
        perm = self._perm
        _floor = math.floor

        xi = int(_floor(x)) & 255
        yi = int(_floor(y)) & 255
        xf = x - _floor(x)
        yf = y - _floor(y)

        u = self._fade(xf)
        v = self._fade(yf)

        aa = perm[perm[xi] + yi]
        ab = perm[perm[xi] + yi + 1]
        ba = perm[perm[xi + 1] + yi]
        bb = perm[perm[xi + 1] + yi + 1]

        x1 = self._grad(aa, xf, yf) * (1 - u) + self._grad(ba, xf - 1, yf) * u
        x2 = self._grad(ab, xf, yf - 1) * (1 - u) + self._grad(bb, xf - 1, yf - 1) * u
        return x1 * (1 - v) + x2 * v

    # -- layered noise ---------------------------------------------------

    def fbm(self, x, y, octaves=6, lacunarity=2.0, gain=0.5):
        """Fractal Brownian Motion — layered Perlin noise."""
        value = 0.0
        amplitude = 1.0
        frequency = 1.0
        total_amp = 0.0
        noise2d = self.noise2d          # avoid repeated lookup

        for _ in range(octaves):
            value += amplitude * noise2d(x * frequency, y * frequency)
            total_amp += amplitude
            amplitude *= gain
            frequency *= lacunarity

        return value / total_amp

    def turbulence(self, x, y, octaves=6, lacunarity=2.0, gain=0.5):
        """Turbulence — |noise| summation."""
        value = 0.0
        amplitude = 1.0
        frequency = 1.0
        total_amp = 0.0
        noise2d = self.noise2d

        for _ in range(octaves):
            value += amplitude * abs(noise2d(x * frequency, y * frequency))
            total_amp += amplitude
            amplitude *= gain
            frequency *= lacunarity

        return value / total_amp

    def ridge(self, x, y, octaves=6, lacunarity=2.0, gain=0.5, offset=1.0):
        """Ridged multi-fractal — sharp ridge-like features."""
        value = 0.0
        amplitude = 1.0
        frequency = 1.0
        prev = 1.0
        total_amp = 0.0
        noise2d = self.noise2d

        for _ in range(octaves):
            n = offset - abs(noise2d(x * frequency, y * frequency))
            n = n * n * prev
            prev = n
            value += n * amplitude
            total_amp += amplitude
            frequency *= lacunarity
            amplitude *= gain

        return value / total_amp

    def domain_warp(self, x, y, strength=1.0, detail=4):
        """Two-level domain warping — flowing organic distortion."""
        fbm = self.fbm
        qx = fbm(x, y, detail)
        qy = fbm(x + 5.2, y + 1.3, detail)
        rx = fbm(x + strength * qx + 1.7, y + strength * qy + 9.2, detail)
        ry = fbm(x + strength * qx + 8.3, y + strength * qy + 2.8, detail)
        return x + strength * rx, y + strength * ry


# ------------------------------------------------------------------ #
#  Voronoi / Worley Cellular Noise                                    #
# ------------------------------------------------------------------ #

class VoronoiNoise:
    """2-D Voronoi (Worley) cellular noise."""

    def __init__(self, seed=0):
        self.seed = seed
        self._cache = {}

    def _cell_point(self, cx, cy):
        key = (cx, cy)
        if key not in self._cache:
            h = hash((self.seed, cx, cy))
            px = cx + ((h & 0xFFFF) / 65535.0)
            py = cy + (((h >> 16) & 0xFFFF) / 65535.0)
            self._cache[key] = (px, py)
        return self._cache[key]

    def noise2d(self, x, y):
        """Return *(d1, d2)* — distances to two nearest cell points."""
        cx = int(math.floor(x))
        cy = int(math.floor(y))
        min_d = 1e30
        min2_d = 1e30

        for dx in range(-2, 3):
            for dy in range(-2, 3):
                px, py = self._cell_point(cx + dx, cy + dy)
                d = math.sqrt((x - px) ** 2 + (y - py) ** 2)
                if d < min_d:
                    min2_d = min_d
                    min_d = d
                elif d < min2_d:
                    min2_d = d

        return min_d, min2_d
