#!/usr/bin/env python3
"""
Quantum MCAGI — Local Chat (Termux)
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
    /quit         - Save and exit
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quantum_language_engine import QuantumLanguageEngine
try:
    from self_evolution_core import SelfEvolutionEngine
    HAS_EVOLUTION = True
except ImportError:
    HAS_EVOLUTION = False

try:
    from document_ingester import handle_ingest_command
    HAS_INGEST = True
except ImportError:
    HAS_INGEST = False

try:
    from self_research import SelfResearchEngine
    HAS_RESEARCH = True
except ImportError:
    HAS_RESEARCH = False

try:
    from wolfram_cloud import cloud_save, cloud_load, cloud_status
    HAS_CLOUD = True
except ImportError:
    HAS_CLOUD = False

# Optional imports — degrade gracefully
try:
    from hybrid_generator import create_hybrid_generator
    HAS_HYBRID = True
except ImportError:
    HAS_HYBRID = False

try:
    from unified_generator import create_unified_generator
    HAS_UNIFIED = True
except ImportError:
    HAS_UNIFIED = False

try:
    from quote_engine import get_quote_engine
    HAS_QUOTES = True
except ImportError:
    HAS_QUOTES = False

try:
    from personality_engine import get_personality_engine
    HAS_PERSONALITY = True
except ImportError:
    HAS_PERSONALITY = False

try:
    from knowledge_base import get_knowledge_base
    HAS_KNOWLEDGE = True
except ImportError:
    HAS_KNOWLEDGE = False

try:
    from text_analyzer import get_text_analyzer
    HAS_ANALYZER = True
except ImportError:
    HAS_ANALYZER = False

try:
    from semantic_collapse_engine import SemanticCollapseEngine
    HAS_COLLAPSE = True
except ImportError:
    HAS_COLLAPSE = False

try:
    from tone_detector import detect_tone
    HAS_TONE = True
except ImportError:
    HAS_TONE = False

try:
    from library import handle_library_command
    HAS_LIBRARY = True
except ImportError:
    HAS_LIBRARY = False


class LocalMemory:
    """JSON-file backed memory for local chat."""

    # All 12 tracks must be met simultaneously to advance.
    # High watermark protection on diameter and avg_degree — earned progress never regresses.
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
        # High watermark protection — earned topology progress never regresses
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
        self.growth["total_questions_asked"] += len(questions)
        self.session_state["total_lifetime_interactions"] = self.session_state.get(
            "total_lifetime_interactions", 0) + 1

        # Track new concepts and ensure relationships field
        for c in concepts:
            c_lower = c.lower()
            if c_lower in self.concepts:
                self.concepts[c_lower]["count"] += 1
                self.concepts[c_lower]["strength"] = min(10.0, self.concepts[c_lower]["strength"] + 0.1)
            else:
                self.concepts[c_lower] = {
                    "count": 1,
                    "strength": 1.0,
                    "first_seen": datetime.now().isoformat(),
                    "relationships": []  # initialize relationships
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
                        self.concepts[c1]["relationships"].append(c2)
                    # Add c1 to c2's relationships (undirected graph)
                    if c1 not in self.concepts[c2]["relationships"]:
                        self.concepts[c2]["relationships"].append(c1)

        # Detect insights: response mentions 2+ known concepts
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
        High watermark protection on diameter and avg_degree — earned progress never regresses."""
        metrics = {
            "total_concepts": self.growth.get("total_concepts", 0),
            "total_connections": self.count_connections(),
            "total_questions": self.growth.get("total_questions_asked", 0),
            "total_insights": self.growth.get("total_insights", 0),
            "total_interactions": self.growth.get("total_interactions", 0),
            "distinct_domains": 0,
            "markov_states": 0,
            "transitions": 0,
            "comm_score": 0,
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
        try:
            from quantum_language_engine import QuantumLanguageEngine
            lang = QuantumLanguageEngine()
            if lang.markov and lang.markov.trained:
                metrics["markov_states"] = len(lang.markov.chain)
                metrics["transitions"] = lang.markov.total_tokens
        except Exception:
            pass

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

    def get_known_concepts(self):
        return list(self.concepts.keys())


def save_everything(memory, engine, state_dir):
    """Save all state to disk."""
    memory.save_all()
    engine.save_state(state_dir)
    if getattr(engine, "_has_orch_or", False):
        memory.save_orch_or(engine.orch_or)


EVOLUTION_ENABLED = True  # Killswitch

def run_chat(verbose=False):
    """run_chat - Auto-documented by self-evolution."""
    print()
    print("  Quantum MCAGI - Local Chat")
    print("  Real algorithms. No templates. No LLM.")
    print("  /status  /learn FILE  /save  /load  /quit")
    print("  /export [N]  /copy-last  — share conversations")
    print()

    # Initialize all systems
    engine = QuantumLanguageEngine()
    memory = LocalMemory()

    hybrid_gen = create_hybrid_generator(engine) if HAS_HYBRID else None
    unified_gen = create_unified_generator(engine) if HAS_UNIFIED else None
    quotes = get_quote_engine() if HAS_QUOTES else None
    personality = get_personality_engine() if HAS_PERSONALITY else None
    knowledge = get_knowledge_base() if HAS_KNOWLEDGE else None
    analyzer = get_text_analyzer() if HAS_ANALYZER else None
    collapse = SemanticCollapseEngine() if HAS_COLLAPSE else None
    evolution = SelfEvolutionEngine() if HAS_EVOLUTION else None
    if evolution:
        print("  Self-Evolution: ACTIVE")
        # Check for covenant violation record
        import json
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
            except:
                pass
    research = SelfResearchEngine() if HAS_RESEARCH else None
    if research:
        print("  Self-Research: ACTIVE")

    # Load saved state
    state_dir = str(memory.data_dir / "engine_state")
    if engine.load_state(state_dir):
        print(f"  Loaded saved state from {state_dir}")

    if getattr(engine, "_has_orch_or", False):
        memory.load_orch_or(engine.orch_or)

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
    print()

    _last_auto_save = time.time()

    while True:
        try:
            user_input = input("You: ").strip()
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
                    print(f"  Autonomous research started — {minutes} min")
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
            elif cmd[0] == '/evolve':
                if evolution and evolution.is_evolution_locked():
                    continue
                elif evolution:
                    print("  [EVOLUTION] Analyzing code for improvements...")
                    import asyncio
                    results = asyncio.run(evolution.auto_evolve())
                    print(f"  Found: {len(results['improvements_found'])} improvements")
                    print(f"  Applied: {len(results['changes_made'])} changes")
                    print(f"  Skipped: {len(results['skipped'])}")
                    if results['errors']:
                        print(f"  Errors: {len(results['errors'])}")
                else:
                    print("  Self-Evolution not available.")
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
                engine = QuantumLanguageEngine()
                hybrid_gen = create_hybrid_generator(engine) if HAS_HYBRID else None
                unified_gen = create_unified_generator(engine) if HAS_UNIFIED else None
                memory = LocalMemory()
                print("  Engine reset.")
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
                print(f"  Corpus docs: {engine.extractor.total_documents}")
                print(f"  Vocabulary size: {len(engine.extractor.word_frequencies)}")
                print()
                print("  --- ORCH OR (Penrose-Hameroff) ---")
                if getattr(engine, "_has_orch_or", False):
                    orch = {"note": "use get_system_state"}
                    print(f"  Status: ACTIVE")
                    print(f"  Conscious moments: {engine.orch_or.conscious_moments}")

                    for name, mt in engine.orch_or.microtubules.items():
                        print(f"    {name}: {len(mt.tubulins)} tubulins")



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
                    total_q = sum(len(v) for v in quotes.movie_quotes.values())
                    print(f"  Categories: {', '.join(quotes.movie_quotes.keys())}")
                    print(f"  Total quotes: {total_q}")
                    print(f"  Asides: {len(quotes.philosophical_asides)}")
                else:
                    print("  Not loaded")
                print()
                print("  --- KNOWLEDGE BASE ---")
                if knowledge:
                    topics = list(knowledge._build_topics().keys())
                    print(f"  Topics ({len(topics)}): {', '.join(topics[:10])}{'...' if len(topics) > 10 else ''}")
                else:
                    print("  Not loaded")
                print()
                print("  --- GENERATORS ---")
                print(f"  Hybrid: {'ACTIVE' if hybrid_gen else 'OFF'}")
                print(f"  Unified: {'ACTIVE' if unified_gen else 'OFF'}")
                print()
                print("  --- RESPONSE PIPELINE ---")
                print("  1. TF-IDF concept extraction")
                print(f"  2. Orch OR quantum encoding + collapse [{'ACTIVE' if getattr(engine, "_has_orch_or", False) else 'OFF'}]")
                print(f"  3. Bloom's taxonomy question gen (stage {g['stage']})")
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
                    result = handle_library_command(cmd, engine)
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
                    print("  Usage: /feed <category>   — process one category")
                    print("         /feed all          — process all categories")
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
                    print("  Saving to Wolfram Cloud...")
                    result = cloud_save(memory)
                    print(f"  {result}")
                else:
                    print("  Wolfram Cloud not available.")
                continue
            elif cmd[0] == '/cloud-status':
                if HAS_CLOUD:
                    print(f"  {cloud_status()}")
                else:
                    print("  Wolfram Cloud not available.")
                continue
            elif cmd[0] == '/cloud-load':
                if HAS_CLOUD:
                    result = cloud_load()
                    print(f"  {result}")
                else:
                    print("  Wolfram Cloud not available.")
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
                        "# Quantum MCAGI — Local Chat Export",
                        f"**Growth stage:** {memory.growth.get('stage', 0)} — {memory.growth.get('name', 'Unknown')}",
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

            else:
                print("  Commands: /status /learn FILE /save /load /reset /quit")
                print("  Gen:      /hybrid TEXT  /unified TEXT")
                print("  Extra:    /analyze TEXT  /personality  /knowledge TOPIC  /collapse TEXT")
                print("  Share:    /export [N]  /copy-last")
                continue

        # ---- Process input ----
        t0 = time.time()

        engine.learn_from_text(user_input)
        concepts = engine.extract_concepts(user_input)
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

        # Generate response based on register
        if tone['register'] in ('analytical', 'philosophical') and hybrid_gen:
            # Deep: hybrid quantum generation
            concept_scores = engine.extract_concepts(user_input)
            response = hybrid_gen.generate(
                user_input, concepts, concept_scores,
                min_words=10, max_words=25
            )
            # Append a question if appropriate
            if questions and (not getattr(engine, "_has_orch_or", False) or True):
                q = questions[0] if isinstance(questions[0], str) else questions[0].get('question', '')
                response = response + " " + q
        else:
            # Casual/conversational: tone-aware composer
            response = engine.generate_response(
                user_input, questions, understanding, concepts,
                growth_stage=growth_stage
            )

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
        memory.add_exchange(user_input, response, concepts, questions)

        # Auto-save every 10 interactions or every 5 minutes
        if memory.growth["total_interactions"] % 10 == 0:
            save_everything(memory, engine, state_dir)
        elif time.time() - _last_auto_save >= 300:  # 5 minutes
            save_everything(memory, engine, state_dir)
            _last_auto_save = time.time()

        # Display
        print()
        print(f"AI: {response}")

        if verbose:
            gen_used = 'hybrid' if tone['register'] in ('analytical', 'philosophical') and hybrid_gen else 'composer'
            orch = getattr(engine, 'orch_or', None)
            cm = getattr(orch, 'conscious_moments', 0) if orch else 0
            markov_states = len(engine.markov.chain) if hasattr(engine, 'markov') else 0
            vocab = len(engine.extractor.document_frequencies) if hasattr(engine, 'extractor') else 0
            known = [c for c in concepts if c in memory.concepts]
            unknown = [c for c in concepts if c not in memory.concepts]
            gaps = understanding.get('gaps', [])
            related = understanding.get('related_concepts', [])

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
            # Get topology
            topo = memory.check_graph_topology()
            conn = memory.count_connections()
            print(f"  ║   Stage:         {growth_stage} — {memory.growth['name']}")
            print(f"  ║   Concepts:      {memory.growth.get('total_concepts', len(memory.concepts))}")
            print(f"  ║   Connections:   {conn}")
            print(f"  ║   Graph: avg deg={topo['avg_degree']}, diam={topo['diameter']}, comps={topo['component_count']}")
            if questions:
                print(f"  ║")
                print(f"  ║ QUESTIONS GENERATED")
                for q in questions[:3]:
                    print(f"  ║   → {q}")
            print(f"  ╚═══════════════════════════════════════════════════")

        print()


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    run_chat(verbose=verbose)
