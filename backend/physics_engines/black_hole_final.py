"""
🕳️ FINAL BLACK HOLE RENDERER - High Quality / Reasonable Speed
Aims for EHT/JWST visual quality with optimized numpy.
"""

import numpy as np
import math
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance


class FinalBlackHoleRenderer:
    """The best pure-Python black hole renderer."""
    
    RS = 100.0  # Schwarzschild radius in pixels
    PHOTON_SPHERE = 1.5 * RS
    
    def __init__(self, seed: Optional[int] = None):
        self.rng = np.random.RandomState(seed)
    
    def _temperature_color(self, T: float) -> Tuple[int, int, int]:
        """Blackbody approximation: T=1 (hottest, white-blue) to T=0 (red)."""
        if T > 0.95:
            return (255, 255, 240)
        elif T > 0.8:
            return (255, 255, 200)
        elif T > 0.6:
            return (255, 200, 100)
        elif T > 0.3:
            return (255, 100, 50)
        elif T > 0.1:
            return (200, 50, 20)
        else:
            return (50, 10, 0)
    
    def render(self, width: int, height: int, complexity: float = 1.0,
               mass: float = 50.0, inclination: float = 0.0) -> Image.Image:
        """
        Render a high-quality black hole.
        """
        # Fast path
        if width < 64 or height < 64:
            return self._simple(width, height)
        
        w, h = width, height
        cx, cy = w // 2, h // 2
        scale = min(w, h) * 0.4 / self.RS
        
        # Create image array
        img = np.zeros((h, w, 3), dtype=np.uint8)
        img[:] = (5, 5, 12)  # Dark space
        
        # 1. Star field (more at higher complexity)
        num_stars = int(100 + 500 * complexity)
        self._draw_stars(img, cx, cy, scale, num_stars)
        
        # 2. Gravitational lensing: warp star field
        if complexity > 0.3:
            self._lens_stars(img, cx, cy, scale, complexity)
        
        # 3. Accretion disk (high detail)
        if complexity > 0.2:
            self._accretion_disk(img, cx, cy, scale, complexity, inclination)
        
        # 4. Photon ring
        if complexity > 0.4:
            self._photon_ring(img, cx, cy, scale)
        
        # 5. Jets
        if complexity > 0.6:
            self._jets(img, cx, cy, scale)
        
        # 6. Event horizon
        self._event_horizon(img, cx, cy, scale)
        
        # 7. Convert to PIL and enhance
        pil = Image.fromarray(img, 'RGB')
        
        # Post-processing
        if complexity > 0.5:
            # Sharpen
            pil = pil.filter(ImageFilter.UnsharpMask(radius=1, percent=100, threshold=3))
            # Enhance color saturation
            enhancer = ImageEnhance.Color(pil)
            #increase saturation by 30% for more vivid colors
            pil = enhancer.enhance(1.3)
            # Slight brightness boost
            enhancer = ImageEnhance.Brightness(pil)
            pil = enhancer.enhance(1.1)
        
        return pil
    
    def _simple(self, w: int, h: int) -> Image.Image:
        img = Image.new('RGB', (w, h), (0, 0, 0))
        d = ImageDraw.Draw(img)
        cx, cy = w//2, h//2
        r = min(w, h)//2 - 1
        d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(0,0,0))
        d.ellipse([cx-r+1, cy-r+1, cx+r-1, cy+r-1], outline=(255,255,200), width=1)
        return img
    
    def _draw_stars(self, img: np.ndarray, cx: int, cy: int, scale: float, num: int):
        h, w = img.shape[:2]
        stars = self.rng.randint(0, [w, h], size=(num, 2))
        # Filter
        dists = np.linalg.norm(stars - [cx, cy], axis=1)
        stars = stars[dists > self.RS*scale*2.5]
        if len(stars) == 0: return
        
        sizes = self.rng.choice([1, 1, 1, 2, 2, 3], size=len(stars))
        brightness = self.rng.randint(180, 255, size=len(stars))
        for (x, y), sz, b in zip(stars, sizes, brightness):
            x0, x1 = max(0, x-sz), min(w-1, x+sz)
            y0, y1 = max(0, y-sz), min(h-1, y+sz)
            if x1 > x0 and y1 > y0:
                img[y0:y1+1, x0:x1+1] = (b, b, b)
    
    def _lens_stars(self, img: np.ndarray, cx: int, cy: int, scale: float, complexity: float):
        h, w = img.shape[:2]
        y, x = np.ogrid[:h, :w]
        dx = x - cx
        dy = y - cy
        r = np.sqrt(dx**2 + dy**2).astype(np.float32)
        
        # Lensing magnification near photon sphere
        rs_px = self.RS * scale
        mask = (r > rs_px) & (r < rs_px * 2.5)
        if np.any(mask):
            # Magnification factor
            r_masked = r[mask]
            factor = 1.0 + 50 * np.exp(-((r_masked - self.PHOTON_SPHERE*scale)**2) / (2 * (15*scale)**2))
            factor = factor[:, None]  # for broadcasting to 3 channels
            
            # Increase brightness
            brightened = np.clip(img[mask] * factor, 0, 255).astype(np.uint8)
            img[mask] = brightened
    
    def _accretion_disk(self, img: np.ndarray, cx: int, cy: int, scale: float,
                        complexity: float, inclination: float):
        h, w = img.shape[:2]
        cos_i = math.cos(inclination)
        inner = self.PHOTON_SPHERE * scale * 1.05
        outer = self.RS * scale * 7.0
        rings = int(10 + 15 * complexity)
        
        # Precompute y-grid
        y, x = np.ogrid[:h, :w]
        dx = x - cx
        dy = y - cy
        
        for i in range(rings):
            t = i / rings
            r = inner + (outer - inner) * t
            # Temperature T ∝ r^(-3/4)
            T = (inner / r)**0.75 if r > inner else 1.0
            col = self._temperature_color(T)
            
            # Disk thickness
            height_scale = max(0.08, 1.0 - t*0.88) * cos_i
            # Ellipse condition: (dx^2 / r^2) + (dy^2 / (r*height_scale)^2) ≈ 1
            a = r**2
            b = (r * height_scale)**2
            ell = (dx**2 / a + dy**2 / b)
            mask = (ell >= 0.98) & (ell <= 1.02)
            
            alpha = (T**4) * 0.85
            if np.any(mask):
                for c in range(3):
                    channel = img[:, :, c].astype(np.float32)
                    channel[mask] = np.clip(channel[mask] * (1-alpha) + col[c] * alpha, 0, 255)
                    img[:, :, c] = channel.astype(np.uint8)
    
    def _photon_ring(self, img: np.ndarray, cx: int, cy: int, scale: float):
        h, w = img.shape[:2]
        r = int(self.PHOTON_SPHERE * scale)
        y, x = np.ogrid[:h, :w]
        dist2 = (x - cx)**2 + (y - cy)**2
        mask = (dist2 <= (r+1)**2) & (dist2 >= (r-1)**2)
        img[mask] = np.clip(img[mask] + 50, 0, 255).astype(np.uint8)
    
    def _jets(self, img: np.ndarray, cx: int, cy: int, scale: float):
        """Draw simple jets as rectangles (skip complex numpy)."""
        h, w = img.shape[:2]
        jet_len = int(self.RS * scale * 2.5)
        jet_w = max(2, int(self.RS * scale * 0.04))
        color = np.array([120, 180, 255], dtype=np.uint8)
        
        # Top jet region
        y0 = cy - int(self.RS*scale) - jet_len
        y1 = cy - int(self.RS*scale)
        x0, x1 = cx - jet_w, cx + jet_w
        if y0 >= 0 and y1 < h and x0 >= 0 and x1 < w:
            # Simple gradient by rows
            for i, y in enumerate(range(y0, y1)):
                alpha = 0.7 - 0.5 * (i / jet_len)
                img[y, x0:x1] = np.clip(img[y, x0:x1] * (1-alpha) + color * alpha, 0, 255).astype(np.uint8)
        
        # Bottom jet
        y0b = cy + int(self.RS*scale)
        y1b = cy + int(self.RS*scale) + jet_len
        if y0b >= 0 and y1b < h and x0 >= 0 and x1 < w:
            for i, y in enumerate(range(y0b, y1b)):
                alpha = 0.7 - 0.5 * (i / jet_len)
                img[y, x0:x1] = np.clip(img[y, x0:x1] * (1-alpha) + color * alpha, 0, 255).astype(np.uint8)
    
    def _event_horizon(self, img: np.ndarray, cx: int, cy: int, scale: float):
        h, w = img.shape[:2]
        r = int(self.RS * scale)
        y, x = np.ogrid[:h, :w]
        mask = (x - cx)**2 + (y - cy)**2 <= r*r
        img[mask] = (0, 0, 0)
