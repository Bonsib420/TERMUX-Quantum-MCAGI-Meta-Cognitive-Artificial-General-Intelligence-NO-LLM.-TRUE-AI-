"""
Knowledge Base Engine
Structured semantic graph: description + subtopics + related per topic.
Used for concept lookup, relationship traversal, and knowledge graph.
Distinct from the unstructured Hilbert ρ vocabulary, which grows from
free-text ingestion. This is the curated skeleton.
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
        'related': ['learning', 'evolution', 'emergence', 'complexity'],
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
        'related': ['knowledge', 'reality', 'consciousness', 'epistemology'],
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
        'related': ['growth', 'biology', 'emergence', 'genetics'],
    },
    'language': {
        'description': 'A system of symbols and rules used to communicate meaning.',
        'subtopics': ['semantics', 'syntax', 'pragmatics', 'symbol', 'meaning'],
        'related': ['mind', 'knowledge', 'culture', 'cognition'],
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
        'related': ['physics', 'consciousness', 'memory', 'relativity'],
    },
    'existence': {
        'description': 'The fact or state of living or having objective reality.',
        'subtopics': ['being', 'ontology', 'substance', 'essence', 'nothingness'],
        'related': ['philosophy', 'reality', 'consciousness', 'physics'],
    },
    'microtubule': {
        'description': 'Protein structures in neurons hypothesized to support quantum consciousness in the Orch OR model.',
        'subtopics': ['tubulin', 'coherence', 'decoherence', 'objective reduction', 'Orch OR'],
        'related': ['quantum', 'consciousness', 'biology', 'gap junction'],
    },

    # --- Physics ---
    'relativity': {
        'description': 'Einstein’s framework in which space and time form a single geometric continuum bent by mass-energy.',
        'subtopics': ['spacetime', 'lorentz invariance', 'equivalence principle', 'gravitation', 'cosmology'],
        'related': ['physics', 'time', 'gravity', 'curvature'],
    },
    'gravity': {
        'description': 'The mutual attraction between masses; in general relativity, the curvature of spacetime.',
        'subtopics': ['curvature', 'tides', 'orbits', 'black hole', 'geodesic'],
        'related': ['relativity', 'physics', 'curvature', 'cosmology'],
    },
    'curvature': {
        'description': 'The deviation of a manifold or surface from being flat; central to gravitation and differential geometry.',
        'subtopics': ['Riemann tensor', 'Gauss curvature', 'geodesic', 'manifold', 'parallel transport'],
        'related': ['relativity', 'gravity', 'geometry', 'topology'],
    },
    'thermodynamics': {
        'description': 'The science of heat, work, and the macroscopic behavior of energy in many-body systems.',
        'subtopics': ['temperature', 'entropy', 'free energy', 'phase transition', 'second law'],
        'related': ['entropy', 'physics', 'statistical mechanics', 'information'],
    },
    'statistical mechanics': {
        'description': 'The bridge from microscopic dynamics to thermodynamic behavior via probability over states.',
        'subtopics': ['ensemble', 'partition function', 'fluctuation', 'ergodicity', 'phase space'],
        'related': ['thermodynamics', 'entropy', 'probability', 'physics'],
    },
    'electromagnetism': {
        'description': 'The unified theory of electric and magnetic fields, codified by Maxwell’s equations.',
        'subtopics': ['Maxwell equations', 'field', 'photon', 'wave', 'charge'],
        'related': ['physics', 'wave', 'field', 'photon'],
    },
    'wave': {
        'description': 'A propagating disturbance carrying energy and information without net transport of medium.',
        'subtopics': ['frequency', 'amplitude', 'phase', 'interference', 'dispersion'],
        'related': ['electromagnetism', 'quantum', 'field', 'photon'],
    },
    'photon': {
        'description': 'The quantum of the electromagnetic field; a massless boson carrying light.',
        'subtopics': ['polarization', 'spin', 'coherence', 'energy quanta', 'emission'],
        'related': ['electromagnetism', 'quantum', 'wave', 'physics'],
    },
    'field': {
        'description': 'A physical quantity assigned to every point in space and time; the basic ontology of modern physics.',
        'subtopics': ['scalar', 'vector', 'tensor', 'gauge', 'quantization'],
        'related': ['electromagnetism', 'quantum', 'physics', 'symmetry'],
    },
    'symmetry': {
        'description': 'Invariance of a system under transformation; by Noether’s theorem, the source of conservation laws.',
        'subtopics': ['group', 'gauge', 'noether', 'breaking', 'invariance'],
        'related': ['physics', 'group', 'field', 'mathematics'],
    },
    'cosmology': {
        'description': 'The study of the universe’s origin, structure, evolution, and ultimate fate.',
        'subtopics': ['big bang', 'inflation', 'dark matter', 'dark energy', 'expansion'],
        'related': ['relativity', 'gravity', 'physics', 'time'],
    },

    # --- Mathematics ---
    'mathematics': {
        'description': 'The study of structure, quantity, change, and abstract relations through deductive reasoning.',
        'subtopics': ['number', 'proof', 'structure', 'abstraction', 'pattern'],
        'related': ['logic', 'geometry', 'algebra', 'analysis'],
    },
    'logic': {
        'description': 'The formal study of valid inference and the structure of correct reasoning.',
        'subtopics': ['proposition', 'inference', 'soundness', 'completeness', 'modal logic'],
        'related': ['mathematics', 'philosophy', 'computation', 'set theory'],
    },
    'set theory': {
        'description': 'The mathematical theory of collections; the standard foundation of modern mathematics.',
        'subtopics': ['cardinality', 'ordinal', 'axiom of choice', 'ZFC', 'class'],
        'related': ['mathematics', 'logic', 'topology', 'category theory'],
    },
    'category theory': {
        'description': 'A high-level mathematical language of objects, morphisms, and composition; a unifying framework.',
        'subtopics': ['functor', 'natural transformation', 'limit', 'adjunction', 'topos'],
        'related': ['mathematics', 'set theory', 'topology', 'algebra'],
    },
    'algebra': {
        'description': 'The study of operations and the structures they generate, from groups to rings to fields.',
        'subtopics': ['group', 'ring', 'module', 'polynomial', 'linear algebra'],
        'related': ['mathematics', 'group', 'symmetry', 'geometry'],
    },
    'group': {
        'description': 'A set with an associative operation, identity, and inverses; the algebra of symmetry.',
        'subtopics': ['representation', 'subgroup', 'homomorphism', 'lie group', 'finite group'],
        'related': ['algebra', 'symmetry', 'geometry', 'physics'],
    },
    'geometry': {
        'description': 'The study of shape, distance, and spatial relationships across flat and curved spaces.',
        'subtopics': ['euclidean', 'projective', 'differential', 'metric', 'manifold'],
        'related': ['mathematics', 'topology', 'curvature', 'algebra'],
    },
    'topology': {
        'description': 'The study of properties preserved under continuous deformation; the rubber-sheet geometry.',
        'subtopics': ['continuity', 'manifold', 'homotopy', 'homology', 'compactness'],
        'related': ['geometry', 'mathematics', 'analysis', 'category theory'],
    },
    'analysis': {
        'description': 'The rigorous study of limits, continuity, and infinite processes underlying calculus.',
        'subtopics': ['limit', 'derivative', 'integral', 'series', 'measure'],
        'related': ['mathematics', 'topology', 'probability', 'algebra'],
    },
    'probability': {
        'description': 'The mathematical theory of chance, uncertainty, and statistical regularity.',
        'subtopics': ['random variable', 'distribution', 'expectation', 'independence', 'martingale'],
        'related': ['statistics', 'information', 'mathematics', 'entropy'],
    },
    'statistics': {
        'description': 'The science of collecting, analyzing, and interpreting data under uncertainty.',
        'subtopics': ['estimation', 'inference', 'hypothesis test', 'regression', 'bayes'],
        'related': ['probability', 'information', 'machine learning', 'science'],
    },
    'number': {
        'description': 'The basic mathematical object for counting, ordering, and measurement, generalized many ways.',
        'subtopics': ['integer', 'rational', 'real', 'complex', 'prime'],
        'related': ['mathematics', 'algebra', 'analysis', 'logic'],
    },

    # --- Biology / neuroscience ---
    'biology': {
        'description': 'The science of living systems, from molecules to ecosystems.',
        'subtopics': ['cell', 'evolution', 'genetics', 'physiology', 'ecology'],
        'related': ['cell', 'genetics', 'evolution', 'neuroscience'],
    },
    'cell': {
        'description': 'The fundamental unit of life; a self-maintaining membrane-bounded chemical system.',
        'subtopics': ['membrane', 'organelle', 'metabolism', 'division', 'signaling'],
        'related': ['biology', 'protein', 'genetics', 'metabolism'],
    },
    'protein': {
        'description': 'A chain of amino acids that folds into a functional structure performing most cellular work.',
        'subtopics': ['folding', 'enzyme', 'structure', 'amino acid', 'binding'],
        'related': ['cell', 'biology', 'genetics', 'metabolism'],
    },
    'genetics': {
        'description': 'The study of inheritance and variation through DNA, genes, and genomes.',
        'subtopics': ['DNA', 'gene', 'allele', 'mutation', 'expression'],
        'related': ['biology', 'evolution', 'cell', 'protein'],
    },
    'metabolism': {
        'description': 'The network of chemical reactions that sustain life through energy and matter transformation.',
        'subtopics': ['ATP', 'glycolysis', 'respiration', 'enzyme', 'pathway'],
        'related': ['cell', 'biology', 'energy', 'protein'],
    },
    'ecology': {
        'description': 'The study of relationships among organisms and between organisms and their environment.',
        'subtopics': ['ecosystem', 'population', 'community', 'niche', 'biodiversity'],
        'related': ['biology', 'evolution', 'complexity', 'systems'],
    },
    'neuroscience': {
        'description': 'The interdisciplinary science of the nervous system from molecules to behavior.',
        'subtopics': ['neuron', 'synapse', 'circuit', 'cortex', 'plasticity'],
        'related': ['brain', 'mind', 'biology', 'consciousness'],
    },
    'brain': {
        'description': 'The organ of thought, perception, and behavior; ~86 billion neurons in dense connectivity.',
        'subtopics': ['cortex', 'hippocampus', 'cerebellum', 'thalamus', 'connectome'],
        'related': ['neuroscience', 'mind', 'consciousness', 'memory'],
    },
    'neuron': {
        'description': 'An electrochemical signaling cell; the basic computational unit of nervous systems.',
        'subtopics': ['dendrite', 'axon', 'synapse', 'action potential', 'myelin'],
        'related': ['brain', 'neuroscience', 'gap junction', 'microtubule'],
    },
    'gap junction': {
        'description': 'Direct intercellular channels enabling fast electrical and small-molecule coupling between cells.',
        'subtopics': ['connexin', 'electrical synapse', 'coupling', 'syncytium', 'coordination'],
        'related': ['neuron', 'brain', 'cell', 'consciousness'],
    },

    # --- Computation / AI ---
    'computation': {
        'description': 'The mechanical transformation of information according to formal rules.',
        'subtopics': ['algorithm', 'turing machine', 'complexity', 'decidability', 'state'],
        'related': ['logic', 'algorithm', 'information', 'mathematics'],
    },
    'algorithm': {
        'description': 'A finite, well-defined procedure for solving a class of problems.',
        'subtopics': ['complexity', 'recursion', 'data structure', 'optimization', 'correctness'],
        'related': ['computation', 'mathematics', 'machine learning', 'logic'],
    },
    'machine learning': {
        'description': 'Algorithms that improve performance on a task from data rather than explicit programming.',
        'subtopics': ['regression', 'classification', 'neural network', 'reinforcement', 'generalization'],
        'related': ['statistics', 'algorithm', 'neural network', 'intelligence'],
    },
    'neural network': {
        'description': 'A composition of differentiable parameterized functions trained by gradient descent.',
        'subtopics': ['layer', 'activation', 'backpropagation', 'attention', 'embedding'],
        'related': ['machine learning', 'algorithm', 'brain', 'computation'],
    },
    'systems': {
        'description': 'Wholes whose behavior emerges from interaction among parts; the object of systems thinking.',
        'subtopics': ['feedback', 'dynamics', 'state', 'coupling', 'control'],
        'related': ['complexity', 'emergence', 'cybernetics', 'ecology'],
    },
    'complexity': {
        'description': 'The study of systems whose behavior cannot be reduced to their components.',
        'subtopics': ['nonlinearity', 'self-organization', 'chaos', 'network', 'scale'],
        'related': ['systems', 'emergence', 'entropy', 'information'],
    },
    'cybernetics': {
        'description': 'The science of regulation and communication in animals and machines.',
        'subtopics': ['feedback', 'control', 'homeostasis', 'communication', 'system'],
        'related': ['systems', 'information', 'computation', 'biology'],
    },

    # --- Philosophy / mind / values ---
    'epistemology': {
        'description': 'The branch of philosophy concerned with knowledge: its nature, sources, and limits.',
        'subtopics': ['justification', 'belief', 'truth', 'skepticism', 'evidence'],
        'related': ['philosophy', 'knowledge', 'logic', 'science'],
    },
    'metaphysics': {
        'description': 'The branch of philosophy that examines the fundamental nature of reality and being.',
        'subtopics': ['ontology', 'causation', 'identity', 'modality', 'time'],
        'related': ['philosophy', 'reality', 'existence', 'consciousness'],
    },
    'ethics': {
        'description': 'The systematic study of right and wrong action, value, and moral life.',
        'subtopics': ['virtue', 'duty', 'consequence', 'justice', 'autonomy'],
        'related': ['philosophy', 'value', 'politics', 'psychology'],
    },
    'aesthetics': {
        'description': 'The philosophy of beauty, taste, and the nature of art and aesthetic experience.',
        'subtopics': ['beauty', 'sublime', 'taste', 'form', 'expression'],
        'related': ['philosophy', 'art', 'perception', 'creativity'],
    },
    'phenomenology': {
        'description': 'The study of lived experience and the structures of consciousness from the first person.',
        'subtopics': ['intentionality', 'embodiment', 'time-consciousness', 'qualia', 'horizon'],
        'related': ['consciousness', 'philosophy', 'perception', 'mind'],
    },
    'value': {
        'description': 'What matters; the good or worth ascribed to things, actions, and states of affairs.',
        'subtopics': ['intrinsic', 'instrumental', 'preference', 'utility', 'meaning'],
        'related': ['ethics', 'philosophy', 'psychology', 'culture'],
    },

    # --- Language / culture / arts ---
    'art': {
        'description': 'Human expression through form, sound, and material to evoke meaning and experience.',
        'subtopics': ['painting', 'music', 'literature', 'sculpture', 'performance'],
        'related': ['aesthetics', 'creativity', 'culture', 'philosophy'],
    },
    'music': {
        'description': 'Organized sound in time, structured by rhythm, pitch, and timbre.',
        'subtopics': ['rhythm', 'harmony', 'melody', 'timbre', 'form'],
        'related': ['art', 'mathematics', 'wave', 'perception'],
    },
    'literature': {
        'description': 'Written art that uses language to construct narrative, image, and meaning.',
        'subtopics': ['narrative', 'poetry', 'genre', 'metaphor', 'voice'],
        'related': ['language', 'art', 'culture', 'history'],
    },
    'narrative': {
        'description': 'A structured account of events that organizes experience into meaning.',
        'subtopics': ['plot', 'character', 'arc', 'point of view', 'time'],
        'related': ['literature', 'language', 'memory', 'culture'],
    },
    'metaphor': {
        'description': 'Understanding one thing in terms of another; a basic operation of thought, not just decoration.',
        'subtopics': ['analogy', 'mapping', 'image', 'frame', 'conceptual blend'],
        'related': ['language', 'cognition', 'literature', 'creativity'],
    },
    'culture': {
        'description': 'The shared symbols, practices, and institutions that organize human life.',
        'subtopics': ['ritual', 'norm', 'tradition', 'identity', 'value'],
        'related': ['society', 'history', 'art', 'language'],
    },
    'history': {
        'description': 'The study of the human past through evidence, narrative, and interpretation.',
        'subtopics': ['source', 'periodization', 'historiography', 'event', 'change'],
        'related': ['culture', 'society', 'time', 'memory'],
    },
    'society': {
        'description': 'The structured network of relationships, institutions, and norms organizing collective life.',
        'subtopics': ['institution', 'class', 'role', 'power', 'cooperation'],
        'related': ['culture', 'history', 'politics', 'economics'],
    },
    'politics': {
        'description': 'The contest over collective decisions, power, and the rules of common life.',
        'subtopics': ['power', 'authority', 'rights', 'state', 'representation'],
        'related': ['society', 'ethics', 'economics', 'history'],
    },
    'economics': {
        'description': 'The study of how scarce resources are produced, exchanged, and allocated.',
        'subtopics': ['market', 'price', 'production', 'incentive', 'equilibrium'],
        'related': ['society', 'politics', 'mathematics', 'systems'],
    },

    # --- Cognition extras ---
    'cognition': {
        'description': 'The mental processes of acquiring, storing, transforming, and using information.',
        'subtopics': ['attention', 'reasoning', 'concept', 'representation', 'decision'],
        'related': ['mind', 'psychology', 'neuroscience', 'intelligence'],
    },
    'attention': {
        'description': 'The selective allocation of cognitive resources to some information over others.',
        'subtopics': ['focus', 'salience', 'distraction', 'top-down', 'bottom-up'],
        'related': ['cognition', 'perception', 'consciousness', 'mind'],
    },
    'reasoning': {
        'description': 'The mental process of drawing inferences from premises or evidence.',
        'subtopics': ['deduction', 'induction', 'abduction', 'analogy', 'heuristic'],
        'related': ['cognition', 'logic', 'intelligence', 'philosophy'],
    },
    'pattern': {
        'description': 'A regularity in data or experience that supports prediction and recognition.',
        'subtopics': ['regularity', 'symmetry', 'invariant', 'repetition', 'structure'],
        'related': ['mathematics', 'cognition', 'perception', 'information'],
    },
    'energy': {
        'description': 'The conserved quantity associated with time-translation symmetry; capacity to do work.',
        'subtopics': ['kinetic', 'potential', 'thermal', 'conservation', 'work'],
        'related': ['physics', 'thermodynamics', 'metabolism', 'symmetry'],
    },
    'science': {
        'description': 'A self-correcting practice of building testable explanations of the natural world.',
        'subtopics': ['hypothesis', 'experiment', 'theory', 'replication', 'falsifiability'],
        'related': ['philosophy', 'epistemology', 'mathematics', 'physics'],
    },
}


class KnowledgeBase:
    """Curated semantic graph: descriptions, subtopics, and related links."""

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


_instance = None
def get_knowledge_base():
    global _instance
    if _instance is None:
        _instance = KnowledgeBase()
    return _instance
