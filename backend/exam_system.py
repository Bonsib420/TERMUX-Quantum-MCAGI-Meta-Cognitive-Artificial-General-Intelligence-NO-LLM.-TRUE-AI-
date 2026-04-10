"""
🎓 EXAM SYSTEM — Knowledge Examination & Testing
=================================================
Tests the AI's knowledge through structured examinations.

Provides:
  - Concept recall tests (can the AI retrieve stored concepts?)
  - Relationship mapping (does it know connections between concepts?)
  - Domain coverage (which knowledge domains are strongest?)
  - Markov coherence (are generated sentences grammatically sound?)
  - Conversation memory (can it recall previous exchanges?)
  - Graph topology (is the concept graph well-connected?)
  - Cross-domain tests (can it link concepts across domains?)

Chat commands:
  /exam              — Run a full examination
  /exam DOMAIN       — Test a specific domain
  /exam summary      — Show exam history summary

API endpoints:
  POST /api/brain/exam         — Run examination
  GET  /api/brain/exam/summary — Get exam summary
"""

import random
import time
import math
import logging
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from datetime import datetime, timezone

logger = logging.getLogger("quantum_ai")


# ============================================================================
# TEST CATEGORIES
# ============================================================================

EXAM_CATEGORIES = [
    "concept_recall",
    "relationship_mapping",
    "domain_coverage",
    "markov_coherence",
    "conversation_memory",
    "graph_topology",
    "cross_domain",
]

DOMAIN_NAMES = [
    "philosophy", "physics", "computer_science",
    "biology", "mathematics", "psychology", "language",
]


class ExamResult:
    """Result of a single test question."""

    def __init__(self, category: str, question: str, passed: bool,
                 score: float = 0.0, details: str = ""):
        self.category = category
        self.question = question
        self.passed = passed
        self.score = score
        self.details = details
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict:
        return {
            "category": self.category,
            "question": self.question,
            "passed": self.passed,
            "score": self.score,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


class ExamSystem:
    """
    Knowledge examination engine for testing the AI's capabilities.
    """

    def __init__(self):
        self.history: List[Dict] = []
        self._exam_count = 0

    def run_exam(self, memory: Any, engine: Any = None,
                 domain: str = None,
                 categories: List[str] = None) -> Dict:
        """
        Run a knowledge examination.

        Args:
            memory: LocalMemory instance with concepts, exchanges, growth
            engine: QuantumLanguageEngine (optional, for Markov tests)
            domain: Specific domain to test (or None for all)
            categories: Specific categories to test (or None for all)

        Returns:
            Exam results dict with scores per category
        """
        start_time = time.time()
        self._exam_count += 1

        if categories is None:
            categories = EXAM_CATEGORIES

        results: List[ExamResult] = []

        for category in categories:
            if category == "concept_recall":
                results.extend(self._test_concept_recall(memory, domain))
            elif category == "relationship_mapping":
                results.extend(self._test_relationships(memory, domain))
            elif category == "domain_coverage":
                results.extend(self._test_domain_coverage(memory))
            elif category == "markov_coherence":
                results.extend(self._test_markov_coherence(engine))
            elif category == "conversation_memory":
                results.extend(self._test_conversation_memory(memory))
            elif category == "graph_topology":
                results.extend(self._test_graph_topology(memory))
            elif category == "cross_domain":
                results.extend(self._test_cross_domain(memory))

        # Compute scores
        elapsed = time.time() - start_time
        category_scores = defaultdict(lambda: {"passed": 0, "total": 0, "score_sum": 0.0})

        for r in results:
            cat = category_scores[r.category]
            cat["total"] += 1
            cat["score_sum"] += r.score
            if r.passed:
                cat["passed"] += 1

        # Overall score
        total_tests = len(results)
        total_passed = sum(1 for r in results if r.passed)
        overall_score = total_passed / total_tests if total_tests > 0 else 0.0

        exam_result = {
            "exam_number": self._exam_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed": round(elapsed, 3),
            "total_tests": total_tests,
            "total_passed": total_passed,
            "overall_score": round(overall_score, 4),
            "categories": {
                cat: {
                    "passed": data["passed"],
                    "total": data["total"],
                    "score": round(data["score_sum"] / data["total"], 4) if data["total"] > 0 else 0,
                }
                for cat, data in category_scores.items()
            },
            "details": [r.to_dict() for r in results],
        }

        self.history.append(exam_result)
        return exam_result

    def get_summary(self) -> Dict:
        """Get summary of all past exams."""
        if not self.history:
            return {"exams": 0, "message": "No exams taken yet"}

        scores = [e["overall_score"] for e in self.history]
        return {
            "exams": len(self.history),
            "latest_score": scores[-1],
            "best_score": max(scores),
            "average_score": round(sum(scores) / len(scores), 4),
            "trend": "improving" if len(scores) >= 2 and scores[-1] > scores[0] else "stable",
        }

    # ── Test Implementations ──

    def _test_concept_recall(self, memory: Any,
                              domain: str = None) -> List[ExamResult]:
        """Test: Can we recall stored concepts?"""
        results = []
        concepts = list(getattr(memory, 'concepts', {}).keys())

        if domain:
            concepts = [
                c for c in concepts
                if getattr(memory.concepts.get(c), 'metadata', {}).get('domain') == domain
            ]

        if not concepts:
            return [ExamResult("concept_recall", "No concepts available", False, 0.0)]

        # Sample up to 10 concepts
        sample = random.sample(concepts, min(10, len(concepts)))
        for concept in sample:
            exists = concept in memory.concepts
            results.append(ExamResult(
                "concept_recall",
                f"Recall: {concept}",
                exists,
                1.0 if exists else 0.0,
                "Found in concept store" if exists else "Not found",
            ))

        return results

    def _test_relationships(self, memory: Any,
                             domain: str = None) -> List[ExamResult]:
        """Test: Do concepts have connections?"""
        results = []
        concepts = getattr(memory, 'concepts', {})

        if len(concepts) < 2:
            return [ExamResult("relationship_mapping", "Too few concepts", False, 0.0)]

        concept_list = list(concepts.keys())
        sample = random.sample(concept_list, min(10, len(concept_list)))

        for concept in sample:
            data = concepts[concept]
            connections = 0
            if isinstance(data, dict):
                connections = len(data.get('connections', []))
            elif hasattr(data, 'connections'):
                connections = len(data.connections)

            has_connections = connections > 0
            results.append(ExamResult(
                "relationship_mapping",
                f"Connections for '{concept}'",
                has_connections,
                min(1.0, connections / 3.0),  # Normalize: 3+ connections = full score
                f"{connections} connections",
            ))

        return results

    def _test_domain_coverage(self, memory: Any) -> List[ExamResult]:
        """Test: Which knowledge domains are covered?"""
        results = []
        concepts = getattr(memory, 'concepts', {})

        domain_counts = defaultdict(int)
        for concept, data in concepts.items():
            domain = "general"
            if isinstance(data, dict):
                domain = data.get('metadata', {}).get('domain', 'general')
            elif hasattr(data, 'metadata'):
                domain = getattr(data.metadata, 'domain', 'general') if hasattr(data, 'metadata') else 'general'
            domain_counts[domain] += 1

        for domain_name in DOMAIN_NAMES:
            count = domain_counts.get(domain_name, 0)
            has_coverage = count > 0
            results.append(ExamResult(
                "domain_coverage",
                f"Domain: {domain_name}",
                has_coverage,
                min(1.0, count / 10.0),
                f"{count} concepts",
            ))

        return results

    def _test_markov_coherence(self, engine: Any) -> List[ExamResult]:
        """Test: Is the Markov chain producing coherent text?"""
        results = []

        if engine is None or not hasattr(engine, 'markov'):
            return [ExamResult("markov_coherence", "No engine available", False, 0.0)]

        markov = engine.markov
        if not hasattr(markov, 'generate') or not hasattr(markov, 'trained'):
            return [ExamResult("markov_coherence", "Markov not trained", False, 0.0)]

        if not markov.trained:
            return [ExamResult("markov_coherence", "Markov chain empty", False, 0.0)]

        # Generate 5 test sentences
        for i in range(5):
            try:
                text = markov.generate(max_words=20)
                words = text.split() if text else []
                has_words = len(words) >= 3
                results.append(ExamResult(
                    "markov_coherence",
                    f"Generation test {i + 1}",
                    has_words,
                    min(1.0, len(words) / 10.0),
                    f"Generated {len(words)} words: {text[:50]}..." if text else "Empty output",
                ))
            except Exception as e:
                results.append(ExamResult(
                    "markov_coherence",
                    f"Generation test {i + 1}",
                    False,
                    0.0,
                    f"Error: {e}",
                ))

        return results

    def _test_conversation_memory(self, memory: Any) -> List[ExamResult]:
        """Test: Can we recall previous conversations?"""
        results = []
        exchanges = getattr(memory, 'exchanges', [])

        if not exchanges:
            return [ExamResult("conversation_memory", "No exchanges stored", False, 0.0)]

        count = len(exchanges)
        results.append(ExamResult(
            "conversation_memory",
            f"Exchange count",
            count > 0,
            min(1.0, count / 50.0),
            f"{count} exchanges stored",
        ))

        # Check most recent exchanges are retrievable
        recent = exchanges[-min(5, len(exchanges)):]
        for ex in recent:
            has_response = bool(ex.get('response', ''))
            results.append(ExamResult(
                "conversation_memory",
                f"Recent exchange recall",
                has_response,
                1.0 if has_response else 0.0,
                "Exchange has response" if has_response else "Missing response",
            ))

        return results

    def _test_graph_topology(self, memory: Any) -> List[ExamResult]:
        """Test: Is the concept graph well-connected?"""
        results = []

        if hasattr(memory, 'check_graph_topology'):
            topo = memory.check_graph_topology()
        else:
            return [ExamResult("graph_topology", "No topology method", False, 0.0)]

        # Average degree
        avg_deg = topo.get('avg_degree', 0)
        results.append(ExamResult(
            "graph_topology",
            "Average degree",
            avg_deg >= 2.0,
            min(1.0, avg_deg / 5.0),
            f"avg_degree={avg_deg:.2f}",
        ))

        # Diameter
        diameter = topo.get('diameter', 0)
        results.append(ExamResult(
            "graph_topology",
            "Graph diameter",
            diameter >= 3,
            min(1.0, diameter / 8.0),
            f"diameter={diameter}",
        ))

        # Components
        components = topo.get('component_count', 0)
        total_concepts = len(getattr(memory, 'concepts', {}))
        ratio = components / total_concepts if total_concepts > 0 else 1.0
        well_connected = ratio < 0.5  # Less than half as many components as concepts
        results.append(ExamResult(
            "graph_topology",
            "Component ratio",
            well_connected,
            max(0.0, 1.0 - ratio),
            f"{components} components / {total_concepts} concepts",
        ))

        return results

    def _test_cross_domain(self, memory: Any) -> List[ExamResult]:
        """Test: Are there connections between different domains?"""
        results = []
        concepts = getattr(memory, 'concepts', {})

        if len(concepts) < 10:
            return [ExamResult("cross_domain", "Too few concepts", False, 0.0)]

        # Check for cross-domain connections
        cross_connections = 0
        total_checked = 0

        concept_list = list(concepts.keys())
        sample = random.sample(concept_list, min(20, len(concept_list)))

        for concept in sample:
            data = concepts[concept]
            concept_domain = "general"
            connections = []

            if isinstance(data, dict):
                concept_domain = data.get('metadata', {}).get('domain', 'general')
                connections = data.get('connections', [])
            elif hasattr(data, 'connections'):
                connections = list(data.connections) if hasattr(data, 'connections') else []

            for conn in connections[:5]:
                conn_name = conn if isinstance(conn, str) else conn.get('concept', '')
                if conn_name in concepts:
                    conn_data = concepts[conn_name]
                    conn_domain = "general"
                    if isinstance(conn_data, dict):
                        conn_domain = conn_data.get('metadata', {}).get('domain', 'general')
                    if conn_domain != concept_domain and conn_domain != "general":
                        cross_connections += 1
                    total_checked += 1

        ratio = cross_connections / total_checked if total_checked > 0 else 0.0
        results.append(ExamResult(
            "cross_domain",
            "Cross-domain connections",
            cross_connections > 0,
            min(1.0, ratio * 5),
            f"{cross_connections}/{total_checked} cross-domain links",
        ))

        return results


def format_exam_results(results: Dict) -> str:
    """Format exam results for terminal display."""
    lines = [
        f"\n  ╔══ KNOWLEDGE EXAM #{results['exam_number']} ══════════════════════════",
        f"  ║ Overall: {results['overall_score']:.1%} "
        f"({results['total_passed']}/{results['total_tests']} passed)",
        f"  ║ Time: {results['elapsed']:.1f}s",
        f"  ║",
    ]

    for cat, data in results.get("categories", {}).items():
        bar_len = int(data['score'] * 20)
        bar = '█' * bar_len + '░' * (20 - bar_len)
        lines.append(
            f"  ║ {cat:25s} [{bar}] {data['score']:.0%} "
            f"({data['passed']}/{data['total']})"
        )

    lines.append(f"  ╚═══════════════════════════════════════════════════")
    return '\n'.join(lines)


# Module-level singleton
_exam_system: Optional[ExamSystem] = None


def get_exam_system() -> ExamSystem:
    """Get or create the exam system singleton."""
    global _exam_system
    if _exam_system is None:
        _exam_system = ExamSystem()
    return _exam_system
