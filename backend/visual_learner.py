#!/usr/bin/env python3
"""
Quantum MCAGI Visual Learner
Extracts mathematical features from images and stores them as visual vocabulary
in the brain state — the visual equivalent of Markov chain text learning.

Extracts:
- Dominant color palettes (k-means clustering in LAB space)
- Spatial frequency analysis (FFT-based texture signatures)
- Color temperature distributions
- Brightness/contrast profiles
- Compositional structure (where bright/dark regions cluster)
- Texture complexity metrics (fractal dimension estimates)

All pure math. No neural networks. No API keys.
"""

import numpy as np
from PIL import Image
import io
import math
import hashlib
import json
import os
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("visual_learner")

DATA_DIR = Path(os.environ.get("RUNTIME_DATA", "runtime-data"))
VISUAL_STATE_FILE = DATA_DIR / "visual_memory.json"


def _rgb_to_lab(rgb):
    r, g, b = rgb[..., 0] / 255.0, rgb[..., 1] / 255.0, rgb[..., 2] / 255.0

    r = np.where(r > 0.04045, ((r + 0.055) / 1.055) ** 2.4, r / 12.92)
    g = np.where(g > 0.04045, ((g + 0.055) / 1.055) ** 2.4, g / 12.92)
    b = np.where(b > 0.04045, ((b + 0.055) / 1.055) ** 2.4, b / 12.92)

    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041

    x /= 0.95047
    z /= 1.08883

    eps = 0.008856
    kappa = 903.3

    fx = np.where(x > eps, x ** (1/3), (kappa * x + 16) / 116)
    fy = np.where(y > eps, y ** (1/3), (kappa * y + 16) / 116)
    fz = np.where(z > eps, z ** (1/3), (kappa * z + 16) / 116)

    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b_val = 200 * (fy - fz)

    return np.stack([L, a, b_val], axis=-1)


def _lab_to_rgb(lab):
    L, a, b_val = lab[..., 0], lab[..., 1], lab[..., 2]

    fy = (L + 16) / 116
    fx = a / 500 + fy
    fz = fy - b_val / 200

    eps = 0.008856
    kappa = 903.3

    x = np.where(fx ** 3 > eps, fx ** 3, (116 * fx - 16) / kappa)
    y = np.where(L > kappa * eps, ((L + 16) / 116) ** 3, L / kappa)
    z = np.where(fz ** 3 > eps, fz ** 3, (116 * fz - 16) / kappa)

    x *= 0.95047
    z *= 1.08883

    r = x * 3.2404542 - y * 1.5371385 - z * 0.4985314
    g = -x * 0.9692660 + y * 1.8760108 + z * 0.0415560
    b = x * 0.0556434 - y * 0.2040259 + z * 1.0572252

    r = np.where(r > 0.0031308, 1.055 * r ** (1/2.4) - 0.055, 12.92 * r)
    g = np.where(g > 0.0031308, 1.055 * g ** (1/2.4) - 0.055, 12.92 * g)
    b = np.where(b > 0.0031308, 1.055 * b ** (1/2.4) - 0.055, 12.92 * b)

    rgb = np.stack([r, g, b], axis=-1)
    return np.clip(rgb * 255, 0, 255).astype(np.uint8)


def _kmeans_colors(pixels, k=7, max_iter=20):
    rng = np.random.RandomState(42)
    indices = rng.choice(len(pixels), size=min(k, len(pixels)), replace=False)
    centroids = pixels[indices].copy()

    for _ in range(max_iter):
        dists = np.linalg.norm(pixels[:, np.newaxis] - centroids[np.newaxis, :], axis=2)
        labels = np.argmin(dists, axis=1)
        new_centroids = np.zeros_like(centroids)
        for i in range(k):
            mask = labels == i
            if mask.any():
                new_centroids[i] = pixels[mask].mean(axis=0)
            else:
                new_centroids[i] = centroids[i]
        if np.allclose(centroids, new_centroids, atol=0.5):
            break
        centroids = new_centroids

    dists = np.linalg.norm(pixels[:, np.newaxis] - centroids[np.newaxis, :], axis=2)
    labels = np.argmin(dists, axis=1)
    counts = np.bincount(labels, minlength=k)
    order = np.argsort(-counts)

    return centroids[order], counts[order] / counts.sum()


def extract_palette(img_array, k=7):
    h, w = img_array.shape[:2]
    small = img_array[::max(1, h//64), ::max(1, w//64)]
    pixels = small.reshape(-1, 3).astype(np.float64)

    lab_pixels = _rgb_to_lab(pixels.reshape(-1, 1, 3)).reshape(-1, 3)
    centroids_lab, weights = _kmeans_colors(lab_pixels, k=k)
    centroids_rgb = _lab_to_rgb(centroids_lab.reshape(-1, 1, 3)).reshape(-1, 3)

    palette = []
    for i in range(len(centroids_rgb)):
        r, g, b = int(centroids_rgb[i][0]), int(centroids_rgb[i][1]), int(centroids_rgb[i][2])
        L = float(centroids_lab[i][0])
        palette.append({
            "rgb": [r, g, b],
            "weight": float(weights[i]),
            "luminance": L,
        })

    return palette


def extract_color_temperature(img_array):
    pixels = img_array.reshape(-1, 3).astype(np.float64)
    r_mean, g_mean, b_mean = pixels[:, 0].mean(), pixels[:, 1].mean(), pixels[:, 2].mean()

    warmth = (r_mean - b_mean) / 255.0
    temp_estimate = 6500 + warmth * -3000

    warm_pixels = (pixels[:, 0] > pixels[:, 2] + 30).sum()
    cool_pixels = (pixels[:, 2] > pixels[:, 0] + 30).sum()
    neutral = len(pixels) - warm_pixels - cool_pixels

    return {
        "estimated_kelvin": float(np.clip(temp_estimate, 2000, 12000)),
        "warmth_bias": float(warmth),
        "warm_ratio": float(warm_pixels / len(pixels)),
        "cool_ratio": float(cool_pixels / len(pixels)),
        "neutral_ratio": float(neutral / len(pixels)),
    }


def extract_spatial_frequency(img_array):
    gray = np.mean(img_array.astype(np.float64), axis=2)
    h, w = gray.shape

    small_dim = min(h, w, 256)
    gray_small = gray[:small_dim, :small_dim]

    fft = np.fft.fft2(gray_small)
    fft_shift = np.fft.fftshift(fft)
    magnitude = np.log1p(np.abs(fft_shift))

    cy, cx = small_dim // 2, small_dim // 2
    y_grid, x_grid = np.mgrid[0:small_dim, 0:small_dim]
    radius = np.sqrt((x_grid - cx) ** 2 + (y_grid - cy) ** 2)

    bands = {
        "very_low": (0, small_dim * 0.05),
        "low": (small_dim * 0.05, small_dim * 0.15),
        "mid": (small_dim * 0.15, small_dim * 0.3),
        "high": (small_dim * 0.3, small_dim * 0.5),
    }

    energy = {}
    total = magnitude.sum()
    for name, (r_min, r_max) in bands.items():
        mask = (radius >= r_min) & (radius < r_max)
        energy[name] = float(magnitude[mask].sum() / (total + 1e-8))

    texture_complexity = energy.get("high", 0) / (energy.get("low", 0.01) + 1e-8)

    return {
        "frequency_bands": energy,
        "texture_complexity": float(np.clip(texture_complexity, 0, 10)),
        "dominant_scale": "fine" if texture_complexity > 1.5 else "coarse" if texture_complexity < 0.3 else "balanced",
    }


def extract_brightness_profile(img_array):
    gray = np.mean(img_array.astype(np.float64), axis=2) / 255.0
    h, w = gray.shape

    quadrants = {
        "top_left": gray[:h//2, :w//2],
        "top_right": gray[:h//2, w//2:],
        "bottom_left": gray[h//2:, :w//2],
        "bottom_right": gray[h//2:, w//2:],
        "center": gray[h//4:3*h//4, w//4:3*w//4],
    }

    profile = {}
    for name, region in quadrants.items():
        profile[name] = float(region.mean())

    histogram = np.histogram(gray, bins=10, range=(0, 1))[0]
    histogram = histogram / histogram.sum()

    dark_ratio = float(histogram[:3].sum())
    mid_ratio = float(histogram[3:7].sum())
    bright_ratio = float(histogram[7:].sum())

    contrast = float(gray.std())

    return {
        "quadrant_brightness": profile,
        "dark_ratio": dark_ratio,
        "mid_ratio": mid_ratio,
        "bright_ratio": bright_ratio,
        "contrast": contrast,
        "mean_brightness": float(gray.mean()),
        "dynamic_range": float(gray.max() - gray.min()),
    }


def extract_composition(img_array):
    gray = np.mean(img_array.astype(np.float64), axis=2)
    h, w = gray.shape

    from scipy import ndimage as ndi
    smooth = ndi.gaussian_filter(gray, sigma=min(h, w) * 0.05)

    bright_mask = smooth > np.percentile(smooth, 75)
    dark_mask = smooth < np.percentile(smooth, 25)

    if bright_mask.any():
        y_grid, x_grid = np.mgrid[0:h, 0:w]
        bright_cy = float(y_grid[bright_mask].mean() / h)
        bright_cx = float(x_grid[bright_mask].mean() / w)
    else:
        bright_cy, bright_cx = 0.5, 0.5

    if dark_mask.any():
        y_grid, x_grid = np.mgrid[0:h, 0:w]
        dark_cy = float(y_grid[dark_mask].mean() / h)
        dark_cx = float(x_grid[dark_mask].mean() / w)
    else:
        dark_cy, dark_cx = 0.5, 0.5

    edges = ndi.sobel(smooth)
    edges = edges / (edges.max() + 1e-8)
    edge_density = float((edges > 0.3).mean())

    return {
        "bright_center": [bright_cx, bright_cy],
        "dark_center": [dark_cx, dark_cy],
        "edge_density": edge_density,
        "composition_type": _classify_composition(bright_cx, bright_cy, edge_density),
    }


def _classify_composition(cx, cy, edge_density):
    center_dist = math.sqrt((cx - 0.5) ** 2 + (cy - 0.5) ** 2)
    if center_dist < 0.15:
        return "centered"
    elif cx < 0.35 or cx > 0.65:
        return "asymmetric"
    elif edge_density > 0.15:
        return "complex"
    else:
        return "balanced"


def extract_color_harmony(palette):
    if len(palette) < 2:
        return {"type": "monochrome", "spread": 0}

    rgbs = [p["rgb"] for p in palette[:5]]
    hues = []
    for r, g, b in rgbs:
        r_, g_, b_ = r / 255, g / 255, b / 255
        cmax = max(r_, g_, b_)
        cmin = min(r_, g_, b_)
        delta = cmax - cmin
        if delta < 0.01:
            hues.append(0)
        elif cmax == r_:
            hues.append(((g_ - b_) / delta) % 6 * 60)
        elif cmax == g_:
            hues.append(((b_ - r_) / delta + 2) * 60)
        else:
            hues.append(((r_ - g_) / delta + 4) * 60)

    hue_diffs = []
    for i in range(len(hues)):
        for j in range(i + 1, len(hues)):
            diff = abs(hues[i] - hues[j])
            diff = min(diff, 360 - diff)
            hue_diffs.append(diff)

    avg_diff = np.mean(hue_diffs)
    max_diff = max(hue_diffs)

    if max_diff < 30:
        harmony_type = "monochromatic"
    elif 25 < avg_diff < 50:
        harmony_type = "analogous"
    elif 140 < max_diff < 200:
        harmony_type = "complementary"
    elif 100 < max_diff < 150:
        harmony_type = "triadic"
    else:
        harmony_type = "varied"

    return {
        "type": harmony_type,
        "hue_spread": float(max_diff),
        "dominant_hues": [float(h) for h in hues],
    }


def analyze_image(img_bytes=None, img_path=None, img_array=None):
    if img_array is not None:
        arr = img_array
    elif img_bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        arr = np.array(img)
    elif img_path:
        img = Image.open(img_path).convert("RGB")
        arr = np.array(img)
    else:
        return {"error": "No image provided"}

    max_dim = 256
    h, w = arr.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        new_h, new_w = int(h * scale), int(w * scale)
        img_resized = Image.fromarray(arr).resize((new_w, new_h), Image.LANCZOS)
        arr = np.array(img_resized)

    palette = extract_palette(arr)
    temperature = extract_color_temperature(arr)
    frequency = extract_spatial_frequency(arr)
    brightness = extract_brightness_profile(arr)
    composition = extract_composition(arr)
    harmony = extract_color_harmony(palette)

    fingerprint = hashlib.md5(arr.tobytes()[:4096]).hexdigest()[:12]

    return {
        "fingerprint": fingerprint,
        "dimensions": [int(w), int(h)],
        "palette": palette,
        "color_temperature": temperature,
        "spatial_frequency": frequency,
        "brightness_profile": brightness,
        "composition": composition,
        "color_harmony": harmony,
        "analyzed_at": datetime.now().isoformat(),
    }


class VisualMemory:
    def __init__(self, state_file=None):
        self.state_file = Path(state_file) if state_file else VISUAL_STATE_FILE
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load()

    def _load(self):
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "learned_images": 0,
            "palette_library": [],
            "avg_temperature": {"kelvin": 6500, "warmth": 0.0},
            "texture_preferences": {"fine": 0, "coarse": 0, "balanced": 0},
            "composition_preferences": {"centered": 0, "asymmetric": 0, "complex": 0, "balanced": 0},
            "harmony_preferences": defaultdict(int),
            "brightness_stats": {"dark": 0, "mid": 0, "bright": 0},
            "learned_palettes": [],
            "visual_concepts": {},
            "history": [],
        }

    def save(self):
        state_copy = self.state.copy()
        if isinstance(state_copy.get("harmony_preferences"), defaultdict):
            state_copy["harmony_preferences"] = dict(state_copy["harmony_preferences"])
        with open(self.state_file, 'w') as f:
            json.dump(state_copy, f, indent=2)

    def learn_from_analysis(self, analysis, label=""):
        self.state["learned_images"] += 1

        palette = analysis.get("palette", [])
        if palette:
            palette_entry = {
                "colors": [p["rgb"] for p in palette[:5]],
                "weights": [p["weight"] for p in palette[:5]],
                "label": label,
                "temperature": analysis.get("color_temperature", {}).get("estimated_kelvin", 6500),
            }
            self.state["learned_palettes"].append(palette_entry)
            if len(self.state["learned_palettes"]) > 100:
                self.state["learned_palettes"] = self.state["learned_palettes"][-100:]

        temp = analysis.get("color_temperature", {})
        n = self.state["learned_images"]
        old_k = self.state["avg_temperature"]["kelvin"]
        new_k = temp.get("estimated_kelvin", 6500)
        self.state["avg_temperature"]["kelvin"] = old_k + (new_k - old_k) / n
        old_w = self.state["avg_temperature"]["warmth"]
        new_w = temp.get("warmth_bias", 0)
        self.state["avg_temperature"]["warmth"] = old_w + (new_w - old_w) / n

        freq = analysis.get("spatial_frequency", {})
        scale = freq.get("dominant_scale", "balanced")
        if scale in self.state["texture_preferences"]:
            self.state["texture_preferences"][scale] += 1

        comp = analysis.get("composition", {})
        comp_type = comp.get("composition_type", "balanced")
        if comp_type in self.state["composition_preferences"]:
            self.state["composition_preferences"][comp_type] += 1

        harmony = analysis.get("color_harmony", {})
        h_type = harmony.get("type", "varied")
        if not isinstance(self.state["harmony_preferences"], dict):
            self.state["harmony_preferences"] = {}
        self.state["harmony_preferences"][h_type] = self.state["harmony_preferences"].get(h_type, 0) + 1

        bright = analysis.get("brightness_profile", {})
        if bright.get("dark_ratio", 0) > 0.5:
            self.state["brightness_stats"]["dark"] += 1
        elif bright.get("bright_ratio", 0) > 0.3:
            self.state["brightness_stats"]["bright"] += 1
        else:
            self.state["brightness_stats"]["mid"] += 1

        if label:
            words = label.lower().split()
            for word in words:
                word = word.strip(".,!?-_")
                if len(word) > 2:
                    if word not in self.state["visual_concepts"]:
                        self.state["visual_concepts"][word] = {
                            "count": 0,
                            "avg_palette": None,
                            "avg_warmth": 0,
                            "avg_complexity": 0,
                        }
                    vc = self.state["visual_concepts"][word]
                    vc["count"] += 1
                    vc["avg_warmth"] += (temp.get("warmth_bias", 0) - vc["avg_warmth"]) / vc["count"]
                    vc["avg_complexity"] += (freq.get("texture_complexity", 1) - vc["avg_complexity"]) / vc["count"]
                    if palette and vc["avg_palette"] is None:
                        vc["avg_palette"] = palette[0]["rgb"]

        self.state["history"].append({
            "fingerprint": analysis.get("fingerprint", ""),
            "label": label,
            "timestamp": analysis.get("analyzed_at", ""),
        })
        if len(self.state["history"]) > 200:
            self.state["history"] = self.state["history"][-200:]

        self.save()

        return {
            "total_images_learned": self.state["learned_images"],
            "palettes_stored": len(self.state["learned_palettes"]),
            "visual_concepts": len(self.state["visual_concepts"]),
            "texture_preference": max(self.state["texture_preferences"], key=self.state["texture_preferences"].get),
            "avg_temperature": self.state["avg_temperature"],
        }

    def get_learned_palette_for_prompt(self, prompt):
        words = prompt.lower().split()
        best_match = None
        best_score = 0

        for word in words:
            word = word.strip(".,!?-_")
            if word in self.state.get("visual_concepts", {}):
                vc = self.state["visual_concepts"][word]
                if vc["count"] > best_score:
                    best_score = vc["count"]
                    best_match = word

        if best_match and self.state.get("learned_palettes"):
            for pal in reversed(self.state["learned_palettes"]):
                label_words = pal.get("label", "").lower().split()
                if best_match in label_words:
                    return pal["colors"]

        if self.state.get("learned_palettes"):
            return self.state["learned_palettes"][-1]["colors"]

        return None

    def get_stats(self):
        return {
            "total_images_learned": self.state.get("learned_images", 0),
            "palettes_stored": len(self.state.get("learned_palettes", [])),
            "visual_concepts": len(self.state.get("visual_concepts", {})),
            "texture_preferences": self.state.get("texture_preferences", {}),
            "composition_preferences": self.state.get("composition_preferences", {}),
            "brightness_stats": self.state.get("brightness_stats", {}),
            "avg_temperature": self.state.get("avg_temperature", {}),
            "harmony_preferences": dict(self.state.get("harmony_preferences", {})),
            "top_concepts": sorted(
                [(k, v["count"]) for k, v in self.state.get("visual_concepts", {}).items()],
                key=lambda x: -x[1]
            )[:20],
        }
