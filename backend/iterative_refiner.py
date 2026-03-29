"""
🔄 ITERATIVE REFINER
Generate → Critique → Refine loop.
Self-improves output until quality threshold is met.
"""

from typing import Dict, Any, Optional, List
from PIL import Image
import base64
from io import BytesIO

from renderer import get_renderer
from critic import ImageCritic


class IterativeRefiner:
    """
    Iteratively refines an image through generate-critique-refine cycles.
    Targets a quality score threshold (default 0.75).
    """
    
    def __init__(self, target_score: float = 0.75, max_iterations: int = 3):
        self.target_score = target_score
        self.max_iterations = max_iterations
        self.renderer = get_renderer()
        self.critic = ImageCritic()
    
    def refine(self, prompt: str, width: int = 512, height: int = 512,
               initial_complexity: Optional[float] = None) -> Dict[str, Any]:
        """
        Generate and refine an image.
        
        Args:
            prompt: text description
            width, height: output resolution
            initial_complexity: override initial complexity (if None, inferred from prompt)
            
        Returns:
            {
                'image': data_url,
                'final_score': float,
                'iterations': int,
                'history': [
                    {'iteration': 1, 'score': 0.6, 'feedback': [...], 'image': data_url},
                    ...
                ]
            }
        """
        best_image = None
        best_score = 0.0
        history = []
        
        current_prompt = prompt
        current_complexity = initial_complexity
        current_quality = None
        
        for iteration in range(1, self.max_iterations + 1):
            # 1. Generate
            if iteration == 1 and current_complexity is not None:
                # Temporarily override renderer complexity (need a way to pass it)
                # For now we just use the prompt as-is
                img_data = self.renderer.render(current_prompt, width, height)
            else:
                # Modify prompt based on feedback to improve
                if iteration > 1 and history:
                    last_feedback = history[-1]['feedback']
                    current_prompt = self._enhance_prompt(prompt, last_feedback)
                img_data = self.renderer.render(current_prompt, width, height)
            
            # Decode for critique
            img = self._decode_image(img_data)
            
            # 2. Critique
            # Infer complexity from prompt (simple heuristic)
            complexity = 0.5
            if 'black hole' in current_prompt.lower():
                complexity = 1.0
            elif 'stick figure' in current_prompt.lower():
                complexity = 0.05
            
            evaluation = self.critic.evaluate(img, current_prompt, complexity)
            
            history.append({
                'iteration': iteration,
                'score': evaluation['overall_score'],
                'feedback': evaluation['feedback'],
                'suggestions': evaluation['suggestions'],
                'image': img_data,
                'prompt_used': current_prompt
            })
            
            # Track best
            if evaluation['overall_score'] > best_score:
                best_score = evaluation['overall_score']
                best_image = img_data
            
            # 3. Check if target reached
            if evaluation['overall_score'] >= self.target_score:
                break
            
            # Prepare for next iteration (modify prompt based on suggestions)
            if iteration < self.max_iterations:
                current_prompt = self._enhance_prompt(current_prompt, evaluation['suggestions'])
        
        return {
            'image': best_image,
            'final_score': best_score,
            'iterations': len(history),
            'target_met': best_score >= self.target_score,
            'history': history
        }
    
    def _decode_image(self, data_url: str) -> Image.Image:
        """Decode base64 PNG to PIL Image."""
        b64 = data_url.split(',')[1]
        img_bytes = base64.b64decode(b64)
        return Image.open(BytesIO(img_bytes))
    
    def _enhance_prompt(self, base_prompt: str, feedback: List[str]) -> str:
        """
        Enhance prompt based on critic feedback.
        This is a simple rule-based enhancement.
        """
        enhanced = base_prompt
        
        # Add quality boosters if needed
        if any('complexity' in f.lower() or 'detail' in f.lower() for f in feedback):
            if 'highly detailed' not in enhanced:
                enhanced = "highly detailed " + enhanced
            if 'physically accurate' not in enhanced:
                enhanced = enhanced.replace('two', 'two physically accurate')
        
        if any('composition' in f.lower() for f in feedback):
            if 'centered' not in enhanced:
                enhanced += " centered composition"
        
        return enhanced
