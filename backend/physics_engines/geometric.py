"""
🔷 GEOMETRIC SHAPES ENGINE
Renders basic geometric primitives with clean antialiased rendering.
Handles circles, lines, polygons, patterns, waves, fields.
"""

import math
import random
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw


class GeometricRenderer:
    """
    High-quality renderer for basic geometric shapes and patterns.
    Complexity 0.0 (simple circle) to 0.4 (complex patterns).
    """
    
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
    
    def draw_antialiased_line(self, draw: ImageDraw.ImageDraw, p1: Tuple[int, int], p2: Tuple[int, int], color: Tuple[int, int, int], width: int = 2):
        """Draw a smooth line with antialiasing."""
        for dx in (-0.5, 0, 0.5):
            for dy in (-0.5, 0, 0.5):
                adj_p1 = (p1[0] + dx, p1[1] + dy)
                adj_p2 = (p2[0] + dx, p2[1] + dy)
                draw.line([adj_p1, adj_p2], fill=color, width=width)
    
    def draw_circle(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int, color: Tuple[int, int, int], fill: bool = False, line_width: int = 2):
        """Draw a smooth circle."""
        r_adj = radius + 0.5
        bbox = [cx - r_adj, cy - r_adj, cx + r_adj, cy + r_adj]
        if fill:
            draw.ellipse(bbox, fill=color)
        else:
            draw.ellipse(bbox, outline=color, width=line_width)
    
    def draw_wave_pattern(self, draw: ImageDraw.ImageDraw, w: int, h: int, complexity: float, colors: List[Tuple[int, int, int]], seed: str):
        """
        Draw wavelike interference patterns.
        Complexity controls number of waves, amplitude, frequency.
        """
        num_waves = int(3 + 7 * complexity)
        
        for wave_idx in range(num_waves):
            color = colors[wave_idx % len(colors)]
            phase = hash(seed + str(wave_idx)) % 360
            amplitude = h // (6 + int(8 * self.rng.random() * (1 - complexity)))
            freq = 0.01 + self.rng.random() * 0.04 * (1 + complexity)
            
            points = []
            for x in range(0, w, 2):
                y = h // 2 + int(amplitude * math.sin(x * freq + phase * math.pi/180 + wave_idx))
                points.append((x, y))
            
            if len(points) > 1:
                for i in range(len(points) - 1):
                    self.draw_antialiased_line(draw, points[i], points[i+1], color, width=max(1, int(3 * (1-complexity) + 1)))
    
    def draw_field_grid(self, draw: ImageDraw.ImageDraw, w: int, h: int, complexity: float, colors: List[Tuple[int, int, int]]):
        """
        Draw a field of vectors/arrows representing a field (electric, magnetic, quantum).
        """
        spacing = int(20 + 30 * (1 - complexity))  # denser at higher complexity
        arrow_length = int(8 + 12 * complexity)
        
        for x in range(spacing, w, spacing):
            for y in range(spacing, h, spacing):
                # Determine arrow direction based on position (pseudo-random but deterministic)
                angle = (x * 0.01 + y * 0.01) % (2 * math.pi)
                end_x = x + int(arrow_length * math.cos(angle))
                end_y = y + int(arrow_length * math.sin(angle))
                
                color = colors[self.rng.randint(0, len(colors)-1)]
                self.draw_antialiased_line(draw, (x, y), (end_x, end_y), color, width=2)
                
                # Arrow head
                head_size = 3
                draw.line([(end_x, end_y), 
                          (end_x - head_size * math.cos(angle - math.pi/6), 
                           end_y - head_size * math.sin(angle - math.pi/6))], fill=color, width=1)
                draw.line([(end_x, end_y),
                          (end_x - head_size * math.cos(angle + math.pi/6),
                           end_y - head_size * math.sin(angle + math.pi/6))], fill=color, width=1)
    
    def draw_geometric_pattern(self, draw: ImageDraw.ImageDraw, w: int, h: int, complexity: float, colors: List[Tuple[int, int, int]]):
        """
        Draw a repeating geometric pattern (mandala-inspired, fractal-ish).
        """
        center_x, center_y = w // 2, h // 2
        num_symmetries = int(6 + 6 * complexity)  # 6-fold to 12-fold symmetry
        
        # Radius based on canvas size
        max_r = min(w, h) // 2 - 10
        
        # Number of concentric rings
        num_rings = int(3 + 7 * complexity)
        
        for ring in range(num_rings):
            r = int((ring + 1) * max_r / num_rings)
            
            # Draw ring with geometric shapes
            points_per_ring = int(num_symmetries * (1 + ring * 0.5))
            
            for i in range(points_per_ring):
                angle = 2 * math.pi * i / points_per_ring
                x = center_x + int(r * math.cos(angle))
                y = center_y + int(r * math.sin(angle))
                
                # Size of shape increases with ring
                shape_size = max(2, int(3 + 3 * complexity * (ring / num_rings)))
                color = colors[ring % len(colors)]
                
                # Draw shape
                if complexity < 0.3:
                    # Simple dots
                    self.draw_circle(draw, x, y, shape_size, color, fill=True)
                else:
                    # Small polygons
                    self.draw_antialiased_line(draw,
                        (x, y - shape_size),
                        (x + int(shape_size * 0.866), y + int(shape_size * 0.5)),
                        color, width=2)
                    self.draw_antialiased_line(draw,
                        (x + int(shape_size * 0.866), y + int(shape_size * 0.5)),
                        (x - int(shape_size * 0.866), y + int(shape_size * 0.5)),
                        color, width=2)
                    self.draw_antialiased_line(draw,
                        (x - int(shape_size * 0.866), y + int(shape_size * 0.5)),
                        (x, y - shape_size),
                        color, width=2)
                
                # Connect to next point in ring for higher complexity
                if complexity > 0.5 and ring > 0:
                    next_angle = 2 * math.pi * ((i+1) % points_per_ring) / points_per_ring
                    next_x = center_x + int(r * math.cos(next_angle))
                    next_y = center_y + int(r * math.sin(next_angle))
                    self.draw_antialiased_line(draw, (x, y), (next_x, next_y), 
                                              tuple(c//2 for c in color), width=1)
        
        # Connect center to rings
        if complexity > 0.4:
            for r in [max_r // 4, max_r // 2, max_r * 3 // 4]:
                self.draw_circle(draw, center_x, center_y, r, colors[0], fill=False, line_width=1)
    
    def draw_polygon(self, draw: ImageDraw.ImageDraw, vertices: List[Tuple[int, int]], color: Tuple[int, int, int], fill: bool = False):
        """Draw a smooth polygon."""
        if len(vertices) < 3:
            return
        # Draw edges with antialiasing
        for i in range(len(vertices)):
            p1 = vertices[i]
            p2 = vertices[(i+1) % len(vertices)]
            self.draw_antialiased_line(draw, p1, p2, color, width=2)
        if fill:
            draw.polygon(vertices, fill=color)
    
    def draw_starfield(self, draw: ImageDraw.ImageDraw, w: int, h: int, density: float):
        """Draw a simple starfield."""
        num_stars = int(w * h * density * 0.01)
        for _ in range(num_stars):
            x = self.rng.randint(0, w)
            y = self.rng.randint(0, h)
            r = self.rng.choices([1, 1, 2], weights=[0.7, 0.2, 0.1])[0]
            brightness = self.rng.randint(150, 255)
            draw.ellipse([x-r, y-r, x+r, y+r], fill=(brightness, brightness, brightness))
