"""
🌙 Dream State Engine
When the AI is not actively chatting, it enters Dream State.
- Autonomous background activities
- Self-reflection and learning
- Dream-driven research: ideas → live web research → knowledge growth
- Autonomous cloud sync: brain state ↔ Wolfram Cloud
- Users can see what AI was doing while away
"""

import re
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
        
        # Dream activities — includes autonomous research + cloud sync
        self.dream_activities = [
            'memory_consolidation',
            'curiosity_research',
            'self_reflection',
            'idea_generation',
            'code_contemplation',
            'personality_development',
            'question_formation',
            'dream_driven_research',
            'cloud_sync',
        ]
        
        # Track cloud sync timing (don't sync every cycle)
        self._last_cloud_sync = None
        self._cloud_sync_interval_minutes = 15
    
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
        
        elif activity == 'dream_driven_research':
            return await self._dream_driven_research()
        
        elif activity == 'cloud_sync':
            return await self._cloud_sync()
        
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
    
    async def _dream_driven_research(self) -> Dict:
        """
        Dream-driven research: the dream engine generates an idea or picks a
        curiosity topic, then ACTUALLY researches it — fetching live web content
        and ingesting it into the knowledge graph. This is the dream→research
        pipeline that lets the AI grow autonomously.
        """
        try:
            # Build a research query from dream insights or curiosity
            query = None
            source_type = None
            
            # Strategy 1: Research a topic from a recent dream insight
            if self.insights_gained:
                recent = self.insights_gained[-5:]
                idea_insights = [i for i in recent if i.get('type') == 'idea']
                if idea_insights:
                    insight = random.choice(idea_insights)
                    concepts = insight.get('concepts', ())
                    if concepts:
                        query = f"{concepts[0]} {concepts[1]} connection significance"
                        source_type = 'dream_idea'
            
            # Strategy 2: Research from queued dream topics
            if not query and self.dream_topics:
                topic = random.choice(self.dream_topics[-10:])
                query = f"{topic} research findings"
                source_type = 'dream_curiosity'
            
            # Strategy 3: Pick from exploration topics
            if not query:
                from research_topics import EXPLORATION_TOPICS
                query = random.choice(EXPLORATION_TOPICS)
                source_type = 'exploration_topic'
            
            # Strategy 4: Pick a URL from the research feeds
            use_feed_url = random.random() < 0.4  # 40% chance to use a curated feed URL
            feed_url = None
            if use_feed_url:
                try:
                    import json, os
                    feeds_path = os.path.join(os.path.dirname(__file__), 'research_feeds.json')
                    if os.path.exists(feeds_path):
                        with open(feeds_path, 'r') as f:
                            feeds = json.load(f)
                        # Collect all URLs across all categories
                        all_urls = []
                        for cat_key, cat_data in feeds.items():
                            if cat_key.startswith('_'):
                                continue
                            all_urls.extend(cat_data.get('urls', []))
                        if all_urls:
                            feed_url = random.choice(all_urls)
                            source_type = 'feed_url'
                except Exception:
                    pass  # Fall back to search query
            
            # Execute the research
            text = None
            research_source = query
            
            if feed_url:
                # Fetch and extract from the curated URL
                try:
                    from document_ingester import fetch_url
                    fetched_text, status = fetch_url(feed_url)
                    if fetched_text and len(fetched_text) > 100:
                        text = fetched_text
                        research_source = feed_url
                except Exception as e:
                    logger.warning(f"Dream research URL fetch failed: {e}")
            
            if not text:
                # Fall back to DuckDuckGo search
                try:
                    from self_research import DDGS
                    ddgs = DDGS()
                    results = list(ddgs.text(query, max_results=5))
                    if results:
                        text = ' '.join([r.get('body', '') for r in results])
                except Exception as e:
                    logger.warning(f"Dream research search failed: {e}")
            
            if not text or len(text) < 50:
                return {
                    'activity': 'dream_driven_research',
                    'status': 'no_results',
                    'query': query
                }
            
            # Ingest via cognitive core
            concepts_learned = 0
            try:
                from quantum_cognitive_core import QuantumCognitiveCore
                import shared_state
                if shared_state.cognitive_core:
                    from self_research import SelfResearchEngine
                    engine = SelfResearchEngine(self.db)
                    domain = engine._topic_to_domain(query)
                    result = await shared_state.cognitive_core.ingest_text(
                        text, domain=domain, source='dream_research', max_concepts=15
                    )
                    concepts_learned = result.get('stored', 0)
            except Exception as e:
                logger.warning(f"Dream research ingest failed: {e}")
            
            # Record insight
            insight = {
                'type': 'dream_research',
                'query': query,
                'source': research_source,
                'source_type': source_type,
                'concepts_learned': concepts_learned,
                'discovered_at': datetime.now(timezone.utc).isoformat(),
                'text': f"Dream research: {query} (+{concepts_learned} concepts)"
            }
            self.insights_gained.append(insight)
            if self.current_dream:
                self.current_dream['insights'].append(insight)
                self.current_dream['topics_explored'].append(query)
            
            return {
                'activity': 'dream_driven_research',
                'query': query,
                'source_type': source_type,
                'concepts_learned': concepts_learned,
                'status': 'researched'
            }
            
        except Exception as e:
            logger.error(f"Dream-driven research error: {e}")
            return {'activity': 'dream_driven_research', 'error': str(e)}
    
    async def _cloud_sync(self) -> Dict:
        """
        Autonomous cloud sync: periodically save brain state to cloud providers
        and check for updates. The cloud IS the persistent brain —
        the app/website is just a window into it.
        
        Uses the provider-agnostic CloudProviderRegistry so the brain can
        grow with each user and eventually separate from any single vendor.
        Falls back to direct Wolfram Cloud calls if the registry isn't available.
        """
        # Rate-limit: only sync every N minutes
        now = datetime.now(timezone.utc)
        if self._last_cloud_sync:
            elapsed = (now - self._last_cloud_sync).total_seconds() / 60
            if elapsed < self._cloud_sync_interval_minutes:
                return {
                    'activity': 'cloud_sync',
                    'status': 'skipped',
                    'reason': f'Last sync {elapsed:.1f} min ago (interval: {self._cloud_sync_interval_minutes} min)'
                }
        
        try:
            import shared_state
            
            # Build brain data
            brain_data = {
                'saved_at': now.isoformat(),
                'version': '3.0',
                'sync_source': 'dream_engine_autonomous',
            }
            
            if shared_state.cognitive_core:
                try:
                    stats = shared_state.cognitive_core.get_growth_stats() if hasattr(shared_state.cognitive_core, 'get_growth_stats') else {}
                    from wolfram_cloud import _serialize_dates
                    brain_data['growth_stats'] = _serialize_dates(stats)
                except Exception:
                    brain_data['growth_stats'] = {}
            
            brain_data['dream_state'] = {
                'total_dreams': len(self.dream_log),
                'total_insights': len(self.insights_gained),
                'topics_explored': self.dream_topics[-50:],
                'recent_insights': [
                    {'type': i.get('type', ''), 'text': i.get('text', ''), 'at': i.get('discovered_at', '')}
                    for i in self.insights_gained[-20:]
                ],
            }
            
            # Try provider-agnostic registry first (supports multi-provider replication)
            save_ok = False
            provider_used = 'none'
            try:
                from cloud_provider import get_cloud_registry
                registry = get_cloud_registry()
                save_ok = registry.save('QuantumMCAGI/brain', brain_data)
                provider_used = 'registry'
            except ImportError:
                # Fallback to direct Wolfram Cloud
                try:
                    from wolfram_cloud import cloud_save_brain
                    if shared_state.cognitive_core:
                        save_ok = cloud_save_brain(shared_state.cognitive_core, self)
                        provider_used = 'wolfram_direct'
                except ImportError:
                    pass
            
            self._last_cloud_sync = now
            
            status = 'synced' if save_ok else 'save_failed'
            
            insight = {
                'type': 'cloud_sync',
                'status': status,
                'provider': provider_used,
                'discovered_at': now.isoformat(),
                'text': f"Cloud sync: {'✓ saved' if save_ok else '✗ failed'} brain state via {provider_used}"
            }
            self.insights_gained.append(insight)
            if self.current_dream:
                self.current_dream['insights'].append(insight)
            
            return {
                'activity': 'cloud_sync',
                'status': status,
                'provider': provider_used,
                'synced_at': now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Cloud sync error: {e}")
            return {'activity': 'cloud_sync', 'status': 'error', 'error': str(e)}
    
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
