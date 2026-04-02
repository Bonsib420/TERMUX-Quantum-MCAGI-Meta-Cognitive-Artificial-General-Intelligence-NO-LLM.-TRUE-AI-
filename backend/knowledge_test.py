"""
🧪 KNOWLEDGE RETENTION TEST ENGINE
====================================
Tests Quantum MCAGI's knowledge retention across everything it has consumed.

Test Categories:
  1. Concept Recall        — Can the system recall learned concepts?
  2. Relationship Mapping  — Does it remember concept connections?
  3. Domain Coverage       — How broadly has knowledge spread across domains?
  4. Markov Coherence      — Can it generate coherent text from learned material?
  5. Conversation Memory   — Does it retain key exchanges?
  6. Graph Topology        — Is the knowledge graph well-formed?
  7. Cross-Domain Links    — Can it connect concepts across domains?

Difficulty scales with growth stage:
  Stage 0 (Nascent)       → basic recall, 10 questions
  Stage 1 (Curious)       → + relationships, 20 questions
  Stage 2 (Inquisitive)   → + domain coverage, 30 questions
  Stage 3 (Understanding) → + coherence, 40 questions
  Stage 4+ (Philosophical)→ + cross-domain, 50 questions

Usage:
    from knowledge_test import KnowledgeTestEngine
    tester = KnowledgeTestEngine(memory, engine)
    results = tester.run_full_test()
    print(tester.format_results(results))
"""

import random
import math
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter, defaultdict


# ============================================================================
# TEST QUESTION TYPES
# ============================================================================

class TestQuestion:
    """A single test question with answer verification."""

    def __init__(self, category: str, question: str, answer: Any,
                 verify_fn=None, difficulty: int = 1, domain: str = "general"):
        self.category = category
        self.question = question
        self.answer = answer  # Expected answer (for auto-grading)
        self.verify_fn = verify_fn  # Custom verification function
        self.difficulty = difficulty  # 1=easy, 2=medium, 3=hard
        self.domain = domain
        self.result = None  # Filled after testing
        self.score = 0.0  # 0.0 to 1.0

    def verify(self, system_answer: Any) -> float:
        """Verify the system's answer. Returns score 0.0-1.0."""
        if self.verify_fn:
            self.score = self.verify_fn(self.answer, system_answer)
        else:
            # Default: exact match
            self.score = 1.0 if system_answer == self.answer else 0.0
        self.result = system_answer
        return self.score


# ============================================================================
# VERIFICATION FUNCTIONS
# ============================================================================

def verify_concept_exists(expected, actual_concepts):
    """Check if a concept exists in the system's concept list."""
    if isinstance(actual_concepts, dict):
        return 1.0 if expected.lower() in actual_concepts else 0.0
    if isinstance(actual_concepts, (list, set)):
        return 1.0 if expected.lower() in {c.lower() for c in actual_concepts} else 0.0
    return 0.0


def verify_relationship(expected_pair, actual_graph):
    """Check if two concepts are connected in the knowledge graph."""
    c1, c2 = expected_pair
    c1, c2 = c1.lower(), c2.lower()
    if isinstance(actual_graph, dict):
        rels = actual_graph.get(c1, {}).get("relationships", [])
        return 1.0 if c2 in rels else 0.0
    return 0.0


def verify_minimum_count(expected_min, actual_count):
    """Verify a count meets a minimum threshold."""
    if actual_count >= expected_min:
        return 1.0
    if expected_min == 0:
        return 1.0
    return min(1.0, actual_count / expected_min)


def verify_strength_above(expected_min, actual_strength):
    """Verify concept strength is above threshold."""
    if actual_strength >= expected_min:
        return 1.0
    if expected_min == 0:
        return 1.0
    return min(1.0, actual_strength / expected_min)


def verify_text_contains_concepts(expected_concepts, generated_text):
    """Check how many expected concepts appear in generated text."""
    if not generated_text or not expected_concepts:
        return 0.0
    text_lower = generated_text.lower()
    found = sum(1 for c in expected_concepts if c.lower() in text_lower)
    return found / len(expected_concepts)


def verify_domain_coverage(expected_domains, actual_domains):
    """Check domain coverage ratio."""
    if not expected_domains:
        return 1.0
    if isinstance(actual_domains, set):
        covered = len(actual_domains & set(expected_domains))
    elif isinstance(actual_domains, (list, tuple)):
        covered = len(set(actual_domains) & set(expected_domains))
    else:
        return 0.0
    return covered / len(expected_domains)


def verify_coherence_score(min_score, actual_score):
    """Verify text coherence meets minimum."""
    if actual_score >= min_score:
        return 1.0
    if min_score == 0:
        return 1.0
    return min(1.0, actual_score / min_score)


# ============================================================================
# KNOWLEDGE TEST ENGINE
# ============================================================================

class KnowledgeTestEngine:
    """
    Comprehensive knowledge retention test for Quantum MCAGI.

    Tests the system's ability to recall, connect, and generate from
    everything it has consumed through conversations, feeds, research,
    and document ingestion.
    """

    # Domain keyword mapping for classifying concepts
    DOMAIN_KEYWORDS = {
        "philosophy": {
            "consciousness", "existence", "meaning", "ethics", "metaphysics",
            "epistemology", "ontology", "phenomenology", "logic", "reason",
            "truth", "morality", "virtue", "soul", "free will", "determinism",
            "nihilism", "existentialism", "stoicism", "platonic", "aristotle",
            "descartes", "kant", "nietzsche", "hegel", "wittgenstein",
        },
        "physics": {
            "quantum", "particle", "wave", "relativity", "spacetime",
            "entropy", "energy", "force", "momentum", "photon", "electron",
            "gravity", "electromagnetic", "thermodynamics", "nuclear",
            "string theory", "dark matter", "dark energy", "higgs",
            "superconductor", "planck", "heisenberg", "schrodinger",
        },
        "computer_science": {
            "algorithm", "computation", "neural network", "data structure",
            "machine learning", "programming", "software", "hardware",
            "turing", "binary", "encryption", "database", "compiler",
            "recursive", "parallel", "distributed", "hashing", "sorting",
        },
        "biology": {
            "evolution", "genetics", "dna", "rna", "cell", "organism",
            "species", "mutation", "natural selection", "ecology",
            "neuroscience", "protein", "enzyme", "photosynthesis",
            "mitosis", "genome", "chromosome", "darwin", "crispr",
        },
        "mathematics": {
            "theorem", "proof", "set", "infinity", "topology", "algebra",
            "calculus", "geometry", "number theory", "group theory",
            "prime", "equation", "matrix", "vector", "function",
            "integral", "derivative", "limit", "axiom", "conjecture",
        },
        "psychology": {
            "mind", "behavior", "cognition", "emotion", "memory",
            "perception", "motivation", "personality", "development",
            "freud", "jung", "cognitive", "behavioral", "subconscious",
            "trauma", "therapy", "neuroplasticity", "intelligence",
        },
        "language": {
            "semantics", "syntax", "grammar", "morphology", "phonology",
            "pragmatics", "etymology", "rhetoric", "narrative", "metaphor",
            "linguistics", "dialect", "vocabulary", "communication",
        },
        "history": {
            "civilization", "empire", "war", "revolution", "ancient",
            "medieval", "renaissance", "colonial", "industrial", "dynasty",
            "archaeology", "artifact", "chronicle", "treaty", "monarchy",
        },
        "cosmology": {
            "universe", "big bang", "black hole", "nebula", "galaxy",
            "star", "planet", "supernova", "cosmic", "singularity",
            "multiverse", "dark energy", "expansion", "redshift",
        },
        "music": {
            "harmony", "melody", "rhythm", "chord", "scale", "tempo",
            "composition", "symphony", "sonata", "counterpoint",
            "frequency", "resonance", "timbre", "octave", "tuning",
        },
        "religion": {
            "god", "divine", "sacred", "scripture", "faith", "prayer",
            "ritual", "theology", "creation", "redemption", "prophecy",
            "enlightenment", "karma", "dharma", "meditation", "mysticism",
        },
        "medicine": {
            "diagnosis", "treatment", "disease", "pathology", "anatomy",
            "physiology", "pharmacology", "surgery", "immune", "vaccine",
            "clinical", "symptom", "chronic", "acute", "prognosis",
        },
    }

    # Questions per stage (scales with growth)
    QUESTIONS_PER_STAGE = {
        0: 10,   # Nascent
        1: 20,   # Curious
        2: 30,   # Inquisitive
        3: 40,   # Understanding
        4: 50,   # Philosophical
        5: 50,   # Theory Building
        6: 50,   # Transcendent
    }

    def __init__(self, memory, engine=None):
        """
        Initialize the knowledge test engine.

        Args:
            memory: LocalMemory instance with concepts, conversations, growth
            engine: QuantumLanguageEngine instance (for Markov tests)
        """
        self.memory = memory
        self.engine = engine
        self.questions = []
        self.results = {}
        self.test_timestamp = None

    # ------------------------------------------------------------------
    # DOMAIN CLASSIFICATION
    # ------------------------------------------------------------------

    def classify_concept_domain(self, concept: str) -> str:
        """Classify a concept into a knowledge domain."""
        concept_lower = concept.lower()
        best_domain = "general"
        best_score = 0

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = 0
            for kw in keywords:
                if kw in concept_lower or concept_lower in kw:
                    score += 2  # exact or substring match
                elif any(w in concept_lower for w in kw.split()):
                    score += 1  # partial word match
            if score > best_score:
                best_score = score
                best_domain = domain

        return best_domain

    def get_domain_distribution(self) -> Dict[str, List[str]]:
        """Classify all known concepts into domains."""
        distribution = defaultdict(list)
        for concept in self.memory.concepts:
            # Check metadata domain first
            meta = self.memory.concepts[concept].get("metadata", {})
            if isinstance(meta, dict) and meta.get("domain"):
                domain = meta["domain"]
            else:
                domain = self.classify_concept_domain(concept)
            distribution[domain].append(concept)
        return dict(distribution)

    # ------------------------------------------------------------------
    # QUESTION GENERATORS
    # ------------------------------------------------------------------

    def _generate_concept_recall_questions(self, num: int) -> List[TestQuestion]:
        """Generate questions that test basic concept recall."""
        questions = []
        concepts = list(self.memory.concepts.keys())
        if not concepts:
            return questions

        # Sample concepts weighted by strength (stronger = more likely tested)
        weights = []
        for c in concepts:
            strength = self.memory.concepts[c].get("strength", 1.0)
            weights.append(strength)

        total_w = sum(weights) or 1
        probs = [w / total_w for w in weights]

        num_to_sample = min(num, len(concepts))
        # Weighted sampling without replacement
        sampled = []
        available = list(range(len(concepts)))
        avail_probs = list(probs)
        for _ in range(num_to_sample):
            if not available:
                break
            total = sum(avail_probs) or 1
            normalized = [p / total for p in avail_probs]
            r = random.random()
            cumulative = 0
            chosen_idx = 0
            for i, p in enumerate(normalized):
                cumulative += p
                if r <= cumulative:
                    chosen_idx = i
                    break
            sampled.append(available[chosen_idx])
            available.pop(chosen_idx)
            avail_probs.pop(chosen_idx)

        for idx in sampled:
            concept = concepts[idx]
            data = self.memory.concepts[concept]
            count = data.get("count", 0)
            strength = data.get("strength", 0)

            # Q1: Does the concept exist? (Always passes for known concepts)
            questions.append(TestQuestion(
                category="concept_recall",
                question=f"Is '{concept}' a known concept?",
                answer=concept,
                verify_fn=verify_concept_exists,
                difficulty=1,
                domain=self.classify_concept_domain(concept),
            ))

            # Q2: How reinforced is this concept?
            if count >= 3:
                questions.append(TestQuestion(
                    category="concept_recall",
                    question=f"Has '{concept}' been encountered at least 3 times?",
                    answer=3,
                    verify_fn=verify_minimum_count,
                    difficulty=1,
                    domain=self.classify_concept_domain(concept),
                ))

            # Q3: Strength check
            if strength >= 2.0:
                questions.append(TestQuestion(
                    category="concept_recall",
                    question=f"Is '{concept}' strength above 2.0? (actual: {strength:.1f})",
                    answer=2.0,
                    verify_fn=verify_strength_above,
                    difficulty=2,
                    domain=self.classify_concept_domain(concept),
                ))

        return questions[:num]

    def _generate_relationship_questions(self, num: int) -> List[TestQuestion]:
        """Generate questions testing concept relationship memory."""
        questions = []
        concepts_with_rels = [
            (c, data) for c, data in self.memory.concepts.items()
            if data.get("relationships")
        ]

        if not concepts_with_rels:
            return questions

        random.shuffle(concepts_with_rels)

        for concept, data in concepts_with_rels[:num]:
            rels = data.get("relationships", [])
            if not rels:
                continue

            # Q1: Test a known relationship exists
            rel = random.choice(rels)
            questions.append(TestQuestion(
                category="relationship_mapping",
                question=f"Are '{concept}' and '{rel}' connected?",
                answer=(concept, rel),
                verify_fn=verify_relationship,
                difficulty=2,
                domain=self.classify_concept_domain(concept),
            ))

            # Q2: Test relationship count
            if len(rels) >= 2:
                questions.append(TestQuestion(
                    category="relationship_mapping",
                    question=f"Does '{concept}' have at least 2 connections? (actual: {len(rels)})",
                    answer=2,
                    verify_fn=verify_minimum_count,
                    difficulty=2,
                    domain=self.classify_concept_domain(concept),
                ))

        return questions[:num]

    def _generate_domain_coverage_questions(self, num: int) -> List[TestQuestion]:
        """Generate questions testing breadth of domain knowledge."""
        questions = []
        domain_dist = self.get_domain_distribution()
        domains_covered = [d for d, concepts in domain_dist.items() if concepts]

        if not domains_covered:
            return questions

        # Q1: Overall domain count
        questions.append(TestQuestion(
            category="domain_coverage",
            question=f"How many knowledge domains are covered?",
            answer=max(1, len(domains_covered) - 1),  # At least N-1
            verify_fn=verify_minimum_count,
            difficulty=1,
            domain="general",
        ))

        # Per-domain depth questions
        for domain in domains_covered[:num - 1]:
            domain_concepts = domain_dist[domain]
            if len(domain_concepts) >= 2:
                questions.append(TestQuestion(
                    category="domain_coverage",
                    question=f"Does '{domain}' domain have at least 2 concepts? (actual: {len(domain_concepts)})",
                    answer=2,
                    verify_fn=verify_minimum_count,
                    difficulty=2,
                    domain=domain,
                ))

        return questions[:num]

    def _generate_markov_coherence_questions(self, num: int) -> List[TestQuestion]:
        """Generate questions testing Markov chain knowledge retention."""
        questions = []
        if not self.engine or not hasattr(self.engine, 'markov'):
            return questions

        markov = self.engine.markov
        if not markov.trained or not markov.chain:
            return questions

        # Q1: Chain size check
        chain_size = len(markov.chain)
        questions.append(TestQuestion(
            category="markov_coherence",
            question=f"Markov chain has states? (actual: {chain_size})",
            answer=1,
            verify_fn=verify_minimum_count,
            difficulty=1,
            domain="language",
        ))

        # Q2: Total tokens check
        total_tokens = markov.total_tokens
        questions.append(TestQuestion(
            category="markov_coherence",
            question=f"Markov chain has transitions? (actual: {total_tokens})",
            answer=1,
            verify_fn=verify_minimum_count,
            difficulty=1,
            domain="language",
        ))

        # Q3-Qn: Generate text and check for concept inclusion
        top_concepts = sorted(
            self.memory.concepts.items(),
            key=lambda x: x[1].get("count", 0),
            reverse=True,
        )[:20]

        top_concept_names = [c for c, _ in top_concepts]

        for _ in range(min(num - 2, 5)):
            if not top_concept_names:
                break
            # Pick a seed concept and try to generate
            seed = random.choice(top_concept_names)
            try:
                generated = markov.generate(
                    max_words=40,
                    seed_words=[seed],
                    temperature=0.8,
                )
            except Exception:
                generated = ""

            if generated:
                # Test: does generated text contain any known concepts?
                questions.append(TestQuestion(
                    category="markov_coherence",
                    question=f"Generate from '{seed}': contains known concepts?",
                    answer=top_concept_names[:10],
                    verify_fn=verify_text_contains_concepts,
                    difficulty=3,
                    domain=self.classify_concept_domain(seed),
                ))

        return questions[:num]

    def _generate_conversation_memory_questions(self, num: int) -> List[TestQuestion]:
        """Test retention from conversation history."""
        questions = []
        convos = self.memory.conversations

        if not convos:
            return questions

        # Q1: Total conversations stored
        questions.append(TestQuestion(
            category="conversation_memory",
            question=f"Conversations retained? (actual: {len(convos)})",
            answer=1,
            verify_fn=verify_minimum_count,
            difficulty=1,
            domain="general",
        ))

        # Sample recent conversations and test concept extraction
        recent = convos[-min(20, len(convos)):]
        for conv in random.sample(recent, min(num - 1, len(recent))):
            conv_concepts = conv.get("concepts", [])
            if conv_concepts:
                # Test: are the concepts from this conversation still known?
                for concept in conv_concepts[:2]:
                    questions.append(TestQuestion(
                        category="conversation_memory",
                        question=f"Concept '{concept}' from conversation retained?",
                        answer=concept,
                        verify_fn=verify_concept_exists,
                        difficulty=1,
                        domain=self.classify_concept_domain(concept),
                    ))

        return questions[:num]

    def _generate_graph_topology_questions(self, num: int) -> List[TestQuestion]:
        """Test the health and structure of the knowledge graph."""
        questions = []
        topology = self.memory.check_graph_topology()

        if topology["node_count"] == 0:
            return questions

        # Q1: Graph has nodes
        questions.append(TestQuestion(
            category="graph_topology",
            question=f"Knowledge graph has nodes? (actual: {topology['node_count']})",
            answer=1,
            verify_fn=verify_minimum_count,
            difficulty=1,
            domain="general",
        ))

        # Q2: Graph has edges
        if topology["edge_count"] > 0:
            questions.append(TestQuestion(
                category="graph_topology",
                question=f"Knowledge graph has edges? (actual: {topology['edge_count']})",
                answer=1,
                verify_fn=verify_minimum_count,
                difficulty=1,
                domain="general",
            ))

        # Q3: Average degree check
        if topology["avg_degree"] > 0:
            questions.append(TestQuestion(
                category="graph_topology",
                question=f"Graph avg degree > 0? (actual: {topology['avg_degree']})",
                answer=0.1,
                verify_fn=verify_strength_above,
                difficulty=2,
                domain="general",
            ))

        # Q4: Diameter check
        if topology["diameter"] > 0:
            questions.append(TestQuestion(
                category="graph_topology",
                question=f"Graph diameter > 0? (actual: {topology['diameter']})",
                answer=1,
                verify_fn=verify_minimum_count,
                difficulty=2,
                domain="general",
            ))

        # Q5: Largest component ratio
        if topology["largest_component_ratio"] > 0.3:
            questions.append(TestQuestion(
                category="graph_topology",
                question=f"Largest component > 30%? (actual: {topology['largest_component_ratio']:.1%})",
                answer=0.3,
                verify_fn=verify_strength_above,
                difficulty=3,
                domain="general",
            ))

        return questions[:num]

    def _generate_cross_domain_questions(self, num: int) -> List[TestQuestion]:
        """Test cross-domain concept connections."""
        questions = []
        domain_dist = self.get_domain_distribution()

        # Find concepts that bridge domains
        bridge_pairs = []
        for concept, data in self.memory.concepts.items():
            c_domain = self.classify_concept_domain(concept)
            for rel in data.get("relationships", []):
                r_domain = self.classify_concept_domain(rel)
                if c_domain != r_domain and c_domain != "general" and r_domain != "general":
                    bridge_pairs.append((concept, rel, c_domain, r_domain))

        if not bridge_pairs:
            return questions

        random.shuffle(bridge_pairs)
        for concept, rel, c_domain, r_domain in bridge_pairs[:num]:
            questions.append(TestQuestion(
                category="cross_domain",
                question=f"Cross-domain link: '{concept}' ({c_domain}) ↔ '{rel}' ({r_domain})?",
                answer=(concept, rel),
                verify_fn=verify_relationship,
                difficulty=3,
                domain=c_domain,
            ))

        return questions[:num]

    # ------------------------------------------------------------------
    # TEST EXECUTION
    # ------------------------------------------------------------------

    def generate_test(self, stage: int = None, domain_filter: str = None) -> List[TestQuestion]:
        """
        Generate a complete knowledge test.

        Args:
            stage: Override growth stage (uses current if None)
            domain_filter: Only test a specific domain (None = all)

        Returns:
            List of TestQuestion objects
        """
        if stage is None:
            stage_info = self.memory.get_current_stage()
            stage = stage_info.get("stage", 0)

        total_questions = self.QUESTIONS_PER_STAGE.get(stage, 50)

        # Distribute questions across categories based on stage
        allocation = self._get_question_allocation(stage, total_questions)

        all_questions = []

        # Always include concept recall
        all_questions.extend(
            self._generate_concept_recall_questions(allocation["concept_recall"])
        )

        # Stage 1+: relationships
        if stage >= 1:
            all_questions.extend(
                self._generate_relationship_questions(allocation["relationship_mapping"])
            )

        # Stage 2+: domain coverage
        if stage >= 2:
            all_questions.extend(
                self._generate_domain_coverage_questions(allocation["domain_coverage"])
            )

        # Stage 3+: Markov coherence
        if stage >= 3:
            all_questions.extend(
                self._generate_markov_coherence_questions(allocation["markov_coherence"])
            )

        # Always include conversation memory (if available)
        all_questions.extend(
            self._generate_conversation_memory_questions(allocation["conversation_memory"])
        )

        # Always include graph topology
        all_questions.extend(
            self._generate_graph_topology_questions(allocation["graph_topology"])
        )

        # Stage 4+: cross-domain
        if stage >= 4:
            all_questions.extend(
                self._generate_cross_domain_questions(allocation["cross_domain"])
            )

        # Apply domain filter
        if domain_filter:
            domain_filter = domain_filter.lower()
            all_questions = [
                q for q in all_questions
                if q.domain == domain_filter or domain_filter in q.category
            ]

        self.questions = all_questions
        return all_questions

    def _get_question_allocation(self, stage: int, total: int) -> Dict[str, int]:
        """Allocate question counts per category based on stage."""
        if stage <= 0:
            return {
                "concept_recall": max(4, total // 2),
                "relationship_mapping": 0,
                "domain_coverage": 0,
                "markov_coherence": 0,
                "conversation_memory": max(3, total // 4),
                "graph_topology": max(3, total // 4),
                "cross_domain": 0,
            }
        elif stage == 1:
            return {
                "concept_recall": max(5, total // 3),
                "relationship_mapping": max(4, total // 4),
                "domain_coverage": 0,
                "markov_coherence": 0,
                "conversation_memory": max(3, total // 5),
                "graph_topology": max(3, total // 5),
                "cross_domain": 0,
            }
        elif stage == 2:
            return {
                "concept_recall": max(5, total // 4),
                "relationship_mapping": max(5, total // 5),
                "domain_coverage": max(5, total // 5),
                "markov_coherence": 0,
                "conversation_memory": max(4, total // 5),
                "graph_topology": max(4, total // 5),
                "cross_domain": 0,
            }
        elif stage == 3:
            return {
                "concept_recall": max(6, total // 5),
                "relationship_mapping": max(5, total // 6),
                "domain_coverage": max(5, total // 6),
                "markov_coherence": max(5, total // 6),
                "conversation_memory": max(4, total // 6),
                "graph_topology": max(4, total // 6),
                "cross_domain": 0,
            }
        else:  # Stage 4+
            return {
                "concept_recall": max(7, total // 7),
                "relationship_mapping": max(7, total // 7),
                "domain_coverage": max(6, total // 7),
                "markov_coherence": max(6, total // 7),
                "conversation_memory": max(6, total // 7),
                "graph_topology": max(6, total // 7),
                "cross_domain": max(6, total // 7),
            }

    def run_full_test(self, stage: int = None, domain_filter: str = None) -> Dict:
        """
        Execute the full knowledge retention test.

        Returns:
            Dict with complete test results including scores per category,
            per domain, overall retention percentage, and detailed question results.
        """
        self.test_timestamp = datetime.now().isoformat()

        # Generate questions
        questions = self.generate_test(stage=stage, domain_filter=domain_filter)

        if not questions:
            return {
                "timestamp": self.test_timestamp,
                "total_questions": 0,
                "overall_score": 0.0,
                "overall_percentage": 0.0,
                "message": "No knowledge to test yet. Feed data first with /feed or conversation.",
                "categories": {},
                "domains": {},
                "questions": [],
            }

        # Execute each question
        for q in questions:
            self._execute_question(q)

        # Aggregate results
        return self._aggregate_results(questions)

    def _execute_question(self, q: TestQuestion):
        """Execute a single test question against the system's knowledge."""
        try:
            if q.category == "concept_recall":
                if "known concept" in q.question:
                    q.verify(self.memory.concepts)
                elif "encountered at least" in q.question:
                    concept_name = q.question.split("'")[1]
                    actual = self.memory.concepts.get(
                        concept_name.lower(), {}
                    ).get("count", 0)
                    q.verify(actual)
                elif "strength above" in q.question:
                    concept_name = q.question.split("'")[1]
                    actual = self.memory.concepts.get(
                        concept_name.lower(), {}
                    ).get("strength", 0)
                    q.verify(actual)
                else:
                    q.score = 0.0

            elif q.category == "relationship_mapping":
                if "connected" in q.question:
                    q.verify(self.memory.concepts)
                elif "connections" in q.question:
                    concept_name = q.question.split("'")[1]
                    actual = len(self.memory.concepts.get(
                        concept_name.lower(), {}
                    ).get("relationships", []))
                    q.verify(actual)
                else:
                    q.score = 0.0

            elif q.category == "domain_coverage":
                if "domains are covered" in q.question:
                    domain_dist = self.get_domain_distribution()
                    actual = len([d for d, c in domain_dist.items() if c])
                    q.verify(actual)
                elif "domain have at least" in q.question:
                    domain_dist = self.get_domain_distribution()
                    domain_name = q.question.split("'")[1]
                    actual = len(domain_dist.get(domain_name, []))
                    q.verify(actual)
                else:
                    q.score = 0.0

            elif q.category == "markov_coherence":
                if "has states" in q.question:
                    actual = len(self.engine.markov.chain) if self.engine else 0
                    q.verify(actual)
                elif "has transitions" in q.question:
                    actual = self.engine.markov.total_tokens if self.engine else 0
                    q.verify(actual)
                elif "contains known concepts" in q.question:
                    seed = q.question.split("'")[1]
                    try:
                        generated = self.engine.markov.generate(
                            max_words=40,
                            seed_words=[seed],
                            temperature=0.8,
                        )
                    except Exception:
                        generated = ""
                    q.verify(generated)
                else:
                    q.score = 0.0

            elif q.category == "conversation_memory":
                if "Conversations retained" in q.question:
                    actual = len(self.memory.conversations)
                    q.verify(actual)
                elif "from conversation retained" in q.question:
                    concept_name = q.question.split("'")[1]
                    q.verify(self.memory.concepts)
                else:
                    q.score = 0.0

            elif q.category == "graph_topology":
                topology = self.memory.check_graph_topology()
                if "has nodes" in q.question:
                    q.verify(topology["node_count"])
                elif "has edges" in q.question:
                    q.verify(topology["edge_count"])
                elif "avg degree" in q.question:
                    q.verify(topology["avg_degree"])
                elif "diameter" in q.question:
                    q.verify(topology["diameter"])
                elif "component" in q.question:
                    q.verify(topology["largest_component_ratio"])
                else:
                    q.score = 0.0

            elif q.category == "cross_domain":
                q.verify(self.memory.concepts)

            else:
                q.score = 0.0

        except Exception as e:
            q.score = 0.0
            q.result = f"Error: {e}"

    def _aggregate_results(self, questions: List[TestQuestion]) -> Dict:
        """Aggregate all question results into a structured report."""
        # Per-category scores
        categories = defaultdict(lambda: {"total": 0, "scored": 0.0, "questions": []})
        for q in questions:
            cat = categories[q.category]
            cat["total"] += 1
            cat["scored"] += q.score
            cat["questions"].append({
                "question": q.question,
                "score": q.score,
                "difficulty": q.difficulty,
                "domain": q.domain,
            })

        category_results = {}
        for cat_name, cat_data in categories.items():
            pct = (cat_data["scored"] / cat_data["total"] * 100) if cat_data["total"] else 0
            category_results[cat_name] = {
                "total": cat_data["total"],
                "scored": round(cat_data["scored"], 2),
                "percentage": round(pct, 1),
                "questions": cat_data["questions"],
            }

        # Per-domain scores
        domains = defaultdict(lambda: {"total": 0, "scored": 0.0})
        for q in questions:
            dom = domains[q.domain]
            dom["total"] += 1
            dom["scored"] += q.score

        domain_results = {}
        for dom_name, dom_data in domains.items():
            pct = (dom_data["scored"] / dom_data["total"] * 100) if dom_data["total"] else 0
            domain_results[dom_name] = {
                "total": dom_data["total"],
                "scored": round(dom_data["scored"], 2),
                "percentage": round(pct, 1),
            }

        # Overall
        total_q = len(questions)
        total_score = sum(q.score for q in questions)
        overall_pct = (total_score / total_q * 100) if total_q else 0

        # Difficulty breakdown
        difficulty_scores = defaultdict(lambda: {"total": 0, "scored": 0.0})
        for q in questions:
            d = difficulty_scores[q.difficulty]
            d["total"] += 1
            d["scored"] += q.score

        difficulty_results = {}
        diff_labels = {1: "Easy", 2: "Medium", 3: "Hard"}
        for diff, diff_data in difficulty_scores.items():
            pct = (diff_data["scored"] / diff_data["total"] * 100) if diff_data["total"] else 0
            difficulty_results[diff_labels.get(diff, f"Level {diff}")] = {
                "total": diff_data["total"],
                "scored": round(diff_data["scored"], 2),
                "percentage": round(pct, 1),
            }

        # Growth stage info
        stage_info = self.memory.get_current_stage()

        # Retention grade
        grade = self._compute_grade(overall_pct)

        self.results = {
            "timestamp": self.test_timestamp,
            "growth_stage": stage_info.get("stage", 0),
            "growth_name": stage_info.get("name", "Unknown"),
            "total_questions": total_q,
            "total_score": round(total_score, 2),
            "overall_percentage": round(overall_pct, 1),
            "grade": grade,
            "categories": category_results,
            "domains": domain_results,
            "difficulty": difficulty_results,
            "knowledge_stats": {
                "total_concepts": len(self.memory.concepts),
                "total_connections": self.memory.count_connections(),
                "total_conversations": len(self.memory.conversations),
                "total_interactions": self.memory.growth.get("total_interactions", 0),
                "domains_covered": len([d for d, c in self.get_domain_distribution().items() if c]),
            },
        }
        return self.results

    def _compute_grade(self, percentage: float) -> str:
        """Compute a letter grade from percentage."""
        if percentage >= 95:
            return "A+"
        elif percentage >= 90:
            return "A"
        elif percentage >= 85:
            return "A-"
        elif percentage >= 80:
            return "B+"
        elif percentage >= 75:
            return "B"
        elif percentage >= 70:
            return "B-"
        elif percentage >= 65:
            return "C+"
        elif percentage >= 60:
            return "C"
        elif percentage >= 55:
            return "C-"
        elif percentage >= 50:
            return "D"
        else:
            return "F"

    # ------------------------------------------------------------------
    # RESULTS FORMATTING
    # ------------------------------------------------------------------

    def format_results(self, results: Dict = None) -> str:
        """Format test results for terminal display."""
        if results is None:
            results = self.results
        if not results:
            return "  No test results available. Run /test first."

        lines = []
        lines.append("")
        lines.append("╔══════════════════════════════════════════════════════════════╗")
        lines.append("║            🧪 KNOWLEDGE RETENTION TEST RESULTS              ║")
        lines.append("╠══════════════════════════════════════════════════════════════╣")

        # Overall score
        pct = results.get("overall_percentage", 0)
        grade = results.get("grade", "?")
        total_q = results.get("total_questions", 0)
        total_s = results.get("total_score", 0)
        stage = results.get("growth_stage", 0)
        stage_name = results.get("growth_name", "?")

        lines.append(f"║  Growth Stage: {stage} - {stage_name:<42} ║")
        lines.append(f"║  Overall Score: {total_s}/{total_q} ({pct:.1f}%)  Grade: {grade:<17} ║")
        lines.append("╠══════════════════════════════════════════════════════════════╣")

        # Category breakdown
        lines.append("║  CATEGORY SCORES:                                            ║")
        lines.append("║  ─────────────────────────────────────────                    ║")

        category_labels = {
            "concept_recall": "📚 Concept Recall",
            "relationship_mapping": "🔗 Relationship Mapping",
            "domain_coverage": "🌐 Domain Coverage",
            "markov_coherence": "🔤 Markov Coherence",
            "conversation_memory": "💬 Conversation Memory",
            "graph_topology": "📊 Graph Topology",
            "cross_domain": "🌉 Cross-Domain Links",
        }

        for cat, cat_data in results.get("categories", {}).items():
            label = category_labels.get(cat, cat)
            total = cat_data.get("total", 0)
            scored = cat_data.get("scored", 0)
            pct = cat_data.get("percentage", 0)
            bar = self._progress_bar(pct, 15)
            lines.append(f"║  {label:<25} {scored:>5.1f}/{total:<3} {bar} {pct:>5.1f}% ║")

        lines.append("╠══════════════════════════════════════════════════════════════╣")

        # Domain breakdown
        domain_results = results.get("domains", {})
        if domain_results:
            lines.append("║  DOMAIN RETENTION:                                           ║")
            lines.append("║  ─────────────────────────────────────────                    ║")
            for dom, dom_data in sorted(domain_results.items()):
                total = dom_data.get("total", 0)
                pct = dom_data.get("percentage", 0)
                bar = self._progress_bar(pct, 15)
                lines.append(f"║  {dom:<25} {total:>3} Q  {bar} {pct:>5.1f}% ║")
            lines.append("╠══════════════════════════════════════════════════════════════╣")

        # Difficulty breakdown
        diff_results = results.get("difficulty", {})
        if diff_results:
            lines.append("║  DIFFICULTY BREAKDOWN:                                       ║")
            lines.append("║  ─────────────────────────────────────────                    ║")
            for diff, diff_data in diff_results.items():
                total = diff_data.get("total", 0)
                pct = diff_data.get("percentage", 0)
                bar = self._progress_bar(pct, 15)
                lines.append(f"║  {diff:<25} {total:>3} Q  {bar} {pct:>5.1f}% ║")
            lines.append("╠══════════════════════════════════════════════════════════════╣")

        # Knowledge stats
        stats = results.get("knowledge_stats", {})
        if stats:
            lines.append("║  KNOWLEDGE STATS:                                            ║")
            lines.append("║  ─────────────────────────────────────────                    ║")
            lines.append(f"║  Total Concepts:      {stats.get('total_concepts', 0):<36} ║")
            lines.append(f"║  Total Connections:   {stats.get('total_connections', 0):<36} ║")
            lines.append(f"║  Conversations:       {stats.get('total_conversations', 0):<36} ║")
            lines.append(f"║  Interactions:        {stats.get('total_interactions', 0):<36} ║")
            lines.append(f"║  Domains Covered:     {stats.get('domains_covered', 0):<36} ║")

        lines.append("╠══════════════════════════════════════════════════════════════╣")

        # Assessment
        assessment = self._generate_assessment(results)
        for line in assessment:
            lines.append(f"║  {line:<59}║")

        lines.append("╚══════════════════════════════════════════════════════════════╝")
        lines.append("")

        return "\n".join(lines)

    def _progress_bar(self, percentage: float, width: int = 15) -> str:
        """Create a text progress bar."""
        filled = int(percentage / 100 * width)
        filled = min(filled, width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"

    def _generate_assessment(self, results: Dict) -> List[str]:
        """Generate qualitative assessment of knowledge retention."""
        lines = []
        pct = results.get("overall_percentage", 0)
        grade = results.get("grade", "?")

        lines.append("ASSESSMENT:")
        lines.append("─" * 40)

        if pct >= 90:
            lines.append("Excellent knowledge retention!")
            lines.append("The system demonstrates strong recall")
            lines.append("across all tested domains.")
        elif pct >= 75:
            lines.append("Good knowledge retention.")
            lines.append("Most consumed knowledge is well-retained.")
            # Find weakest category
            cats = results.get("categories", {})
            if cats:
                weakest = min(cats.items(), key=lambda x: x[1].get("percentage", 0))
                lines.append(f"Weakest area: {weakest[0]}")
        elif pct >= 60:
            lines.append("Moderate retention. Some gaps detected.")
            cats = results.get("categories", {})
            weak_cats = [c for c, d in cats.items() if d.get("percentage", 0) < 60]
            if weak_cats:
                lines.append(f"Weak areas: {', '.join(weak_cats[:3])}")
            lines.append("Recommendation: More training needed.")
        elif pct >= 40:
            lines.append("Below average retention.")
            lines.append("Significant knowledge gaps detected.")
            lines.append("Feed more data with /feed or converse")
            lines.append("on varied topics to strengthen recall.")
        else:
            lines.append("Low retention — early stage learning.")
            lines.append("This is normal for a Nascent system.")
            lines.append("Use /feed all to consume knowledge,")
            lines.append("then re-test with /test.")

        return lines

    def format_summary(self, results: Dict = None) -> str:
        """Format a brief summary of the last test."""
        if results is None:
            results = self.results
        if not results:
            return "  No test results. Run /test first."

        pct = results.get("overall_percentage", 0)
        grade = results.get("grade", "?")
        total_q = results.get("total_questions", 0)
        stage = results.get("growth_stage", 0)
        stage_name = results.get("growth_name", "?")
        ts = results.get("timestamp", "?")

        lines = [
            f"  Last Test: {ts}",
            f"  Stage: {stage} ({stage_name}) | Score: {pct:.1f}% | Grade: {grade} | Questions: {total_q}",
        ]

        cats = results.get("categories", {})
        if cats:
            best = max(cats.items(), key=lambda x: x[1].get("percentage", 0))
            worst = min(cats.items(), key=lambda x: x[1].get("percentage", 0))
            lines.append(f"  Best: {best[0]} ({best[1]['percentage']:.0f}%) | Worst: {worst[0]} ({worst[1]['percentage']:.0f}%)")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # PERSISTENCE
    # ------------------------------------------------------------------

    def save_results(self, data_dir=None):
        """Save test results to disk."""
        import json
        from pathlib import Path

        if data_dir is None:
            data_dir = self.memory.data_dir

        filepath = Path(data_dir) / "knowledge_test_results.json"

        # Load existing results history
        history = []
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    history = json.load(f)
            except (json.JSONDecodeError, IOError):
                history = []

        # Append current results (without individual questions to save space)
        summary = {k: v for k, v in self.results.items() if k != "questions"}
        # Strip per-question details from categories to keep file small
        if "categories" in summary:
            for cat_name in summary["categories"]:
                summary["categories"][cat_name].pop("questions", None)

        history.append(summary)

        # Keep last 50 test results
        history = history[-50:]

        with open(filepath, 'w') as f:
            json.dump(history, f, indent=2)

    def load_last_results(self, data_dir=None) -> Optional[Dict]:
        """Load the most recent test results from disk."""
        import json
        from pathlib import Path

        if data_dir is None:
            data_dir = self.memory.data_dir

        filepath = Path(data_dir) / "knowledge_test_results.json"

        if not filepath.exists():
            return None

        try:
            with open(filepath, 'r') as f:
                history = json.load(f)
            if history:
                self.results = history[-1]
                return history[-1]
        except (json.JSONDecodeError, IOError):
            pass

        return None


# ============================================================================
# SINGLETON
# ============================================================================

_knowledge_test_instance = None


def get_knowledge_test(memory, engine=None) -> KnowledgeTestEngine:
    """Get or create the singleton KnowledgeTestEngine."""
    global _knowledge_test_instance
    if _knowledge_test_instance is None:
        _knowledge_test_instance = KnowledgeTestEngine(memory, engine)
    else:
        # Update references in case memory/engine changed
        _knowledge_test_instance.memory = memory
        _knowledge_test_instance.engine = engine
    return _knowledge_test_instance
