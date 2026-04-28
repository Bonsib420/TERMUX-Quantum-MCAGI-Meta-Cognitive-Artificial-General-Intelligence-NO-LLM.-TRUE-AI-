#!/usr/bin/env python3
"""
Quantum MCAGI Procedural Image Generator v2.0
Massive quality upgrade — HDR tone mapping, volumetric rendering,
physically-based accretion disks, multi-pass bloom, ray-marched effects.
Pure math. No API keys.
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

def _seed_from_prompt(prompt: str) -> int:
return int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)

def _fbm_noise(shape, octaves=6, persistence=0.5, seed=42, lacunarity=2.0):
rng = np.random.RandomState(seed)
result = np.zeros(shape, dtype=np.float64)
amplitude = 1.0
total_amp = 0.0
for i in range(octaves):
freq = lacunarity**i
base_h = max(4, int(shape[0] / freq) + 2)
base_w = max(4, int(shape[1] / freq) + 2)
noise_layer = rng.rand(base_h, base_w)
noise_layer = ndimage.gaussian_filter(noise_layer, sigma=1.0)
scaled = zoom(
noise_layer,
(shape[0] / noise_layer.shape[0], shape[1] / noise_layer.shape[1]),
order=3,
)
scaled = scaled[: shape[0], : shape[1]]
result += scaled * amplitude
total_amp += amplitude
amplitude *= persistence
return result / total_amp

def _domain_warp_noise(shape, octaves=6, persistence=0.5, seed=42, warp_strength=0.5):
warp_x = _fbm_noise(shape, octaves=3, seed=seed + 1000) - 0.5
warp_y = _fbm_noise(shape, octaves=3, seed=seed + 2000) - 0.5
h, w = shape
y, x = np.mgrid[0:h, 0:w]
wx = np.clip((x + warp_x * w * warp_strength).astype(int), 0, w - 1)
wy = np.clip((y + warp_y * h * warp_strength).astype(int), 0, h - 1)
base = _fbm_noise(shape, octaves=octaves, persistence=persistence, seed=seed)
return base[wy, wx]

def _aces_tonemap(img):
a = 2.51
b = 0.03
c = 2.43
d = 0.59
e = 0.14
x = img * 0.6
return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)

def _multi_bloom(img_array, passes=3):
result = img_array.astype(np.float64) / 255.0
for i in range(passes):
threshold = 0.6 - i * 0.15
radius = 4 + i * 8
intensity = 0.4 - i * 0.08
bright = np.clip(result - threshold, 0, 10)
blurred = ndimage.gaussian_filter(bright, sigma=radius)
result += blurred * intensity
result = _aces_tonemap(result)
return (result * 255).astype(np.uint8)

def _radial_gradient(shape, cx=None, cy=None):
h, w = shape
if cx is None:
cx = w / 2
if cy is None:
cy = h / 2
y, x = np.mgrid[0:h, 0:w]
r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
r = r / max(r.max(), 1e-6)
return r

def _vignette(shape, strength=0.7):

r = _radial_gradient(shape)
v = 1.0 - (r**2.2) * strength
return np.clip(v, 0, 1)

def _blackbody_color(temp):
t = temp / 100.0
if t <= 66:
r = 1.0
g = max(
0, min(1, (99.4708025861 * math.log(max(t, 1)) - 161.1195681661) / 255.0)
)
else:
r = max(0, min(1, (329.698727446 * ((t - 60) ** -0.1332047592)) / 255.0))
g = max(0, min(1, (288.1221695283 * ((t - 60) ** -0.0755148492)) / 255.0))
if t >= 66:
b = 1.0
elif t <= 19:
b = 0.0
else:
b = max(
0,
min(
1, (138.5177312231 * math.log(max(t - 10, 1)) - 305.0447927307) / 255.0
),
)
return r, g, b

def _blackbody_array(temps):
r = np.zeros_like(temps)
g = np.zeros_like(temps)
b = np.zeros_like(temps)
t = temps / 100.0
low = t <= 66
high = ~low
r[low] = 1.0
safe_t_low = np.clip(t[low], 1, 1e6)
g[low] = np.clip(
(99.4708025861 * np.log(safe_t_low) - 161.1195681661) / 255.0, 0, 1
)
r[high] = np.clip((329.698727446 * ((t[high] - 60) ** -0.1332047592)) / 255.0, 0, 1)
g[high] = np.clip(
(288.1221695283 * ((t[high] - 60) ** -0.0755148492)) / 255.0, 0, 1
)
b[t >= 66] = 1.0
mid = (t > 19) & (t < 66)
safe_t_mid = np.clip(t[mid] - 10, 1, 1e6)
b[mid] = np.clip(
(138.5177312231 * np.log(safe_t_mid) - 305.0447927307) / 255.0, 0, 1
)
return np.stack([r, g, b], axis=-1)

def _star_field_v2(shape, density=1200, seed=42):
rng = np.random.RandomState(seed)
h, w = shape
stars = np.zeros((h, w, 3), dtype=np.float64)
n_faint = int(density * 3)
fx = rng.randint(0, w, n_faint)
fy = rng.randint(0, h, n_faint)
fb = rng.power(0.15, n_faint) * 45
ft = rng.uniform(3000, 20000, n_faint)
for i in range(n_faint):
if 0 <= fy[i] < h and 0 <= fx[i] < w:
rc, gc, bc = _blackbody_color(ft[i])
stars[fy[i], fx[i], 0] += fb[i] * rc
stars[fy[i], fx[i], 1] += fb[i] * gc
stars[fy[i], fx[i], 2] += fb[i] * bc
n_med = int(density * 0.3)
mx = rng.randint(0, w, n_med)
my = rng.randint(0, h, n_med)
mb = rng.power(0.25, n_med) * 180
mt = rng.uniform(3000, 25000, n_med)
for i in range(n_med):
x, y = mx[i], my[i]
rc, gc, bc = _blackbody_color(mt[i])
lum = mb[i]
for dy in range(-1, 2):
for dx in range(-1, 2):
ny, nx = y + dy, x + dx
if 0 <= ny < h and 0 <= nx < w:
d = abs(dx) + abs(dy)
f = [1.0, 0.35, 0.12][min(d, 2)]
stars[ny, nx, 0] += lum * rc * f
stars[ny, nx, 1] += lum * gc * f
stars[ny, nx, 2] += lum * bc * f
n_bright = int(density * 0.04)
bx = rng.randint(0, w, n_bright)
by = rng.randint(0, h, n_bright)
bb = rng.uniform(200, 400, n_bright)
bt = rng.uniform(4000, 30000, n_bright)
for i in range(n_bright):
x, y = bx[i], by[i]
rc, gc, bc = _blackbody_color(bt[i])
lum = bb[i]
size = rng.randint(2, 4)
for dy in range(-size, size + 1):

for dx in range(-size, size + 1):
ny, nx = y + dy, x + dx
if 0 <= ny < h and 0 <= nx < w:
d = math.sqrt(dx * dx + dy * dy)
f = max(0, 1.0 - d / (size + 0.3)) ** 2.5
stars[ny, nx, 0] += lum * rc * f
stars[ny, nx, 1] += lum * gc * f
stars[ny, nx, 2] += lum * bc * f
spike_len = rng.randint(5, 15)
for d in range(1, spike_len):
f = max(0, 1.0 - d / spike_len) ** 2 * 0.25
for sdx, sdy in [(d, 0), (-d, 0), (0, d), (0, -d)]:
ny, nx = y + sdy, x + sdx
if 0 <= ny < h and 0 <= nx < w:
stars[ny, nx, 0] += lum * rc * f
stars[ny, nx, 1] += lum * gc * f
stars[ny, nx, 2] += lum * bc * f
dust = _fbm_noise((h, w), octaves=4, persistence=0.5, seed=seed + 7777)
dust_dim = np.clip(dust * 0.6 + 0.4, 0.3, 1.0)
for c in range(3):
stars[..., c] *= dust_dim
glow = ndimage.gaussian_filter(stars, sigma=0.6)
stars = stars + glow * 0.2
return np.clip(stars, 0, 500)

def _color_map(value, palette):
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

ACCRETION_PALETTE = [
(0, 0, 0),
(40, 5, 2),
(120, 20, 5),
(200, 60, 10),
(255, 120, 30),
(255, 180, 60),
(255, 220, 140),
(255, 245, 220),
(240, 250, 255),
]
ACCRETION_PALETTE_COOL = [
(0, 0, 0),
(20, 5, 30),
(60, 10, 60),
(120, 30, 80),
(180, 60, 100),
(220, 100, 120),
(255, 160, 160),
(255, 220, 200),
(255, 245, 240),
]

def render_black_hole(w, h, seed, params=None):
params = params or {}
rng = np.random.RandomState(seed)
img = np.zeros((h, w, 3), dtype=np.float64)
stars = _star_field_v2((h, w), density=1500, seed=seed)
cx, cy = w / 2, h / 2
bh_radius = min(w, h) * 0.12
photon_ring = bh_radius * 1.5
isco = bh_radius * 3.0
accretion_outer = bh_radius * 5.0
accretion_inner = isco
y, x = np.mgrid[0:h, 0:w]
dx = (x - cx).astype(np.float64)
dy = (y - cy).astype(np.float64)
r = np.sqrt(dx**2 + dy**2)
theta = np.arctan2(dy, dx)
lensing_strength = 3.0
lens_factor = np.where(
r > bh_radius * 0.9,
1.0 + lensing_strength * (bh_radius / np.maximum(r, 1)) ** 2,
0.0,
)
secondary_lens = np.where(
r > bh_radius * 1.2, 0.3 * (bh_radius / np.maximum(r, 1)) ** 3, 0.0
)
lens_factor += secondary_lens
lensed_x = np.clip((cx + dx * lens_factor).astype(int), 0, w - 1)
lensed_y = np.clip((cy + dy * lens_factor).astype(int), 0, h - 1)

for c in range(3):
img[..., c] = stars[lensed_y, lensed_x, c]
tilt = params.get("tilt", 0.25)
cos_tilt = math.cos(tilt * math.pi)
disk_dy = dy * cos_tilt
disk_r = np.sqrt(dx**2 + disk_dy**2)
disk_noise1 = _fbm_noise((h, w), octaves=6, persistence=0.6, seed=seed + 1)
disk_noise2 = _fbm_noise((h, w), octaves=4, persistence=0.5, seed=seed + 2)
disk_noise3 = _domain_warp_noise(
(h, w), octaves=5, seed=seed + 3, warp_strength=0.15
)
spiral = (
np.sin(theta * 3 + np.log(np.maximum(disk_r, 1)) * 4 + disk_noise2 * 2) * 0.5
+ 0.5
)
disk_thickness = bh_radius * 0.12
thin_disk = np.exp(-(disk_dy**2) / (2 * disk_thickness**2))
inner_thick = np.exp(-(disk_dy**2) / (2 * (bh_radius * 0.25) ** 2))
puff = np.clip(1.0 - (disk_r - accretion_inner) / (bh_radius * 2), 0, 1)
thin_disk = thin_disk * (1 - puff) + inner_thick * puff
disk_valid = ((disk_r > accretion_inner * 0.8) & (disk_r < accretion_outer)).astype(
float
)
outer_fade = np.clip((accretion_outer - disk_r) / (accretion_outer * 0.3), 0, 1)
inner_fade = np.clip(
(disk_r - accretion_inner * 0.7) / (accretion_inner * 0.3), 0, 1
)
disk_valid *= outer_fade * inner_fade
disk_temp_base = np.clip(
1.0 - (disk_r - accretion_inner) / (accretion_outer - accretion_inner), 0, 1
)
disk_temp = disk_temp_base**0.5
doppler = 1.0 + 0.5 * np.sin(theta)
relativistic = np.clip(
1.0 / (1.0 + 0.3 * (bh_radius / np.maximum(disk_r, 1)) ** 0.5), 0.3, 1.0
)
disk_temp_shifted = np.clip(disk_temp * doppler * relativistic, 0, 1)
disk_detail = (0.5 + 0.3 * disk_noise1 + 0.2 * spiral) * (0.7 + 0.3 * disk_noise3)
disk_palette = np.array(ACCRETION_PALETTE, dtype=np.float64)
disk_colors = _color_map(disk_temp_shifted, ACCRETION_PALETTE)
disk_intensity = thin_disk * disk_valid * disk_detail * 1.0
for c in range(3):
img[..., c] += disk_colors[..., c] * disk_intensity * 0.6
glow_disk = ndimage.gaussian_filter(
np.stack([disk_colors[..., c] * disk_intensity for c in range(3)], axis=-1),
sigma=min(w, h) * 0.025,
)
for c in range(3):
img[..., c] += glow_disk[..., c] * 25
wide_glow = ndimage.gaussian_filter(
np.stack([disk_colors[..., c] * disk_intensity for c in range(3)], axis=-1),
sigma=min(w, h) * 0.07,
)
for c in range(3):
img[..., c] += wide_glow[..., c] * 8
for ring_r, ring_w, ring_int in [
(photon_ring, 0.04, 0.8),
(photon_ring * 1.015, 0.015, 0.4),
(photon_ring * 0.985, 0.015, 0.4),
]:
ring_mask = np.exp(-((r - ring_r) ** 2) / (2 * (bh_radius * ring_w) ** 2))
ring_noise = 0.7 + 0.3 * _fbm_noise((h, w), octaves=3, seed=seed + 10)
for c, val in enumerate([255, 160, 40]):
img[..., c] += val * ring_mask * ring_int * ring_noise * 0.5
inner_glow_r = bh_radius * 1.6
inner_glow = np.exp(-((r - inner_glow_r) ** 2) / (2 * (bh_radius * 0.35) ** 2))
inner_glow *= thin_disk * 0.3
for c, val in enumerate([255, 140, 30]):
img[..., c] += val * inner_glow * 0.3
event_fade = np.clip((r - bh_radius * 0.85) / (bh_radius * 0.15), 0, 1)
for c in range(3):
img[..., c] *= event_fade
jets = params.get("jets", True)
if jets:
jet_width_base = bh_radius * 0.04
jet_length = min(h, w) * 0.4
jet_noise = _fbm_noise((h, w), octaves=4, seed=seed + 20)
for sign in [-1, 1]:
jy_dist = sign * (y - cy)
jy_mask = (jy_dist > 0).astype(float)
dist_from_bh = np.abs(y - cy)
intensity = np.clip(1.0 - dist_from_bh / jet_length, 0, 1) ** 2.5 * jy_mask

spread = jet_width_base * (1 + 2.5 * dist_from_bh / jet_length)
jet_profile = np.exp(-(dx**2) / (2 * spread**2))
jet_core = np.exp(-(dx**2) / (2 * (spread * 0.25) ** 2))
jet_detail = 0.6 + 0.4 * jet_noise
jet_val = (jet_profile * 0.3 + jet_core * 0.7) * intensity * jet_detail
img[..., 0] += 50 * jet_val
img[..., 1] += 90 * jet_val
img[..., 2] += 180 * jet_val
n_debris = rng.randint(20, 50)
for _ in range(n_debris):
dr = rng.uniform(accretion_inner * 0.5, accretion_outer * 1.3)
da = rng.uniform(0, 2 * math.pi)
dx_d = dr * math.cos(da)
dy_d = dr * math.sin(da) * cos_tilt
px, py = int(cx + dx_d), int(cy + dy_d)
if 0 <= px < w and 0 <= py < h:
streak_len = rng.randint(2, 8)
streak_angle = da + math.pi / 2
brightness = rng.uniform(60, 200)
for s in range(streak_len):
sx = int(px + s * math.cos(streak_angle))
sy = int(py + s * math.sin(streak_angle))
if 0 <= sx < w and 0 <= sy < h:
falloff = 1.0 - s / streak_len
img[sy, sx, 0] += brightness * falloff
img[sy, sx, 1] += brightness * 0.7 * falloff
img[sy, sx, 2] += brightness * 0.3 * falloff
vig = _vignette((h, w), 0.6)
for c in range(3):
img[..., c] *= vig
img = np.clip(img, 0, 600)
img = img / 600.0
img = _aces_tonemap(img * 1.5)
img = (img * 255).astype(np.uint8)
img = _multi_bloom(img, passes=3)
return img

def _render_merging_black_holes(w, h, seed, params=None):
rng = np.random.RandomState(seed)
img = np.zeros((h, w, 3), dtype=np.float64)
stars = _star_field_v2((h, w), density=1200, seed=seed)
separation = min(w, h) * 0.22
cx1, cy1 = w / 2 - separation * 0.5, h / 2
cx2, cy2 = w / 2 + separation * 0.5, h / 2
y, x = np.mgrid[0:h, 0:w]
combined_lens = np.ones((h, w), dtype=np.float64)
for idx, (bcx, bcy, bseed) in enumerate([(cx1, cy1, seed), (cx2, cy2, seed + 500)]):
bdx = (x - bcx).astype(np.float64)
bdy = (y - bcy).astype(np.float64)
br = np.sqrt(bdx**2 + bdy**2)
btheta = np.arctan2(bdy, bdx)
bh_r = min(w, h) * 0.07
photon_r = bh_r * 1.5
accr_outer = bh_r * 3.5
accr_inner = bh_r * 1.8
lens = np.where(
br > bh_r * 0.9, 1.0 + 2.5 * (bh_r / np.maximum(br, 1)) ** 2, 0.0
)
lx = np.clip((bcx + bdx * lens).astype(int), 0, w - 1)
ly = np.clip((bcy + bdy * lens).astype(int), 0, h - 1)
weight = 0.6
for c in range(3):
img[..., c] += stars[ly, lx, c] * weight
disk_noise = _fbm_noise((h, w), octaves=5, persistence=0.6, seed=bseed + 1)
spiral = (
np.sin(btheta * 2.5 + np.log(np.maximum(br, 1)) * 3 + disk_noise * 1.5)
* 0.5
+ 0.5
)
thin_disk = np.exp(-(bdy**2) / (2 * (bh_r * 0.1) ** 2))
disk_valid = ((br > accr_inner) & (br < accr_outer)).astype(float)
outer_fade = np.clip((accr_outer - br) / (accr_outer * 0.3), 0, 1)
inner_fade = np.clip((br - accr_inner * 0.8) / (accr_inner * 0.2), 0, 1)
disk_valid *= outer_fade * inner_fade
disk_temp = (
np.clip(1.0 - (br - accr_inner) / (accr_outer - accr_inner), 0, 1) ** 0.5
)
doppler = 1.0 + 0.4 * np.sin(btheta)
disk_temp_shifted = np.clip(disk_temp * doppler, 0, 1)
disk_detail = 0.5 + 0.3 * disk_noise + 0.2 * spiral
disk_colors = _color_map(disk_temp_shifted, ACCRETION_PALETTE)
disk_intensity = thin_disk * disk_valid * disk_detail * 1.5
for c in range(3):

img[..., c] += disk_colors[..., c] * disk_intensity * 0.8
disk_glow_layer = np.stack(
[disk_colors[..., c] * disk_intensity for c in range(3)], axis=-1
)
disk_glow_layer = ndimage.gaussian_filter(
disk_glow_layer, sigma=min(w, h) * 0.018
)
for c in range(3):
img[..., c] += disk_glow_layer[..., c] * 35
wide_glow_m = ndimage.gaussian_filter(disk_glow_layer, sigma=min(w, h) * 0.05)
for c in range(3):
img[..., c] += wide_glow_m[..., c] * 12
for ring_off, ring_i in [(1.0, 0.9), (1.015, 0.45), (0.985, 0.45)]:
ring = np.exp(-((br - photon_r * ring_off) ** 2) / (2 * (bh_r * 0.04) ** 2))
for c, val in enumerate([255, 180, 50]):
img[..., c] += ring * val * ring_i * 0.6
fade = np.clip((br - bh_r * 0.85) / (bh_r * 0.15), 0, 1)
for c in range(3):
img[..., c] *= fade
mid_x, mid_y = w / 2, h / 2
bridge_dx = (x - mid_x).astype(np.float64)
bridge_dy = (y - mid_y).astype(np.float64)
bridge_r = np.sqrt(bridge_dx**2 + bridge_dy**2)
bridge_noise = _fbm_noise((h, w), octaves=5, seed=seed + 100)
bridge = np.exp(-(bridge_dy**2) / (2 * (min(h, w) * 0.025) ** 2))
bridge *= (np.abs(bridge_dx) < separation * 0.65).astype(float)
bridge_fade = np.exp(-np.abs(bridge_dx) / (separation * 0.4))
bridge *= bridge_fade
bridge *= 0.5 + 0.5 * bridge_noise
gw_waves = np.sin(bridge_r / (min(w, h) * 0.02) * math.pi) * 0.5 + 0.5
bridge *= 0.6 + 0.4 * gw_waves
for c, val in enumerate([200, 140, 255]):
img[..., c] += bridge * val * 0.5
gw_ring_noise = _fbm_noise((h, w), octaves=3, seed=seed + 200)
for gw_r_mult in [0.5, 0.8, 1.2, 1.6]:
gw_r = separation * gw_r_mult
gw_ring = np.exp(-((bridge_r - gw_r) ** 2) / (2 * (min(w, h) * 0.008) ** 2))
gw_ring *= 0.15 * (0.5 + 0.5 * gw_ring_noise)
for c, val in enumerate([150, 120, 200]):
img[..., c] += gw_ring * val
n_debris = rng.randint(30, 60)
for _ in range(n_debris):
which = rng.choice([0, 1])
bcx = cx1 if which == 0 else cx2
bcy = cy1 if which == 0 else cy2
bh_r = min(w, h) * 0.07
dr = rng.uniform(bh_r * 1.5, bh_r * 4)
da = rng.uniform(0, 2 * math.pi)
px = int(bcx + dr * math.cos(da))
py = int(bcy + dr * math.sin(da) * 0.3)
if 0 <= px < w and 0 <= py < h:
streak_len = rng.randint(2, 6)
sa = da + math.pi / 2
bright = rng.uniform(40, 160)
for s in range(streak_len):
sx = int(px + s * math.cos(sa))
sy = int(py + s * math.sin(sa))
if 0 <= sx < w and 0 <= sy < h:
f = 1.0 - s / streak_len
img[sy, sx, 0] += bright * f
img[sy, sx, 1] += bright * 0.6 * f
img[sy, sx, 2] += bright * 0.3 * f
vig = _vignette((h, w), 0.55)
for c in range(3):
img[..., c] *= vig
img = np.clip(img, 0, 600)
img = img / 600.0
img = _aces_tonemap(img * 1.4)
img = (img * 255).astype(np.uint8)
img = _multi_bloom(img, passes=3)
return img

NEBULA_PALETTES = {
"fire": [
(0, 0, 0),
(60, 5, 2),
(140, 25, 5),
(220, 70, 12),
(255, 140, 35),
(255, 200, 80),
(255, 240, 180),
],
"ice": [
(0, 0, 8),
(8, 15, 50),
(20, 45, 120),
(50, 100, 180),
(100, 170, 230),
(180, 220, 255),

(230, 245, 255),
],
"cosmic": [
(0, 0, 3),
(30, 3, 50),
(80, 15, 100),
(140, 35, 130),
(190, 70, 160),
(230, 130, 200),
(255, 200, 255),
],
"emerald": [
(0, 3, 0),
(5, 30, 12),
(15, 80, 35),
(40, 150, 65),
(90, 210, 110),
(160, 240, 170),
(220, 255, 230),
],
"plasma": [
(0, 0, 0),
(50, 0, 70),
(100, 0, 140),
(170, 40, 110),
(240, 100, 50),
(255, 180, 40),
(255, 240, 160),
],
"void": [
(0, 0, 0),
(10, 3, 25),
(25, 8, 45),
(45, 12, 65),
(70, 25, 90),
(100, 40, 120),
(140, 70, 160),
],
}

DUAL_TONE_PAIRS = {
"cosmic": ("fire", "ice"),
"fire": ("fire", "plasma"),
"ice": ("ice", "cosmic"),
"emerald": ("emerald", "ice"),
"plasma": ("plasma", "fire"),
"void": ("void", "cosmic"),
}

def render_nebula(w, h, seed, params=None):
params = params or {}
palette_name = params.get("palette", "cosmic")
rng = np.random.RandomState(seed)
warm_name, cool_name = DUAL_TONE_PAIRS.get(palette_name, ("fire", "ice"))
warm_palette = NEBULA_PALETTES[warm_name]
cool_palette = NEBULA_PALETTES[cool_name]
stars = _star_field_v2((h, w), density=2000, seed=seed)
img = stars.copy()
y_grid, x_grid = np.mgrid[0:h, 0:w]
grad_noise = _domain_warp_noise(
(h, w), octaves=5, seed=seed + 9000, warp_strength=0.3
)
spatial_grad = (x_grid / w) * 0.5 + grad_noise * 0.5
spatial_grad = (spatial_grad - spatial_grad.min()) / (
spatial_grad.max() - spatial_grad.min() + 1e-8
)
spatial_grad = np.clip((spatial_grad - 0.3) * 2.5, 0, 1)
spatial_grad = ndimage.gaussian_filter(spatial_grad, sigma=min(w, h) * 0.03)
cloud_base = np.zeros((h, w), dtype=np.float64)
n_centers = rng.randint(4, 9)
for i in range(n_centers):
cx = rng.uniform(w * -0.1, w * 1.1)
cy = rng.uniform(h * -0.1, h * 1.1)
spread_x = rng.uniform(w * 0.1, w * 0.4)
spread_y = rng.uniform(h * 0.1, h * 0.4)
amp = rng.uniform(0.4, 1.0)
angle = rng.uniform(0, math.pi)
cos_a, sin_a = math.cos(angle), math.sin(angle)
ddx = x_grid - cx
ddy = y_grid - cy
rx = ddx * cos_a + ddy * sin_a
ry = -ddx * sin_a + ddy * cos_a
blob = np.exp(-(rx**2) / (2 * spread_x**2) - (ry**2) / (2 * spread_y**2))
cloud_base += blob * amp
cloud_base = cloud_base / (cloud_base.max() + 1e-8)
cloud_base = ndimage.gaussian_filter(cloud_base, sigma=min(w, h) * 0.03)
detail1 = _domain_warp_noise(
(h, w), octaves=5, persistence=0.5, seed=seed + 10, warp_strength=0.25
)
detail1 = ndimage.gaussian_filter(detail1, sigma=min(w, h) * 0.01)
detail2 = _domain_warp_noise(
(h, w), octaves=4, persistence=0.45, seed=seed + 15, warp_strength=0.2
)

detail2 = ndimage.gaussian_filter(detail2, sigma=min(w, h) * 0.015)
fine = _fbm_noise((h, w), octaves=6, persistence=0.55, seed=seed + 20)
fine = ndimage.gaussian_filter(fine, sigma=min(w, h) * 0.008)
warp_u = _fbm_noise((h, w), octaves=4, seed=seed + 300)
warp_v = _fbm_noise((h, w), octaves=4, seed=seed + 310)
warp_s = min(w, h) * 0.18
wx = np.clip((x_grid + (warp_u - 0.5) * warp_s).astype(int), 0, w - 1)
wy = np.clip((y_grid + (warp_v - 0.5) * warp_s).astype(int), 0, h - 1)
combined = cloud_base[wy, wx] * (0.4 + 0.35 * detail1 + 0.25 * detail2)
combined *= 0.5 + 0.3 * fine + 0.2
combined = (combined - combined.min()) / (combined.max() - combined.min() + 1e-8)
combined = combined**0.5
smooth_cloud = ndimage.gaussian_filter(combined, sigma=min(w, h) * 0.025)
medium_detail = ndimage.gaussian_filter(combined, sigma=min(w, h) * 0.008)
contrast_cloud = np.clip((smooth_cloud - 0.2) * 3.0, 0, 1) ** 0.65
warm_smooth = _color_map(contrast_cloud, warm_palette)
cool_smooth = _color_map(contrast_cloud, cool_palette)
warm_detail = _color_map(medium_detail, warm_palette)
cool_detail = _color_map(medium_detail, cool_palette)
glow_density = np.clip(contrast_cloud * 1.8, 0, 1)
for c in range(3):
smooth_col = (
warm_smooth[..., c] * (1 - spatial_grad)
+ cool_smooth[..., c] * spatial_grad
)
img[..., c] = (
img[..., c] * (1 - glow_density * 0.8) + smooth_col * glow_density * 2.0
)
detail_mask = (contrast_cloud > 0.05).astype(float)
detail_density = np.clip(medium_detail * 2.0 - 0.15, 0, 1) * detail_mask
for c in range(3):
detail_col = (
warm_detail[..., c] * (1 - spatial_grad)
+ cool_detail[..., c] * spatial_grad
)
img[..., c] += detail_col * detail_density * 1.0
layer2_noise = _domain_warp_noise(
(h, w), octaves=5, seed=seed + 100, warp_strength=0.2
)
layer2_smooth = ndimage.gaussian_filter(layer2_noise, sigma=min(w, h) * 0.025)
layer2_density = np.clip(layer2_smooth - 0.2, 0, 1) * np.clip(
contrast_cloud * 2.0, 0, 1
)
layer2_colors_w = _color_map(layer2_smooth, warm_palette)
layer2_colors_c = _color_map(layer2_smooth, cool_palette)
for c in range(3):
l2_col = (
layer2_colors_w[..., c] * (1 - spatial_grad)
+ layer2_colors_c[..., c] * spatial_grad
)
img[..., c] += l2_col * layer2_density * 1.5
third_name = {
"fire": "plasma",
"ice": "emerald",
"cosmic": "void",
"emerald": "cosmic",
"plasma": "cosmic",
"void": "fire",
}.get(palette_name, "cosmic")
third_palette = NEBULA_PALETTES[third_name]
layer3_noise = _domain_warp_noise(
(h, w), octaves=4, seed=seed + 200, warp_strength=0.15
)
layer3_smooth = ndimage.gaussian_filter(layer3_noise, sigma=min(w, h) * 0.03)
layer3_density = (
np.clip(layer3_smooth - 0.3, 0, 1) * np.clip(contrast_cloud * 1.5, 0, 1) * 0.7
)
layer3_colors = _color_map(layer3_smooth, third_palette)
for c in range(3):
img[..., c] += layer3_colors[..., c] * layer3_density * 1.0
for fil_seed, fil_thresh, fil_bright in [
(seed + 400, 30, 0.7),
(seed + 410, 40, 0.5),
(seed + 420, 50, 0.3),
]:
fil = _fbm_noise((h, w), octaves=7, persistence=0.7, seed=fil_seed)
filaments = np.exp(-(np.abs(fil - 0.5) * fil_thresh)) * fil_bright
filaments *= (contrast_cloud > 0.05).astype(float)
filaments = ndimage.gaussian_filter(filaments, sigma=1.0)
fil_grad = spatial_grad if fil_seed % 2 == 0 else (1 - spatial_grad)
for c in range(3):
bright_col = (
warm_palette[-1][c] * (1 - fil_grad) + cool_palette[-1][c] * fil_grad
)
img[..., c] += filaments * bright_col * 0.8
for dk_seed, dk_width in [(seed + 600, 0.07), (seed + 610, 0.09)]:
dark_fil = _fbm_noise((h, w), octaves=6, persistence=0.6, seed=dk_seed)
dark_mask = (np.abs(dark_fil - 0.5) < dk_width).astype(float) * (
contrast_cloud > 0.12
).astype(float)

dark_mask = ndimage.gaussian_filter(dark_mask, sigma=min(w, h) * 0.008)
for c in range(3):
img[..., c] *= 1.0 - dark_mask * 0.6
edge_detect = np.abs(
ndimage.gaussian_filter(smooth_cloud, sigma=3)
- ndimage.gaussian_filter(smooth_cloud, sigma=8)
)
edge_detect = edge_detect / (edge_detect.max() + 1e-8)
edge_bright = edge_detect * (contrast_cloud > 0.08).astype(float)
edge_bright = ndimage.gaussian_filter(edge_bright, sigma=1.5)
for c in range(3):
bright_edge = (
warm_palette[-1][c] * (1 - spatial_grad)
+ cool_palette[-1][c] * spatial_grad
)
img[..., c] += edge_bright * bright_edge * 0.5
bright_noise = _fbm_noise((h, w), octaves=3, seed=seed + 500)
hot = np.clip(bright_noise - 0.55, 0, 1) * 5 * (contrast_cloud > 0.15).astype(float)
hot = ndimage.gaussian_filter(hot, sigma=min(w, h) * 0.02)
hot_wide = ndimage.gaussian_filter(hot, sigma=min(w, h) * 0.06)
for c in range(3):
bright_col = (
warm_palette[-1][c] * (1 - spatial_grad)
+ cool_palette[-1][c] * spatial_grad
)
img[..., c] += hot * bright_col / 255.0 * 250
img[..., c] += hot_wide * bright_col / 255.0 * 100
n_stars_embedded = rng.randint(8, 18)
for _ in range(n_stars_embedded):
sx, sy = rng.randint(0, w), rng.randint(0, h)
if contrast_cloud[min(sy, h - 1), min(sx, w - 1)] > 0.1:
sr = rng.uniform(min(w, h) * 0.005, min(w, h) * 0.018)
glow = np.exp(-((x_grid - sx) ** 2 + (y_grid - sy) ** 2) / (2 * sr**2))
star_bright = rng.uniform(0.4, 1.0)
wide = np.exp(
-((x_grid - sx) ** 2 + (y_grid - sy) ** 2) / (2 * (sr * 5) ** 2)
)
for c in range(3):
img[..., c] += glow * 300 * star_bright
local_col = warm_palette[-2][c] * (1 - sx / w) + cool_palette[-2][c] * (
sx / w
)
img[..., c] += wide * local_col * 0.12 * star_bright
vig = _vignette((h, w), 0.5)
for c in range(3):
img[..., c] *= vig
img = np.clip(img, 0, 600)
img = img / 600.0
img = _aces_tonemap(img * 1.8)
lum = 0.2126 * img[..., 0] + 0.7152 * img[..., 1] + 0.0722 * img[..., 2]
lum = lum[..., np.newaxis]
sat_boost = 1.6
img = lum + (img - lum) * sat_boost
img = np.clip(img, 0, 1)
img = (img * 255).astype(np.uint8)
img = _multi_bloom(img, passes=3)
return img

def _v2_post_process(img_array, bloom_passes=2):
img = np.clip(img_array.astype(np.float64), 0, 500)
vig = _vignette(img.shape[:2], 0.45)
for c in range(3):
img[..., c] *= vig
img = img / 500.0
img = _aces_tonemap(img * 1.2)
img = (img * 255).astype(np.uint8)
img = _multi_bloom(img, passes=bloom_passes)
return img

def _import_v1_renderers():
from image_generator import (
render_galaxy,
render_quantum_state,
render_wormhole,
render_supernova,
render_planet,
render_fractal,
render_neural,
render_consciousness,
_detect_scene,
RENDERERS as V1_RENDERERS,
)
return {
"galaxy": render_galaxy,
"quantum_state": render_quantum_state,
"wormhole": render_wormhole,
"supernova": render_supernova,
"planet": render_planet,
"fractal": render_fractal,
"neural": render_neural,
"consciousness": render_consciousness,

}, _detect_scene

RENDERERS_V2 = {
"black_hole": render_black_hole,
"nebula": render_nebula,
}

MOOD_COLORS = {
"fire": {
"keywords": [
"fire",
"flame",
"burn",
"hot",
"lava",
"magma",
"inferno",
"dragon",
"phoenix",
"hell",
"volcanic",
"blaze",
"ember",
"molten",
],
"palette": "fire",
},
"ice": {
"keywords": [
"ice",
"cold",
"frozen",
"frost",
"winter",
"snow",
"arctic",
"glacier",
"crystal",
"chill",
"freeze",
],
"palette": "ice",
},
"emerald": {
"keywords": [
"green",
"forest",
"nature",
"emerald",
"life",
"growth",
"plant",
"tree",
"leaf",
"garden",
"jungle",
"bio",
"organic",
"alien",
],
"palette": "emerald",
},
"cosmic": {
"keywords": [
"purple",
"violet",
"cosmic",
"mystic",
"magic",
"wizard",
"spell",
"ethereal",
"spirit",
"soul",
"astral",
"psychedelic",
],
"palette": "cosmic",
},
"plasma": {
"keywords": [
"energy",
"electric",
"lightning",
"power",
"plasma",
"thunder",
"storm",
"volt",
"spark",
"charge",
"neon",
"glow",
],
"palette": "plasma",
},
"void": {
"keywords": [
"dark",

"void",
"shadow",
"death",
"abyss",
"deep",
"night",
"horror",
"fear",
"demon",
"evil",
"nightmare",
],
"palette": "void",
},
"warm": {
"keywords": [
"sunset",
"sunrise",
"dawn",
"dusk",
"warm",
"golden",
"amber",
"orange",
"autumn",
"copper",
"bronze",
"desert",
"sand",
],
"palette": "fire",
},
"ocean": {
"keywords": [
"ocean",
"sea",
"water",
"wave",
"marine",
"aqua",
"underwater",
"deep sea",
"coral",
"tide",
"current",
],
"palette": "ice",
},
}

EXTRA_SCENE_KEYWORDS = {
"landscape": [
"landscape",
"mountain",
"valley",
"terrain",
"canyon",
"cliff",
"sunset",
"sunrise",
"horizon",
"sky",
"cloud",
"weather",
"ocean",
"sea",
"lake",
"river",
"waterfall",
"beach",
"forest",
"desert",
"tundra",
"prairie",
"field",
],
"creature": [
"dragon",
"creature",
"monster",
"beast",
"leviathan",
"titan",
"serpent",
"phoenix",
"demon",
"angel",
"alien creature",
"wolf",
"eagle",
"whale",
"shark",
"spider",
"insect",
],
"structure": [
"city",
"building",
"tower",
"castle",

"temple",
"pyramid",
"ruins",
"architecture",
"bridge",
"monument",
"cathedral",
"spaceship",
"station",
"vessel",
"craft",
"machine",
],
"abstract": [
"abstract",
"pattern",
"geometric",
"art",
"color",
"wave",
"flow",
"swirl",
"vortex",
"spiral",
"symmetry",
"tessellation",
"dream",
"vision",
"hallucination",
"psychedelic",
],
"energy": [
"energy",
"explosion",
"blast",
"eruption",
"shockwave",
"lightning",
"thunder",
"storm",
"aurora",
"radiation",
"particle",
"beam",
"ray",
"flash",
"pulse",
],
}

def _detect_mood_palette(prompt):
prompt_lower = prompt.lower()
best_score = 0
best_palette = "cosmic"
for mood, info in MOOD_COLORS.items():
score = sum(len(kw) for kw in info["keywords"] if kw in prompt_lower)
if score > best_score:
best_score = score
best_palette = info["palette"]
return best_palette

def _detect_extra_scene(prompt):
prompt_lower = prompt.lower()
best_score = 0
best_scene = None
for scene, keywords in EXTRA_SCENE_KEYWORDS.items():
score = sum(len(kw) for kw in keywords if kw in prompt_lower)
if score > best_score:
best_score = score
best_scene = scene
return best_scene if best_score > 0 else None

def render_landscape(w, h, seed, params=None):
params = params or {}
rng = np.random.RandomState(seed)
palette_name = _detect_mood_palette(params.get("_prompt", ""))
palette = NEBULA_PALETTES.get(palette_name, NEBULA_PALETTES["fire"])
img = np.zeros((h, w, 3), dtype=np.float64)
y_grid, x_grid = np.mgrid[0:h, 0:w]
sky_grad = (y_grid / h) ** 1.5
sky_colors = _color_map(sky_grad, palette[::-1])
for c in range(3):
img[..., c] = sky_colors[..., c] * 0.6
sky_noise = _domain_warp_noise((h, w), octaves=5, seed=seed + 1, warp_strength=0.12)
cloud_mask = np.clip(sky_noise - 0.35, 0, 1) * 2.0
cloud_mask *= np.clip(1.0 - y_grid / (h * 0.7), 0, 1)
cloud_detail = _fbm_noise((h, w), octaves=6, persistence=0.55, seed=seed + 2)
cloud_mask *= 0.5 + 0.5 * cloud_detail
cloud_col = np.array(palette[-2], dtype=np.float64) / 255.0
for c in range(3):
img[..., c] += cloud_mask * (cloud_col[c] * 200 + 60)
horizon_y = h * 0.55
n_ridges = rng.randint(3, 6)
for i in range(n_ridges):

ridge_y = horizon_y + i * h * 0.06
ridge_noise = _fbm_noise(
(1, w), octaves=5, persistence=0.6, seed=seed + 100 + i
)
ridge_heights = ridge_noise[0] * h * 0.15
darkness = 0.3 + 0.15 * i
for x in range(w):
ry = int(ridge_y - ridge_heights[x])
if 0 <= ry < h:
for y in range(ry, h):
fade = min(1.0, (y - ry) / (h * 0.05 + 1))
col_idx = min(len(palette) - 1, i + 1)
for c in range(3):
img[y, x, c] = (
img[y, x, c] * (1 - fade * 0.7)
+ palette[col_idx][c] * darkness * fade * 0.7
)
ground = (y_grid > horizon_y + h * 0.1).astype(float)
ground_noise = _fbm_noise((h, w), octaves=6, persistence=0.5, seed=seed + 50)
ground_detail = ground * (0.3 + 0.7 * ground_noise)
for c in range(3):
img[..., c] = (
img[..., c] * (1 - ground * 0.5) + palette[2][c] * ground_detail * 0.4
)
glow_y = int(horizon_y)
if 0 < glow_y < h:
for gy in range(max(0, glow_y - int(h * 0.08)), min(h, glow_y + int(h * 0.08))):
fade = max(0, 1.0 - abs(gy - glow_y) / (h * 0.08)) ** 2
for c in range(3):
img[gy, :, c] += palette[-1][c] * fade * 0.5
n_stars_sky = 200 if palette_name in ["void", "ice"] else 80
for _ in range(n_stars_sky):
sx, sy = rng.randint(0, w), rng.randint(0, int(horizon_y * 0.8))
b = rng.uniform(30, 120)
if 0 <= sy < h and 0 <= sx < w:
img[sy, sx] += b
return _v2_post_process(img)

def render_creature(w, h, seed, params=None):
params = params or {}
rng = np.random.RandomState(seed)
palette_name = _detect_mood_palette(params.get("_prompt", ""))
palette = NEBULA_PALETTES.get(palette_name, NEBULA_PALETTES["fire"])
img = np.zeros((h, w, 3), dtype=np.float64)
stars = _star_field_v2((h, w), density=600, seed=seed)
img += stars * 0.4
y_grid, x_grid = np.mgrid[0:h, 0:w]
cx, cy = w * 0.5, h * 0.45
body_noise = _domain_warp_noise(
(h, w), octaves=6, seed=seed + 1, warp_strength=0.25
)
form = np.zeros((h, w), dtype=np.float64)
body_rx, body_ry = w * 0.18, h * 0.22
body = np.exp(
-((x_grid - cx) ** 2) / (2 * body_rx**2)
- ((y_grid - cy) ** 2) / (2 * body_ry**2)
)
form += body
head_cx, head_cy = cx + w * 0.12, cy - h * 0.18
head_r = min(w, h) * 0.09
head = np.exp(
-((x_grid - head_cx) ** 2 + (y_grid - head_cy) ** 2) / (2 * head_r**2)
)
form += head * 0.8
for i in range(rng.randint(2, 5)):
angle = rng.uniform(0, 2 * math.pi)
length = rng.uniform(min(w, h) * 0.12, min(w, h) * 0.25)
lx = cx + math.cos(angle) * length * 0.5
ly = cy + math.sin(angle) * length * 0.5
lr = rng.uniform(min(w, h) * 0.03, min(w, h) * 0.06)
limb = np.exp(-((x_grid - lx) ** 2 + (y_grid - ly) ** 2) / (2 * lr**2))
form += limb * 0.5
form *= 0.5 + 0.5 * body_noise
form = np.clip(form, 0, 1)
creature_colors = _color_map(form, palette)
for c in range(3):
img[..., c] += creature_colors[..., c] * form * 0.8
edge = np.abs(
ndimage.gaussian_filter(form, sigma=2) - ndimage.gaussian_filter(form, sigma=4)
)
edge = edge / (edge.max() + 1e-8)
for c in range(3):
img[..., c] += edge * palette[-1][c] * 0.6
eye_glow = np.exp(
-((x_grid - head_cx) ** 2 + (y_grid - head_cy) ** 2) / (2 * (head_r * 0.2) ** 2)
)

for c in range(3):
img[..., c] += eye_glow * palette[-1][c] * 1.5
energy_noise = _fbm_noise((h, w), octaves=4, seed=seed + 200)
energy = (energy_noise > 0.65).astype(float) * form
energy = ndimage.gaussian_filter(energy, sigma=3)
for c in range(3):
img[..., c] += energy * palette[-2][c] * 0.5
aura = ndimage.gaussian_filter(form, sigma=min(w, h) * 0.04)
for c in range(3):
img[..., c] += aura * palette[3][c] * 0.15
return _v2_post_process(img)

def render_structure(w, h, seed, params=None):
params = params or {}
rng = np.random.RandomState(seed)
palette_name = _detect_mood_palette(params.get("_prompt", ""))
palette = NEBULA_PALETTES.get(palette_name, NEBULA_PALETTES["cosmic"])
img = np.zeros((h, w, 3), dtype=np.float64)
stars = _star_field_v2((h, w), density=800, seed=seed)
img += stars * 0.5
y_grid, x_grid = np.mgrid[0:h, 0:w]
cx, cy = w * 0.5, h * 0.5
n_towers = rng.randint(3, 8)
for i in range(n_towers):
tx = rng.uniform(w * 0.15, w * 0.85)
tw = rng.uniform(w * 0.04, w * 0.1)
th = rng.uniform(h * 0.2, h * 0.6)
base_y = h * rng.uniform(0.55, 0.75)
tower_mask = (
(np.abs(x_grid - tx) < tw / 2) & (y_grid > base_y - th) & (y_grid < base_y)
).astype(float)
taper = np.clip(1.0 - (base_y - y_grid) / th, 0, 1)
taper_width = tw * (0.5 + 0.5 * taper)
tower_mask = (
(np.abs(x_grid - tx) < taper_width / 2).astype(float)
* (y_grid > base_y - th).astype(float)
* (y_grid < base_y).astype(float)
)
detail_noise = _fbm_noise((h, w), octaves=5, seed=seed + 300 + i)
tower_detail = tower_mask * (0.4 + 0.6 * detail_noise)
col_idx = min(len(palette) - 1, max(2, i % len(palette)))
for c in range(3):
img[..., c] += tower_detail * palette[col_idx][c] * 1.2
window_noise = _fbm_noise(
(h, w), octaves=8, persistence=0.7, seed=seed + 400 + i
)
windows = (window_noise > 0.55).astype(float) * tower_mask
for c in range(3):
img[..., c] += windows * palette[-1][c] * 1.5
edge_h = np.abs(
ndimage.gaussian_filter(tower_mask, sigma=1)
- ndimage.gaussian_filter(tower_mask, sigma=2.5)
)
for c in range(3):
img[..., c] += edge_h * palette[-2][c] * 1.0
ground_y = h * 0.7
ground = np.clip((y_grid - ground_y) / (h * 0.15), 0, 1)
ground_noise = _fbm_noise((h, w), octaves=5, seed=seed + 500)
for c in range(3):
img[..., c] += ground * palette[2][c] * 0.6 * (0.5 + 0.5 * ground_noise)
fog = np.exp(-((y_grid - ground_y) ** 2) / (2 * (h * 0.12) ** 2))
fog_noise = _fbm_noise((h, w), octaves=3, seed=seed + 600)
fog *= 0.4 + 0.6 * fog_noise
for c in range(3):
img[..., c] += fog * palette[-2][c] * 0.5
sky_glow = np.clip(1.0 - y_grid / (h * 0.5), 0, 1) ** 2
sky_noise = _fbm_noise((h, w), octaves=3, seed=seed + 700)
for c in range(3):
img[..., c] += sky_glow * palette[3][c] * 0.15 * (0.5 + 0.5 * sky_noise)
return _v2_post_process(img)

def render_abstract(w, h, seed, params=None):
params = params or {}
rng = np.random.RandomState(seed)
palette_name = _detect_mood_palette(params.get("_prompt", ""))
palette = NEBULA_PALETTES.get(palette_name, NEBULA_PALETTES["plasma"])
img = np.zeros((h, w, 3), dtype=np.float64)
y_grid, x_grid = np.mgrid[0:h, 0:w]
layer1 = _domain_warp_noise(
(h, w), octaves=7, persistence=0.6, seed=seed, warp_strength=0.3
)
layer2 = _domain_warp_noise(

(h, w), octaves=5, persistence=0.5, seed=seed + 100, warp_strength=0.2
)
layer3 = _fbm_noise((h, w), octaves=8, persistence=0.65, seed=seed + 200)
combined = layer1 * 0.5 + layer2 * 0.3 + layer3 * 0.2
combined = (combined - combined.min()) / (combined.max() - combined.min() + 1e-8)
colors1 = _color_map(combined, palette)
for c in range(3):
img[..., c] = colors1[..., c] * 0.8
sec_map = {
"fire": "plasma",
"ice": "cosmic",
"cosmic": "plasma",
"emerald": "ice",
"plasma": "fire",
"void": "cosmic",
}
sec_palette = NEBULA_PALETTES[sec_map.get(palette_name, "cosmic")]
phase = _fbm_noise((h, w), octaves=6, seed=seed + 300)
phase_colors = _color_map(phase, sec_palette)
blend = np.clip(layer2 - 0.3, 0, 1) * 0.5
for c in range(3):
img[..., c] = img[..., c] * (1 - blend) + phase_colors[..., c] * blend
edges = np.abs(
ndimage.gaussian_filter(combined, sigma=1)
- ndimage.gaussian_filter(combined, sigma=3)
)
edges = edges / (edges.max() + 1e-8)
for c in range(3):
img[..., c] += edges * palette[-1][c] * 0.4
voronoi_noise = _fbm_noise((h, w), octaves=3, seed=seed + 400)
cells = (np.abs(voronoi_noise - 0.5) < 0.03).astype(float)
cells = ndimage.gaussian_filter(cells, sigma=1)
for c in range(3):
img[..., c] += cells * palette[-2][c] * 0.6
sym_x = np.abs(x_grid - w / 2) / (w / 2)
sym_pattern = np.sin(sym_x * 12 + combined * 6) * 0.5 + 0.5
sym_mask = (sym_pattern > 0.7).astype(float) * 0.15
for c in range(3):
img[..., c] += sym_mask * palette[-1][c]
return _v2_post_process(img)

def render_energy(w, h, seed, params=None):
params = params or {}
rng = np.random.RandomState(seed)
palette_name = _detect_mood_palette(params.get("_prompt", ""))
palette = NEBULA_PALETTES.get(palette_name, NEBULA_PALETTES["plasma"])
img = np.zeros((h, w, 3), dtype=np.float64)
stars = _star_field_v2((h, w), density=500, seed=seed)
img += stars * 0.3
y_grid, x_grid = np.mgrid[0:h, 0:w]
cx, cy = w / 2, h / 2
r = np.sqrt((x_grid - cx) ** 2 + (y_grid - cy) ** 2)
theta = np.arctan2(y_grid - cy, x_grid - cx)
r_norm = r / (min(w, h) * 0.5)
core_r = min(w, h) * 0.06
core = np.exp(-(r**2) / (2 * core_r**2))
core_glow = np.exp(-(r**2) / (2 * (core_r * 3) ** 2))
for c in range(3):
img[..., c] += core * palette[-1][c] * 2.0
img[..., c] += core_glow * palette[-2][c] * 0.4
n_bolts = rng.randint(6, 14)
for i in range(n_bolts):
bolt_angle = rng.uniform(0, 2 * math.pi)
bolt_length = rng.uniform(min(w, h) * 0.2, min(w, h) * 0.45)
bolt_noise = _fbm_noise((h, w), octaves=5, seed=seed + 50 + i)
angle_diff = np.abs(theta - bolt_angle)
angle_diff = np.minimum(angle_diff, 2 * math.pi - angle_diff)
bolt_width = 0.04 + 0.03 * bolt_noise
bolt_mask = np.exp(-(angle_diff**2) / (2 * bolt_width**2))
bolt_reach = np.clip(1.0 - r / bolt_length, 0, 1) ** 0.3
bolt_mask *= bolt_reach
bolt_mask *= (r > core_r * 0.3).astype(float)
bolt_detail = 0.4 + 0.6 * bolt_noise
bolt_mask *= bolt_detail
bolt_core = np.exp(-(angle_diff**2) / (2 * (bolt_width * 0.3) ** 2))
bolt_core *= bolt_reach * (r > core_r * 0.3).astype(float)
col_idx = min(len(palette) - 1, 3 + i % 4)
for c in range(3):
img[..., c] += bolt_mask * palette[col_idx][c] * 1.2
img[..., c] += bolt_core * palette[-1][c] * 0.8
shockwaves = [0.15, 0.3, 0.5, 0.7, 0.9]
sw_noise = _fbm_noise((h, w), octaves=3, seed=seed + 300)
for j, sw_r in enumerate(shockwaves):
ring_r = min(w, h) * sw_r * 0.5
ring = np.exp(-((r - ring_r) ** 2) / (2 * (min(w, h) * 0.008) ** 2))

ring *= 0.5 + 0.5 * sw_noise
intensity = 0.5 * (1.0 - j * 0.12)
for c in range(3):
img[..., c] += ring * palette[-2][c] * intensity
particle_noise = _domain_warp_noise(
(h, w), octaves=5, seed=seed + 400, warp_strength=0.18
)
particles = np.clip(particle_noise - 0.55, 0, 1) * 2
particles *= np.clip(1.0 - r_norm * 0.7, 0, 1)
particles = ndimage.gaussian_filter(particles, sigma=1.2)
for c in range(3):
img[..., c] += particles * palette[-1][c] * 0.6
ambient = _domain_warp_noise((h, w), octaves=4, seed=seed + 500, warp_strength=0.1)
ambient = np.clip(ambient - 0.3, 0, 1) * np.clip(1.0 - r_norm * 0.8, 0, 1)
for c in range(3):
img[..., c] += ambient * palette[3][c] * 0.2
return _v2_post_process(img, bloom_passes=3)

EXTRA_RENDERERS = {
"landscape": render_landscape,
"creature": render_creature,
"structure": render_structure,
"abstract": render_abstract,
"energy": render_energy,
}

def generate_image(
prompt: str, width: int = 512, height: int = 512, variation_seed: int = None
) -> Image.Image:
seed = _seed_from_prompt(prompt)
if variation_seed is not None:
seed = (seed + variation_seed) % (2**31)
v1_renderers, detect_scene = _import_v1_renderers()
scene, params = detect_scene(prompt)
params["_prompt"] = prompt
prompt_lower = prompt.lower()
from image_generator import SCENE_KEYWORDS
v1_matched = any(
any(kw in prompt_lower for kw in keywords)
for keywords in SCENE_KEYWORDS.values()
)
if scene == "black_hole" and params.get("merging"):
img_array = _render_merging_black_holes(width, height, seed, params)
elif scene in RENDERERS_V2 and v1_matched:
img_array = RENDERERS_V2[scene](width, height, seed, params)
elif scene in v1_renderers and v1_matched:
raw = v1_renderers[scene](width, height, seed, params)
img_array = _v2_post_process(raw)
else:
extra_scene = _detect_extra_scene(prompt)
if extra_scene and extra_scene in EXTRA_RENDERERS:
img_array = EXTRA_RENDERERS[extra_scene](width, height, seed, params)
else:
mood_palette = _detect_mood_palette(prompt)
params["palette"] = mood_palette
img_array = render_nebula(width, height, seed, params)
return Image.fromarray(img_array)

def get_available_scenes():
v1_renderers, _ = _import_v1_renderers()
all_scenes = list(RENDERERS_V2.keys()) + [
k for k in v1_renderers if k not in RENDERERS_V2
]
all_scenes += list(EXTRA_RENDERERS.keys())
return all_scenes

