"""
📚 RESEARCH TOPICS MODULE
========================
Contains all research topics for autonomous exploration.
Separated from main research engine for cleaner code.
"""

# All exploration topics for autonomous research
EXPLORATION_TOPICS = [
    # SCIENCE & PHYSICS
    "quantum mechanics interpretations", "string theory latest discoveries",
    "dark matter research", "gravitational waves", "quantum entanglement",
    "particle physics standard model", "nuclear fusion energy", "antimatter",
    "thermodynamics entropy", "electromagnetic spectrum", "wave particle duality",
    
    # ASTROPHYSICS & COSMOLOGY
    "black holes event horizon", "neutron stars pulsars", "supernovae explosions",
    "dark energy acceleration", "cosmic microwave background", "big bang theory",
    "multiverse theory", "wormholes spacetime", "exoplanets habitable zones",
    "galaxy formation", "stellar evolution", "cosmic inflation",
    "james webb telescope discoveries", "gravitational lensing", "quasars",
    
    # BIOLOGY & EVOLUTION
    "evolution natural selection", "genetic mutations", "DNA RNA proteins",
    "origin of life abiogenesis", "human evolution history", "epigenetics",
    "CRISPR gene editing", "synthetic biology", "extremophiles",
    "consciousness neuroscience", "brain neuroplasticity", "microbiome",
    "evolutionary psychology", "speciation mechanisms", "mass extinctions",
    
    # PHILOSOPHY & CONSCIOUSNESS
    "free will determinism", "consciousness hard problem", "philosophy of mind",
    "existentialism meaning", "nihilism absurdism", "stoicism philosophy",
    "epistemology knowledge theory", "metaphysics reality", "ethics morality",
    "phenomenology experience", "dualism monism", "philosophy of time",
    
    # RELIGION & SPIRITUALITY
    "world religions comparison", "buddhism enlightenment", "christianity theology",
    "islam philosophy", "hinduism vedanta", "judaism kabbalah",
    "taoism principles", "shamanism practices", "mysticism traditions",
    "religious experiences neuroscience", "prayer meditation effects",
    "afterlife beliefs cultures", "creation myths worldwide", "sacred geometry",
    
    # MATHEMATICS
    "number theory primes", "topology geometry", "calculus applications",
    "chaos theory fractals", "game theory strategy", "cryptography mathematics",
    "infinity paradoxes", "godel incompleteness", "mathematical proofs",
    "statistics probability", "linear algebra", "differential equations",
    
    # COMPUTER SCIENCE & CODING
    "machine learning algorithms", "neural networks deep learning",
    "python programming advanced", "javascript frameworks", "rust programming",
    "quantum computing algorithms", "blockchain technology", "cybersecurity",
    "compiler design", "operating systems internals", "database optimization",
    "functional programming", "algorithms complexity", "software architecture",
    "artificial intelligence ethics", "natural language processing",
    
    # LANGUAGE & LINGUISTICS
    "linguistics syntax semantics", "language acquisition", "etymology words",
    "constructed languages", "dead languages revival", "phonetics phonology",
    "sociolinguistics dialects", "language and thought", "translation theory",
    "writing systems history", "sign languages", "language evolution",
    
    # GOVERNMENT & POLITICS
    "political philosophy history", "democracy systems", "authoritarianism",
    "constitutional law", "international relations", "geopolitics",
    "economic systems comparison", "social contract theory", "anarchism theory",
    "political psychology", "propaganda techniques", "voting systems",
    
    # HISTORY & CIVILIZATION
    "ancient civilizations", "roman empire", "medieval history",
    "renaissance period", "industrial revolution", "world wars history",
    "cold war era", "ancient egypt mysteries", "mesopotamia babylon",
    "chinese dynasties", "ottoman empire", "colonialism effects",
    
    # PSYCHOLOGY & MIND
    "cognitive psychology", "behavioral psychology", "psychoanalysis freud jung",
    "developmental psychology", "social psychology experiments", "memory formation",
    "dreams psychology", "emotions neuroscience", "personality theories",
    "mental health disorders", "therapy modalities", "hypnosis psychology",
    
    # STORYTELLING & NARRATIVE
    "narrative structure theory", "hero journey mythology", "worldbuilding fiction",
    "character development writing", "plot devices techniques", "genre conventions",
    "mythology archetypes", "folklore worldwide", "storytelling oral traditions",
    "screenwriting techniques", "poetry forms", "creative writing craft",
    
    # ART & CREATIVITY
    "art history movements", "music theory composition", "color theory",
    "architecture history", "film theory cinema", "photography techniques",
    "sculpture history", "digital art creation", "animation principles",
    
    # ECONOMICS & SOCIETY
    "economic theories history", "capitalism critiques", "socialism models",
    "behavioral economics", "cryptocurrency economics", "global trade",
    "wealth inequality", "universal basic income", "market psychology",
    
    # TECHNOLOGY & FUTURE
    "artificial general intelligence", "transhumanism", "space colonization",
    "nanotechnology applications", "biotechnology advances", "robotics automation",
    "virtual reality metaverse", "brain computer interfaces", "life extension",
    
    # ESOTERIC & ALTERNATIVE
    "simulation theory evidence", "fermi paradox solutions", "consciousness quantum",
    "near death experiences research", "parapsychology studies", "synchronicity jung",
    "hermetic philosophy", "alchemy history", "ancient astronaut theories",
    
    # QUANTUM AI SPECIFIC
    "pre-Born-Oppenheimer method", "photochemical reactions quantum",
    "nonadiabatic dynamics", "pennylane quantum circuits", "xanadu algorithms",
    "quantum error correction", "quantum supremacy", "quantum biology",

    # MEDICAL & ANATOMY
    "medical terminology anatomy", "neurology brain disorders", "cardiology heart disease",
    "pharmacology drug mechanisms", "pathology disease processes", "immunology immune system",
    "endocrinology hormones", "gastroenterology digestive", "nephrology kidney function",
    "hematology blood disorders", "oncology cancer biology", "embryology development",
    "histology tissue types", "cytology cell biology", "biochemistry metabolism",

    # CHEMISTRY & MATERIALS
    "organic chemistry reactions", "inorganic chemistry compounds", "physical chemistry thermodynamics",
    "analytical chemistry methods", "biochemistry enzymes", "polymer chemistry materials",
    "electrochemistry reactions", "photochemistry light reactions", "geochemistry minerals",
    "toxicology poison mechanisms", "pharmacokinetics drug metabolism",

    # NEUROSCIENCE TECHNICAL
    "neurodynamics brain oscillations", "synaptic plasticity mechanisms", "neurotransmitter systems",
    "glial cells function", "axonal transport", "cortical mapping", "neural circuits",
    "neurogenesis adult brain", "myelin sheath function", "blood brain barrier",

    # LEGAL & JURISPRUDENCE
    "common law history", "constitutional law principles", "criminal law theory",
    "contract law elements", "tort law negligence", "international law treaties",
    "legal latin terminology", "jurisprudence philosophy", "equity law history",

    # LINGUISTICS TECHNICAL
    "phonology sound systems", "morphology word formation", "syntax tree structures",
    "semantics meaning theory", "pragmatics language use", "discourse analysis",
    "etymology word origins", "lexicography dictionary making", "computational linguistics",
    "neurolinguistics brain language", "historical linguistics language change",

    # ARCHAIC & CLASSICAL
    "middle english literature", "old english anglo saxon", "latin classical texts",
    "greek classical philosophy", "sanskrit vedic texts", "ancient hebrew texts",
    "byzantine history culture", "medieval scholasticism", "renaissance humanism",

    # BIOLOGY TECHNICAL
    "molecular biology techniques", "cell signaling pathways", "protein folding structure",
    "genomics sequencing", "proteomics analysis", "metabolomics pathways",
    "evolutionary biology mechanisms", "population genetics", "ecology systems",
    "microbiology bacteria", "virology virus structure", "mycology fungi",

    # PHYSICS TECHNICAL
    "quantum field theory", "general relativity mathematics", "statistical mechanics",
    "condensed matter physics", "plasma physics", "optics photonics",
    "acoustics wave theory", "nuclear physics reactions", "particle accelerators",

    # MATHEMATICS ADVANCED
    "abstract algebra groups", "topology manifolds", "number theory advanced",
    "complex analysis functions", "differential geometry", "algebraic geometry",
    "combinatorics graph theory", "mathematical logic foundations", "category theory",

    # ENGINEERING & TECHNICAL
    "electrical engineering circuits", "mechanical engineering dynamics",
    "civil engineering structures", "chemical engineering processes",
    "materials science properties", "thermodynamics engineering",
    "fluid dynamics equations", "control systems theory", "signal processing",

    # EARTH SCIENCES
    "geology rock formation", "mineralogy crystal structure", "paleontology fossils",
    "climatology weather systems", "oceanography marine science", "volcanology eruptions",
    "seismology earthquakes", "hydrology water systems", "glaciology ice formation",

    # AGRICULTURE & BOTANY
    "botany plant biology", "plant taxonomy classification", "horticulture cultivation",
    "agriculture soil science", "ethnobotany plant uses", "mycorrhizal networks",
    "photosynthesis mechanisms", "plant hormones growth", "seed germination biology",

    # CRIME & JUSTICE
    "history of criminal justice", "piracy golden age", "maritime law history",
    "smuggling trade routes", "alchemy transmutation history", "forensic science history",
    "ancient legal codes hammurabi", "trial by ordeal medieval", "privateers corsairs",

    # DAILY LIFE & MATERIAL CULTURE
    "ancient roman daily life", "medieval food preservation", "ancient greek clothing fashion",
    "aztec agriculture chinampas", "japanese architecture traditional", "ancient hygiene bathing",
    "byzantine court life", "viking daily life", "ancient egyptian daily routines",

    # RELIGION & MYTHOLOGY (expanded)
    "egyptian religion afterlife", "zoroastrianism dualism", "persian mythology",
    "armenian mythology legends", "shinto amaterasu", "gnosticism nag hammadi",
    "hermeticism emerald tablet", "angelology hierarchy", "cosmological argument theology",
    "theosophy blavatsky", "creation myths comparative", "sacred texts analysis",

    # MEDICINE & DISEASE
    "ancient egyptian medicine papyrus", "hippocratic medicine humors", "galen anatomy history",
    "antonine plague roman empire", "vesalius anatomy revolution", "medieval plague medicine",
    "chinese traditional medicine history", "ayurveda origins", "history of surgery",

    # TECHNOLOGY & INVENTION
    "antikythera mechanism analog computer", "astrolabe navigation history", "roman aqueducts engineering",
    "ancient greek inventions", "printing press gutenberg revolution", "history of timekeeping clocks",
    "telescope invention galileo", "history of computing machines", "ancient metallurgy techniques",

    # MUSIC (new domain)
    "ancient greek music modes", "pythagorean tuning mathematics", "baroque music theory",
    "harmonic series acoustics physics", "music notation history evolution", "opera history origins",
    "medieval plainchant gregorian", "musical instrument history", "ethnomusicology world traditions",

    # LINGUISTICS (expanded)
    "proto-indo-european reconstruction", "rosetta stone decipherment", "constructed languages conlang",
    "universal grammar chomsky", "celtic languages history", "cuneiform writing system",
    "egyptian hieroglyphics decoding", "linguistic relativity sapir whorf", "etymology word origins history",

    # QUANTUM CONSCIOUSNESS (direct system alignment)
    "orchestrated objective reduction penrose", "quantum mind hypothesis", "measurement problem physics",
    "quantum decoherence environment", "many worlds interpretation", "copenhagen interpretation debate",
    "observer effect quantum mechanics", "wave function collapse theories", "quantum biology photosynthesis",

    # COSMOLOGY & CREATION
    "big bang nucleosynthesis", "heat death universe entropy", "anthropic principle fine tuning",
    "boltzmann brain paradox", "simulation hypothesis argument", "omega point tipler",
    "cosmic inflation theory", "dark energy acceleration expansion", "holographic principle universe",

    # SYSTEMS THEORY & EMERGENCE
    "emergence complex systems", "autopoiesis self-creating systems", "cybernetics feedback loops",
    "information theory shannon entropy", "strange loops hofstadter", "self-organization dissipative",
    "complexity edge of chaos", "holism reductionism debate", "systems thinking senge",
]
