"""
🔍 Self-Research Engine
Autonomous research capability for Quantum AI
- Research on demand or by user command
- Long-running autonomous sessions (30-60 minutes)
"""

import re
import random
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta

import requests as _requests

class DDGS:
    """Lightweight DuckDuckGo search using direct API calls."""
    def text(self, query, max_results=5):
        try:
            import urllib.parse, re
            encoded = urllib.parse.quote(query)
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
            r = _requests.get(f'https://html.duckduckgo.com/html/?q={encoded}', headers=headers, timeout=10)
            # Extract snippets from HTML
            snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', r.text, re.DOTALL)
            titles = re.findall(r'class="result__title"[^>]*>.*?<a[^>]*>(.*?)</a>', r.text, re.DOTALL)
            results = []
            for i, snippet in enumerate(snippets[:max_results]):
                clean = re.sub(r'<[^>]+>', '', snippet).strip()
                title = re.sub(r'<[^>]+>', '', titles[i]).strip() if i < len(titles) else query
                if clean:
                    results.append({'title': title, 'body': clean, 'href': ''})
            return results
        except Exception as e:
            return []

from research_topics import EXPLORATION_TOPICS



class SelfResearchEngine:
    """Autonomous research capability with extended sessions."""
    
    def __init__(self, db=None):
        self.db = db
        self.research_log = []
        self.knowledge_gaps = []
        self.auto_research_enabled = True
        self.research_queue = []
        
        # Autonomous research state
        self.autonomous_running = False
        self.autonomous_start_time = None
        self.autonomous_duration_minutes = 30
        self.autonomous_progress = self._init_progress()
        self.exploration_topics = EXPLORATION_TOPICS
    
    def _init_progress(self) -> Dict:
        return {
            'is_running': False,
            'started_at': None,
            'duration_minutes': 0,
            'elapsed_minutes': 0,
            'topics_researched': [],
            'insights_gained': 0,
            'concepts_learned': 0,
            'status': 'Idle'
        }
    
    async def research(self, query: str, reason: str = "user_request") -> Dict:
        """Perform research on a topic."""
        try:
            ddgs = DDGS()
            results = list(ddgs.text(query, max_results=5))
            
            research_result = {
                'query': query,
                'reason': reason,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'results': [{'title': r.get('title',''), 'body': r.get('body',''), 'href': r.get('href','')} for r in results],
                'summary': '',
                'new_concepts': self._extract_concepts(' '.join([r.get('body', '') for r in results]))
            }
            
            self.research_log.append(research_result)
            if self.db is not None:
                await self._store_research(research_result)
            
            return research_result
        except Exception as e:
            return {'query': query, 'reason': reason, 'error': str(e), 'results': []}
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text."""
        words = re.findall(r'\b[a-zA-Z]{5,}\b', text.lower())
        common = {'about', 'which', 'their', 'there', 'would', 'could', 'should', 'these', 'those', 'other', 'being', 'where', 'while', 'through', 'between'}
        from collections import Counter
        counts = Counter(w for w in words if w not in common)
        return [w for w, _ in counts.most_common(10)]

    def _topic_to_domain(self, topic: str) -> str:
        """Map research topic/document name to a broad knowledge domain."""
        topic_lower = topic.lower()
        mapping = {
            'quantum': 'physics',
            'physics': 'physics',
            'philosophy': 'philosophy',
            'mind': 'philosophy',
            'biology': 'biology',
            'cell': 'biology',
            'genetic': 'biology',
            'mathematics': 'mathematics',
            'algebra': 'mathematics',
            'geometry': 'mathematics',
            'history': 'history',
            'rome': 'history',
            'empire': 'history',
            'art': 'art',
            'renaissance': 'art',
            'psychology': 'psychology',
            'cognitive': 'psychology',
            'computer': 'computer science',
            'ai': 'computer science',
            'artificial': 'computer science',
            'literature': 'literature',
            'shakespeare': 'literature',
            'economics': 'economics',
            'market': 'economics',
            'environment': 'environmental science',
            'climate': 'environmental science',
            'ecology': 'environmental science',
            'cosmic': 'philosophy',  # cosmic_philosophy_physics.txt bridges physics + philosophy
            # New domains from research feeds
            'crime': 'crime and justice',
            'justice': 'crime and justice',
            'pirate': 'crime and justice',
            'tobacco': 'crime and justice',
            'daily': 'daily life',
            'food': 'daily life',
            'clothing': 'daily life',
            'family': 'daily life',
            'house': 'daily life',
            'religion': 'religion and mythology',
            'myth': 'religion and mythology',
            'angel': 'religion and mythology',
            'god': 'religion and mythology',
            'divine': 'religion and mythology',
            'zoroast': 'religion and mythology',
            'ahura': 'religion and mythology',
            'amaterasu': 'religion and mythology',
            'gnos': 'religion and mythology',
            'hermet': 'religion and mythology',
            'medicine': 'medicine',
            'medical': 'medicine',
            'disease': 'medicine',
            'plague': 'medicine',
            'anatomy': 'medicine',
            'vesalius': 'medicine',
            'galen': 'medicine',
            'technolog': 'technology',
            'invention': 'technology',
            'mechanism': 'technology',
            'astrolabe': 'technology',
            'aqueduct': 'technology',
            'timekeep': 'technology',
            'telescope': 'technology',
            'printing': 'technology',
            'music': 'music',
            'composer': 'music',
            'vivaldi': 'music',
            'bruckner': 'music',
            'dvorak': 'music',
            'harmonic': 'music',
            'tuning': 'music',
            'linguist': 'linguistics',
            'alphabet': 'linguistics',
            'writing': 'linguistics',
            'language': 'linguistics',
            'grammar': 'linguistics',
            'rosetta': 'linguistics',
            'celtic': 'linguistics',
            'cosmolog': 'cosmology',
            'big bang': 'cosmology',
            'multiverse': 'cosmology',
            'anthropic': 'cosmology',
            'entropy': 'information theory',
            'emergence': 'systems theory',
            'cybernetic': 'systems theory',
            'autopoiesis': 'systems theory',
            'complex': 'systems theory',
        }
        for keyword, domain in mapping.items():
            if keyword in topic_lower:
                return domain
        return 'general'
    
    async def _store_research(self, research: Dict):
        """Store research in database."""
        try:
            await self.db.research_history.insert_one({
                **research, '_stored_at': datetime.now(timezone.utc).isoformat()
            })
            for concept in research.get('new_concepts', [])[:5]:
                await self.db.semantic_memory.update_one(
                    {'concept': concept},
                    {'$set': {'concept': concept, 'source': 'research', 'query': research['query']},
                     '$inc': {'count': 1}},
                    upsert=True
                )
        except Exception as e:
            print(f"[RESEARCH] Store error: {e}")
    
    async def start_autonomous_research(self, duration_minutes: int = 30, engine=None, memory=None) -> Dict:
        """Start autonomous research session."""
        if self.autonomous_running:
            return {'status': 'already_running'}
        self.engine = engine
        self.memory = memory
        
        self.autonomous_running = True
        self.autonomous_start_time = datetime.now(timezone.utc)
        self.autonomous_duration_minutes = min(duration_minutes, 60)
        
        self.autonomous_progress = {
            'is_running': True,
            'started_at': self.autonomous_start_time.isoformat(),
            'duration_minutes': self.autonomous_duration_minutes,
            'elapsed_minutes': 0,
            'topics_researched': [],
            'insights_gained': 0,
            'concepts_learned': 0,
            'status': 'Starting...'
        }
        
        # Run research as async task in background
        import asyncio
        asyncio.create_task(self._run_autonomous_research())
        return {'status': 'started', 'duration_minutes': self.autonomous_duration_minutes,
                'message': f'Starting {self.autonomous_duration_minutes} minute autonomous research session'}
    
    async def _run_autonomous_research(self):
        """Background task for autonomous research."""
        try:
            has_db = self.db is not None
            print(f"[RESEARCH] Starting autonomous research, has_db={has_db}")
            
            # Check for local document corpus
            import os
            docs_dir = os.path.join(os.path.dirname(__file__), 'documents')
            use_local_corpus = os.path.exists(docs_dir) and any(f.endswith('.txt') for f in os.listdir(docs_dir))
            
            end_time = self.autonomous_start_time + timedelta(minutes=self.autonomous_duration_minutes)
            
            while datetime.now(timezone.utc) < end_time and self.autonomous_running:
                try:
                    if use_local_corpus:
                        # Pick a random document from the corpus
                        doc_files = [f for f in os.listdir(docs_dir) if f.endswith('.txt')]
                        if not doc_files:
                            break
                        doc_file = random.choice(doc_files)
                        topic = doc_file.replace('.txt', '').replace('_', ' ').title()
                        query = topic  # for DB storage
                        with open(os.path.join(docs_dir, doc_file), 'r', encoding='utf-8') as f:
                            text = f.read()
                    else:
                        # Fallback to DuckDuckGo search (requires internet)
                        topic = random.choice(self.exploration_topics)
                        query = f"{topic} {random.choice(['latest', 'explained', 'applications', 'deep dive'])}"
                        ddgs = DDGS()
                        results = list(ddgs.text(query, max_results=5))
                        if not results:
                            continue  # skip if no results
                        text = ' '.join([r.get('body', '') for r in results])
                    
                    self.autonomous_progress['topics_researched'].append(topic)
                    concepts = self._extract_concepts(text)
                    self.autonomous_progress['concepts_learned'] += len(concepts)
                    
                    # Ingest via cognitive core with domain tagging
                    if hasattr(self, 'engine') and self.engine:
                        domain = self._topic_to_domain(topic)
                        result = await self.engine.ingest_text(text, domain=domain, source='autonomous_research', max_concepts=15)
                        print(f"  [RESEARCH] Ingested: {topic} (domain={domain}, +{result['stored']} new concepts)")
                        
                        # Update in-memory counters for immediate UI feedback
                        if hasattr(self, 'memory') and self.memory:
                            self.memory.growth['total_concepts'] += result['stored']
                            if len(concepts) > 3:
                                self.memory.growth['total_insights'] += 1
                    
                    if len(concepts) > 3:
                        self.autonomous_progress['insights_gained'] += 1
                    
                    # Store research session metadata
                    if has_db:
                        try:
                            await self.db.research_history.insert_one({
                                'query': topic if use_local_corpus else query,
                                'topic': topic,
                                'reason': 'autonomous',
                                'timestamp': datetime.now(timezone.utc).isoformat(),
                                'concepts': concepts,
                                'results_count': 1 if use_local_corpus else len(results)
                            })
                            
                            # Update autonomous research aggregate metrics
                            await self.db.growth_metrics.update_one(
                                {'type': 'autonomous_research'},
                                {'$inc': {'researches': 1, 'concepts': len(concepts)},
                                 '$set': {'last_topic': topic, 'timestamp': datetime.now(timezone.utc).isoformat()}},
                                upsert=True
                            )
                            print(f"[RESEARCH] Logged: {topic}")
                        except Exception as db_err:
                            print(f"[RESEARCH] DB error: {db_err}")
                except Exception as e:
                    print(f"[RESEARCH] Search error: {e}")
                
                elapsed = (datetime.now(timezone.utc) - self.autonomous_start_time).total_seconds() / 60
                self.autonomous_progress['elapsed_minutes'] = round(elapsed, 1)
                import time; time.sleep(0.1)
            
            # Complete
            self.autonomous_running = False
            self.autonomous_progress['is_running'] = False
            self.autonomous_progress['status'] = f'Complete! {self.autonomous_progress["concepts_learned"]} concepts learned'
            
            if has_db:
                await self.db.autonomous_sessions.insert_one({
                    'completed_at': datetime.now(timezone.utc).isoformat(),
                    'duration': self.autonomous_duration_minutes,
                    'topics': len(self.autonomous_progress['topics_researched']),
                    'concepts': self.autonomous_progress['concepts_learned']
                })
                
        except Exception as e:
            print(f"[RESEARCH] Fatal error: {e}")
            self.autonomous_running = False
            self.autonomous_progress['status'] = f'Error: {e}'
    
    def stop_autonomous_research(self) -> Dict:
        """Stop autonomous research."""
        if not self.autonomous_running:
            return {'status': 'not_running'}
        self.autonomous_running = False
        self.autonomous_progress['is_running'] = False
        self.autonomous_progress['status'] = 'Stopped'
        return {'status': 'stopped', 'concepts': self.autonomous_progress['concepts_learned']}
    
    def get_autonomous_progress(self) -> Dict:
        """Get current progress."""
        if self.autonomous_running and self.autonomous_start_time:
            elapsed = (datetime.now(timezone.utc) - self.autonomous_start_time).total_seconds() / 60
            self.autonomous_progress['elapsed_minutes'] = round(elapsed, 1)
        return self.autonomous_progress
    
    def get_research_stats(self) -> Dict:
        """Get research statistics."""
        return {
            'total_researches': len(self.research_log),
            'knowledge_gaps_identified': len(self.knowledge_gaps),
            'queue_size': len(self.research_queue),
            'auto_research_enabled': self.auto_research_enabled,
            'recent_topics': [r['query'] for r in self.research_log[-5:]],
            'autonomous_running': self.autonomous_running
        }


# Singleton
_research_engine = None

async def get_research_engine(db=None) -> SelfResearchEngine:
    """Get or create research engine."""
    global _research_engine
    if _research_engine is None:
        _research_engine = SelfResearchEngine(db)
    if db is not None:
        _research_engine.db = db
    return _research_engine
