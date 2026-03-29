"""
Quantum Image Generator - Renderer Module
==========================================
Procedural cosmic scene generators and post-processing effects.
Zero external dependencies - built from scratch.
"""

import math
import random

from .core import (
    PixelBuffer, clamp, lerp, smoothstep, lerp_color,
    blackbody_color, gradient_sample, tone_map_aces, gamma_correct,
    hsv_to_rgb,
)
from .noise import PerlinNoise, VoronoiNoise


# ================================================================== #
#  Individual Render Passes                                           #
# ================================================================== #

def render_starfield(buf, density=0.003, seed=42,
                     brightness_range=(0.3, 1.5)):
    """Scatter stars with varying brightness and colour temperature."""
    rng = random.Random(seed)
    w, h = buf.width, buf.height
    num_stars = int(w * h * density)
    add = buf.add_pixel

    for _ in range(num_stars):
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        base_b = rng.uniform(*brightness_range) * (rng.random() ** 2)
        temp = rng.uniform(3000, 20000)
        cr, cg, cb = blackbody_color(temp)
        r, g, b = cr * base_b, cg * base_b, cb * base_b
        add(x, y, r, g, b)
        # bright stars get a 3x3 soft glow
        if base_b > 0.5:
            gl = base_b * 0.15
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx or dy:
                        add(x + dx, y + dy, cr * gl, cg * gl, cb * gl)


def render_nebula_layer(buf, noise, scale=2.0, color_stops=None,
                        opacity=0.5, warp_strength=0.0,
                        offset_x=0.0, offset_y=0.0):
    """Render one layer of nebula cloud via domain-warped fBm."""
    if color_stops is None:
        color_stops = [
            (0.0, (0.0,  0.0,  0.05)),
            (0.3, (0.1,  0.0,  0.2)),
            (0.5, (0.3,  0.1,  0.4)),
            (0.7, (0.6,  0.3,  0.2)),
            (1.0, (1.0,  0.8,  0.5)),
        ]

    w, h = buf.width, buf.height
    inv_w, inv_h = 1.0 / w, 1.0 / h
    data = buf.data
    _clamp = clamp
    blend_fn = buf.blend_pixel

    for y in range(h):
        row_off = y * w * 3
        ny_base = (y * inv_h + offset_y) * scale
        for x in range(w):
            nx = (x * inv_w + offset_x) * scale
            ny = ny_base

            if warp_strength > 0:
                nx, ny = noise.domain_warp(nx, ny, warp_strength, 4)

            n = noise.fbm(nx, ny, 6) * 0.5 + 0.5
            n = _clamp(n)
            cr, cg, cb = gradient_sample(n, color_stops)
            a = opacity * n
            blend_fn(x, y, cr * n, cg * n, cb * n, a)


def render_spiral_arms(buf, noise, center_x=0.5, center_y=0.5,
                       num_arms=2, spiral_tightness=0.8,
                       inner_radius=0.03, outer_radius=0.5,
                       arm_width=0.4, rotation=0.0):
    """Render logarithmic spiral arms with noise modulation."""
    w, h = buf.width, buf.height
    cx, cy = center_x * w, center_y * h
    max_r = max(w, h) * outer_radius
    inv_max_r = 1.0 / max_r
    inv_w, inv_h = 1.0 / w, 1.0 / h
    data = buf.data
    _log = math.log
    _cos = math.cos
    _atan2 = math.atan2
    _sqrt = math.sqrt
    _exp = math.exp
    _clamp = clamp

    arm_colors = [
        (0.0,  (1.0, 0.95, 0.9)),
        (0.12, (1.0, 0.8,  0.4)),
        (0.25, (0.9, 0.5,  0.15)),
        (0.45, (0.6, 0.2,  0.1)),
        (0.65, (0.3, 0.1,  0.2)),
        (1.0,  (0.05, 0.02, 0.08)),
    ]
    two_pi = 2.0 * math.pi
    arm_step = two_pi / num_arms
    noise_2d = noise.noise2d
    fbm = noise.fbm

    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy
            r2 = dx * dx + dy * dy
            r = _sqrt(r2) + 1e-10
            r_norm = r * inv_max_r

            if r_norm > 1.5:
                continue

            theta = _atan2(dy, dx) + rotation
            log_r = _log(r_norm + 0.01)
            spiral_angle = theta - spiral_tightness * log_r * 6.0

            # noise perturbation
            nx = x * inv_w * 3.0
            ny = y * inv_h * 3.0
            spiral_angle += fbm(nx + 10, ny + 10, 4) * 0.8

            # evaluate arm contribution (max over all arms)
            arm_val = 0.0
            for a in range(num_arms):
                ca = _cos(spiral_angle + a * arm_step)
                profile = max(0.0, ca)
                profile = profile ** (1.0 / (arm_width + 0.01))
                if profile > arm_val:
                    arm_val = profile

            # radial fade
            inner_fade = smoothstep(0.0, inner_radius * 3.0, r_norm)
            outer_fade = 1.0 - smoothstep(0.7, 1.3, r_norm)
            arm_val *= inner_fade * outer_fade

            # noise texture modulation
            detail = fbm(nx * 4, ny * 4, 5) * 0.5 + 0.5
            arm_val *= lerp(0.5, 1.0, detail)

            if arm_val < 0.001:
                continue

            color = gradient_sample(r_norm, arm_colors)
            intensity = arm_val * (1.0 + 3.0 * _exp(-r_norm * r_norm * 10))
            i = (y * w + x) * 3
            data[i]     += color[0] * intensity
            data[i + 1] += color[1] * intensity
            data[i + 2] += color[2] * intensity


def render_accretion_glow(buf, noise, center_x=0.5, center_y=0.5,
                          radius=0.15, width=0.08, intensity=2.0):
    """Render a glowing accretion ring with Doppler brightening."""
    w, h = buf.width, buf.height
    cx, cy = center_x * w, center_y * h
    dim = max(w, h)
    ring_r = dim * radius
    ring_w = dim * width
    inv_ring_w = 1.0 / ring_w
    _sqrt = math.sqrt
    _exp = math.exp
    _atan2 = math.atan2
    _sin = math.sin
    data = buf.data

    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy
            r = _sqrt(dx * dx + dy * dy)
            ring_dist = abs(r - ring_r) * inv_ring_w
            if ring_dist > 3.0:
                continue

            glow = _exp(-ring_dist * ring_dist * 2.0) * intensity
            theta = _atan2(dy, dx)
            n = noise.fbm(theta * 2 + r * 0.01, r * 0.02, 3) * 0.3 + 0.7
            glow *= n * (1.0 + 0.5 * _sin(theta))     # Doppler

            temp = lerp(8000, 3000, clamp(ring_dist / 2.0))
            cr, cg, cb = blackbody_color(temp)
            i = (y * w + x) * 3
            data[i]     += cr * glow
            data[i + 1] += cg * glow
            data[i + 2] += cb * glow


def render_black_hole_center(buf, center_x=0.5, center_y=0.5,
                             radius=0.025):
    """Darken the event-horizon region."""
    w, h = buf.width, buf.height
    cx, cy = center_x * w, center_y * h
    r_px = max(w, h) * radius
    data = buf.data
    y_lo = max(0, int(cy - r_px * 2))
    y_hi = min(h, int(cy + r_px * 2) + 1)
    x_lo = max(0, int(cx - r_px * 2))
    x_hi = min(w, int(cx + r_px * 2) + 1)
    _sqrt = math.sqrt

    for y in range(y_lo, y_hi):
        for x in range(x_lo, x_hi):
            d = _sqrt((x - cx) ** 2 + (y - cy) ** 2)
            f = smoothstep(r_px * 0.5, r_px * 1.5, d)
            if f < 1.0:
                i = (y * w + x) * 3
                data[i]     *= f
                data[i + 1] *= f
                data[i + 2] *= f


def render_light_streaks(buf, noise, center_x=0.5, center_y=0.5,
                         num_streaks=5, seed=42):
    """Trace flowing light/energy streaks outward from the centre."""
    rng = random.Random(seed)
    w, h = buf.width, buf.height
    cx, cy = center_x * w, center_y * h
    add = buf.add_pixel
    _cos = math.cos
    _sin = math.sin
    _sqrt = math.sqrt
    _exp = math.exp

    for _ in range(num_streaks):
        angle = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.05, 0.15) * max(w, h)
        temp = rng.uniform(4000, 12000)
        cr, cg, cb = blackbody_color(temp)
        n_pts = 250

        for i in range(n_pts):
            t = i / n_pts
            px = cx + r * _cos(angle)
            py = cy + r * _sin(angle)
            r += rng.uniform(0.5, 2.0)
            angle += rng.uniform(0.02, 0.08)
            angle += noise.noise2d(px / w * 3, py / h * 3) * 0.1
            bright = (1.0 - t) * 1.5 * rng.uniform(0.5, 1.0)
            ix, iy = int(px), int(py)
            for ddx in range(-2, 3):
                for ddy in range(-2, 3):
                    d2 = ddx * ddx + ddy * ddy
                    if d2 > 6:
                        continue
                    g = _exp(-d2 * 0.5) * bright * 0.3
                    add(ix + ddx, iy + ddy, cr * g, cg * g, cb * g)


# ================================================================== #
#  Gravitational Lensing                                              #
# ================================================================== #

def apply_gravitational_lensing(buf, center_x=0.5, center_y=0.5,
                                strength=0.05, inner_radius=0.04):
    """Displace pixels to simulate gravitational light-bending."""
    w, h = buf.width, buf.height
    cx, cy = center_x * w, center_y * h
    dim = max(w, h)
    src = buf.copy()
    data = buf.data
    _floor = math.floor
    _sqrt = math.sqrt

    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy
            r = _sqrt(dx * dx + dy * dy) / dim
            if r < 0.001:
                continue

            ls = strength / (r * r + inner_radius * inner_radius)
            if ls > 0.3:
                ls = 0.3

            rd = r * dim + 1.0
            disp_x = -dx / rd * ls * dim
            disp_y = -dy / rd * ls * dim
            tang_x = -dy / rd * ls * dim * 0.3
            tang_y =  dx / rd * ls * dim * 0.3

            sx = x + disp_x + tang_x
            sy = y + disp_y + tang_y

            # bilinear interpolation
            sxi = int(_floor(sx))
            syi = int(_floor(sy))
            fx = sx - sxi
            fy = sy - syi
            c00 = src.get_pixel(sxi,     syi)
            c10 = src.get_pixel(sxi + 1, syi)
            c01 = src.get_pixel(sxi,     syi + 1)
            c11 = src.get_pixel(sxi + 1, syi + 1)
            ifx = 1 - fx
            ify = 1 - fy
            cr = c00[0]*ifx*ify + c10[0]*fx*ify + c01[0]*ifx*fy + c11[0]*fx*fy
            cg = c00[1]*ifx*ify + c10[1]*fx*ify + c01[1]*ifx*fy + c11[1]*fx*fy
            cb = c00[2]*ifx*ify + c10[2]*fx*ify + c01[2]*ifx*fy + c11[2]*fx*fy

            i = (y * w + x) * 3
            data[i]     = cr
            data[i + 1] = cg
            data[i + 2] = cb


# ================================================================== #
#  Post-processing Effects                                            #
# ================================================================== #

def apply_bloom(buf, radius=10, threshold=0.8, intensity=0.4):
    """Separable-Gaussian bloom on bright pixels."""
    w, h = buf.width, buf.height
    data = buf.data

    # --- extract bright pixels ---
    bright = [0.0] * (w * h * 3)
    for i in range(0, w * h * 3, 3):
        r, g, b = data[i], data[i + 1], data[i + 2]
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        if lum > threshold:
            ex = lum - threshold
            bright[i]     = r * ex
            bright[i + 1] = g * ex
            bright[i + 2] = b * ex

    # --- build 1-D Gaussian kernel ---
    sigma = radius / 3.0
    kernel = []
    k_sum = 0.0
    for k in range(-radius, radius + 1):
        v = math.exp(-k * k / (2.0 * sigma * sigma))
        kernel.append(v)
        k_sum += v
    kernel = [k / k_sum for k in kernel]

    # --- horizontal pass ---
    h_pass = [0.0] * (w * h * 3)
    for y in range(h):
        row = y * w * 3
        for x in range(w):
            rr = gg = bb = 0.0
            for ki in range(len(kernel)):
                sx = x + ki - radius
                if sx < 0:
                    sx = 0
                elif sx >= w:
                    sx = w - 1
                si = row + sx * 3
                wt = kernel[ki]
                rr += bright[si] * wt
                gg += bright[si + 1] * wt
                bb += bright[si + 2] * wt
            oi = row + x * 3
            h_pass[oi]     = rr
            h_pass[oi + 1] = gg
            h_pass[oi + 2] = bb

    # --- vertical pass + add back ---
    for x in range(w):
        for y in range(h):
            rr = gg = bb = 0.0
            for ki in range(len(kernel)):
                sy = y + ki - radius
                if sy < 0:
                    sy = 0
                elif sy >= h:
                    sy = h - 1
                si = sy * w * 3 + x * 3
                wt = kernel[ki]
                rr += h_pass[si] * wt
                gg += h_pass[si + 1] * wt
                bb += h_pass[si + 2] * wt
            i = y * w * 3 + x * 3
            data[i]     += rr * intensity
            data[i + 1] += gg * intensity
            data[i + 2] += bb * intensity


def apply_vignette(buf, strength=0.7, radius=0.8):
    """Darken image edges."""
    w, h = buf.width, buf.height
    cx, cy = w * 0.5, h * 0.5
    inv_cx, inv_cy = 1.0 / cx, 1.0 / cy
    data = buf.data
    _sqrt = math.sqrt
    r_lo = radius * 0.5
    r_hi = radius * 1.5

    for y in range(h):
        dy = (y - cy) * inv_cy
        dy2 = dy * dy
        row = y * w * 3
        for x in range(w):
            dx = (x - cx) * inv_cx
            d = _sqrt(dx * dx + dy2)
            f = 1.0 - strength * smoothstep(r_lo, r_hi, d)
            i = row + x * 3
            data[i]     *= f
            data[i + 1] *= f
            data[i + 2] *= f


def apply_tone_mapping(buf):
    """Apply ACES tone mapping + sRGB gamma to every pixel."""
    d = buf.data
    for i in range(0, len(d), 3):
        r, g, b = d[i], d[i + 1], d[i + 2]
        r, g, b = tone_map_aces(r, g, b)
        r, g, b = gamma_correct(r, g, b, 2.2)
        d[i], d[i + 1], d[i + 2] = r, g, b


def apply_color_grade(buf, tint=(1.0, 0.95, 0.9),
                      shadows=(0.05, 0.02, 0.08),
                      contrast=1.1, saturation=1.2):
    """Cinematic colour grading pass."""
    d = buf.data
    _clamp = clamp
    for i in range(0, len(d), 3):
        r, g, b = d[i], d[i + 1], d[i + 2]
        r *= tint[0]; g *= tint[1]; b *= tint[2]
        r = (r - 0.5) * contrast + 0.5
        g = (g - 0.5) * contrast + 0.5
        b = (b - 0.5) * contrast + 0.5
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        sb = (1.0 - _clamp(lum * 2)) * 0.5
        r = lerp(r, shadows[0], sb)
        g = lerp(g, shadows[1], sb)
        b = lerp(b, shadows[2], sb)
        r = lerp(lum, r, saturation)
        g = lerp(lum, g, saturation)
        b = lerp(lum, b, saturation)
        d[i]     = _clamp(r)
        d[i + 1] = _clamp(g)
        d[i + 2] = _clamp(b)


# ================================================================== #
#  Scene Presets                                                      #
# ================================================================== #

def create_cosmic_vortex(width=512, height=512, seed=42):
    """Black hole with swirling accretion disk & gravitational lensing."""
    print(f"Generating cosmic vortex ({width}x{height}, seed={seed})...")
    buf = PixelBuffer(width, height)
    noise  = PerlinNoise(seed)
    noise2 = PerlinNoise(seed + 1)

    # 1 ---- deep-space background
    print("  [1/8] Deep space background...")
    for y in range(height):
        for x in range(width):
            n = noise2.fbm(x / width * 2, y / height * 2, 4) * 0.5 + 0.5
            buf.set_pixel(x, y, 0.01 + 0.02 * n,
                                0.005 + 0.015 * n,
                                0.03 + 0.05 * n)

    # 2 ---- nebula clouds
    print("  [2/8] Nebula clouds...")
    render_nebula_layer(buf, noise, scale=2.5,
        color_stops=[
            (0.0, (0.0,  0.0,  0.02)),
            (0.3, (0.08, 0.01, 0.15)),
            (0.5, (0.15, 0.05, 0.25)),
            (0.7, (0.25, 0.1,  0.15)),
            (1.0, (0.4,  0.2,  0.1)),
        ], opacity=0.6, warp_strength=1.5)

    render_nebula_layer(buf, noise2, scale=3.0,
        color_stops=[
            (0.0, (0.0,  0.01, 0.03)),
            (0.4, (0.05, 0.02, 0.12)),
            (0.6, (0.1,  0.15, 0.3)),
            (0.8, (0.2,  0.1,  0.25)),
            (1.0, (0.3,  0.15, 0.2)),
        ], opacity=0.4, warp_strength=2.0,
        offset_x=3.0, offset_y=2.0)

    # 3 ---- spiral arms
    print("  [3/8] Spiral arms...")
    render_spiral_arms(buf, noise, num_arms=2,
                       spiral_tightness=0.7,
                       inner_radius=0.04, outer_radius=0.55,
                       arm_width=0.35)

    # 4 ---- accretion glow
    print("  [4/8] Accretion disk...")
    render_accretion_glow(buf, noise, radius=0.08,
                          width=0.04, intensity=2.5)

    # 5 ---- light streaks
    print("  [5/8] Light streaks...")
    render_light_streaks(buf, noise, num_streaks=8, seed=seed)

    # 6 ---- gravitational lensing
    print("  [6/8] Gravitational lensing...")
    apply_gravitational_lensing(buf, strength=0.04, inner_radius=0.03)

    # 7 ---- black hole centre
    render_black_hole_center(buf, radius=0.02)

    # 8 ---- stars
    print("  [7/8] Star field...")
    render_starfield(buf, density=0.004, seed=seed + 100)

    # post-processing
    print("  [8/8] Post-processing...")
    apply_bloom(buf, radius=8, threshold=0.7, intensity=0.5)
    apply_vignette(buf, strength=0.6)
    apply_tone_mapping(buf)
    apply_color_grade(buf, contrast=1.15, saturation=1.3,
                      shadows=(0.04, 0.02, 0.07))
    return buf


def create_nebula(width=512, height=512, seed=42):
    """Colourful interstellar nebula cloud."""
    print(f"Generating nebula ({width}x{height}, seed={seed})...")
    buf = PixelBuffer(width, height)
    noise  = PerlinNoise(seed)
    noise2 = PerlinNoise(seed + 1)
    noise3 = PerlinNoise(seed + 2)

    buf.clear(0.01, 0.005, 0.02)

    print("  Rendering nebula layers...")
    render_nebula_layer(buf, noise, 3.0,
        [(0.0,(0,0,0)),(0.2,(0.1,0,0.2)),(0.4,(0.3,0.05,0.4)),
         (0.6,(0.5,0.1,0.3)),(0.8,(0.8,0.3,0.15)),(1.0,(1.0,0.7,0.3))],
        0.8, 2.5)
    render_nebula_layer(buf, noise2, 2.0,
        [(0.0,(0,0,0)),(0.3,(0,0.05,0.15)),(0.5,(0.05,0.15,0.35)),
         (0.7,(0.1,0.3,0.5)),(1.0,(0.3,0.5,0.8))],
        0.6, 1.8, 5, 3)
    render_nebula_layer(buf, noise3, 4.0,
        [(0.0,(0,0,0)),(0.4,(0.15,0,0.05)),(0.6,(0.4,0.05,0.1)),
         (0.8,(0.6,0.15,0.1)),(1.0,(0.9,0.4,0.2))],
        0.5, 3.0, 7, 1)

    print("  Rendering stars...")
    render_starfield(buf, density=0.005, seed=seed + 100)

    print("  Post-processing...")
    apply_bloom(buf, radius=6, threshold=0.6, intensity=0.4)
    apply_vignette(buf, strength=0.5)
    apply_tone_mapping(buf)
    apply_color_grade(buf, saturation=1.4, contrast=1.1)
    return buf


def create_galaxy(width=512, height=512, seed=42):
    """Spiral galaxy with central bulge."""
    print(f"Generating galaxy ({width}x{height}, seed={seed})...")
    buf = PixelBuffer(width, height)
    noise = PerlinNoise(seed)

    buf.clear(0.005, 0.003, 0.015)

    render_spiral_arms(buf, noise, num_arms=4,
                       spiral_tightness=0.5,
                       inner_radius=0.01, outer_radius=0.45,
                       arm_width=0.5)

    # central bulge
    w, h = width, height
    cx, cy = w * 0.5, h * 0.5
    for y in range(h):
        for x in range(w):
            dx = (x - cx) / w
            dy = (y - cy) / h
            g = 2.0 * math.exp(-(dx*dx + dy*dy) * 80)
            buf.add_pixel(x, y, g, g * 0.9, g * 0.7)

    render_starfield(buf, density=0.006, seed=seed + 100)
    apply_bloom(buf, radius=8, threshold=0.5, intensity=0.5)
    apply_vignette(buf, strength=0.4)
    apply_tone_mapping(buf)
    apply_color_grade(buf, saturation=1.2, contrast=1.05)
    return buf


def create_quantum_field(width=512, height=512, seed=42):
    """Abstract quantum energy-field visualisation."""
    print(f"Generating quantum field ({width}x{height}, seed={seed})...")
    buf = PixelBuffer(width, height)
    noise = PerlinNoise(seed)
    voronoi = VoronoiNoise(seed)
    _clamp = clamp

    for y in range(height):
        for x in range(width):
            nx = x / width * 4
            ny = y / height * 4
            wx, wy = noise.domain_warp(nx, ny, 2.0, 5)
            n1 = noise.fbm(wx, wy, 6) * 0.5 + 0.5
            n2 = noise.ridge(nx * 2, ny * 2, 5)
            d1, d2 = voronoi.noise2d(nx * 1.5, ny * 1.5)
            edge = _clamp(1.0 - (d2 - d1) * 3)
            value = n1 * 0.4 + n2 * 0.3 + edge * 0.3

            if value < 0.3:
                r, g, b = value * 0.3, value * 0.1, value * 1.5
            elif value < 0.6:
                t = (value - 0.3) / 0.3
                r = lerp(0.1, 0.5, t)
                g = lerp(0.03, 0.2, t)
                b = lerp(0.45, 0.3, t)
            else:
                t = (value - 0.6) / 0.4
                r = lerp(0.5, 1.0, t)
                g = lerp(0.2, 0.8, t)
                b = lerp(0.3, 0.5, t)

            intensity = 1.0 + value * value * 2.0
            buf.set_pixel(x, y,
                          r * intensity, g * intensity, b * intensity)

    apply_bloom(buf, radius=6, threshold=0.8, intensity=0.3)
    apply_vignette(buf, strength=0.5)
    apply_tone_mapping(buf)
    apply_color_grade(buf, tint=(0.95, 0.9, 1.0), saturation=1.3)
    return buf


# ================================================================== #
#  Preset registry                                                    #
# ================================================================== #

PRESETS = {
    "cosmic_vortex": create_cosmic_vortex,
    "nebula":        create_nebula,
    "galaxy":        create_galaxy,
    "quantum_field": create_quantum_field,
}
