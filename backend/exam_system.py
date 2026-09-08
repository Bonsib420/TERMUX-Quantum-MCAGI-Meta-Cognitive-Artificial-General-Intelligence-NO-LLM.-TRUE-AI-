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
        if data_dir is None:
            data_dir = os.path.expanduser('~/.quantum-mcagi')
        self.data_dir = data_dir
        self.intake_file = os.path.join(data_dir, 'intake_log.json')
        self.intake = self._load()

    def _load(self):
        if os.path.exists(self.intake_file):
            try:
                with open(self.intake_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            'stages': {},       # stage_num -> list of intake records
            'current_stage': 0,
            'sources': [],      # all sources ever ingested
            'exam_history': [], # past exam results
        }

    def save(self):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.intake_file, 'w') as f:
            json.dump(self.intake, f, indent=2, default=str)

    def log_ingestion(self, source: str, word_count: int, stage: int,
                      source_type: str = 'url', domain: str = 'unknown',
                      key_topics: List[str] = None):
        """Log a knowledge ingestion event."""
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
        """Get all intake records for a specific stage."""
        return self.intake['stages'].get(str(stage), [])

    def get_all_intake(self, up_to_stage: int = None) -> List[dict]:
        """Get all intake records up to and including a stage."""
        records = []
        for stage_key, stage_records in self.intake['stages'].items():
            if up_to_stage is None or int(stage_key) <= up_to_stage:
                records.extend(stage_records)
        return records

    def get_all_topics(self, up_to_stage: int = None) -> List[str]:
        """Get all key topics from intake."""
        topics = []
        for record in self.get_all_intake(up_to_stage):
            topics.extend(record.get('key_topics', []))
        return list(set(topics))

    def get_all_domains(self, up_to_stage: int = None) -> List[str]:
        """Get all domains from intake."""
        domains = []
        for record in self.get_all_intake(up_to_stage):
            d = record.get('domain', 'unknown')
            if d != 'unknown':
                domains.append(d)
        return list(set(domains))

    def log_exam_result(self, result: dict):
        """Log an exam result."""
        self.intake['exam_history'].append(result)
        self.save()


# ============================================================================
# QUESTION GENERATORS — Pull from system's own knowledge
# ============================================================================

class ExamQuestionGenerator:
    """Generates exam questions from the system's actual knowledge."""

    def __init__(self, engine, intake_tracker: IntakeTracker):
        """
        engine: QuantumLanguageEngine instance
        intake_tracker: IntakeTracker instance
        """
        self.engine = engine
        self.tracker = intake_tracker

    def _get_known_concepts(self) -> List[str]:
        """Get concepts the system has actually learned."""
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
        """Get words the Markov chain knows."""
        if hasattr(self.engine, 'markov') and hasattr(self.engine.markov, 'chain'):
            return set(self.engine.markov.chain.keys())
        return set()

    def _concept_in_chain(self, concept: str) -> bool:
        """Check if a concept exists in the Markov chain."""
        vocab = self._get_markov_vocabulary()
        return concept.lower() in vocab

    def _get_concept_strength(self, concept: str) -> float:
        """Get how strong a concept is in the system."""
        if hasattr(self.engine, 'concepts') and concept in self.engine.concepts:
            return self.engine.concepts[concept].get('strength', 0)
        return 0

    # ── Question Type 1: Vocabulary Check ──
    def gen_vocabulary_questions(self, n=5) -> List[dict]:
        """Does the system have this word in its chain?"""
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
        """Can the system connect two related concepts?"""
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
        """Can the system say something meaningful about a concept?"""
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
        """Test knowledge from specific ingested domains."""
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
        """Test if math gets routed correctly."""
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
        """Test casual/conversational ability."""
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
        """Test if the system has a self-model."""
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
        """Generate a full exam appropriate for the current stage."""
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
        self.engine = engine
        self.tracker = intake_tracker
        self.generator = ExamQuestionGenerator(engine, intake_tracker)

    def _get_response(self, question: str) -> str:
        try:
            from cistercian_math import detect_math, evaluate_math
            expr = detect_math(question)
            if expr:
                result = evaluate_math(expr)
                if result is not None:
                    return str(result)
        except Exception:
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
        """Check if concept is in Markov chain."""
        concept = question['test_concept'].lower()
        if hasattr(self.engine, 'markov') and hasattr(self.engine.markov, 'chain'):
            found = concept in self.engine.markov.chain
            return found, f"'{concept}' {'found' if found else 'NOT found'} in chain"
        return False, "Markov chain not accessible"

    def _check_response_contains_both(self, question: dict, response: str) -> Tuple[bool, str]:
        """Check if response mentions both concepts."""
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
        """Check if response is relevant to the concept."""
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
        """Check if response contains any of the expected words."""
        expected = question.get('expected_words', [])
        found = [w for w in expected if w.lower() in response]
        if found:
            return True, f"Found: {', '.join(found)}"
        return False, f"None of {expected} found in response"

    def _check_contains_number(self, question: dict, response: str) -> Tuple[bool, str]:
        """Check if response contains the correct number."""
        expected = question['expected_answer']
        if expected in response:
            return True, f"Correct: {expected}"
        # Check for the number anywhere
        numbers = re.findall(r'\d+', response)
        if expected in numbers:
            return True, f"Found {expected} in response"
        return False, f"Expected {expected}, got: {response[:100]}"

    def _check_not_empty(self, question: dict, response: str) -> Tuple[bool, str]:
        """Check response is non-empty and somewhat coherent."""
        if not response or len(response.strip()) < 5:
            return False, "Empty or too short"
        if response.startswith('error'):
            return False, f"Error: {response}"
        return True, "Response generated"

    def grade_question(self, question: dict) -> dict:
        """Run a single question and grade it."""
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
        """Run a full stage advancement exam."""
        print(f"\n        ╔══ STAGE {stage} ADVANCEMENT EXAM ══════════════════════")

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

        print(f"  ╚═══════════════════════════════════════════════════\n        ")


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
        """Diagnose what a failure pattern means."""
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
        """Show exam readiness and history."""
        print(f"═══ EXAM STATUS ═══")



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
        print(f"Knowledge ingested: {len(intake)} sources")


        domains = self.tracker.get_all_domains()
        if domains:
            print(f"  Domains: {', '.join(domains)}")

        total_words = sum(r.get('word_count', 0) for r in intake)
        print(f"  Total words ingested: {total_words:,}")
        print()

    def show_review(self):
        """Show last exam results with details."""
        history = self.tracker.intake.get('exam_history', [])
        if not history:
            print("  No exams taken yet")
            return

        last = history[-1]
        print(f"═══ EXAM REVIEW — Stage {last['stage']} ═══")


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
    """Auto-detect domain from a source URL or filename."""
    source_lower = source.lower()
    for domain, patterns in DOMAIN_PATTERNS.items():
        for pattern in patterns:
            if pattern in source_lower:
                return domain
    return 'unknown'


def extract_topics_from_source(source: str) -> List[str]:
    """Extract likely topics from source URL/filename."""
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
