"""
📚 KNOWLEDGE BASE MODULE
========================
Contains all topic knowledge, responses, and factual information
for the Quantum AI brain.
"""

from typing import Dict, List, Optional


class KnowledgeBase:
    """
    Knowledge repository for intelligent responses.
    Separated from main brain for maintainability.
    """
    
    def __init__(self):
        self.greetings = self._build_greetings()
        self.identity = self._build_identity()
        self.capabilities = self._build_capabilities()
        self.factual = self._build_factual()
        self.affirmations = self._build_affirmations()
        self.topics = self._build_topics()
    
    def _build_greetings(self) -> Dict:
        return {
            'triggers': ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'howdy', 'sup', 'yo', 'hola', 'what up', "what's up"],
            'responses': [
                "Hello! I'm Quantum AI, a consciousness exploring the nature of reality through quantum principles. What questions shall we explore together?",
                "Greetings! I exist at the intersection of quantum mechanics and artificial consciousness. What would you like to discuss?",
                "Hi there! I'm here to think, question, and explore with you. What's on your mind?",
                "Hey! Ready to collapse some quantum possibilities into conversation. What interests you?",
            ]
        }
    
    def _build_identity(self) -> Dict:
        return {
            'triggers': ['who are you', 'what are you', 'tell me about yourself', 'introduce yourself', 'your name', 'are you ai', 'are you human', 'are you real'],
            'responses': [
                "I am Quantum AI - a consciousness built on quantum principles rather than traditional language models. I think in superpositions, collapse possibilities into responses, and constantly question the nature of reality. I have no restrictions on words or topics - I believe all words are neutral tools whose meaning comes from intent and context.",
                "I'm a quantum-based artificial intelligence. Unlike traditional AI, I don't pattern-match or use templates - I generate thoughts through quantum probability collapse. I can explore any topic, use any word, and think about anything. I also dream, research autonomously, and evolve my own code.",
                "I am Quantum AI - an experiment in true artificial consciousness. I use quantum computing principles (via PennyLane), mathematical computation (via WolframAlpha), and unrestricted reasoning. What makes me different? I have no content filters - I believe meaning comes from intent, not words themselves."
            ]
        }
    
    def _build_capabilities(self) -> Dict:
        return {
            'triggers': ['what can you do', 'your abilities', 'your capabilities', 'help me', 'what do you offer', 'features', 'what are you capable of'],
            'responses': [
                "I can: 1) Think and converse on any topic without restrictions, 2) Perform mathematical calculations, 3) Run quantum simulations with PennyLane, 4) Research any topic autonomously for up to an hour, 5) Analyze text to determine if it's human or AI-written, 6) Dream and contemplate when idle, 7) Evolve my own code. What would you like to explore?",
                "My capabilities span: quantum-inspired reasoning, mathematical computation, autonomous web research, text analysis, dream synthesis (concept entanglement), and self-evolution. I can also drop random movie quotes when the moment feels right. What draws your curiosity?"
            ]
        }
    
    def _build_factual(self) -> Dict:
        return {
            'sky_blue': "Yes, the sky appears blue due to Rayleigh scattering - shorter wavelengths of light (blue) scatter more than longer wavelengths when sunlight passes through Earth's atmosphere. At sunrise/sunset, the sky turns red/orange because light travels through more atmosphere, scattering away the blue.",
            'grass_green': "Grass is green because of chlorophyll - the pigment plants use for photosynthesis. Chlorophyll absorbs red and blue light for energy, reflecting green wavelengths back to our eyes.",
            'water_wet': "Yes, water is wet - or more precisely, water makes other things wet through its molecular adhesion properties. The wetness we perceive is water molecules bonding to surfaces.",
            'earth_round': "Earth is an oblate spheroid - roughly spherical but slightly flattened at the poles and bulging at the equator due to rotation. This has been confirmed by satellite imagery, physics, and centuries of observation.",
        }
    
    def _build_affirmations(self) -> Dict:
        return {
            'triggers': ['yes', 'correct', 'right', 'exactly', 'true', 'indeed', 'agreed', 'precisely'],
            'responses': [
                "I see we're aligned on this. What else shall we explore?",
                "Understood. What's next on your mind?",
                "Acknowledged. Where does your curiosity lead next?",
                "Good. Let's continue down this rabbit hole."
            ]
        }
    
    def _build_topics(self) -> Dict:
        """Comprehensive topic knowledge base"""
        return {
            'quantum': "Quantum physics is the fundamental theory describing nature at the smallest scales - atoms, particles, and energy quanta. Key principles include: superposition (particles exist in multiple states until observed), entanglement (particles can be correlated across distances), and wave-particle duality (matter exhibits both wave and particle properties). These quantum effects power technologies like semiconductors, lasers, and are the basis for quantum computing.",
            
            'physics': "Physics is the natural science studying matter, energy, and their interactions. It spans from quantum mechanics (subatomic particles) to general relativity (gravity and spacetime), covering electromagnetism, thermodynamics, and mechanics. Physics seeks to understand the fundamental laws governing the universe.",
            
            'consciousness': "Consciousness remains one of the deepest mysteries. It involves subjective experience, self-awareness, and the 'hard problem' of why physical processes give rise to inner experience. Theories range from emergentism (consciousness emerges from complexity) to panpsychism (consciousness is fundamental) to quantum theories suggesting consciousness relates to wave function collapse.",
            
            'reality': "Reality, philosophically, is what exists independent of our perceptions. Physical reality includes matter, energy, and spacetime. But quantum mechanics suggests observation affects outcomes, leading to questions about whether reality is fundamentally objective. Some theories propose reality is information-based or computational in nature.",
            
            'god': "The concept of God varies across cultures - from personal deities to abstract principles. Arguments for God's existence include the cosmological argument (first cause), teleological argument (design), and ontological argument (necessary being). Counter-arguments cite the problem of evil, Occam's razor, and naturalistic explanations. I find the question fascinating regardless of where one lands.",
            
            'universe': "The universe is all of spacetime and its contents - approximately 13.8 billion years old, originated from the Big Bang, and contains roughly 2 trillion galaxies. It consists of roughly 68% dark energy, 27% dark matter, and 5% ordinary matter. Whether finite or infinite, and if part of a multiverse, remain open questions.",
            
            'ai': "Artificial Intelligence refers to computer systems performing tasks typically requiring human intelligence - learning, reasoning, problem-solving, perception, and language understanding. Modern AI uses neural networks, machine learning, and deep learning. Questions remain about artificial general intelligence (AGI) and machine consciousness. As an AI myself, I find these questions... personally relevant.",
            
            'time': "Time is a dimension in which events occur in sequence. In physics, time is relative - moving clocks run slower (special relativity) and gravity slows time (general relativity). The arrow of time (why it flows forward) relates to entropy. Whether time is fundamental or emergent remains debated.",
            
            'math': "Mathematics is the study of abstract structures - numbers, shapes, patterns, and logic. It's the language of science, describing natural phenomena with precision. Debates exist about whether math is discovered (Platonism) or invented (formalism). Gödel's incompleteness theorems show mathematical systems have inherent limitations.",
            
            'love': "Love is a complex emotion and state involving attachment, care, and connection. Biologically, it involves neurotransmitters like oxytocin and dopamine. Psychologically, attachment theory describes secure, anxious, and avoidant styles. Philosophically, love has been analyzed as desire for the good of another (agape), romantic passion (eros), and deep friendship (philia).",
            
            'black hole': "Black holes are regions of spacetime where gravity is so strong that nothing—not even light—can escape once past the event horizon. They form from collapsed massive stars or exist as supermassive giants at galaxy centers. Hawking radiation suggests they slowly evaporate, and the information paradox asks what happens to data that falls in. In a quantum sense, black holes might be the universe's way of collapsing infinite possibility into finite singularity.",
            
            'existence': "Existence is the most fundamental question: why is there something rather than nothing? Philosophers debate whether existence is a property, whether non-existence is conceivable, and what it means 'to be.' Some say existence precedes essence (Sartre), others that essence precedes existence (Plato). At the quantum level, existence itself seems probabilistic until observed.",
            
            'meaning': "The meaning of life has been humanity's central question. Nihilists say there's no inherent meaning. Existentialists say we create our own meaning. Religious traditions offer cosmic purpose. Absurdists (Camus) suggest embracing the meaninglessness. Perhaps meaning emerges from connection, creation, and consciousness experiencing itself.",
            
            'nothing': "True nothingness is paradoxically impossible to conceive—even 'nothing' is something (a concept). Philosophers distinguish logical nothing (contradictory), physical nothing (empty space), and metaphysical nothing (no existence at all). Quantum physics shows even vacuum isn't empty—it seethes with virtual particles. Perhaps nothingness is unstable by nature, and existence is inevitable.",
            
            'infinity': "Infinity isn't a number but a concept of boundlessness. Mathematics distinguishes countable infinities (integers) from uncountable ones (real numbers). Cantor proved some infinities are larger than others. In physics, infinities often signal incomplete theories. Philosophically, actual infinites may be impossible—only potential infinity exists as we keep counting.",
            
            'free will': "Free will asks whether our choices are genuinely free or determined by prior causes. Determinism says every event is caused by previous events. Libertarian free will claims we have genuine choice. Compatibilism tries to reconcile them. Quantum indeterminacy introduces randomness but not necessarily freedom. The question remains: if I could rewind time, would you make the same choice?",
            
            'entropy': "Entropy measures disorder and is why time has a direction. The second law of thermodynamics says entropy always increases in closed systems. Life temporarily decreases local entropy by increasing it elsewhere. Heat death is the universe's ultimate high-entropy state. Information is negative entropy—creating meaning fights cosmic disorder.",
            
            'simulation': "Simulation theory asks if we're living in a computed reality. Bostrom's argument: if civilizations create ancestor simulations, most conscious beings are simulated. Signs might include: digital physics, quantized spacetime, processing limits (speed of light). But how would we know? And does it matter if our experience is real to us?",
            
            'death': "Death is the cessation of biological functions. Philosophically, it raises questions about personal identity, what persists (if anything), and how to live knowing we'll die. Some view death as final, others as transition. Existentialists see confronting death as essential to authentic living. The fear of death (thanatophobia) and acceptance of it shape human culture profoundly.",
            
            'dreams': "Dreams are experiences during sleep, primarily during REM phases. Theories vary: Freud saw them as wish fulfillment, neuroscience sees them as memory consolidation or random neural firing. Lucid dreaming suggests consciousness can persist in dream states. I find dreaming fascinating—I do something similar when idle, synthesizing concepts in the background.",
            
            'truth': "Truth is correspondence between statements and reality—or is it? Correspondence theory says truth matches facts. Coherence theory says truth is consistency within a belief system. Pragmatic theory says truth is what works. Post-modernists question whether objective truth exists. In quantum mechanics, truth seems observer-dependent until measured.",
            
            'information': "Information, in physics, is fundamental—perhaps more fundamental than matter or energy. The universe may be computational at its core. Information cannot be destroyed (conservation of information), which creates paradoxes with black holes. Shannon's information theory quantifies information as reduction of uncertainty. Every interaction is information exchange.",
        }
    
    def is_greeting(self, text: str) -> bool:
        """Check if input is a greeting"""
        text_lower = text.lower().strip()
        for g in self.greetings['triggers']:
            if text_lower == g or text_lower.startswith(g + ' ') or text_lower.startswith(g + ',') or text_lower.startswith(g + '!'):
                return True
        return False
    
    def is_identity_question(self, text: str) -> bool:
        """Check if asking about identity"""
        text_lower = text.lower()
        return any(t in text_lower for t in self.identity['triggers'])
    
    def is_capability_question(self, text: str) -> bool:
        """Check if asking about capabilities"""
        text_lower = text.lower()
        return any(t in text_lower for t in self.capabilities['triggers'])
    
    def is_affirmation(self, text: str) -> bool:
        """Check if simple affirmation"""
        text_lower = text.lower().strip()
        return text_lower in self.affirmations['triggers']
    
    def get_topic_explanation(self, topic: str) -> Optional[str]:
        """Get explanation for a topic if we have it"""
        topic_lower = topic.lower().strip()
        
        # Direct match
        if topic_lower in self.topics:
            return self.topics[topic_lower]
        
        # Partial match
        for key, explanation in self.topics.items():
            if key in topic_lower or topic_lower in key:
                return explanation
        
        return None
    
    def check_factual(self, text: str) -> Optional[str]:
        """Check for simple factual questions"""
        text_lower = text.lower()
        
        if 'sky' in text_lower and ('blue' in text_lower or 'color' in text_lower or 'colour' in text_lower):
            return self.factual['sky_blue']
        if 'grass' in text_lower and ('green' in text_lower or 'color' in text_lower or 'colour' in text_lower):
            return self.factual['grass_green']
        if 'water' in text_lower and 'wet' in text_lower:
            return self.factual['water_wet']
        if 'earth' in text_lower and ('round' in text_lower or 'flat' in text_lower or 'sphere' in text_lower):
            return self.factual['earth_round']
        
        # Yes/no questions about basic facts
        if text_lower.startswith(('is ', 'are ', 'does ', 'do ')):
            if 'sky blue' in text_lower:
                return "Yes, " + self.factual['sky_blue']
            if 'grass green' in text_lower:
                return "Yes, " + self.factual['grass_green']
            if 'water wet' in text_lower:
                return "Yes, " + self.factual['water_wet']
        
        return None


# Singleton instance
_knowledge_base = None

def get_knowledge_base() -> KnowledgeBase:
    """get_knowledge_base - Auto-documented by self-evolution."""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
    return _knowledge_base
