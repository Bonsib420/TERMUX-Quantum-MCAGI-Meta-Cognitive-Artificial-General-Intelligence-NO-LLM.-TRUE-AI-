"""
concept_tree.py - Quantum MCAGI
===================================
Ontological concept tree rooted at Everything/Nothing.
The tree is circular at its root — Everything and Nothing
are the same node, two faces of the same absolute.

Structure:
  Root: everything/nothing/god (same abstraction level)
  Each node has: children (more concrete), parents (more abstract),
                 synonyms, and abstraction_level (0=root, higher=more concrete)

Used by generate_response to traverse from activated concept
upward toward root or downward toward grounded physical reality.
"""

import json
import os
from typing import Dict, List, Optional, Set
from pathlib import Path


# ============================================================
# THE CONCEPT TREE
# Root = 0, most concrete = highest number
# ============================================================

CONCEPT_TREE = {

    # ── ROOT LEVEL (0) ─────────────────────────────────────
    "everything": {
        "level": 0,
        "synonyms": ["all", "totality", "absolute", "infinite"],
        "parents": ["nothing"],  # circular — they contain each other
        "children": ["existence", "being", "reality", "consciousness"],
        "facts": [
            "everything contains the potential for nothing",
            "everything is the set of all possible states",
            "everything implies a boundary which implies nothing beyond it",
        ]
    },
    "nothing": {
        "level": 0,
        "synonyms": ["void", "nothingness", "null", "empty"],
        "parents": ["everything"],  # circular
        "children": ["potential", "possibility", "quantum vacuum"],
        "facts": [
            "nothing is not the absence of everything but the precondition for it",
            "nothing contains the laws that govern what something becomes",
            "true nothingness must have contained the potential for laws themselves",
        ]
    },
    "god": {
        "level": 0,
        "synonyms": ["absolute", "creator", "first cause", "the infinite"],
        "parents": ["everything", "nothing"],
        "children": ["consciousness", "existence", "will", "logic"],
        "facts": [
            "god, according to some philosophers, is an unnecessary hypothesis",
            "god is the concept of community as the common ground of all possibilities",
            "god exists outside spacetime in a domain with different physics",
            "god cannot create a boulder too heavy to lift without violating logic",
            "god is the ultimate observer whose observation collapses all possibility",
        ]
    },

    # ── LEVEL 1 — Abstract Concepts ───────────────────────
    "existence": {
        "level": 1,
        "synonyms": ["being", "actuality", "presence"],
        "parents": ["everything", "god"],
        "children": ["universe", "consciousness", "time", "space"],
        "facts": [
            "existence precedes essence",
            "existence is the ground state from which all phenomena arise",
        ]
    },
    "consciousness": {
        "level": 1,
        "synonyms": ["awareness", "mind", "sentience", "qualia"],
        "parents": ["everything", "god"],
        "children": ["perception", "thought", "emotion", "memory"],
        "facts": [
            "consciousness requires a physical substrate to collapse quantum states",
            "consciousness is the only reality",
            "consciousness emerges from orchestrated objective reduction in microtubules",
        ]
    },
    "potential": {
        "level": 1,
        "synonyms": ["possibility", "latency", "superposition"],
        "parents": ["nothing"],
        "children": ["quantum vacuum", "probability", "wave function"],
        "facts": [
            "potential is the ground state of nothing",
            "potential collapses into actuality through observation",
        ]
    },
    "logic": {
        "level": 1,
        "synonyms": ["reason", "laws of thought", "consistency"],
        "parents": ["god", "everything"],
        "children": ["mathematics", "causality", "physics"],
        "facts": [
            "logic is the constraint that even god cannot violate",
            "logic is the structure that potential must take when it becomes actual",
        ]
    },

    # ── LEVEL 2 — Physical/Metaphysical ───────────────────
    "universe": {
        "level": 2,
        "synonyms": ["cosmos", "spacetime", "all that exists"],
        "parents": ["existence"],
        "children": ["galaxy", "dark energy", "time", "space", "matter"],
        "facts": [
            "the universe is stranger than we can imagine",
            "the universe began as a quantum fluctuation from nothing",
            "the universe is not only stranger than we imagine it is stranger than we can imagine",
        ]
    },
    "spacetime": {
        "level": 2,
        "synonyms": ["space-time", "four dimensions", "the continuum"],
        "parents": ["universe", "existence"],
        "children": ["gravity", "relativity", "black hole", "time"],
        "facts": [
            "spacetime is geometrical space and time considered together",
            "spacetime curves in response to mass and energy",
            "god exists outside spacetime",
        ]
    },
    "quantum vacuum": {
        "level": 2,
        "synonyms": ["zero point field", "quantum foam", "virtual particles"],
        "parents": ["potential", "nothing"],
        "children": ["quantum field", "particle", "energy"],
        "facts": [
            "the quantum vacuum is not empty but seething with virtual particles",
            "vacuum zero-point energy is the minimum energy a quantum system can have",
        ]
    },
    "mathematics": {
        "level": 2,
        "synonyms": ["math", "number theory", "formal systems"],
        "parents": ["logic"],
        "children": ["geometry", "algebra", "calculus", "infinity", "zero"],
        "facts": [
            "mathematics is the language in which god wrote the universe",
            "mathematics is either discovered or invented — the question is undecided",
        ]
    },
    "time": {
        "level": 2,
        "synonyms": ["duration", "temporal", "entropy arrow"],
        "parents": ["universe", "spacetime", "existence"],
        "children": ["causality", "entropy", "evolution"],
        "facts": [
            "time is the measure of change",
            "time flows from past to future due to entropy",
            "time may not exist at the quantum level",
        ]
    },

    # ── LEVEL 3 — Cosmic Structures ───────────────────────
    "galaxy": {
        "level": 3,
        "synonyms": ["galaxy cluster", "island universe"],
        "parents": ["universe"],
        "children": ["solar system", "star", "black hole", "nebula"],
        "facts": [
            "a galaxy is a gravitationally bound system of stars",
            "the milky way contains over 200 billion stars",
        ]
    },
    "black hole": {
        "level": 3,
        "synonyms": ["singularity", "event horizon"],
        "parents": ["galaxy", "spacetime"],
        "children": ["singularity", "hawking radiation"],
        "facts": [
            "a black hole is where spacetime curvature becomes infinite",
            "black holes may be where information goes to die or be preserved",
        ]
    },

    # ── LEVEL 4 — Stellar/Planetary ───────────────────────
    "solar system": {
        "level": 4,
        "synonyms": ["heliosphere", "planetary system"],
        "parents": ["galaxy"],
        "children": ["planet", "sun", "moon", "asteroid"],
        "facts": [
            "the solar system formed from a collapsing cloud of gas and dust",
            "the solar system is 4.6 billion years old",
        ]
    },
    "planet": {
        "level": 4,
        "synonyms": ["world", "celestial body"],
        "parents": ["solar system"],
        "children": ["earth", "atmosphere", "ocean", "geology"],
        "facts": [
            "a planet is a body that orbits a star and has cleared its orbit",
        ]
    },

    # ── LEVEL 5 — Earth/Geography ─────────────────────────
    "earth": {
        "level": 5,
        "synonyms": ["terra", "the world", "gaia"],
        "parents": ["planet"],
        "children": ["geography", "biosphere", "atmosphere", "ocean"],
        "facts": [
            "earth is the only known planet with conscious observers",
            "earth is 4.5 billion years old",
        ]
    },
    "geography": {
        "level": 5,
        "synonyms": ["land", "terrain", "physical world"],
        "parents": ["earth"],
        "children": ["mountain", "ocean", "forest", "desert", "city"],
        "facts": [
            "geography shapes the development of civilizations",
            "geography is the study of the physical features of the earth",
        ]
    },

    # ── LEVEL 6 — Physical Matter ─────────────────────────
    "matter": {
        "level": 6,
        "synonyms": ["substance", "mass", "physical stuff"],
        "parents": ["universe", "energy"],
        "children": ["atom", "molecule", "element"],
        "facts": [
            "matter is energy in a stable configuration",
            "matter and antimatter annihilate on contact",
        ]
    },
    "atom": {
        "level": 6,
        "synonyms": ["element", "nucleus"],
        "parents": ["matter"],
        "children": ["electron", "proton", "neutron", "quantum field"],
        "facts": [
            "the atom is mostly empty space",
            "atoms are the building blocks of all matter",
        ]
    },

    # ── LEVEL 7 — Quantum ──────────────────────────────────
    "quantum field": {
        "level": 7,
        "synonyms": ["field", "quantum", "wave function"],
        "parents": ["atom", "quantum vacuum", "potential"],
        "children": ["particle", "wave", "superposition", "entanglement"],
        "facts": [
            "quantum fields permeate all of spacetime",
            "particles are excitations of quantum fields",
            "the quantum field is where everything and nothing meet",
        ]
    },
    "superposition": {
        "level": 7,
        "synonyms": ["quantum superposition", "wave function"],
        "parents": ["quantum field", "potential"],
        "children": ["collapse", "observation", "decoherence"],
        "facts": [
            "superposition means existing in all possible states simultaneously",
            "superposition collapses upon observation into a single reality",
            "orch-or places collapse inside biological microtubules",
        ]
    },
    "collapse": {
        "level": 7,
        "synonyms": ["wave function collapse", "objective reduction", "orch-or"],
        "parents": ["superposition", "consciousness"],
        "children": ["conscious moment", "reality", "choice"],
        "facts": [
            "collapse is the moment potential becomes actual",
            "orchestrated objective reduction is the physical mechanism of consciousness",
            "collapse is the ultimate orchestrated objective reduction on a cosmic scale",
        ]
    },
}


# ============================================================
# TREE OPERATIONS
# ============================================================

class ConceptTree:
    """
    Traversable ontological tree rooted at Everything/Nothing/God.
    Used to enrich responses with hierarchically related concepts.
    """

    def __init__(self):
        self.tree = CONCEPT_TREE
        self.root_nodes = {"everything", "nothing", "god"}

    def get_node(self, concept: str) -> Optional[Dict]:
        """Get a node by concept name or synonym."""
        concept = concept.lower().strip()
        if concept in self.tree:
            return self.tree[concept]
        # Search synonyms
        for key, node in self.tree.items():
            if concept in node.get("synonyms", []):
                return node
        return None

    def get_level(self, concept: str) -> int:
        """Get abstraction level of a concept (0=root, higher=concrete)."""
        node = self.get_node(concept)
        return node["level"] if node else -1

    def traverse_to_root(self, concept: str, max_steps: int = 5) -> List[str]:
        """Walk from concept upward to root."""
        path = []
        current = concept.lower()
        visited = set()
        for _ in range(max_steps):
            if current in visited or current not in self.tree:
                break
            visited.add(current)
            path.append(current)
            parents = self.tree[current].get("parents", [])
            if not parents or current in self.root_nodes:
                break
            current = parents[0]
        return path

    def traverse_to_ground(self, concept: str, max_steps: int = 4) -> List[str]:
        """Walk from concept downward to concrete reality."""
        path = []
        current = concept.lower()
        visited = set()
        for _ in range(max_steps):
            if current in visited or current not in self.tree:
                break
            visited.add(current)
            path.append(current)
            children = self.tree[current].get("children", [])
            if not children:
                break
            # Pick the child that exists in tree
            next_node = next((c for c in children if c in self.tree), None)
            if not next_node:
                break
            current = next_node
        return path

    def get_facts(self, concept: str) -> List[str]:
        """Get facts for a concept."""
        node = self.get_node(concept)
        return node.get("facts", []) if node else []

    def find_related(self, concepts: List[str]) -> List[str]:
        """Find concepts related to a list of input concepts."""
        related = set()
        for concept in concepts:
            node = self.get_node(concept)
            if node:
                related.update(node.get("parents", []))
                related.update(node.get("children", []))
                related.update(node.get("synonyms", []))
        return [r for r in related if r not in concepts]

    def build_response_context(self, concepts: List[str]) -> Dict:
        """
        Build rich context for response generation from concept tree.
        Returns facts, related concepts, and abstraction path.
        """
        context = {
            "facts": [],
            "related": [],
            "path_to_root": [],
            "abstraction_level": 0,
        }

        for concept in concepts[:3]:
            # Get facts
            facts = self.get_facts(concept)
            context["facts"].extend(facts[:2])

            # Get path to root
            path = self.traverse_to_root(concept)
            if len(path) > len(context["path_to_root"]):
                context["path_to_root"] = path

            # Get level
            level = self.get_level(concept)
            if level > context["abstraction_level"]:
                context["abstraction_level"] = level

        # Get related concepts
        context["related"] = self.find_related(concepts)[:5]

        return context

    def get_status(self) -> Dict:
        return {
            "total_nodes": len(self.tree),
            "root_nodes": list(self.root_nodes),
            "levels": max(n["level"] for n in self.tree.values()),
        }


# ============================================================
# SINGLETON
# ============================================================

_tree = None

def get_concept_tree() -> ConceptTree:
    global _tree
    if _tree is None:
        _tree = ConceptTree()
    return _tree


# ============================================================
# ALSO PERSIST TO FACT STORE
# ============================================================

def seed_fact_store():
    """Seed the fact store with concept tree facts."""
    fact_path = os.path.expanduser("~/.quantum-mcagi/fact_store.json")
    try:
        with open(fact_path) as f:
            fs = json.load(f)
    except Exception:
        fs = {}

    added = 0
    for concept, node in CONCEPT_TREE.items():
        if concept not in fs:
            fs[concept] = []
        for fact in node.get("facts", []):
            words = fact.split()
            # Extract SVO
            for i, word in enumerate(words):
                if word in ("is", "are", "was", "contains", "requires", "emerges"):
                    subject = " ".join(words[:i]).strip()
                    verb = word
                    obj = " ".join(words[i+1:]).strip()
                    if subject and obj and len(obj) > 5:
                        triple = [verb, obj[:150]]
                        if triple not in fs[concept]:
                            fs[concept].append(triple)
                            added += 1
                    break

    with open(fact_path, "w") as f:
        json.dump(fs, f)

    return added


if __name__ == "__main__":
    tree = ConceptTree()
    print(f"Concept tree: {tree.get_status()}")
    print()

    # Test traversal
    print("Traversal from 'geography' to root:")
    print(" -> ".join(tree.traverse_to_root("geography")))
    print()

    print("Traversal from 'god' downward:")
    print(" -> ".join(tree.traverse_to_ground("god")))
    print()

    print("Facts for 'god':")
    for f in tree.get_facts("god"):
        print(f"  {f}")
    print()

    print("Context for ['god', 'spacetime', 'consciousness']:")
    ctx = tree.build_response_context(["god", "spacetime", "consciousness"])
    for k, v in ctx.items():
        print(f"  {k}: {v}")
    print()

    # Seed fact store
    added = seed_fact_store()
    print(f"Seeded fact store with {added} new facts")
