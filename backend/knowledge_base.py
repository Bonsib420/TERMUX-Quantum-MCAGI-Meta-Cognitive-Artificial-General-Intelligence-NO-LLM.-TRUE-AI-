"""
Knowledge Base Engine
22 topics with semantic relationships.
From PDF 2 — not present in clean form in PDF 1.
Used for concept lookup, relationship traversal, and knowledge graph.
"""

import random
from typing import Dict, List, Optional


TOPICS = {
    'consciousness': {
        'description': "The state of being aware of and able to think about one's own existence.",
        'subtopics': ['awareness', 'self-awareness', 'sentience', 'phenomenology', 'qualia'],
        'related': ['quantum', 'mind', 'perception', 'reality'],
    },
    'quantum': {
        'description': 'The branch of physics dealing with matter and energy at the atomic and subatomic scale.',
        'subtopics': ['superposition', 'entanglement', 'wave-particle duality', 'uncertainty principle', 'collapse'],
        'related': ['consciousness', 'physics', 'reality', 'microtubule'],
    },
    'mind': {
        'description': 'The element of a person that enables awareness, thought, feeling, and memory.',
        'subtopics': ['cognition', 'perception', 'emotion', 'memory', 'imagination'],
        'related': ['consciousness', 'brain', 'psychology', 'language'],
    },
    'learning': {
        'description': 'The acquisition of knowledge or skills through experience, study, or teaching.',
        'subtopics': ['education', 'training', 'development', 'growth', 'adaptation'],
        'related': ['knowledge', 'intelligence', 'memory', 'growth'],
    },
    'growth': {
        'description': 'The process of developing, increasing, or maturing.',
        'subtopics': ['evolution', 'development', 'progress', 'transformation', 'emergence'],
        'related': ['learning', 'change', 'emergence', 'evolution'],
    },
    'knowledge': {
        'description': 'Facts, information, and skills acquired through experience or education.',
        'subtopics': ['wisdom', 'understanding', 'expertise', 'information', 'insight'],
        'related': ['learning', 'intelligence', 'philosophy', 'memory'],
    },
    'perception': {
        'description': 'The process of becoming aware of something through the senses or mind.',
        'subtopics': ['sensation', 'interpretation', 'attention', 'observation', 'intuition'],
        'related': ['consciousness', 'mind', 'reality', 'cognition'],
    },
    'reality': {
        'description': 'The state of things as they actually exist, as opposed to how they appear.',
        'subtopics': ['existence', 'truth', 'objectivity', 'subjectivity', 'being'],
        'related': ['quantum', 'perception', 'philosophy', 'consciousness'],
    },
    'physics': {
        'description': 'The natural science that studies matter, energy, space, and time.',
        'subtopics': ['mechanics', 'thermodynamics', 'electromagnetism', 'relativity', 'quantum'],
        'related': ['quantum', 'reality', 'mathematics', 'energy'],
    },
    'psychology': {
        'description': 'The scientific study of the human mind, behavior, and experience.',
        'subtopics': ['cognition', 'emotion', 'personality', 'development', 'behavior'],
        'related': ['mind', 'consciousness', 'brain', 'learning'],
    },
    'philosophy': {
        'description': 'The study of fundamental questions about existence, knowledge, values, and reason.',
        'subtopics': ['metaphysics', 'epistemology', 'ethics', 'logic', 'aesthetics'],
        'related': ['knowledge', 'reality', 'consciousness', 'wisdom'],
    },
    'intelligence': {
        'description': 'The ability to acquire and apply knowledge and skills.',
        'subtopics': ['reasoning', 'problem-solving', 'creativity', 'adaptation', 'learning'],
        'related': ['mind', 'learning', 'knowledge', 'consciousness'],
    },
    'emergence': {
        'description': 'The arising of novel, complex properties from simpler interactions.',
        'subtopics': ['self-organization', 'complexity', 'chaos', 'pattern', 'system'],
        'related': ['growth', 'consciousness', 'quantum', 'evolution'],
    },
    'evolution': {
        'description': 'The process of gradual development or change over time.',
        'subtopics': ['adaptation', 'selection', 'mutation', 'heredity', 'fitness'],
        'related': ['growth', 'learning', 'emergence', 'change'],
    },
    'language': {
        'description': 'A system of symbols and rules used to communicate meaning.',
        'subtopics': ['semantics', 'syntax', 'pragmatics', 'symbol', 'meaning'],
        'related': ['mind', 'knowledge', 'communication', 'thought'],
    },
    'memory': {
        'description': 'The mental faculty by which information is encoded, stored, and retrieved.',
        'subtopics': ['encoding', 'storage', 'retrieval', 'forgetting', 'recognition'],
        'related': ['mind', 'learning', 'knowledge', 'consciousness'],
    },
    'entropy': {
        'description': 'A measure of disorder, uncertainty, or randomness in a system.',
        'subtopics': ['disorder', 'randomness', 'information', 'thermodynamics', 'chaos'],
        'related': ['quantum', 'physics', 'information', 'complexity'],
    },
    'information': {
        'description': 'Data that has been processed to give it meaning and reduce uncertainty.',
        'subtopics': ['data', 'signal', 'noise', 'encoding', 'pattern'],
        'related': ['knowledge', 'entropy', 'language', 'quantum'],
    },
    'creativity': {
        'description': 'The ability to produce original, imaginative, and novel ideas or works.',
        'subtopics': ['imagination', 'innovation', 'divergent thinking', 'inspiration', 'art'],
        'related': ['intelligence', 'mind', 'emergence', 'growth'],
    },
    'time': {
        'description': 'The indefinite continued progress of events from past through present to future.',
        'subtopics': ['past', 'present', 'future', 'duration', 'causality'],
        'related': ['physics', 'consciousness', 'memory', 'change'],
    },
    'existence': {
        'description': 'The fact or state of living or having objective reality.',
        'subtopics': ['being', 'ontology', 'substance', 'essence', 'nothingness'],
        'related': ['philosophy', 'reality', 'consciousness', 'physics'],
    },
    'microtubule': {
        'description': 'Protein structures in neurons hypothesized to support quantum consciousness in the Orch OR model.',
        'subtopics': ['tubulin', 'coherence', 'decoherence', 'objective reduction', 'Orch OR'],
        'related': ['quantum', 'consciousness', 'biology', 'Penrose', 'Hameroff'],
    },
}


class KnowledgeBase:
    """Knowledge base with 22 topics and semantic graph traversal."""

    def __init__(self):
        self.topics = TOPICS
        self.queries = 0

    def lookup(self, concept: str) -> Optional[Dict]:
        """Look up a concept, fuzzy matching."""
        concept_lower = concept.lower()
        if concept_lower in self.topics:
            self.queries += 1
            return {'topic': concept_lower, **self.topics[concept_lower]}

        for topic_name, topic_data in self.topics.items():
            if concept_lower in topic_name or topic_name in concept_lower:
                self.queries += 1
                return {'topic': topic_name, **topic_data}
            if any(concept_lower in sub or sub in concept_lower
                   for sub in topic_data.get('subtopics', [])):
                self.queries += 1
                return {'topic': topic_name, **topic_data}

        return None

    def get_topic_explanation(self, topic: str) -> Optional[str]:
        """Compatibility alias for callers expecting the old API."""
        entry = self.lookup(topic)
        return entry['description'] if entry else None

    def get_related(self, concept: str, depth: int = 1) -> List[str]:
        """Get related concepts at given traversal depth."""
        entry = self.lookup(concept)
        if not entry:
            return []

        related = set(entry.get('related', []))
        if depth > 1:
            for r in list(related):
                sub_entry = self.lookup(r)
                if sub_entry:
                    related.update(sub_entry.get('related', [])[:2])

        return list(related)

    def suggest_for_concepts(self, concepts: List[str]) -> List[Dict]:
        """Get knowledge base entries relevant to a list of concepts."""
        results = []
        seen = set()
        for concept in concepts:
            entry = self.lookup(concept)
            if entry and entry['topic'] not in seen:
                results.append(entry)
                seen.add(entry['topic'])
        return results[:3]

    def get_random_topic(self) -> Dict:
        """Get a random topic for exploration."""
        name = random.choice(list(self.topics.keys()))
        return {'topic': name, **self.topics[name]}

    def list_all_topics(self) -> List[str]:
        return list(self.topics.keys())

    def get_status(self) -> Dict:
        return {
            'total_topics': len(self.topics),
            'topics': list(self.topics.keys()),
            'total_subtopics': sum(len(v.get('subtopics', [])) for v in self.topics.values()),
            'queries': self.queries,
        }


_kb_instance = None
def get_knowledge_base():
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance
