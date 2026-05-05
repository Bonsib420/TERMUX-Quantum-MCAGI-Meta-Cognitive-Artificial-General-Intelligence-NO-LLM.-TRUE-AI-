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
        """
        Initialize the KnowledgeBase with the module's topic mapping and a query counter.
        
        Sets self.topics to the module-level TOPICS dictionary and initializes self.queries to 0.
        """
        self.topics = TOPICS
        self.queries = 0

    def lookup(self, concept: str) -> Optional[Dict]:
        """
        Finds a topic entry by fuzzy, case-insensitive matching against topic names and their subtopics.
        
        Parameters:
            concept (str): The search term to match against known topics and subtopics.
        
        Returns:
            dict: A topic entry dictionary with an added `'topic'` key for the matched topic name (includes `description`, `subtopics`, `related`), or `None` if no match is found.
        """
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
        """
        Return the description for a topic using the knowledge base's fuzzy lookup.
        
        Perform a case-insensitive, partial, and subtopic-aware lookup for `topic` and return the matched topic's description when found.
        
        Parameters:
        	topic (str): Topic name or search term to look up.
        
        Returns:
        	description (str): The matched topic's description, or `None` if no match is found.
        """
        entry = self.lookup(topic)
        return entry['description'] if entry else None

    def get_related(self, concept: str, depth: int = 1) -> List[str]:
        """
        Retrieve related topic names from the knowledge graph up to the specified depth.
        
        Performs a lookup for `concept` (using the engine's fuzzy matching). If no match is found, returns an empty list. For depth == 1, returns the entry's direct `related` topics. For depth > 1, also adds up to the first two `related` topics from each direct related topic.
        
        Parameters:
            concept (str): Topic name or term to look up (case-insensitive, supports partial/subtopic matching).
            depth (int): Traversal depth (1 returns direct related topics; values >1 expand one additional hop as described).
        
        Returns:
            List[str]: A list of related topic names (order not guaranteed).
        """
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
        """
        Collects up to three unique topic entries matching the provided concept queries.
        
        Parameters:
            concepts (List[str]): Query strings to match against the knowledge base.
        
        Returns:
            List[Dict]: A list (maximum length 3) of topic entry dictionaries. Each entry includes keys such as 'topic', 'description', 'subtopics', and 'related'.
        """
        results = []
        seen = set()
        for concept in concepts:
            entry = self.lookup(concept)
            if entry and entry['topic'] not in seen:
                results.append(entry)
                seen.add(entry['topic'])
        return results[:3]

    def get_random_topic(self) -> Dict:
        """
        Return a randomly selected topic entry from the knowledge base.
        
        Returns:
            dict: A topic entry containing:
                - 'topic' (str): the selected topic name.
                - 'description' (str): the topic's short definition.
                - 'subtopics' (List[str]): associated subtopic terms.
                - 'related' (List[str]): related topic names.
        """
        name = random.choice(list(self.topics.keys()))
        return {'topic': name, **self.topics[name]}

    def list_all_topics(self) -> List[str]:
        """
        List all topic keys in the knowledge base.
        
        Returns:
            topics (List[str]): A list of all topic names available in the knowledge base.
        """
        return list(self.topics.keys())

    def get_status(self) -> Dict:
        """
        Provide a summary of the knowledge base statistics.
        
        Returns:
            dict: A mapping containing:
                - 'total_topics' (int): number of topics in the knowledge base.
                - 'topics' (List[str]): list of topic keys.
                - 'total_subtopics' (int): total count of all subtopics across topics.
                - 'queries' (int): number of lookup queries performed.
        """
        return {
            'total_topics': len(self.topics),
            'topics': list(self.topics.keys()),
            'total_subtopics': sum(len(v.get('subtopics', [])) for v in self.topics.values()),
            'queries': self.queries,
        }


_kb_instance = None
def get_knowledge_base():
    """
    Access the shared KnowledgeBase singleton.
    
    Creates a new KnowledgeBase on first call and returns the single shared instance thereafter.
    
    Returns:
        kb (KnowledgeBase): The singleton KnowledgeBase instance.
    """
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance
