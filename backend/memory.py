"""
Local Memory System
JSON-file backed memory — stores conversations, concepts, and growth tracking.
Two-track growth system: Knowledge Track + Communication Track.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from personality_engine import GROWTH_STAGES, KNOWLEDGE_THRESHOLDS, COMMUNICATION_THRESHOLDS


class LocalMemory:
    """JSON-file backed memory for conversations and two-track growth."""

    def __init__(self, data_dir: str = "~/.quantum-mcagi"):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.conversations: List[Dict] = self._load("conversations.json", [])
        self.concepts: Dict[str, Dict] = self._load("concepts.json", {})
        self.growth: Dict = self._load("growth.json", self._default_growth())
        self.analyzer_scores: List[Dict] = self._load("analyzer_scores.json", [])

        self._migrate_growth()

    def _default_growth(self) -> Dict:
        return {
            "stage": 0,
            "name": "Nascent",
            "total_interactions": 0,
            "total_concepts": 0,
            "total_questions_asked": 0,
            "total_insights": 0,
            "knowledge_track": {
                "connections": 0,
                "avg_degree": 0.0,
                "domains": 0,
                "diameter": 0,
                "stage": 0,
            },
            "communication_track": {
                "avg_score": 0.0,
                "total_samples": 0,
                "score_sum": 0.0,
                "stage": 0,
            },
        }

    def _migrate_growth(self):
        needs_reconcile = False
        if "knowledge_track" not in self.growth:
            self.growth["knowledge_track"] = {
                "connections": 0,
                "avg_degree": 0.0,
                "domains": 0,
                "diameter": 0,
                "stage": 0,
            }
            needs_reconcile = True
        if "communication_track" not in self.growth:
            self.growth["communication_track"] = {
                "avg_score": 0.0,
                "total_samples": 0,
                "score_sum": 0.0,
                "stage": 0,
            }
            needs_reconcile = True

        if needs_reconcile:
            self._update_knowledge_track()
            self._recompute_communication_track()
            kt_stage = self.growth["knowledge_track"]["stage"]
            ct_stage = self.growth["communication_track"]["stage"]
            combined = min(kt_stage, ct_stage)
            if self.growth["stage"] > combined:
                self.growth["stage"] = combined
                for s, name, *_ in GROWTH_STAGES:
                    if s == combined:
                        self.growth["name"] = name
                        break

    def _recompute_communication_track(self):
        ct = self.growth["communication_track"]
        if self.analyzer_scores:
            ct["total_samples"] = len(self.analyzer_scores)
            ct["score_sum"] = sum(s.get("composite", 0.0) for s in self.analyzer_scores)
            ct["avg_score"] = ct["score_sum"] / ct["total_samples"]
            self._update_communication_track()

    def _load(self, filename: str, default):
        filepath = self.data_dir / filename
        if filepath.exists():
            try:
                with open(filepath) as f:
                    return json.load(f)
            except Exception:
                return default
        return default

    def _save(self, filename: str, data):
        filepath = self.data_dir / filename
        try:
            from system_safety import atomic_write_json
            atomic_write_json(str(filepath), data, indent=2)
        except ImportError:
            # Fallback if system_safety unavailable for any reason
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

    def save_all(self):
        self._save("conversations.json", self.conversations[-500:])
        self._save("concepts.json", self.concepts)
        self._save("growth.json", self.growth)
        self._save("analyzer_scores.json", self.analyzer_scores[-200:])

    def add_exchange(
        self,
        user_input: str,
        response: str,
        concepts: List[str],
        questions: List[str],
    ):
        self.conversations.append({
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "ai": response,
            "concepts": concepts,
            "questions": questions,
        })
        self.growth["total_interactions"] += 1
        self.growth["total_questions_asked"] += len(questions)

        for c in concepts:
            if c in self.concepts:
                self.concepts[c]["count"] += 1
                self.concepts[c]["strength"] = min(10.0, self.concepts[c]["strength"] + 0.1)
            else:
                self.concepts[c] = {
                    "count": 1,
                    "strength": 1.0,
                    "first_seen": datetime.now().isoformat(),
                    "edges": [],
                }
                self.growth["total_concepts"] += 1

        for i, c1 in enumerate(concepts):
            for c2 in concepts[i + 1:]:
                if c1 in self.concepts and c2 in self.concepts:
                    edges1 = self.concepts[c1].get("edges", [])
                    edges2 = self.concepts[c2].get("edges", [])
                    if c2 not in edges1:
                        edges1.append(c2)
                        self.concepts[c1]["edges"] = edges1
                    if c1 not in edges2:
                        edges2.append(c1)
                        self.concepts[c2]["edges"] = edges2

        self._update_knowledge_track()
        self._check_stage()

        if self.growth["total_interactions"] % 10 == 0:
            self.save_all()

    def ingest_concepts(self, concepts: List[str]):
        for c in concepts:
            if c in self.concepts:
                self.concepts[c]["count"] += 1
                self.concepts[c]["strength"] = min(10.0, self.concepts[c]["strength"] + 0.1)
            else:
                self.concepts[c] = {
                    "count": 1,
                    "strength": 1.0,
                    "first_seen": datetime.now().isoformat(),
                    "edges": [],
                }
                self.growth["total_concepts"] += 1

        for i, c1 in enumerate(concepts):
            for c2 in concepts[i + 1:]:
                if c1 in self.concepts and c2 in self.concepts:
                    edges1 = self.concepts[c1].get("edges", [])
                    edges2 = self.concepts[c2].get("edges", [])
                    if c2 not in edges1:
                        edges1.append(c2)
                        self.concepts[c1]["edges"] = edges1
                    if c1 not in edges2:
                        edges2.append(c1)
                        self.concepts[c2]["edges"] = edges2

        self._update_knowledge_track()
        self._check_stage()

    def record_analyzer_score(self, score_data: Dict):
        self.analyzer_scores.append({
            "timestamp": datetime.now().isoformat(),
            **score_data,
        })

        ct = self.growth["communication_track"]
        ct["total_samples"] += 1
        ct["score_sum"] = ct.get("score_sum", 0.0) + score_data.get("composite", 0.0)
        ct["avg_score"] = ct["score_sum"] / ct["total_samples"]

        self._update_communication_track()
        self._check_stage()

    def _update_knowledge_track(self):
        kt = self.growth["knowledge_track"]

        adjacency: Dict[str, List[str]] = {}
        domains = set()
        total_edges = 0

        for concept, data in self.concepts.items():
            edges = data.get("edges", [])
            valid_edges = [e for e in edges if e in self.concepts]
            adjacency[concept] = valid_edges
            total_edges += len(valid_edges)

            tokens = concept.lower().split()
            for token in tokens:
                if len(token) >= 3:
                    domains.add(token[:4])

        num_nodes = len(adjacency)
        total_connections = total_edges // 2
        avg_degree = total_edges / max(num_nodes, 1)

        diameter = self._compute_graph_diameter(adjacency)

        kt["connections"] = total_connections
        kt["avg_degree"] = round(avg_degree, 3)
        kt["domains"] = len(domains)
        kt["diameter"] = diameter

        for stage_idx in range(6, -1, -1):
            thresh = KNOWLEDGE_THRESHOLDS[stage_idx]
            if (kt["connections"] >= thresh["connections"]
                    and kt["avg_degree"] >= thresh["avg_degree"]
                    and kt["domains"] >= thresh["domains"]
                    and diameter >= thresh.get("diameter", 0)):
                kt["stage"] = stage_idx
                break

    def _compute_graph_diameter(self, adjacency: Dict[str, List[str]]) -> int:
        if len(adjacency) < 2:
            return 0

        nodes_with_edges = [n for n, edges in adjacency.items() if edges]
        if not nodes_with_edges:
            return 0

        max_shortest = 0
        sample = nodes_with_edges[:20] if len(nodes_with_edges) > 20 else nodes_with_edges

        for start in sample:
            visited = {start: 0}
            queue = [start]
            qi = 0
            while qi < len(queue):
                current = queue[qi]
                qi += 1
                for neighbor in adjacency.get(current, []):
                    if neighbor not in visited:
                        visited[neighbor] = visited[current] + 1
                        queue.append(neighbor)
                        if visited[neighbor] > max_shortest:
                            max_shortest = visited[neighbor]

        return max_shortest

    def _update_communication_track(self):
        ct = self.growth["communication_track"]
        for stage_idx in range(6, -1, -1):
            thresh = COMMUNICATION_THRESHOLDS[stage_idx]
            if (ct["avg_score"] >= thresh["avg_score"]
                    and ct["total_samples"] >= thresh["min_samples"]):
                ct["stage"] = stage_idx
                break

    def _check_stage(self):
        g = self.growth
        kt_stage = g["knowledge_track"]["stage"]
        ct_stage = g["communication_track"]["stage"]

        combined_stage = min(kt_stage, ct_stage)

        if combined_stage > g["stage"]:
            g["stage"] = combined_stage
            for s, name, *_ in GROWTH_STAGES:
                if s == combined_stage:
                    g["name"] = name
                    break

    def get_known_concepts(self) -> List[str]:
        return list(self.concepts.keys())

    def get_top_concepts(self, n: int = 10) -> List[str]:
        if not self.concepts:
            return []
        top = sorted(self.concepts.items(), key=lambda x: x[1]['strength'], reverse=True)
        return [c for c, _ in top[:n]]

    def get_recent_context(self, n: int = 5) -> Dict:
        recent = self.conversations[-n:] if self.conversations else []
        recent_concepts = []
        recent_topics = []
        last_ai_response = ""
        last_user_input = ""

        for ex in recent:
            recent_concepts.extend(ex.get("concepts", []))
            if ex.get("concepts"):
                recent_topics.append(ex["concepts"][0])
            last_ai_response = ex.get("ai", "")
            last_user_input = ex.get("user", "")

        seen = set()
        unique_concepts = []
        for c in reversed(recent_concepts):
            if c not in seen:
                seen.add(c)
                unique_concepts.append(c)
        unique_concepts.reverse()

        return {
            "recent_exchanges": recent,
            "recent_concepts": unique_concepts[-15:],
            "recent_topics": recent_topics,
            "last_ai_response": last_ai_response,
            "last_user_input": last_user_input,
            "exchange_count": len(self.conversations),
        }

    def get_history(self, limit: int = 20) -> List[Dict]:
        return self.conversations[-limit:]

    def get_analyzer_history(self, limit: int = 20) -> List[Dict]:
        return self.analyzer_scores[-limit:]

    def reset(self):
        self.conversations = []
        self.concepts = {}
        self.growth = self._default_growth()
        self.analyzer_scores = []
        self.save_all()

    def get_status(self) -> dict:
        """Return status dict for /status command."""
        g = self.growth
        kt = g.get("knowledge_track", {})
        ct = g.get("communication_track", {})
        return {
            "growth": {
                "stage": g.get("stage", 0),
                "name": g.get("name", "Unknown"),
                "total_interactions": g.get("total_interactions", 0),
                "total_concepts": g.get("total_concepts", 0),
                "total_questions_asked": g.get("total_questions_asked", 0),
                "total_insights": g.get("total_insights", 0),
                "knowledge_track": kt,
                "communication_track": ct,
            },
            "concepts": {
                "total": len(self.concepts),
                "top_strength": self.get_top_concepts(15),
            },
            "recent_exchanges": len(self.conversations),
        }
