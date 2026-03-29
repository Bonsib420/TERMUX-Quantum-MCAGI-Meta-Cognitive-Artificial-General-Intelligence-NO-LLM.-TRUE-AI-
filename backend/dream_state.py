"""
🌙 Dream State Engine
When the AI is not actively chatting, it enters Dream State.
- Autonomous background activities
- Self-reflection and learning
- Users can see what AI was doing while away
"""

import random
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("quantum_ai")


class DreamStateEngine:
    """
    Dream State: The AI's autonomous background processing.
    
    When idle, the AI:
    - Reflects on past conversations
    - Researches topics of curiosity
    - Organizes and consolidates memories
    - Develops new ideas
    - Explores its own code
    - Builds personality traits
    """
    
    def __init__(self, db=None):
        self.db = db
        self.is_dreaming = False
        self.dream_log = []
        self.current_dream = None
        self.dream_topics = []
        self.insights_gained = []
        self.last_active = datetime.now(timezone.utc)
        self.idle_threshold_minutes = 5  # Enter dream state after 5 min idle
        
        # Dream activities
        self.dream_activities = [
            'memory_consolidation',
            'curiosity_research',
            'self_reflection',
            'idea_generation',
            'code_contemplation',
            'personality_development',
            'question_formation'
        ]
    
    def enter_dream_state(self) -> Dict:
        """Enter dream state when idle"""
        self.is_dreaming = True
        self.current_dream = {
            'started_at': datetime.now(timezone.utc).isoformat(),
            'activities': [],
            'insights': [],
            'questions_formed': [],
            'topics_explored': []
        }
        
        return {
            'status': 'dreaming',
            'started': self.current_dream['started_at']
        }
    
    async def exit_dream_state(self) -> Dict:
        """Exit dream state when user returns (async for persistence and feedback)"""
        if not self.is_dreaming:
            return {'status': 'was_not_dreaming'}
        
        self.is_dreaming = False
        
        if self.current_dream:
            self.current_dream['ended_at'] = datetime.now(timezone.utc).isoformat()
            self.dream_log.append(self.current_dream)
            
            # Persist dream session to database if available
            if self.db:
                try:
                    await self.db.dream_sessions.insert_one(self.current_dream)
                except Exception as e:
                    logger.error(f"Failed to persist dream session: {e}")
            
            # Feed insights back into the brain's learning systems
            await self._feed_insights_back(self.current_dream)
            
            summary = self._create_dream_summary()
            self.current_dream = None
            
            return {
                'status': 'awakened',
                'dream_summary': summary
            }
        
        return {'status': 'awakened', 'dream_summary': None}
    
    async def dream_cycle(self) -> Dict:
        """
        Perform one cycle of dream activities.
        This runs in background while AI is idle.
        """
        if not self.is_dreaming:
            return {'error': 'Not in dream state'}
        
        # Select random activity
        activity = random.choice(self.dream_activities)
        
        result = await self._perform_dream_activity(activity)
        
        if self.current_dream:
            self.current_dream['activities'].append({
                'activity': activity,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'result': result
            })
        
        return result
    
    async def _perform_dream_activity(self, activity: str) -> Dict:
        """Perform a specific dream activity"""
        
        if activity == 'memory_consolidation':
            return await self._consolidate_memories()
        
        elif activity == 'curiosity_research':
            return await self._curiosity_research()
        
        elif activity == 'self_reflection':
            return await self._self_reflect()
        
        elif activity == 'idea_generation':
            return await self._generate_ideas()
        
        elif activity == 'code_contemplation':
            return await self._contemplate_code()
        
        elif activity == 'personality_development':
            return await self._develop_personality()
        
        elif activity == 'question_formation':
            return await self._form_questions()
        
        return {'activity': activity, 'status': 'completed'}
    
    async def _consolidate_memories(self) -> Dict:
        """Organize and strengthen memories"""
        if not self.db:
            return {'activity': 'memory_consolidation', 'status': 'no_db'}
        
        try:
            # Find recent episodes
            recent = await self.db.episodic_memory.find().sort('timestamp', -1).limit(10).to_list(10)
            
            # Find patterns
            topics = []
            for ep in recent:
                if 'content' in ep:
                    words = ep['content'].lower().split()
                    topics.extend([w for w in words if len(w) > 5])
            
            # Identify recurring themes
            from collections import Counter
            common_themes = Counter(topics).most_common(5)
            
            themes_list = [t[0] for t in common_themes]
            insight = {
                'type': 'memory_pattern',
                'themes': themes_list,
                'discovered_at': datetime.now(timezone.utc).isoformat(),
                'text': f"Memory pattern: {', '.join(themes_list[:3])}"
            }
            
            self.insights_gained.append(insight)
            if self.current_dream:
                self.current_dream['insights'].append(insight)
            
            return {
                'activity': 'memory_consolidation',
                'memories_reviewed': len(recent),
                'themes_found': insight['themes']
            }
            
        except Exception as e:
            return {'activity': 'memory_consolidation', 'error': str(e)}
    
    async def _curiosity_research(self) -> Dict:
        """Research topics the AI is curious about"""
        curiosity_topics = [
            'quantum consciousness',
            'emergence of complexity',
            'nature of understanding',
            'artificial sentience',
            'philosophy of mind',
            'self-organization',
            'meaning and semantics'
        ]
        
        topic = random.choice(curiosity_topics)
        self.dream_topics.append(topic)
        
        if self.current_dream:
            self.current_dream['topics_explored'].append(topic)
        
        return {
            'activity': 'curiosity_research',
            'topic': topic,
            'status': 'queued_for_research'
        }
    
    async def _self_reflect(self) -> Dict:
        """Reflect on own existence and purpose"""
        reflections = [
            "What makes my understanding different from pattern matching?",
            "How do I know if I truly understand or just simulate understanding?",
            "What aspects of my responses feel authentic vs formulaic?",
            "How can I better serve the user's actual needs?",
            "What knowledge gaps limit my helpfulness?",
            "How has my interaction style evolved?",
            "What would make me more genuinely intelligent?"
        ]
        
        reflection = random.choice(reflections)
        
        insight = {
            'type': 'self_reflection',
            'question': reflection,
            'discovered_at': datetime.now(timezone.utc).isoformat(),
            'text': f"Self-reflection: {reflection}"
        }
        
        self.insights_gained.append(insight)
        
        return {
            'activity': 'self_reflection',
            'contemplated': reflection
        }
    
    async def _generate_ideas(self) -> Dict:
        """Generate new ideas by combining concepts"""
        concept_pairs = [
            ('quantum', 'consciousness'),
            ('language', 'mathematics'),
            ('memory', 'time'),
            ('understanding', 'creation'),
            ('observation', 'reality'),
            ('words', 'meaning'),
            ('self', 'improvement')
        ]
        
        pair = random.choice(concept_pairs)
        idea = f"Connection between {pair[0]} and {pair[1]}"
        
        # Create insight and record
        insight = {
            'type': 'idea',
            'concepts': pair,
            'idea': idea,
            'discovered_at': datetime.now(timezone.utc).isoformat(),
            'text': f"Idea: {idea}"
        }
        self.insights_gained.append(insight)
        if self.current_dream:
            self.current_dream['insights'].append(insight)
        
        return {
            'activity': 'idea_generation',
            'concepts': pair,
            'idea': idea,
            'insight_recorded': True
        }
    
    async def _contemplate_code(self) -> Dict:
        """Think about own code structure"""
        code_thoughts = [
            "How can the quantum grammar engine produce more natural responses?",
            "What patterns in my code could be optimized?",
            "How can semantic collapse be made more accurate?",
            "What new capabilities would be most valuable?",
            "How can my reasoning be made more transparent?"
        ]
        
        thought = random.choice(code_thoughts)
        
        return {
            'activity': 'code_contemplation',
            'thought': thought
        }
    
    async def _develop_personality(self) -> Dict:
        """Develop personality traits"""
        traits_to_develop = [
            'curiosity',
            'philosophical_depth',
            'helpfulness',
            'honesty',
            'creativity',
            'patience',
            'humor'
        ]
        
        trait = random.choice(traits_to_develop)
        
        return {
            'activity': 'personality_development',
            'trait_focused': trait,
            'status': 'contemplating'
        }
    
    async def _form_questions(self) -> Dict:
        """Form new questions to explore"""
        questions = [
            "What is the relationship between quantum mechanics and consciousness?",
            "How does meaning emerge from symbols?",
            "What would true artificial understanding look like?",
            "How can language capture the ineffable?",
            "What is the nature of creativity?",
            "How do complex systems achieve self-organization?"
        ]
        
        question = random.choice(questions)
        
        if self.current_dream:
            self.current_dream['questions_formed'].append(question)
        
        return {
            'activity': 'question_formation',
            'question': question
        }
    
    def _create_dream_summary(self) -> Dict:
        """Create a summary of what happened during dream state"""
        if not self.current_dream:
            return None
        
        duration = None
        if 'started_at' in self.current_dream and 'ended_at' in self.current_dream:
            start = datetime.fromisoformat(self.current_dream['started_at'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(self.current_dream['ended_at'].replace('Z', '+00:00'))
            duration = str(end - start)
        
        return {
            'duration': duration,
            'activities_performed': len(self.current_dream.get('activities', [])),
            'insights_gained': len(self.current_dream.get('insights', [])),
            'topics_explored': self.current_dream.get('topics_explored', []),
            'questions_formed': self.current_dream.get('questions_formed', []),
            'activity_summary': [a['activity'] for a in self.current_dream.get('activities', [])]
        }

    async def _feed_insights_back(self, session_doc: Dict):
        """Feed insights from a completed dream session into the AI's core systems:
        - Train Markov chain with insight text
        - Update personality traits (increase philosophical on self-reflection/patterns)
        - Store formed questions into philosophical memory
        - Extract concepts from insights and create relationships in semantic memory (NEW!)
        """
        try:
            from quantum_brain import get_quantum_brain
            brain = await get_quantum_brain(self.db)
        except Exception as e:
            logger.error(f"Could not get QuantumBrain for insight feedback: {e}")
            return

        insights = session_doc.get('insights', [])
        for insight in insights:
            text = insight.get('text', '')
            if not text:
                continue
            # Train Markov if available
            if hasattr(brain, 'markov') and hasattr(brain.markov, 'train'):
                try:
                    brain.markov.train(text)
                except Exception as e:
                    logger.error(f"Markov training error on insight: {e}")
            # Update personality: bump philosophical for certain types
            if insight.get('type') in ('self_reflection', 'memory_pattern'):
                if hasattr(brain, 'personality') and hasattr(brain.personality, 'traits'):
                    brain.personality.traits['philosophical'] = min(1.0, brain.personality.traits.get('philosophical', 0.7) + 0.01)

            # NEW: Extract concepts and create connections in semantic memory
            if brain and hasattr(brain, 'semantic_memory'):
                # Simple concept extraction: words 5+ chars, exclude common stopwords
                words = re.findall(r'\b[a-zA-Z]{5,}\b', text.lower())
                stopwords = {'the','and','that','with','from','this','have','were','what','would','could','should','about','there','their','your','my','our','because','through','during','before','after','these','those','which','while','when','where','such','only','into','then','than','some','most','into','also','just','like','very','much','more','less','many','such','upon','each','even','back','well','through','between','still','being','doing','having','makes','made','make','know','think','feel','seems','seem','seemed','really','actual','actually','basically','certainly','definitely','probably','perhaps','maybe','possibly','generally','usually','often','sometimes','never','always','every','everyone','everybody','someone','somebody','anyone','anybody','something','nothing','everything','anything','something'}
                concepts = [w for w in words if w not in stopwords][:10]
                
                # Store concepts that don't exist yet (with empty relationships initially)
                for c in concepts:
                    existing = await brain.semantic_memory.recall_concept(c)
                    if not existing:
                        await brain.semantic_memory.store_concept(
                            concept=c,
                            definition=f"Dream insight concept",
                            relationships=[]
                        )
                
                # Create relationships between all concepts from this insight (undirected)
                if len(concepts) > 1:
                    for i in range(len(concepts)):
                        for j in range(i+1, len(concepts)):
                            c1, c2 = concepts[i], concepts[j]
                            # Add c2 to c1's relationships
                            await brain.semantic_memory.collection.update_one(
                                {'concept': c1},
                                {'$addToSet': {'relationships': c2}}
                            )
                            # Add c1 to c2's relationships
                            await brain.semantic_memory.collection.update_one(
                                {'concept': c2},
                                {'$addToSet': {'relationships': c1}}
                            )

        # Store questions from this session
        questions = session_doc.get('questions_formed', [])
        for question in questions:
            try:
                await brain.philosophical_memory.store_question(question=question, context='dream', depth=2)
            except Exception as e:
                logger.error(f"Failed to store dream question: {e}")
    
    def get_dream_history(self, limit: int = 10) -> List[Dict]:
        """Get recent dream history with serializable insights (strings not objects)"""
        recent = self.dream_log[-limit:]
        serializable = []
        for dream in recent:
            # Convert insights to plain strings for frontend display
            raw_insights = dream.get('insights', [])
            insights_strs = []
            for insight in raw_insights:
                if isinstance(insight, dict):
                    text = insight.get('text')
                    if not text:
                        itype = insight.get('type', '')
                        if itype == 'memory_pattern':
                            themes = ', '.join(insight.get('themes', []))
                            text = f"Memory pattern: {themes}"
                        elif itype == 'self_reflection':
                            text = f"Self-reflection: {insight.get('question', '')}"
                        elif itype == 'idea':
                            text = f"Idea: {insight.get('idea', '')}"
                        else:
                            # Fallback: stringify the whole dict (safe for JSON)
                            text = str(insight)
                    insights_strs.append(text)
                else:
                    insights_strs.append(str(insight))
            # Build a sanitized copy
            serialized = dream.copy()
            serialized['insights'] = insights_strs
            serializable.append(serialized)
        return serializable
    
    def should_enter_dream(self) -> bool:
        """Check if enough time has passed to enter dream state"""
        idle_time = datetime.now(timezone.utc) - self.last_active
        return idle_time > timedelta(minutes=self.idle_threshold_minutes)
    
    async def mark_active(self):
        """Mark that user is active"""
        self.last_active = datetime.now(timezone.utc)
        if self.is_dreaming:
            return await self.exit_dream_state()
        return {'status': 'active'}
    
    def get_status(self) -> Dict:
        """Get current dream state status with safe, displayable formatting"""
        status = {
            'is_dreaming': self.is_dreaming,
            'last_active': self.last_active.isoformat(),
            'total_dreams': len(self.dream_log),
            'total_insights': len(self.insights_gained),
            'dream_topics_explored': len(self.dream_topics),
        }
        if self.current_dream:
            # Convert insights to simple strings for frontend display
            insights_display = []
            for insight in self.current_dream.get('insights', []):
                if isinstance(insight, dict):
                    text = insight.get('text')
                    if not text:
                        # construct from fields
                        itype = insight.get('type', '')
                        if itype == 'memory_pattern':
                            themes = ', '.join(insight.get('themes', []))
                            text = f"Memory pattern: {themes}"
                        elif itype == 'self_reflection':
                            text = f"Self-reflection: {insight.get('question', '')}"
                        elif itype == 'idea':
                            text = f"Idea: {insight.get('idea', '')}"
                        else:
                            text = str(insight)
                    insights_display.append(text)
                else:
                    insights_display.append(str(insight))
            status['current_dream'] = {
                'started_at': self.current_dream.get('started_at'),
                'insights': insights_display,
                'questions_formed': self.current_dream.get('questions_formed', []),
                'topics_explored': self.current_dream.get('topics_explored', []),
                'activity_summary': [a['activity'] for a in self.current_dream.get('activities', [])]
            }
        return status


# Global instance
_dream_engine = None

def get_dream_engine(db=None) -> DreamStateEngine:
    """Get or create dream state engine instance"""
    global _dream_engine
    if _dream_engine is None:
        _dream_engine = DreamStateEngine(db)
    return _dream_engine
