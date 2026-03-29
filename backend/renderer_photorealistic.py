"""
🌟 PHOTOREALISTIC COGNITIVE RENDERER
Uses the new high-quality physics engines.
"""

import math
import random
import numpy as np
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

from concept_ontology import get_ontology, ConceptDefinition, RenderingStrategy
from physics_engines.black_hole_photorealistic import PhotorealisticBlackHole
from physics_engines.human_figure import HumanFigureRenderer
from physics_engines.geometric import GeometricRenderer


class PhotorealisticRenderer:
    """High-quality renderer with realistic black holes."""
    
    def __init__(self, seed: Optional[int] = None):
        self.ontology = get_ontology()
        self.seed = seed if seed is not None else 12345
        self.rng = random.Random(self.seed)
        
        # Engines
        self.black_hole_engine = PhotorealisticBlackHole(seed=self.seed)
        self.human_engine = HumanFigureRenderer(seed=self.seed)
        self.geo_engine = GeometricRenderer(seed=self.seed)
        
        self.engines = {
            RenderingStrategy.BLACK_HOLE: self.black_hole_engine,
            RenderingStrategy.HUMAN_FIGURE: self.human_engine,
            RenderingStrategy.GEOMETRIC: self.geo_engine,
        }
    
    def _parse_concepts(self, prompt: str) -> List[Dict[str, Any]]:
        words = prompt.lower().replace(',', ' ').split()
        count = 1
        numbers = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
        for i, num in enumerate(numbers, 1):
            if num in words: count = i; break
        for word in words:
            if word.isdigit(): count = int(word); break
        
        concepts = []
        for name in self.ontology.list_concepts():
            if name in prompt.lower():
                defn = self.ontology.get_concept(name)
                if defn:
                    concepts.append({'name': name, 'def': defn, 'count': count})
        
        if not concepts:
            default = self.ontology.get_concept('default')
            if default:
                concepts.append({'name': 'default', 'def': default, 'count': count})
            else:
                # Fallback black hole
                from concept_ontology import ConceptDefinition, RenderingStrategy
                fallback = ConceptDefinition(
                    name='black_hole', category='astronomical', base_complexity=1.0,
                    strategy=RenderingStrategy.BLACK_HOLE,
                    visual_properties={'color_palette': [(255,255,255)]},
                    components=[]
                )
                concepts.append({'name': 'black_hole', 'def': fallback, 'count': count})
        
        return concepts
    
    def _layout_two_black_holes(self, width: int, height: int, count: int) -> List[Dict[str, Any]]:
        """Special layout for merging black holes."""
        instances = []
        cx, cy = width // 2, height // 2
        base_scale = min(width, height) / 300
        
        # Place in orbit
        orbit_radius = width * 0.15
        for i in range(count):
            angle = (2 * math.pi * i / count) + (self.seed % 10) * 0.1
            x = cx + int(orbit_radius * math.cos(angle))
            y = cy + int(orbit_radius * 0.6 * math.sin(angle))  # Flatten for perspective
            scale = base_scale * (0.9 if i == 0 else 1.0)
            
            instances.append({
                'type': 'black_hole',
                'position': (x, y),
                'scale': scale
            })
        return instances
    
    def render(self, prompt: str, width: int = 1024, height: int = 1024) -> str:
        # Parse
        concepts = self._parse_concepts(prompt)
        is_bh_merger = any(c['def'].strategy == RenderingStrategy.BLACK_HOLE for c in concepts) and \
                       ('merg' in prompt.lower() or 'two' in prompt.lower() or 'collision' in prompt.lower())
        
        # Create canvas
        img = Image.new('RGB', (width, height), (5, 5, 12))
        
        if is_bh_merger and len(concepts) == 1:
            # Special case: render overlapping BHs
            bh_scale = min(width, height) / 250
            offset_x = width * 0.15
            offset_y = height * 0.1
            
            # Render first BH
            bh1 = self.black_hole_engine.render(width, height, complexity=1.0, inclination=0.2)
            img.paste(bh1, (0, 0), bh1 if bh1.mode == 'RGBA' else None)
            
            # Render second BH shifted
            bh2 = self.black_hole_engine.render(width, height, complexity=1.0, inclination=0.2)
            img2 = Image.new('RGB', (width, height), (0,0,0))
            img2.paste(bh2, (int(offset_x), int(offset_y)), bh2 if bh2.mode == 'RGBA' else None)
            
            # Blend with screen mode effect
            arr1 = np.array(img, dtype=np.float32)
            arr2 = np.array(img2, dtype=np.float32)
            merged = np.maximum(arr1, arr2) * 0.9 + np.minimum(arr1, arr2) * 0.1
            img = Image.fromarray(np.clip(merged, 0, 255).astype(np.uint8))
        else:
            # Standard single-concept rendering
            concept = concepts[0]
            engine = self.engines.get(concept['def'].strategy)
            if engine:
                rendered = engine.render(width, height, complexity=concept['def'].base_complexity)
                if rendered:
                    img = rendered
        
        # Final touches
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=110, threshold=3))
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.25)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        
        # Encode
        from io import BytesIO
        import base64
        buffered = BytesIO()
        img.save(buffered, format="PNG", quality=95, optimize=True)
        return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"


def get_photorealistic_renderer(seed: Optional[int] = None):
    """Get global renderer instance."""
    global _renderer
    try:
        return _renderer
    except NameError:
        _renderer = PhotorealisticRenderer(seed)
        return _renderer
