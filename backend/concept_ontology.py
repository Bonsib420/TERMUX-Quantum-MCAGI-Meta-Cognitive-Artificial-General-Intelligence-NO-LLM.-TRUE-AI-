"""
🧠 CONCEPT ONTOLOGY
The knowledge base of Quantum MCAGI's understanding of the world.
Maps concepts to physical parameters, rendering strategies, and complexity.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class RenderingStrategy(Enum):
    """How to render this concept."""
    BLACK_HOLE = "black_hole"
    HUMAN_FIGURE = "human_figure"
    GEOMETRIC = "geometric"
    PARTICLE_SYSTEM = "particle_system"
    COMPOSITE = "composite"


class PhysicalProperty(Enum):
    """Types of physical properties a concept can have."""
    MASS = "mass"
    RADIUS = "radius"
    POSITION = "position"
    ORIENTATION = "orientation"
    TEMPERATURE = "temperature"
    SPIN = "spin"
    CHARGE = "charge"
    COLOR = "color"
    TEXTURE = "texture"
    LUMINOSITY = "luminosity"


@dataclass
class ConceptDefinition:
    """
    Complete definition of a concept in the ontology.
    This is what the AI "knows" about each concept.
    """
    name: str
    category: str  # e.g., "astrophysical", "biological", "geometric"
    base_complexity: float  # 0.0 (easiest) to 1.0 (hardest)
    
    # Rendering strategy
    strategy: RenderingStrategy
    
    # Physical parameters (with ranges for variability)
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # Example: {
    #   "mass": {"type": "float", "min": 1.0, "max": 100.0, "units": "solar_masses", "default": 10.0},
    #   "spin": {"type": "float", "min": 0.0, "max": 0.99, "default": 0.5}
    # }
    
    # Visual properties
    visual_properties: Dict[str, Any] = field(default_factory=dict)
    # Example: {
    #   "color_palette": ["black", "orange", "yellow"],
    #   "glow_intensity": 0.8,
    #   "requires_lighting": True
    # }
    
    # What sub-components does this concept have?
    components: List[Dict[str, Any]] = field(default_factory=list)
    # Example: [
    #   {"name": "event_horizon", "type": "circle", "z_index": 0},
    #   {"name": "accretion_disk", "type": "ring", "z_index": 1}
    # ]
    
    # Complexity scaling: how detail increases with complexity parameter
    detail_functions: Dict[str, str] = field(default_factory=dict)
    # Example: {
    #   "num_particles": "int(100 + 900 * complexity)",
    #   "ring_segments": "int(10 + 40 * complexity)"
    # }
    
    # Required physics engines
    physics_engines: List[str] = field(default_factory=list)
    
    # Dependencies: other concepts needed to understand this one
    prerequisites: List[str] = field(default_factory=list)


class ConceptOntology:
    """
    The master knowledge base.
    Contains all concepts the AI understands with their complete definitions.
    """
    
    def __init__(self):
        self._concepts: Dict[str, ConceptDefinition] = {}
        self._initialize_concepts()
    
    def _initialize_concepts(self):
        """Build the complete ontology tree."""
        
        # ============================================
        # BLACK HOLE (complexity 1.0 - HARDEST)
        # ============================================
        black_hole = ConceptDefinition(
            name="black hole",
            category="astrophysical",
            base_complexity=1.0,
            strategy=RenderingStrategy.BLACK_HOLE,
            parameters={
                "mass": {"type": "float", "min": 5.0, "max": 1000.0, "units": "solar_masses", "default": 50.0},
                "spin": {"type": "float", "min": 0.0, "max": 0.998, "default": 0.5},
                "charge": {"type": "float", "min": 0.0, "max": 1.0, "default": 0.0},
                "orientation": {"type": "vector3d", "default": [0, 0, 1]},
            },
            visual_properties={
                "color_palette": ["black", "orange", "yellow", "white", "blue"],
                "event_horizon_color": (0, 0, 0),
                "photon_sphere_color": (255, 255, 220),
                "accretion_disk_colors": [(255, 255, 200), (255, 200, 50), (255, 100, 0), (200, 50, 0)],
                "jet_color": (100, 150, 255),
                "glow_intensity": 0.9,
            },
            components=[
                {"name": "singularity", "type": "point", "radius": 0, "z_index": 0},
                {"name": "event_horizon", "type": "circle", "z_index": 1},
                {"name": "photon_sphere", "type": "ring", "z_index": 2},
                {"name": "accretion_disk", "type": "torus", "z_index": 3},
                {"name": "gravitational_lensing", "type": "effect", "z_index": 4},
                {"name": "relativistic_jets", "type": "cones", "z_index": 5},
            ],
            detail_functions={
                "disk_rings": "int(15 + 20 * complexity)",
                "lensing_stars": "int(40 + 80 * complexity)",
                "jet_particles": "int(20 + 40 * complexity)",
                "ring_segments": "int(30 + 50 * complexity)",
            },
            physics_engines=["general_relativity_raytracing", "magnetohydrodynamics"],
            prerequisites=["gravity", "spacetime"]
        )
        self._concepts["black hole"] = black_hole
        
        # ============================================
        # STICK FIGURE (complexity 0.05 - EASIEST)
        # ============================================
        stick_figure = ConceptDefinition(
            name="stick figure",
            category="biological",
            base_complexity=0.05,
            strategy=RenderingStrategy.HUMAN_FIGURE,
            parameters={
                "height": {"type": "float", "min": 0.5, "max": 2.0, "units": "m", "default": 1.0},
                "pose": {"type": "string", "options": ["standing", "walking", "t-pose"], "default": "standing"},
                "simplicity": {"type": "float", "min": 0.0, "max": 1.0, "default": 0.9},
            },
            visual_properties={
                "color_palette": ["white", "gray", "light_gray"],
                "line_width_base": 3,
                "joint_size": 5,
                "requires_anatomy": False,
            },
            components=[
                {"name": "head", "type": "circle", "parent": "torso", "z_index": 0},
                {"name": "torso", "type": "line", "z_index": 1},
                {"name": "arms", "type": "limbs", "count": 2, "z_index": 2},
                {"name": "legs", "type": "limbs", "count": 2, "z_index": 3},
            ],
            detail_functions={
                "joint_detail": "int(1 + 4 * complexity)",  # 1=simple circle, 5=detailed joint
                "finger_segments": "int(0 + 3 * complexity)",
                "foot_detail": "int(1 + 4 * complexity)",
                "muscle_definition": "complexity * 0.3",
            },
            physics_engines=["forward_kinematics"],
            prerequisites=[]
        )
        self._concepts["stick figure"] = stick_figure
        
        # ============================================
        # HUMAN (complexity 0.2)
        # ============================================
        human = ConceptDefinition(
            name="human",
            category="biological",
            base_complexity=0.2,
            strategy=RenderingStrategy.HUMAN_FIGURE,
            parameters={
                "height": {"type": "float", "min": 1.4, "max": 2.0, "units": "m", "default": 1.75},
                "gender": {"type": "string", "options": ["male", "female"], "default": "person"},
                "body_type": {"type": "string", "options": ["athletic", "average", "slim"], "default": "average"},
            },
            visual_properties={
                "color_palette": [(255, 200, 150), (200, 160, 100)],
                "skin_tone": (210, 180, 140),
                "line_width_base": 3,
                "requires_anatomy": True,
            },
            components=[
                {"name": "head", "type": "oval", "parent": "neck", "z_index": 0},
                {"name": "neck", "type": "line", "z_index": 1},
                {"name": "torso", "type": "shape", "z_index": 2},
                {"name": "arms", "type": "limbs", "count": 2, "z_index": 3},
                {"name": "legs", "type": "limbs", "count": 2, "z_index": 4},
            ],
            detail_functions={
                "muscle_definition": "complexity * 0.5",
                "facial_features": "complexity > 0.3",
                "hair_detail": "complexity * 0.4",
                "clothing": "complexity > 0.5",
            },
            physics_engines=["forward_kinematics", "muscle_simulation"],
            prerequisites=["stick figure"]
        )
        self._concepts["human"] = human
        
        # ============================================
        # GRAVITY WAVE (complexity 0.6)
        # ============================================
        gravity_wave = ConceptDefinition(
            name="gravity wave",
            category="physical",
            base_complexity=0.6,
            strategy=RenderingStrategy.PARTICLE_SYSTEM,
            parameters={
                "amplitude": {"type": "float", "min": 0.1, "max": 1.0, "default": 0.5},
                "frequency": {"type": "float", "min": 0.1, "max": 5.0, "default": 1.0},
                "wavelength": {"type": "float", "min": 10, "max": 200, "default": 100},
            },
            visual_properties={
                "color_palette": [(100, 150, 255), (150, 100, 255)],
                "line_width": 2,
                "opacity": 0.7,
            },
            components=[
                {"name": "wave_front", "type": "curve", "z_index": 0},
                {"name": "particles", "type": "particles", "count": 100, "z_index": 1},
            ],
            detail_functions={
                "num_waves": "int(3 + 7 * complexity)",
                "particle_count": "int(50 + 450 * complexity)",
                "wave_segments": "int(20 + 80 * complexity)",
            },
            physics_engines=["wave_propagation"],
            prerequisites=[]
        )
        self._concepts["gravity wave"] = gravity_wave
        
        # ============================================
        # QUANTUM (complexity 0.5)
        # ============================================
        quantum = ConceptDefinition(
            name="quantum",
            category="abstract",
            base_complexity=0.5,
            strategy=RenderingStrategy.PARTICLE_SYSTEM,
            parameters={
                "superposition_states": {"type": "int", "min": 2, "max": 8, "default": 4},
                "entanglement": {"type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
                "uncertainty": {"type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
            },
            visual_properties={
                "color_palette": [(0, 255, 0), (255, 0, 255), (0, 255, 255), (255, 255, 0)],
                "particle_size_range": [2, 6],
                "glow_intensity": 0.6,
            },
            components=[
                {"name": "probability_cloud", "type": "blob", "z_index": 0},
                {"name": "wave_function", "type": "lines", "z_index": 1},
                {"name": "particles", "type": "particles", "count": 200, "z_index": 2},
            ],
            detail_functions={
                "cloud_points": "int(100 + 900 * complexity)",
                "wave_lines": "int(20 + 80 * complexity)",
                "entanglement_links": "int(0 + 15 * complexity)",
            },
            physics_engines=["wave_function_visualization"],
            prerequisites=[]
        )
        self._concepts["quantum"] = quantum
        
        # Add more foundational concepts
        self._add_foundational_concepts()
        
        # Add default fallback concept
        default_concept = ConceptDefinition(
            name="default",
            category="abstract",
            base_complexity=0.3,
            strategy=RenderingStrategy.GEOMETRIC,
            parameters={},
            visual_properties={"color_palette": [(100, 150, 200), (150, 100, 200)]},
            components=[],
            detail_functions={},
            physics_engines=[],
            prerequisites=[]
        )
        self._concepts["default"] = default_concept
    
    def _add_foundational_concepts(self):
        """Add simple geometric and foundational concepts."""
        foundational = [
            ("circle", "geometric", 0.0, "GEOMETRIC", {"radius": {"min": 10, "max": 100, "default": 50}}),
            ("line", "geometric", 0.0, "GEOMETRIC", {"length": {"min": 50, "max": 200, "default": 100}}),
            ("point", "geometric", 0.0, "GEOMETRIC", {}),
            ("wave", "physical", 0.4, "PARTICLE_SYSTEM", {"amplitude": {"min": 5, "max": 50, "default": 20}}),
            ("field", "physical", 0.45, "PARTICLE_SYSTEM", {"field_strength": {"min": 0.1, "max": 1.0, "default": 0.5}}),
            ("pattern", "abstract", 0.35, "GEOMETRIC", {}),
        ]
        
        for name, category, complexity, strategy, params in foundational:
            concept = ConceptDefinition(
                name=name,
                category=category,
                base_complexity=complexity,
                strategy=RenderingStrategy[strategy],
                parameters=params,
                visual_properties={"color_palette": [(255, 255, 255)]},
                components=[{"name": name, "type": "primitive", "z_index": 0}],
                detail_functions={},
                physics_engines=[],
                prerequisites=[]
            )
            self._concepts[name] = concept
    
    def get_concept(self, name: str) -> Optional[ConceptDefinition]:
        """Retrieve a concept definition by name (fuzzy matching)."""
        name_lower = name.lower().strip()
        
        # Exact match
        if name_lower in self._concepts:
            return self._concepts[name_lower]
        
        # Partial match
        for concept_name in self._concepts:
            if name_lower in concept_name or concept_name in name_lower:
                return self._concepts[concept_name]
        
        return None
    
    def get_complexity(self, concept_name: str, override: Optional[float] = None) -> float:
        """Get complexity for a concept, optionally with override."""
        concept = self.get_concept(concept_name)
        if concept:
            return override if override is not None else concept.base_complexity
        return 0.3  # default
    
    def list_concepts(self) -> List[str]:
        """List all known concepts."""
        return list(self._concepts.keys())
    
    def get_prerequisites(self, concept_name: str) -> List[str]:
        """Get prerequisite concepts needed to understand this one."""
        concept = self.get_concept(concept_name)
        if concept:
            return concept.prerequisites
        return []


# Global ontology instance
_ontology: Optional[ConceptOntology] = None


def get_ontology() -> ConceptOntology:
    """Get or create the global ontology."""
    global _ontology
    if _ontology is None:
        _ontology = ConceptOntology()
    return _ontology
