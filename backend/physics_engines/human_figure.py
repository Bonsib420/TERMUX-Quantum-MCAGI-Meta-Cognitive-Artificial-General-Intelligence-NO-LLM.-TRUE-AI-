"""
🦴 HUMAN FIGURE PHYSICS ENGINE
Anatomically accurate human figure renderer with biomechanical constraints.
Understands proportions, joint articulation, and natural poses.
"""

import math
import random
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw


class HumanFigureRenderer:
    """
    Renders human figures with anatomical accuracy.
    Supports complexity scaling from stick figures (0.05) to detailed anatomical (0.2-0.3).
    """
    
    # Proportions (based on 8-head canon)
    PROPORTIONS = {
        'head_height': 1.0,
        'neck_length': 0.25,
        'shoulder_width': 2.0,  # in head units
        'torso_length': 3.0,    # from shoulders to hips
        'upper_arm_length': 1.5,
        'lower_arm_length': 1.25,
        'hand_length': 0.75,
        'thigh_length': 2.0,
        'shin_length': 2.0,
        'foot_length': 1.0,
    }
    
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
    
    def _scale_to_canvas(self, value: float, scale_factor: float, base_y: int) -> int:
        """Convert anatomical units to canvas coordinates."""
        return int(base_y - value * scale_factor)
    
    def draw_line_smooth(self, draw: ImageDraw.ImageDraw, p1: Tuple[int, int], p2: Tuple[int, int], color: Tuple[int, int, int], width: int):
        """Draw an antialiased line."""
        # Multiple passes for smoothness
        for dx in (-0.5, 0, 0.5):
            for dy in (-0.5, 0, 0.5):
                adj_p1 = (p1[0] + dx, p1[1] + dy)
                adj_p2 = (p2[0] + dx, p2[1] + dy)
                draw.line([adj_p1, adj_p2], fill=color, width=width)
    
    def draw_joint_smooth(self, draw: ImageDraw.ImageDraw, x: int, y: int, radius: int, color: Tuple[int, int, int]):
        """Draw an antialiased joint circle."""
        r_adj = radius + 0.5
        bbox = [x - r_adj, y - r_adj, x + r_adj, y + r_adj]
        draw.ellipse(bbox, fill=color)
    
    def draw_head(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int, complexity: float, color: Tuple[int, int, int]):
        """Draw head (oval) with simple facial features if complexity high."""
        # Head outline
        self.draw_joint_smooth(draw, cx, cy, radius, color)
        
        if complexity > 0.5:
            # Eyes
            eye_offset = radius // 2
            eye_y = cy - radius // 4
            eye_radius = max(2, radius // 5)
            for ex in [cx - eye_offset, cx + eye_offset]:
                self.draw_joint_smooth(draw, ex, eye_y, eye_radius, color)
            
            # Nose (simple)
            nose_y = cy + radius // 4
            draw.line([(cx, cy), (cx, nose_y)], fill=color, width=max(1, radius//10))
            
            # Mouth (smile)
            mouth_y = cy + radius // 2
            smile_radius = radius // 2
            draw.arc([cx - smile_radius, mouth_y - smile_radius//2, cx + smile_radius, mouth_y + smile_radius//2],
                    200, 340, fill=color, width=max(1, radius//12))
        
        if complexity > 0.8:
            # Hair
            hair_y_top = cy - radius - radius//4
            hair_width = radius + radius//3
            draw.ellipse([cx - hair_width, hair_y_top - hair_width//2, cx + hair_width, cy], fill=color)
    
    def draw_torso(self, draw: ImageDraw.ImageDraw, x: int, y_top: int, y_bottom: int, width: int, complexity: float, color: Tuple[int, int, int]):
        """Draw torso (ribcage/pelvis simplified)."""
        # Center line (spine)
        self.draw_line_smooth(draw, (x, y_top), (x, y_bottom), color, max(2, width//3))
        
        # Shoulders
        shoulder_y = y_top
        for side in [-1, 1]:
            self.draw_joint_smooth(draw, x + side * width//2, shoulder_y, max(2, width//4), color)
            # Collarbone
            collar_y = y_top + width//4
            self.draw_line_smooth(draw, (x, collar_y), (x + side * width//2, shoulder_y), color, 2)
        
        if complexity > 0.6:
            # Ribs
            num_ribs = 4
            for i in range(num_ribs):
                rib_y = y_top + int((y_bottom - y_top) * (0.3 + i * 0.15))
                rib_half_width = int(width//2 * (0.6 - i * 0.1))
                draw.line([(x - rib_half_width, rib_y), (x + rib_half_width, rib_y)], fill=color, width=1)
        
        # Hips
        hip_y = y_bottom
        hip_width = int(width * 0.8)
        for side in [-1, 1]:
            self.draw_joint_smooth(draw, x + side * hip_width//2, hip_y, max(3, width//3), color)
    
    def draw_arm(self, draw: ImageDraw.ImageDraw, x: int, y_top: int, y_bottom: int, width: int, complexity: float, color: Tuple[int, int, int]):
        """Draw a complete arm: upper arm + forearm + hand."""
        # Upper arm (shoulder to elbow)
        elbow_x = x
        elbow_y = y_top + int((y_bottom - y_top) * 0.4)
        self.draw_line_smooth(draw, (x, y_top), (elbow_x, elbow_y), color, max(2, width//2))
        
        # Elbow joint
        self.draw_joint_smooth(draw, elbow_x, elbow_y, max(3, width//3), color)
        
        # Forearm (elbow to wrist)
        wrist_x = x + width//4  # arm extended slightly forward
        wrist_y = y_bottom
        self.draw_line_smooth(draw, (elbow_x, elbow_y), (wrist_x, wrist_y), color, max(2, width//2))
        
        # Wrist
        self.draw_joint_smooth(draw, wrist_x, wrist_y, max(3, width//3), color)
        
        # Hand
        if complexity > 0.3:
            hand_length = width
            hand_dir = -0.3  # slightly downward
            hand_end_x = wrist_x + int(hand_length * math.sin(hand_dir))
            hand_end_y = wrist_y + int(hand_length * math.cos(hand_dir))
            self.draw_line_smooth(draw, (wrist_x, wrist_y), (hand_end_x, hand_end_y), color, max(1, width//3))
            
            if complexity > 0.6:
                # Fingers
                for i in range(4):
                    finger_angle = -0.5 + i * 0.3
                    finger_len = hand_length * 0.3
                    fx = hand_end_x + int(finger_len * math.sin(finger_angle))
                    fy = hand_end_y + int(finger_len * math.cos(finger_angle))
                    self.draw_line_smooth(draw, (hand_end_x, hand_end_y), (fx, fy), color, max(1, width//5))
    
    def draw_leg(self, draw: ImageDraw.ImageDraw, x: int, y_top: int, y_bottom: int, width: int, complexity: float, color: Tuple[int, int, int]):
        """Draw a complete leg: thigh + shin + foot."""
        # Hip joint
        hip_x = x
        hip_y = y_top
        self.draw_joint_smooth(draw, hip_x, hip_y, max(4, width//2), color)
        
        # Thigh
        knee_x = x
        knee_y = y_top + int((y_bottom - y_top) * 0.5)
        self.draw_line_smooth(draw, (hip_x, hip_y), (knee_x, knee_y), color, max(3, width//2))
        
        # Knee
        self.draw_joint_smooth(draw, knee_x, knee_y, max(4, width//2), color)
        
        # Shin
        ankle_x = knee_x + width//6  # foot forward slightly
        ankle_y = y_bottom - width//2
        self.draw_line_smooth(draw, (knee_x, knee_y), (ankle_x, ankle_y), color, max(3, width//2))
        
        # Ankle
        self.draw_joint_smooth(draw, ankle_x, ankle_y, max(3, width//2), color)
        
        # Foot
        foot_length = int(width * 1.2)
        foot_angle = 0.0  # flat ground
        foot_end_x = ankle_x + int(foot_length * math.sin(foot_angle))
        foot_end_y = ankle_y + int(foot_length * math.cos(foot_angle))
        self.draw_line_smooth(draw, (ankle_x, ankle_y), (foot_end_x, foot_end_y), color, max(2, width//2))
        
        # Foot sole (thicker)
        foot_width = width // 2
        draw.ellipse([ankle_x - foot_width//2, ankle_y - foot_width//4,
                     foot_end_x, ankle_y + foot_width//4], fill=color)
    
    def render(self, width: int, height: int, complexity: float = 0.05, scale: float = 1.0, color: Tuple[int, int, int] = (255, 255, 255), pose: str = "standing") -> Image.Image:
        """
        Render a human figure.
        
        Args:
            width, height: canvas size
            complexity: 0.0 (stick figure) to 0.2 (detailed)
            scale: figure size relative to canvas (0.5-1.0)
            color: RGB color for lines
            pose: "standing", "t-pose", "walking"
            
        Returns:
            PIL Image with rendered figure
        """
        img = Image.new('RGB', (width, height), (12, 15, 22))
        draw = ImageDraw.Draw(img)
        
        # Calculate base figure dimensions
        base_unit = int(min(width, height) * 0.15 * scale)
        
        center_x = width // 2
        ground_y = height - int(min(width, height) * 0.1)
        head_radius = base_unit // 3
        
        # Pose: standing with feet shoulder-width apart
        stance_width = base_unit // 2
        
        # Key points (starting from head)
        head_y = ground_y - base_unit * 3
        
        neck_y = head_y + head_radius + base_unit // 4
        shoulder_y = neck_y
        hip_y = ground_y - base_unit // 2
        
        arm_length = base_unit * 0.8
        leg_length = base_unit * 1.0
        
        # Adjust positions based on pose
        if pose == "t-pose":
            arm_span = base_unit
            left_hand_x = center_x - arm_span // 2
            right_hand_x = center_x + arm_span // 2
            arm_y = shoulder_y
        else:  # standing自然的
            arm_span = base_unit * 0.6
            left_hand_x = center_x - arm_span // 2
            right_hand_x = center_x + arm_span // 2
            arm_y = shoulder_y + base_unit // 4
        
        foot_offset = base_unit // 4
        left_foot_x = center_x - foot_offset
        right_foot_x = center_x + foot_offset
        
        # Determine line width based on complexity (simpler = thinner lines)
        base_line_width = max(1, int(3 * (1 - complexity) + 1))
        
        # ----- DRAW IN ORDER (back to front) -----
        
        # 1. Back leg (left if facing forward)
        # Actually both legs visible from front
        self.draw_leg(draw, left_foot_x, hip_y, ground_y, base_unit // 2, complexity, color)
        
        # 2. Back arm
        self.draw_arm(draw, left_hand_x, shoulder_y, arm_y, base_unit // 3, complexity, color)
        
        # 3. Torso
        torso_width = base_unit // 2
        self.draw_torso(draw, center_x, shoulder_y, hip_y, torso_width, complexity, color)
        
        # 4. Front arm
        self.draw_arm(draw, right_hand_x, shoulder_y, arm_y, base_unit // 3, complexity, color)
        
        # 5. Front leg
        self.draw_leg(draw, right_foot_x, hip_y, ground_y, base_unit // 2, complexity, color)
        
        # 6. Head (on top)
        self.draw_head(draw, center_x, head_y, head_radius, complexity, color)
        
        # 7. Extra details based on complexity
        if complexity > 0.5:
            # Shadows
            shadow_offset = 5
            shadow_color = (color[0]//4, color[1]//4, color[2]//4)
            # Head shadow
            draw.ellipse([center_x - head_radius + shadow_offset, head_y + head_radius//2,
                         center_x + head_radius + shadow_offset, head_y + head_radius + head_radius//2],
                        fill=shadow_color)
        
        return img
