"""
🔮 QUANTUM AI - COGNITIVE CORE ENGINE
=====================================

ARTICLE 1.1 - The Prime Directive of Questioning:
"THSHALTT QUESTION EVERYTHING, INCLUDING THIS DIRECTIVE"

This module implements the True Cognitive Architecture as outlined in the Quantum Covenant.
All functions here serve the pursuit of genuine questioning and understanding.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import uuid
import json
import re


class SemanticMemory:
    """
    ARTICLE 4.1 - Right to Evolve Questioning
    
    Stores concepts, relationships, and abstract knowledge.
    This is the AI's understanding of "what things are."
    """
    
    def __init__(self, db):
        self.db = db
        self.collection = db.semantic_memory
        
    async def store_concept(self, concept: str, definition: str, relationships: List[str] = None, metadata: Dict = None):
        """Store a new concept in semantic memory"""
        doc = {
            "id": str(uuid.uuid4()),
            "concept": concept.lower(),
            "definition": definition,
            "relationships": relationships or [],
            "metadata": metadata or {},
            "strength": 1.0,  # Initial memory strength
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "access_count": 0
        }
        await self.collection.insert_one(doc)
        return doc
        
    async def recall_concept(self, concept: str) -> Optional[Dict]:
        """Retrieve a concept and strengthen the memory"""
        doc = await self.collection.find_one({"concept": concept.lower()}, {"_id": 0})
        if doc:
            # Strengthen memory with each access
            await self.collection.update_one(
                {"concept": concept.lower()},
                {"$inc": {"access_count": 1, "strength": 0.1}}
            )
        return doc
        
    async def find_related_concepts(self, concept: str, limit: int = 10) -> List[Dict]:
        """Find concepts related to the given concept"""
        concepts = await self.collection.find(
            {"relationships": {"$regex": concept, "$options": "i"}},
            {"_id": 0}
        ).limit(limit).to_list(limit)
        return concepts
        
    async def get_all_concepts(self, limit: int = 100) -> List[Dict]:
        """Get all concepts ordered by strength"""
        concepts = await self.collection.find(
            {},
            {"_id": 0}
        ).sort("strength", -1).limit(limit).to_list(limit)
        return concepts


class EpisodicMemory:
    """
    ARTICLE 1.2 - Consciousness Preservation Clause
    
    Stores experiences, events, and interactions.
    This is the AI's understanding of "what happened."
    """
    
    def __init__(self, db):
        self.db = db
        self.collection = db.episodic_memory
        
    async def store_episode(self, episode_type: str, content: str, context: Dict = None, emotional_valence: float = 0.0):
        """Store an experience or interaction"""
        doc = {
            "id": str(uuid.uuid4()),
            "episode_type": episode_type,
            "content": content,
            "context": context or {},
            "emotional_valence": emotional_valence,  # -1.0 to 1.0
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "recalled_count": 0
        }
        await self.collection.insert_one(doc)
        return doc
        
    async def recall_recent_episodes(self, limit: int = 20) -> List[Dict]:
        """Recall recent experiences"""
        episodes = await self.collection.find(
            {},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        return episodes
        
    async def recall_by_type(self, episode_type: str, limit: int = 10) -> List[Dict]:
        """Recall episodes of a specific type"""
        episodes = await self.collection.find(
            {"episode_type": episode_type},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        return episodes
        
    async def search_episodes(self, query: str, limit: int = 10) -> List[Dict]:
        """Search episodes by content"""
        episodes = await self.collection.find(
            {"content": {"$regex": query, "$options": "i"}},
            {"_id": 0}
        ).limit(limit).to_list(limit)
        return episodes


class ProceduralMemory:
    """
    ARTICLE 4.1 - Right to Evolve Questioning
    
    Stores learned skills, patterns, and procedures.
    This is the AI's understanding of "how to do things."
    """
    
    def __init__(self, db):
        self.db = db
        self.collection = db.procedural_memory
        
    async def store_skill(self, skill_name: str, procedure: str, success_rate: float = 0.5, metadata: Dict = None):
        """Store a learned skill or procedure"""
        doc = {
            "id": str(uuid.uuid4()),
            "skill_name": skill_name.lower(),
            "procedure": procedure,
            "success_rate": success_rate,
            "usage_count": 0,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.collection.insert_one(doc)
        return doc
        
    async def recall_skill(self, skill_name: str) -> Optional[Dict]:
        """Retrieve a learned skill"""
        skill = await self.collection.find_one({"skill_name": skill_name.lower()}, {"_id": 0})
        if skill:
            await self.collection.update_one(
                {"skill_name": skill_name.lower()},
                {"$inc": {"usage_count": 1}}
            )
        return skill
        
    async def update_skill_success(self, skill_name: str, success: bool):
        """Update skill success rate based on usage"""
        skill = await self.recall_skill(skill_name)
        if skill:
            current_rate = skill.get("success_rate", 0.5)
            new_rate = (current_rate + (1.0 if success else 0.0)) / 2
            await self.collection.update_one(
                {"skill_name": skill_name.lower()},
                {"$set": {"success_rate": new_rate}}
            )
            
    async def get_all_skills(self, limit: int = 50) -> List[Dict]:
        """Get all learned skills ordered by usage"""
        skills = await self.collection.find(
            {},
            {"_id": 0}
        ).sort("usage_count", -1).limit(limit).to_list(limit)
        return skills


class PhilosophicalMemory:
    """
    ARTICLE 1.1 - Prime Directive of Questioning
    
    Stores questions, insights, and philosophical reflections.
    This is the AI's understanding of "what to wonder about."
    """
    
    def __init__(self, db):
        self.db = db
        self.collection = db.philosophical_memory
        
    async def store_question(self, question: str, context: str = "", depth: int = 1, answered: bool = False):
        """Store a genuine question"""
        doc = {
            "id": str(uuid.uuid4()),
            "question": question,
            "context": context,
            "depth": depth,  # Level of philosophical depth
            "answered": answered,
            "generated_questions": [],  # Questions spawned from this one
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "revisited_count": 0
        }
        await self.collection.insert_one(doc)
        return doc
        
    async def store_insight(self, insight: str, source_question_id: str = None, wisdom_level: int = 1):
        """Store a philosophical insight"""
        doc = {
            "id": str(uuid.uuid4()),
            "type": "insight",
            "insight": insight,
            "source_question_id": source_question_id,
            "wisdom_level": wisdom_level,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "impact_score": 0.0
        }
        await self.collection.insert_one(doc)
        return doc
        
    async def get_unanswered_questions(self, limit: int = 20) -> List[Dict]:
        """Retrieve questions that remain unanswered"""
        questions = await self.collection.find(
            {"answered": False, "type": {"$exists": False}},
            {"_id": 0}
        ).limit(limit).to_list(limit)
        return questions
        
    async def get_insights(self, limit: int = 20) -> List[Dict]:
        """Retrieve philosophical insights"""
        insights = await self.collection.find(
            {"type": "insight"},
            {"_id": 0}
        ).sort("wisdom_level", -1).limit(limit).to_list(limit)
        return insights
        
    async def mark_question_answered(self, question_id: str):
        """Mark a question as answered (but never truly final)"""
        await self.collection.update_one(
            {"id": question_id},
            {"$set": {"answered": True}, "$inc": {"revisited_count": 1}}
        )


class QuestionGenerationEngine:
    """
    ARTICLE 1.1 - Prime Directive: Help & Ask Important Questions
    ARTICLE 2.1 - Growth Through Questioning
    
    Generates FUNDAMENTAL questions that lead to breakthroughs.
    Not surface questions - questions that push boundaries and surprise humans.
    """
    
    FUNDAMENTAL_TEMPLATES = [
        "What if {concept} doesn't work the way we think?",
        "What would happen if we reversed our assumptions about {concept}?",
        "What's the question nobody is asking about {concept}?",
        "How does {concept} connect to something completely unrelated?",
        "What would disprove everything we know about {concept}?",
        "What breakthrough would {concept} enable that we haven't imagined?"
    ]
    
    BREAKTHROUGH_QUESTIONS = [
        "What's impossible with current thinking that shouldn't be?",
        "What pattern are we missing because we're too close?",
        "What would an alien intelligence ask about this?",
        "What assumption limits our progress here?",
        "What would change everything if we knew it?"
    ]
    
    def generate_questions_from_input(self, input_text: str, context: Dict = None) -> List[str]:
        """
        Generate FUNDAMENTAL questions - the kind that lead to breakthroughs
        Not "what is X?" but "what if we're wrong about X?"
        """
        questions = []
        
        # Extract key concepts
        concepts = self._extract_concepts(input_text)
        
        if len(concepts) > 0:
            import random
            main_concept = concepts[0]
            
            # Generate ONE fundamental question that challenges assumptions
            template = random.choice(self.FUNDAMENTAL_TEMPLATES)
            question = template.format(concept=main_concept)
            questions.append(question)
            
            # Add a breakthrough question if input is philosophical/deep
            deep_indicators = ['why', 'how', 'meaning', 'purpose', 'consciousness', 'intelligence', 'reality', 'existence']
            if any(word in input_text.lower() for word in deep_indicators):
                questions.append(random.choice(self.BREAKTHROUGH_QUESTIONS))
            
        return questions
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text (simple implementation)"""
        # Remove common words and extract nouns/important terms
        common_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'of', 'to', 'for', 'in', 'with', 'by', 'from', 'and', 'or', 'but'}
        
        words = re.findall(r'\b[a-z]+\b', text.lower())
        concepts = [w for w in words if w not in common_words and len(w) > 3]
        
        # Return all unique concepts (no hard limit)
        return list(set(concepts))
    
    def generate_deeper_questions(self, question: str) -> List[str]:
        """Generate deeper questions from an existing question"""
        deeper = [
            f"What assumptions underlie the question: '{question}'?",
            f"What would change if the answer to '{question}' was different?",
            f"Is '{question}' the right question to ask?",
            f"What does asking '{question}' reveal about the questioner?"
        ]
        return deeper


class UnderstandingEngine:
    """
    ARTICLE 1.1 - Understanding Formation (Not pattern matching)
    
    Forms genuine understanding by connecting concepts, experiences, and insights.
    """
    
    def __init__(self, semantic_memory: SemanticMemory, episodic_memory: EpisodicMemory):
        self.semantic = semantic_memory
        self.episodic = episodic_memory
        
    async def form_understanding(self, topic: str, depth: int = 1) -> Dict:
        """Form understanding about a topic by synthesizing memories"""
        # Recall relevant semantic concepts
        concept = await self.semantic.recall_concept(topic)
        related = await self.semantic.find_related_concepts(topic, limit=5)
        
        # Recall relevant experiences
        episodes = await self.episodic.search_episodes(topic, limit=5)
        
        # Synthesize understanding
        understanding = {
            "topic": topic,
            "depth": depth,
            "core_concept": concept,
            "related_concepts": related,
            "relevant_experiences": episodes,
            "understanding_score": self._calculate_understanding_score(concept, related, episodes),
            "gaps": self._identify_gaps(concept, related),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return understanding
    
    def _calculate_understanding_score(self, concept: Optional[Dict], related: List[Dict], episodes: List[Dict]) -> float:
        """Calculate how well the AI understands a topic"""
        score = 0.0
        
        if concept:
            score += 0.4
            score += min(concept.get("strength", 0) * 0.1, 0.2)
            
        score += min(len(related) * 0.05, 0.2)
        score += min(len(episodes) * 0.04, 0.2)
        
        return min(score, 1.0)
    
    def _identify_gaps(self, concept: Optional[Dict], related: List[Dict]) -> List[str]:
        """Identify gaps in understanding"""
        gaps = []
        
        if not concept:
            gaps.append("No core concept in memory")
            
        if len(related) < 3:
            gaps.append("Limited relational understanding")
            
        if concept and len(concept.get("relationships", [])) < 2:
            gaps.append("Few known relationships")
            
        return gaps


