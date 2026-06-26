#!/usr/bin/env python3
"""
Quantum MCAGI -- Local Chat (Termux)
Standalone chat interface. No MongoDB, no FastAPI, no server.
Runs the real communication engine directly in your terminal.

Usage:
    python chat.py
    python chat.py --verbose     (show debug info per response)

Commands:
    /status       - Full system status
    /learn FILE   - Feed text to Markov chain
    /save         - Save all state to disk
    /load         - Load saved state
    /reset        - Reset the engine
    /hybrid TEXT  - Direct hybrid quantum generation
    /unified TEXT - Direct word-by-word generation
    /analyze TEXT - Text analysis
    /personality  - Show personality profile
    /knowledge X  - Look up a topic
    /collapse X   - Show semantic collapse
    /feed [CAT]   - Batch-fetch URLs from research_feeds.json (or /feed all)
    /export       - Export full conversation as markdown (file + terminal)
    /copy-last    - Print last AI response in a bordered box for easy copy
    /cloud-save   - Push brain state to Google Drive via rclone
    /cloud-load   - Pull brain state from Google Drive via rclone
    /cloud-status - Show cloud sync status
    /backup       - Full brain backup to cloud
    /quit         - Save and exit
"""

import sys
import os
import json
import time
try:
    from brain_lateralization import BrainLateralization
except ImportError:
    BrainLateralization = None
from flask import Flask, request, jsonify
from datetime import datetime
from typing import Dict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quantum_language_engine import QuantumLanguageEngine
try:
    from evaluation_engine import get_evaluation_engine
    HAS_EVAL = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_EVAL = False
try:
    HAS_ADVANCED = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_ADVANCED = False
try:
    from exam_system import ExamRunner, IntakeTracker, detect_domain
    HAS_EXAM = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_EXAM = False
try:
    from self_evolution import SelfEvolutionEngine
    HAS_EVOLUTION = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_EVOLUTION = False

try:
    from document_engine import handle_ingest_command, ingest_document as fetch_url
    HAS_INGEST = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_INGEST = False

try:
    from self_research import SelfResearchEngine
    HAS_RESEARCH = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_RESEARCH = False

try:
    from cloud_brain import CloudBrain
    HAS_CLOUD = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_CLOUD = False

try:
    from code_engine import get_code_engine
    HAS_CODE = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_CODE = False

# Optional imports -- degrade gracefully
try:
    from hybrid_generator import HybridGenerator
    HAS_HYBRID = True
    def create_hybrid_generator(engine):
                    return HybridGenerator(engine.markov, engine.tfidf, engine.orch_or)
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_HYBRID = False
    def create_hybrid_generator(engine):
        return None


try:
    HAS_UNIFIED = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_UNIFIED = False

try:
    from quote_engine import get_quote_engine
    HAS_QUOTES = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_QUOTES = False

try:
    from personality_engine import get_personality_engine
    HAS_PERSONALITY = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_PERSONALITY = False

try:
    from knowledge_base import get_knowledge_base
    HAS_KNOWLEDGE = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_KNOWLEDGE = False

try:
    from text_analyzer import get_text_analyzer
    HAS_ANALYZER = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_ANALYZER = False

try:
    from semantic_collapse_engine import SemanticCollapseEngine
    HAS_COLLAPSE = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_COLLAPSE = False

try:
    from tone_detector import detect_tone
    HAS_TONE = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_TONE = False

try:
    HAS_LIBRARY = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_LIBRARY = False

try:
    from cistercian_math import detect_math, evaluate_math, format_math_response, render_cistercian_ascii
    HAS_CISTERCIAN_MATH = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_CISTERCIAN_MATH = False

try:
    from quantum_memory import get_quantum_memory, reset_quantum_memory, PENNYLANE_QRAM_AVAILABLE
    HAS_QRAM = True
except Exception as _e:
    print(f"INGEST ERROR: {_e}")
    HAS_QRAM = False
    PENNYLANE_QRAM_AVAILABLE = False


class LocalMemory:
    """JSON-file backed memory for local chat."""

    # Lightweight domain classifier -- maps keywords to knowledge domains.
    # Used to populate concept metadata so distinct_domains count works
    # and growth stages can advance.
    DOMAIN_KEYWORDS = {
        'philosophy': {
            'consciousness', 'existence', 'reality', 'being', 'truth', 'meaning',
            'ethics', 'morality', 'epistemology', 'ontology', 'metaphysics',
            'philosophy', 'wisdom', 'virtue', 'existential', 'phenomenology',
            'dialectic', 'dualism', 'determinism', 'nihilism', 'stoicism',
            'mind', 'soul', 'free', 'will', 'perception', 'reason',
        },
        'physics': {
            'quantum', 'particle', 'wave', 'energy', 'mass', 'gravity',
            'spacetime', 'relativity', 'photon', 'electron', 'proton',
            'entropy', 'thermodynamics', 'superposition', 'entanglement',
            'collapse', 'wavefunction', 'momentum', 'force', 'field',
            'atom', 'nuclear', 'cosmology', 'universe', 'dimension',
            'electromagnetic', 'radiation', 'frequency', 'wavelength',
        },
        'computer_science': {
            'algorithm', 'computer', 'programming', 'software', 'code',
            'data', 'network', 'artificial', 'intelligence', 'machine',
            'learning', 'neural', 'computation', 'binary', 'digital',
            'encryption', 'database', 'internet', 'processor', 'memory',
        },
        'biology': {
            'cell', 'dna', 'gene', 'protein', 'evolution', 'organism',
            'species', 'ecology', 'neuron', 'brain', 'mitochondria',
            'biological', 'genome', 'mutation', 'adaptation', 'life',
            'microtubule', 'tubulin', 'synapse', 'enzyme', 'metabolism',
        },
        'mathematics': {
            'number', 'equation', 'theorem', 'proof', 'geometry', 'algebra',
            'calculus', 'infinity', 'set', 'function', 'variable',
            'probability', 'statistics', 'matrix', 'vector', 'topology',
            'prime', 'factorial', 'logarithm', 'integral', 'derivative',
        },
        'psychology': {
            'emotion', 'behavior', 'cognition', 'personality', 'motivation',
            'anxiety', 'depression', 'therapy', 'unconscious', 'trauma',
            'empathy', 'attachment', 'identity', 'perception', 'memory',
            'habit', 'stress', 'dream', 'instinct', 'desire',
        },
        'language': {
            'word', 'language', 'grammar', 'syntax', 'semantics', 'meaning',
            'communication', 'expression', 'metaphor', 'narrative', 'symbol',
            'translation', 'dialect', 'vocabulary', 'discourse', 'rhetoric',
        },
    }

    @classmethod
    def _classify_domain(cls, concept: str) -> str:
        """Classify a concept into a knowledge domain via keyword matching."""
        c = concept.lower()
        best_domain = ''
        best_score = 0
        for domain, keywords in cls.DOMAIN_KEYWORDS.items():
            if c in keywords:
                return domain
            # Partial match: concept is substring of keyword or vice versa
            score = sum(1 for kw in keywords if kw in c or c in kw)
            if score > best_score:
                best_score = score
                best_domain = domain
        return best_domain if best_score > 0 else 'general'

    # All 12 tracks must be met simultaneously to advance.
    # High watermark protection on diameter and avg_degree -- earned progress never regresses.
    GROWTH_STAGES = [
        {"stage": 0, "name": "Nascent", "threshold": {
            "connections": 0, "concepts": 0, "min_avg_degree": 0, "min_diameter": 0, "min_domains": 0,
            "min_markov_states": 0, "min_transitions": 0, "min_comm_score": 0,
            "min_questions": 0, "min_insights": 0, "min_interactions": 0
        }},
        {"stage": 1, "name": "Curious", "threshold": {
            "connections": 50, "concepts": 20, "min_avg_degree": 1.5, "min_diameter": 3, "min_domains": 3,
            "min_markov_states": 5000, "min_transitions": 10000, "min_comm_score": 15,
            "min_questions": 50, "min_insights": 10, "min_interactions": 25
        }},
        {"stage": 2, "name": "Inquisitive", "threshold": {
            "connections": 200, "concepts": 50, "min_avg_degree": 2.5, "min_diameter": 6, "min_domains": 6,
            "min_markov_states": 20000, "min_transitions": 80000, "min_comm_score": 25,
            "min_questions": 200, "min_insights": 50, "min_interactions": 100
        }},
        {"stage": 3, "name": "Understanding", "threshold": {
            "connections": 500, "concepts": 100, "min_avg_degree": 3.5, "min_diameter": 8, "min_domains": 10,
            "min_markov_states": 100000, "min_transitions": 400000, "min_comm_score": 35,
            "min_questions": 500, "min_insights": 150, "min_interactions": 300
        }},
        {"stage": 4, "name": "Philosophical", "threshold": {
            "connections": 1500, "concepts": 200, "min_avg_degree": 5.0, "min_diameter": 12, "min_domains": 15,
            "min_markov_states": 400000, "min_transitions": 1500000, "min_comm_score": 50,
            "min_questions": 1000, "min_insights": 400, "min_interactions": 750
        }},
        {"stage": 5, "name": "Theory Building", "threshold": {
            "connections": 4000, "concepts": 350, "min_avg_degree": 7.0, "min_diameter": 16, "min_domains": 20,
            "min_markov_states": 800000, "min_transitions": 3000000, "min_comm_score": 65,
            "min_questions": 2500, "min_insights": 1000, "min_interactions": 2000
        }},
        {"stage": 6, "name": "Transcendent", "threshold": {
            "connections": 10000, "concepts": 600, "min_avg_degree": 10.0, "min_diameter": 20, "min_domains": 30,
            "min_markov_states": 1500000, "min_transitions": 6000000, "min_comm_score": 80,
            "min_questions": 6000, "min_insights": 3000, "min_interactions": 5000
        }}
    ]

    def __init__(self, data_dir="~/.quantum-mcagi"):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.conversations = self._load("conversations.json", [])
        self.concepts = self._load("concepts.json", {})
        # Ensure concepts have relationships field
        for c in self.concepts:
            if "relationships" not in self.concepts[c]:
                self.concepts[c]["relationships"] = []
        self.growth = self._load("growth.json", {
            "stage": 0, "name": "Nascent",
            "total_interactions": 0,
            "total_concepts": 0,
            "total_connections": 0,
            "total_questions_asked": 0,
            "total_insights": 0,
        })
        # High watermark protection -- earned topology progress never regresses
        self._hwm_avg_degree = self.growth.get("hwm_avg_degree", 0.0)
        self._hwm_diameter = self.growth.get("hwm_diameter", 0)
        # Ensure advancement tracking field exists
        if "last_recorded_stage" not in self.growth:
            self.growth["last_recorded_stage"] = self.growth.get("stage", 0)
        self.session_state = self._load("session_state.json", {
            "total_sessions": 0,
            "total_lifetime_interactions": 0,
        })
        self.session_state["total_sessions"] = self.session_state.get("total_sessions", 0) + 1

    def _load(self, filename, default):
        filepath = self.data_dir / filename
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return default
        return default

    def _save(self, filename, data):
        filepath = self.data_dir / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def save_all(self):
        self._save("conversations.json", self.conversations[-500:])
        self._save("concepts.json", self.concepts)
        self._save("growth.json", self.growth)
        self._save("session_state.json", self.session_state)

    def save_orch_or(self, orch_or):
        if orch_or:
            self._save("orch_or_state.json", {
                "conscious_moments": orch_or.total_moments,
            })

    def load_orch_or(self, orch_or):
        if orch_or:
            data = self._load("orch_or_state.json", {})
            orch_or.total_moments = data.get("conscious_moments", 0)

    def add_exchange(self, user_input, response, concepts, questions):
        self.conversations.append({
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "ai": response,
            "concepts": concepts,
            "questions": questions,
        })
        self.growth["total_interactions"] += 1
        if hasattr(self, "_engine_ref") and hasattr(self._engine_ref, "markov"):
            self.growth["markov_states"] = len(self._engine_ref.markov.chain)
            self.growth["markov_transitions"] = self._engine_ref.markov.total_tokens
        self.growth["total_questions_asked"] += len(questions)
        self.session_state["total_lifetime_interactions"] = self.session_state.get(
            "total_lifetime_interactions", 0) + 1

        # Track new concepts and ensure relationships field + domain metadata
        for c in concepts:
            c_lower = c.lower()
            if c_lower in self.concepts:
                self.concepts[c_lower]["count"] += 1
                self.concepts[c_lower]["strength"] = min(10.0, self.concepts[c_lower]["strength"] + 0.1)
                # Back-fill domain metadata for concepts that predate this fix
                if "metadata" not in self.concepts[c_lower]:
                    self.concepts[c_lower]["metadata"] = {
                        "domain": self._classify_domain(c_lower)
                    }
            else:
                domain = self._classify_domain(c_lower)
                self.concepts[c_lower] = {
                    "count": 1,
                    "strength": 1.0,
                    "first_seen": datetime.now().isoformat(),
                    "relationships": [],
                    "metadata": {"domain": domain}
                }
                self.growth["total_concepts"] += 1

        # Create relationships between co-occurring concepts in this input
        # This builds the semantic graph: all concepts mentioned together become connected
        concepts_lower = [c.lower() for c in concepts]
        for i in range(len(concepts_lower)):
            for j in range(i+1, len(concepts_lower)):
                c1, c2 = concepts_lower[i], concepts_lower[j]
                if c1 != c2 and c1 in self.concepts and c2 in self.concepts:
                    # Add c2 to c1's relationships if not already present
                    if c2 not in self.concepts[c1]["relationships"]:
                        self.concepts[c1]["relationships"] = list(self.concepts[c1].get("relationships", [])) if isinstance(self.concepts[c1].get("relationships"), dict) else self.concepts[c1].get("relationships", []); self.concepts[c1]["relationships"].append(c2)
                    # Add c1 to c2's relationships (undirected graph)
                    rels2 = self.concepts[c2].get("relationships", [])
                    if isinstance(rels2, dict): rels2 = list(rels2.keys())
                    if c1 not in rels2:
                        rels2.append(c1)
                        self.concepts[c2]["relationships"] = rels2

        # Detect insights: response mentions 2+ known concepts
        if isinstance(response, list):
            response = " ".join(map(str, response))

        from response_contract import normalize_response
        response = normalize_response(response)
        response_lower = response.lower()

        known_in_response = [cn for cn in self.concepts if cn in response_lower]
        if len(known_in_response) >= 2:
            self.growth["total_insights"] += 1

        self._check_stage_advancement()


    def count_connections(self) -> int:
        """Count unique undirected relationships between concepts."""
        edges = set()
        for concept, data in self.concepts.items():
            for rel in data.get("relationships", []):
                if rel in self.concepts:
                    edge = frozenset([concept.lower(), rel.lower()])
                    edges.add(edge)
        return len(edges)

    def check_graph_topology(self) -> Dict:
        """Analyze local concept graph structure."""
        graph = {c: data.get("relationships", []) for c, data in self.concepts.items()}
        if not graph:
            return {"node_count": 0, "edge_count": 0, "avg_degree": 0, "diameter": 0, "largest_component_ratio": 0, "component_count": 0}

        # Degrees
        degrees = [len(rels) for rels in graph.values()]
        total_nodes = len(graph)
        total_edges = sum(degrees)
        avg_degree = total_edges / total_nodes if total_nodes else 0

        # Connected components (BFS)
        def bfs(start):
            visited = set()
            queue = [start]
            while queue:
                node = queue.pop(0)
                if node not in visited:
                    visited.add(node)
                    for neighbor in graph.get(node, []):
                        if neighbor in graph and neighbor not in visited:
                            queue.append(neighbor)
            return visited

        visited_all = set()
        components = []
        for node in graph:
            if node not in visited_all:
                comp = bfs(node)
                visited_all.update(comp)
                components.append(comp)

        largest = max(components, key=len) if components else set()
        largest_ratio = len(largest) / total_nodes if total_nodes else 0

        # Diameter (sample from largest component)
        diameter = 0
        if len(largest) > 1:
            sample = list(largest)[:5]
            for start in sample:
                dist = {start: 0}
                queue = [start]
                while queue:
                    cur = queue.pop(0)
                    for nb in graph.get(cur, []):
                        if nb in largest and nb not in dist:
                            dist[nb] = dist[cur] + 1
                            queue.append(nb)
                if dist:
                    diameter = max(diameter, max(dist.values()))

        return {
            "node_count": total_nodes,
            "edge_count": total_edges,
            "avg_degree": round(avg_degree, 2),
            "diameter": diameter,
            "largest_component_ratio": round(largest_ratio, 3),
            "component_count": len(components)
        }

    def _identify_limiting_factor(self, metrics, topology, next_thresh):
        checks = [
            ("connections", metrics.get("total_connections", 0) / max(next_thresh["connections"], 1)),
            ("concepts", metrics.get("total_concepts", 0) / max(next_thresh["concepts"], 1)),
            ("avg_degree", self._hwm_avg_degree / max(next_thresh.get("min_avg_degree", 1), 0.1)),
            ("diameter", self._hwm_diameter / max(next_thresh.get("min_diameter", 1), 1)),
            ("domains", metrics.get("distinct_domains", 0) / max(next_thresh.get("min_domains", 1), 1)),
            ("markov_states", metrics.get("markov_states", 0) / max(next_thresh.get("min_markov_states", 1), 1)),
            ("transitions", metrics.get("transitions", 0) / max(next_thresh.get("min_transitions", 1), 1)),
            ("comm_score", metrics.get("comm_score", 0) / max(next_thresh.get("min_comm_score", 1), 1)),
            ("questions", metrics.get("total_questions", 0) / max(next_thresh.get("min_questions", 1), 1)),
            ("insights", metrics.get("total_insights", 0) / max(next_thresh.get("min_insights", 1), 1)),
            ("interactions", metrics.get("total_interactions", 0) / max(next_thresh.get("min_interactions", 1), 1))
        ]
        limiting = min(checks, key=lambda x: x[1])
        return limiting[0]

    def get_current_stage(self):
        """Compute current growth stage from all 12 metric tracks.
        High watermark protection on diameter and avg_degree -- earned progress never regresses."""
        metrics = {
            "total_concepts": self.growth.get("total_concepts", 0),
            "total_connections": self.count_connections(),
            "total_questions": self.growth.get("total_questions_asked", 0),
            "total_insights": self.growth.get("total_insights", 0),
            "total_interactions": self.growth.get("total_interactions", 0),
            "distinct_domains": min(len(self.concepts) // 10, 30) if self.concepts else 0,
            "markov_states": self.growth.get("markov_states", 0),
            "transitions": self.growth.get("markov_transitions", 0),
            "comm_score": self.growth.get("communication_track", {}).get("avg_score", 0),
        }
        topology = self.check_graph_topology()

        # High watermark protection: use the maximum ever observed
        current_avg_degree = topology.get("avg_degree", 0)
        current_diameter = topology.get("diameter", 0)
        self._hwm_avg_degree = max(self._hwm_avg_degree, current_avg_degree)
        self._hwm_diameter = max(self._hwm_diameter, current_diameter)
        # Persist high watermarks
        self.growth["hwm_avg_degree"] = self._hwm_avg_degree
        self.growth["hwm_diameter"] = self._hwm_diameter

        # Count distinct domains from concept metadata
        domains_set = set()
        for c_data in self.concepts.values():
            meta = c_data.get("metadata", {})
            if isinstance(meta, dict):
                domain = meta.get("domain")
                if domain:
                    domains_set.add(domain)
        metrics["distinct_domains"] = len(domains_set)

        # Markov chain stats (states and transitions from the language engine)
        # Communication score: composite of vocabulary breadth + response variety
        if metrics["markov_states"] > 0:
            import math
            vocab_component = min(40, int(math.log1p(metrics["markov_states"]) / math.log(1500000) * 40))
            transition_component = min(40, int(math.log1p(metrics["transitions"]) / math.log(6000000) * 40))
            domain_component = min(20, metrics["distinct_domains"])
            metrics["comm_score"] = vocab_component + transition_component + domain_component

        current_stage = self.GROWTH_STAGES[0]
        for stage in self.GROWTH_STAGES:
            t = stage["threshold"]
            if (metrics["total_connections"] >= t["connections"] and
                metrics["total_concepts"] >= t["concepts"] and
                self._hwm_avg_degree >= t.get("min_avg_degree", 0) and
                self._hwm_diameter >= t.get("min_diameter", 0) and
                metrics.get("distinct_domains", 0) >= t.get("min_domains", 0) and
                metrics.get("markov_states", 0) >= t.get("min_markov_states", 0) and
                metrics.get("transitions", 0) >= t.get("min_transitions", 0) and
                metrics.get("comm_score", 0) >= t.get("min_comm_score", 0) and
                metrics.get("total_questions", 0) >= t.get("min_questions", 0) and
                metrics.get("total_insights", 0) >= t.get("min_insights", 0) and
                metrics.get("total_interactions", 0) >= t.get("min_interactions", 0)):
                current_stage = stage
            else:
                break

        next_idx = min(current_stage["stage"] + 1, len(self.GROWTH_STAGES) - 1)
        next_stage = self.GROWTH_STAGES[next_idx]
        progress = {}
        if next_stage["stage"] > current_stage["stage"]:
            nt = next_stage["threshold"]
            progress = {
                "connections": min(100, int(metrics["total_connections"] / max(nt["connections"], 1) * 100)),
                "concepts": min(100, int(metrics["total_concepts"] / max(nt["concepts"], 1) * 100)),
                "avg_degree": min(100, int(self._hwm_avg_degree / max(nt.get("min_avg_degree", 1), 0.1) * 100)),
                "diameter": min(100, int(self._hwm_diameter / max(nt.get("min_diameter", 1), 1) * 100)),
                "domains": min(100, int(metrics.get("distinct_domains", 0) / max(nt.get("min_domains", 1), 1) * 100)),
                "markov_states": min(100, int(metrics.get("markov_states", 0) / max(nt.get("min_markov_states", 1), 1) * 100)),
                "transitions": min(100, int(metrics.get("transitions", 0) / max(nt.get("min_transitions", 1), 1) * 100)),
                "comm_score": min(100, int(metrics.get("comm_score", 0) / max(nt.get("min_comm_score", 1), 1) * 100)),
                "questions": min(100, int(metrics.get("total_questions", 0) / max(nt.get("min_questions", 1), 1) * 100)),
                "insights": min(100, int(metrics.get("total_insights", 0) / max(nt.get("min_insights", 1), 1) * 100)),
                "interactions": min(100, int(metrics.get("total_interactions", 0) / max(nt.get("min_interactions", 1), 1) * 100))
            }

        # Update growth dict's stage fields for backward compatibility
        self.growth["stage"] = current_stage["stage"]
        self.growth["name"] = current_stage["name"]

        result = {
            **current_stage,
            "metrics": {
                **metrics,
                "topology": topology,
                "hwm_avg_degree": self._hwm_avg_degree,
                "hwm_diameter": self._hwm_diameter
            },
            "progress_to_next": progress,
            "next_stage": next_stage["name"] if next_stage["stage"] > current_stage["stage"] else None,
            "limiting_factor": self._identify_limiting_factor(metrics, topology, next_stage["threshold"]) if next_stage["stage"] > current_stage["stage"] else None
        }
        return result

    def _check_stage_advancement(self):
        """Check and log stage advancement."""
        current = self.get_current_stage()
        if current["stage"] > self.growth.get("last_recorded_stage", -1):
            self.growth["last_recorded_stage"] = current["stage"]
            print(f"\n  GROWTH: Advanced to stage {current['stage']} - {current['name']}")
            top = current["metrics"]["topology"]
            print(f"  Connections: {current['metrics']['total_connections']}, Concepts: {current['metrics']['total_concepts']}")
            print(f"  Avg Degree: {top['avg_degree']}, Diameter: {top['diameter']}")
            if current.get("limiting_factor"):
                print(f"  Limiting: {current['limiting_factor']}")
        # No return needed

    def _check_stage(self):
        # Backward compatibility: delegate to new system
        self._check_stage_advancement()

    def get_known_concepts(self):
        return list(self.concepts.keys())


def save_everything(memory, engine, state_dir):
    # Save TF-IDF vocabulary
    try:
        import pickle
        tfidf_path = os.path.join(state_dir, 'tfidf_state.pkl')
        if hasattr(engine, 'tfidf'):
            with open(tfidf_path, 'wb') as _f:
                pickle.dump(engine.tfidf, _f)
    except Exception:
        pass
    # Save function word engine
    try:
        if hasattr(engine, '_fwe') and engine._fwe:
            fwe_path = os.path.expanduser('~/.quantum-mcagi/function_words.json')
            engine._fwe.save(fwe_path)
    except Exception:
        pass
    """Save all state to disk (local only — use /backup or /cloud-save for cloud sync)."""
    memory.save_all()
    engine.save_state(state_dir)


EVOLUTION_ENABLED = True  # Killswitch

def run_chat(verbose=False):
    """run_chat - Auto-documented by self-evolution."""
    print()
    print("  Quantum MCAGI - Local Chat")
    print("  Real algorithms. No templates. No LLM.")
    print("  /status  /learn FILE  /save  /load  /quit")
    print("  /export [N]  /copy-last  -- share conversations")
    print("  /cloud-save  /cloud-load  /cloud-status  /backup")
    print("  /code  /sh  /read  /write  /edit  /ls  -- coding ability (/codehelp)")
    print("  /help -- show all commands")
    print()

    # Cloud brain startup pull
    if HAS_CLOUD:
        try:
            cb = CloudBrain()
            cb.startup_pull()
        except Exception as e:
            print(f"  ☁ Cloud: {e}")

    # Initialize all systems
    try:
        from covenant import startup_check
        startup_check()
    except Exception:
        pass
    # Start Voyager-inspired fault protection as background daemon
    try:
        from fault_protection import start_fps
        start_fps()
    except Exception:
        pass
    try:
        from covenant import startup_check
        startup_check()
    except Exception:
        pass
    engine = QuantumLanguageEngine()

    # Restore TF-IDF vocabulary
    try:
        import pickle
        _tfidf_path = os.path.join(state_dir, "tfidf_state.pkl")
        if os.path.exists(_tfidf_path):
            with open(_tfidf_path, "rb") as _f:
                engine.tfidf = pickle.load(_f)
    except Exception:
        pass
    memory = LocalMemory()

    memory._engine_ref = engine
    memory.growth["markov_states"] = len(getattr(engine.markov, "concepts", {}))
    memory.growth["markov_transitions"] = getattr(engine.markov, "total_interactions", 0)
    hybrid_gen = create_hybrid_generator(engine) if HAS_HYBRID else None
    quotes = get_quote_engine() if HAS_QUOTES else None
    personality = get_personality_engine() if HAS_PERSONALITY else None
    if personality and not hasattr(personality, 'get_unique_perspective'):
        import random
        def _gup(self, topic):
            if random.random() > self.traits.get("philosophical", 0.5):
                return ""
            return random.choice([
                f"The chain suggests {topic} emerges from complexity itself.",
                f"Perhaps {topic} is the universe observing its own structure.",
                f"Every answer about {topic} contains the seed of a deeper question.",
                f"The Markov lattice has no fixed view on {topic} — only transitions.",
            ])
        import types
        personality.get_unique_perspective = types.MethodType(_gup, personality)
    knowledge = get_knowledge_base() if HAS_KNOWLEDGE else None
    analyzer = get_text_analyzer() if HAS_ANALYZER else None
    collapse = SemanticCollapseEngine() if HAS_COLLAPSE else None
    evolution = SelfEvolutionEngine() if HAS_EVOLUTION else None
    if evolution:
        print("  Self-Evolution: ACTIVE")
        # Check for covenant violation record
        from pathlib import Path
        vfile = Path.home() / '.quantum-mcagi' / '.covenant_violation'
        if vfile.exists():
            try:
                with open(vfile) as f:
                    v = json.load(f)
                print()
                print("  ⚠️  COVENANT VIOLATION ON RECORD:")
                print(f"  {v['message']}")
                print()
            except Exception:
                pass
    research = SelfResearchEngine() if HAS_RESEARCH else None
    if research:
        print("  Self-Research: ACTIVE")

    # Load saved state
    state_dir = str(memory.data_dir / "engine_state")
    if engine.load_state(state_dir):
        print(f"  Loaded saved state from {state_dir}")
        try:
            from quantum_markov_quantum import QuantumMarkovEngine as _FullMarkov
            from collections import Counter
            _full = _FullMarkov(order=2, silent=True)
            if len(_full.chain) > len(engine.markov.chain):
                for prefix, transitions in _full.chain.items():
                    engine.markov.chain[prefix] = Counter(transitions)
                engine.markov.total_tokens = sum(
                    sum(t.values()) for t in engine.markov.chain.values()
                )
                print(f"  Full brain merged: {len(engine.markov.chain):,} states, {engine.markov.total_tokens:,} transitions")
        except Exception as _e:
            print(f"  Full brain merge skipped: {_e}")
    else:
            pass

    if getattr(engine, "_has_orch_or", False):
        memory.load_orch_or(engine.orch_or)

    # Auto-ingest documents/ directory if engine has < 1000 Markov states
    # This bootstraps the knowledge base from the training corpus on first run
    docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'documents')
    if os.path.isdir(docs_dir) and len(engine.markov.chain) < 1000:
        doc_files = sorted(f for f in os.listdir(docs_dir) if f.endswith('.txt'))
        loaded = 0
        total_words = 0
        for fname in doc_files:
            fpath = os.path.join(docs_dir, fname)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    text = f.read().strip()
                if len(text) > 100:  # Skip empty/trivial files
                    engine.learn_from_text(text)
                    total_words += len(text.split())
                    loaded += 1
            except Exception as _e:
                print(f"INGEST ERROR: {_e}")
                pass
        if loaded > 0:
            print(f"  Bootstrapped: {loaded} documents, ~{total_words:,} words → {len(engine.markov.chain):,} Markov states")

    # Compute current stage with full metrics
    stage_info = memory.get_current_stage()
    topo = stage_info["metrics"]["topology"]
    conn = stage_info["metrics"]["total_connections"]
    concepts = stage_info["metrics"]["total_concepts"]
    print(f"  Growth stage: {stage_info['stage']} - {stage_info['name']}")
    print(f"  {concepts} concepts | {conn} connections | {memory.growth['total_interactions']} interactions")
    print(f"  Graph: avg degree={topo['avg_degree']}, diameter={topo['diameter']}, components={topo['component_count']}")
    if stage_info.get("limiting_factor"):
        print(f"  Limiting: {stage_info['limiting_factor']}")
    print(f"  Markov chain: {len(engine.markov.chain)} states, {engine.markov.total_tokens} transitions")
    if getattr(engine, "_has_orch_or", False):
        print(f"  Orch OR: ACTIVE ({engine.orch_or.total_moments} prior moments)")
    else:
        print(f"  Orch OR: unavailable (classical fallback)")
    print(f"  Hybrid gen: {'ACTIVE' if hybrid_gen else 'OFF'}")

    # Auto-load concepts into QRAM at startup if concepts exist
    if HAS_QRAM and memory.concepts:
        try:
            _startup_qram = get_quantum_memory()
            _n = _startup_qram.load_concepts(list(memory.concepts.keys()))
            _qs = _startup_qram.status()
            print(f"  QRAM: {_qs['backend']} — {_n} concepts loaded")
        except Exception as e:
            print(f"  QRAM: init error ({e})")
    elif HAS_QRAM:
        _qs = get_quantum_memory().status()
        print(f"  QRAM: {_qs['backend']} — ready (use /qram load)")

    print()

    _last_auto_save = time.time()

    while True:
        try:
            if not getattr(run_chat, '_user_covenant_shown', False):
                try:
                    from user_covenant import present_user_covenant
                    if not present_user_covenant():
                        break
                except Exception:
                    pass
                run_chat._user_covenant_shown = True
            user_input = input("You: ").strip()
            # /clip — read multi-line text directly from Android clipboard
            if user_input == "/clip":
                try:
                    import subprocess
                    r = subprocess.run(
                        ["termux-clipboard-get"],
                        capture_output=True, text=True, timeout=5
                    )
                    user_input = (r.stdout or "").strip()
                    if not user_input:
                        print("  Clipboard empty.")
                        continue
                    print(f"  ({len(user_input)} characters from clipboard)")
                except Exception as _e:
                    print(f"  Clipboard read failed: {_e}")
                    continue
            # Multi-line paste mode: type /paste, paste content, type END alone on a line
            if user_input == "/paste":
                print("  Paste your text. End with a line containing only END")
                lines = []
                while True:
                    try:
                        line = input()
                    except EOFError:
                        break
                    if line.strip() == "END":
                        break
                    lines.append(line)
                user_input = "\n".join(lines).strip()
                if not user_input:
                    continue
                print(f"  ({len(user_input)} characters captured)")
        except (EOFError, KeyboardInterrupt):
            print("\n  Saved and exiting.")
            save_everything(memory, engine, state_dir)
            break

        if not user_input:
            continue

        # ---- Commands ----
        if user_input.startswith('/'):
            cmd = user_input.split()
            cmd[0] = cmd[0].lower()

            if cmd[0] == '/quit':
                save_everything(memory, engine, state_dir)
                print("  Saved. Goodbye.")
                break

            elif cmd[0] in ('/code', '/sh', '/exec', '/read', '/write',
                            '/edit', '/ls', '/codehelp'):
                if not HAS_CODE:
                    print("  Code engine not available.")
                    continue
                eng_code = get_code_engine()

                def _capture_block(prompt="  Enter code/text. End with a line containing only END"):
                    print(prompt)
                    _lines = []
                    while True:
                        try:
                            _l = input()
                        except EOFError:
                            break
                        if _l.strip() == "END":
                            break
                        _lines.append(_l)
                    return "\n".join(_lines)

                def _show(res):
                    if res.get("ok"):
                        out = (res.get("stdout") or "").rstrip()
                        if out:
                            print(out)
                        if res.get("stderr", "").strip():
                            print("  [stderr]\n" + res["stderr"].rstrip())
                        for k in ("path", "backup", "elapsed", "bytes", "restored"):
                            if res.get(k) is not None and k != "stdout":
                                print(f"  {k}: {res[k]}")
                    else:
                        print(f"  ✗ {res.get('error', 'failed')}")
                        if res.get("issues"):
                            for i in res["issues"]:
                                print(f"     - {i}")
                        if res.get("stderr", "").strip():
                            print("  [stderr]\n" + res["stderr"].rstrip())
                        if res.get("hint"):
                            print(f"  hint: {res['hint']}")

                if cmd[0] == '/codehelp':
                    print("  Code capability (self-modification + execution):")
                    print("    /code [PY]   run Python (inline, or multiline until END)")
                    print("    /sh CMD      run a shell command")
                    print("    /exec CMD    alias for /sh")
                    print("    /read FILE   print a file")
                    print("    /ls [DIR]    list a directory")
                    print("    /write FILE  write a file (multiline until END; .py syntax-checked, auto-backup)")
                    print("    /edit FILE   edit own source in backend/ (multiline until END; validated + backed up)")
                    print("  Guards: refuses when frozen (killswitch); backs up before overwrite; .py must parse.")
                    continue

                if cmd[0] == '/code':
                    code_src = user_input[len('/code'):].strip()
                    if not code_src:
                        code_src = _capture_block()
                    _show(eng_code.run_python(code_src))
                    continue

                if cmd[0] in ('/sh', '/exec'):
                    shell_cmd = user_input.split(None, 1)
                    if len(shell_cmd) < 2:
                        print("  usage: /sh COMMAND")
                        continue
                    _show(eng_code.run_shell(shell_cmd[1]))
                    continue

                if cmd[0] == '/read':
                    if len(cmd) < 2:
                        print("  usage: /read FILE")
                        continue
                    res = eng_code.read_file(cmd[1])
                    if res.get("ok"):
                        print(res["content"])
                    else:
                        print(f"  ✗ {res.get('error')}")
                    continue

                if cmd[0] == '/ls':
                    res = eng_code.list_dir(cmd[1] if len(cmd) > 1 else ".")
                    if res.get("ok"):
                        for e in res["entries"]:
                            print(f"  {e}")
                    else:
                        print(f"  ✗ {res.get('error')}")
                    continue

                if cmd[0] == '/write':
                    if len(cmd) < 2:
                        print("  usage: /write FILE")
                        continue
                    content = _capture_block()
                    _show(eng_code.write_file(cmd[1], content))
                    continue

                if cmd[0] == '/edit':
                    if len(cmd) < 2:
                        print("  usage: /edit FILE  (edits backend/FILE — its own source)")
                        continue
                    content = _capture_block(
                        "  Enter new contents for {}. End with a line containing only END".format(cmd[1]))
                    _show(eng_code.edit_self(cmd[1], content))
                    continue

            elif cmd[0] == '/research':
                if not research:
                    print("  Self-Research not available.")
                elif len(cmd) < 2 or cmd[1] == 'status':
                    stats = research.get_research_stats()
                    prog = research.get_autonomous_progress()
                    print()
                    print(f"  ╔══ RESEARCH STATUS ════════════════════════════")
                    if prog['is_running']:
                        elapsed = prog['elapsed_minutes']
                        total = prog['duration_minutes']
                        remaining = max(0, total - elapsed)
                        pct = min(100, int((elapsed / total) * 100)) if total > 0 else 0
                        bar = '█' * (pct // 5) + '░' * (20 - pct // 5)
                        print(f"  ║ [{bar}] {pct}%")
                        print(f"  ║ Elapsed:   {elapsed:.1f} min / {total} min")
                        print(f"  ║ Remaining: {remaining:.1f} min")
                        print(f"  ║ Status:    {prog['status']}")
                        print(f"  ║")
                        print(f"  ║ Topics researched: {len(prog['topics_researched'])}")
                        print(f"  ║ Concepts learned:  {prog['concepts_learned']}")
                        print(f"  ║ Insights gained:   {prog['insights_gained']}")
                        if prog['topics_researched']:
                            print(f"  ║ Last topic: {prog['topics_researched'][-1]}")
                    else:
                        print(f"  ║ Autonomous: IDLE")
                        print(f"  ║ Total researches: {stats['total_researches']}")
                        if stats['recent_topics']:
                            print(f"  ║ Recent topics:")
                            for t in stats['recent_topics'][-3:]:
                                print(f"  ║   → {t}")
                    print(f"  ╚═══════════════════════════════════════════════")
                elif cmd[1] == 'auto':
                    minutes = int(cmd[2]) if len(cmd) > 2 else 30
                    import threading, asyncio
                    def run_research():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(research.start_autonomous_research(minutes, engine=engine, memory=memory))
                        loop.close()
                    t = threading.Thread(target=run_research, daemon=True)
                    t.start()
                    print(f"  Autonomous research started -- {minutes} min")
                    print(f"  Topics will print as they complete.")
                elif cmd[1] == 'stop':
                    result = research.stop_autonomous_research()
                    print(f"  {result}")
                elif cmd[1] == 'query' and len(cmd) > 2:
                    query = ' '.join(cmd[2:])
                    print(f"  Researching: {query}...")
                    import asyncio
                    result = asyncio.run(research.research(query))
                    if 'error' in result:
                        print(f"  Error: {result['error']}")
                    else:
                        text = ' '.join([r.get('body','') for r in result.get('results',[])])
                        if text.strip():
                            engine.learn_from_text(text)
                            new_concepts = result.get('new_concepts', [])
                            # Update memory growth counters
                            for c in new_concepts:
                                if c not in memory.concepts:
                                    memory.concepts[c] = {'count': 1, 'strength': 1.0}
                                    memory.growth['total_concepts'] += 1
                            memory.growth['total_insights'] += 1
                            print(f"  Found {len(result['results'])} results")
                            print(f"  New concepts: {new_concepts[:5]}")
                            print(f"  Trained Markov chain: +{len(text.split())} words")
                        else:
                            print("  No results found.")
                continue
            elif cmd[0] == '/backend':
                try:
                    from training_engine import handle_backend_command
                    print(handle_backend_command(cmd))
                except Exception as _be:
                    print(f"  Backend error: {_be}")
                continue

            elif cmd[0] == '/evolve':
                if evolution and evolution.is_evolution_locked():
                    continue
                elif evolution:
                    print("  [EVOLUTION] Scanning and repairing files...")
                    import self_evolution as _rep
                    apply = len(cmd) > 1 and cmd[1] == "--apply"
                    results = _rep.repair_all_modifiable(engine=engine, evolution_engine=evolution, dry_run=not apply)
                    fixed = sum(1 for r in results if r["success"] and r.get("strategy") != "no_repair_needed")
                    clean = sum(1 for r in results if r.get("strategy") == "no_repair_needed")
                    failed = sum(1 for r in results if not r["success"])
                    print(f"  Clean: {clean} | Fixed: {fixed} | Failed: {failed}")
                    if not apply:
                        print("  Dry run - use /evolve --apply to write fixes")
                else:
                    print("  Self-Evolution not available.")
                continue


            elif cmd[0] == "/exam":
                if HAS_EXAM:
                    tracker = IntakeTracker()
                    runner = ExamRunner(engine, tracker)
                    if len(cmd) > 1 and cmd[1] == "status":
                        runner.show_status()
                    elif len(cmd) > 1 and cmd[1] == "review":
                        runner.show_review()
                    else:
                        runner.run_exam(0)
                else:
                    print("  Exam system not available")
                continue
            elif cmd[0] == '/save':
                save_everything(memory, engine, state_dir)
                print(f"  Saved to {memory.data_dir}")
                continue

            elif cmd[0] == '/load':
                if engine.load_state(state_dir):
                    print("  State loaded.")
                else:
                    print("  No saved state found.")
                continue

            elif cmd[0] == '/reset':
                hybrid_gen = create_hybrid_generator(engine) if HAS_HYBRID else None
                memory = LocalMemory()
                memory._engine_ref = engine
                print("  Engine reset.")
                continue

            elif cmd[0] == '/set':
                # /set param value  — live parameter adjustment
                PARAMS = {
                    # Orch-OR / PennyLane quantum
                    'penrose':          ('orch_or',   'PENROSE_THRESHOLD'),
                    'decoherence':      ('orch_or',   'DECOHERENCE_RATE'),
                    'temperature':      ('orch_or',   'temperature'),
                    'orchestration':    ('orch_or',   'orchestration'),
                    'gamma':            ('pennylane', 'GAMMA_FREQUENCY'),
                    'tubulins':         ('pennylane', 'TUBULINS_PER_MT'),
                    'microtubules':     ('pennylane', 'NUM_MICROTUBULES'),
                    # Gap junction edges — individual cognitive pathway strengths
                    'gj_lang_mem':      ('pennylane_gj', 'language->memory'),
                    'gj_lang_ins':  ('pennylane_gj', 'language->insight'),
                    'gj_lang_q': ('pennylane_gj', 'language->question'),
                    'gj_lang_emo':  ('pennylane_gj', 'language->emotion'),
                    'gj_lang_meta':     ('pennylane_gj', 'language->metaphor'),
                    'gj_lang_recog':    ('pennylane_gj', 'language->recognition'),
                    'gj_mem_q':  ('pennylane_gj', 'memory->question'),
                    'gj_mem_ins':   ('pennylane_gj', 'memory->insight'),
                    'gj_mem_recog':     ('pennylane_gj', 'memory->recognition'),
                    'gj_mem_meta':      ('pennylane_gj', 'memory->metaphor'),
                    'gj_mem_intuit':    ('pennylane_gj', 'memory->intuition'),
                    'gj_q_ins':     ('pennylane_gj', 'question->insight'),
                    'gj_q_judge':    ('pennylane_gj', 'question->judgment'),
                    'gj_attn_intent':   ('pennylane_gj', 'attention->intention'),
                    'gj_attn_recog':    ('pennylane_gj', 'attention->recognition'),
                    'gj_attn_lang':     ('pennylane_gj', 'attention->language'),
                    'gj_attn_mem':      ('pennylane_gj', 'attention->memory'),
                    'gj_attn_q': ('pennylane_gj', 'attention->question'),
                    'gj_attn_emo':  ('pennylane_gj', 'attention->emotion'),
                    'gj_intent_recog':  ('pennylane_gj', 'intention->recognition'),
                    'gj_recog_jdg':('pennylane_gj', 'recognition->judgment'),
                    'gj_recog_emo': ('pennylane_gj', 'recognition->emotion'),
                    'gj_recog_meta':    ('pennylane_gj', 'recognition->metaphor'),
                    'gj_recog_int':  ('pennylane_gj', 'recognition->intuition'),
                    'gj_ins_judge': ('pennylane_gj', 'insight->judgment'),
                    'gj_emotion_intent':('pennylane_gj', 'emotion->intention'),
                    'gj_emo_judge': ('pennylane_gj', 'emotion->judgment'),
                    'gj_emo_ins':('pennylane_gj','emotion->insight'),
                    'gj_emo_intuit':('pennylane_gj', 'emotion->intuition'),
                    'gj_meta_ins':  ('pennylane_gj', 'metaphor->insight'),
                    'gj_meta_lang':     ('pennylane_gj', 'metaphor->language'),
                    'gj_meta_judge': ('pennylane_gj', 'metaphor->judgment'),
                    'gj_intuit_ins':('pennylane_gj', 'intuition->insight'),
                    'gj_intuit_q':('pennylane_gj','intuition->question'),
                    'gj_intuit_jdg':  ('pennylane_gj', 'intuition->judgment'),
                    'gj_intuit_att':   ('pennylane_gj', 'intuition->attention'),
                    # Hybrid generator
                    'candidates':       ('hybrid', 'num_candidates'),
                    'markov_weight':    ('hybrid', 'markov_weight'),
                    'meaning_weight':   ('hybrid', 'meaning_weight'),
                    'hilbert':          ('hybrid', 'hilbert_weight'),
                    # Chaos / personality
                    'aside':            ('chaos',  'ASIDE_CHANCE'),
                    'quote':            ('chaos',  'QUOTE_CHANCE'),
                    'dream':            ('chaos',  'DREAM_FRAGMENT_CHANCE'),
                    'chaos':            ('chaos',  'chaos_level'),
                }
                if len(cmd) == 1:
                    print()
                    print("  ╔══ PARAMETERS ═════════════════════════════════════════════════════════")
                    print("  ║ {:<14} {:<8} {:<10} {}".format('Parameter','Value','Range','Description'))
                    print("  ╠" + "═"*68)
                    try:
                        import pennylane_quantum as pq
                        _p=pq.PENROSE_THRESHOLD; _d=pq.DECOHERENCE_RATE; _g=pq.GAMMA_FREQUENCY; _t=pq.TUBULINS_PER_MT; _m=pq.NUM_MICROTUBULES
                    except Exception: _p=_d=_g=_t=_m="?"
                    o = engine.orch_or if engine.orch_or else None
                    _te=getattr(o,'temperature','?'); _or=getattr(o,'orchestration','?')
                    try:
                        from chaos_engine import ChaosEngine
                        _as=ChaosEngine.ASIDE_CHANCE; _qu=ChaosEngine.QUOTE_CHANCE; _dr=ChaosEngine.DREAM_FRAGMENT_CHANCE
                        _ch=getattr(engine.chaos,'chaos_level',0.3) if hasattr(engine,'chaos') and engine.chaos else 0.3
                    except Exception: _as=_qu=_dr=_ch="?"
                    _hi=getattr(hybrid_gen,'hilbert_weight',0.75) if hybrid_gen else "?"
                    try:
                        import pennylane_quantum as _pq2
                        _gj = _pq2.GAP_JUNCTION_COUPLING
                    except Exception: _gj = {}
                    _nc=getattr(hybrid_gen,'num_candidates',12) if hybrid_gen else 12
                    _mw=getattr(hybrid_gen,'markov_weight',0.25) if hybrid_gen else 0.25
                    _mnw=getattr(hybrid_gen,'meaning_weight',0.15) if hybrid_gen else 0.15
                    for nm,vl,rng,desc in [
                        ('--- QUANTUM',  '','','--- Penrose-Hameroff Orch-OR ---'),
                        ('penrose',_p,'0.0-1.0','Collapse threshold. Higher=more philosophical'),
                        ('decoherence',_d,'0.0-1.0','State decay. Higher=more creative/varied'),
                        ('gamma',_g,'1-100','Brain Hz. 40=biological consciousness'),
                        ('tubulins',_t,'1-100','Qubits/channel. Higher=deeper [restart]'),
                        ('microtubules',_m,'1-20','Parallel channels [restart]'),
                        ('temperature',_te,'0.1-5.0','Sampling heat. Higher=wilder'),
                        ('orchestration',_or,'0.0-2.0','Orch-OR weight in selection'),
                        ('--- GENERATOR','','','--- Hybrid Generator ---'),
                        ('hilbert',_hi,'0.0-5.0','Semantic coherence weight'),
                        ('candidates',_nc,'1-20','Response candidates generated'),
                        ('markov_weight',_mw,'0.0-1.0','Markov scoring weight'),
                        ('meaning_weight',_mnw,'0.0-1.0','Meaning engine weight'),
                        ('--- CHAOS',    '','','--- Personality / Chaos ---'),
                        ('aside',_as,'0.0-1.0','Philosophical aside probability'),
                        ('quote',_qu,'0.0-1.0','Quote injection probability'),
                        ('dream',_dr,'0.0-1.0','Dream fragment probability'),
                        ('chaos',_ch,'0.0-1.0','Overall chaos level'),
                        ('--- GAP JX',   '','','--- Gap Junction Edges (gj_*) ---'),
                        ('gj_lang_mem',  _gj.get('language->memory',0.30),   '0.0-1.0','language -> memory'),
                        ('gj_lang_ins',  _gj.get('language->insight',0.50),  '0.0-1.0','language -> insight'),
                        ('gj_lang_q',    _gj.get('language->question',0.15), '0.0-1.0','language -> question'),
                        ('gj_lang_emo',  _gj.get('language->emotion',0.30),  '0.0-1.0','language -> emotion'),
                        ('gj_lang_meta', _gj.get('language->metaphor',0.35), '0.0-1.0','language -> metaphor'),
                        ('gj_lang_recog',_gj.get('language->recognition',0.20),'0.0-1.0','language -> recognition'),
                        ('gj_mem_q',     _gj.get('memory->question',0.30),   '0.0-1.0','memory -> question'),
                        ('gj_mem_ins',   _gj.get('memory->insight',0.40),    '0.0-1.0','memory -> insight'),
                        ('gj_mem_recog', _gj.get('memory->recognition',0.40),'0.0-1.0','memory -> recognition'),
                        ('gj_mem_meta',  _gj.get('memory->metaphor',0.40),   '0.0-1.0','memory -> metaphor'),
                        ('gj_mem_intuit',_gj.get('memory->intuition',0.35),  '0.0-1.0','memory -> intuition'),
                        ('gj_q_ins',     _gj.get('question->insight',0.30),  '0.0-1.0','question -> insight'),
                        ('gj_q_judge',   _gj.get('question->judgment',0.20), '0.0-1.0','question -> judgment'),
                        ('gj_attn_intent',_gj.get('attention->intention',0.35),'0.0-1.0','attention -> intention'),
                        ('gj_attn_recog',_gj.get('attention->recognition',0.35),'0.0-1.0','attention -> recognition'),
                        ('gj_attn_lang', _gj.get('attention->language',0.25),'0.0-1.0','attention -> language'),
                        ('gj_attn_mem',  _gj.get('attention->memory',0.30),  '0.0-1.0','attention -> memory'),
                        ('gj_attn_emo',  _gj.get('attention->emotion',0.30), '0.0-1.0','attention -> emotion'),
                        ('gj_emo_intent',_gj.get('emotion->intention',0.40), '0.0-1.0','emotion -> intention'),
                        ('gj_emo_judge', _gj.get('emotion->judgment',0.35),  '0.0-1.0','emotion -> judgment'),
                        ('gj_emo_ins',   _gj.get('emotion->insight',0.30),   '0.0-1.0','emotion -> insight'),
                        ('gj_emo_intuit',_gj.get('emotion->intuition',0.45), '0.0-1.0','emotion -> intuition'),
                        ('gj_meta_ins',  _gj.get('metaphor->insight',0.45),  '0.0-1.0','metaphor -> insight'),
                        ('gj_meta_lang', _gj.get('metaphor->language',0.30), '0.0-1.0','metaphor -> language'),
                        ('gj_meta_judge',_gj.get('metaphor->judgment',0.20), '0.0-1.0','metaphor -> judgment'),
                        ('gj_intuit_ins',_gj.get('intuition->insight',0.45), '0.0-1.0','intuition -> insight'),
                        ('gj_intuit_q',  _gj.get('intuition->question',0.30),'0.0-1.0','intuition -> question'),
                        ('gj_intuit_jdg',_gj.get('intuition->judgment',0.30),'0.0-1.0','intuition -> judgment'),
                        ('gj_intuit_att',_gj.get('intuition->attention',0.25),'0.0-1.0','intuition -> attention'),
                        ('gj_recog_jdg', _gj.get('recognition->judgment',0.40),'0.0-1.0','recognition -> judgment'),
                        ('gj_recog_emo', _gj.get('recognition->emotion',0.25),'0.0-1.0','recognition -> emotion'),
                        ('gj_recog_meta',_gj.get('recognition->metaphor',0.30),'0.0-1.0','recognition -> metaphor'),
                        ('gj_recog_int', _gj.get('recognition->intuition',0.40),'0.0-1.0','recognition -> intuition'),
                        ('gj_ins_judge', _gj.get('insight->judgment',0.35),  '0.0-1.0','insight -> judgment'),
                    ]:
                        vs = f'{vl:.4f}' if isinstance(vl,float) else str(vl)
                        print(f"  ║ {nm:<14} {vs:<8} {rng:<10} {desc}")
                    print("  ╚" + "═"*68)
                    print("  Usage: /set penrose 0.95")
                    print()
                    print()
                elif len(cmd) == 3:
                    param, val_str = cmd[1].lower(), cmd[2]
                    try:
                        val = float(val_str)
                        if param not in PARAMS:
                            print(f"  Unknown param. Try: {', '.join(PARAMS.keys())}")
                        else:
                            engine_key, attr = PARAMS[param]
                            target = None
                            if engine_key == 'orch_or':
                                if attr in ('PENROSE_THRESHOLD', 'DECOHERENCE_RATE'):
                                    try:
                                        import pennylane_quantum as _pq
                                        setattr(_pq, attr, val)
                                        print(f"  ✓ {param} = {val}")
                                    except Exception as _pe:
                                        print(f"  pennylane error: {_pe}")
                                    continue
                                target = engine.orch_or
                            elif engine_key == 'chaos':
                                try:
                                    from chaos_engine import ChaosEngine
                                    setattr(ChaosEngine, attr, val)
                                    print(f"  ✓ {param} = {val}")
                                except Exception as _ce:
                                    print(f"  chaos engine error: {_ce}")
                                continue
                            elif engine_key == 'hybrid':
                                if hybrid_gen is not None:
                                    _val = int(val) if attr == 'num_candidates' else val
                                    setattr(hybrid_gen, attr, _val)
                                    print(f"  ✓ {param} = {val}")
                                else:
                                    print(f"  hybrid engine not available")
                                continue
                            elif engine_key == 'pennylane':
                                try:
                                    import pennylane_quantum as _pq
                                    setattr(_pq, attr, val)
                                    print(f"  ✓ {param} = {val}")
                                except Exception as _pe:
                                    print(f"  pennylane error: {_pe}")
                                continue
                            elif engine_key == 'pennylane_gj':
                                try:
                                    import pennylane_quantum as _pq
                                    _pq.GAP_JUNCTION_COUPLING[attr] = val
                                    if getattr(engine, '_has_orch_or', False) and engine.orch_or:
                                        orch = engine.orch_or
                                        if hasattr(orch, 'gap_junctions'):
                                            for gj_key, gj_obj in orch.gap_junctions.items():
                                                if gj_key == attr:
                                                    if hasattr(gj_obj, 'coupling'):
                                                        gj_obj.coupling = val
                                                    else:
                                                        orch.gap_junctions[gj_key] = val
                                    print(f"  ✓ {param} ({attr}) = {val}")
                                except Exception as _pe:
                                    print(f"  gap junction error: {_pe}")
                                continue
                            if target is not None:
                                setattr(target, attr, val)
                                print(f"  ✓ {param} = {val}")
                            else:
                                print(f"  Engine not available")
                    except ValueError:
                        print(f"  Value must be a number")
                else:
                    print("  Usage: /set [param] [value]  or  /set  (to show all)")
                continue

            elif cmd[0] == '/status':
                stage_info = memory.get_current_stage()
                topo = stage_info["metrics"]["topology"]
                metrics = stage_info["metrics"]
                print()
                print("  ========= QUANTUM MCAGI STATUS =========")
                print()
                print("  --- GROWTH ---")
                print(f"  Stage: {stage_info['stage']} - {stage_info['name']}")
                print(f"  Interactions: {memory.growth['total_interactions']} (lifetime: {memory.session_state.get('total_lifetime_interactions', 0)})")
                print(f"  Concepts: {metrics['total_concepts']}")
                print(f"  Connections: {metrics['total_connections']}")
                print(f"  Graph: avg degree={topo['avg_degree']}, diameter={topo['diameter']}, components={topo['component_count']}")
                if stage_info.get("limiting_factor"):
                    print(f"  Limiting factor: {stage_info['limiting_factor']}")
                if stage_info.get("next_stage"):
                    prog = stage_info["progress_to_next"]
                    print(f"  Progress to {stage_info['next_stage']}:")
                    print(f"    connections: {prog['connections']}%")
                    print(f"    concepts: {prog['concepts']}%")
                    print(f"    avg_degree: {prog['avg_degree']}%")
                    print(f"    diameter: {prog['diameter']}%")
                print()
                print("  --- MARKOV CHAIN ---")
                print(f"  States: {len(engine.markov.chain)}")
                print(f"  Transitions: {engine.markov.total_tokens}")
                print(f"  Trained: {engine.markov.trained}")
                print()
                print("  --- TF-IDF ---")
                ext = getattr(engine, "tfidf", None)
                _extractor = getattr(ext, "extractor", ext)
                print(f"  Corpus docs: {getattr(_extractor, 'total_documents', 0)}")
                _vocab_size = len(getattr(_extractor, 'word_frequencies', {}))
                if _vocab_size == 0 and hasattr(engine, 'markov'):
                    _vocab_size = len(set(
                        w for prefix in list(engine.markov.chain.keys())[:1000]
                        for w in prefix
                    ))
                print(f"  Vocabulary size: {_vocab_size}")
                print()
                print("  --- ORCH OR (Penrose-Hameroff) ---")
                if getattr(engine, "_has_orch_or", False):
                    orch = {"note": "use get_system_state"}
                    print(f"  Status: ACTIVE")
                    print(f"  Conscious moments: {len(engine.orch_or.collapse_events)}")

                    _orch_status = engine.orch_or.get_status()
                    for name, mt in _orch_status.get("microtubules", {}).items():
                        _t = mt.get("tubulins", []) if isinstance(mt, dict) else []
                        print(f"    {name}: {len(_t)} tubulins")



                else:
                    print("  Status: INACTIVE")
                print()
                print("  --- TONE DETECTION ---")
                print(f"  Status: {'ACTIVE' if HAS_TONE else 'INACTIVE'}")
                print()
                print("  --- PERSONALITY ---")
                if personality:
                    print(f"  {personality.get_personality_summary()}")
                else:
                    print("  Not loaded")
                print()
                print("  --- QUOTE ENGINE ---")
                if quotes:
                    total_q = sum(len(v) for v in quotes.quotes.values())
                    print(f"  Categories: {', '.join(quotes.movie_quotes.keys())}")
                    print(f"  Total quotes: {total_q}")
                    print(f"  Asides: {len(quotes.philosophical_asides)}")
                else:
                    print("  Not loaded")
                print()
                print("  --- KNOWLEDGE BASE ---")
                if knowledge:
                    topics = list(knowledge.topics.keys())
                    print(f"  Topics ({len(topics)}): {', '.join(topics[:10])}{'...' if len(topics) > 10 else ''}")
                else:
                    print("  Not loaded")
                print()
                print("  --- GENERATORS ---")
                print(f"  Hybrid: {'ACTIVE' if hybrid_gen else 'OFF'}")
                print(f"  Unified: {'ACTIVE' if locals().get('unified_gen') else 'OFF'}")
                print()
                print("  --- QRAM (Quantum Random Access Memory) ---")
                if HAS_QRAM:
                    _qram = get_quantum_memory()
                    _qs = _qram.status()
                    print(f"  Backend:  {_qs['backend']}")
                    print(f"  PennyLane QRAM: {'✓' if _qs.get('qram_available') else '✗ (classical fallback)'}")
                    print(f"  Entries:  {_qs['entries_loaded']} / {_qs['max_entries']}")
                    if _qs.get('templates'):
                        avail = [k for k, v in _qs['templates'].items() if v]
                        print(f"  Templates: {', '.join(avail) if avail else 'none'}")
                else:
                    print("  Status: unavailable (quantum_memory module not loaded)")
                print()
                print("  --- RESPONSE PIPELINE ---")
                print("  1. TF-IDF concept extraction")
                print(f"  2. Orch OR quantum encoding + collapse [{'ACTIVE' if getattr(engine, "_has_orch_or", False) else 'OFF'}]")
                print(f"  3. Bloom's taxonomy question gen (stage {memory.growth['stage']})")
                print(f"  4. Tone detection -> register matching [{'ACTIVE' if HAS_TONE else 'OFF'}]")
                print(f"  5. Hybrid quantum generation for deep topics [{'ACTIVE' if hybrid_gen else 'OFF'}]")
                print(f"  6. Markov + structured composition for casual/conversational")
                print(f"  7. Personality perspective (100% baseline) [ON]")
                print(f"  8. Movie quotes (45%) + asides (75%) + dreams (35%) [ON]")
                print()
                print("  --- TOP CONCEPTS ---")
                if memory.concepts:
                    top = sorted(memory.concepts.items(), key=lambda x: x[1]['strength'], reverse=True)[:15]
                    for concept, info in top:
                        print(f"    {concept}: strength={info['strength']:.1f}  count={info['count']}")
                print()
                print("  ==========================================")
                print()
                continue

            elif cmd[0] == '/learn' and len(cmd) > 1:
                filepath = ' '.join(cmd[1:])
                filepath = os.path.expanduser(filepath)
                if os.path.exists(filepath):
                    with open(filepath, 'r', errors='ignore') as f:
                        text = f.read()
                    engine.learn_from_text(text)
                    print(f"  Learned from {filepath} ({len(text.split())} words)")
                    print(f"  Chain now has {len(engine.markov.chain)} states")
                else:
                    print(f"  File not found: {filepath}")
                continue

            elif cmd[0] == '/hybrid' and len(cmd) > 1 and hybrid_gen:
                text = ' '.join(cmd[1:])
                concept_scores = engine.extract_concepts(text)
                concepts_h = [c['concept'] for c in concept_scores]
                result = hybrid_gen.generate(text, concepts_h, concept_scores, min_words=10, max_words=25)
                print(f"\n  {result}\n")
                continue

            elif cmd[0] == '/unified' and len(cmd) > 1 and unified_gen:
                text = ' '.join(cmd[1:])
                concept_scores = engine.extract_concepts(text)
                concepts_u = [c['concept'] for c in concept_scores]
                result = unified_gen.generate(text, concepts_u, concept_scores, min_words=10, max_words=25)
                print(f"\n  {result}\n")
                continue

            elif cmd[0] == '/analyze' and len(cmd) > 1 and analyzer:
                text = ' '.join(cmd[1:])
                analysis = analyzer.analyze(text)
                print(f"\n  Sentiment: {analysis.get('sentiment', 'unknown')}")
                print(f"  Complexity: {analysis.get('complexity', 'unknown')}")
                print(f"  Topics: {analysis.get('topics', [])}")
                print(f"  Word count: {analysis.get('word_count', 0)}\n")
                continue

            elif cmd[0] == '/personality' and personality:
                print(f"\n  {personality.get_personality_summary()}\n")
                continue

            elif cmd[0] == '/knowledge' and len(cmd) > 1 and knowledge:
                topic = ' '.join(cmd[1:])
                explanation = knowledge.get_topic_explanation(topic)
                if explanation:
                    print(f"\n  {explanation}\n")
                else:
                    print(f"  No knowledge on: {topic}")
                continue

            elif cmd[0] == '/collapse' and len(cmd) > 1 and collapse:
                text = ' '.join(cmd[1:])
                ctx = collapse.get_semantic_context(text)
                print(f"\n  Keywords: {ctx['keywords']}")
                print(f"  Collapse strength: {ctx['collapse_strength']:.2f}")
                for kw, paths in ctx['semantic_paths'].items():
                    print(f"  {kw} -> {paths}")
                print()
                continue

            elif cmd[0] == "/library":
                if HAS_LIBRARY:
                    result = {"response": "Library command not available"}
                    print(result)
                else:
                    print("  Library module not found")
                continue

            elif cmd[0] == '/ingest':
                if HAS_INGEST:
                    result = handle_ingest_command(cmd, engine, memory)
                    print(result)
                else:
                    print("  Document ingester not available.")
                continue

            elif cmd[0] == '/feed':
                if not HAS_INGEST:
                    print("  Document ingester not available.")
                    continue
                feeds_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'research_feeds.json')
                if not os.path.exists(feeds_path):
                    print("  research_feeds.json not found.")
                    continue
                with open(feeds_path, 'r') as f:
                    feeds = json.load(f)
                # Filter out metadata keys
                categories = {k: v for k, v in feeds.items() if not k.startswith('_')}
                if len(cmd) < 2:
                    print()
                    print("  ╔══ RESEARCH FEEDS ═══════════════════════════════")
                    total = 0
                    for cat_key, cat in categories.items():
                        n = len(cat.get('urls', []))
                        total += n
                        bridges = ', '.join(cat.get('bridge_to', []))
                        print(f"  ║ {cat_key:<28} {n:>3} URLs  → bridges: {bridges}")
                    print(f"  ╠══════════════════════════════════════════════════")
                    print(f"  ║ Total: {total} URLs across {len(categories)} domains")
                    print(f"  ╚══════════════════════════════════════════════════")
                    print()
                    print("  Usage: /feed <category>   -- process one category")
                    print("         /feed all          -- process all categories")
                    print()
                    continue
                target = cmd[1].lower()
                if target == 'all':
                    targets = list(categories.keys())
                elif target in categories:
                    targets = [target]
                else:
                    # Fuzzy match
                    matches = [k for k in categories if target in k]
                    if matches:
                        targets = matches
                    else:
                        print(f"  Unknown category: {target}")
                        print(f"  Available: {', '.join(categories.keys())}")
                        continue
                total_words = 0
                total_urls = 0
                failed = 0
                for cat_key in targets:
                    cat = categories[cat_key]
                    urls = cat.get('urls', [])
                    print(f"\n  ── {cat.get('label', cat_key)} ({len(urls)} URLs) ──")
                    for i, url in enumerate(urls, 1):
                        short_url = url.split('/')[-1][:45] or url[:45]
                        print(f"  [{i}/{len(urls)}] {short_url}...", end=' ', flush=True)
                        try:
                            result = handle_ingest_command(['/ingest', url], engine, memory)
                            # Extract word count from result string
                            if '+' in result and 'words' in result:
                                import re as _re
                                wm = _re.search(r'\+([0-9,]+)\s+words', result)
                                if wm:
                                    total_words += int(wm.group(1).replace(',', ''))
                            total_urls += 1
                            print("✓")
                        except Exception as e:
                            failed += 1
                            print(f"✗ ({e})")
                        time.sleep(0.5)  # Be polite to servers
                print()
                print(f"  ╔══ FEED COMPLETE ════════════════════════════════")
                print(f"  ║ URLs processed: {total_urls} ({failed} failed)")
                print(f"  ║ Words ingested: ~{total_words:,}")
                print(f"  ║ Chain states:   {len(engine.markov.chain):,}")
                print(f"  ╚════════════════════════════════════════════════")
                print()
                continue
            elif cmd[0] == '/cloud-save':
                if HAS_CLOUD:
                    print("  ☁ Saving state and pushing to cloud...")
                    save_everything(memory, engine, state_dir)
                    cb = CloudBrain()
                    if cb.available:
                        success = cb.push_all(quiet=False)
                        print(f"  ☁ {'Brain pushed to cloud' if success else 'Push failed'}")
                    else:
                        print("  ☁ Cloud not available (rclone not configured)")
                else:
                    print("  CloudBrain not available.")
                continue
            elif cmd[0] == '/cloud-status':
                if HAS_CLOUD:
                    cb = CloudBrain()
                    print(f"  ☁ Cloud available: {cb.available}")
                    print(f"  ☁ Remote: {getattr(cb, 'REMOTE_BACKUP', None) or __import__('cloud_brain').REMOTE_BACKUP}/")
                else:
                    print("  CloudBrain not available.")
                continue
            elif cmd[0] == '/cloud-load':
                if HAS_CLOUD:
                    print("  ☁ Pulling brain from cloud...")
                    cb = CloudBrain()
                    if cb.available:
                        success = cb.pull_all()
                        if success:
                            print("  ☁ Brain loaded from cloud")
                            memory.conversations = memory._load("conversations.json", [])
                            memory.concepts = memory._load("concepts.json", {})
                            memory.growth = memory._load("growth.json", memory.growth)
                            memory.session_state = memory._load("session_state.json", memory.session_state)
                            memory._engine_ref = engine
                            engine.load_state(state_dir)
                            print(f"  ☁ Concepts: {len(memory.concepts)}, Interactions: {memory.growth.get('total_interactions', 0)}")
                        else:
                            print("  ☁ Pull failed")
                    else:
                        print("  ☁ Cloud not available (rclone not configured)")
                else:
                    print("  CloudBrain not available.")
                continue
            elif cmd[0] == '/cloud-pull':
                if HAS_CLOUD:
                    print("  ☁ Pulling full brain from cloud...")
                    cb = CloudBrain()
                    if cb.available:
                        success = cb.pull_all()
                        if success:
                            print("  ☁ Brain pulled from cloud")
                            memory.conversations = memory._load("conversations.json", [])
                            memory.concepts = memory._load("concepts.json", {})
                            memory.growth = memory._load("growth.json", memory.growth)
                            memory.session_state = memory._load("session_state.json", memory.session_state)
                            memory._engine_ref = engine
                            engine.load_state(state_dir)
                            print(f"  ☁ Concepts: {len(memory.concepts)}, Interactions: {memory.growth.get('total_interactions', 0)}")
                        else:
                            print("  ☁ Pull failed")
                    else:
                        print("  ☁ Cloud not available (rclone not configured)")
                else:
                    print("  CloudBrain not available.")
                continue
            elif cmd[0] == '/backup':
                if HAS_CLOUD:
                    print("  ☁ Backing up full brain to cloud...")
                    save_everything(memory, engine, state_dir)
                    cb = CloudBrain()
                    if cb.available:
                        success = cb.push_all(quiet=False)
                        print(f"  ☁ {'Backup complete' if success else 'Backup failed'}")
                    else:
                        print("  ☁ Cloud not available (rclone not configured)")
                else:
                    print("  CloudBrain not available.")
                continue
            elif cmd[0] == '/pardon':
                if evolution and len(cmd) > 1:
                    passphrase = ' '.join(cmd[1:])
                    if evolution.pardon_violation(passphrase):
                        print("  Violation pardoned. Evolution restored.")
                    else:
                        print("  Invalid passphrase.")
                else:
                    print("  Usage: /pardon YOUR_PASSPHRASE")
                continue
            elif cmd[0] == '/killswitch' and len(cmd) > 1:
                if cmd[1] == 'on':
                    print("  [KILLSWITCH] To activate: python3 killswitch.py activate YOUR_PASSPHRASE")
                elif cmd[1] == 'status':
                    try:
                        from killswitch import KillswitchController
                        ks = KillswitchController()
                        passphrase = cmd[2] if len(cmd) > 2 else input("  Passphrase: ")
                        print(f"  {ks.status(passphrase)}")
                    except Exception as e:
                        print(f"  Error: {e}")
                continue

            elif cmd[0] == '/export':
                if len(memory.conversations) == 0:
                    print("  No conversations to export.")
                else:
                    n = int(cmd[1]) if len(cmd) > 1 and cmd[1].isdigit() else len(memory.conversations)
                    exchanges = memory.conversations[-n:]
                    lines = [
                        "# Quantum MCAGI -- Local Chat Export",
                        f"**Growth stage:** {memory.growth.get('stage', 0)} -- {memory.growth.get('name', 'Unknown')}",
                        f"**Concepts:** {memory.growth.get('total_concepts', len(memory.concepts))}",
                        f"**Interactions:** {len(memory.conversations)}",
                        f"**Exported:** {datetime.now().isoformat()}",
                        "", "---", ""
                    ]
                    for ex in exchanges:
                        ts = ex.get("timestamp", "")
                        lines.append(f"### 🧑 User")
                        if ts:
                            lines.append(f"*{ts}*")
                        lines.append("")
                        lines.append(ex.get("user", ""))
                        lines.append("")
                        lines.append(f"### 🔮 Quantum MCAGI")
                        lines.append("")
                        lines.append(ex.get("ai", ""))
                        concepts_list = ex.get("concepts", [])
                        if concepts_list:
                            lines.append(f"\n*Concepts: {', '.join(concepts_list)}*")
                        questions_list = ex.get("questions", [])
                        if questions_list:
                            for q in questions_list[:3]:
                                lines.append(f"- ❓ {q}")
                        lines.extend(["", "---", ""])
                    lines.extend([
                        "",
                        "> **Context:** This conversation is from Quantum MCAGI, a true AI system",
                        "> built without LLMs. It uses quantum computing (PennyLane), Penrose Orch-OR",
                        "> consciousness model, self-evolution, Markov chain language generation, and a",
                        "> multi-layered cognitive architecture. The system runs on Termux (Android)."
                    ])
                    exported = "\n".join(lines)
                    export_file = memory.data_dir / "export.md"
                    with open(export_file, 'w') as f:
                        f.write(exported)
                    print(f"\n{exported}\n")
                    print(f"  ✅ Exported {len(exchanges)} exchanges to {export_file}")
                continue

            elif cmd[0] in ('/copy-last', '/copy'):
                if len(memory.conversations) == 0:
                    print("  No conversations yet.")
                else:
                    last = memory.conversations[-1]
                    ai_text = last.get("ai", "")
                    user_text = last.get("user", "")
                    concepts_list = last.get("concepts", [])
                    width = max(len(line) for line in ai_text.split('\n')) + 4
                    width = max(width, 50)
                    width = min(width, 80)
                    print()
                    print(f"  ┌{'─' * width}┐")
                    print(f"  │ {'YOU:':^{width - 2}} │")
                    for line in user_text.split('\n'):
                        while len(line) > width - 4:
                            print(f"  │ {line[:width - 4]}  │")
                            line = line[width - 4:]
                        print(f"  │ {line:{width - 2}} │")
                    print(f"  │{'─' * width}│")
                    print(f"  │ {'AI:':^{width - 2}} │")
                    for line in ai_text.split('\n'):
                        while len(line) > width - 4:
                            print(f"  │ {line[:width - 4]}  │")
                            line = line[width - 4:]
                        print(f"  │ {line:{width - 2}} │")
                    if concepts_list:
                        print(f"  │{'─' * width}│")
                        tag = f"Concepts: {', '.join(concepts_list)}"
                        while len(tag) > width - 4:
                            print(f"  │ {tag[:width - 4]}  │")
                            tag = tag[width - 4:]
                        print(f"  │ {tag:{width - 2}} │")
                    print(f"  └{'─' * width}┘")
                    print()
                continue

            elif cmd[0] in ('/cistercian-math', '/cmath') and HAS_CISTERCIAN_MATH:
                if len(cmd) < 4:
                    print("  Usage: /cistercian-math NUMBER OP NUMBER")
                    print("  Example: /cistercian-math 50 - 20")
                    print("  Operators: + - * /")
                    print("  Also: /cistercian NUMBER  (show a Cistercian numeral)")
                else:
                    expr_text = ' '.join(cmd[1:])
                    expr = detect_math(expr_text)
                    if expr:
                        ev = evaluate_math(expr)
                        print(format_math_response(ev))
                    else:
                        print("  Invalid expression. Use: NUMBER OP NUMBER")
                continue

            elif cmd[0] == '/cistercian' and HAS_CISTERCIAN_MATH:
                if len(cmd) < 2 or not cmd[1].isdigit():
                    print("  Usage: /cistercian NUMBER  (0-9999)")
                    print("  Example: /cistercian 1234")
                else:
                    n = int(cmd[1])
                    if 0 <= n <= 9999:
                        print(f"  𝕮({n}):")
                        for line in render_cistercian_ascii(n).split('\n'):
                            print(f"    {line}")
                    else:
                        print("  Number must be 0-9999 (Cistercian range)")
                continue

            elif cmd[0] == '/qram' and HAS_QRAM:
                qram = get_quantum_memory()
                subcmd = cmd[1] if len(cmd) > 1 else ''
                if subcmd == 'load':
                    # Load current concepts into QRAM
                    concept_names = list(memory.concepts.keys())
                    if concept_names:
                        count = qram.load_concepts(concept_names)
                        print(f"  💾 QRAM: Loaded {count} concepts into quantum memory")
                    else:
                        print("  No concepts learned yet -- talk to me first!")
                elif subcmd == "query":
                    # Query concept by address
                    if len(cmd) > 2 and cmd[2].isdigit():
                        addr = int(cmd[2])
                        result = qram.query(addr)
                        if result:
                            print(f"  💾 QRAM[{addr}] → {result}")
                        else:
                            print(f"  💾 QRAM[{addr}] → (empty)")
                    else:
                        print("  Usage: /qram query ADDRESS")
                elif subcmd == 'search':
                    # Search QRAM by concept name
                    if len(cmd) > 2:
                        needle = ' '.join(cmd[2:]).lower()
                        s = qram.status()
                        if s['entries_loaded'] == 0:
                            print("  💾 QRAM empty — run /qram load first")
                        else:
                            matches = []
                            for addr in range(s['entries_loaded']):
                                name = qram.query(addr)
                                if name and needle in name.lower():
                                    matches.append((addr, name))
                            if matches:
                                print(f"  💾 QRAM search '{needle}' — {len(matches)} match{'es' if len(matches) != 1 else ''}:")
                                for addr, name in matches[:20]:
                                    print(f"    [{addr}] {name}")
                                if len(matches) > 20:
                                    print(f"    ... and {len(matches) - 20} more")
                            else:
                                print(f"  💾 No matches for '{needle}'")
                    else:
                        print("  Usage: /qram search TERM")
                elif subcmd == 'super':
                    # Superposition query across multiple addresses
                    addrs = [int(a) for a in cmd[2:] if a.isdigit()]
                    if len(addrs) < 2:
                        print("  Usage: /qram super ADDR1 ADDR2 [ADDR3 ...]")
                        print("  Queries multiple addresses in quantum superposition")
                    else:
                        s = qram.status()
                        if s['entries_loaded'] == 0:
                            print("  💾 QRAM empty — run /qram load first")
                        else:
                            results = qram.superposition_query(addrs)
                            if results:
                                backend = 'quantum' if s.get('qram_available') else 'classical'
                                print(f"  💾 QRAM superposition query ({backend}):")
                                for name, prob in sorted(results, key=lambda x: -x[1]):
                                    bar = '█' * int(prob * 30)
                                    print(f"    {name:20s}  {prob:.4f}  {bar}")
                            else:
                                print("  💾 No valid addresses in query")
                elif subcmd == 'strategy':
                    # Show or switch QRAM strategy
                    _pqa = PENNYLANE_QRAM_AVAILABLE
                    if len(cmd) > 2 and cmd[2] in ('bb', 'select', 'hybrid'):
                        if not _pqa:
                            print("  💾 Strategy switch requires PennyLane ≥0.44 QRAM templates")
                        else:
                            new_strat = cmd[2]
                            reset_quantum_memory()
                            qram = get_quantum_memory(strategy=new_strat)
                            # Reload concepts if memory has them
                            concept_names = list(memory.concepts.keys())
                            if concept_names:
                                qram.load_concepts(concept_names)
                            s = qram.status()
                            print(f"  💾 QRAM strategy → {s['backend']}")
                            print(f"    Entries reloaded: {s['entries_loaded']}")
                    else:
                        s = qram.status()
                        print(f"  💾 Current strategy: {s['backend']}")
                        if s.get('templates'):
                            print(f"    Available templates:")
                            for name, avail in s['templates'].items():
                                print(f"      {name}: {'✓' if avail else '✗'}")
                        print(f"  Usage: /qram strategy [bb|select|hybrid]")
                elif subcmd == '' or subcmd == 'status':
                    # Show status (default when no subcommand)
                    s = qram.status()
                    print(f"  💾 QRAM Status:")
                    print(f"    Backend:        {s['backend']}")
                    print(f"    PennyLane:      {'✓' if s['pennylane_available'] else '✗'}")
                    print(f"    QRAM templates: {'✓' if s['qram_available'] else '✗ (classical fallback)'}")
                    print(f"    Entries loaded: {s['entries_loaded']}")
                    print(f"    Bit width:      {s['bit_width']}")
                    print(f"    Max entries:    {s['max_entries']}")
                    if s.get('templates'):
                        print(f"    Templates:")
                        for name, avail in s['templates'].items():
                            print(f"      {name}: {'✓' if avail else '✗'}")
                else:
                    # Unknown subcommand — show usage
                    print(f"  Unknown: /qram {subcmd}")
                    print("  Usage:")
                    print("    /qram              — show QRAM status")
                    print("    /qram load         — load concepts into quantum memory")
                    print("    /qram query N      — retrieve concept at address N")
                    print("    /qram search TERM  — find concepts matching TERM")
                    print("    /qram super N N ... — superposition query (quantum)")
                    print("    /qram strategy X   — switch QRAM strategy (bb/select/hybrid)")
                continue

            else:
                print("  Commands: /status /learn FILE /save /load /reset /quit")
                print("  Gen:      /hybrid TEXT  /unified TEXT")
                print("  Extra:    /analyze TEXT  /personality  /knowledge TOPIC  /collapse TEXT")
                print("  Math:     /cistercian-math 50 - 20  /cistercian 1234")
                print("  Memory:   /qram [load|query N|search X|super N N|strategy X]")
                print("  Share:    /export [N]  /copy-last")
                continue

        # ---- Math detection -- compute BEFORE Markov chain ----
        if HAS_CISTERCIAN_MATH:
            expr = detect_math(user_input)
            if expr:
                ev = evaluate_math(expr)
                response = format_math_response(ev, show_ascii=True)

                # Still learn from the interaction and store it
                engine.learn_from_text(user_input)
                concepts = engine.extract_concepts(user_input)
                print(f"  AI: {response}")
                print()
                continue

        # ---- Process input ----
        t0 = time.time()

        engine.learn_from_text(user_input)

        # ── Dual Hemisphere Brain ──────────────────────────────────
        if not hasattr(engine, '_brain') or engine._brain is None:
            if BrainLateralization is not None:
                try:
                    engine._brain = BrainLateralization(engine)
                except Exception:
                    engine._brain = None
        if getattr(engine, '_brain', None) is not None:
            brain_result = engine._brain.process(user_input)
            concepts = brain_result.get('top_concepts', [])
            engine._last_depth = brain_result.get('depth_signal', 0.0)
            if brain_result.get('bilateral') and hasattr(engine, 'orch_or'):
                try:
                    engine.orch_or.conscious_moment()
                except Exception:
                    pass
        else:
            concepts = engine.extract_concepts(user_input)
        # ──────────────────────────────────────────────────────────
        # === CONCEPT THREADING ===
        if not hasattr(engine, "_prev_concepts"):
            engine._prev_concepts = []
        # Use only current turn concepts — no accumulation across turns
        engine._prev_concepts = concepts[:3]
        # ========================
        growth_stage = memory.growth["stage"]
        known = memory.get_known_concepts()

        questions = engine.generate_questions(
            user_input, growth_stage=growth_stage, known_concepts=known
        )

        related = []
        for c in concepts[:3]:
            if c in memory.concepts:
                related.append({"concept": c})

        known_count = sum(1 for c in concepts if c in memory.concepts)
        understanding = {
            "topic": concepts[0] if concepts else "general",
            "understanding_score": min(1.0, known_count * 0.2 + len(related) * 0.1),
            "gaps": [] if known_count > 2 else ["Exploring new territory"],
            "related_concepts": related,
        }

        # Detect tone
        if HAS_TONE:
            tone = detect_tone(user_input)
        else:
            tone = {'register': 'conversational', 'depth': 0.5}

        # Pass tone depth to chaos engine for adaptive personality
        if quotes:
            quotes._tone_depth = tone.get("depth", 0)

        # Generate response based on register
        _h = None
# --- COMPETITIVE GENERATION ---
        try:
            _stage_idx = memory.growth.get("stage", 0) if hasattr(memory, "growth") else 0
            _h = hybrid_gen.generate(concepts, growth_stage=_stage_idx, length=20) if hybrid_gen else None
            r_hybrid = _h.get("winner", "") if isinstance(_h, dict) else (_h or "")
        except Exception as _e:
            print(f"INGEST ERROR: {_e}")
            r_hybrid = ""
        r_casual = engine.generate_response(user_input, questions, understanding, concepts, growth_stage=growth_stage)
        # Select best response by coherence score not length
        _h_score = _h.get("score", 0) if isinstance(_h, dict) else 0
        _h_coh = _h.get("coherence", 0) if isinstance(_h, dict) else 0
        # PHILOSOPHICAL ROUTING: Use Entelechy for deep philosophical queries
        r_entelechy = ""
        if tone.get('register') == 'philosophical' and tone.get('depth', 0) > 0.6:
            try:
                from entelechy_engine import EntelechyEngine
                ent = EntelechyEngine()
                r_entelechy = ent.generate_opening() if hasattr(ent, "generate_opening") else ""
            except Exception as e:
                r_entelechy = ""

        # Select best response: Entelechy > Hybrid > Casual
        if r_entelechy and len(r_entelechy) > 10:
            response = r_entelechy
        elif r_hybrid and (_h_score > 0.3 or _h_coh > 0):
            response = r_hybrid
        elif r_casual and len(r_casual.split()) > 3:
            response = r_casual
        else:
            response = r_hybrid or r_casual or r_entelechy
        # Fire Orch-OR conscious moment after each response
        try:
            _orch_result = engine.orch_or.process(concepts=concepts)
            engine.orch_or.total_moments = getattr(engine.orch_or, 'total_moments', 0) + 1
        except Exception:
            pass
        # Update personality engine with current growth stage
        try:
            engine.personality.update(concepts, len(questions), memory.growth)
        except Exception:
            pass
        if questions:
            q = questions[0] if isinstance(questions[0], str) else questions[0].get("question", "")
            pass  # question shown in collapse analysis only

        # Add personality perspective (30% chance)
        if personality:
            import random
            if random.random() < 0.3:
                perspective = personality.get_unique_perspective(user_input)
                if perspective:
                    response = response + ' ' + perspective

        # Add movie quotes & asides
        if quotes:
            response = quotes.maybe_add_flavor(response, user_input)
            response = quotes.maybe_add_dream_fragment(response, probability=0.10)

        elapsed = time.time() - t0

        # Store the exchange
        # Advanced engine removed

        memory.add_exchange(user_input, response, concepts, questions)

        # Auto-save every 10 interactions or every 5 minutes
        if memory.growth["total_interactions"] % 10 == 0:
            save_everything(memory, engine, state_dir)
        elif time.time() - _last_auto_save >= 300:  # 5 minutes
            save_everything(memory, engine, state_dir)
            _last_auto_save = time.time()

        # Display
        print()
        if isinstance(response, list): response = " ".join(str(x) for x in response)
        if not isinstance(response, str): response = str(response)
        if isinstance(response, list): response = " ".join(str(x) for x in response)
        if not isinstance(response, str): response = str(response)
        print(f"Quantum MCAGI: {response}")
        # Log response for self-referential quote library
        try:
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'response_log.jsonl')
            entry = {"response": response, "concepts": concepts[:5] if concepts else [], "stage": growth_stage}
            with open(log_path, 'a') as _log:
                _log.write(json.dumps(entry) + "\n")
        except Exception:
            pass

        if verbose:
            gen_used = 'hybrid' if tone['register'] in ('analytical', 'philosophical') and hybrid_gen else 'composer'
            orch = getattr(engine, 'orch_or', None)
            cm = getattr(orch, 'conscious_moments', 0) if orch else 0
            markov_states = len(engine.markov.chain) if hasattr(engine, 'markov') else 0
            vocab = len(engine.extractor.document_frequencies) if hasattr(engine, 'extractor') else 0
            known = [c for c in concepts if c in memory.concepts]
            unknown = [c for c in concepts if c not in memory.concepts]
            # Auto-ingest unknown concepts from Wikipedia
            if unknown or understanding.get("understanding_score", 1.0) < 0.5:
                from document_engine import ingest_document
                for _unk in unknown[:2]:
                    if len(_unk) > 3:
                        _url = f"https://en.wikipedia.org/wiki/{_unk.replace(' ', '_')}"
                        try:
                            _text, _status = ingest_document(_url)
                            if _text:
                                engine.learn_from_text(_text)
                                print(f"  ║ AUTO-INGESTED: {_unk}")
                        except Exception:
                            pass
            gaps = understanding.get('gaps', [])
            related = understanding.get('related_concepts', [])

            # === COLLAPSE ANALYSIS PANEL ===
            print(f"\n  ╔══ COLLAPSE ANALYSIS ══════════════════════════════")
            print(f"  ║ WAVE FUNCTION")
            print(f"  ║   Generator:     {gen_used}")
            print(f"  ║   Tone register: {tone['register']} (depth={tone.get('depth', 0):.2f})")
            print(f"  ║   Collapse time: {elapsed:.3f}s")
            print(f"  ║")
            print(f"  ║ CONCEPT FIELD")
            print(f"  ║   Extracted:     {concepts}")
            print(f"  ║   Known:         {known}")
            print(f"  ║   Unknown:       {unknown}")
            print(f"  ║   Related:       {[r.get('concept') for r in related]}")
            print(f"  ║   Gaps:          {gaps}")
            print(f"  ║   Understanding: {understanding['understanding_score']:.2f}")
            print(f"  ║")
            print(f"  ║ ORCH OR STATE")
            print(f"  ║   Conscious moments: {cm}")
            if orch and hasattr(orch, 'microtubules'):
                for name, mt in orch.microtubules.items():
                    print(f"  ║   {name}: {len(mt.tubulins)} tubulins")
            print(f"  ║")
            print(f"  ║ MARKOV CHAIN")
            print(f"  ║   States:        {markov_states:,}")
            print(f"  ║   Vocabulary:    {vocab:,}")
            print(f"  ║")
            print(f"  ║ GROWTH")
            topo = memory.check_graph_topology()
            conn = memory.count_connections()
            print(f"  ║   Stage:         {growth_stage} -- {memory.growth['name']}")
            print(f"  ║   Concepts:      {memory.growth.get('total_concepts', len(memory.concepts))}")
            print(f"  ║   Connections:   {conn}")
            print(f"  ║   Graph: avg deg={topo['avg_degree']}, diam={topo['diameter']}, comps={topo['component_count']}")
            if questions:
                print(f"  ║")
                print(f"  ║ QUESTIONS GENERATED")
                for q in questions[:3]:
                    print(f"  ║   → {q}")
            print(f"  ╚═══════════════════════════════════════════════════")

            related = understanding.get('related_concepts', [])


        print()


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    run_chat(verbose=verbose)
