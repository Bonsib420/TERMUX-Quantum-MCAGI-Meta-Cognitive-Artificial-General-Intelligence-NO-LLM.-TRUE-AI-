"""
🌐 MULTI-DOMAIN KNOWLEDGE SYSTEM
================================
Specialized knowledge domains with dedicated corpora.

Each domain has:
- Dedicated Markov chain trained on domain-specific text
- Domain-specific vocabulary and concepts
- Cross-domain association mapping
- Dynamic domain detection and switching
"""

import re
import json
import os
import math
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
import logging

logger = logging.getLogger("quantum_ai")


class KnowledgeDomain:
    """
    A specialized knowledge domain with its own trained models.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.vocabulary = set()
        self.concepts = Counter()  # concept -> importance
        self.corpus = []  # Training texts
        self.keywords = set()  # Domain-identifying keywords
        self.associations = defaultdict(float)  # concept pair -> strength
    
    def add_corpus(self, text: str):
        """Add training text to domain."""
        self.corpus.append(text)
        words = re.findall(r'\b[a-z]+\b', text.lower())
        self.vocabulary.update(words)
        
        # Extract concepts (words 5+ chars, not stopwords)
        stopwords = {'about', 'which', 'their', 'there', 'would', 'could', 'should', 'through', 'between', 'these', 'those'}
        for word in words:
            if len(word) >= 5 and word not in stopwords:
                self.concepts[word] += 1
    
    def add_keywords(self, keywords: List[str]):
        """Add domain-identifying keywords."""
        self.keywords.update(k.lower() for k in keywords)
    
    def match_score(self, text: str) -> float:
        """Score how well text matches this domain."""
        words = set(re.findall(r'\b[a-z]+\b', text.lower()))
        
        # Keyword matches (high weight)
        keyword_matches = len(words & self.keywords)
        
        # Vocabulary overlap
        vocab_overlap = len(words & self.vocabulary) / max(len(words), 1)
        
        # Concept matches
        concept_matches = sum(1 for w in words if w in self.concepts)
        
        return keyword_matches * 3 + vocab_overlap * 2 + concept_matches * 0.5
    
    def get_top_concepts(self, n: int = 20) -> List[Tuple[str, int]]:
        """Get most important concepts in domain."""
        return self.concepts.most_common(n)


class MultiDomainKnowledge:
    """
    Multi-domain knowledge system with specialized expertise.
    
    Domains:
    - Philosophy: consciousness, existence, meaning, ethics
    - Physics: quantum, relativity, thermodynamics, matter
    - Computer Science: algorithms, computation, AI, data
    - Biology: evolution, life, genetics, neuroscience
    - Mathematics: logic, proof, sets, infinity
    - Psychology: mind, behavior, cognition, emotion
    - Language: semantics, syntax, communication, meaning
    """
    
    def __init__(self):
        self.domains: Dict[str, KnowledgeDomain] = {}
        self.cross_domain_links = defaultdict(list)  # concept -> [(domain, strength)]
        
        # Initialize all domains
        self._init_domains()
        
        # Persistence
        self.state_file = "/app/backend/domain_knowledge.json"
        self._load_state()
    
    def _init_domains(self):
        """Initialize all knowledge domains with seed corpora."""
        
        # ===== PHILOSOPHY =====
        phil = KnowledgeDomain("philosophy", "Study of fundamental questions about existence, knowledge, and ethics")
        phil.add_keywords(['consciousness', 'existence', 'meaning', 'ethics', 'morality', 'truth', 
                          'reality', 'being', 'philosophy', 'metaphysics', 'epistemology', 'ontology',
                          'free will', 'determinism', 'soul', 'mind', 'perception', 'phenomenology',
                          'knowledge', 'wisdom', 'virtue', 'justice', 'beauty', 'good', 'evil',
                          'thought', 'reason', 'logic', 'belief', 'understanding'])
        phil.add_corpus("""
            Consciousness is the subjective experience of awareness. The hard problem asks why physical processes 
            give rise to subjective experience at all. Qualia are the individual instances of subjective experience.
            
            Existence precedes essence means beings first exist then define themselves through choices. Authentic 
            existence requires confronting freedom and responsibility. Being-in-the-world describes our embedded nature.
            
            Truth can be understood as correspondence to facts, coherence among beliefs, or pragmatic usefulness.
            Knowledge is traditionally defined as justified true belief, though Gettier cases challenge this.
            
            Free will is the capacity to choose between alternatives without external determination. Compatibilists 
            argue free will is compatible with determinism if we act according to our desires. Libertarians argue 
            genuine free will requires indeterminism.
            
            Ethics examines how we ought to live and act. Deontology focuses on duties and rules. Consequentialism 
            judges actions by outcomes. Virtue ethics emphasizes character development. Care ethics prioritizes 
            relationships and context.
            
            The meaning of life is perhaps the central question of human existence. Existentialists argue we create 
            our own meaning. Nihilists deny objective meaning exists. Religious views often locate meaning in divine purpose.
        """)
        self.domains["philosophy"] = phil

        # ===== PHYSICS =====
        phys = KnowledgeDomain("physics", "Study of matter, energy, space, time, and their interactions")
        phys.add_keywords(['quantum', 'particle', 'wave', 'energy', 'matter', 'force', 'gravity',
                          'relativity', 'spacetime', 'photon', 'electron', 'atom', 'entropy',
                          'thermodynamics', 'momentum', 'mass', 'velocity', 'acceleration', 'field',
                          'time', 'space', 'light', 'universe', 'cosmos', 'black hole', 'star',
                          'planet', 'orbit', 'motion', 'speed', 'physics', 'mechanics',
                          'neutron star', 'supernova', 'galaxy', 'pulsar', 'quasar',
                          'superposition', 'entanglement', 'wormhole', 'singularity'])
        phys.add_corpus("""
            Quantum mechanics describes nature at atomic scales where classical physics breaks down. Particles 
            exhibit wave-particle duality, behaving as waves or particles depending on measurement. The Heisenberg 
            uncertainty principle limits simultaneous knowledge of position and momentum.
            
            Wave function collapse occurs when measurement forces a quantum system from superposition into definite 
            state. The Copenhagen interpretation says observation causes collapse. Many-worlds says all outcomes occur.
            
            Special relativity shows space and time are unified as spacetime. Time dilates and length contracts at 
            high velocities. Mass and energy are equivalent via E=mc². Nothing travels faster than light.
            
            General relativity describes gravity as spacetime curvature caused by mass-energy. Massive objects bend 
            spacetime, causing other objects to follow curved paths. Black holes are regions of extreme curvature.
            
            Thermodynamics governs energy transformations. The first law says energy is conserved. The second law 
            says entropy increases in closed systems. Temperature measures average kinetic energy of particles.
            
            The Standard Model describes fundamental particles and forces. Quarks combine into protons and neutrons. 
            Leptons include electrons and neutrinos. Gauge bosons carry forces. The Higgs boson gives mass.
        """)
        self.domains["physics"] = phys

        # ===== COMPUTER SCIENCE =====
        cs = KnowledgeDomain("computer_science", "Study of computation, algorithms, and information processing")
        cs.add_keywords(['algorithm', 'computation', 'programming', 'code', 'software', 'data',
                        'computer', 'artificial', 'intelligence', 'machine', 'learning', 'neural',
                        'network', 'database', 'memory', 'processor', 'binary', 'recursive'])
        cs.add_corpus("""
            Algorithms are step-by-step procedures for solving problems. Time complexity measures how runtime scales 
            with input size. Space complexity measures memory requirements. Big O notation describes asymptotic behavior.
            
            Machine learning enables computers to learn from data without explicit programming. Supervised learning 
            uses labeled examples. Unsupervised learning finds patterns in unlabeled data. Reinforcement learning 
            optimizes through trial and error with rewards.
            
            Neural networks are computing systems inspired by biological brains. Layers of artificial neurons process 
            inputs through weighted connections. Deep learning uses many layers to learn hierarchical representations.
            
            Data structures organize information for efficient access. Arrays provide constant-time indexed access. 
            Linked lists enable efficient insertion. Trees support hierarchical relationships. Hash tables offer 
            fast key-value lookup.
            
            Turing machines are theoretical models of computation. The Church-Turing thesis says they capture all 
            effective computation. The halting problem shows some questions are undecidable. P vs NP asks whether 
            efficient verification implies efficient solution.
            
            Artificial intelligence aims to create systems exhibiting intelligent behavior. Strong AI would possess 
            genuine understanding. Weak AI performs specific tasks without general intelligence. The Turing test 
            measures conversational indistinguishability from humans.
        """)
        self.domains["computer_science"] = cs

        self.__init_domains_continued()

    def __init_domains_continued(self, ):
        """Continuation of _init_domains — auto-extracted by self-evolution."""
        # ===== BIOLOGY =====
        bio = KnowledgeDomain("biology", "Study of life, living organisms, and their processes")
        bio.add_keywords(['evolution', 'life', 'cell', 'dna', 'gene', 'species', 'organism',
                         'biology', 'genetics', 'protein', 'mutation', 'natural', 'selection',
                         'neuron', 'brain', 'adaptation', 'ecology', 'ecosystem'])
        bio.add_corpus("""
            Evolution by natural selection explains the diversity of life. Variation arises through mutation and 
            recombination. Selection favors traits that enhance survival and reproduction. Over generations, 
            populations adapt to their environments.

            DNA encodes genetic information in sequences of nucleotides. Genes are segments that code for proteins. 
            Transcription copies DNA to RNA. Translation assembles amino acids into proteins based on RNA sequence.

            Cells are the basic units of life. Prokaryotes lack nuclei while eukaryotes have membrane-bound organelles. 
            Mitochondria generate energy through cellular respiration. Chloroplasts enable photosynthesis in plants.

            The brain processes information through networks of neurons. Synapses transmit signals between neurons 
            using neurotransmitters. Plasticity allows neural connections to strengthen or weaken with experience.

            Ecosystems are communities of organisms interacting with their environment. Energy flows from producers 
            through consumers to decomposers. Matter cycles through biogeochemical processes. Biodiversity provides 
            ecosystem resilience.

            Consciousness may emerge from neural complexity. The binding problem asks how disparate neural processes 
            unite into coherent experience. Theories range from global workspace to integrated information.
        """)
        self.domains["biology"] = bio

        # ===== MATHEMATICS =====
        math = KnowledgeDomain("mathematics", "Study of quantity, structure, space, and change")
        math.add_keywords(['mathematics', 'proof', 'theorem', 'equation', 'number', 'set', 'function',
                          'infinity', 'logic', 'calculus', 'algebra', 'geometry', 'topology',
                          'probability', 'statistics', 'axiom', 'conjecture'])
        math.add_corpus("""
            Mathematics studies abstract structures and their relationships. Proofs establish truth through logical 
            deduction from axioms. Theorems are proven statements. Conjectures are unproven claims believed to be true.

            Set theory provides foundations for mathematics. Sets are collections of objects. Operations include 
            union, intersection, and complement. Cardinality measures set size. Infinity comes in different sizes.

            Logic studies valid reasoning. Propositional logic deals with truth values of statements. Predicate 
            logic adds quantifiers over variables. Gödel showed consistent systems cannot prove their own consistency.

            Calculus analyzes change and accumulation. Derivatives measure instantaneous rates of change. Integrals 
            compute accumulated quantities. The fundamental theorem connects differentiation and integration.

            Probability quantifies uncertainty mathematically. Random variables map outcomes to numbers. Distributions 
            describe probability patterns. Bayes theorem updates beliefs given evidence. Statistics draws inferences 

            Topology studies properties preserved under continuous deformation. Homeomorphisms are continuous bijections 
            with continuous inverses. Genus counts holes in surfaces. Manifolds are spaces locally resembling Euclidean space.
        """)
        self.domains["mathematics"] = math

        # ===== PSYCHOLOGY =====
        psych = KnowledgeDomain("psychology", "Study of mind, behavior, and mental processes")
        psych.add_keywords(['psychology', 'mind', 'behavior', 'cognition', 'emotion', 'memory',
                           'perception', 'learning', 'motivation', 'personality', 'development',
                           'consciousness', 'unconscious', 'therapy', 'mental', 'thought'])
        psych.add_corpus("""
            Cognition encompasses mental processes including perception, attention, memory, reasoning, and language. 
            Working memory holds information for active manipulation. Long-term memory stores knowledge indefinitely.

            Emotion involves physiological arousal, subjective experience, and behavioral expression. Basic emotions 
            may be universal. Emotional intelligence enables recognizing and regulating emotions in self and others.

            Learning changes behavior through experience. Classical conditioning associates stimuli. Operant conditioning 
            shapes behavior through consequences. Observational learning occurs through watching others.

            Memory encodes, stores, and retrieves information. Encoding transforms experience into memory traces. 
            Storage maintains information over time. Retrieval accesses stored memories. Forgetting results from 
            decay or interference.

            Perception constructs experience from sensory input. Bottom-up processing builds from features. Top-down 
            processing applies expectations. Attention selects relevant information. Gestalt principles organize 
            perception into coherent wholes.

            Motivation drives and directs behavior. Intrinsic motivation comes from internal satisfaction. Extrinsic 
            motivation comes from external rewards. Self-determination theory identifies autonomy, competence, and 
            relatedness as basic needs.
        """)
        self.domains["psychology"] = psych

        # ===== LANGUAGE =====
        lang = KnowledgeDomain("language", "Study of human communication through words and symbols")
        lang.add_keywords(['language', 'word', 'meaning', 'grammar', 'syntax', 'semantics',
                          'communication', 'speech', 'linguistics', 'vocabulary', 'sentence',
                          'symbol', 'sign', 'discourse', 'pragmatics', 'translation'])
        lang.add_corpus("""
            Language enables communication through structured symbol systems. Phonology studies sound patterns. 
            Morphology examines word formation. Syntax governs sentence structure. Semantics analyzes meaning.

            Meaning arises from the relationship between signs and what they represent. Denotation is literal meaning. 
            Connotation is associated meaning. Context shapes interpretation. Pragmatics studies meaning in use.

            Grammar consists of rules governing language structure. Generative grammar proposes innate language 
            faculty. Construction grammar emphasizes learned patterns. Usage-based approaches derive grammar from 
            language experience.

            Communication transfers information between minds. Encoding converts thoughts to signals. Transmission 
            sends signals through channels. Decoding interprets signals as thoughts. Noise can corrupt transmission.

            Language acquisition occurs naturally in children. Critical periods exist for native-like attainment. 
            First language develops without formal instruction. Second language learning often requires explicit study.

            Thought and language interact complexly. The Sapir-Whorf hypothesis suggests language shapes thought. 
            Weak versions are well-supported. Strong versions claiming language determines thought are controversial.
        """)
        self.domains["language"] = lang

    
    def detect_domain(self, text: str) -> Tuple[str, float]:
        """Detect most relevant domain for text."""
        scores = {}
        for name, domain in self.domains.items():
            scores[name] = domain.match_score(text)
        
        if not scores:
            return ("philosophy", 0.0)  # Default domain
        
        best = max(scores.items(), key=lambda x: x[1])
        return best
    
    def get_domain(self, name: str) -> Optional[KnowledgeDomain]:
        """Get domain by name."""
        return self.domains.get(name)
    
    def get_relevant_corpus(self, text: str, top_k: int = 3) -> List[str]:
        """Get most relevant corpus texts for input."""
        domain_name, _ = self.detect_domain(text)
        domain = self.domains.get(domain_name)
        
        if domain:
            return domain.corpus[:top_k]
        return []
    
    def get_cross_domain_concepts(self, concept: str) -> List[Tuple[str, str, float]]:
        """Find concept across domains with relevance scores."""
        results = []
        concept_lower = concept.lower()
        
        for domain_name, domain in self.domains.items():
            if concept_lower in domain.concepts:
                results.append((domain_name, concept_lower, domain.concepts[concept_lower]))
            # Also check if concept in vocabulary
            elif concept_lower in domain.vocabulary:
                results.append((domain_name, concept_lower, 0.5))
        
        results.sort(key=lambda x: x[2], reverse=True)
        return results
    
    def add_to_domain(self, domain_name: str, text: str):
        """Add text to specific domain."""
        if domain_name in self.domains:
            self.domains[domain_name].add_corpus(text)
            self._save_state()
    
    def get_all_domains(self) -> List[str]:
        """Get list of all domain names."""
        return list(self.domains.keys())
    
    def get_domain_stats(self) -> Dict:
        """Get statistics for all domains."""
        return {
            name: {
                "vocabulary_size": len(d.vocabulary),
                "concept_count": len(d.concepts),
                "corpus_size": len(d.corpus),
                "top_concepts": d.get_top_concepts(5)
            }
            for name, d in self.domains.items()
        }
    
    def _save_state(self):
        """Save additional learned content."""
        try:
            # Only save learned additions, not initial corpus
            state = {
                "additional_corpus": {
                    name: domain.corpus[1:]  # Skip initial corpus
                    for name, domain in self.domains.items()
                    if len(domain.corpus) > 1
                },
                "saved_at": datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logger.warning(f"Could not save domain state: {e}")
    
    def _load_state(self):
        """Load previously learned content."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                
                for domain_name, texts in state.get("additional_corpus", {}).items():
                    if domain_name in self.domains:
                        for text in texts:
                            self.domains[domain_name].add_corpus(text)
                
                logger.info("Loaded domain knowledge state")
        except Exception as e:
            logger.warning(f"Could not load domain state: {e}")


# Singleton
_domain_knowledge = None

def get_domain_knowledge() -> MultiDomainKnowledge:
    """Get or create multi-domain knowledge system."""
    global _domain_knowledge
    if _domain_knowledge is None:
        _domain_knowledge = MultiDomainKnowledge()
    return _domain_knowledge
