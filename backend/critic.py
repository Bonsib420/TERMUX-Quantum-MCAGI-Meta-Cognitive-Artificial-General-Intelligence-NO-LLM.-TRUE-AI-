"""
🔍 CRITIC - Self-Evaluation Module
Evaluates generated images for quality, accuracy, and prompt alignment.
No LLM used - purely algorithmic assessment based on image analysis.
"""

import math
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image
import numpy as np


class ImageCritic:
    """
    Critiques an image and returns a score + feedback.
    Evaluates composition, technical quality, and prompt alignment.
    """
    
    def __init__(self):
        # Feature detectors map concepts to detection functions (stubs for now)
        self.feature_detectors = {
            'black hole': self._detect_black_hole_features,
            'stick figure': self._detect_figure_features,
            'human': self._detect_figure_features,
        }
    
    # Stub detection methods - return basic metrics
    def _detect_black_hole_features(self, arr: np.ndarray) -> Dict[str, float]:
        """Detect black hole features: central darkness, bright rings."""
        h, w = arr.shape[:2]
        cx, cy = w // 2, h // 2
        center_region = arr[cy-h//8:cy+h//8, cx-w//8:cx+w//8]
        if center_region.size == 0:
            return {'has_event_horizon': 0.0, 'has_accretion': 0.0}
        darkness = float(center_region.mean())
        has_event = 1.0 if darkness < 50 else 0.0
        ring_region = arr[cy-h//4:cy+h//4, cx-w//4:cx+w//4]
        brightness_std = float(ring_region.std())
        has_accretion = 1.0 if brightness_std > 30 else 0.5
        return {'has_event_horizon': float(has_event), 'has_accretion': has_accretion}
    
    def _detect_figure_features(self, arr: np.ndarray) -> Dict[str, float]:
        """Detect human figure: elongated shape, joint points."""
        non_dark = float(np.sum(arr > 50) / arr.size)
        return {'has_figure': min(1.0, non_dark * 10), 'complexity': non_dark}
    
    def evaluate(self, image: Image.Image, prompt: str, complexity_expected: float) -> Dict[str, Any]:
        """
        Evaluate image quality and correctness.
        
        Returns:
            {
                'overall_score': 0.0-1.0,
                'composition_score': 0.0-1.0,
                'technical_score': 0.0-1.0,
                'alignment_score': 0.0-1.0,
                'feedback': ['message1', 'message2', ...],
                'suggestions': ['suggestion1', ...]
            }
        """
        scores = {
            'composition': self._score_composition(image),
            'technical': self._score_technical(image),
            'alignment': self._score_prompt_alignment(image, prompt, complexity_expected),
        }
        
        overall = sum(scores.values()) / len(scores)
        
        feedback = self._generate_feedback(image, prompt, scores)
        suggestions = self._generate_suggestions(image, prompt, scores)
        
        return {
            'overall_score': round(overall, 3),
            'composition_score': round(scores['composition'], 3),
            'technical_score': round(scores['technical'], 3),
            'alignment_score': round(scores['alignment'], 3),
            'feedback': feedback,
            'suggestions': suggestions
        }
    
    def _score_composition(self, img: Image.Image) -> float:
        """Evaluate compositional quality."""
        w, h = img.size
        arr = np.array(img.convert('L'))
        
        left_third = w // 3
        right_third = 2 * w // 3
        top_third = h // 3
        bottom_third = 2 * h // 3
        
        regions = {
            'tl': float(arr[:top_third, :left_third].mean()),
            'tr': float(arr[:top_third, right_third:].mean()),
            'bl': float(arr[bottom_third:, :left_third].mean()),
            'br': float(arr[bottom_third:, right_third:].mean()),
            'center': float(arr[top_third:bottom_third, left_third:right_third].mean()),
        }
        
        center_score = regions['center'] / max(1, np.mean(list(regions.values())))
        if 0.8 < center_score < 1.5:
            comp_score = 0.8
        else:
            comp_score = 0.5
        
        left = float(arr[:, :w//2].mean())
        right = float(arr[:, w//2:].mean())
        balance = 1.0 - abs(left - right) / max(1, (left + right))
        comp_score = (comp_score + balance) / 2
        
        return float(min(1.0, comp_score))
    
    def _score_technical(self, img: Image.Image) -> float:
        """Technical quality: contrast, color variety."""
        arr = np.array(img)
        
        contrast = float(arr.std())
        if contrast < 30:
            contrast_score = 0.3
        elif contrast < 60:
            contrast_score = 0.6
        else:
            contrast_score = 1.0
        
        unique_colors = len(np.unique(arr.reshape(-1, 3), axis=0))
        total_pixels = arr.shape[0] * arr.shape[1]
        color_variety = unique_colors / max(1, total_pixels)
        variety_score = min(1.0, color_variety * 10000)
        
        tech_score = (contrast_score + variety_score) / 2
        return float(min(1.0, tech_score))
    
    def _score_prompt_alignment(self, img: Image.Image, prompt: str, complexity_expected: float) -> float:
        """Check alignment with prompt."""
        prompt_lower = prompt.lower()
        arr = np.array(img.convert('L'))
        
        score = 0.5
        
        if 'black hole' in prompt_lower or 'singularity' in prompt_lower:
            h, w = arr.shape
            cx, cy = w // 2, h // 2
            center_region = arr[cy-h//8:cy+h//8, cx-w//8:cx+w//8]
            if center_region.size > 0:
                darkness = float(center_region.mean())
                if darkness < 30:
                    score += 0.4
                else:
                    score -= 0.2
        
        if 'stick figure' in prompt_lower or 'simple' in prompt_lower:
            unique_colors = len(np.unique(arr))
            if unique_colors < 100:
                score += 0.3
            else:
                score -= 0.1
        
        actual_variety = len(np.unique(arr)) / max(1, arr.size)
        expected_variety = 0.001 + 0.01 * complexity_expected
        if abs(actual_variety - expected_variety) < 0.005:
            score += 0.1
        
        return float(min(1.0, max(0.0, score)))
    
    def _generate_feedback(self, img: Image.Image, prompt: str, scores: Dict[str, float]) -> List[str]:
        """Generate human-readable feedback."""
        feedback = []
        
        if scores['composition'] < 0.6:
            feedback.append("Composition could be improved - consider Rule of Thirds")
        if scores['technical'] < 0.6:
            feedback.append("Technical quality low: increase contrast or detail")
        if scores['alignment'] < 0.6:
            feedback.append("Image may not fully match prompt description")
        
        if all(v > 0.8 for v in scores.values()):
            feedback.append("Excellent quality across all metrics")
        
        return feedback
    
    def _generate_suggestions(self, img: Image.Image, prompt: str, scores: Dict[str, float]) -> List[str]:
        """Generate actionable suggestions for improvement."""
        suggestions = []
        
        if scores['technical'] < 0.7:
            suggestions.append("Increase render resolution or quality settings")
        if scores['composition'] < 0.5:
            suggestions.append("Adjust object placement for better balance")
        if 'black hole' in prompt and scores['alignment'] < 0.7:
            suggestions.append("Enhance black hole physics: add photon sphere, accretion disk")
        
        return suggestions
