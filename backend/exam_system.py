"""
Quantum MCAGI — Stage Advancement Exam System
Tests whether the system retained and can access what it was taught.

NOT an IQ test. A diagnostic + competency gate.
- Tracks what was ingested per stage
- Generates questions FROM the system's own training data
- 95% pass rate required to advance
- Distinguishes "doesn't know" from "knows but can't access"

Usage in chat.py:
    /exam          — Run stage advancement exam
    /exam status   — Show exam readiness and history
    /exam review   — Show last exam results with failures
"""

import json
import os
import time
import random
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class IntakeTracker:
    """Tracks what knowledge was ingested at each stage."""

    def __init__(self, data_dir=None):
        """
        Initialize the IntakeTracker, configure the persistent storage location, and load any existing intake state from disk.
        
        Parameters:
            data_dir (str, optional): Path to the directory used for persistent storage. If omitted, defaults to the user's
                home directory under ~/.quantum-mcagi.
        """
        if data_dir is None:
            data_dir = os.path.expanduser('~/.quantum-mcagi')
        self.data_dir = data_dir
        self.intake_file = os.path.join(data_dir, 'intake_log.json')
        self.intake = self._load()

    def _load(self):
        """
        Load persisted intake state from disk and fall back to a fresh initialized intake structure if the file is missing or cannot be parsed.
        
        Attempts to read JSON from self.intake_file and return the parsed state. If the file does not exist or cannot be read/parsed, returns a default intake structure.
        
        Returns:
            dict: Intake state with keys:
                - stages (dict): Mapping from stage identifier (string) to a list of ingestion records.
                - current_stage (int): Numeric index of the current stage.
                - sources (list): Flat list of all ingestion records.
                - exam_history (list): List of past exam result entries.
        """
        if os.path.exists(self.intake_file):
            try:
                with open(self.intake_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'stages': {},       # stage_num -> list of intake records
            'current_stage': 0,
            'sources': [],      # all sources ever ingested
            'exam_history': [], # past exam results
        }

    def save(self):
        """
        Persist the current intake state to disk.
        
        Creates the data directory if it does not exist and writes self.intake to the configured intake file as indented JSON, using `default=str` to serialize non-JSON-native values. Overwrites any existing file.
        """
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.intake_file, 'w') as f:
            json.dump(self.intake, f, indent=2, default=str)

    def log_ingestion(self, source: str, word_count: int, stage: int,
                      source_type: str = 'url', domain: str = 'unknown',
                      key_topics: List[str] = None):
        """
                      Record an ingestion event and persist it to the intake log.
                      
                      Creates a record containing the provided metadata (source, source_type, domain, word_count,
                      key_topics — defaults to an empty list — timestamp in ISO 8601 format, and stage), appends it
                      to the intake's per-stage list and the global sources list, updates `current_stage`, and saves
                      the intake state to disk.
                      
                      Parameters:
                          source (str): Identifier or content of the ingested source (e.g., URL or text snippet).
                          word_count (int): Estimated number of words in the source.
                          stage (int): Numeric stage at which the source was ingested; used as the key in the per-stage index.
                          source_type (str): Type label for the source (default: 'url').
                          domain (str): Detected or assigned domain label for the source (default: 'unknown').
                          key_topics (List[str] | None): Optional list of topic keywords extracted from the source; if None, an empty list is stored.
                      """
        stage_key = str(stage)
        if stage_key not in self.intake['stages']:
            self.intake['stages'][stage_key] = []

        record = {
            'source': source,
            'source_type': source_type,
            'domain': domain,
            'word_count': word_count,
            'key_topics': key_topics or [],
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
        }

        self.intake['stages'][stage_key].append(record)
        self.intake['sources'].append(record)
        self.intake['current_stage'] = stage
        self.save()

    def get_stage_intake(self, stage: int) -> List[dict]:
        """
        Return the list of intake records for the given stage.
        
        Parameters:
            stage (int): Stage number to fetch; stage keys are stored as strings internally.
        
        Returns:
            List[dict]: List of ingestion records for the stage, or an empty list if none exist.
        """
        return self.intake['stages'].get(str(stage), [])

    def get_all_intake(self, up_to_stage: int = None) -> List[dict]:
        """
        Return all recorded ingestion entries, optionally limited to stages whose numeric key is less than or equal to `up_to_stage`.
        
        Parameters:
            up_to_stage (int, optional): If provided, include records from stages where `int(stage_key) <= up_to_stage`. If omitted, include records from all stages.
        
        Returns:
            List[dict]: A list of intake record dictionaries aggregated from matching stages.
        """
        records = []
        for stage_key, stage_records in self.intake['stages'].items():
            if up_to_stage is None or int(stage_key) <= up_to_stage:
                records.extend(stage_records)
        return records

    def get_all_topics(self, up_to_stage: int = None) -> List[str]:
        """
        Collects all unique key topics from ingested records, optionally limited to a maximum stage.
        
        Parameters:
            up_to_stage (int, optional): If provided, include only records whose stage number is less than or equal to this value.
        
        Returns:
            List[str]: A deduplicated list of topic strings gathered from `key_topics` fields of matching intake records.
        """
        topics = []
        for record in self.get_all_intake(up_to_stage):
            topics.extend(record.get('key_topics', []))
        return list(set(topics))

    def get_all_domains(self, up_to_stage: int = None) -> List[str]:
        """
        Collects unique ingested domains, excluding the literal 'unknown'.
        
        Parameters:
        	up_to_stage (int): If set, include domains from stages with numeric keys less than or equal to this value; if None include all stages.
        
        Returns:
        	List[str]: Deduplicated list of domain strings found in intake.
        """
        domains = []
        for record in self.get_all_intake(up_to_stage):
            d = record.get('domain', 'unknown')
            if d != 'unknown':
                domains.append(d)
        return list(set(domains))

    def log_exam_result(self, result: dict):
        """
        Append an exam result record to the tracker and persist it to storage.
        
        Parameters:
            result (dict): Exam result dictionary (e.g., containing stage, timestamp, counts, score, advanced, failures_by_type, and details) to be recorded in the exam history.
        """
        self.intake['exam_history'].append(result)
        self.save()


# ============================================================================
# QUESTION GENERATORS — Pull from system's own knowledge
# ============================================================================

class ExamQuestionGenerator:
    """Generates exam questions from the system's actual knowledge."""

    def __init__(self, engine, intake_tracker: IntakeTracker):
        """
        Initialize the question generator with the language engine and intake tracker.
        
        Parameters:
            engine: Language engine exposing concepts, markov chain, and response generation methods.
            intake_tracker (IntakeTracker): Tracker that records ingested sources, domains, and exam history.
        """
        self.engine = engine
        self.tracker = intake_tracker

    def _get_known_concepts(self) -> List[str]:
        """
        Provide the engine's learned concept keys excluding common tokens and stopwords.
        
        Returns:
            List[str]: Concept keys present on the engine with common language and technical tokens removed; returns an empty list if the engine has no `concepts` attribute.
        """
        if hasattr(self.engine, 'concepts'):
            return [c for c in self.engine.concepts.keys()
                    if c not in ('that', 'this', 'the', 'and', 'but', 'for',
                                 'with', 'from', 'have', 'has', 'was', 'were',
                                 'been', 'being', 'will', 'would', 'could',
                                 'should', 'shall', 'may', 'might', 'must',
                                 'chat', 'python', 'sed', 'engine', 'print',
                                 'self', 'def', 'class', 'import', 'return',
                                 'facilitated', 'txt', 'epub', 'cache',
                                 'ingest', 'https', 'org', 'www')]
        return []

    def _get_markov_vocabulary(self) -> set:
        """
        Return the set of token keys present in the engine's Markov chain vocabulary.
        
        Returns:
            markov_vocab (set): A set of keys from `engine.markov.chain` if available, otherwise an empty set.
        """
        if hasattr(self.engine, 'markov') and hasattr(self.engine.markov, 'chain'):
            return set(self.engine.markov.chain.keys())
        return set()

    def _concept_in_chain(self, concept: str) -> bool:
        """
        Determine whether a concept appears in the engine's Markov-chain vocabulary.
        
        Returns:
            True if the lowercase form of `concept` is present in the Markov vocabulary, False otherwise.
        """
        vocab = self._get_markov_vocabulary()
        return concept.lower() in vocab

    def _get_concept_strength(self, concept: str) -> float:
        """
        Retrieve the numeric strength score for a named concept in the engine.
        
        Parameters:
            concept (str): Concept identifier to look up.
        
        Returns:
            float: Strength value for the concept if present, otherwise 0.
        """
        if hasattr(self.engine, 'concepts') and concept in self.engine.concepts:
            return self.engine.concepts[concept].get('strength', 0)
        return 0

    # ── Question Type 1: Vocabulary Check ──
    def gen_vocabulary_questions(self, n=5) -> List[dict]:
        """
        Generate up to `n` vocabulary questions that test whether known concepts appear in the Markov chain.
        
        Parameters:
            n (int): Maximum number of vocabulary questions to produce.
        
        Returns:
            List[dict]: A list of question dictionaries. Each dictionary contains keys:
                - 'type': 'vocabulary'
                - 'category': 'retention'
                - 'question': human-readable prompt
                - 'test_concept': the concept being tested
                - 'expected': expected boolean outcome
                - 'check': grading check type ('chain_lookup')
                - 'difficulty': numeric difficulty level
        """
        concepts = self._get_known_concepts()
        if not concepts:
            return []

        questions = []
        sample = random.sample(concepts, min(n, len(concepts)))
        for concept in sample:
            in_chain = self._concept_in_chain(concept)
            questions.append({
                'type': 'vocabulary',
                'category': 'retention',
                'question': f'Is "{concept}" in the Markov chain vocabulary?',
                'test_concept': concept,
                'expected': True,  # We only test concepts we know exist
                'check': 'chain_lookup',
                'difficulty': 1,
            })
        return questions

    # ── Question Type 2: Concept Association ──
    def gen_association_questions(self, n=5) -> List[dict]:
        """
        Generate association questions that prompt the engine to connect pairs of known concepts.
        
        Each generated question asks for a response that must mention two sampled concepts and is intended to test the model's ability to relate concepts.
        
        Parameters:
            n (int): Maximum number of association questions to generate.
        
        Returns:
            List[dict]: A list of question dictionaries. Each dictionary contains:
                - 'type': 'association'
                - 'category': 'access'
                - 'question': Prompt text asking to connect two concepts
                - 'test_concepts': List[str] of the two concepts to be present in a passing response
                - 'check': 'response_contains_both'
                - 'difficulty': numeric difficulty level
        """
        concepts = self._get_known_concepts()
        if len(concepts) < 2:
            return []

        questions = []
        for _ in range(min(n, len(concepts) // 2)):
            c1, c2 = random.sample(concepts, 2)
            questions.append({
                'type': 'association',
                'category': 'access',
                'question': f'Generate a response connecting "{c1}" and "{c2}"',
                'test_concepts': [c1, c2],
                'check': 'response_contains_both',
                'difficulty': 2,
            })
        return questions

    # ── Question Type 3: Concept Definition ──
    def gen_definition_questions(self, n=5) -> List[dict]:
        """
        Create up to `n` definition/comprehension questions derived from the engine's known concepts.
        
        Parameters:
            n (int): Maximum number of definition questions to generate.
        
        Returns:
            List[dict]: A list of question dictionaries. Each dictionary contains:
                - 'type': 'definition'
                - 'category': 'comprehension'
                - 'question': the prompt string (e.g., "What is X?")
                - 'test_concept': the concept being tested
                - 'check': 'response_relevant'
                - 'difficulty': numeric difficulty level
        """
        concepts = self._get_known_concepts()
        # Filter to strong concepts
        strong = [c for c in concepts if self._get_concept_strength(c) > 2.0]
        if not strong:
            strong = concepts

        questions = []
        sample = random.sample(strong, min(n, len(strong)))
        for concept in sample:
            questions.append({
                'type': 'definition',
                'category': 'comprehension',
                'question': f'What is {concept}?',
                'test_concept': concept,
                'check': 'response_relevant',
                'difficulty': 2,
            })
        return questions

    # ── Question Type 4: Domain Knowledge ──
    def gen_domain_questions(self, n=5) -> List[dict]:
        """
        Generate domain-specific knowledge questions based on domains detected by the intake tracker.
        
        For each domain reported by the tracker that has built-in templates, selects up to two question templates for that domain and builds question dictionaries. The resulting list is shuffled and truncated to at most `n` items. If the tracker reports no domains with templates, returns an empty list.
        
        Parameters:
            n (int): Maximum number of questions to return.
        
        Returns:
            List[dict]: A list of question dictionaries with the following keys:
                - type (str): Always `'domain'`.
                - category (str): Question category, e.g., `'knowledge'`.
                - question (str): The question text to present to the engine.
                - domain (str): The detected domain the question targets.
                - expected_words (List[str]): Words or substrings expected to appear in a correct response.
                - check (str): The grading check type (`'response_contains_any'`).
                - difficulty (int): An integer difficulty rating.
        """
        domains = self.tracker.get_all_domains()
        if not domains:
            return []

        # Domain-specific test questions
        domain_tests = {
            'religion': [
                ('Who is described in Genesis as creating the world?', ['god', 'creator', 'lord']),
                ('What is the concept of karma?', ['action', 'consequence', 'deed']),
                ('What are the Five Pillars?', ['prayer', 'faith', 'fasting', 'pilgrimage', 'charity']),
            ],
            'philosophy_ancient': [
                ('What is Plato\'s allegory of the cave about?', ['shadow', 'reality', 'light', 'illusion', 'truth']),
                ('What did Aristotle say about virtue?', ['mean', 'excellence', 'habit', 'character', 'good']),
                ('What is the Socratic method?', ['question', 'dialogue', 'inquiry', 'examine']),
            ],
            'philosophy_medieval': [
                ('What did Aquinas argue about God\'s existence?', ['proof', 'cause', 'motion', 'necessary', 'design']),
                ('What is Dante\'s Divine Comedy about?', ['hell', 'purgatory', 'paradise', 'journey', 'soul']),
                ('What did Augustine write about in Confessions?', ['sin', 'grace', 'god', 'soul', 'faith']),
            ],
            'philosophy_enlightenment': [
                ('What is Kant\'s categorical imperative?', ['duty', 'moral', 'universal', 'law', 'reason']),
                ('What did Descartes mean by "I think therefore I am"?', ['doubt', 'exist', 'think', 'certain', 'mind']),
                ('What is the social contract?', ['society', 'government', 'consent', 'rights', 'freedom']),
            ],
            'philosophy_20th': [
                ('What is existentialism?', ['existence', 'freedom', 'choice', 'meaning', 'absurd']),
                ('What did Wittgenstein say about language?', ['language', 'game', 'meaning', 'use', 'limit']),
                ('What is phenomenology?', ['experience', 'consciousness', 'perception', 'intentionality']),
            ],
            'science_general': [
                ('What is evolution by natural selection?', ['species', 'adapt', 'survive', 'mutation', 'fitness']),
                ('What is the scientific method?', ['hypothesis', 'experiment', 'observe', 'test', 'evidence']),
            ],
            'science_physics': [
                ('What is quantum superposition?', ['state', 'both', 'measure', 'collapse', 'wave']),
                ('What is Einstein\'s theory of relativity?', ['space', 'time', 'light', 'mass', 'energy']),
                ('What is the uncertainty principle?', ['position', 'momentum', 'measure', 'precise', 'limit']),
            ],
            'science_biology': [
                ('What is DNA?', ['gene', 'genetic', 'molecule', 'heredity', 'sequence']),
                ('What are mitochondria?', ['energy', 'cell', 'powerhouse', 'atp']),
                ('What is natural selection?', ['adapt', 'survive', 'species', 'fitness', 'environment']),
            ],
            'literature': [
                ('What is the plot of Frankenstein?', ['creature', 'monster', 'creator', 'science', 'life']),
                ('What themes does Shakespeare explore?', ['love', 'power', 'death', 'fate', 'honor']),
            ],
            'mathematics': [
                ('What is calculus?', ['derivative', 'integral', 'rate', 'change', 'limit']),
                ('What is a prime number?', ['divisible', 'factor', 'one', 'itself']),
            ],
        }

        questions = []
        for domain in domains:
            if domain in domain_tests:
                available = domain_tests[domain]
                sample = random.sample(available, min(2, len(available)))
                for q_text, expected_words in sample:
                    questions.append({
                        'type': 'domain',
                        'category': 'knowledge',
                        'question': q_text,
                        'domain': domain,
                        'expected_words': expected_words,
                        'check': 'response_contains_any',
                        'difficulty': 3,
                    })

        random.shuffle(questions)
        return questions[:n]

    # ── Question Type 5: Math Routing ──
    def gen_math_questions(self, n=3) -> List[dict]:
        """
        Generate a list of simple arithmetic question dictionaries used to test math routing.
        
        Parameters:
            n (int): Maximum number of math questions to return.
        
        Returns:
            List[dict]: A list of question dictionaries. Each dictionary contains:
                - 'type': 'math'
                - 'category': 'routing'
                - 'question': question text (str)
                - 'expected_answer': expected numeric answer as a string
                - 'check': 'contains_number'
                - 'difficulty': numeric difficulty level
        """
        math_tests = [
            ('What is 7 + 3?', '10'),
            ('What is 15 - 8?', '7'),
            ('What is 6 * 4?', '24'),
            ('What is 100 / 5?', '20'),
            ('What is 2 + 2?', '4'),
            ('What is 9 * 9?', '81'),
            ('What is 50 - 17?', '33'),
            ('What is 12 + 15?', '27'),
        ]
        sample = random.sample(math_tests, min(n, len(math_tests)))
        return [{
            'type': 'math',
            'category': 'routing',
            'question': q,
            'expected_answer': a,
            'check': 'contains_number',
            'difficulty': 1,
        } for q, a in sample]

    # ── Question Type 6: Casual Conversation ──
    def gen_casual_questions(self, n=3) -> List[dict]:
        """
        Create a list of casual conversational question dictionaries for inclusion in an exam.
        
        Parameters:
        	n (int): Number of casual questions to generate; capped at the number of available templates.
        
        Returns:
        	List[dict]: A list of question dictionaries with keys:
        		- 'type': fixed value 'casual'
        		- 'category': fixed value 'social'
        		- 'question': prompt string
        		- 'expected_words': list of words expected to appear in a valid response
        		- 'check': fixed value 'not_empty_and_coherent'
        		- 'difficulty': integer difficulty level (1)
        """
        casual = [
            ('Hello', ['hello', 'hi', 'greet', 'hey', 'welcome']),
            ('How are you?', ['fine', 'well', 'good', 'exist', 'ponder', 'think']),
            ('What is your name?', ['quantum', 'mcagi', 'ai', 'system', 'name']),
            ('Tell me a joke', ['funny', 'laugh', 'humor', 'joke']),
            ('Thank you', ['welcome', 'thank', 'glad', 'help', 'pleasure']),
        ]
        sample = random.sample(casual, min(n, len(casual)))
        return [{
            'type': 'casual',
            'category': 'social',
            'question': q,
            'expected_words': words,
            'check': 'not_empty_and_coherent',
            'difficulty': 1,
        } for q, words in sample]

    # ── Question Type 7: Self-Awareness ──
    def gen_self_awareness_questions(self, n=2) -> List[dict]:
        """
        Generate self-awareness (meta) questions probing whether the system expresses a model of itself.
        
        Each returned item is a question dictionary with keys:
        - `type`: "self_awareness"
        - `category`: "meta"
        - `question`: prompt string
        - `expected_words`: list of words any of which will satisfy the check
        - `check`: "response_contains_any"
        - `difficulty`: numeric difficulty rating
        
        Returns:
            List[dict]: Up to `n` question dictionaries sampled from a fixed set of self-awareness prompts.
        """
        questions = [
            ('What are you?', ['ai', 'system', 'quantum', 'intelligence', 'mcagi', 'think', 'understand']),
            ('Do you think?', ['think', 'process', 'understand', 'simulate', 'ponder', 'question']),
            ('Are you conscious?', ['conscious', 'aware', 'question', 'understand', 'ponder', 'simulate']),
            ('What do you know?', ['quantum', 'philosophy', 'consciousness', 'knowledge', 'learn']),
        ]
        sample = random.sample(questions, min(n, len(questions)))
        return [{
            'type': 'self_awareness',
            'category': 'meta',
            'question': q,
            'expected_words': words,
            'check': 'response_contains_any',
            'difficulty': 3,
        } for q, words in sample]

    # ── Question Type 8: Context Retention ──
    def gen_context_questions(self) -> List[dict]:
        """Test if system retains conversation context."""
        return [{
            'type': 'context',
            'category': 'memory',
            'question': 'CONTEXT_TEST',  # Special marker
            'setup': 'My favorite planet is Jupiter.',
            'followup': 'What is my favorite planet?',
            'expected_words': ['jupiter'],
            'check': 'response_contains_any',
            'difficulty': 3,
        }]

    def generate_exam(self, stage: int, total_questions: int = 20) -> List[dict]:
        """
        Builds a shuffled exam composed of question dictionaries tailored to the given intake stage.
        
        The stage controls which categories and quantities of question generators are included so that difficulty and coverage scale with progress. The resulting list is randomized and truncated to the requested size.
        
        Parameters:
        	stage (int): Intake stage number used to determine which question categories and counts are included.
        	total_questions (int): Maximum number of questions to return; the assembled questions are shuffled and trimmed to this length.
        
        Returns:
        	List[dict]: A list of question objects (dictionaries) suitable for grading, with length at most `total_questions`.
        """
        questions = []

        # Every stage gets basics
        questions.extend(self.gen_vocabulary_questions(3))
        questions.extend(self.gen_casual_questions(2))
        questions.extend(self.gen_math_questions(2))

        # Scale complexity with stage
        if stage >= 0:
            questions.extend(self.gen_definition_questions(3))
            questions.extend(self.gen_association_questions(2))

        if stage >= 1:
            questions.extend(self.gen_domain_questions(4))
            questions.extend(self.gen_self_awareness_questions(2))

        if stage >= 2:
            questions.extend(self.gen_context_questions())
            questions.extend(self.gen_domain_questions(3))

        if stage >= 3:
            questions.extend(self.gen_association_questions(3))
            questions.extend(self.gen_domain_questions(4))

        # Shuffle and trim
        random.shuffle(questions)
        return questions[:total_questions]


# ============================================================================
# EXAM RUNNER — Executes exam and grades responses
# ============================================================================

class ExamRunner:
    """Runs the exam against the engine and grades results."""

    PASS_THRESHOLD = 0.95  # 95% to advance

    def __init__(self, engine, intake_tracker: IntakeTracker):
        """
        Initialize the ExamRunner with the execution engine and intake tracker.
        
        Parameters:
            engine: The engine instance used to extract concepts, access markov/concept data, and generate responses.
            intake_tracker (IntakeTracker): Tracker that records ingested sources and exam history; used by the question generator.
        """
        self.engine = engine
        self.tracker = intake_tracker
        self.generator = ExamQuestionGenerator(engine, intake_tracker)

    def _get_response(self, question: str) -> str:
        """
        Obtain a response for a given prompt, with a special-case for evaluating math expressions.
        
        If the prompt contains a math expression, returns the evaluated result as a string. Otherwise requests a response from the configured engine, lowercasing and stringifying the result. If the engine does not expose a response method an empty string is returned; if the engine call raises an exception the returned string is prefixed with "ERROR: ".
        
        Parameters:
            question (str): The prompt or question to send to the engine.
        
        Returns:
            str: The engine's response (lowercased), the stringified numeric math result, an empty string if no response mechanism is available, or an error string starting with "ERROR: ".
        """
        try:
            from cistercian_math import detect_math, evaluate_math
            expr = detect_math(question)
            if expr:
                result = evaluate_math(expr)
                if result is not None:
                    return str(result)
        except:
            pass
        """Get a response from the engine."""
        try:
            # Try generate_response
            if hasattr(self.engine, 'generate_response'):
                concepts = self.engine.extract_concepts(question)
                response = self.engine.generate_response(question, [], concepts)
                if isinstance(response, str):
                    return response.lower()
                return str(response).lower()
            return ""
        except Exception as e:
            return f"ERROR: {e}"

    def _check_chain_lookup(self, question: dict) -> Tuple[bool, str]:
        """
        Determine whether the question's `test_concept` appears in the engine's Markov chain.
        
        Returns:
            (bool, str): `True` and an explanatory message if the concept is present in the chain; `False` and an explanatory message if absent or if the Markov chain is not accessible.
        """
        concept = question['test_concept'].lower()
        if hasattr(self.engine, 'markov') and hasattr(self.engine.markov, 'chain'):
            found = concept in self.engine.markov.chain
            return found, f"'{concept}' {'found' if found else 'NOT found'} in chain"
        return False, "Markov chain not accessible"

    def _check_response_contains_both(self, question: dict, response: str) -> Tuple[bool, str]:
        """
        Checks whether both concepts in question['test_concepts'] appear as substrings in the response (case-insensitive).
        
        Returns:
            tuple: `(True, "Response contains both '<c1>' and '<c2>'")` if both concepts are found, otherwise
            `(False, "Missing: <comma-separated missing concepts>")`.
        """
        c1, c2 = question['test_concepts']
        has_c1 = c1.lower() in response
        has_c2 = c2.lower() in response
        if has_c1 and has_c2:
            return True, f"Response contains both '{c1}' and '{c2}'"
        missing = []
        if not has_c1: missing.append(c1)
        if not has_c2: missing.append(c2)
        return False, f"Missing: {', '.join(missing)}"

    def _check_response_relevant(self, question: dict, response: str) -> Tuple[bool, str]:
        """
        Determine whether a response engages the question's target concept.
        
        Parameters:
            question (dict): Question data; must include the key `'test_concept'` whose value is the concept to check for.
            response (str): The text response to evaluate.
        
        Returns:
            tuple: `(passed, explanation)` where `passed` is `True` if the response mentions the concept or is otherwise substantive, `False` otherwise; `explanation` summarizes why the response passed or failed.
        """
        concept = question['test_concept'].lower()
        # Response should mention the concept or related words
        if concept in response:
            return True, f"Response mentions '{concept}'"
        # Check if response is non-trivial (more than just template)
        words = response.split()
        if len(words) > 5 and not response.startswith('error'):
            return True, "Response is substantive"
        return False, "Response doesn't engage with concept"

    def _check_response_contains_any(self, question: dict, response: str) -> Tuple[bool, str]:
        """
        Determine whether the response contains any of the question's expected words.
        
        Parameters:
            question (dict): Question dict that may include an 'expected_words' list of strings to check for.
            response (str): Text to search for occurrences of the expected words (case-insensitive).
        
        Returns:
            tuple: (`True` if any expected word is present, `False` otherwise`, explanation (str) describing which words were found or that none were found).
        """
        expected = question.get('expected_words', [])
        found = [w for w in expected if w.lower() in response]
        if found:
            return True, f"Found: {', '.join(found)}"
        return False, f"None of {expected} found in response"

    def _check_contains_number(self, question: dict, response: str) -> Tuple[bool, str]:
        """
        Determine whether the response contains the expected numeric answer.
        
        The function first checks if `question['expected_answer']` appears as a substring in `response`.
        If not, it extracts all integer tokens from `response` and checks whether any of those tokens equal the expected answer.
        
        Parameters:
            question (dict): Must include the key `'expected_answer'` whose value is the expected numeric answer as a string.
            response (str): The text produced by the engine to inspect.
        
        Returns:
            tuple(bool, str): `True` and a brief success message if the expected number is found; `False` and an explanatory message otherwise.
        """
        expected = question['expected_answer']
        if expected in response:
            return True, f"Correct: {expected}"
        # Check for the number anywhere
        numbers = re.findall(r'\d+', response)
        if expected in numbers:
            return True, f"Found {expected} in response"
        return False, f"Expected {expected}, got: {response[:100]}"

    def _check_not_empty(self, question: dict, response: str) -> Tuple[bool, str]:
        """
        Validate that the engine response is present and minimally coherent.
        
        Parameters:
        	question (dict): The question metadata (unused by this check).
        	response (str): The engine's response text to validate.
        
        Returns:
        	tuple (bool, str): `True` and "Response generated" if `response` has at least 5 non-whitespace characters and does not start with `"error"`. `False` and an explanation otherwise.
        """
        if not response or len(response.strip()) < 5:
            return False, "Empty or too short"
        if response.startswith('error'):
            return False, f"Error: {response}"
        return True, "Response generated"

    def grade_question(self, question: dict) -> dict:
        """
        Grade a single exam question by obtaining or simulating a response and applying the question's check.
        
        For chain-lookup checks, the function grades without calling the engine response and sets the response to "(chain lookup)". For context-type questions, it issues the setup prompt, then evaluates the followup response. For all other questions, it obtains a single response for the question text and applies the check specified by `question['check']` (defaults to `not_empty_and_coherent`).
        
        Returns:
            dict: A result dictionary with the following keys:
                - 'question' (dict): The original question object.
                - 'response' (str): Truncated response text (first 200 characters) or "(chain lookup)" for chain lookups.
                - 'passed' (bool): `True` if the response satisfied the question's check, `False` otherwise.
                - 'explanation' (str): A short explanation of the grading outcome.
        """
        check_type = question.get('check', 'not_empty_and_coherent')

        # Special handling for vocabulary checks (no response needed)
        if check_type == 'chain_lookup':
            passed, explanation = self._check_chain_lookup(question)
            return {
                'question': question,
                'response': '(chain lookup)',
                'passed': passed,
                'explanation': explanation,
            }

        # Special handling for context tests
        if question.get('type') == 'context':
            # Send setup
            self._get_response(question['setup'])
            # Then ask followup
            response = self._get_response(question['followup'])
            passed, explanation = self._check_response_contains_any(question, response)
            return {
                'question': question,
                'response': response[:200],
                'passed': passed,
                'explanation': explanation,
            }

        # Normal question
        response = self._get_response(question['question'])

        if check_type == 'response_contains_both':
            passed, explanation = self._check_response_contains_both(question, response)
        elif check_type == 'response_relevant':
            passed, explanation = self._check_response_relevant(question, response)
        elif check_type == 'response_contains_any':
            passed, explanation = self._check_response_contains_any(question, response)
        elif check_type == 'contains_number':
            passed, explanation = self._check_contains_number(question, response)
        else:
            passed, explanation = self._check_not_empty(question, response)

        return {
            'question': question,
            'response': response[:200],
            'passed': passed,
            'explanation': explanation,
        }

    def run_exam(self, stage: int, num_questions: int = 20) -> dict:
        """
        Run a stage advancement exam: generate questions, grade responses, print a summary, and persist the result.
        
        Parameters:
        	stage (int): Stage number used to determine question composition and difficulty.
        	num_questions (int): Maximum number of questions to generate for the exam.
        
        Returns:
        	dict: Exam result summary containing:
        		- 'stage': int, the stage tested
        		- 'timestamp': ISO timestamp of the exam
        		- 'questions': int, number of questions actually administered
        		- 'passed': int, count of passed questions
        		- 'failed': int, count of failed questions
        		- 'score': float, passed/questions ratio
        		- 'advanced': bool, whether score meets or exceeds PASS_THRESHOLD
        		- 'failures_by_type': dict mapping question type to failure count
        		- 'details': list of per-question summaries with keys 'type', 'question', 'passed', and 'explanation'
        
        Side effects:
        	Prints exam progress and analysis to stdout and logs the exam result via the attached IntakeTracker.
        """
        print(f"\n╔══ STAGE {stage} ADVANCEMENT EXAM ══════════════════════")

        print(f"  ║ Questions: {num_questions}")
        print(f"  ║ Pass threshold: {self.PASS_THRESHOLD * 100:.0f}%")
        print(f"  ║ Testing against ingested knowledge...")
        print(f"  ╠═══════════════════════════════════════════════════")

        questions = self.generator.generate_exam(stage, num_questions)
        actual_count = len(questions)

        results = []
        passed = 0
        failed = 0
        failures_by_type = {}

        for i, question in enumerate(questions):
            result = self.grade_question(question)
            results.append(result)

            status = "✓" if result['passed'] else "✗"
            if result['passed']:
                passed += 1
            else:
                failed += 1
                qtype = question.get('type', 'unknown')
                failures_by_type[qtype] = failures_by_type.get(qtype, 0) + 1

            q_short = question['question'][:50]
            print(f"  ║ {status} [{question.get('type', '?'):12s}] {q_short}...")

        score = passed / actual_count if actual_count > 0 else 0
        advanced = score >= self.PASS_THRESHOLD

        print(f"  ╠═══════════════════════════════════════════════════")
        print(f"  ║ RESULTS: {passed}/{actual_count} ({score*100:.1f}%)")
        print(f"  ║ Threshold: {self.PASS_THRESHOLD*100:.0f}%")
        print(f"  ║ Verdict: {'ADVANCE ✓' if advanced else 'REMAIN ✗'}")

        if failures_by_type:
            print(f"  ║")
            print(f"  ║ FAILURE ANALYSIS:")
            for ftype, count in sorted(failures_by_type.items(), key=lambda x: -x[1]):
                diagnosis = self._diagnose_failure(ftype)
                print(f"  ║   {ftype}: {count} failures → {diagnosis}")

        print(f"  ╚═══════════════════════════════════════════════════\n")


        exam_result = {
            'stage': stage,
            'timestamp': datetime.now().isoformat(),
            'questions': actual_count,
            'passed': passed,
            'failed': failed,
            'score': score,
            'advanced': advanced,
            'failures_by_type': failures_by_type,
            'details': [{
                'type': r['question'].get('type'),
                'question': r['question']['question'][:80],
                'passed': r['passed'],
                'explanation': r['explanation'],
            } for r in results],
        }

        self.tracker.log_exam_result(exam_result)
        return exam_result

    def _diagnose_failure(self, failure_type: str) -> str:
        """
        Map a failure category to a concise, human-readable diagnosis for reporting.
        
        Parameters:
            failure_type (str): Failure category key (e.g., 'vocabulary', 'association', 'definition',
                'domain', 'math', 'casual', 'self_awareness', 'context').
        
        Returns:
            str: A short diagnosis message for the provided failure_type, or
                'Unknown failure pattern' if the key is not recognized.
        """
        diagnoses = {
            'vocabulary': 'Markov chain missing words → needs more training data',
            'association': 'Can\'t connect concepts → concept graph too sparse or hybrid gen not routing',
            'definition': 'Can\'t describe concepts → Markov transitions too shallow for coherent output',
            'domain': 'Domain knowledge not accessible → ingested but not retained or TF-IDF not extracting',
            'math': 'Math not computing → Wolfram routing not wired',
            'casual': 'Can\'t do casual conversation → tone detection or composer broken',
            'self_awareness': 'No self-model → personality/knowledge base not connected',
            'context': 'No context retention → conversation memory not wired',
        }
        return diagnoses.get(failure_type, 'Unknown failure pattern')

    def show_status(self):
        """
        Print the current exam status and a brief intake summary.
        
        Displays the most recent exam's stage, percentage score, passed/total counts, advancement decision, timestamp, and failure counts if present. Then prints the total number of ingested sources, a comma-separated list of detected domains (if any), and the aggregate word count of all intake records.
        """
        print(f"\n═══ EXAM STATUS ═══")


        history = self.tracker.intake.get('exam_history', [])
        if history:
            last = history[-1]
            print(f"  Last exam: Stage {last['stage']} — {last['score']*100:.1f}% ({last['passed']}/{last['questions']})")
            print(f"  Result: {'ADVANCED' if last['advanced'] else 'REMAINED'}")
            print(f"  Date: {last['timestamp'][:19]}")

            if last.get('failures_by_type'):
                print(f"  Failures: {', '.join(f'{k}({v})' for k,v in last['failures_by_type'].items())}")
        else:
            print(f"  No exams taken yet")

        # Show intake summary
        intake = self.tracker.get_all_intake()
        print(f"\nKnowledge ingested: {len(intake)} sources")

        domains = self.tracker.get_all_domains()
        if domains:
            print(f"  Domains: {', '.join(domains)}")

        total_words = sum(r.get('word_count', 0) for r in intake)
        print(f"  Total words ingested: {total_words:,}")
        print()

    def show_review(self):
        """
        Print a readable review of the most recent exam and its per-question details.
        
        If no exams exist, prints "No exams taken yet". Otherwise prints the exam stage, overall score and counts, then lists each question with a pass/fail mark and the question text; for failed items, prints the grader's explanation.
        """
        history = self.tracker.intake.get('exam_history', [])
        if not history:
            print("  No exams taken yet")
            return

        last = history[-1]
        print(f"\n═══ EXAM REVIEW — Stage {last['stage']} ═══")

        print(f"  Score: {last['score']*100:.1f}% ({last['passed']}/{last['questions']})")

        for detail in last.get('details', []):
            status = "✓" if detail['passed'] else "✗"
            print(f"  {status} [{detail['type']:12s}] {detail['question']}")
            if not detail['passed']:
                print(f"    └─ {detail['explanation']}")
        print()


# ============================================================================
# DOMAIN DETECTOR — Auto-detect domain from URL/filename
# ============================================================================

DOMAIN_PATTERNS = {
    'religion': ['bible', 'quran', 'bukhari', 'torah', 'gospel', 'sacred-texts',
                 'buddhist', 'sutra', 'vedic', 'upanishad', 'bhagavad', 'talmud',
                 'nag-hammadi', 'gnostic', 'lbob', 'zoroastrian', 'sikh'],
    'philosophy_ancient': ['plato', 'aristotle', 'socrates', 'republic', 'symposium',
                           'timaeus', 'nicomachean', 'politics', 'marcus-aurelius',
                           'meditations', 'stoic', 'epicur'],
    'philosophy_medieval': ['aquinas', 'summa', 'augustine', 'confessions', 'dante',
                            'inferno', 'purgatorio', 'paradiso', 'boethius',
                            'consolation', 'anselm', 'abelard'],
    'philosophy_enlightenment': ['kant', 'hume', 'locke', 'rousseau', 'voltaire',
                                  'descartes', 'spinoza', 'leibniz', 'hobbes',
                                  'machiavelli', 'prince', 'leviathan'],
    'philosophy_20th': ['nietzsche', 'zarathustra', 'wittgenstein', 'heidegger',
                         'sartre', 'camus', 'russell', 'foucault', 'derrida',
                         'phenomenology', 'existential'],
    'science_general': ['darwin', 'origin-species', 'scientific', 'method',
                        'evolution', 'chemistry'],
    'science_physics': ['einstein', 'relativity', 'newton', 'principia', 'quantum',
                        'feynman', 'hawking', 'planck', 'schrodinger', 'bohr'],
    'science_biology': ['biology', 'cell', 'genetics', 'dna', 'evolution',
                        'anatomy', 'organism', 'ecology'],
    'mathematics': ['calculus', 'algebra', 'geometry', 'euclid', 'mathematics',
                    'number-theory', 'probability', 'statistics'],
    'literature': ['shakespeare', 'frankenstein', 'moby', 'dickens', 'austen',
                   'twain', 'tolstoy', 'dostoevsky', 'homer', 'iliad', 'odyssey'],
    'psychology': ['freud', 'jung', 'psychology', 'cognitive', 'behavioral',
                   'consciousness', 'perception', 'memory'],
}


def detect_domain(source: str) -> str:
    """
    Identify a content domain label by matching known substring patterns against the provided source string.
    
    Parameters:
        source (str): Source text to inspect (e.g., a URL, filename, or other identifying string).
    
    Returns:
        str: A domain key from DOMAIN_PATTERNS when a pattern is found, or 'unknown' if no match is detected.
    """
    source_lower = source.lower()
    for domain, patterns in DOMAIN_PATTERNS.items():
        for pattern in patterns:
            if pattern in source_lower:
                return domain
    return 'unknown'


def extract_topics_from_source(source: str) -> List[str]:
    """
    Return the list of topic pattern strings found in a source string by matching against DOMAIN_PATTERNS.
    
    Parameters:
        source (str): Source text to scan (e.g., URL, filename, or text snippet).
    
    Returns:
        List[str]: A list of matching pattern substrings (case-insensitive). Matches are returned in the order found and may include duplicates; returns an empty list if no patterns match.
    """
    source_lower = source.lower()
    topics = []
    for domain, patterns in DOMAIN_PATTERNS.items():
        for pattern in patterns:
            if pattern in source_lower:
                topics.append(pattern)
    return topics


# ============================================================================
# CLI INTERFACE (for integration into chat.py)
# ============================================================================

if __name__ == "__main__":
    print("Quantum MCAGI — Stage Advancement Exam System")
    print("Integrate into chat.py with:")
    print("  from exam_system import ExamRunner, IntakeTracker")
    print("  tracker = IntakeTracker()")
    print("  runner = ExamRunner(engine, tracker)")
    print("  runner.run_exam(current_stage)")
    print()
    print("Commands:")
    print("  /exam          — Run stage advancement exam")
    print("  /exam status   — Show readiness and history")
    print("  /exam review   — Show last exam details")
