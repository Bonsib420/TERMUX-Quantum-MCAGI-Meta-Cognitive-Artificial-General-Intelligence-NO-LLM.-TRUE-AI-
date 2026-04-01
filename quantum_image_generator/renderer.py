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
    hsv_to_rgb, soft_light_blend,
)
from .noise import PerlinNoise, VoronoiNoise


# ================================================================== #
#  Individual Render Passes                                           #
# ================================================================== #

def render_starfield(buf, density=0.003, seed=42,
                     brightness_range=(0.3, 1.5)):
    """Scatter stars with varying brightness and color temperature.

    Three tiers: tiny dim background, medium with soft glow, and bright
    prominent stars with halos.  Occasional tight star clusters add
    realism.
    """
    rng = random.Random(seed)
    w, h = buf.width, buf.height
    add = buf.add_pixel

    # --- Tier 1: tiny dim background stars ---
    num_bg = int(w * h * density * 3)
    for _ in range(num_bg):
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        base_b = rng.uniform(0.1, 0.3) * (rng.random() ** 2)
        temp = rng.uniform(3000, 20000)
        cr, cg, cb = blackbody_color(temp)
        add(x, y, cr * base_b, cg * base_b, cb * base_b)

    # --- Tier 2: medium stars with 3×3 glow ---
    num_med = int(w * h * density)
    for _ in range(num_med):
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        base_b = rng.uniform(0.3, 0.8) * (rng.random() ** 2)
        temp = rng.uniform(3000, 20000)
        cr, cg, cb = blackbody_color(temp)
        add(x, y, cr * base_b, cg * base_b, cb * base_b)
        gl = base_b * 0.15
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx or dy:
                    add(x + dx, y + dy, cr * gl, cg * gl, cb * gl)

    # --- Tier 3: bright prominent stars with 5×5 halos ---
    num_bright = int(w * h * density * 0.15)
    _exp = math.exp
    for _ in range(num_bright):
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        base_b = rng.uniform(0.8, 2.0) * (rng.random() ** 0.5)
        temp = rng.uniform(5000, 25000)
        cr, cg, cb = blackbody_color(temp)
        add(x, y, cr * base_b, cg * base_b, cb * base_b)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx or dy:
                    d2 = dx * dx + dy * dy
                    gl = _exp(-d2 * 0.4) * base_b * 0.2
                    add(x + dx, y + dy, cr * gl, cg * gl, cb * gl)

    # --- Occasional star clusters ---
    num_clusters = 5
    for _ in range(num_clusters):
        cx = rng.randint(0, w - 1)
        cy = rng.randint(0, h - 1)
        cluster_size = rng.randint(8, 20)
        spread = rng.randint(5, 15)
        for _s in range(cluster_size):
            sx = cx + rng.randint(-spread, spread)
            sy = cy + rng.randint(-spread, spread)
            if 0 <= sx < w and 0 <= sy < h:
                sb = rng.uniform(0.15, 0.5)
                temp = rng.uniform(5000, 12000)
                cr, cg, cb = blackbody_color(temp)
                add(sx, sy, cr * sb, cg * sb, cb * sb)


def render_nebula_layer(buf, noise, scale=2.0, color_stops=None,
                        opacity=0.5, warp_strength=0.0,
                        offset_x=0.0, offset_y=0.0):
    """Render one layer of nebula cloud via domain-warped fBm.

    Uses 8-octave fBm for finer detail and adds emission highlights
    in the brightest regions.
    """
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
    _clamp = clamp
    blend_fn = buf.blend_pixel
    add_fn = buf.add_pixel

    for y in range(h):
        ny_base = (y * inv_h + offset_y) * scale
        for x in range(w):
            nx = (x * inv_w + offset_x) * scale
            ny = ny_base

            if warp_strength > 0:
                nx, ny = noise.domain_warp(nx, ny, warp_strength, 4)

            n = noise.fbm(nx, ny, 8) * 0.5 + 0.5
            n = _clamp(n)
            cr, cg, cb = gradient_sample(n, color_stops)
            a = opacity * n
            blend_fn(x, y, cr * n, cg * n, cb * n, a)

            # emission highlights in bright regions
            if n > 0.75:
                boost = (n - 0.75) * 4.0
                add_fn(x, y, cr * boost * 0.3, cg * boost * 0.3,
                       cb * boost * 0.3)


def render_spiral_arms(buf, noise, center_x=0.5, center_y=0.5,
                       num_arms=2, spiral_tightness=0.8,
                       inner_radius=0.03, outer_radius=0.5,
                       arm_width=0.4, rotation=0.0):
    """Render logarithmic spiral arms with noise modulation, dust lanes
    and bright star-forming knots."""
    w, h = buf.width, buf.height
    cx, cy = center_x * w, center_y * h
    max_r = max(w, h) * outer_radius
    inv_max_r = 1.0 / max_r
    inv_w, inv_h = 1.0 / w, 1.0 / h
    data = buf.data
    add = buf.add_pixel
    _log = math.log
    _cos = math.cos
    _atan2 = math.atan2
    _sqrt = math.sqrt
    _exp = math.exp
    _clamp = clamp

    arm_colors = [
        (0.0,  (1.0,  0.95, 0.9)),
        (0.08, (1.0,  0.88, 0.65)),
        (0.16, (1.0,  0.8,  0.4)),
        (0.25, (0.95, 0.65, 0.25)),
        (0.35, (0.9,  0.5,  0.15)),
        (0.45, (0.75, 0.3,  0.1)),
        (0.55, (0.6,  0.2,  0.1)),
        (0.65, (0.45, 0.15, 0.15)),
        (0.8,  (0.3,  0.1,  0.2)),
        (1.0,  (0.05, 0.02, 0.08)),
    ]
    two_pi = 2.0 * math.pi
    arm_step = two_pi / num_arms
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

            # dust lanes: darken between arms
            dust = fbm(nx * 6 + 100, ny * 6 + 100, 4) * 0.5 + 0.5
            dust_factor = 1.0 - 0.4 * dust * (1.0 - arm_val)
            arm_val *= max(0.0, dust_factor)

            if arm_val < 0.001:
                continue

            color = gradient_sample(r_norm, arm_colors)
            intensity = arm_val * (1.0 + 3.0 * _exp(-r_norm * r_norm * 10))
            i = (y * w + x) * 3
            data[i]     += color[0] * intensity
            data[i + 1] += color[1] * intensity
            data[i + 2] += color[2] * intensity

            # bright star-forming knots
            if arm_val > 0.6 and detail > 0.7:
                knot = (arm_val - 0.6) * (detail - 0.7) * 15.0
                add(x, y, knot, knot * 0.9, knot * 0.6)


def render_accretion_glow(buf, noise, center_x=0.5, center_y=0.5,
                          radius=0.15, width=0.08, intensity=2.0):
    """Multi-ring accretion with angular turbulence and Doppler beaming."""
    w, h = buf.width, buf.height
    cx, cy = center_x * w, center_y * h
    dim = max(w, h)

    # inner hot ring
    ring_r_inner = dim * radius
    # outer cooler ring
    ring_r_outer = dim * radius * 2.2
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
            theta = _atan2(dy, dx)

            # angular turbulence
            turb = noise.fbm(theta * 3 + r * 0.015, r * 0.01, 4) * 0.3

            # Doppler beaming: one side brighter
            doppler = 1.0 + 0.7 * _sin(theta)

            # inner ring contribution
            dist_inner = abs(r - ring_r_inner) * inv_ring_w
            glow_inner = 0.0
            if dist_inner < 3.5:
                glow_inner = _exp(-dist_inner * dist_inner * 2.0) * intensity
                n_inner = turb + 0.7
                glow_inner *= n_inner * doppler
                temp_inner = lerp(12000, 4000, clamp(dist_inner / 2.0))
                cr, cg, cb = blackbody_color(temp_inner)
                i = (y * w + x) * 3
                data[i]     += cr * glow_inner
                data[i + 1] += cg * glow_inner
                data[i + 2] += cb * glow_inner

            # outer ring contribution
            dist_outer = abs(r - ring_r_outer) * inv_ring_w
            if dist_outer < 3.5:
                glow_outer = _exp(-dist_outer * dist_outer * 1.5) * intensity * 0.5
                n_outer = turb + 0.7
                glow_outer *= n_outer * doppler
                temp_outer = lerp(6000, 2000, clamp(dist_outer / 2.0))
                cr2, cg2, cb2 = blackbody_color(temp_outer)
                i = (y * w + x) * 3
                data[i]     += cr2 * glow_outer
                data[i + 1] += cg2 * glow_outer
                data[i + 2] += cb2 * glow_outer


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
    """Trace flowing light/energy streaks outward from the centre.

    Thicker glow radius, more sample points, and occasional bright
    flare spots along each streak.
    """
    rng = random.Random(seed)
    w, h = buf.width, buf.height
    cx, cy = center_x * w, center_y * h
    add = buf.add_pixel
    _cos = math.cos
    _sin = math.sin
    _exp = math.exp

    for _ in range(num_streaks):
        angle = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.05, 0.15) * max(w, h)
        temp = rng.uniform(4000, 12000)
        cr, cg, cb = blackbody_color(temp)
        n_pts = 400

        for i in range(n_pts):
            t = i / n_pts
            px = cx + r * _cos(angle)
            py = cy + r * _sin(angle)
            r += rng.uniform(0.5, 2.0)
            angle += rng.uniform(0.02, 0.08)
            angle += noise.noise2d(px / w * 3, py / h * 3) * 0.1
            bright = (1.0 - t) * 1.5 * rng.uniform(0.5, 1.0)
            ix, iy = int(px), int(py)

            # radius 3 soft glow
            for ddx in range(-3, 4):
                for ddy in range(-3, 4):
                    d2 = ddx * ddx + ddy * ddy
                    if d2 > 9:
                        continue
                    g = _exp(-d2 * 0.35) * bright * 0.25
                    add(ix + ddx, iy + ddy, cr * g, cg * g, cb * g)

            # occasional bright flare
            if i % 50 == 0 and i > 0:
                flare = bright * 3.0
                for ddx in range(-4, 5):
                    for ddy in range(-4, 5):
                        d2 = ddx * ddx + ddy * ddy
                        if d2 > 16:
                            continue
                        g = _exp(-d2 * 0.25) * flare * 0.15
                        add(ix + ddx, iy + ddy, cr * g, cg * g, cb * g)


def render_jet_streams(buf, noise, center_x=0.5, center_y=0.5,
                       length=0.4, width=0.015, intensity=1.5,
                       seed=42):
    """Render relativistic jets extending vertically from centre."""
    w, h = buf.width, buf.height
    cx, cy = int(center_x * w), int(center_y * h)
    dim = max(w, h)
    jet_len = int(dim * length)
    jet_w = dim * width
    _exp = math.exp
    add = buf.add_pixel
    rng = random.Random(seed)

    for direction in (1, -1):
        for step in range(jet_len):
            t = step / jet_len
            jy = cy + direction * step
            if jy < 0 or jy >= h:
                continue

            # noise-modulated horizontal wobble
            wobble = noise.noise2d(t * 8 + direction * 50,
                                   rng.random() * 0.01) * jet_w * 2
            jx_center = cx + wobble

            # temperature fades from core outward
            temp = lerp(30000, 15000, t)
            cr, cg, cb = blackbody_color(temp)

            # brightness fades along length
            bright = intensity * (1.0 - t) ** 1.5

            # gaussian cross-section
            hw = int(jet_w * 3) + 1
            for dx in range(-hw, hw + 1):
                px = int(jx_center) + dx
                if 0 <= px < w:
                    dist = abs(px - jx_center) / (jet_w + 1e-6)
                    g = _exp(-dist * dist * 2.0) * bright
                    add(px, jy, cr * g, cg * g, cb * g)


# ================================================================== #
#  Gravitational Lensing                                              #
# ================================================================== #

def apply_gravitational_lensing(buf, center_x=0.5, center_y=0.5,
                                strength=0.05, inner_radius=0.04):
    """Displace pixels to simulate gravitational light-bending.

    Includes an Einstein ring glow at the critical lensing radius.
    """
    w, h = buf.width, buf.height
    cx, cy = center_x * w, center_y * h
    dim = max(w, h)
    src = buf.copy()
    data = buf.data
    _floor = math.floor
    _sqrt = math.sqrt
    _exp = math.exp

    # critical radius for Einstein ring
    crit_r = strength * 4.0

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
            tang_x = -dy / rd * ls * dim * 0.5
            tang_y =  dx / rd * ls * dim * 0.5

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

            # Einstein ring glow
            ring_dist = abs(r - crit_r) / (crit_r * 0.3 + 1e-6)
            ring_glow = _exp(-ring_dist * ring_dist * 4.0) * 0.4
            cr += ring_glow * 0.8
            cg += ring_glow * 0.85
            cb += ring_glow * 1.0

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
    """Cinematic color grading pass."""
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


def apply_chromatic_aberration(buf, strength=0.003):
    """Shift R/B channels to simulate lens chromatic aberration."""
    buf.chromatic_aberration(strength)


def apply_film_grain(buf, amount=0.02, seed=42):
    """Add subtle random noise to each pixel."""
    rng = random.Random(seed)
    d = buf.data
    _clamp = clamp
    for i in range(0, len(d), 3):
        grain = (rng.random() - 0.5) * amount * 2
        d[i]     = _clamp(d[i] + grain)
        d[i + 1] = _clamp(d[i + 1] + grain)
        d[i + 2] = _clamp(d[i + 2] + grain)


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
    print("  [1/9] Deep space background...")
    for y in range(height):
        for x in range(width):
            n = noise2.fbm(x / width * 2, y / height * 2, 4) * 0.5 + 0.5
            buf.set_pixel(x, y, 0.01 + 0.02 * n,
                                0.005 + 0.015 * n,
                                0.03 + 0.05 * n)

    # 2 ---- nebula clouds (richer, more saturated stops)
    print("  [2/9] Nebula clouds...")
    render_nebula_layer(buf, noise, scale=2.5,
        color_stops=[
            (0.0,  (0.0,  0.0,  0.03)),
            (0.15, (0.05, 0.0,  0.1)),
            (0.3,  (0.12, 0.02, 0.22)),
            (0.5,  (0.25, 0.08, 0.35)),
            (0.7,  (0.4,  0.15, 0.2)),
            (0.85, (0.5,  0.25, 0.12)),
            (1.0,  (0.6,  0.3,  0.1)),
        ], opacity=0.6, warp_strength=1.5)

    render_nebula_layer(buf, noise2, scale=3.0,
        color_stops=[
            (0.0,  (0.0,  0.01, 0.04)),
            (0.2,  (0.03, 0.01, 0.1)),
            (0.4,  (0.06, 0.04, 0.18)),
            (0.6,  (0.12, 0.18, 0.35)),
            (0.8,  (0.22, 0.12, 0.3)),
            (1.0,  (0.35, 0.18, 0.25)),
        ], opacity=0.4, warp_strength=2.0,
        offset_x=3.0, offset_y=2.0)

    # 3 ---- spiral arms
    print("  [3/9] Spiral arms...")
    render_spiral_arms(buf, noise, num_arms=2,
                       spiral_tightness=0.7,
                       inner_radius=0.04, outer_radius=0.55,
                       arm_width=0.35)

    # 4 ---- accretion glow (multi-ring)
    print("  [4/9] Accretion disk...")
    render_accretion_glow(buf, noise, radius=0.08,
                          width=0.04, intensity=2.5)

    # 5 ---- light streaks
    print("  [5/9] Light streaks...")
    render_light_streaks(buf, noise, num_streaks=8, seed=seed)

    # 6 ---- jet streams
    print("  [6/9] Jet streams...")
    render_jet_streams(buf, noise, length=0.35, width=0.012,
                       intensity=1.2, seed=seed)

    # 7 ---- gravitational lensing
    print("  [7/9] Gravitational lensing...")
    apply_gravitational_lensing(buf, strength=0.04, inner_radius=0.03)

    # 8 ---- black hole centre
    render_black_hole_center(buf, radius=0.02)

    # 9 ---- stars
    print("  [8/9] Star field...")
    render_starfield(buf, density=0.004, seed=seed + 100)

    # post-processing
    print("  [9/9] Post-processing...")
    apply_bloom(buf, radius=8, threshold=0.6, intensity=0.6)
    apply_vignette(buf, strength=0.75)
    apply_tone_mapping(buf)
    apply_chromatic_aberration(buf, strength=0.003)
    apply_color_grade(buf, contrast=1.15, saturation=1.3,
                      shadows=(0.04, 0.02, 0.07))
    apply_film_grain(buf, amount=0.015, seed=seed + 200)
    return buf


def create_nebula(width=512, height=512, seed=42):
    """Colorful interstellar nebula cloud."""
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


def create_deep_space(width=512, height=512, seed=42):
    """Rich deep-field scene with overlapping nebulae, dense stars,
    scattered small spiral structures, and volumetric dust."""
    print(f"Generating deep space ({width}x{height}, seed={seed})...")
    buf = PixelBuffer(width, height)
    noise  = PerlinNoise(seed)
    noise2 = PerlinNoise(seed + 1)
    noise3 = PerlinNoise(seed + 2)
    rng = random.Random(seed)

    # 1 ---- dark background with subtle gradient
    print("  [1/7] Background...")
    for y in range(height):
        t = y / height
        r = lerp(0.005, 0.015, t)
        g = lerp(0.003, 0.01, t)
        b = lerp(0.015, 0.035, t)
        for x in range(width):
            n = noise.fbm(x / width * 2, y / height * 2, 3) * 0.5 + 0.5
            buf.set_pixel(x, y, r + 0.01 * n, g + 0.005 * n,
                          b + 0.02 * n)

    # 2 ---- three overlapping nebula layers
    print("  [2/7] Nebula layers...")
    render_nebula_layer(buf, noise, scale=2.5,
        color_stops=[
            (0.0, (0.0,  0.0,  0.02)),
            (0.25, (0.08, 0.0,  0.15)),
            (0.5,  (0.2,  0.05, 0.35)),
            (0.75, (0.4,  0.15, 0.25)),
            (1.0,  (0.6,  0.3,  0.15)),
        ], opacity=0.5, warp_strength=2.0)

    render_nebula_layer(buf, noise2, scale=3.5,
        color_stops=[
            (0.0,  (0.0,  0.0,  0.0)),
            (0.3,  (0.0,  0.04, 0.12)),
            (0.5,  (0.03, 0.12, 0.25)),
            (0.7,  (0.08, 0.2,  0.4)),
            (1.0,  (0.15, 0.35, 0.6)),
        ], opacity=0.4, warp_strength=2.5,
        offset_x=4.0, offset_y=2.5)

    render_nebula_layer(buf, noise3, scale=4.0,
        color_stops=[
            (0.0,  (0.0,  0.0,  0.0)),
            (0.3,  (0.1,  0.02, 0.05)),
            (0.6,  (0.25, 0.05, 0.08)),
            (0.8,  (0.45, 0.12, 0.08)),
            (1.0,  (0.7,  0.25, 0.1)),
        ], opacity=0.35, warp_strength=3.0,
        offset_x=7.0, offset_y=5.0)

    # 3 ---- dense starfield
    print("  [3/7] Dense starfield...")
    render_starfield(buf, density=0.008, seed=seed + 100)

    # 4 ---- scattered small spiral structures
    print("  [4/7] Small spirals...")
    num_spirals = rng.randint(2, 3)
    for s in range(num_spirals):
        sp_x = rng.uniform(0.2, 0.8)
        sp_y = rng.uniform(0.2, 0.8)
        sp_noise = PerlinNoise(seed + 10 + s)
        render_spiral_arms(buf, sp_noise, center_x=sp_x, center_y=sp_y,
                           num_arms=rng.randint(2, 3),
                           spiral_tightness=rng.uniform(0.4, 0.8),
                           inner_radius=0.005, outer_radius=0.08,
                           arm_width=0.5,
                           rotation=rng.uniform(0, 2 * math.pi))

    # 5 ---- volumetric dust (dark absorption via billowy noise)
    print("  [5/7] Volumetric dust...")
    data = buf.data
    for y in range(height):
        for x in range(width):
            nx = x / width * 3.0
            ny = y / height * 3.0
            dust = noise.billowy(nx + 20, ny + 20, 5)
            # billowy returns [0,1]-ish; use as absorption factor
            absorption = 1.0 - clamp(dust * 0.4)
            i = (y * width + x) * 3
            data[i]     *= absorption
            data[i + 1] *= absorption
            data[i + 2] *= absorption

    # 6 ---- post-processing
    print("  [6/7] Post-processing...")
    apply_bloom(buf, radius=8, threshold=0.6, intensity=0.45)
    apply_vignette(buf, strength=0.6)
    apply_tone_mapping(buf)
    apply_color_grade(buf, contrast=1.1, saturation=1.25,
                      shadows=(0.03, 0.015, 0.06))

    print("  [7/7] Done.")
    return buf


# ================================================================== #
#  Preset registry                                                    #
# ================================================================== #

PRESETS = {
    "cosmic_vortex": create_cosmic_vortex,
    "nebula":        create_nebula,
    "galaxy":        create_galaxy,
    "quantum_field": create_quantum_field,
    "deep_space":    create_deep_space,
}
