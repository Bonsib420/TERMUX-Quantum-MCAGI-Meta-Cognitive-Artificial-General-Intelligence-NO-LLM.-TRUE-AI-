"""
🎨 QUANTUM IMAGE GENERATOR v1.0
Pure math + physics-based image generation. No API keys. Runs anywhere.
Renders: black holes, nebulae, galaxies, quantum states, wormholes,
supernovae, planets, fractals, neural patterns, consciousness fields.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
from scipy.ndimage import zoom
import re
import math
import hashlib
import logging

logger = logging.getLogger("quantum_image_gen")

# ============ Helper Functions ============

def _seed_from_prompt(prompt: str) -> int:
    """Generate deterministic seed from prompt text"""
    return int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)


def _fbm_noise(shape, octaves=6, persistence=0.5, seed=42):
    """Fractional Brownian Motion noise"""
    rng = np.random.RandomState(seed)
    result = np.zeros(shape, dtype=np.float64)
    amplitude = 1.0
    total_amp = 0.0

    for i in range(octaves):
        freq = 2 ** i
        base_h = max(3, shape[0] // freq + 2)
        base_w = max(3, shape[1] // freq + 2)
        noise_layer = rng.rand(base_h, base_w)
        noise_layer = ndimage.gaussian_filter(noise_layer, sigma=0.8)

        scaled = zoom(noise_layer,
                     (shape[0] / noise_layer.shape[0],
                      shape[1] / noise_layer.shape[1]),
                     order=3)
        scaled = scaled[:shape[0], :shape[1]]

        result += scaled * amplitude
        total_amp += amplitude
        amplitude *= persistence

    return result / total_amp


def _radial_gradient(shape, cx=None, cy=None):
    """Radial distance from center"""
    h, w = shape
    if cx is None:
        cx = w / 2
    if cy is None:
        cy = h / 2
    y, x = np.mgrid[0:h, 0:w]
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    r = r / max(r.max(), 1e-6)
    return r


def _bloom(img_array, threshold=200, radius=8, intensity=0.6):
    """Add bloom/glow effect to bright areas"""
    bright = np.clip(img_array.astype(np.float64) - threshold, 0, 255)
    blurred = ndimage.gaussian_filter(bright, sigma=radius)
    result = img_array.astype(np.float64) + blurred * intensity
    return np.clip(result, 0, 255).astype(np.uint8)


def _vignette(shape, strength=0.7):
    """Vignette darkening at edges"""
    r = _radial_gradient(shape)
    v = 1.0 - (r ** 1.8) * strength
    return np.clip(v, 0, 1)


def _star_field(shape, density=800, seed=42):
    """Generate star field background"""
    rng = np.random.RandomState(seed)
    h, w = shape
    stars = np.zeros((h, w, 3), dtype=np.float64)
    n_stars = density
    xs = rng.randint(0, w, n_stars)
    ys = rng.randint(0, h, n_stars)
    brightnesses = rng.power(0.5, n_stars)
    temps = rng.uniform(3000, 20000, n_stars)

    for i in range(n_stars):
        x, y = xs[i], ys[i]
        b = brightnesses[i]
        t = temps[i]
        r_c, g_c, b_c = _blackbody_color(t)
        size = 1 if b < 0.7 else (2 if b < 0.9 else 3)
        lum = b * 255

        for dy in range(-size, size + 1):
            for dx in range(-size, size + 1):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w:
                    d = math.sqrt(dx * dx + dy * dy)
                    falloff = max(0, 1.0 - d / (size + 0.5))
                    falloff = falloff ** 1.5
                    stars[ny, nx, 0] += lum * r_c * falloff
                    stars[ny, nx, 1] += lum * g_c * falloff
                    stars[ny, nx, 2] += lum * b_c * falloff

    return np.clip(stars, 0, 255)


def _blackbody_color(temp):
    """Blackbody radiation color from temperature (in Kelvin)"""
    t = temp / 100.0
    if t <= 66:
        r = 1.0
        g = max(0, min(1, (99.4708025861 * math.log(t) - 161.1195681661) / 255.0)) if t > 1 else 0
    else:
        r = max(0, min(1, (329.698727446 * ((t - 60) ** -0.1332047592)) / 255.0))
        g = max(0, min(1, (288.1221695283 * ((t - 60) ** -0.0755148492)) / 255.0))
    if t >= 66:
        b = 1.0
    elif t <= 19:
        b = 0.0
    else:
        b = max(0, min(1, (138.5177312231 * math.log(t - 10) - 305.0447927307) / 255.0))
    return r, g, b


def _color_map(value, palette):
    """Map 0-1 values to RGB colors from palette via linear interpolation"""
    value = np.clip(value, 0, 1)
    n = len(palette) - 1
    idx = value * n
    low = np.floor(idx).astype(int)
    low = np.clip(low, 0, n - 1)
    high = np.clip(low + 1, 0, n)
    frac = idx - low
    result = np.zeros((*value.shape, 3), dtype=np.float64)
    for c in range(3):
        low_vals = np.array([palette[i][c] for i in range(len(palette))])
        result[..., c] = low_vals[low] * (1 - frac) + low_vals[high] * frac
    return result


# Color palettes for nebulae
NEBULA_PALETTES = {
    'fire': [(0, 0, 0), (80, 10, 5), (180, 40, 10), (255, 120, 20), (255, 200, 80), (255, 255, 200)],
    'ice': [(0, 0, 10), (10, 20, 60), (30, 60, 140), (80, 140, 200), (160, 210, 255), (230, 245, 255)],
    'cosmic': [(0, 0, 5), (40, 5, 60), (100, 20, 120), (160, 40, 140), (200, 80, 180), (255, 180, 255)],
    'emerald': [(0, 5, 0), (10, 40, 20), (20, 100, 50), (60, 180, 80), (120, 230, 140), (200, 255, 220)],
    'plasma': [(0, 0, 0), (60, 0, 80), (120, 0, 160), (200, 60, 120), (255, 140, 60), (255, 240, 180)],
    'void': [(0, 0, 0), (15, 5, 30), (30, 10, 50), (50, 15, 70), (80, 30, 100), (120, 50, 140)],
}


# ============ Renderers ============

def render_black_hole(w, h, seed, params=None):
    """Render a black hole with accretion disk, photon ring, and gravitational lensing"""
    params = params or {}
    rng = np.random.RandomState(seed)
    img = np.zeros((h, w, 3), dtype=np.float64)
    stars = _star_field((h, w), density=1200, seed=seed)
    cx, cy = w / 2, h / 2
    bh_radius = min(w, h) * 0.15
    photon_ring = bh_radius * 1.5
    accretion_outer = bh_radius * 3.5
    accretion_inner = bh_radius * 1.8

    y, x = np.mgrid[0:h, 0:w]
    dx = (x - cx).astype(np.float64)
    dy = (y - cy).astype(np.float64)
    r = np.sqrt(dx ** 2 + dy ** 2)
    theta = np.arctan2(dy, dx)

    # Gravitational lensing
    lensing_strength = 2.5
    lens_factor = np.where(r > bh_radius,
                           1.0 + lensing_strength * (bh_radius / np.maximum(r, 1)) ** 2,
                           0.0)
    lensed_x = (cx + dx * lens_factor).astype(int)
    lensed_y = (cy + dy * lens_factor).astype(int)
    lensed_x = np.clip(lensed_x, 0, w - 1)
    lensed_y = np.clip(lensed_y, 0, h - 1)

    for c in range(3):
        img[..., c] = stars[lensed_y, lensed_x, c]

    # Accretion disk
    tilt = params.get('tilt', 0.3)
    disk_y = dy * math.cos(tilt * math.pi)
    disk_r = np.sqrt(dx ** 2 + disk_y ** 2)
    thin_disk = np.exp(-((dy * math.cos(tilt * math.pi)) ** 2) / (2 * (bh_radius * 0.15) ** 2))
    thin_disk *= ((disk_r > accretion_inner) & (disk_r < accretion_outer)).astype(float)
    disk_temp = np.clip(1.0 - (disk_r - accretion_inner) / (accretion_outer - accretion_inner), 0, 1)
    disk_temp = disk_temp ** 0.6
    doppler = 1.0 + 0.4 * np.sin(theta)
    disk_temp_shifted = np.clip(disk_temp * doppler, 0, 1)
    noise_disk = _fbm_noise((h, w), octaves=4, seed=seed + 1)
    disk_detail = 0.6 + 0.4 * noise_disk

    for c, base in enumerate([(255, 180, 60), (120, 60, 20), (40, 20, 5)]):
        hot_color = np.array([255, 220, 180])[c]
        cool_color = np.array([180, 60, 10])[c]
        disk_color = cool_color + (hot_color - cool_color) * disk_temp_shifted
        img[..., c] += disk_color * thin_disk * disk_detail * 1.5

    # Photon ring
    ring_mask = np.exp(-((r - photon_ring) ** 2) / (2 * (bh_radius * 0.05) ** 2))
    for c, val in enumerate([255, 240, 200]):
        img[..., c] += ring_mask * val * 0.8

    # Event horizon fade
    event_horizon = np.where(r < bh_radius, 0.0, 1.0)
    fade = np.clip((r - bh_radius * 0.8) / (bh_radius * 0.2), 0, 1)
    for c in range(3):
        img[..., c] *= fade

    # Jets
    if params.get('jets', True):
        jet_width = bh_radius * 0.08
        jet_length = min(h, w) * 0.4
        for sign in [-1, 1]:
            jet_y_center = cy + sign * np.arange(0, jet_length)
            for jy in jet_y_center.astype(int):
                if 0 <= jy < h:
                    dist_from_bh = abs(jy - cy)
                    intensity = max(0, 1.0 - dist_from_bh / jet_length) ** 1.5
                    spread = jet_width * (1 + dist_from_bh / jet_length)
                    for jx in range(max(0, int(cx - spread)), min(w, int(cx + spread))):
                        dx_j = abs(jx - cx)
                        profile = math.exp(-(dx_j ** 2) / (2 * (spread * 0.3) ** 2))
                        img[jy, jx, 0] += 100 * intensity * profile
                        img[jy, jx, 1] += 140 * intensity * profile
                        img[jy, jx, 2] += 255 * intensity * profile

    # Post-processing
    vig = _vignette((h, w), 0.5)
    for c in range(3):
        img[..., c] *= vig
    img = np.clip(img, 0, 255).astype(np.uint8)
    img = _bloom(img, threshold=180, radius=6, intensity=0.5)
    return img


def render_nebula(w, h, seed, params=None):
    """Render nebula clouds with multiple palettes and fine detail"""
    params = params or {}
    palette_name = params.get('palette', 'cosmic')
    palette = NEBULA_PALETTES.get(palette_name, NEBULA_PALETTES['cosmic'])
    rng = np.random.RandomState(seed)

    stars = _star_field((h, w), density=800, seed=seed)
    img = stars.copy()

    y_grid, x_grid = np.mgrid[0:h, 0:w]
    cloud_base = np.zeros((h, w), dtype=np.float64)

    n_centers = rng.randint(3, 7)
    for i in range(n_centers):
        cx = rng.uniform(w * 0.1, w * 0.9)
        cy = rng.uniform(h * 0.1, h * 0.9)
        spread_x = rng.uniform(w * 0.15, w * 0.4)
        spread_y = rng.uniform(h * 0.15, h * 0.4)
        amp = rng.uniform(0.3, 1.0)
        angle = rng.uniform(0, math.pi)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        dx = (x_grid - cx)
        dy = (y_grid - cy)
        rx = dx * cos_a + dy * sin_a
        ry = -dx * sin_a + dy * cos_a
        blob = np.exp(-(rx ** 2) / (2 * spread_x ** 2) - (ry ** 2) / (2 * spread_y ** 2))
        cloud_base += blob * amp

    cloud_base = cloud_base / (cloud_base.max() + 1e-8)

    detail = _fbm_noise((h, w), octaves=7, persistence=0.55, seed=seed + 10)
    fine = _fbm_noise((h, w), octaves=5, persistence=0.6, seed=seed + 20)

    warp_u = _fbm_noise((h, w), octaves=4, seed=seed + 300)
    warp_v = _fbm_noise((h, w), octaves=4, seed=seed + 310)
    warp_s = min(w, h) * 0.1
    wx = np.clip((x_grid + (warp_u - 0.5) * warp_s).astype(int), 0, w - 1)
    wy = np.clip((y_grid + (warp_v - 0.5) * warp_s).astype(int), 0, h - 1)

    combined = cloud_base[wy, wx] * (0.4 + 0.6 * detail)
    combined *= (0.6 + 0.4 * fine)
    combined = (combined - combined.min()) / (combined.max() - combined.min() + 1e-8)
    combined = combined ** 0.9

    nebula_colors = _color_map(combined, palette)
    density = np.clip(combined * 1.8 - 0.15, 0, 1)
    for c in range(3):
        img[..., c] = img[..., c] * (1 - density * 0.9) + nebula_colors[..., c] * density

    # Secondary color layer
    secondary_map = {'fire': 'plasma', 'ice': 'cosmic', 'cosmic': 'plasma',
                     'emerald': 'ice', 'plasma': 'fire', 'void': 'cosmic'}
    sec_palette = NEBULA_PALETTES[secondary_map.get(palette_name, 'cosmic')]
    sec_noise = _fbm_noise((h, w), octaves=5, seed=seed + 800)
    sec_density = np.clip(sec_noise - 0.4, 0, 1) * combined * 0.35
    sec_colors = _color_map(sec_noise, sec_palette)
    for c in range(3):
        img[..., c] += sec_colors[..., c] * sec_density

    # Filaments
    fil = _fbm_noise((h, w), octaves=8, persistence=0.7, seed=seed + 400)
    filaments = np.exp(-(np.abs(fil - 0.5) * 30)) * 0.8
    filaments *= (combined > 0.1).astype(float)
    for c in range(3):
        img[..., c] += filaments * palette[-1][c] * 0.5

    # Hot spots
    bright_noise = _fbm_noise((h, w), octaves=3, seed=seed + 500)
    hot = (bright_noise > 0.7).astype(float) * (combined > 0.35).astype(float)
    hot = ndimage.gaussian_filter(hot, sigma=min(w, h) * 0.012)
    for c in range(3):
        img[..., c] += hot * 240 * (palette[-1][c] / 255.0)

    # Embedded stars
    n_stars_embedded = rng.randint(3, 8)
    for _ in range(n_stars_embedded):
        sx, sy = rng.randint(0, w), rng.randint(0, h)
        if combined[min(sy, h - 1), min(sx, w - 1)] > 0.25:
            sr = rng.uniform(min(w, h) * 0.008, min(w, h) * 0.025)
            glow = np.exp(-((x_grid - sx) ** 2 + (y_grid - sy) ** 2) / (2 * sr ** 2))
            for c in range(3):
                img[..., c] += glow * 255 * rng.uniform(0.5, 1.0)

    vig = _vignette((h, w), 0.5)
    for c in range(3):
        img[..., c] *= vig
    img = np.clip(img, 0, 255).astype(np.uint8)
    img = _bloom(img, threshold=130, radius=14, intensity=0.5)
    return img


def render_galaxy(w, h, seed, params=None):
    """Render spiral galaxy with arms and star field"""
    params = params or {}
    rng = np.random.RandomState(seed)
    img = np.zeros((h, w, 3), dtype=np.float64)
    stars_bg = _star_field((h, w), density=500, seed=seed)
    img += stars_bg
    cx, cy = w / 2, h / 2
    y, x = np.mgrid[0:h, 0:w]
    dx = (x - cx).astype(np.float64)
    dy = (y - cy).astype(np.float64)
    tilt = params.get('tilt', 0.6)
    dy_tilted = dy / max(math.cos(tilt), 0.3)
    r = np.sqrt(dx ** 2 + dy_tilted ** 2)
    theta = np.arctan2(dy_tilted, dx)
    galaxy_r = min(w, h) * 0.35
    n_arms = params.get('arms', 2)
    arm_tightness = 0.4
    arm_pattern = np.zeros((h, w), dtype=np.float64)

    for arm in range(n_arms):
        arm_offset = arm * 2 * math.pi / n_arms
        spiral_angle = theta - arm_tightness * np.log(np.maximum(r, 1)) - arm_offset
        arm_dist = np.abs(np.sin(spiral_angle))
        arm_width = 0.15 + 0.1 * (r / galaxy_r)
        arm_intensity = np.exp(-(arm_dist ** 2) / (2 * arm_width ** 2))
        arm_intensity *= np.exp(-r / galaxy_r)
        arm_pattern += arm_intensity

    arm_pattern = np.clip(arm_pattern, 0, 1)
    noise = _fbm_noise((h, w), octaves=5, seed=seed + 10)
    arm_pattern *= (0.6 + 0.4 * noise)
    core_glow = np.exp(-r ** 2 / (2 * (galaxy_r * 0.15) ** 2))
    palette = [(255, 200, 150), (200, 150, 255), (150, 180, 255)]
    for c in range(3):
        core_c = [255, 240, 200][c]
        arm_c = palette[c % len(palette)][c]
        img[..., c] += core_glow * core_c * 1.2
        img[..., c] += arm_pattern * arm_c * 0.8

    # Galactic stars
    n_gal_stars = 3000
    for _ in range(n_gal_stars):
        angle = rng.uniform(0, 2 * math.pi)
        radius = rng.exponential(galaxy_r * 0.3)
        arm_idx = rng.randint(0, n_arms)
        spiral_offset = arm_tightness * math.log(max(radius, 1)) + arm_idx * 2 * math.pi / n_arms
        angle = spiral_offset + rng.normal(0, 0.2)
        sx = int(cx + radius * math.cos(angle))
        sy = int(cy + radius * math.sin(angle) * math.cos(tilt))
        if 0 <= sx < w and 0 <= sy < h:
            brightness = rng.uniform(50, 255) * math.exp(-radius / galaxy_r)
            temp = rng.uniform(4000, 15000)
            rc, gc, bc = _blackbody_color(temp)
            img[sy, sx, 0] += brightness * rc
            img[sy, sx, 1] += brightness * gc
            img[sy, sx, 2] += brightness * bc

    vig = _vignette((h, w), 0.5)
    for c in range(3):
        img[..., c] *= vig
    img = np.clip(img, 0, 255).astype(np.uint8)
    img = _bloom(img, threshold=150, radius=8, intensity=0.5)
    return img


def render_quantum_state(w, h, seed, params=None):
    """Render quantum probability wave visualization"""
    params = params or {}
    rng = np.random.RandomState(seed)
    img = np.zeros((h, w, 3), dtype=np.float64)
    y, x = np.mgrid[0:h, 0:w]
    cx, cy = w / 2, h / 2
    dx = (x - cx) / (w / 2)
    dy = (y - cy) / (h / 2)
    r = np.sqrt(dx ** 2 + dy ** 2)

    n_modes = rng.randint(3, 7)
    psi_real = np.zeros((h, w), dtype=np.float64)
    psi_imag = np.zeros((h, w), dtype=np.float64)

    for _ in range(n_modes):
        kx = rng.uniform(-8, 8)
        ky = rng.uniform(-8, 8)
        phase = rng.uniform(0, 2 * math.pi)
        amp = rng.uniform(0.5, 1.5)
        psi_real += amp * np.cos(kx * dx * math.pi + ky * dy * math.pi + phase)
        psi_imag += amp * np.sin(kx * dx * math.pi + ky * dy * math.pi + phase)

    prob = psi_real ** 2 + psi_imag ** 2
    prob = prob / (prob.max() + 1e-8)
    phase = np.arctan2(psi_imag, psi_real)
    phase_norm = (phase + math.pi) / (2 * math.pi)
    phase_palette = [
        (0, 60, 255), (0, 200, 200), (0, 255, 60),
        (255, 255, 0), (255, 100, 0), (255, 0, 100),
        (200, 0, 255), (0, 60, 255)
    ]
    phase_colors = _color_map(phase_norm, phase_palette)
    envelope = np.exp(-r ** 2 / 0.8)
    prob *= envelope
    for c in range(3):
        img[..., c] = phase_colors[..., c] * prob * 1.5

    stars = _star_field((h, w), density=200, seed=seed)
    for c in range(3):
        img[..., c] += stars[..., c] * (1 - prob * 0.8)

    interference = np.cos(prob * 20 * math.pi) * 0.5 + 0.5
    for c in range(3):
        img[..., c] *= (0.7 + 0.3 * interference)

    contour_lines = np.abs(np.sin(prob * 15 * math.pi))
    contour_lines = (contour_lines < 0.05).astype(float) * prob * 0.3
    for c in range(3):
        img[..., c] += contour_lines * 200

    vig = _vignette((h, w), 0.4)
    for c in range(3):
        img[..., c] *= vig
    img = np.clip(img, 0, 255).astype(np.uint8)
    img = _bloom(img, threshold=140, radius=6, intensity=0.4)
    return img


def render_wormhole(w, h, seed, params=None):
    """Render an Einstein-Rosen bridge (wormhole)"""
    params = params or {}
    img = np.zeros((h, w, 3), dtype=np.float64)
    cx, cy = w / 2, h / 2
    y, x = np.mgrid[0:h, 0:w]
    dx = (x - cx).astype(np.float64)
    dy = (y - cy).astype(np.float64)
    r = np.sqrt(dx ** 2 + dy ** 2)
    theta = np.arctan2(dy, dx)
    throat_radius = min(w, h) * 0.08
    tunnel_depth = 15.0
    depth = np.where(r > throat_radius,
                     tunnel_depth * (throat_radius / np.maximum(r, 1)) ** 0.8,
                     tunnel_depth)
    tunnel_pattern = np.sin(depth * 3 + theta * 4) * 0.5 + 0.5
    noise = _fbm_noise((h, w), octaves=5, seed=seed)
    tunnel_pattern *= (0.5 + 0.5 * noise)
    ring_dist = np.abs(r - throat_radius * 2)
    ring_glow = np.exp(-ring_dist ** 2 / (2 * (throat_radius * 0.3) ** 2))
    warp_factor = np.where(r > throat_radius,
                          (throat_radius / np.maximum(r, 1)) ** 1.5,
                          1.0)
    edge_glow = np.exp(-((r - throat_radius) ** 2) / (2 * (throat_radius * 0.15) ** 2))
    palette = [(0, 0, 20), (20, 40, 120), (80, 100, 200), (150, 180, 255), (220, 240, 255)]
    tunnel_colors = _color_map(tunnel_pattern * warp_factor, palette)
    for c in range(3):
        img[..., c] = tunnel_colors[..., c]
    for c, val in enumerate([200, 220, 255]):
        img[..., c] += ring_glow * val * 0.6
    for c, val in enumerate([100, 200, 255]):
        img[..., c] += edge_glow * val * 1.2
    inner_mask = (r < throat_radius * 0.6).astype(float)
    dest_stars = _star_field((h, w), density=400, seed=seed + 999)
    dest_nebula = _fbm_noise((h, w), octaves=4, seed=seed + 888)
    fade_in = np.clip(1.0 - r / (throat_radius * 0.6), 0, 1) * inner_mask
    for c in range(3):
        dest_color = [80, 40, 120][c]
        img[..., c] += (dest_stars[..., c] * 0.5 + dest_nebula * dest_color * 0.3) * fade_in
    stars = _star_field((h, w), density=800, seed=seed)
    outer_mask = np.clip((r - throat_radius * 3) / (throat_radius * 2), 0, 1)
    for c in range(3):
        img[..., c] += stars[..., c] * outer_mask
    vig = _vignette((h, w), 0.5)
    for c in range(3):
        img[..., c] *= vig
    img = np.clip(img, 0, 255).astype(np.uint8)
    img = _bloom(img, threshold=150, radius=8, intensity=0.5)
    return img


def render_supernova(w, h, seed, params=None):
    """Render supernova explosion"""
    params = params or {}
    rng = np.random.RandomState(seed)
    img = np.zeros((h, w, 3), dtype=np.float64)
    stars = _star_field((h, w), density=800, seed=seed)
    img += stars
    cx, cy = w / 2, h / 2
    y, x = np.mgrid[0:h, 0:w]
    dx = (x - cx).astype(np.float64)
    dy = (y - cy).astype(np.float64)
    r = np.sqrt(dx ** 2 + dy ** 2)
    theta = np.arctan2(dy, dx)
    blast_radius = min(w, h) * 0.35
    core_radius = min(w, h) * 0.03
    core_glow = np.exp(-r ** 2 / (2 * core_radius ** 2))
    for c, val in enumerate([255, 255, 240]):
        img[..., c] += core_glow * val * 2.0

    # Rays
    n_rays = rng.randint(12, 24)
    for i in range(n_rays):
        ray_angle = i * 2 * math.pi / n_rays + rng.uniform(-0.1, 0.1)
        ray_width = rng.uniform(0.03, 0.08)
        ray_length = blast_radius * rng.uniform(0.5, 1.0)
        angle_diff = np.abs(np.mod(theta - ray_angle + math.pi, 2 * math.pi) - math.pi)
        ray_mask = np.exp(-(angle_diff ** 2) / (2 * ray_width ** 2))
        ray_mask *= np.exp(-r / ray_length)
        ray_mask *= (r > core_radius * 2).astype(float)
        ray_temp = rng.uniform(5000, 30000)
        rc, gc, bc = _blackbody_color(ray_temp)
        intensity = rng.uniform(150, 255)
        img[..., 0] += ray_mask * intensity * rc
        img[..., 1] += ray_mask * intensity * gc
        img[..., 2] += ray_mask * intensity * bc

    # Shells
    shell_r = blast_radius * 0.7
    shell_width = blast_radius * 0.1
    shell = np.exp(-((r - shell_r) ** 2) / (2 * shell_width ** 2))
    shell_noise = _fbm_noise((h, w), octaves=6, seed=seed + 50)
    shell *= (0.4 + 0.6 * shell_noise)
    for c, val in enumerate([200, 100, 50]):
        img[..., c] += shell * val
    inner_shell_r = blast_radius * 0.4
    inner_shell = np.exp(-((r - inner_shell_r) ** 2) / (2 * (shell_width * 0.7) ** 2))
    for c, val in enumerate([100, 180, 255]):
        img[..., c] += inner_shell * val * 0.5

    vig = _vignette((h, w), 0.5)
    for c in range(3):
        img[..., c] *= vig
    img = np.clip(img, 0, 255).astype(np.uint8)
    img = _bloom(img, threshold=140, radius=12, intensity=0.7)
    return img


def render_planet(w, h, seed, params=None):
    """Render a planet with atmosphere and surface features"""
    params = params or {}
    rng = np.random.RandomState(seed)
    img = np.zeros((h, w, 3), dtype=np.float64)
    stars = _star_field((h, w), density=600, seed=seed)
    img += stars
    cx, cy = w / 2, h / 2
    planet_r = min(w, h) * 0.3
    y, x = np.mgrid[0:h, 0:w]
    dx = (x - cx).astype(np.float64)
    dy = (y - cy).astype(np.float64)
    r = np.sqrt(dx ** 2 + dy ** 2)
    planet_mask = (r <= planet_r).astype(float)
    norm_r = r / planet_r
    nx = dx / np.maximum(r, 1e-6)
    ny = dy / np.maximum(r, 1e-6)
    nz = np.sqrt(np.maximum(1 - norm_r ** 2, 0))
    light_dir = np.array([0.5, -0.3, 0.8])
    light_dir /= np.linalg.norm(light_dir)
    shading = nx * light_dir[0] + ny * light_dir[1] + nz * light_dir[2]
    shading = np.clip(shading, 0, 1) * planet_mask

    planet_type = params.get('type', rng.choice(['rocky', 'gas', 'ice', 'lava']))

    if planet_type == 'gas':
        band_noise = _fbm_noise((h, w), octaves=6, seed=seed + 10)
        bands = np.sin((dy / planet_r) * 15 + band_noise * 3) * 0.5 + 0.5
        colors = _color_map(bands, [
            (180, 140, 80), (200, 160, 100), (160, 120, 60),
            (220, 180, 120), (140, 100, 50), (200, 160, 90)
        ])
        spot_r = planet_r * 0.15
        spot_cx, spot_cy = cx + planet_r * 0.2, cy + planet_r * 0.1
        spot_dist = np.sqrt((x - spot_cx) ** 2 + (y - spot_cy) ** 2)
        spot = np.exp(-(spot_dist ** 2) / (2 * spot_r ** 2)) * planet_mask
        colors[..., 0] += spot * 80
        colors[..., 1] -= spot * 30

    elif planet_type == 'ice':
        surface = _fbm_noise((h, w), octaves=7, seed=seed + 20)
        colors = _color_map(surface, [
            (180, 210, 230), (200, 230, 250), (220, 240, 255),
            (160, 200, 240), (140, 180, 220)
        ])
        cracks = _fbm_noise((h, w), octaves=8, persistence=0.7, seed=seed + 30)
        crack_lines = (np.abs(cracks - 0.5) < 0.02).astype(float)
        for c in range(3):
            colors[..., c] += crack_lines * 60

    elif planet_type == 'lava':
        surface = _fbm_noise((h, w), octaves=6, seed=seed + 40)
        colors = _color_map(surface, [
            (40, 20, 10), (80, 30, 10), (60, 25, 10),
            (100, 40, 15), (50, 20, 8)
        ])
        lava = _fbm_noise((h, w), octaves=4, seed=seed + 50)
        lava_mask = (lava > 0.65).astype(float)
        lava_mask = ndimage.gaussian_filter(lava_mask, sigma=2)
        colors[..., 0] += lava_mask * 200
        colors[..., 1] += lava_mask * 80
        colors[..., 2] += lava_mask * 10

    else:  # rocky
        surface = _fbm_noise((h, w), octaves=7, seed=seed + 60)
        colors = _color_map(surface, [
            (60, 80, 40), (80, 100, 50), (100, 120, 60),
            (140, 130, 100), (120, 110, 80), (80, 90, 45)
        ])
        ocean = (surface < 0.4).astype(float)
        for c, val in enumerate([30, 60, 140]):
            colors[..., c] = colors[..., c] * (1 - ocean) + val * ocean

    for c in range(3):
        img[..., c] = img[..., c] * (1 - planet_mask) + colors[..., c] * shading * planet_mask

    # Atmosphere glow
    atmo_dist = np.abs(r - planet_r)
    atmo_glow = np.exp(-(atmo_dist ** 2) / (2 * (planet_r * 0.05) ** 2))
    atmo_glow *= (r > planet_r * 0.95).astype(float)
    atmo_colors = {'gas': (200, 180, 120), 'ice': (150, 200, 255),
                  'lava': (255, 100, 30), 'rocky': (100, 150, 255)}
    ac = atmo_colors.get(planet_type, (100, 150, 255))
    for c in range(3):
        img[..., c] += atmo_glow * ac[c] * 0.6

    vig = _vignette((h, w), 0.4)
    for c in range(3):
        img[..., c] *= vig
    img = np.clip(img, 0, 255).astype(np.uint8)
    img = _bloom(img, threshold=180, radius=6, intensity=0.3)
    return img


def render_fractal(w, h, seed, params=None):
    """Render Mandelbrot/Julia-like fractal"""
    params = params or {}
    rng = np.random.RandomState(seed)
    cx = rng.uniform(-0.8, 0.3)
    cy = rng.uniform(-0.6, 0.6)
    zoom_level = rng.uniform(0.5, 3.0)
    scale = 2.0 / (zoom_level * min(w, h))
    y_coords, x_coords = np.mgrid[0:h, 0:w]
    x0 = (x_coords - w / 2) * scale + cx
    y0 = (y_coords - h / 2) * scale + cy
    z_real = np.zeros((h, w), dtype=np.float64)
    z_imag = np.zeros((h, w), dtype=np.float64)
    iterations = np.zeros((h, w), dtype=np.float64)
    max_iter = 256
    mask = np.ones((h, w), dtype=bool)

    for i in range(max_iter):
        zr2 = z_real ** 2
        zi2 = z_imag ** 2
        escaped = (zr2 + zi2 > 4) & mask
        iterations[escaped] = i + 1 - np.log2(np.log2(np.sqrt(zr2[escaped] + zi2[escaped])))
        mask[escaped] = False
        if not mask.any():
            break
        z_imag[mask] = 2 * z_real[mask] * z_imag[mask] + y0[mask]
        z_real[mask] = zr2[mask] - zi2[mask] + x0[mask]

    iterations[mask] = max_iter
    norm_iter = iterations / max_iter
    norm_iter = np.sqrt(norm_iter)
    palette_choice = params.get('palette', rng.choice(['cosmic', 'fire', 'ice']))
    palette = NEBULA_PALETTES.get(palette_choice, NEBULA_PALETTES['cosmic'])
    colors = _color_map(norm_iter, palette)
    interior = (iterations >= max_iter)
    colors[interior] = [0, 0, 0]
    img = np.clip(colors, 0, 255).astype(np.uint8)
    img = _bloom(img, threshold=200, radius=4, intensity=0.3)
    return img


def render_neural(w, h, seed, params=None):
    """Render neural network/brain-like connectivity visualization"""
    params = params or {}
    rng = np.random.RandomState(seed)
    img = np.zeros((h, w, 3), dtype=np.float64)
    bg = _fbm_noise((h, w), octaves=5, seed=seed)
    bg = bg ** 2
    for c, val in enumerate([15, 5, 25]):
        img[..., c] = bg * val

    n_nodes = params.get('nodes', rng.randint(15, 40))
    nodes = []
    for _ in range(n_nodes):
        nodes.append((rng.randint(w * 0.1, w * 0.9),
                     rng.randint(h * 0.1, h * 0.9),
                     rng.uniform(5, 20)))

    pil_img = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(pil_img)

    # Connections
    for i, (x1, y1, r1) in enumerate(nodes):
        for j, (x2, y2, r2) in enumerate(nodes):
            if i >= j:
                continue
            dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
            max_dist = min(w, h) * 0.4
            if dist < max_dist and rng.random() < 0.4:
                alpha = int(max(20, 150 * (1 - dist / max_dist)))
                color_choice = rng.choice(['cyan', 'violet', 'white'])
                if color_choice == 'cyan':
                    c = (0, alpha, alpha)
                elif color_choice == 'violet':
                    c = (alpha // 2, 0, alpha)
                else:
                    c = (alpha // 2, alpha // 2, alpha // 2)
                draw.line([(x1, y1), (x2, y2)], fill=c, width=1)

                # Pulses along connection
                n_pulses = rng.randint(0, 3)
                for p in range(n_pulses):
                    t = rng.uniform(0.2, 0.8)
                    px = int(x1 + t * (x2 - x1))
                    py = int(y1 + t * (y2 - y1))
                    pr = rng.randint(2, 5)
                    draw.ellipse([px - pr, py - pr, px + pr, py + pr],
                                fill=(100, 200, 255, 200))

    # Nodes
    for x, y, radius in nodes:
        for ring_r in [radius * 1.5, radius]:
            draw.ellipse([x - ring_r, y - ring_r, x + ring_r, y + ring_r],
                        outline=(80, 40, 140), width=1)
        draw.ellipse([x - radius * 0.6, y - radius * 0.6,
                     x + radius * 0.6, y + radius * 0.6],
                    fill=(160, 100, 255))
        inner_r = radius * 0.3
        draw.ellipse([x - inner_r, y - inner_r, x + inner_r, y + inner_r],
                    fill=(220, 200, 255))

    img = np.array(pil_img).astype(np.float64)
    vig = _vignette((h, w), 0.5)
    for c in range(3):
        img[..., c] *= vig
    img = np.clip(img, 0, 255).astype(np.uint8)
    img = _bloom(img, threshold=120, radius=10, intensity=0.6)
    return img


def render_consciousness(w, h, seed, params=None):
    """Render consciousness field with quantum-like patterns"""
    params = params or {}
    rng = np.random.RandomState(seed)
    img = np.zeros((h, w, 3), dtype=np.float64)
    stars = _star_field((h, w), density=300, seed=seed)
    img += stars * 0.3
    cx, cy = w / 2, h / 2
    y, x = np.mgrid[0:h, 0:w]
    dx = (x - cx).astype(np.float64) / (w / 2)
    dy = (y - cy).astype(np.float64) / (h / 2)
    r = np.sqrt(dx ** 2 + dy ** 2)
    theta = np.arctan2(dy, dx)

    # Quantum tubes
    n_tubes = rng.randint(5, 12)
    for t in range(n_tubes):
        tube_angle = t * 2 * math.pi / n_tubes + rng.uniform(-0.2, 0.2)
        tube_len = rng.uniform(0.3, 0.8)
        tube_width = 0.02 + rng.uniform(0, 0.01)
        cos_a = math.cos(tube_angle)
        sin_a = math.sin(tube_angle)
        proj = dx * cos_a + dy * sin_a
        perp = np.abs(-dx * sin_a + dy * cos_a)
        tube_mask = np.exp(-(perp ** 2) / (2 * tube_width ** 2))
        tube_mask *= (proj > 0.05).astype(float) * (proj < tube_len).astype(float)
        wave = np.sin(proj * 30 + rng.uniform(0, 2 * math.pi)) * 0.5 + 0.5
        tube_mask *= (0.3 + 0.7 * wave)
        hue = rng.uniform(0, 1)
        if hue < 0.33:
            tc = (100, 200, 255)
        elif hue < 0.66:
            tc = (200, 100, 255)
        else:
            tc = (100, 255, 200)
        for c in range(3):
            img[..., c] += tube_mask * tc[c] * 0.6

    # Central core
    core_r = 0.12
    core = np.exp(-r ** 2 / (2 * core_r ** 2))
    pulse = np.sin(r * 40) * 0.3 + 0.7
    core *= pulse
    for c, val in enumerate([255, 200, 255]):
        img[..., c] += core * val * 0.8

    # Concentric rings
    n_rings = 5
    for i in range(n_rings):
        ring_r = 0.15 + i * 0.12
        ring = np.exp(-((r - ring_r) ** 2) / (2 * 0.008 ** 2))
        alpha = 0.4 * (1 - i / n_rings)
        for c, val in enumerate([150, 100, 255]):
            img[..., c] += ring * val * alpha

    # Decoherence
    coherence_noise = _fbm_noise((h, w), octaves=5, seed=seed + 77)
    decoherence = np.clip(r - 0.4, 0, 1) * coherence_noise
    for c in range(3):
        img[..., c] *= (1 - decoherence * 0.5)

    vig = _vignette((h, w), 0.5)
    for c in range(3):
        img[..., c] *= vig
    img = np.clip(img, 0, 255).astype(np.uint8)
    img = _bloom(img, threshold=120, radius=10, intensity=0.6)
    return img


# ============ Scene Detection & Main API ============

SCENE_KEYWORDS = {
    'black_hole': ['black hole', 'event horizon', 'singularity', 'gravitational', 'accretion',
                   'photon ring', 'schwarzschild', 'kerr', 'spacetime curvature', 'merg', 'jet'],
    'nebula': ['nebula', 'nebulae', 'gas cloud', 'stellar nursery', 'emission',
               'interstellar', 'cosmic dust', 'pillars', 'orion', 'carina', 'eagle'],
    'galaxy': ['galaxy', 'spiral', 'milky way', 'andromeda', 'galactic',
               'barred spiral', 'elliptical', 'star system'],
    'quantum_state': ['quantum', 'wavefunction', 'superposition', 'entangle',
                      'probability', 'schrodinger', 'qubit', 'quantum state',
                      'wave function', 'quantum field'],
    'wormhole': ['wormhole', 'einstein-rosen', 'bridge', 'portal', 'tunnel',
                 'spacetime tunnel', 'traversable'],
    'supernova': ['supernova', 'explosion', 'stellar death', 'nova', 'burst',
                  'star explod', 'detonation', 'stellar explosion', 'gamma ray'],
    'planet': ['planet', 'world', 'terrestrial', 'jovian', 'earth',
               'mars', 'jupiter', 'saturn', 'venus', 'exoplanet', 'moon'],
    'fractal': ['fractal', 'mandelbrot', 'julia', 'recursive', 'self-similar',
                'chaos', 'strange attractor', 'infinite', 'iteration'],
    'neural': ['neural', 'brain', 'neuron', 'synapse', 'network',
               'microtubule', 'axon', 'dendrite', 'cortex', 'cognitive'],
    'consciousness': ['consciousness', 'awareness', 'orch-or', 'penrose',
                      'hameroff', 'tubulin', 'orchestrated', 'subjective',
                      'qualia', 'mind', 'sentien'],
}

RENDERERS = {
    'black_hole': render_black_hole,
    'nebula': render_nebula,
    'galaxy': render_galaxy,
    'quantum_state': render_quantum_state,
    'wormhole': render_wormhole,
    'supernova': render_supernova,
    'planet': render_planet,
    'fractal': render_fractal,
    'neural': render_neural,
    'consciousness': render_consciousness,
}


def _detect_scene(prompt: str) -> tuple:
    """Detect which scene type best matches the prompt"""
    prompt_lower = prompt.lower()
    scores = {}
    for scene, keywords in SCENE_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in prompt_lower:
                score += len(kw)
        if score > 0:
            scores[scene] = score
    if not scores:
        return 'nebula', {}

    best = max(scores, key=scores.get)
    params = {}

    if best == 'black_hole':
        if 'merg' in prompt_lower:
            params['merging'] = True
        if 'jet' in prompt_lower:
            params['jets'] = True

    elif best == 'nebula':
        for name in NEBULA_PALETTES:
            if name in prompt_lower:
                params['palette'] = name
        if 'fire' in prompt_lower or 'red' in prompt_lower or 'hot' in prompt_lower:
            params['palette'] = 'fire'
        elif 'ice' in prompt_lower or 'blue' in prompt_lower or 'cold' in prompt_lower:
            params['palette'] = 'ice'
        elif 'green' in prompt_lower or 'emerald' in prompt_lower:
            params['palette'] = 'emerald'
        elif 'purple' in prompt_lower or 'violet' in prompt_lower:
            params['palette'] = 'cosmic'
        elif 'dark' in prompt_lower or 'void' in prompt_lower:
            params['palette'] = 'void'

    elif best == 'planet':
        if 'gas' in prompt_lower or 'jupiter' in prompt_lower:
            params['type'] = 'gas'
        elif 'ice' in prompt_lower or 'frozen' in prompt_lower:
            params['type'] = 'ice'
        elif 'lava' in prompt_lower or 'volcanic' in prompt_lower:
            params['type'] = 'lava'
        elif 'rocky' in prompt_lower or 'mars' in prompt_lower:
            params['type'] = 'rocky'

    elif best == 'galaxy':
        if 'barred' in prompt_lower:
            params['arms'] = 2

    return best, params


def _render_merging_black_holes(w, h, seed, params=None):
    """Special effect for merging black holes"""
    params = params or {}
    img = np.zeros((h, w, 3), dtype=np.float64)
    stars = _star_field((h, w), density=1000, seed=seed)
    separation = min(w, h) * 0.2
    cx1, cy1 = w / 2 - separation * 0.5, h / 2
    cx2, cy2 = w / 2 + separation * 0.5, h / 2
    y, x = np.mgrid[0:h, 0:w]

    for (bcx, bcy, bseed) in [(cx1, cy1, seed), (cx2, cy2, seed + 500)]:
        dx = (x - bcx).astype(np.float64)
        dy = (y - bcy).astype(np.float64)
        r = np.sqrt(dx ** 2 + dy ** 2)
        theta = np.arctan2(dy, dx)
        bh_r = min(w, h) * 0.08
        photon_r = bh_r * 1.5
        accr_outer = bh_r * 2.5
        accr_inner = bh_r * 1.5
        lens = np.where(r > bh_r,
                        1.0 + 2.0 * (bh_r / np.maximum(r, 1)) ** 2,
                        0.0)
        lx = np.clip((bcx + dx * lens).astype(int), 0, w - 1)
        ly = np.clip((bcy + dy * lens).astype(int), 0, h - 1)
        for c in range(3):
            img[..., c] += stars[ly, lx, c] * 0.5
        thin_disk = np.exp(-(dy ** 2) / (2 * (bh_r * 0.12) ** 2))
        disk_valid = ((r > accr_inner) & (r < accr_outer)).astype(float)
        thin_disk *= disk_valid
        disk_temp = np.clip(1.0 - (r - accr_inner) / (accr_outer - accr_inner), 0, 1) ** 0.6
        doppler = 1.0 + 0.3 * np.sin(theta)
        for c, (hot, cool) in enumerate([(255, 180), (200, 50), (150, 10)]):
            disk_c = cool + (hot - cool) * disk_temp * doppler
            img[..., c] += disk_c * thin_disk * 1.2
        ring = np.exp(-((r - photon_r) ** 2) / (2 * (bh_r * 0.04) ** 2))
        for c, val in enumerate([255, 230, 180]):
            img[..., c] += ring * val * 0.6
        fade = np.clip((r - bh_r * 0.8) / (bh_r * 0.2), 0, 1)
        for c in range(3):
            img[..., c] *= fade

    # Gravitational wave bridge between BHs
    mid_x, mid_y = w / 2, h / 2
    bridge_dx = (x - mid_x).astype(np.float64)
    bridge_dy = (y - mid_y).astype(np.float64)
    bridge_r = np.sqrt(bridge_dx ** 2 + bridge_dy ** 2)
    bridge = np.exp(-(bridge_dy ** 2) / (2 * (min(h, w) * 0.03) ** 2))
    bridge *= (np.abs(bridge_dx) < separation * 0.6).astype(float)
    bridge *= np.exp(-bridge_r / (separation * 0.8))
    gw_waves = np.sin(bridge_r / (min(w, h) * 0.03) * math.pi) * 0.5 + 0.5
    bridge *= gw_waves
    for c, val in enumerate([200, 150, 255]):
        img[..., c] += bridge * val * 0.4

    vig = _vignette((h, w), 0.5)
    for c in range(3):
        img[..., c] *= vig
    img = np.clip(img, 0, 255).astype(np.uint8)
    img = _bloom(img, threshold=150, radius=8, intensity=0.6)
    return img


def generate_image(prompt: str, width: int = 512, height: int = 512,
                   variation_seed: int = None):
    """
    Generate an image from a text prompt.

    Args:
        prompt: Text description of desired image
        width: Output width in pixels
        height: Output height in pixels
        variation_seed: Optional seed modifier for variations

    Returns:
        PIL.Image.Image object
    """
    seed = _seed_from_prompt(prompt)
    if variation_seed is not None:
        seed = (seed + variation_seed) % (2 ** 31)
    scene, params = _detect_scene(prompt)
    if scene == 'black_hole' and params.get('merging'):
        img_array = _render_merging_black_holes(width, height, seed, params)
    else:
        renderer = RENDERERS.get(scene, render_nebula)
        img_array = renderer(width, height, seed, params)
    return Image.fromarray(img_array)


def get_available_scenes():
    """Return list of available scene types"""
    return list(RENDERERS.keys())


# ============ CLI Entry Point ============

if __name__ == "__main__":
    import sys
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "two black holes merging"
    print(f"Generating: {prompt}")
    img = generate_image(prompt, 768, 768)
    out_path = "test_render.png"
    img.save(out_path)
    print(f"Saved to {out_path}")
