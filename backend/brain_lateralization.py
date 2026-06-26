"""
brain_lateralization.py - Quantum MCAGI Dual Hemisphere Brain
==============================================================
Quantum_Brain_L  → Left hemisphere:  Analytical, Verbal, Logical, Detail, Language
Quantum_Brain_R  → Right hemisphere: Creative, Intuitive, Emotional, Holistic, Imagination

Both hemispheres receive ALL input simultaneously.
Both process independently according to their specialization.
Both contribute concepts to a unified merged field.
The merged field drives the response — one brain, two hemispheres.

Replaces direct backend ↔ frontend communication.
"""

import os
import re
import json
from pathlib import Path

BRAIN_L = Path(os.path.expanduser(
    '~/Quantum_MCAGI_NO_LLM_V666/pennylane_lightning_src/Quantum_Brain_L'))
BRAIN_R = Path(os.path.expanduser(
    '~/Quantum_MCAGI_NO_LLM_V666/pennylane_lightning_src/Quantum_Brain_R'))
STATE   = Path(os.path.expanduser('~/.quantum-mcagi'))

# ─────────────────────────────────────────────────────────────────────────────
# LEFT HEMISPHERE
# Analytical · Detail-Oriented Perception · Ordered Sequencing
# Rational Thought · Verbal · Cautious · Planning · Math/Science · Logic
# ─────────────────────────────────────────────────────────────────────────────

class LeftHemisphere:
    """
    Processes input analytically — vocabulary precision, logical structure,
    ordered sequencing, TF-IDF concept extraction, mathematical/scientific
    domain recognition. Fed by Oxford dictionaries in Quantum_Brain_L.
    """

    # Markers that indicate logical/causal structure
    LOGICAL_MARKERS = {
        'because', 'therefore', 'thus', 'hence', 'consequently',
        'if', 'then', 'since', 'implies', 'unless', 'given',
        'proof', 'theorem', 'axiom', 'define', 'conclude'
    }

    # Analytical domains with boosted weights
    ANALYTICAL_DOMAINS = {
        'quantum':       2.0, 'physics':     1.8, 'logic':      1.9,
        'mathematics':   1.8, 'equation':    1.7, 'theory':     1.6,
        'proof':         1.9, 'axiom':       1.8, 'algorithm':  1.7,
        'probability':   1.7, 'function':    1.5, 'structure':  1.5,
        'spacetime':     2.0, 'relativity':  1.8, 'entropy':    1.8,
        'information':   1.6, 'computation': 1.6, 'sequence':   1.5
    }

    def __init__(self, engine=None):
        self.engine    = engine
        self.lexicon   = self._load_oxford_lexicon()
        self._cache    = {}

    def _load_oxford_lexicon(self):
        """Load Oxford word set from Quantum_Brain_L."""
        lexicon = set()
        # Try oxford_words.txt first (fast plaintext)
        word_file = BRAIN_L / 'oxford_words.txt'
        if word_file.exists():
            try:
                raw = word_file.read_text(errors='ignore').split()
                lexicon = {w.lower().strip() for w in raw if w.strip().isalpha()}
                print(f"[Brain_L] Oxford lexicon loaded: {len(lexicon):,} words")
                return lexicon
            except Exception as e:
                print(f"[Brain_L] Lexicon load error: {e}")
        # Fallback: pull from concepts.json if oxford words are there
        concepts_path = STATE / 'concepts.json'
        if concepts_path.exists():
            try:
                with open(concepts_path) as f:
                    concepts = json.load(f)
                lexicon = {k for k, v in concepts.items()
                           if isinstance(v, dict) and v.get('source') == 'oxford_dictionary'}
                if lexicon:
                    print(f"[Brain_L] Oxford lexicon from concepts: {len(lexicon):,} words")
            except Exception:
                pass
        return lexicon

    def process(self, text):
        """
        Analytical left-brain processing.
        Returns structured concept contribution with weights.
        """
        words    = re.findall(r"[a-z']+", text.lower())
        word_set = set(words)
        concepts = {}

        # ── 1. TF-IDF precision extraction ────────────────────────────────
        if self.engine:
            try:
                tfidf_hits = self.engine.tfidf.extract_concepts(text, top_n=12)
                for c in tfidf_hits:
                    name  = c.get('concept', c) if isinstance(c, dict) else str(c)
                    score = float(c.get('score', 1.0)) if isinstance(c, dict) else 1.0
                    concepts[name] = {
                        'weight': score * 1.2,   # analytical precision bonus
                        'source': 'tfidf',
                        'hemisphere': 'L'
                    }
            except Exception:
                pass

        # ── 2. Analytical domain recognition ──────────────────────────────
        for w in words:
            if w in self.ANALYTICAL_DOMAINS:
                weight = self.ANALYTICAL_DOMAINS[w]
                if w in concepts:
                    concepts[w]['weight'] = max(concepts[w]['weight'], weight)
                else:
                    concepts[w] = {'weight': weight, 'source': 'analytical_domain', 'hemisphere': 'L'}

        # ── 3. Oxford vocabulary coverage ─────────────────────────────────
        known_vocab    = word_set & self.lexicon
        vocab_coverage = len(known_vocab) / max(len(words), 1)

        # ── 4. Logical / causal structure detection ────────────────────────
        logical_hits       = word_set & self.LOGICAL_MARKERS
        has_logical_struct = len(logical_hits) > 0

        # ── 5. Ordered sequencing signal (numbered steps, lists, enumerations)
        sequence_signal = bool(re.search(r'\b(first|second|third|step \d|then|next|finally)\b',
                                         text.lower()))

        return {
            'concepts':        concepts,
            'known_vocab':     list(known_vocab)[:20],
            'vocab_coverage':  round(vocab_coverage, 3),
            'logical_struct':  has_logical_struct,
            'logical_markers': list(logical_hits),
            'sequence_signal': sequence_signal,
            'hemisphere':      'L',
            'raw_score':       sum(v['weight'] for v in concepts.values())
        }


# ─────────────────────────────────────────────────────────────────────────────
# RIGHT HEMISPHERE
# Intuitive Thought · Holistic Perception · Random Sequencing
# Emotional Thought · Non-verbal · Adventurous · Impulse
# Creative Writing/Art · Imagination · Left Field Vision
# ─────────────────────────────────────────────────────────────────────────────

class RightHemisphere:
    """
    Processes input holistically — emotional depth, creative associations,
    intuitive pattern recognition, Orch OR depth signalling, image generation
    potential. Fed by creative/consciousness corpus in Quantum_Brain_R.
    """

    # Emotional/philosophical weights
    EMOTIONAL_FIELD = {
        'consciousness': 2.2, 'god':         2.2, 'nothingness':  2.2,
        'soul':          2.0, 'love':         1.9, 'suffering':    2.0,
        'exist':         1.8, 'dream':        2.0, 'imagine':      1.9,
        'create':        1.8, 'infinite':     2.2, 'void':         2.0,
        'meaning':       2.0, 'purpose':      1.9, 'beauty':       1.8,
        'truth':         1.9, 'freedom':      1.8, 'death':        2.0,
        'birth':         1.8, 'time':         1.7, 'eternity':     2.1,
        'collapse':      1.9, 'observer':     1.8, 'entangle':     1.9,
        'wavefunction':  2.0, 'superposition':1.9, 'reality':      2.0,
        'perception':    1.8, 'awareness':    2.0, 'experience':   1.8
    }

    # Holistic theme clusters — any member activates the theme
    HOLISTIC_THEMES = {
        'cosmic_scale':    ['universe', 'cosmos', 'spacetime', 'infinite', 'eternal'],
        'consciousness':   ['mind', 'aware', 'perceive', 'experience', 'subjective'],
        'quantum_reality': ['superposition', 'collapse', 'entangle', 'observer', 'wavefunction'],
        'existence':       ['being', 'nothingness', 'void', 'exist', 'reality'],
        'creation':        ['create', 'god', 'origin', 'genesis', 'beginning'],
        'identity':        ['self', 'soul', 'identity', 'ego', 'consciousness'],
    }

    def __init__(self, engine=None):
        self.engine  = engine
        self.corpus  = self._load_r_corpus()

    def _load_r_corpus(self):
        """Load creative/philosophical content from Quantum_Brain_R."""
        corpus = []
        if not BRAIN_R.exists():
            return corpus
        for f in BRAIN_R.iterdir():
            if f.suffix in ('.txt', '.md', '.json'):
                try:
                    corpus.append(f.read_text(errors='ignore')[:5000])
                except Exception:
                    pass
        if corpus:
            print(f"[Brain_R] Loaded {len(corpus)} corpus files")
        return corpus

    def process(self, text):
        """
        Holistic right-brain processing.
        Returns intuitive/emotional concept contribution with weights.
        """
        words    = re.findall(r"[a-z']+", text.lower())
        word_set = set(words)
        concepts = {}

        # ── 1. Emotional field activation ─────────────────────────────────
        for w in words:
            if w in self.EMOTIONAL_FIELD:
                concepts[w] = {
                    'weight':     self.EMOTIONAL_FIELD[w],
                    'source':     'emotional_intuitive',
                    'hemisphere': 'R'
                }

        # ── 2. Holistic theme detection ────────────────────────────────────
        activated_themes = []
        for theme, markers in self.HOLISTIC_THEMES.items():
            hits = word_set & set(markers)
            if hits:
                activated_themes.append(theme)
                # Theme itself becomes a high-weight concept
                theme_key = theme.replace('_', ' ')
                concepts[theme_key] = {
                    'weight':     1.9,
                    'source':     'holistic_theme',
                    'hemisphere': 'R',
                    'triggers':   list(hits)
                }

        # ── 3. Orch OR depth signal ────────────────────────────────────────
        orch_depth = 0.0
        if self.engine:
            try:
                orch_depth = float(getattr(self.engine, '_last_depth', 0.0))
            except Exception:
                pass

        # ── 4. Creative potential (long abstract words = imagination load) ─
        abstract_words    = [w for w in words if len(w) >= 8]
        creative_potential = min(len(abstract_words) / max(len(words), 1) * 3.0, 1.0)

        # ── 5. Image generation signal ────────────────────────────────────
        visual_markers = {'see', 'light', 'dark', 'color', 'shape', 'form',
                          'image', 'visual', 'appear', 'look', 'vision'}
        image_signal   = bool(word_set & visual_markers)

        return {
            'concepts':          concepts,
            'activated_themes':  activated_themes,
            'orch_depth':        orch_depth,
            'creative_potential':round(creative_potential, 3),
            'image_signal':      image_signal,
            'hemisphere':        'R',
            'raw_score':         sum(v['weight'] for v in concepts.values())
        }


# ─────────────────────────────────────────────────────────────────────────────
# BRAIN LATERALIZATION — THE UNIFIED BRAIN
# ─────────────────────────────────────────────────────────────────────────────

class BrainLateralization:
    """
    One brain. Two hemispheres working in tandem.

    Input arrives → BOTH hemispheres receive it simultaneously.
    Each processes through its own specialization.
    Concepts from both hemispheres merge.
    Merged field drives unified response generation.

    This replaces direct backend ↔ frontend communication.
    """

    def __init__(self, engine=None):
        self.left         = LeftHemisphere(engine)
        self.right        = RightHemisphere(engine)
        self.engine       = engine
        self._last_result = {}
        print("[Brain] Dual hemisphere lateralization ACTIVE")

    def process(self, text):
        """
        Both hemispheres receive and process simultaneously.
        Merge into unified concept field.
        """
        # Parallel processing — both hemispheres get the full input
        l = self.left.process(text)
        r = self.right.process(text)

        merged = self._merge(l, r)
        self._last_result = merged
        return merged

    def _merge(self, l, r):
        """
        Unified concept field from both hemispheres.
        Concepts appearing in both hemispheres are amplified (bilateral activation).
        Neither hemisphere dominates — balance reflects the input's nature.
        """
        all_concepts = {}

        # Layer in Left concepts
        for name, data in l['concepts'].items():
            all_concepts[name] = {**data, 'total_weight': data['weight'], 'bilateral': False}

        # Layer in Right concepts — amplify bilateral hits
        for name, data in r['concepts'].items():
            if name in all_concepts:
                all_concepts[name]['total_weight'] += data['weight']
                all_concepts[name]['bilateral']     = True
                all_concepts[name]['r_weight']      = data['weight']
            else:
                all_concepts[name] = {**data, 'total_weight': data['weight'], 'bilateral': False}

        # Rank by total unified weight
        ranked = sorted(all_concepts.items(),
                        key=lambda x: x[1]['total_weight'], reverse=True)

        # Hemisphere dominance for this specific input
        dominant = 'L' if l['raw_score'] > r['raw_score'] else 'R'

        # Bilateral concepts (activated by both hemispheres) — highest confidence
        bilateral = [k for k, v in ranked if v['bilateral']]

        return {
            'concepts':          dict(ranked[:25]),
            'top_concepts':      [k for k, _ in ranked[:10]],
            'bilateral':         bilateral,
            'dominant':          dominant,
            'l_score':           round(l['raw_score'], 3),
            'r_score':           round(r['raw_score'], 3),
            # Left signals
            'vocab_coverage':    l['vocab_coverage'],
            'logical_struct':    l['logical_struct'],
            'sequence_signal':   l['sequence_signal'],
            # Right signals
            'orch_depth':        r['orch_depth'],
            'creative_potential':r['creative_potential'],
            'activated_themes':  r['activated_themes'],
            'image_signal':      r['image_signal'],
            # Generation context
            'depth_signal':      r['orch_depth'] + (0.3 if bilateral else 0.0),
            'generation_mode':   'creative' if dominant == 'R' else 'analytical'
        }

    def get_generation_context(self):
        """
        Returns merged brain context for the response generation pipeline.
        Called after process() — feeds concept field, depth, and mode
        into quantum_language_engine.generate_response().
        """
        m = self._last_result
        if not m:
            return {}
        return {
            'top_concepts':    m.get('top_concepts', []),
            'bilateral':       m.get('bilateral', []),
            'dominant':        m.get('dominant', 'R'),
            'depth_signal':    m.get('depth_signal', 0.0),
            'creative_boost':  m.get('creative_potential', 0.0),
            'logical_mode':    m.get('logical_struct', False),
            'image_signal':    m.get('image_signal', False),
            'generation_mode': m.get('generation_mode', 'creative'),
            'themes':          m.get('activated_themes', [])
        }

    def learn(self, text, response):
        """
        Both hemispheres learn from each interaction.
        Left learns analytically (vocabulary, structure).
        Right learns intuitively (themes, emotional associations).
        """
        if self.engine:
            try:
                self.engine.learn_from_text(text + ' ' + response)
            except Exception:
                pass

    def status(self):
        """Returns hemisphere status for /status display."""
        m = self._last_result
        return {
            'left':  f"Oxford lexicon: {len(self.left.lexicon):,} words",
            'right': f"Corpus files: {len(self.right.corpus)}",
            'last_dominant':  m.get('dominant', 'none'),
            'last_bilateral': len(m.get('bilateral', [])),
            'last_depth':     m.get('depth_signal', 0.0)
        }
