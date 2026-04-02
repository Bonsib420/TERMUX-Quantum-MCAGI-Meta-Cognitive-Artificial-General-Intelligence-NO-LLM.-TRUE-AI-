"""
🎨 ULTIMATE RENDERER - Photorealistic Black Holes
"""

import numpy as np
import math
import random
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

from concept_ontology import get_ontology, ConceptDefinition, RenderingStrategy
from physics_engines.black_hole_ultimate import UltimateBlackHoleRenderer
from physics_engines.human_figure import HumanFigureRenderer
from physics_engines.geometric import GeometricRenderer


class UltimateRenderer:
    """Top-tier renderer."""
    
    def __init__(self, seed: Optional[int] = None):
        self.ontology = get_ontology()
        self.seed = seed if seed is not None else 12345
        self.rng = random.Random(self.seed)
        
        self.bh_engine = UltimateBlackHoleRenderer(seed=self.seed)
        self.human_engine = HumanFigureRenderer(seed=self.seed)
        self.geo_engine = GeometricRenderer(seed=self.seed)
        
        self.engines = {
            RenderingStrategy.BLACK_HOLE: self.bh_engine,
            RenderingStrategy.HUMAN_FIGURE: self.human_engine,
            RenderingStrategy.GEOMETRIC: self.geo_engine,
        }
    
    def _parse_prompt(self, prompt: str) -> Dict[str, Any]:
        words = prompt.lower().split()
        count = 1
        for w in words:
            if w.isdigit():
                count = int(w)
                break
            if w in ['two', 'three', 'four', 'five']:
                count = {'two':2, 'three':3, 'four':4, 'five':5}[w]
                break
        
        concept_name = None
        for name in self.ontology.list_concepts():
            if name in prompt.lower():
                concept_name = name
                break
        if not concept_name:
            concept_name = 'black_hole'  # default
        
        concept_def = self.ontology.get_concept(concept_name)
        if not concept_def:
            # fallback
            from concept_ontology import ConceptDefinition, RenderingStrategy
            concept_def = ConceptDefinition(
                name='fallback', category='astronomical', base_complexity=1.0,
                strategy=RenderingStrategy.BLACK_HOLE,
                visual_properties={'color_palette':[(255,255,255)]}, components=[]
            )
        
        return {'name': concept_name, 'def': concept_def, 'count': count}
    
    def render(self, prompt: str, width: int = 1024, height: int = 1024) -> str:
        info = self._parse_prompt(prompt)
        is_merger = info['count'] >= 2 and info['def'].strategy == RenderingStrategy.BLACK_HOLE
        
        # Create base
        img = Image.new('RGB', (width, height), (0,0,0))
        
        if is_merger:
            count = min(info['count'], 3)
            base = np.zeros((height, width, 3), dtype=np.float32)
            orbit_r = width * 0.12
            for i in range(count):
                angle = 2 * math.pi * i / count
                offx = int(orbit_r * math.cos(angle))
                offy = int(orbit_r * math.sin(angle) * 0.5)
                bh = self.bh_engine.render(width, height, complexity=info['def'].base_complexity, inclination=0.1)
                # Convert to RGB if RGBA
                if bh.mode == 'RGBA':
                    bh = bh.convert('RGB')
                arr = np.array(bh, dtype=np.float32)
                # Compute destination and source rectangles
                dest_x0 = max(0, offx)
                dest_x1 = min(width, offx + width)
                src_x0 = dest_x0 - offx
                src_x1 = src_x0 + (dest_x1 - dest_x0)
                
                dest_y0 = max(0, offy)
                dest_y1 = min(height, offy + height)
                src_y0 = dest_y0 - offy
                src_y1 = src_y0 + (dest_y1 - dest_y0)
                
                if dest_x1 > dest_x0 and dest_y1 > dest_y0:
                    base[dest_y0:dest_y1, dest_x0:dest_x1] = np.maximum(
                        base[dest_y0:dest_y1, dest_x0:dest_x1],
                        arr[src_y0:src_y1, src_x0:src_x1]
                    )
            img = Image.fromarray(np.clip(base,0,255).astype(np.uint8))
        else:
            # Single object
            engine = self.engines.get(info['def'].strategy)
            if engine:
                rendered = engine.render(width, height, complexity=info['def'].base_complexity)
                if rendered:
                    img = rendered
        
        # Global enhancements
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=100, threshold=3))
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        
        # Encode
        from io import BytesIO
        import base64
        buf = BytesIO()
        img.save(buf, format="PNG", quality=95, optimize=True)
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"


def get_ultimate_renderer(seed: Optional[int] = None):
    global _renderer
    try:
        return _renderer
    except NameError:
        _renderer = UltimateRenderer(seed)
        return _renderer
