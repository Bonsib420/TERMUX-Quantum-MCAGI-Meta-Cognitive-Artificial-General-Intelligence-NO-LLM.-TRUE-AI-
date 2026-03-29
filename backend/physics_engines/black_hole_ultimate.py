"""
🕳️ ULTIMATE BLACK HOLE RENDERER - Optimized
High-quality volumetric rendering with vectorized operations.
"""

import numpy as np
import math
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance


class UltimateBlackHoleRenderer:
    """Fast yet photorealistic black hole."""
    
    RS = 100.0  # Schwarzschild radius (pixels at scale)
    PHOTON_SPHERE = 1.5 * RS
    
    def __init__(self, seed: Optional[int] = None):
        self.rng = np.random.RandomState(seed)
    
    def _fast_blackbody(self, T: np.ndarray) -> np.ndarray:
        """
        Vectorized blackbody approximation. T ∈ [0,1] → RGB in [0,1].
        Uses analytic piecewise functions ( Tanner Helland ).
        """
        T_K = 1000.0 + T * 39000.0  # map to 1000-40000 K
        
        # Red channel
        R = np.where(T_K <= 6600,
                     255.0,
                     329.698727466 * np.exp(-0.043 * (T_K - 6600) / 255.0) - 0.040)
        # Green channel
        G = np.where(T_K <= 6600,
                     99.4708025861 * np.log(T_K / 1000.0) - 161.1195681661,
                     288.1221695283 * np.exp(-0.031 * (T_K - 6600) / 255.0) - 0.075)
        # Blue channel
        B = np.where(T_K <= 1900,
                     0.0,
                     np.where(T_K <= 6600,
                              138.5177312231 * np.log((T_K - 1000.0) / 4000.0) - 305.0447927307,
                              255.0))
        rgb = np.stack([R, G, B], axis=-1)
        rgb = np.clip(rgb, 0, 255)
        return (rgb / 255.0).astype(np.float32)
    
    def _fBM_noise(self, x: np.ndarray, y: np.ndarray, octaves: int = 6) -> np.ndarray:
        """Fractional Brownian Motion noise (vectorized)."""
        noise = np.zeros_like(x, dtype=np.float32)
        freq = 0.03
        amp = 1.0
        for o in range(octaves):
            xi = (x * freq).astype(int)
            yi = (y * freq).astype(int)
            h = (xi * 374761393 + yi * 668265263) & 0x7fffffff
            n = h.astype(np.float32) / 0x7fffffff
            noise += n * amp
            freq *= 2.0
            amp *= 0.5
        return noise
    
    def _deflection_angle(self, b_vals: np.ndarray) -> np.ndarray:
        """
        Strong-field deflection angle for multiple impact parameters.
        b_vals: array in Rs units.
        Returns array of angles in radians.
        """
        alpha = np.zeros_like(b_vals)
        # Weak field for large b
        weak = b_vals >= 3.0
        alpha[weak] = 4.0 / b_vals[weak]
        # Strong field for 1.5 < b < 3.0
        strong = (b_vals > 1.6) & (b_vals < 3.0)
        bc = 1.5 * math.sqrt(3)  # ~2.598
        b_strong = b_vals[strong]
        # For b > bc, use log formula; else near capture set 0
        mask = b_strong > bc
        if np.any(mask):
            alpha[strong][mask] = 2 * math.sqrt(3) * np.log(b_strong[mask] / bc - 1) + 2 * math.pi
        # b < 1.5 captured => alpha stays 0
        return alpha
    
    def _lens_coordinates(self, x: np.ndarray, y: np.ndarray, cx: int, cy: int, scale: float) -> Tuple[np.ndarray, np.ndarray]:
        """Apply gravitational lensing to compute source coordinates."""
        dx = x - cx
        dy = y - cy
        r = np.sqrt(dx**2 + dy**2)
        r_phys = r / scale  # in Rs units
        
        alpha_rad = np.zeros_like(r)
        mask = r_phys > 1.6
        if np.any(mask):
            b = r_phys[mask]
            alpha = self._deflection_angle(b)
            alpha_rad[mask] = alpha
        
        factor = np.where(r > 0, alpha_rad * self.RS / (r + 1e-10), 0)
        x_src = x + dx * factor * 0.5
        y_src = y + dy * factor * 0.5
        return x_src, y_src
    
    def _volumetric_disk(self, x: np.ndarray, y: np.ndarray, cx: int, cy: int, scale: float,
                         complexity: float, inclination: float) -> np.ndarray:
        """
        Volumetric accretion disk using vectorized operations.
        """
        h, w = y.shape[0], x.shape[1]
        L = np.zeros((h, w, 3), dtype=np.float32)
        
        cos_i = max(0.05, math.cos(inclination))
        dx = x - cx
        dy = y - cy
        # Project y to disk plane coordinate
        y_disk = dy / cos_i
        R = np.sqrt(dx**2 + y_disk**2)
        
        inner = self.PHOTON_SPHERE * 1.05 * scale
        outer = self.RS * scale * 8.0
        
        # Valid pixel mask (inside image bounds)
        valid = (x >= 0) & (x < w) & (y >= 0) & (y < h)
        
        annulus = (R >= inner) & (R <= outer) & valid
        if not np.any(annulus):
            return L
        
        # Extract radii for annulus pixels
        R_vals = R[annulus]
        xs = x[annulus]
        ys = y[annulus]
        
        # Temperature profile: T ∝ r^(-3/4)
        T_vals = (inner / R_vals)**0.75
        T_vals = np.clip(T_vals, 0.0, 1.0)
        
        # Turbulence noise
        noise = self._fBM_noise(xs, ys, octaves=6)
        alphas = (T_vals**3) * (0.85 + 0.3 * noise)
        alphas = np.clip(alphas, 0, 1)
        
        # Colors (vectorized)
        colors = self._fast_blackbody(T_vals)  # (N,3) float
        
        # Accumulate using alpha blending
        L[annulus] += alphas[:, None] * colors
        
        return L
    
    def _render_starfield(self, w: int, h: int, cx: int, cy: int, scale: float, complexity: float) -> np.ndarray:
        """Render background stars."""
        stars = np.zeros((h, w, 3), dtype=np.float32)
        num_stars = int(500 + 2000 * complexity)
        
        # Polar distribution
        angles = self.rng.uniform(0, 2*math.pi, num_stars)
        dists = np.sqrt(self.rng.uniform(0, 1, num_stars)) * max(w, h) * 0.7
        xs = cx + (dists * np.cos(angles)).astype(int)
        ys = cy + (dists * np.sin(angles)).astype(int)
        
        for i in range(num_stars):
            x, y = xs[i], ys[i]
            if 0 <= x < w and 0 <= y < h:
                brightness = int(min(255, 150 + 105 * self.rng.random()))
                size = 1 if brightness < 200 else 2
                stars[y-size:y+size+1, x-size:x+size+1] = brightness
        return stars
    
    def render(self, width: int, height: int, complexity: float = 1.0,
               mass: float = 50.0, inclination: float = 0.1) -> Image.Image:
        start = __import__('time').time()
        
        # Adaptive supersampling: 2x for moderate sizes to improve quality without too much cost
        max_dim = max(width, height)
        ss = 1
        if max_dim <= 800 and complexity > 0.7:
            ss = 2
        # For very large (1024+), keep ss=1 to maintain reasonable performance
        w_ss, h_ss = width * ss, height * ss
        cx_ss, cy_ss = w_ss // 2, h_ss // 2
        scale_ss = min(w_ss, h_ss) * 0.4 / self.RS
        
        # Coordinate grids
        y_ss, x_ss = np.ogrid[:h_ss, :w_ss]
        x_ss = x_ss.astype(np.float32)
        y_ss = y_ss.astype(np.float32)
        
        # Lensing
        x_src, y_src = self._lens_coordinates(x_ss, y_ss, cx_ss, cy_ss, scale_ss)
        
        # Background stars
        img = self._render_starfield(w_ss, h_ss, cx_ss, cy_ss, scale_ss, complexity)
        
        # Accretion disk
        img += self._volumetric_disk(x_src, y_src, cx_ss, cy_ss, scale_ss, complexity, inclination)
        
        # Photon ring
        r_ph = int(self.PHOTON_SPHERE * scale_ss)
        ph_mask = (x_src - cx_ss)**2 + (y_src - cy_ss)**2 <= (r_ph+2)**2
        img[ph_mask] = np.clip(img[ph_mask] + 120, 0, 255)
        
        # Event horizon
        r_eh = int(self.RS * scale_ss)
        eh_mask = (x_src - cx_ss)**2 + (y_src - cy_ss)**2 <= r_eh**2
        img[eh_mask] = (0, 0, 0)
        
        # Relativistic jets
        if complexity > 0.6 and inclination < 0.3:
            jet_len = int(self.RS * scale_ss * 3.0)
            jet_w = max(1, int(self.RS * scale_ss * 0.05))
            jet_col = np.array([180, 220, 255], dtype=np.float32)
            # Top
            y0 = cy_ss - int(self.RS*scale_ss) - jet_len
            y1 = cy_ss - int(self.RS*scale_ss)
            for yy in range(y0, y1):
                alpha = 0.75 - 0.65 * (yy - y0) / jet_len
                mask = (x_src >= cx_ss-jet_w) & (x_src <= cx_ss+jet_w) & (y_src == yy)
                if np.any(mask):
                    img[mask] = img[mask] * (1-alpha*0.4) + jet_col * alpha
            # Bottom
            y0b = cy_ss + int(self.RS*scale_ss)
            y1b = cy_ss + int(self.RS*scale_ss) + jet_len
            for yy in range(y0b, y1b):
                alpha = 0.75 - 0.65 * (yy - y0b) / jet_len
                mask = (x_src >= cx_ss-jet_w) & (x_src <= cx_ss+jet_w) & (y_src == yy)
                if np.any(mask):
                    img[mask] = img[mask] * (1-alpha*0.4) + jet_col * alpha
        
        # Convert and post-process
        img_u8 = np.clip(img, 0, 255).astype(np.uint8)
        pil = Image.fromarray(img_u8, 'RGB')
        
        if ss > 1:
            pil = pil.resize((width, height), Image.Resampling.LANCZOS)
        
        if complexity > 0.5:
            pil = pil.filter(ImageFilter.UnsharpMask(radius=1, percent=100, threshold=3))
            enhancer = ImageEnhance.Color(pil)
            pil = enhancer.enhance(1.25)
            enhancer = ImageEnhance.Contrast(pil)
            pil = enhancer.enhance(1.1)
            if complexity > 0.8:
                vign = Image.new('L', (width, height), 255)
                draw = ImageDraw.Draw(vign)
                cx_v, cy_v = width//2, height//2
                max_r = max(width, height) * 0.7
                for r in range(int(max_r), 0, -5):
                    alpha = int(255 * (1 - (r/max_r)**2))
                    draw.ellipse([cx_v-r, cy_v-r, cx_v+r, cy_v+r], fill=alpha)
                pil.putalpha(vign)
        
        elapsed = __import__('time').time() - start
        if elapsed > 1.0:
            print(f"[UltraBH] {width}x{height} c={complexity:.2f} t={elapsed:.2f}s")
        return pil
