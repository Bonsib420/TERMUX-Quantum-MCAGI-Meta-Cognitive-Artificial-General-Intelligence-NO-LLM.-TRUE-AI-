"""
🎨 COGNITIVE RENDERING ENGINE
Master orchestrator that understands prompts and produces high-quality images.
Selects appropriate physics engines, manages complexity, composes final output.
"""

import math
import random
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance

from concept_ontology import get_ontology, ConceptDefinition, RenderingStrategy
from physics_engines.black_hole import BlackHoleRenderer
from physics_engines.human_figure import HumanFigureRenderer
from physics_engines.geometric import GeometricRenderer


class CognitiveRenderer:
    """
    The master rendering engine. This is the "artist" that understands
    concepts and can render them at any level of complexity.
    """
    
    def __init__(self, seed: Optional[int] = None):
        self.ontology = get_ontology()
        self.seed = seed if seed is not None else 12345
        self.rng = random.Random(self.seed)  # For post-processing noise etc.
        
        # Initialize physics engines
        self.black_hole_engine = BlackHoleRenderer(seed=self.seed)
        self.human_figure_engine = HumanFigureRenderer(seed=self.seed)
        self.geometric_engine = GeometricRenderer(seed=self.seed)
        
        # Engine mapping
        self.engines = {
            RenderingStrategy.BLACK_HOLE: self.black_hole_engine,
            RenderingStrategy.HUMAN_FIGURE: self.human_figure_engine,
            RenderingStrategy.GEOMETRIC: self.geometric_engine,
            RenderingStrategy.PARTICLE_SYSTEM: self.geometric_engine,
            RenderingStrategy.COMPOSITE: None,
        }
    
    def _parse_concepts(self, prompt: str) -> List[Dict[str, Any]]:
        """Extract concept instances from prompt."""
        words = prompt.lower().replace(',', ' ').split()
        
        # Count objects
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
        
        # Find concepts
        concepts_found = []
        for concept_name in self.ontology.list_concepts():
            if concept_name in prompt.lower():
                concept_def = self.ontology.get_concept(concept_name)
                if concept_def:
                    concepts_found.append({
                        'name': concept_name,
                        'definition': concept_def,
                        'count': count,
                    })
        
        if not concepts_found:
            default_concept = self.ontology.get_concept('default')
            concepts_found.append({
                'name': 'default',
                'definition': default_concept,
                'count': count,
            })
        
        return concepts_found
    
    def _calculate_scene_complexity(self, concepts: List[Dict[str, Any]]) -> float:
        """Overall complexity = max of individual complexities."""
        complexities = [c['definition'].base_complexity for c in concepts]
        return max(complexities) if complexities else 0.3
    
    def _determine_quality_settings(self, complexity: float, width: int, height: int) -> Dict[str, Any]:
        """Map complexity to rendering parameters."""
        if complexity < 0.2:
            return {
                'render_scale': 1.0,
                'background_stars': False,
                'glow': False,
                'noise': False,
                'color_correction': False,
                'max_objects': 5
            }
        elif complexity < 0.5:
            return {
                'render_scale': 1.5,
                'background_stars': True,
                'glow': complexity > 0.4,
                'noise': False,
                'color_correction': False,
                'max_objects': 10
            }
        else:
            return {
                'render_scale': 2.0,
                'background_stars': True,
                'glow': True,
                'noise': complexity > 0.8,
                'color_correction': True,
                'max_objects': 20
            }
    
    def _layout_objects(self, width: int, height: int, concept_counts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Arrange objects in the scene."""
        instances = []
        margin = width // 8
        
        for concept_info in concept_counts:
            count = concept_info['count']
            definition = concept_info['definition']
            
            if count == 1:
                x_positions = [width // 2]
            else:
                spacing = (width - 2 * margin) // (count + 1)
                x_positions = [margin + (i + 1) * spacing for i in range(min(count, 20))]
            
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
    
    def _render_object(self, obj_instance: Dict[str, Any], quality: Dict[str, Any], canvas_width: int, canvas_height: int) -> Image.Image:
        """Render a single object using its appropriate physics engine."""
        definition = obj_instance['definition']
        strategy = definition.strategy
        engine = self.engines.get(strategy)
        
        if not engine:
            return self._render_placeholder(obj_instance, canvas_width, canvas_height)
        
        obj_size = int(200 * obj_instance['scale'])
        local_img = Image.new('RGBA', (obj_size * 2, obj_size * 2), (0, 0, 0, 0))
        local_draw = ImageDraw.Draw(local_img)
        
        cx, cy = obj_size, obj_size
        palette = definition.visual_properties.get('color_palette', [(255, 255, 255)])
        color = palette[obj_instance['color_index']]
        
        if strategy == RenderingStrategy.BLACK_HOLE:
            # Render black hole at object's local size (much faster)
            local_size = obj_size * 2
            bh_render = engine.render(
                width=local_size,
                height=local_size,
                complexity=definition.base_complexity,
                mass=definition.parameters.get('mass', {}).get('default', 50.0)
            )
            return bh_render.convert('RGBA')
        
        elif strategy == RenderingStrategy.HUMAN_FIGURE:
            fig_img = engine.render(
                width=obj_size*2,
                height=obj_size*3,
                complexity=definition.base_complexity,
                scale=obj_instance['scale'],
                color=color,
                pose="standing"
            )
            return fig_img.convert('RGBA')
        
        elif strategy == RenderingStrategy.GEOMETRIC:
            if 'circle' in definition.name:
                engine.draw_circle(local_draw, cx, cy, obj_size, color, fill=False, line_width=3)
            elif 'line' in definition.name:
                engine.draw_antialiased_line(local_draw, (cx - obj_size, cy), (cx + obj_size, cy), color, width=3)
            elif 'wave' in definition.name or 'field' in definition.name:
                engine.draw_wave_pattern(local_draw, obj_size*2, obj_size*2,
                                        definition.base_complexity, palette, str(self.seed))
            elif 'pattern' in definition.name:
                engine.draw_geometric_pattern(local_draw, obj_size*2, obj_size*2,
                                             definition.base_complexity, palette)
            else:
                engine.draw_circle(local_draw, cx, cy, obj_size, color, fill=True)
            
            return local_img
        
        else:
            return self._render_placeholder(obj_instance, canvas_width, canvas_height)
    
    def _render_placeholder(self, obj_instance: Dict[str, Any], w: int, h: int) -> Image.Image:
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        try:
            draw.text((w//2, h//2), f"?{obj_instance['concept_name']}", fill=(255,255,255))
        except:
            pass
        return img
    
    def _apply_post_processing(self, img: Image.Image, complexity: float, quality: Dict[str, Any]) -> Image.Image:
        """Apply post-processing effects."""
        if quality['glow']:
            glow = img.filter(ImageFilter.GaussianBlur(radius=3))
            img = ImageChops.screen(img, glow)
        
        if quality['color_correction']:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.2)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.1)
        
        if quality['noise']:
            pixels = img.load()
            w, h = img.size
            for i in range(w):
                for j in range(h):
                    if self.rng.random() < 0.1:
                        v = self.rng.randint(-8, 8)
                        r, g, b = pixels[i, j]
                        pixels[i, j] = (max(0, min(255, r+v)), max(0, min(255, g+v)), max(0, min(255, b+v)))
        
        return img
    
    def render(self, prompt: str, width: int = 1024, height: int = 1024) -> str:
        """
        Generate image from prompt.
        Returns base64 PNG data URL.
        """
        # Parse concepts
        concepts = self._parse_concepts(prompt)
        
        # Determine complexity
        scene_complexity = self._calculate_scene_complexity(concepts)
        
        # Quality settings
        quality = self._determine_quality_settings(scene_complexity, width, height)
        
        # Render resolution
        render_scale = quality['render_scale']
        render_w = int(width * render_scale)
        render_h = int(height * render_scale)
        
        # Create base canvas
        bg_color = (5, 5, 12) if scene_complexity > 0.3 else (12, 15, 22)
        base = Image.new('RGB', (render_w, render_h), bg_color)
        draw = ImageDraw.Draw(base)
        
        # Background stars
        if quality['background_stars']:
            self.geometric_engine.draw_starfield(draw, render_w, render_h, density=0.02)
        
        # Layout objects
        obj_instances = self._layout_objects(render_w, render_h, concepts)
        
        # Render and composite objects
        for obj in obj_instances:
            obj_img = self._render_object(obj, quality, render_w, render_h)
            if obj_img:
                pos = obj['position']
                ox = pos[0] - obj_img.width // 2
                oy = pos[1] - obj_img.height // 2
                base.paste(obj_img, (ox, oy), obj_img if obj_img.mode == 'RGBA' else None)
        
        # Post-processing
        final = self._apply_post_processing(base, scene_complexity, quality)
        
        # Downsample
        if render_scale > 1.0:
            final = final.resize((width, height), Image.Resampling.LANCZOS)
        
        # Encode
        from io import BytesIO
        import base64
        buffered = BytesIO()
        final.save(buffered, format="PNG", quality=95, optimize=True)
        img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{img_b64}"


# Global renderer instance
_renderer: Optional[CognitiveRenderer] = None

def get_renderer(seed: Optional[int] = None) -> CognitiveRenderer:
    """Get or create the global cognitive renderer."""
    global _renderer
    if _renderer is None:
        _renderer = CognitiveRenderer(seed)
    return _renderer
