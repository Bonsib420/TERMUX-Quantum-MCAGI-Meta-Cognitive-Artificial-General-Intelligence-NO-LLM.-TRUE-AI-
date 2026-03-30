"""
🎨 FINAL COGNITIVE RENDERER - High Quality
Uses the best physics engines for photorealistic output.
"""

import math
import random
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

from concept_ontology import get_ontology, ConceptDefinition, RenderingStrategy
# Use final engines
from physics_engines.black_hole_final import FinalBlackHoleRenderer
from physics_engines.human_figure import HumanFigureRenderer
from physics_engines.geometric import GeometricRenderer


class FinalCognitiveRenderer:
    """The ultimate renderer with highest quality."""
    
    def __init__(self, seed: Optional[int] = None):
        self.ontology = get_ontology()
        self.seed = seed if seed is not None else 12345
        self.rng = random.Random(self.seed)
        
        # Initialize engines
        self.black_hole_engine = FinalBlackHoleRenderer(seed=self.seed)
        self.human_figure_engine = HumanFigureRenderer(seed=self.seed)
        self.geometric_engine = GeometricRenderer(seed=self.seed)
        
        self.engines = {
            RenderingStrategy.BLACK_HOLE: self.black_hole_engine,
            RenderingStrategy.HUMAN_FIGURE: self.human_figure_engine,
            RenderingStrategy.GEOMETRIC: self.geometric_engine,
            RenderingStrategy.PARTICLE_SYSTEM: self.geometric_engine,
        }
    
    def _parse_concepts(self, prompt: str) -> List[Dict[str, Any]]:
        words = prompt.lower().replace(',', ' ').split()
        count = 1
        numbers = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
        for i, num in enumerate(numbers, 1):
            if num in words: count = i; break
        for word in words:
            if word.isdigit(): count = int(word); break
        
        concepts_found = []
        for concept_name in self.ontology.list_concepts():
            if concept_name in prompt.lower():
                concept_def = self.ontology.get_concept(concept_name)
                if concept_def:
                    concepts_found.append({'name': concept_name, 'definition': concept_def, 'count': count})
        
        if not concepts_found:
            default_concept = self.ontology.get_concept('default')
            if default_concept:
                concepts_found.append({'name': 'default', 'definition': default_concept, 'count': count})
            else:
                # Fallback to simple circle
                fallback = ConceptDefinition(
                    name='fallback', category='geometric', base_complexity=0.0,
                    strategy=RenderingStrategy.GEOMETRIC,
                    visual_properties={'color_palette': [(200, 200, 200)]},
                    components=[]
                )
                concepts_found.append({'name': 'fallback', 'definition': fallback, 'count': count})
        
        return concepts_found
    
    def _calculate_scene_complexity(self, concepts: List[Dict[str, Any]]) -> float:
        complexities = [c['definition'].base_complexity for c in concepts]
        return max(complexities) if complexities else 0.3
    
    def _layout_objects(self, width: int, height: int, concept_counts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        instances = []
        margin = width // 8
        
        for concept_info in concept_counts:
            count = concept_info['count']
            definition = concept_info['definition']
            
            if count == 1:
                x_positions = [width // 2]
            else:
                spacing = (width - 2 * margin) // (count + 1)
                x_positions = [margin + (i + 1) * spacing for i in range(min(count, 10))]
            
            for i, x in enumerate(x_positions):
                y_jitter = height // 20 * ((self.seed + i) % 7 - 3)
                y_pos = height // 2 + y_jitter
                
                base_scale = min(width, height) / 800 * 0.8
                if definition.base_complexity > 0.8:
                    base_scale *= 1.2
                elif definition.base_complexity < 0.2:
                    base_scale *= 0.7
                
                instances.append({
                    'concept_name': concept_info['name'],
                    'definition': definition,
                    'position': (x, y_pos),
                    'scale': base_scale * (0.9 + 0.2 * (self.seed + i) % 10 / 10),
                    'color_index': i % len(definition.visual_properties.get('color_palette', [(255,255,255)]))
                })
        
        return instances
    
    def _render_object(self, obj_instance: Dict[str, Any], width: int, height: int) -> Optional[Image.Image]:
        definition = obj_instance['definition']
        strategy = definition.strategy
        engine = self.engines.get(strategy)
        
        if not engine:
            return None
        
        palette = definition.visual_properties.get('color_palette', [(255, 255, 255)])
        color = palette[obj_instance['color_index']]
        scale = obj_instance['scale']
        
        if strategy == RenderingStrategy.BLACK_HOLE:
            # Render black hole at full quality
            return engine.render(width, height, complexity=definition.base_complexity, mass=50.0)
        
        elif strategy == RenderingStrategy.HUMAN_FIGURE:
            size = int(200 * scale)
            return engine.render(width=size*2, height=size*3, complexity=definition.base_complexity,
                               scale=scale, color=color, pose="standing")
        
        elif strategy == RenderingStrategy.GEOMETRIC:
            # For geometric shapes, draw directly on a canvas
            size = int(150 * scale)
            img = Image.new('RGBA', (size*2, size*2), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            cx, cy = size, size
            
            if 'circle' in definition.name:
                r = int(size * 0.8)
                draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=color, width=3)
            elif 'line' in definition.name:
                draw.line([(cx-size, cy), (cx+size, cy)], fill=color, width=3)
            elif 'wave' in definition.name or 'field' in definition.name:
                # Simple wave pattern
                points = []
                for x in range(cx-size, cx+size, 2):
                    y = cy + int(20 * math.sin((x-cx)*0.1))
                    points.append((x, y))
                if len(points) > 1:
                    for i in range(len(points)-1):
                        draw.line([points[i], points[i+1]], fill=color, width=2)
            else:
                draw.ellipse([cx-size, cy-size, cx+size, cy+size], fill=color)
            
            return img
        
        return None
    
    def render(self, prompt: str, width: int = 1024, height: int = 1024) -> str:
        """Generate high-quality image from prompt."""
        # Parse
        concepts = self._parse_concepts(prompt)
        scene_complexity = self._calculate_scene_complexity(concepts)
        
        # Create base image
        bg_color = (5, 5, 12) if scene_complexity > 0.3 else (12, 15, 22)
        base = Image.new('RGB', (width, height), bg_color)
        
        # Layout objects
        obj_instances = self._layout_objects(width, height, concepts)
        
        # Render each object
        for obj in obj_instances:
            obj_img = self._render_object(obj, width, height)
            if obj_img:
                pos = obj['position']
                ox = pos[0] - obj_img.width // 2
                oy = pos[1] - obj_img.height // 2
                if obj_img.mode == 'RGBA':
                    base.paste(obj_img, (ox, oy), obj_img)
                else:
                    base.paste(obj_img, (ox, oy))
        
        # === BLACK HOLE SPECIFIC: If only one black hole centered, improve quality ===
        if scene_complexity > 0.8 and len(obj_instances) == 1:
            # Replace with high-res centered black hole
            bh_img = self.black_hole_engine.render(width, height, complexity=scene_complexity)
            base = bh_img
        
        # Post-processing
        if scene_complexity > 0.5:
            # Unsharp mask for sharpness
            base = base.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
            # Color boost
            enhancer = ImageEnhance.Color(base)
            base = enhancer.enhance(1.2)
            # Contrast
            enhancer = ImageEnhance.Contrast(base)
            base = enhancer.enhance(1.1)
        
        # Encode
        from io import BytesIO
        import base64
        buffered = BytesIO()
        base.save(buffered, format="PNG", quality=95, optimize=True)
        return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"


# Global renderer instance
_renderer: Optional[FinalCognitiveRenderer] = None

def get_final_renderer(seed: Optional[int] = None) -> FinalCognitiveRenderer:
    """Get or create the global final renderer."""
    global _renderer
    if _renderer is None:
        _renderer = FinalCognitiveRenderer(seed)
    return _renderer

