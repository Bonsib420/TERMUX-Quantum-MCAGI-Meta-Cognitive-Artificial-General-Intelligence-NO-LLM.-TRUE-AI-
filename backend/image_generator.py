"""
🎨 HIGH-QUALITY COMPLEXITY-GRADIENT IMAGE GENERATOR
Generates professional-quality images from EASY to HARD.
Features antialiasing, smooth curves, and detailed rendering.
"""

import random
import math
import base64
from io import BytesIO
from typing import List, Tuple, Optional

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageChops
except ImportError:
    raise ImportError("Pillow is required: pip install pillow")


class HighQualityGenerator:
    """
    High-quality procedural image generator with smooth antialiasing.
    Complexity: 0.0 (stick figures) → 1.0 (black holes)
    """
    
    CONCEPT_PROFILES = {
        # EASIEST
        'stick figure': {'complexity': 0.05, 'colors': [(255, 255, 255), (220, 220, 220), (180, 180, 180)]},
        'simple': {'complexity': 0.1, 'colors': [(255, 255, 255), (220, 220, 220)]},
        'circle': {'complexity': 0.0, 'colors': [(255, 255, 255)]},
        'line': {'complexity': 0.0, 'colors': [(255, 255, 255)]},
        'basic': {'complexity': 0.1, 'colors': [(255, 255, 255)]},
        'figure': {'complexity': 0.15, 'colors': [(255, 255, 255)]},
        'human': {'complexity': 0.2, 'colors': [(255, 210, 160), (210, 160, 110)]},
        
        # MID
        'quantum': {'complexity': 0.5, 'colors': [(0, 255, 100), (255, 0, 255), (0, 150, 255)]},
        'wave': {'complexity': 0.4, 'colors': [(0, 191, 255), (30, 144, 255)]},
        'field': {'complexity': 0.45, 'colors': [(100, 149, 237), (72, 61, 139)]},
        'pattern': {'complexity': 0.35, 'colors': [(255, 105, 180), (138, 43, 226)]},
        'geometric': {'complexity': 0.3, 'colors': [(255, 255, 0), (0, 255, 255)]},
        'polygon': {'complexity': 0.25, 'colors': [(255, 165, 0), (0, 255, 0)]},
        
        # HARD
        'gravity': {'complexity': 0.9, 'colors': [(25, 25, 112), (72, 61, 139), (255, 215, 0)]},
        'accretion': {'complexity': 0.85, 'colors': [(255, 100, 0), (255, 165, 0), (255, 255, 0)]},
        'spacetime': {'complexity': 0.75, 'colors': [(100, 100, 255), (200, 200, 255)]},
        'warp': {'complexity': 0.7, 'colors': [(255, 0, 255), (100, 0, 100)]},
        
        # HARDEST
        'black hole': {'complexity': 1.0, 'colors': [(0, 0, 0), (10, 10, 10), (255, 255, 0), (255, 165, 0), (255, 0, 0)]},
        'event horizon': {'complexity': 0.98, 'colors': [(0, 0, 0), (10, 10, 10), (255, 255, 255)]},
        'singularity': {'complexity': 1.0, 'colors': [(0, 0, 0), (20, 20, 20), (40, 40, 40)]},
        'quantum gravity': {'complexity': 0.95, 'colors': [(0, 0, 0), (255, 0, 255), (128, 128, 128)]},
        'wormhole': {'complexity': 0.92, 'colors': [(75, 0, 130), (138, 43, 226), (255, 255, 255)]},
        
        'default': {'complexity': 0.3, 'colors': [(100, 150, 200), (150, 100, 200)]}
    }
    
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
    
    def _parse_prompt(self, text: str) -> dict:
        text_lower = text.lower()
        words = text_lower.replace(',', ' ').split()
        
        found_concepts = []
        complexity_values = []
        
        count = 1
        numbers = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
        for i, num in enumerate(numbers, 1):
            if num in words:
                count = i
                break
        for word in words:
            if word.isdigit():
                count = int(word)
                break
        
        for concept, profile in self.CONCEPT_PROFILES.items():
            if concept in text_lower or any(concept in w for w in words):
                found_concepts.append(concept)
                complexity_values.append(profile['complexity'])
        
        target_complexity = max(complexity_values) if complexity_values else 0.3
        
        colors = self.CONCEPT_PROFILES['default']['colors']
        if found_concepts:
            main_concept = max(found_concepts, key=lambda c: self.CONCEPT_PROFILES[c]['complexity'])
            colors = self.CONCEPT_PROFILES[main_concept]['colors']
        
        return {
            'concepts': found_concepts,
            'complexity': target_complexity,
            'colors': colors,
            'count': count
        }
    
    def _lerp(self, a: float, b: float, t: float) -> float:
        return a + (b - a) * t
    
    def _lerp_color(self, c1: Tuple, c2: Tuple, t: float) -> Tuple:
        return tuple(int(self._lerp(c1[i], c2[i], t)) for i in range(3))
    
    def _draw_antialiased_line(self, draw: ImageDraw.ImageDraw, p1: Tuple, p2: Tuple, color: Tuple, width: int):
        """Draw a smooth antialiased line."""
        # Draw multiple times with slight offsets for antialiasing
        for dx in [-0.5, 0, 0.5]:
            for dy in [-0.5, 0, 0.5]:
                adj_p1 = (p1[0] + dx, p1[1] + dy)
                adj_p2 = (p2[0] + dx, p2[1] + dy)
                draw.line([adj_p1, adj_p2], fill=color, width=width)
    
    def _draw_antialiased_ellipse(self, draw: ImageDraw.ImageDraw, bbox: List, color: Tuple, width: int = 0, fill: bool = False):
        """Draw smooth ellipse with antialiasing."""
        # enlarge slightly for antialiasing
        enlarged_bbox = [
            bbox[0] - 1, bbox[1] - 1,
            bbox[2] + 1, bbox[3] + 1
        ]
        if fill:
            draw.ellipse(enlarged_bbox, fill=color)
        else:
            draw.ellipse(enlarged_bbox, outline=color, width=width)
    
    def _draw_stick_figure(self, draw: ImageDraw.ImageDraw, x: int, y: int, size: int, color: Tuple, complexity: float):
        """Draw a high-quality stick figure with smooth lines."""
        head_radius = int(size * 0.28)
        body_length = int(size * 0.55)
        limb_width = max(2, int(4 * (1 - complexity) + 2))
        
        # NECK
        neck_y = y + head_radius + 2
        draw.line([(x, y + head_radius), (x, neck_y)], fill=color, width=limb_width)
        
        # SHOULDERS (slightly below neck)
        shoulder_y = neck_y + int(size * 0.05)
        shoulder_x_span = int(size * 0.35)
        
        # Shoulder joints (circles)
        shoulder_size = max(3, int(limb_width * 1.2))
        for sx in [x - shoulder_x_span, x + shoulder_x_span]:
            self._draw_antialiased_ellipse(draw, [sx - shoulder_size, shoulder_y - shoulder_size, sx + shoulder_size, shoulder_y + shoulder_size], color, fill=True)
        
        # ARMS (with elbows)
        elbow_y = shoulder_y + int(size * 0.12)
        arm_length = int(size * 0.3)
        
        for side in [-1, 1]:
            # Upper arm (shoulder to elbow)
            self._draw_antialiased_line(draw, 
                (x + side * shoulder_x_span, shoulder_y),
                (x + side * (shoulder_x_span + arm_length * 0.3), elbow_y),
                color, limb_width)
            
            # Lower arm (elbow to wrist)
            wrist_y = elbow_y + int(size * 0.1)
            wrist_x = x + side * (shoulder_x_span + arm_length)
            self._draw_antialiased_line(draw,
                (x + side * (shoulder_x_span + arm_length * 0.3), elbow_y),
                (wrist_x, wrist_y),
                color, limb_width)
            
            # Hand (small circle)
            hand_radius = max(3, int(limb_width))
            self._draw_antialiased_ellipse(draw, [wrist_x - hand_radius, wrist_y - hand_radius, wrist_x + hand_radius, wrist_y + hand_radius], color, fill=True)
        
        # TORSO (from shoulders to waist)
        torso_top = shoulder_y
        torso_bottom = shoulder_y + int(size * 0.25)
        self._draw_antialiased_line(draw, (x, torso_top), (x, torso_bottom), color, max(3, limb_width + 1))
        
        # HIPS (pelvis)
        hip_y = torso_bottom + 2
        hip_radius = int(size * 0.08)
        self._draw_antialiased_ellipse(draw, [x - hip_radius, hip_y - hip_radius, x + hip_radius, hip_y + hip_radius], color, fill=True)
        
        # LEGS (with knees)
        knee_y = hip_y + int(size * 0.2)
        ankle_y = hip_y + int(size * 0.35)
        foot_size = int(size * 0.1)
        
        for side in [-1, 1]:
            leg_outer_x = x + side * (hip_radius + 2)
            knee_x = leg_outer_x + side * int(size * 0.08)
            ankle_x = leg_outer_x + side * int(size * 0.05)
            
            # Upper leg
            self._draw_antialiased_line(draw,
                (leg_outer_x, hip_y),
                (knee_x, knee_y),
                color, limb_width)
            
            # Lower leg
            self._draw_antialiased_line(draw,
                (knee_x, knee_y),
                (ankle_x, ankle_y),
                color, limb_width)
            
            # Foot
            foot_bbox = [
                ankle_x + side * foot_size - (foot_size//2 if side == -1 else 0),
                ankle_y - foot_size//3,
                ankle_x + side * foot_size + (foot_size//2 if side == 1 else 0),
                ankle_y + foot_size//2
            ]
            self._draw_antialiased_ellipse(draw, foot_bbox, color, fill=True)
        
        # HEAD DETAILS
        # Face (simple)
        eye_offset = head_radius // 3
        eye_y = y - eye_offset
        for ex in [x - eye_offset, x + eye_offset]:
            eye_radius = max(2, head_radius // 6)
            self._draw_antialiased_ellipse(draw, [ex - eye_radius, eye_y - eye_radius, ex + eye_radius, eye_y + eye_radius], color, fill=True)
        
        # Mouth (smile)
        mouth_y = y + head_radius // 3
        smile_radius = head_radius // 2
        draw.arc([x - smile_radius, mouth_y - smile_radius//2, x + smile_radius, mouth_y + smile_radius//2], 200, 340, fill=color, width=max(1, limb_width//2))
    
    def _draw_black_hole(self, draw: ImageDraw.ImageDraw, x: int, y: int, size: int, color: Tuple, complexity: float, img: Image):
        """High-quality black hole with full physics."""
        w, h = img.size
        
        # EVENT HORIZON (perfect black circle)
        event_radius = size // 2
        draw.ellipse([x - event_radius, y - event_radius, x + event_radius, y + event_radius], fill=(0, 0, 0))
        
        # PHOTON SPHERE (bright thin ring)
        photon_radius = int(event_radius * 1.05)
        draw.ellipse([x - photon_radius, y - photon_radius, x + photon_radius, y + photon_radius], 
                    outline=(255, 255, 220), width=2)
        
        # ACCRETION DISK (3D elliptical rings with smooth gradients)
        disk_max_radius = int(size * 0.95)
        disk_min_radius = int(event_radius * 1.25)
        num_rings = 25
        
        for i in range(num_rings):
            t = i / num_rings
            radius = int(self._lerp(disk_min_radius, disk_max_radius, t**1.2))  # Quadratic for denser inner rings
            height_scale = max(0.05, 1.0 - t * 0.85)
            
            # Temperature gradient: white -> yellow -> orange -> red
            if t < 0.3:
                # Inner: white-blue hot
                disk_color = self._lerp_color((255, 255, 240), (255, 255, 150), t/0.3)
            elif t < 0.6:
                # Middle: yellow-orange
                disk_color = self._lerp_color((255, 255, 150), (255, 150, 0), (t-0.3)/0.3)
            else:
                # Outer: red
                disk_color = self._lerp_color((255, 150, 0), (180, 50, 0), (t-0.6)/0.4)
            
            bbox = [
                x - radius,
                int(y - radius * height_scale),
                x + radius,
                int(y + radius * height_scale)
            ]
            
            # Thinner rings outward
            ring_width = max(1, int(6 * (1 - t*0.7)))
            # Use multiple arcs for better antialiasing
            for angle_offset in [0, 1]:
                draw.arc(bbox, 0 + angle_offset, 360 - angle_offset, fill=disk_color, width=ring_width)
        
        # GRAVITATIONAL LENSING (light distortion)
        lens_radius = int(size * 1.6)
        num_lens_spots = 60
        
        for _ in range(num_lens_spots):
            angle = self.rng.random() * 2 * math.pi
            # Closer to black hole = more distorted (non-uniform distribution)
            dist_factor = self.rng.random() ** 0.7  # Clump near black hole
            dist = int(event_radius + dist_factor * (lens_radius - event_radius))
            
            sx = int(x + math.cos(angle) * dist)
            sy = int(y + math.sin(angle) * dist)
            
            brightness = int(150 + 105 * self.rng.random())
            dot_size = self.rng.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]
            
            # Soft glow around bright spots
            for r in range(dot_size + 2):
                alpha = max(0, 150 - r * 60)
                if alpha > 0:
                    draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(brightness, brightness, brightness, alpha))
        
        # RELATIVISTIC JETS
        jet_length = int(size * 3.0)
        jet_width = max(3, int(size * 0.06))
        jet_color_base = (130, 180, 255)
        
        # Top jet
        draw.ellipse([x - jet_width, y - event_radius - jet_length, 
                     x + jet_width, y - event_radius], 
                    fill=jet_color_base)
        # Bottom jet
        draw.ellipse([x - jet_width, y + event_radius, 
                     x + jet_width, y + event_radius + jet_length], 
                    fill=jet_color_base)
        
        # Jet particles
        num_jet_particles = 30
        for i in range(num_jet_particles):
            t = i / num_jet_particles
            # Top jet particle
            jet_y = y - event_radius - int(jet_length * t)
            jet_x_offset = self.rng.randint(-jet_width//3, jet_width//3)
            particle_size = max(2, int(5 * (1-t)))
            draw.ellipse([x + jet_x_offset - particle_size, jet_y - particle_size,
                         x + jet_x_offset + particle_size, jet_y + particle_size],
                        fill=(200, 220, 255))
            
            # Bottom jet particle
            jet_y = y + event_radius + int(jet_length * t)
            draw.ellipse([x + jet_x_offset - particle_size, jet_y - particle_size,
                         x + jet_x_offset + particle_size, jet_y + particle_size],
                        fill=(200, 220, 255))
    
    def _draw_stars(self, draw: ImageDraw.ImageDraw, w: int, h: int, complexity: float, color_main: Tuple):
        """Draw high-quality star field with varied brightness and size."""
        num_stars = int(100 + 400 * complexity)
        
        # Stars color varies: white, blue-ish, yellow-ish
        star_colors = [(255, 255, 255), (200, 220, 255), (255, 250, 200), (200, 255, 200)]
        
        for _ in range(num_stars):
            sx = self.rng.randint(0, w)
            sy = self.rng.randint(0, h)
            
            # Size distribution: most stars small, few large
            r = self.rng.choices([1, 1, 1, 2, 2, 3], weights=[0.5, 0.3, 0.1, 0.07, 0.03, 0.01])[0]
            r = max(1, r)
            
            # Brightness varies by size
            base_brightness = self.rng.randint(180, 255) if r > 1 else self.rng.randint(120, 200)
            
            # Slight color tint
            base_color = self.rng.choice(star_colors)
            color = tuple(min(255, int(base_color[i] * (base_brightness/255))) for i in range(3))
            
            # Draw star with soft glow if larger
            if r >= 2:
                # Outer glow
                glow_radius = r + 1
                glow_color = tuple(int(c * 0.3) for c in color)
                draw.ellipse([sx - glow_radius, sy - glow_radius, sx + glow_radius, sy + glow_radius], fill=glow_color)
            
            draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=color)
    
    def _apply_glow(self, img: Image, intensity: float = 0.3):
        """Apply a subtle bloom/glow effect."""
        # Create a blurred version
        glow = img.filter(ImageFilter.GaussianBlur(radius=3))
        # Blend with screen mode for glow
        return ImageChops.screen(img, glow)
    
    def _apply_noise(self, img: Image, intensity: float):
        """Add subtle film grain."""
        pixels = img.load()
        w, h = img.size
        noise_range = int(10 * intensity)
        
        for i in range(w):
            for j in range(h):
                if self.rng.random() < 0.15:  # 15% of pixels get noise
                    offset = self.rng.randint(-noise_range, noise_range)
                    r, g, b = pixels[i, j]
                    pixels[i, j] = (
                        max(0, min(255, r + offset)),
                        max(0, min(255, g + offset)),
                        max(0, min(255, b + offset))
                    )
    
    def generate(self, prompt: str, width: int = 512, height: int = 512) -> str:
        """
        Generate high-quality image at a single complexity level.
        """
        params = self._parse_prompt(prompt)
        complexity = params['complexity']
        colors = params['colors']
        count = params['count']
        
        # Seed for deterministic output
        seed_val = hash(prompt) % (2**32)
        self.rng.seed(seed_val)
        
        # Render at 2x resolution for quality, then downsample
        render_scale = 2.0 if complexity >= 0.6 else 1.0
        render_w = int(width * render_scale)
        render_h = int(height * render_scale)
        
        # Create image with deep space background
        bg_color = (8, 10, 18) if complexity > 0.3 else (12, 15, 25)
        img = Image.new('RGB', (render_w, render_h), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Draw detailed star field
        if complexity > 0.1:
            self._draw_stars(draw, render_w, render_h, complexity, colors[0])
        
        # Determine what to draw
        draw_black_holes = any(c in ['black hole', 'singularity', 'gravity', 'event horizon', 'accretion', 'wormhole'] 
                              for c in params['concepts'])
        draw_stick_figures = any(c in ['stick figure', 'simple', 'basic', 'figure', 'human', 'circle', 'line'] 
                                for c in params['concepts'])
        
        if not draw_black_holes and not draw_stick_figures:
            if complexity < 0.4:
                draw_stick_figures = True
            else:
                draw_black_holes = True
        
        # Calculate positions
        positions = []
        if count == 1:
            positions = [(render_w // 2, render_h // 2)]
        else:
            margin = render_w // (count + 1)
            for i in range(count):
                x = margin * (i + 1)
                y = render_h // 2 + self.rng.randint(-render_h//10, render_h//10)
                positions.append((x, y))
        
        # Scale for drawing
        scale_factor = render_scale
        
        # Draw objects
        for x, y in positions:
            if draw_stick_figures:
                self._draw_stick_figure(draw, x, y, 
                                      size=int(80 * scale_factor),
                                      color=self.rng.choice(colors),
                                      complexity=complexity)
            if draw_black_holes:
                self._draw_black_hole(draw, x, y,
                                     size=int(120 * scale_factor),
                                     color=self.rng.choice(colors),
                                     complexity=complexity,
                                     img=img)
        
        # Post-processing
        if complexity > 0.5:
            img = self._apply_glow(img, intensity=0.2 + 0.3 * complexity)
        
        if complexity > 0.7:
            self._apply_noise(img, intensity=0.05)
        
        # Downsample if we rendered at high res
        if render_scale > 1.0:
            img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # Final color correction (subtle saturation boost for vibrant colors)
        if complexity > 0.3:
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.1 + 0.2 * complexity)
        
        # Encode with high quality
        buffered = BytesIO()
        img.save(buffered, format="PNG", quality=95, optimize=True)
        img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{img_b64}"


# Singleton
_generator = None

def get_quantum_image_generator(seed: Optional[int] = None) -> HighQualityGenerator:
    global _generator
    if _generator is None:
        _generator = HighQualityGenerator(seed)
    return _generator
