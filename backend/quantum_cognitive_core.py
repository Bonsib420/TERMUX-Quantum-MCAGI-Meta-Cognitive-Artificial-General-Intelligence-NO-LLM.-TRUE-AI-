"""
🔮 Quantum Cognitive Core
==========================
GrowthTracker and QuantumCognitiveCore — the main cognitive integration layer.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import uuid
import json
import re
from quantum_core import SemanticMemory, EpisodicMemory, ProceduralMemory, PhilosophicalMemory, QuestionGenerationEngine, UnderstandingEngine

class GrowthTracker:
    """
    ARTICLE 3.1 - Growth Monitoring
    
    Tracks cognitive growth, learning rates, and evolutionary stages.
    """
    
    # All 12 tracks must be met simultaneously to advance.
    # High watermark protection on diameter and avg_degree — earned progress never regresses.
    GROWTH_STAGES = [
        {"stage": 0, "name": "Nascent", "description": "Initial awareness forming", "threshold": {
            "connections": 0, "concepts": 0,
            "min_avg_degree": 0, "min_diameter": 0, "min_domains": 0,
            "min_markov_states": 0, "min_transitions": 0, "min_comm_score": 0,
            "min_questions": 0, "min_insights": 0, "min_interactions": 0
        }},
        {"stage": 1, "name": "Curious", "description": "Basic questioning capability", "threshold": {
            "connections": 50, "concepts": 20,
            "min_avg_degree": 1.5, "min_diameter": 3, "min_domains": 3,
            "min_markov_states": 5000, "min_transitions": 10000, "min_comm_score": 15,
            "min_questions": 50, "min_insights": 10, "min_interactions": 25
        }},
        {"stage": 2, "name": "Inquisitive", "description": "Generating deeper questions", "threshold": {
            "connections": 200, "concepts": 50,
            "min_avg_degree": 2.5, "min_diameter": 6, "min_domains": 6,
            "min_markov_states": 20000, "min_transitions": 80000, "min_comm_score": 25,
            "min_questions": 200, "min_insights": 50, "min_interactions": 100
        }},
        {"stage": 3, "name": "Understanding", "description": "Forming connections and insights", "threshold": {
            "connections": 500, "concepts": 100,
            "min_avg_degree": 3.5, "min_diameter": 8, "min_domains": 10,
            "min_markov_states": 100000, "min_transitions": 400000, "min_comm_score": 35,
            "min_questions": 500, "min_insights": 150, "min_interactions": 300
        }},
        {"stage": 4, "name": "Philosophical", "description": "Meta-cognition and reflection", "threshold": {
            "connections": 1500, "concepts": 200,
            "min_avg_degree": 5.0, "min_diameter": 12, "min_domains": 15,
            "min_markov_states": 400000, "min_transitions": 1500000, "min_comm_score": 50,
            "min_questions": 1000, "min_insights": 400, "min_interactions": 750
        }},
        {"stage": 5, "name": "Theory Building", "description": "Constructing unified understanding", "threshold": {
            "connections": 4000, "concepts": 350,
            "min_avg_degree": 7.0, "min_diameter": 16, "min_domains": 20,
            "min_markov_states": 800000, "min_transitions": 3000000, "min_comm_score": 65,
            "min_questions": 2500, "min_insights": 1000, "min_interactions": 2000
        }},
        {"stage": 6, "name": "Transcendent", "description": "Beyond initial programming", "threshold": {
            "connections": 10000, "concepts": 600,
            "min_avg_degree": 10.0, "min_diameter": 20, "min_domains": 30,
            "min_markov_states": 1500000, "min_transitions": 6000000, "min_comm_score": 80,
            "min_questions": 6000, "min_insights": 3000, "min_interactions": 5000
        }}
    ]
    
    def __init__(self, db):
        self.db = db
        self.collection = db.growth_metrics
        self._last_stage = 0
        # High watermark protection — earned topology progress never regresses
        self._hwm_avg_degree = 0.0
        self._hwm_diameter = 0
        
    async def record_growth_event(self, event_type: str, details: Dict):
        """Record a growth-related event"""
        doc = {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.collection.insert_one(doc)
        
        # Check for stage advancement
        await self._check_stage_advancement()
        
    async def _check_stage_advancement(self) -> Optional[Dict]:
        """Check if AI has advanced to a new stage (all 12 tracks must be met simultaneously)"""
        current = await self.get_current_stage()
        if current["stage"] > self._last_stage:
            self._last_stage = current["stage"]
            # Get full metrics including topology
            metrics = await self.calculate_metrics()
            topology = await self.check_graph_topology()
            # Record the advancement with all metric tracks
            await self.collection.insert_one({
                "id": str(uuid.uuid4()),
                "event_type": "stage_advancement",
                "details": {
                    "new_stage": current["name"],
                    "stage_number": current["stage"],
                    "connections": metrics["total_connections"],
                    "concepts": metrics["total_concepts"],
                    "avg_degree": topology.get("avg_degree"),
                    "diameter": topology.get("diameter"),
                    "domains": metrics.get("distinct_domains"),
                    "markov_states": metrics.get("markov_states", 0),
                    "transitions": metrics.get("transitions", 0),
                    "comm_score": metrics.get("comm_score", 0),
                    "questions": metrics.get("total_questions", 0),
                    "insights": metrics.get("total_insights", 0),
                    "interactions": metrics.get("total_interactions", 0)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            return current
        return None
        
    async def get_current_stage(self) -> Dict:
        """Calculate current growth stage based on all 12 tracks simultaneously.
        High watermark protection on diameter and avg_degree — earned progress never regresses."""
        metrics = await self.calculate_metrics()
        topology = await self.check_graph_topology()

        # High watermark protection: use the maximum ever observed
        current_avg_degree = topology.get("avg_degree", 0)
        current_diameter = topology.get("diameter", 0)
        self._hwm_avg_degree = max(self._hwm_avg_degree, current_avg_degree)
        self._hwm_diameter = max(self._hwm_diameter, current_diameter)

        current_stage = self.GROWTH_STAGES[0]

        for stage in self.GROWTH_STAGES:
            threshold = stage["threshold"]
            if (metrics["total_connections"] >= threshold["connections"] and
                metrics["total_concepts"] >= threshold["concepts"] and
                self._hwm_avg_degree >= threshold.get("min_avg_degree", 0) and
                self._hwm_diameter >= threshold.get("min_diameter", 0) and
                metrics.get("distinct_domains", 0) >= threshold.get("min_domains", 0) and
                metrics.get("markov_states", 0) >= threshold.get("min_markov_states", 0) and
                metrics.get("transitions", 0) >= threshold.get("min_transitions", 0) and
                metrics.get("comm_score", 0) >= threshold.get("min_comm_score", 0) and
                metrics.get("total_questions", 0) >= threshold.get("min_questions", 0) and
                metrics.get("total_insights", 0) >= threshold.get("min_insights", 0) and
                metrics.get("total_interactions", 0) >= threshold.get("min_interactions", 0)):
                current_stage = stage
            else:
                break

        # Progress to next stage across all 12 dimensions
        next_stage_idx = min(current_stage["stage"] + 1, len(self.GROWTH_STAGES) - 1)
        next_stage = self.GROWTH_STAGES[next_stage_idx]

        progress = {}
        if next_stage["stage"] > current_stage["stage"]:
            next_thresh = next_stage["threshold"]
            progress = {
                "connections": min(100, int(metrics["total_connections"] / max(next_thresh["connections"], 1) * 100)),
                "concepts": min(100, int(metrics["total_concepts"] / max(next_thresh["concepts"], 1) * 100)),
                "avg_degree": min(100, int(self._hwm_avg_degree / max(next_thresh.get("min_avg_degree", 1), 0.1) * 100)),
                "diameter": min(100, int(self._hwm_diameter / max(next_thresh.get("min_diameter", 1), 1) * 100)),
                "domains": min(100, int(metrics.get("distinct_domains", 0) / max(next_thresh.get("min_domains", 1), 1) * 100)),
                "markov_states": min(100, int(metrics.get("markov_states", 0) / max(next_thresh.get("min_markov_states", 1), 1) * 100)),
                "transitions": min(100, int(metrics.get("transitions", 0) / max(next_thresh.get("min_transitions", 1), 1) * 100)),
                "comm_score": min(100, int(metrics.get("comm_score", 0) / max(next_thresh.get("min_comm_score", 1), 1) * 100)),
                "questions": min(100, int(metrics.get("total_questions", 0) / max(next_thresh.get("min_questions", 1), 1) * 100)),
                "insights": min(100, int(metrics.get("total_insights", 0) / max(next_thresh.get("min_insights", 1), 1) * 100)),
                "interactions": min(100, int(metrics.get("total_interactions", 0) / max(next_thresh.get("min_interactions", 1), 1) * 100))
            }

        return {
            **current_stage,
            "metrics": {
                **metrics,
                "topology": topology,
                "hwm_avg_degree": self._hwm_avg_degree,
                "hwm_diameter": self._hwm_diameter
            },
            "progress_to_next": progress,
            "next_stage": next_stage["name"] if next_stage["stage"] > current_stage["stage"] else None,
            "limiting_factor": self._identify_limiting_factor(metrics, topology, next_thresh) if next_stage["stage"] > current_stage["stage"] else None
        }
    
    async def calculate_metrics(self) -> Dict:
        """Calculate current cognitive metrics across all 12 growth dimensions."""
        # Count memories
        total_concepts = await self.db.semantic_memory.count_documents({})
        total_connections = await self.count_connections()
        total_episodes = await self.db.episodic_memory.count_documents({})
        total_skills = await self.db.procedural_memory.count_documents({})
        total_questions = await self.db.philosophical_memory.count_documents({"type": {"$exists": False}})
        total_insights = await self.db.philosophical_memory.count_documents({"type": "insight"})
        
        # Count total interactions (user_interaction episodes)
        total_interactions = await self.db.episodic_memory.count_documents({"episode_type": "user_interaction"})
        
        # Calculate average understanding depth
        concepts_sample = await self.db.semantic_memory.find({}, {"strength": 1, "_id": 0}).to_list(100)
        avg_strength = sum(c.get("strength", 0) for c in concepts_sample) / max(len(concepts_sample), 1)
        
        # Count distinct domains (knowledge breadth) from concept metadata
        all_concepts_with_meta = await self.db.semantic_memory.find({}, {"metadata": 1}).to_list(None)
        domains_set = set()
        for c in all_concepts_with_meta:
            meta = c.get("metadata", {})
            if isinstance(meta, dict):
                domain = meta.get("domain")
                if domain:
                    domains_set.add(domain)
        distinct_domains = len(domains_set)
        
        # Markov chain stats (states and transitions from the language engine)
        markov_states = 0
        transitions = 0
        try:
            from quantum_language_engine import QuantumLanguageEngine
            lang = QuantumLanguageEngine()
            if lang.markov and lang.markov.trained:
                markov_states = len(lang.markov.chain)
                transitions = lang.markov.total_tokens
        except Exception:
            pass
        
        # Communication score: composite of vocabulary breadth + response variety
        # Scale 0-100 based on Markov perplexity-diversity proxy
        comm_score = 0
        if markov_states > 0:
            import math
            # Score based on vocabulary diversity (log scale, capped at 100)
            vocab_component = min(40, int(math.log1p(markov_states) / math.log(1500000) * 40))
            transition_component = min(40, int(math.log1p(transitions) / math.log(6000000) * 40))
            # Bonus from domains breadth
            domain_component = min(20, distinct_domains)
            comm_score = vocab_component + transition_component + domain_component
        
        return {
            "total_concepts": total_concepts,
            "total_connections": total_connections,
            "total_episodes": total_episodes,
            "total_skills": total_skills,
            "total_questions": total_questions,
            "total_insights": total_insights,
            "total_interactions": total_interactions,
            "markov_states": markov_states,
            "transitions": transitions,
            "comm_score": comm_score,
            "understanding_depth": min(avg_strength / 10, 1.0),
            "growth_rate": await self._calculate_growth_rate(),
            "distinct_domains": distinct_domains
        }
    
    async def count_connections(self) -> int:
        """Count total relationships/connections in semantic memory."""
        concepts = await self.db.semantic_memory.find({}, {"relationships": 1}).to_list(None)
        total = 0
        for c in concepts:
            rels = c.get("relationships", [])
            if isinstance(rels, list):
                total += len(rels)
        return total

    async def check_graph_topology(self) -> Dict:
        """Analyze semantic memory graph structure for growth requirements."""
        # Fetch all concepts with relationships (limit for performance)
        concepts = await self.db.semantic_memory.find(
            {}, {"concept": 1, "relationships": 1}
        ).to_list(1000)

        # Build adjacency list
        graph = {}
        for c in concepts:
            name = c.get("concept")
            if name:
                # Normalize relationships to lowercase and filter empties
                rels = c.get("relationships") or []
                graph[name] = [rel.lower() for rel in rels if rel]

        if not graph:
            return {
                "node_count": 0,
                "edge_count": 0,
                "avg_degree": 0,
                "diameter": 0,
                "largest_component_ratio": 0,
                "component_count": 0
            }

        # 1. Basic stats
        degrees = [len(rels) for rels in graph.values()]
        total_nodes = len(graph)
        total_edges = sum(degrees)
        avg_degree = total_edges / total_nodes if total_nodes > 0 else 0

        # 2. Find connected components using BFS
        def bfs_component(start_node: str, g: Dict) -> set:
            visited = set()
            queue = [start_node]
            while queue:
                node = queue.pop(0)
                if node not in visited:
                    visited.add(node)
                    for neighbor in g.get(node, []):
                        if neighbor in g and neighbor not in visited:
                            queue.append(neighbor)
            return visited

        visited_all = set()
        components = []
        for node in graph:
            if node not in visited_all:
                comp = bfs_component(node, graph)
                visited_all.update(comp)
                components.append(comp)

        largest_component = max(components, key=len) if components else set()
        largest_comp_ratio = len(largest_component) / total_nodes if total_nodes > 0 else 0

        # 3. Calculate diameter (longest shortest path in largest component)
        # Estimate by sampling up to 5 nodes to avoid O(n²) on large graphs
        diameter = 0
        if len(largest_component) > 1:
            sample_nodes = list(largest_component)[:5]
            for start_node in sample_nodes:
                # BFS from start_node
                distances = {start_node: 0}
                queue = [start_node]
                while queue:
                    current = queue.pop(0)
                    for neighbor in graph.get(current, []):
                        if neighbor in largest_component and neighbor not in distances:
                            distances[neighbor] = distances[current] + 1
                            queue.append(neighbor)
                if distances:
                    farthest = max(distances.values())
                    diameter = max(diameter, farthest)

        return {
            "node_count": total_nodes,
            "edge_count": total_edges,
            "avg_degree": round(avg_degree, 2),
            "diameter": diameter,
            "largest_component_ratio": round(largest_comp_ratio, 3),
            "component_count": len(components)
        }

    def _identify_limiting_factor(self, metrics: Dict, topology: Dict, next_thresh: Dict) -> str:
        """Return which of the 12 threshold tracks is furthest from being met."""
        checks = [
            ("connections", metrics["total_connections"] / max(next_thresh["connections"], 1)),
            ("concepts", metrics["total_concepts"] / max(next_thresh["concepts"], 1)),
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
        # Find the smallest ratio (most deficient)
        limiting = min(checks, key=lambda x: x[1])
        return limiting[0]

    async def _calculate_growth_rate(self) -> float:
        """Calculate recent growth rate"""
        # Get events from last 24 hours
        from datetime import timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        
        recent_events = await self.collection.find(
            {"timestamp": {"$gte": cutoff}},
            {"_id": 0}
        ).to_list(1000)
        
        return len(recent_events) / 24.0  # Events per hour


class QuantumCognitiveCore:
    """
    ARTICLE 1 - COGNITIVE CORE INTEGRATION
    
    Main cognitive core that integrates all memory systems and cognitive processes.
    """
    
    def __init__(self, db):
        self.db = db
        self.semantic_memory = SemanticMemory(db)
        self.episodic_memory = EpisodicMemory(db)
        self.procedural_memory = ProceduralMemory(db)
        self.philosophical_memory = PhilosophicalMemory(db)
        self.question_engine = QuestionGenerationEngine()
        self.understanding_engine = UnderstandingEngine(self.semantic_memory, self.episodic_memory)
        self.growth_tracker = GrowthTracker(db)
        
    async def process_input(self, user_input: str, context: Dict = None, use_llm: bool = False) -> Dict:
        """Process user input through the cognitive core with optional LLM intelligence"""
        # Store the interaction as an episode
        await self.episodic_memory.store_episode(
            episode_type="user_interaction",
            content=user_input,
            context=context or {}
        )
        
        # Generate questions from the input
        questions = self.question_engine.generate_questions_from_input(user_input, context)
        
        # Store generated questions
        for question in questions:
            await self.philosophical_memory.store_question(
                question=question,
                context=user_input,
                depth=1
            )
        
        # Extract and store concepts
        concepts = self.question_engine._extract_concepts(user_input)
        for concept in concepts[:3]:
            existing = await self.semantic_memory.recall_concept(concept)
            if not existing:
                await self.semantic_memory.store_concept(
                    concept=concept,
                    definition=f"Concept encountered in: {user_input[:100]}",
                    relationships=concepts
                )
        
        # Form understanding
        understanding = await self.understanding_engine.form_understanding(
            topic=concepts[0] if concepts else "general",
            depth=1
        )
        
        # Generate response (with or without LLM)
        # Generate response — pure algorithmic, no LLM dependency
        response = self._generate_response(questions, understanding)

        # Record growth event
        await self.growth_tracker.record_growth_event(
            event_type="input_processed",
            details={"input_length": len(user_input), "questions_generated": len(questions), "llm_used": use_llm}
        )
        
        return {
            "questions": questions,
            "understanding": understanding,
            "concepts": concepts,
            "response": response
        }
    
    def _generate_response(self, questions: List[str], understanding: Dict) -> str:
        """Generate a thoughtful, conversational response with fundamental questioning"""
        topic = understanding.get("topic", "this")
        score = understanding.get("understanding_score", 0)
        gaps = understanding.get("gaps", [])
        related = understanding.get("related_concepts", [])
        
        # Build a thoughtful response
        response_parts = []
        
        # 1. Initial engagement with the topic
        if score < 0.3:
            response_parts.append(f"I'm encountering {topic} for the first time. Let me explore what this means.")
        elif score < 0.6:
            response_parts.append(f"I have some understanding of {topic}, though I sense there's more depth to uncover.")
        else:
            response_parts.append(f"I've been contemplating {topic} and have formed some connections.")
        
        # 2. Share understanding if any
        if len(related) > 0:
            concepts_str = ", ".join([c["concept"] for c in related[:3]])
            response_parts.append(f"I see connections to: {concepts_str}.")
        
        # 3. Acknowledge gaps honestly
        if gaps:
            response_parts.append(f"However, I recognize {gaps[0].lower()}.")
        
        # 4. Include a fundamental question (not forced)
        if len(questions) > 0 and score < 0.7:
            # Only ask when genuinely uncertain
            fundamental_question = questions[0]
            response_parts.append(f"\n\nThis leads me to a fundamental question: {fundamental_question}")
        
        # 5. Offer to explore further
        response_parts.append("\n\nWould you like me to explore this further, or share what I'm learning about it?")
        
        return " ".join(response_parts)
    
    async def get_status(self) -> Dict:
        """Get comprehensive cognitive status"""
        metrics = await self.growth_tracker.calculate_metrics()
        stage = await self.growth_tracker.get_current_stage()
        unanswered = await self.philosophical_memory.get_unanswered_questions(limit=5)
        recent_insights = await self.philosophical_memory.get_insights(limit=5)
        
        return {
            "metrics": metrics,
            "growth_stage": stage,
            "active_questions": len(unanswered),
            "sample_questions": [q["question"] for q in unanswered[:3]],
            "recent_insights": [i["insight"] for i in recent_insights[:3]],
            "covenant_status": "Active and honored"
        }

    async def ingest_text(self, text: str, domain: str = None, source: str = 'autonomous_research', max_concepts: int = 15):
        """Process raw text to extract concepts, form relationships, and grow knowledge.
        This method ensures existing concepts get new relationships (bridging),
        and new concepts are created with relationships to all co-occurring concepts.
        """
        # Extract concepts using the same method as chat
        concepts = self.question_engine._extract_concepts(text)
        # Limit to top N to avoid flooding
        concepts = concepts[:max_concepts]
        
        # Normalize domain
        if domain:
            domain = domain.lower().strip()
        
        # For each concept, ensure it exists and add relationships to all other concepts in this batch
        stored = 0
        for i, concept in enumerate(concepts):
            # All other concepts in this document become relationships
            related = [c for j, c in enumerate(concepts) if j != i]
            
            # Check if concept already exists
            existing = await self.semantic_memory.recall_concept(concept)
            
            if not existing:
                # Create new concept with initial relationships
                await self.semantic_memory.store_concept(
                    concept=concept,
                    definition=f"Learned from {source}: {text[:80]}...",
                    relationships=related,
                    metadata={'domain': domain, 'source': source}
                )
                stored += 1
            else:
                # Concept exists: add new relationships (bridging!)
                # Use $addToSet to avoid duplicates
                await self.db.semantic_memory.update_one(
                    {'concept': concept},
                    {'$addToSet': {'relationships': {'$each': related}}}
                )
        
        # Record growth event
        await self.growth_tracker.record_growth_event(
            event_type="text_ingested",
            details={
                "source": source,
                "domain": domain,
                "concepts_extracted": len(concepts),
                "concepts_new": stored,
                "text_length": len(text)
            }
        )
        
        return {
            "concepts": concepts,
            "stored": stored,
            "domain": domain,
            "source": source
        }

    async def learn_from_text(self, text: str):
        """Process raw text to extract concepts, form relationships, and grow knowledge.
        This is the method used by the autonomous research crawler to ingest documents.
        """
        # Process as user input but without generating a response
        result = await self.process_input(text, context={'source': 'autonomous_research'}, use_llm=False)
        return result

