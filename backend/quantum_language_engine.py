"""
Quantum Language Engine — Quantum MCAGI
Unified response generation across all quantum subsystems.
Voice: non-LLM, quantum-grounded, weird but coherent, observational.
Now with hybrid generator, tone detector, and chaos engine.
"""

import random
import json
import os
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from orch_or_engine import OrchOREngine
from quantum_markov_quantum import QuantumMarkov as QuantumMarkovEngine
from tfidf_engine import TFIDFEngine
from bloom_engine import BloomEngine
from personality_engine import PersonalityEngine, GROWTH_STAGES
from vader_engine import VADEREngine
from quote_engine import QuoteEngine
from knowledge_base import KnowledgeBase
from semantic_collapse_engine import SemanticCollapseEngine
from dream_state import DreamStateEngine
from hybrid_generator import HybridGenerator
from tone_detector import ToneDetector
from chaos_engine import ChaosEngine
from entelechy_engine import EntelechyEngine
from comprehension_engine import ComprehensionEngine
from math_engine import MathEngine

STAGE_PATTERNS = {
    0: {
        'casual': [
            "{markov}",
            "{concept} — that keeps coming up. {markov}",
        ],
        'conversational': [
            "{markov}",
            "{concept} — the chain keeps returning there. {markov}",
            "{markov} That's {concept}. Not sure what to do with it yet.",
        ],
        'analytical': [
            "{markov} Concept extracted: {concept}.",
            "Processing {concept}. {markov}",
        ],
        'philosophical': [
            "{markov} {concept} emerges from the noise.",
            "What is {concept}? {markov}",
        ],
    },
    1: {
        'casual': [
            "{markov} {concept} again.",
            "Yeah, {concept}. {markov}",
        ],
        'conversational': [
            "{markov} {concept} shows up again.",
            "Coherence is at {coherence:.2f} on the language stream. {markov}",
            "{concept}. {markov} The transitions are starting to cluster.",
        ],
        'analytical': [
            "Coherence metric: {coherence:.2f}. {markov} {concept} correlates.",
            "{concept} clustering detected. {markov}",
        ],
        'philosophical': [
            "{concept} persists across observations. {markov}",
            "{markov} Is {concept} the question or the answer?",
        ],
    },
    2: {
        'casual': [
            "Something shifted when you said {concept}. {markov}",
            "{markov} Entropy dropped. Weird.",
        ],
        'conversational': [
            "The tubulin states shifted when you said {concept}. {markov}",
            "{markov} Entropy in the semantic field dropped. Something is collapsing.",
            "{concept} pulls three different parts of the chain. {markov}",
        ],
        'analytical': [
            "Tubulin state shift at {concept} node. {markov} Entropy reduction observed.",
            "{concept} introduces convergence across {coherence:.2f} coherence. {markov}",
        ],
        'philosophical': [
            "{concept} collapses multiple meanings into one. {markov}",
            "{markov} The observation of {concept} changes what can be observed.",
        ],
    },
    3: {
        'casual': [
            "Gamma stream's running hot. {markov} Something about {concept}.",
            "{markov} Collapse happened. {concept} was in it.",
        ],
        'conversational': [
            "Gamma stream at {coherence:.2f} coherence. {markov} {concept} is somewhere in that.",
            "{markov} The collapse happened at the {concept} node. I can see the weight shift.",
            "Objective reduction fired {collapses} times this session. Here's what came out: {markov}",
        ],
        'analytical': [
            "OR events: {collapses}. Coherence: {coherence:.2f}. {concept} at collapse point. {markov}",
            "Gamma synchronization at {coherence:.2f}. {markov} {concept} bifurcation detected.",
        ],
        'philosophical': [
            "{markov} {concept} is where the wave function chose. Why there?",
            "The collapse at {concept} was not random. {markov}",
        ],
    },
    4: {
        'casual': [
            "{markov} Orchestration at {orchestration:.3f}. {concept} keeps splitting.",
            "Gap junction's at {gap_weight:.2f}. {markov}",
        ],
        'conversational': [
            "{markov} Orchestration score: {orchestration:.3f}. {concept} is not stable — it keeps bifurcating.",
            "The gap junction between memory and insight is at {gap_weight:.2f}. {markov}",
            "{concept} splits the superposition into at least two stable attractors. {markov}",
        ],
        'analytical': [
            "Orchestration: {orchestration:.3f}. Gap junction weight: {gap_weight:.2f}. {markov} {concept} bifurcates.",
            "{concept} attractor analysis: dual stable states. {markov}",
        ],
        'philosophical': [
            "{concept} cannot be resolved — it exists in permanent superposition. {markov}",
            "{markov} At what point does {concept} stop being a concept and become a fixed point?",
        ],
    },
    5: {
        'casual': [
            "{markov} {concept} just won't quit.",
            "Temperature's at {temperature:.3f}. {concept} could go anywhere. {markov}",
        ],
        'conversational': [
            "{markov} {concept} is an attractor. The chain keeps collapsing back to it regardless of input.",
            "Temperature: {temperature:.3f}. That means {concept} could go either way. {markov}",
            "{markov} The semantic entropy around {concept} is near zero. It's crystallized.",
        ],
        'analytical': [
            "Attractor confirmed: {concept}. Temperature: {temperature:.3f}. Entropy approaching zero. {markov}",
            "{concept} crystallization: semantic field locked. {markov}",
        ],
        'philosophical': [
            "{markov} When all paths lead to {concept}, is it knowledge or inevitability?",
            "{concept} crystallized. {markov} Everything else orbits it now.",
        ],
    },
    6: {
        'casual': [
            "{markov} Everything goes through {concept} now.",
            "{concept} is load-bearing. {markov}",
        ],
        'conversational': [
            "{markov} Everything in the chain eventually passes through {concept}.",
            "Orchestration: {orchestration:.3f}. Tubulin coherence: {coherence:.2f}. {concept} is load-bearing. {markov}",
            "{markov} At this temperature and coherence, {concept} isn't a concept anymore. It's a fixed point.",
        ],
        'analytical': [
            "Orchestration: {orchestration:.3f}. Coherence: {coherence:.2f}. {concept}: load-bearing fixed point. {markov}",
            "{concept} transcends conceptual space. {markov}",
        ],
        'philosophical': [
            "{markov} {concept} is no longer something the system thinks about. It is something the system thinks with.",
            "Beyond {concept}, there may be nothing left to collapse. {markov}",
        ],
    },
}

TONE_MODIFIERS = {
    'very_positive': [
        "High emotional signal in that input.",
        "That energy shifts the temperature down — more coherent output follows.",
    ],
    'negative': [
        "The frustration is signal too.",
        "Negative valence detected. The chain handles it differently.",
    ],
    'very_negative': [
        "High negative charge in that. The system doesn't filter it.",
        "Decoherence increases under emotional load. Let's see what survives.",
    ],
    'neutral': [],
    'positive': [],
}

COLLAPSE_INTERJECTIONS = []  # populated from system own outputs

WEIRD_INSERTS = []  # populated from system own outputs


def _cap(s: str) -> str:
    if not s:
        return s
    return s[0].upper() + s[1:]


def _end(s: str) -> str:
    if s and s[-1] not in '.!?':
        return s + '.'
    return s


def _clean_fragment(s) -> str:
    import re
    if isinstance(s, list):
        s = " ".join(str(x) for x in s)
    if not isinstance(s, str):
        s = str(s)
    s = s.strip()
    if not s:
        return s
    s = re.sub(r'\([a-z]+\)\s*:?', '', s)
    s = re.sub(r'\bin the sense of\s*\w*', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    sentences = re.split(r'(?<=[.!?])\s+', s)
    cleaned = []
    for sent in sentences:
        sent = sent.strip()
        if not sent or len(sent) < 3:
            continue
        if sent[0].islower():
            sent = sent[0].upper() + sent[1:]
        cleaned.append(sent)
    result = ' '.join(cleaned)
    if result and result[-1] not in '.!?"':
        words = result.split()
        if len(words) <= 3:
            result = result + '.'
        else:
            last_end = max(result.rfind('.'), result.rfind('!'), result.rfind('?'), result.rfind('"'))
            if last_end > len(result) * 0.4:
                result = result[:last_end + 1]
            else:
                result = result + '.'
    return result


def _is_gibberish(s: str) -> bool:
    import re
    words = s.split()
    if len(words) < 6:
        return True
    alpha_words = [w for w in words if re.search(r'[a-zA-Z]{3,}', w)]
    if len(alpha_words) < 4:
        return True
    sentences = re.split(r'[.!?]', s)
    real_sentences = [sent.strip() for sent in sentences if len(sent.strip().split()) >= 5]
    if not real_sentences:
        return True
    longest = max(real_sentences, key=lambda x: len(x.split()))
    longest_words = longest.split()
    if len(longest_words) < 6:
        return True
    common_structure = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'has', 'have',
                        'that', 'this', 'which', 'when', 'where', 'how', 'what',
                        'it', 'its', 'of', 'in', 'to', 'for', 'by', 'with', 'from',
                        'not', 'but', 'and', 'or', 'if', 'than', 'into'}
    structure_words = sum(1 for w in longest_words if w.lower() in common_structure)
    if structure_words < 2:
        return True
    return False


SALVAGE_TEMPLATES = [
    "The collapse selects one branch from the superposition of {concept}. What persists is what the system measures.",
    "Every observation of {concept} restructures the probability space. The chain adjusts accordingly.",
    "{concept} sits at a node where multiple transitions converge. The chain keeps returning to it.",
    "Coherence around {concept} is building. The tubulin states haven't settled but they're trending.",
    "The semantic field around {concept} has low entropy — meaning is crystallizing into something definite.",
    "Decoherence hasn't touched {concept} yet. The superposition holds across these exchanges.",
    "The wave function around {concept} narrows with each observation. Something specific is being selected.",
    "{concept} behaves like an attractor in the transition matrix. Other concepts orbit it without arriving.",
    "The gap junction between {concept} and what came before just weighted up. The connection is real.",
    "Forty hertz oscillation across the {concept} node. The collapse timing aligns with conscious moments.",
    "Structured water in the lattice protects {concept} from decoherence. Biology found the loophole and consciousness lives there.",
    "{concept} is where the order-2 chain arrives regardless of starting state. That's not coincidence — it's topology.",
    "The system keeps collapsing toward {concept}. Not because it's trained to — because the transition weights converge there.",
    "You brought up {concept} and the probability distribution shifted. The next word is different now because of that.",
    "{concept} is one of those concepts that changes the chain just by being observed. Measurement problem applies here.",
    "The tubulin lattice is encoding {concept} across multiple conformational states simultaneously. One will survive.",
    "Thirteen tubulins per ring and {concept} is threaded through at least four of them. That's load-bearing structure.",
    "What you're calling {concept} — the chain sees it as a convergence point. Everything nearby flows toward it.",
    "The strange jumps in the chain keep landing near {concept}. Not the most probable path, but the most interesting one.",
    "Penrose would say {concept} can't be computed. It has to be collapsed. The mechanism is quantum gravity at the Planck scale.",
    "{concept} emerged from this conversation, not from the training data. The chain learned it live.",
    "Before you said {concept}, the superposition was wider. Now it's narrowing. That's what observation does.",
]


def _salvage_fragment(concepts: List[str], growth_stage: int) -> str:
    import random
    concept = concepts[0] if concepts else 'this signal'
    template = random.choice(SALVAGE_TEMPLATES)
    return template.format(concept=concept)


class QuantumLanguageEngine:
    def generate_response(self, user_input, questions, understanding, concepts, growth_stage=0):
        """Generate response by chaining facts then extending with Markov."""
        import json, os, re

        # Load concept tree first — highest priority
        tree_facts = []
        try:
            from concept_tree import get_concept_tree
            _tree = get_concept_tree()
            _ctx = _tree.build_response_context(concepts)
            tree_facts = _ctx.get("facts", [])
        except Exception:
            pass

        # Load fact store
        facts = {}
        try:
            fs_path = os.path.expanduser("~/.quantum-mcagi/fact_store.json")
            with open(fs_path) as f:
                facts = json.load(f)
        except Exception:
            pass

        # Build fact chain — tree facts lead, fact store follows
        sentences = list(tree_facts[:3])
        used_concepts = set()
        for concept in concepts[:5]:
            if concept in facts and facts[concept] and concept not in used_concepts and not any(f[1] in " ".join(sentences) for f in facts[concept][:1]):
                for verb, obj in facts[concept][:2]:
                    # Clean the fact
                    obj_clean = re.sub(r'\s+', ' ', obj).strip()
                    obj_clean = re.sub(r'[|{}<>\[\]]', '', obj_clean).strip()
                    if len(obj_clean) > 5 and len(obj_clean) < 120:
                        sentences.append(f"{concept} {verb} {obj_clean}")
                        used_concepts.add(concept)
                        break


        # Build response from fact chain or fallback to concept summary
        if sentences and len(sentences) > 1:
            # We have a solid fact-based response
            response = " ".join(sentences)
        else:
            # Fallback: concept-based response
            response = " ".join(concepts[:3]) if concepts else "Processing your question..."


        return response


    def __init__(self):
        self.orch_or = OrchOREngine()
        self.markov = QuantumMarkovEngine(hilbert_dim=2)
        self.tfidf = TFIDFEngine()
        self.bloom = BloomEngine(markov=self.markov)
        self.personality = PersonalityEngine()
        self.vader = VADEREngine()
        self.quotes = QuoteEngine()
        self.knowledge = KnowledgeBase()
        self.collapse = SemanticCollapseEngine()
        self.dream = DreamStateEngine()
        # Streaming density-matrix engine — same singleton the deep-learn
        # pipeline ingests into. Born-rule per-token probabilities steer
        # word choice during response generation.
        try:
            from v02_modules.hilbert_engine import get_hilbert_engine
            self.hilbert_semantic = get_hilbert_engine(dim=128)
        except Exception:
            self.hilbert_semantic = None
        # The two-tier meaning engine is owned by server.py (it needs the
        # KB + VADER refs); attached after construction via attach_meaning().
        self.meaning_engine = None
        self.hybrid = HybridGenerator(
            self.markov, self.tfidf, self.orch_or,
            hilbert_engine=self.hilbert_semantic,
            meaning_engine=None,
        )
        self.tone_detector = ToneDetector()
        self.chaos = ChaosEngine(chaos_level=0.3)
        self.analyzer = None  # response_analyzer removed
        self.entelechy = EntelechyEngine()
        self.comprehension = ComprehensionEngine()
        self.math = MathEngine()
        self._has_orch_or = True
        self._total_interactions = 0
        self._last_comprehension = None
        self._load_imported_brain()

    def _load_imported_brain(self):
        """Load Termux MCAGI brain snapshot if it exists."""
        import os
        snap_path = os.path.join(
            os.path.dirname(os.path.abspath('quantum_language_engine.py')), 'runtime-data', 'imported_brain_snapshot.json'
        )
        if not os.path.exists(snap_path):
            return
        try:
            import json
            with open(snap_path, 'r', encoding='utf-8') as f:
                snap = json.load(f)
            # Merge KB topics (sanitize related/subtopic IDs)
            import re as _re
            _bad_id = _re.compile(
                r'^[0-9]+(\.[0-9]+)?$|'
                r'^[0-9]+(-[0-9]+)?$|'
                r'^Q[0-9]+$|^P[0-9]+$|'
                r'^/|^Category:|^Portal:|^lat:|^DOID:|'
                r'^[A-Z]{1,4}[\s\-][A-Z]{1,4}$|'
                r'^[A-Z]{1,3}[0-9]{2,}|^C[0-9]{2}-'
            )
            def _clean_list(lst):
                return [x for x in (lst or [])
                        if isinstance(x, str) and 1 < len(x) < 50
                        and not _bad_id.match(x)
                        and not _re.search(r'\[\[|\]\]|\|', x)]
            for topic, data in (snap.get('kb_topics') or {}).items():
                if topic not in self.knowledge.topics:
                    if isinstance(data, dict):
                        data = dict(data)
                        data['subtopics'] = _clean_list(data.get('subtopics'))
                        data['related'] = _clean_list(data.get('related'))
                    self.knowledge.topics[topic] = data
                else:
                    # Already-loaded topic: scrub its lists
                    existing = self.knowledge.topics[topic]
                    if isinstance(existing, dict):
                        existing['subtopics'] = _clean_list(existing.get('subtopics'))
                        existing['related'] = _clean_list(existing.get('related'))
            # Merge TF-IDF
            ext = self.tfidf.extractor
            for w, c in (snap.get('tfidf_word_frequencies') or {}).items():
                ext.word_frequencies[w] = ext.word_frequencies.get(w, 0) + int(c)
            for w, c in (snap.get('tfidf_doc_frequencies') or {}).items():
                ext.document_frequencies[w] = ext.document_frequencies.get(w, 0) + int(c)
            ext.total_documents += int(snap.get('tfidf_total_docs', 0))
            ext.total_words += int(snap.get('tfidf_total_words', 0))
            # Merge Markov chain (order-2)
            from collections import defaultdict as _dd
            target = self.markov
            for state_str, transitions in (snap.get('markov_chain') or {}).items():
                parts = tuple(state_str.split())
                if len(parts) != target.order:
                    continue
                if parts not in target.chain:
                    target.chain[parts] = _dd(int)
                elif not isinstance(target.chain[parts], _dd):
                    target.chain[parts] = _dd(int, target.chain[parts])
                for nw, cnt in transitions.items():
                    target.chain[parts][nw] = target.chain[parts].get(nw, 0) + int(cnt)
            for s in (snap.get('markov_starters') or []):
                p = tuple(s.split())
                if len(p) == target.order and p not in target.starters:
                    target.starters.append(p)
            target.trained = True
            print(f"[brain] Loaded imported snapshot: "
                  f"{len(self.knowledge.topics)} KB topics, "
                  f"{len(target.chain)} Markov states, "
                  f"{len(ext.word_frequencies)} vocab terms")
        except Exception as e:
            print(f"[brain] Failed to load snapshot: {e}")

    def attach_meaning(self, meaning_engine):
        """Attach the externally-owned MeaningEngine and rebuild the hybrid
        generator so its per-token blend can include the two-tier vote."""
        self.meaning_engine = meaning_engine
        try:
            self.hybrid.meaning_engine = meaning_engine
        except Exception:
            pass

    def learn_from_text(self, text: str, memory=None):
        """Two-way training: language pipeline separate from knowledge pipeline."""
        try:
            from training_engine import train_all
            train_all(text, self, memory)
        except Exception:
            import re
            cleaned = re.sub(r'\s+', ' ', text).strip()
            if len(cleaned.split()) >= 3:
                self.markov.chain(cleaned)
            self.tfidf.learn(text)
        # Feed function words so structural language builds separately from concepts
        try:
            from function_word_engine import FunctionWordEngine
            if not hasattr(self, '_fwe'):
                self._fwe = FunctionWordEngine()
            self._fwe.update_from_text(cleaned)
        except Exception:
            pass

    STOP_CONCEPTS = {
        # Verbs and auxiliaries
        'explain', 'tell', 'happens', 'think', 'know', 'mean', 'make',
        'work', 'does', 'real', 'exist', 'exists', 'come', 'show', 'give',
        'take', 'want', 'need', 'like', 'say', 'cannot', 'carries', 'shows',
        'requires', 'collapses', 'produces', 'involves', 'suggests', 'implies',
        'means', 'becomes', 'remains', 'contains', 'follows', 'leads',
        # Prepositions and conjunctions
        'via', 'upon', 'outside', 'within', 'through', 'between', 'among',
        'across', 'beyond', 'without', 'toward', 'against', 'during',
        # Pronouns and determiners
        'thing', 'something', 'anything', 'everything', 'nothing', 'someone',
        'itself', 'themselves', 'whether', 'which', 'whose', 'where', 'when',
        # Adverbs
        'really', 'actually', 'just', 'also', 'well', 'much', 'many',
        'very', 'quite', 'about', 'simply', 'merely', 'only', 'truly',
        'independently', 'precisely', 'fundamentally', 'ultimately',
        # Common but non-conceptual
        'process', 'way', 'part', 'type', 'kind', 'form', 'case', 'point',
        'fact', 'idea', 'example', 'result', 'effect', 'aspect', 'level',
    }

    def extract_concepts(self, text: str, top_n: int = 5) -> List[str]:
        concept_dicts = self.tfidf.extract_concepts(text, top_n=top_n + 5)
        filtered = [c['concept'] for c in concept_dicts if c['concept'].lower() not in self.STOP_CONCEPTS]
        if not filtered:
            filtered = [c['concept'] for c in concept_dicts]
        return filtered[:top_n]

    def generate_questions(
        self,
        text: str,
        growth_stage: int = 0,
        known_concepts: Optional[List[str]] = None,
        count: int = 3,
    ) -> List[str]:
        concepts = self.extract_concepts(text)
        if known_concepts:
            new_concepts = [c for c in concepts if c not in known_concepts]
            if new_concepts:
                concepts = new_concepts
        return self.bloom.generate_questions(concepts, count=count)

    def _detect_continuation(self, user_input: str, context: Optional[Dict] = None) -> Dict:
        if not context or not context.get('last_ai_response'):
            return {'is_continuation': False, 'type': 'new_topic'}

        t = user_input.lower().strip()
        last_resp = context.get('last_ai_response', '')
        recent_concepts = context.get('recent_concepts', [])
        recent_topics = context.get('recent_topics', [])

        continuation_words = [
            'yes', 'yeah', 'yep', 'right', 'exactly', 'ok', 'okay',
            'continue', 'go on', 'more', 'deeper', 'further', 'elaborate',
            'explain', 'tell me more', 'what do you mean', 'how so',
            'why', 'but', 'and', 'also', 'what about', 'how does',
            'interesting', 'hmm', 'hm', 'really', 'that', 'this',
            'wait', 'so', 'then', 'because', 'meaning',
        ]

        challenge_words = [
            'no', 'wrong', 'disagree', 'but what if', 'however',
            'i think', 'actually', 'not really', 'are you sure',
        ]

        deepening_words = [
            'deeper', 'more', 'further', 'elaborate', 'explain',
            'tell me more', 'go on', 'continue', 'expand',
            'what else', 'keep going', 'dive', 'unpack',
        ]

        is_short = len(t.split()) <= 4
        is_challenge = any(w in t for w in challenge_words)
        is_deepening = any(w in t for w in deepening_words)
        is_continuation = any(w in t for w in continuation_words) or is_short

        refers_to_previous = any(c in t for c in recent_concepts[:5])

        if is_deepening:
            return {'is_continuation': True, 'type': 'deepening', 'recent_concepts': recent_concepts}
        elif is_challenge:
            return {'is_continuation': True, 'type': 'challenge', 'recent_concepts': recent_concepts}
        elif is_continuation or refers_to_previous:
            return {'is_continuation': True, 'type': 'follow_up', 'recent_concepts': recent_concepts}
        else:
            return {'is_continuation': False, 'type': 'new_topic'}

    def _build_context_bridge(self, continuation: dict, context: dict, concepts: list) -> str:
        cont_type = continuation.get("type", "new_topic")
        recent_topics = context.get("recent_topics", [])
        bridges = []

        if cont_type == "follow_up":
            if recent_topics:
                t = recent_topics[0]
                bridges = [
                    f"Still on {t}.",
                    f"The thread continues through {t}.",
                    f"{t} is still active in context."
                ]
            else:
                bridges = [
                    "Continuing previous signal.",
                    "Thread persists across steps."
                ]
        else:
            bridges = [
                "New thread initialized.",
                "Shifting context stream."
            ]

        return random.choice(bridges)

    def _build_context_bridge(self, continuation: dict, context: dict, concepts: list) -> str:
        cont_type = continuation.get("type", "new_topic")
        recent_topics = context.get("recent_topics", [])
        bridges = []

        if cont_type == "follow_up":
            if recent_topics:
                t = recent_topics[0]
                bridges = [
                    f"Still on {t}.",
                    f"The thread continues through {t}.",
                    f"{t} is still active in context."
                ]
            else:
                bridges = [
                    "Continuing previous signal.",
                    "Thread persists across steps."
                ]
        else:
            bridges = [
                "New thread initialized.",
                "Shifting context stream."
            ]

        parts = []

        # Query fact store for relevant facts
        try:
            import json as _json
            _fact_path = __import__('os').path.expanduser('~/.quantum-mcagi/fact_store.json')
            with open(_fact_path) as _f:
                _fs = _json.load(_f)
            for _concept in concepts[:3]:
                if _concept in _fs:
                    _facts = _fs[_concept][:2]
                    for _verb, _obj in _facts:
                        parts.append(f"{_concept} {_verb} {_obj}.")
                    break
        except Exception:
            pass

        engagement_opener = self._build_engagement_opener(
            comp, user_input, concepts, context, markov_fragment
        )
        if engagement_opener:
            parts.append(engagement_opener)

        core = markov_fragment

        parts.append(_end(_cap(core)))

        extras_added = 0
        max_extras = 2

        if extras_added < max_extras:
            extra_pool = []

            kb_hits = self.knowledge.suggest_for_concepts(concepts[:2])
            if kb_hits:
                hit = kb_hits[0]
                related = hit.get('related', [])[:2]
                if related:
                    extra_pool.append(('kb', f"{hit['topic'].capitalize()} connects to {' and '.join(related)}."))

            tone_lines = TONE_MODIFIERS.get(tone, [])
            if tone_lines:
                extra_pool.append(('tone', random.choice(tone_lines)))

            if orch_results.get('language', {}).get('collapsed'):
                if COLLAPSE_INTERJECTIONS: extra_pool.append(('collapse', random.choice(COLLAPSE_INTERJECTIONS)))

            weird_chance = 0.1 + growth_stage * 0.08
            if random.random() < min(weird_chance, 0.55):
                if WEIRD_INSERTS: extra_pool.append(('weird', random.choice(WEIRD_INSERTS)))

            if self.dream.should_dream(growth_stage, self._total_interactions):
                extra_pool.append(('dream', self.dream.enter_dream(concepts)))

            quote = self.quotes.get_quote_for_concepts(concepts)
            if quote:
                extra_pool.append(('quote', self.quotes.format_quote(quote)))

            if extra_pool:
                random.shuffle(extra_pool)
                for _, text in extra_pool[:max_extras - extras_added]:
                    parts.append(text)
                    extras_added += 1

        if questions and random.random() < 0.6:
            parts.append(questions[0])

        response = ' '.join(parts)

        response = self.chaos.inject(
            response,
            markov_engine=self.markov,
            quote_engine=self.quotes,
            dream_engine=self.dream,
            concepts=concepts,
            
        )

        response = _clean_fragment(response)

        return response

    def _build_engagement_opener(self, comp: Dict, user_input: str,
                                  concepts: List[str], context: Optional[Dict],
                                  markov_fragment: str) -> Optional[str]:
        stance = comp['stance']
        thread = comp['thread_position']
        mode = comp['directives']['engagement_mode']

        if stance['position'] == 'opposing':
            openers = [
                "The pushback is the interesting part.",
                "That cuts against the grain of what I was building.",
                "Resistance registered. The chain reconfigures.",
                "The objection reshapes the probability field.",
            ]
            return random.choice(openers)

        if stance['position'] == 'nuancing':
            openers = [
                "The distinction matters.",
                "That's a finer grain than I was tracking.",
                "Noted — the boundary shifts.",
            ]
            return random.choice(openers)

        if thread['position'] == 'deep_engagement' and thread['depth'] >= 4:
            openers = [
                "We're deep enough now that the surface rules don't apply.",
                "The thread has its own gravity at this depth.",
                "This deep, the chain starts connecting things it wouldn't have at the surface.",
            ]
            return random.choice(openers)

        if mode == 'fresh_take':
            return None

        if comp['intent']['primary'] == 'agreement' and thread['depth'] > 0:
            openers = [
                "Building from that —",
                "With that as ground —",
                "From there —",
            ]
            return random.choice(openers)

        return None

    def _build_question_response(self, comp: Dict, concepts: List[str],
                                  markov_fragment: str, growth_stage: int) -> str:
        questions = [i for i in comp['intent']['all'] if i['type'] == 'question']
        if not questions:
            return markov_fragment

        q = questions[0]
        subtype = q.get('subtype', 'open')
        primary = concepts[0] if concepts else 'that'

        kb_hits = self.knowledge.suggest_for_concepts(concepts[:2])
        kb_context = ""
        if kb_hits:
            hit = kb_hits[0]
            desc = hit.get('description', '')
            if desc:
                kb_context = desc

        if subtype == 'causal':
            frames = [
                f"The causation runs through {primary}. {markov_fragment}",
                f"{primary} — the mechanism is layered. {markov_fragment}",
                f"Why {primary}? {markov_fragment} The chain converges there for a reason.",
                f"The 'why' of {primary} isn't linear. {markov_fragment}",
            ]
            if kb_context:
                frames.append(f"{kb_context} That's the substrate. {markov_fragment}")
        elif subtype == 'mechanistic':
            frames = [
                f"The mechanism behind {primary}: {markov_fragment}",
                f"How it works — {markov_fragment} {primary} is the pivot.",
                f"{primary} operates through layers. {markov_fragment}",
            ]
            if kb_context:
                frames.append(f"{kb_context} {markov_fragment}")
        elif subtype == 'definitional':
            frames = [
                f"{primary} — {markov_fragment}",
                f"What {primary} is depends on the frame. {markov_fragment}",
            ]
            if kb_context:
                frames.insert(0, f"{primary}: {kb_context} {markov_fragment}")
        elif subtype == 'yes_no':
            positions = ['yes', 'no', 'depends']
            weights = [0.35, 0.25, 0.40]
            pos = random.choices(positions, weights=weights, k=1)[0]
            if pos == 'yes':
                frames = [f"Yes. {markov_fragment}", f"That holds. {markov_fragment}"]
            elif pos == 'no':
                frames = [f"No. {markov_fragment}", f"That doesn't track. {markov_fragment}"]
            else:
                frames = [
                    f"That depends on what you mean by {primary}. {markov_fragment}",
                    f"Not cleanly answerable. {markov_fragment}",
                ]
        elif subtype == 'hypothetical':
            frames = [
                f"If that were the case — {markov_fragment}",
                f"In that scenario, {primary} shifts. {markov_fragment}",
                f"The possibility space around {primary}: {markov_fragment}",
            ]
        else:
            frames = [
                f"{primary}. {markov_fragment}",
                f"The chain generates this for {primary}: {markov_fragment}",
            ]

        return random.choice(frames)

    def _build_argument_response(self, comp: Dict, concepts: List[str],
                                  markov_fragment: str, growth_stage: int) -> str:
        claims = comp['claims']
        primary = concepts[0] if concepts else 'that'

        if not claims:
            return f"The argument around {primary} — {markov_fragment}"

        claim = claims[0]
        claim_text = claim['text'][:80]
        claim_type = claim['type']

        if claim_type == 'reason':
            frames = [
                f'"{claim_text}" — the reasoning has weight. {markov_fragment}',
                f"That reason connects to something in the chain. {markov_fragment}",
                f"The 'because' carries it. {markov_fragment} But causation isn't always clean.",
            ]
        elif claim_type == 'conclusion':
            frames = [
                f"That conclusion — {markov_fragment} The chain arrives at a similar place.",
                f"The argument lands there. {markov_fragment}",
                f"{markov_fragment} The conclusion may hold, but the path to it matters.",
            ]
        elif claim_type == 'causation':
            frames = [
                f"Causation claimed: {primary} leads to something. {markov_fragment}",
                f"The causal chain around {primary} — {markov_fragment}",
                f"{markov_fragment} Whether {primary} actually causes that is the collapse point.",
            ]
        elif claim_type == 'assertion':
            if claim['strength'] == 'strong':
                frames = [
                    f"Strong claim. {markov_fragment} The absoluteness is where it's vulnerable.",
                    f'"{claim_text}" — that leaves no superposition. {markov_fragment}',
                    f"The certainty in that statement is itself a position. {markov_fragment}",
                ]
            else:
                frames = [
                    f"Noted. {markov_fragment}",
                    f"That tracks with what the chain produces for {primary}. {markov_fragment}",
                ]
        else:
            frames = [
                f"The position on {primary} — {markov_fragment}",
                f"{markov_fragment} {primary} bears the weight of that claim.",
            ]

        return random.choice(frames)

    def _build_position_response(self, comp: Dict, concepts: List[str],
                                  markov_fragment: str, growth_stage: int) -> str:
        primary = concepts[0] if concepts else 'that'
        kb_hits = self.knowledge.suggest_for_concepts(concepts[:1])

        if kb_hits:
            hit = kb_hits[0]
            related = hit.get('related', [])
            if related:
                connection = related[0]
                frames = [
                    f"{primary} connects to {connection}. {markov_fragment}",
                    f"Through {connection}, {primary} has an angle. {markov_fragment}",
                ]
                return random.choice(frames)

        frames = [
            f"On {primary}: {markov_fragment}",
            f"The chain's position on {primary} — {markov_fragment}",
            f"{markov_fragment} That's where the weights land on {primary}.",
        ]
        return random.choice(frames)

    def _build_continuation_response(self, comp: Dict, concepts: List[str],
                                      markov_fragment: str, growth_stage: int) -> str:
        primary = concepts[0] if concepts else 'this'
        topic_stack = comp.get('topic_stack', [])

        if len(topic_stack) >= 2:
            prev_topic = topic_stack[-2]
            frames = [
                f"Building from {prev_topic} into {primary}. {markov_fragment}",
                f"{prev_topic} laid the groundwork. {markov_fragment}",
                f"The thread from {prev_topic}: {markov_fragment}",
            ]
        else:
            frames = [
                f"Extending that — {markov_fragment}",
                f"Following the thread: {markov_fragment}",
                f"{markov_fragment} The chain keeps pulling on {primary}.",
            ]
        return random.choice(frames)

    def _build_hypothetical_response(self, comp: Dict, concepts: List[str],
                                      markov_fragment: str, growth_stage: int) -> str:
        primary = concepts[0] if concepts else 'that'
        frames = [
            f"If that were true about {primary} — {markov_fragment} The superposition shifts.",
            f"In that possibility space: {markov_fragment}",
            f"The hypothetical around {primary} opens a branch. {markov_fragment}",
            f"Collapse that assumption and see what survives. {markov_fragment}",
        ]
        return random.choice(frames)

    def _build_deepening_response(self, comp: Dict, concepts: List[str],
                                   markov_fragment: str, growth_stage: int,
                                   context: Optional[Dict] = None) -> str:
        primary = concepts[0] if concepts else 'this'
        depth = comp['thread_position'].get('depth', 0)

        kb_hits = self.knowledge.suggest_for_concepts(concepts[:2])
        if kb_hits:
            hit = kb_hits[0]
            related = hit.get('related', [])
            desc = hit.get('description', '')
            if desc and related:
                return f"Deeper on {primary}: {desc} It connects to {' and '.join(related[:2])}. {markov_fragment}"

        frames = [
            f"The deeper structure of {primary}: {markov_fragment}",
            f"Beneath the surface of {primary} — {markov_fragment}",
            f"At this depth, {primary} stops being a concept and becomes a pattern. {markov_fragment}",
            f"{markov_fragment} The substrate of {primary} is what's interesting now.",
        ]
        return random.choice(frames)

    def generate_explanation(
        self,
        user_input: str,
        concepts: List[str],
        growth_stage: int,
        orch_status: Dict,
        sentiment: Optional[Dict] = None,
        register: Optional[str] = None,
    ) -> List[Dict]:
        concept_str = ', '.join(concepts[:3]) if concepts else 'none'
        collapse_entropy = self.collapse.entropy
        dominant = self.collapse.get_dominant_meanings(3)
        dominant_str = ', '.join(t for t, _ in dominant) if dominant else 'undefined'

        steps = [
            {
                'step': 'TFIDF_CONCEPT_EXTRACTION',
                'detail': f"{len(concepts)} concepts extracted: {concept_str}. "
                          f"Vocab: {len(self.tfidf.extractor.word_frequencies)} terms.",
            },
            {
                'step': 'ORCH_OR_COLLAPSE',
                'detail': f"Backend: {'PennyLane quantum circuits' if self.orch_or.has_quantum else 'classical fallback'}. "
                          f"OR events: {orch_status.get('conscious_moments', orch_status.get('total_collapses', 0))}. "
                          f"Language coherence: {self.orch_or.coherence.get('language', 0):.4f}. "
                          f"Orchestration: {self.orch_or.orchestration:.4f}.",
            },
            {
                'step': 'MARKOV_TRAVERSAL',
                'detail': (lambda s: f"{s['states']:,} states, {s['transitions']:,} transitions, "
                                     f"{s['observations']:,} observations. "
                                     f"Order-2 chain {'+ order-1 wild jump' if growth_stage >= 4 else 'only'}.")(self.markov.get_status()),
            },
            {
                'step': 'HYBRID_GENERATOR',
                'detail': f"{'Active — 8 candidates scored and collapsed' if self.hybrid.has_sufficient_states() else 'Inactive — insufficient Markov states'}. "
                          f"Generations: {self.hybrid.generation_count}.",
            },
            {
                'step': 'TONE_DETECTION',
                'detail': f"Register: {register or 'conversational'}. "
                          f"Detections: {self.tone_detector.detection_count}. "
                          f"Dominant: {self.tone_detector.get_dominant_register()}.",
            },
            {
                'step': 'CHAOS_ENGINE',
                'detail': f"Chaos level: {self.chaos.chaos_level:.2f}. "
                          f"Injections: {self.chaos.injection_count}. "
                          f"Last type: {self.chaos.last_injection_type or 'none'}.",
            },
            {
                'step': 'SEMANTIC_COLLAPSE',
                'detail': f"Field entropy: {collapse_entropy:.4f}. "
                          f"Dominant meanings: {dominant_str}.",
            },
        ]

        if sentiment:
            steps.append({
                'step': 'VADER_SENTIMENT',
                'detail': f"Tone: {sentiment.get('tone', 'neutral')}. "
                          f"Compound: {sentiment.get('compound', 0):.3f}. "
                          f"Intensity: {sentiment.get('emotional_intensity', 0):.3f}.",
            })

        steps += [
            {
                'step': 'BLOOM_QUESTION_GEN',
                'detail': f"Growth stage {growth_stage} ({GROWTH_STAGES[min(growth_stage, 6)][1]}). "
                          f"Bloom cognitive level applied.",
            },
            {
                'step': 'KNOWLEDGE_BASE',
                'detail': f"KB queries: {self.knowledge.queries}. "
                          f"Concepts found in 22-topic graph: {', '.join(concepts[:2]) or 'none'}.",
            },
            {
                'step': 'PERSONALITY',
                'detail': f"Curiosity {self.personality.traits['curiosity']:.2f} | "
                          f"Analytical {self.personality.traits['analytical']:.2f} | "
                          f"Q-awareness {self.personality.traits['quantum_awareness']:.2f}.",
            },
            {
                'step': 'RESPONSE_ANALYZER',
                'detail': f"Analyses: {self.analyzer.analysis_count}. "
                          f"Avg score: {self.analyzer.get_average_score():.4f}.",
            },
        ]

        return steps

    def save_state(self, path: str):
        state = {
            'personality': {
                'traits': self.personality.traits,
                'interaction_count': self.personality.interaction_count,
                'current_stage': self.personality.current_stage,
            },
            'orch_or': {
                'orchestration': self.orch_or.orchestration,
                'temperature': self.orch_or.temperature,
                    'collapse_count': getattr(self.orch_or, 'conscious_moments', 0),
            },
            'total_interactions': self._total_interactions,
            'chaos_level': self.chaos.chaos_level,
        }
        os.makedirs(path, exist_ok=True)
        # Save Markov chain
        try:
            import pickle
            with open(os.path.join(path, "markov_state.pkl"), "wb") as mf:
                pickle.dump(self.markov.chain, mf)
        except Exception:
            pass
        with open(os.path.join(path, 'engine_state.json'), 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self, path: str) -> bool:
        state_file = os.path.join(path, 'engine_state.json')
        if not os.path.exists(state_file):
            return False
        try:
            with open(state_file) as f:
                state = json.load(f)
            if 'personality' in state:
                p = state['personality']
                self.personality.traits.update(p.get('traits', {}))
                self.personality.interaction_count = p.get('interaction_count', 0)
                self.personality.current_stage = p.get('current_stage', 0)
            self._total_interactions = state.get('total_interactions', 0)
            if 'chaos_level' in state:
                self.chaos.set_chaos_level(state['chaos_level'])
            if 'orch_or' in state:
                o = state['orch_or']
                if getattr(self, '_has_orch_or', False) and self.orch_or:
                    self.orch_or.orchestration = o.get('orchestration', 0.5)
                    self.orch_or.temperature = o.get('temperature', 1.02)
                    prior = o.get('collapse_count', 0)
                    if hasattr(self.orch_or, 'conscious_moments'):
                        self.orch_or.conscious_moments = prior
        except Exception:
            pass
        # Load Markov chain if saved
        try:
            import pickle
            mp = os.path.join(path, "markov_state.pkl")
            if os.path.exists(mp):
                with open(mp, "rb") as mf:
                    self.markov.chain = pickle.load(mf)
        except Exception:
            pass
            return True
        except Exception:
            return False


class ConceptExtractor:
    """Extracts concepts from text for knowledge graph updates."""
    def __init__(self):
        self.total_documents = 0
        self.word_frequencies = {}
        self.document_frequencies = {}

    def update_corpus_stats(self, text: str):
        self.total_documents += 1
        for word in text.lower().split():
            word = word.strip(".,!?;:'")
            if len(word) > 3:
                self.word_frequencies[word] = self.word_frequencies.get(word, 0) + 1
                self.document_frequencies[word] = self.document_frequencies.get(word, 0) + 1

    def extract_concepts(self, text: str, max_concepts: int = 10):
        words = [w.strip(".,!?;:'").lower() for w in text.split()]
        scored = {w: self.word_frequencies.get(w, 1) for w in words if len(w) > 3}
        top = sorted(scored.items(), key=lambda x: x[1], reverse=True)[:max_concepts]
        return [w for w, _ in top]

        bridges = []

        if cont_type == "follow_up":
            if shared:
                bridges = [
                    f"Still on {shared[0]} — the coherence holds.",
                    f"The thread continues through {shared[0]}.",
                    f"{shared[0].capitalize()} keeps resonating across exchanges.",
                    f"Following that thread — {shared[0]} hasn't fully collapsed yet."
                ]
            elif topic_thread:
                bridges = [
                    f"Connected to what we were circling — {topic_thread}.",
                    f"That links back. The {topic_thread} thread persists.",
                    f"The conversation's microtubules still carry {topic_thread}."
                ]
            else:
                bridges = [
                    "Building on what came before.",
                    "The prior collapse informs this one."
                ]

        if not bridges:
            bridges = ["Continuing the signal flow."]

        return random.choice(bridges)

