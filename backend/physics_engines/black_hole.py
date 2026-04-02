"""
🕳️ BLACK HOLE RENDERER - Optimized
Simplified but still realistic black hole rendering.
"""

import math
import random
from typing import Tuple, Optional
from PIL import Image, ImageDraw


class BlackHoleRenderer:
    """High-quality but fast black hole renderer."""
    
    RS = 100.0  # Schwarzschild radius (pixel units)
    PHOTON_SPHERE = 150.0
    
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
    
    def render(self, width: int, height: int, complexity: float = 1.0, mass: float = 50.0, spin: float = 0.0) -> Image.Image:
        """Render a black hole."""
        # Fast path for tiny renders
        if width < 64 or height < 64:
            img = Image.new('RGB', (width, height), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            cx, cy = width // 2, height // 2
            r = min(width, height) // 2 - 1
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0))
            draw.ellipse([cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1], outline=(255, 255, 200), width=1)
            return img
        
        img = Image.new('RGB', (width, height), (8, 10, 16))
        draw = ImageDraw.Draw(img)
        cx, cy = width // 2, height // 2
        
        # Scale
        margin = min(width, height) * 0.4
        scale = margin / self.RS
        
        # Stars (limited)
        if complexity > 0.1:
            num_stars = min(150, int(20 + 150 * complexity))
            for _ in range(num_stars):
                sx = self.rng.randint(0, width)
                sy = self.rng.randint(0, height)
                if math.hypot(sx - cx, sy - cy) < self.RS * scale * 2:
                    continue
                r = self.rng.choice([1, 1, 1, 2])
                b = self.rng.randint(180, 255)
                draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(b, b, b))
        
        # Accretion disk
        if complexity > 0.2:
            inner = int(self.PHOTON_SPHERE * scale)
            outer = int(self.RS * scale * 7)
            rings = min(10, int(4 + 7 * complexity))
            
            for i in range(rings):
                t = i / rings
                r = int(inner + (outer - inner) * t)
                height_scale = max(0.15, 1.0 - t * 0.85)
                
                # Color gradient: white -> yellow -> orange -> red
                if t < 0.3:
                    color = (255, 255, int(200 + 55 * t/0.3))
                elif t < 0.6:
                    u = (t - 0.3) / 0.3
                    color = (255, int(200 + 55 * (1-u)), int(100 * u))
                else:
                    color = (int(255 * (1-t)), int(100 * (1-t)), 0)
                
                bbox = [cx - r, int(cy - r * height_scale), cx + r, int(cy + r * height_scale)]
                w = max(1, int(3 * (1 - t)))
                draw.ellipse(bbox, outline=color, width=w)
        
        # Photon sphere
        if complexity > 0.4:
            r = int(self.PHOTON_SPHERE * scale)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 200), width=2)
        
        # Lensing
        if complexity > 0.3:
            n_lens = min(40, int(15 + 25 * complexity))
            for _ in range(n_lens):
                angle = self.rng.random() * 2 * math.pi
                dist = self.RS * scale * self.rng.uniform(1.3, 2.5)
                sx = int(cx + math.cos(angle) * dist)
                sy = int(cy + math.sin(angle) * dist)
                size = self.rng.choice([1, 2])
                b = self.rng.randint(150, 255)
                draw.ellipse([sx - size, sy - size, sx + size, sy + size], fill=(b, b, b))
        
        # Jets
        if complexity > 0.6:
            jet_len = int(self.RS * scale * 2.0)
            jet_w = max(2, int(self.RS * scale * 0.04))
            # Top
            draw.ellipse([cx - jet_w, cy - int(self.RS * scale) - jet_len,
                         cx + jet_w, cy - int(self.RS * scale)], fill=(130, 180, 255))
            # Bottom
            draw.ellipse([cx - jet_w, cy + int(self.RS * scale),
                         cx + jet_w, cy + int(self.RS * scale) + jet_len], fill=(130, 180, 255))
        
        # Event horizon (on top)
        r = int(self.RS * scale)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0))
        
        return img
