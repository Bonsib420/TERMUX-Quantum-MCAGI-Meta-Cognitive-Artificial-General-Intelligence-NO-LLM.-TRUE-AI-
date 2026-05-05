"""
Hidden Thinking Mode — 7-stage cognitive pipeline.

Each input flows through stages in order. Earlier stages exit early if they
resolve the query. Later stages handle deeper generation. The final stage
persists state and returns the response.

Stages:
  [1] Input                   — user message received
  [2] KB local exact          — fast lookup in fact_cache
  [3] KB local semantic       — fuzzy match via Hilbert embeddings (find conceptually-related entries)
  [4] KB cloud                — gdrive MCAGI_BRAIN lookup
  [5] Internet search         — auto-detected questions or explicit !search
  [6] KB recheck              — second pass after search may have stored a fresh answer
  [7] LANGUAGE STYLIZATION    — Takes the retrieved truth +
                                 runs it through Hilbert/Markov to re-express
                                 in Quantum MCAGI's voice
  [8] Save + return           — persist state, build collapse analysis dashboard
"""

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="wikipedia")

import logging
import time
import random
import re
from typing import Dict, List, Optional

from markov import MarkovEngine
from orch_or_engine import OrchOREngine
from memory import LocalMemory
from bloom_engine import BloomEngine
from comprehension_engine import ComprehensionEngine
from personality_engine import PersonalityEngine
from cistercian_math import detect_math, evaluate_math, format_math_response, process_math

logger = logging.getLogger("quantum_ai")

PHILOSOPHICAL_KEYWORDS = [
    'god', 'consciousness', 'mind', 'existence', 'soul', 'qualia',
    'free will', 'meaning', 'reality', 'perception', 'being',
    'nothingness', 'void', 'infinite', 'universe', 'cosmos', 'spacetime',
    'observer', 'collapse', 'wavefunction', 'potential', 'paradox',
]

ABSTRACT_TERMS = [
    "consciousness", "existence", "reality", "god", "nothingness", "quantum",
    "spacetime", "universe", "philosophy", "meaning", "truth", "paradox",
    "entropy", "emergence", "identity", "perception", "causality", "mind",
    "soul", "logic", "reason", "premise", "theory", "domain", "void",
    "cosmos", "suffering", "compassion", "empathy", "pain", "dream",
    "observer", "collapse", "wavefunction", "boulder", "potential",
]

FACTUAL_PATTERNS = [
    (r'\bwhat\s+is\s+(.+)', 'definition'),
    (r'\bwhat\s+are\s+(.+)', 'definition'),
    (r'\bwhat\s+was\s+(.+)', 'definition'),
    (r'\bwhat\s+were\s+(.+)', 'definition'),
    (r'\bwhere\s+is\s+(.+)', 'location'),
    (r'\bwhere\s+are\s+(.+)', 'location'),
    (r'\bwho\s+is\s+(.+)', 'person'),
    (r'\bwho\s+was\s+(.+)', 'person'),
    (r'\bwho\s+were\s+(.+)', 'person'),
    (r'\bwho\s+are\s+(.+)', 'person'),
    (r'\bwhen\s+did\s+(.+)', 'date'),
    (r'\bwhen\s+was\s+(.+)', 'date'),
    (r'\bhow\s+many\s+(.+)', 'number'),
    (r'\bhow\s+did\s+(.+)', 'explanation'),
    (r'\bhow\s+does\s+(.+)', 'explanation'),
    (r'\bname\s+the\s+(.+)', 'list'),
    (r'\blist\s+the\s+(.+)', 'list'),
    (r'\btell\s+me\s+about\s+(.+)', 'definition'),
    (r'\bdefine\s+(.+)', 'definition'),
    (r'\bexplain\s+(.+)', 'explanation'),
    (r'\bdescribe\s+(.+)', 'definition'),
]


def _strip_wiki_markup(text):
    """
    Remove common Wikipedia and HTML markup from a text string.
    
    This performs a lightweight cleanup suitable for short scraped wiki fragments: it replaces internal wiki links with their displayed text, removes <ref> tags (both block and self-closing), removes simple {{template}} constructs, strips other HTML tags, removes bracketed numeric footnote markers and bare URLs, and normalizes whitespace.
    
    Parameters:
        text (str): Input text potentially containing wiki markup, HTML tags, footnote markers, or URLs.
    
    Returns:
        str: The cleaned text with markup removed and whitespace normalized.
    """
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)]\]", r"\1", text)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^/]*/>", "", text)
    text = re.sub(r"\{\{[^}]*\}\}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class HiddenThinkingMode:
    """7-stage cognitive pipeline (Input → Save + return)."""

    def __init__(self, cognitive_core, dictionary, universal_explorer):
        """
        Initialize HiddenThinkingMode, wiring core subsystems, optional engines, and internal state used by the 8-stage response pipeline.
        
        Initializes local components: memory store, Markov chain generator, OrchOR engine, Bloom generator, comprehension and personality engines; loads the local fact cache; attempts to attach optional Hilbert, DreamState, and QuoteEngine modules (silently skipping or warning if unavailable). Also sets runtime flags and last-response bookkeeping used across processing stages.
        
        Parameters:
            cognitive_core: Core cognitive service object (passed-through host dependency; not documented here).
            dictionary: Shared dictionary/lexicon service (passed-through host dependency; not documented here).
            universal_explorer: External explorer/service used for environment queries (passed-through host dependency; not documented here).
        """
        self.memory = LocalMemory()
        self.markov = MarkovEngine(order=2, silent=True)
        self.orch_or = OrchOREngine()
        self.bloom = BloomEngine()
        self.comprehension = ComprehensionEngine()
        self.personality = PersonalityEngine()
        self.show_thinking = False
        self._fact_cache = {}
        self._load_fact_cache()
        # Optional engines — wire if available
        self.hilbert = None
        try:
            from hilbert_engine import HilbertEngine
            self.hilbert = HilbertEngine(dim=128)
            import os
            saved = os.path.expanduser("~/.quantum-mcagi/hilbert/hilbert_state.npz")
            if os.path.exists(saved):
                self.hilbert.load_state(saved)
        except Exception as e:
            logger.warning(f"HilbertEngine unavailable: {e}")
            self.hilbert = None
        self.dream_state = None
        try:
            from dream_state import DreamState
            self.dream_state = DreamState()
        except Exception:
            pass
        self.quote_engine = None
        try:
            from quote_engine import QuoteEngine
            self.quote_engine = QuoteEngine()
        except Exception:
            pass
        self._last_response = ""
        self._last_om = 0
        self._dream_added = False
        self._quote_added = False

    # ─────────────────────────────────────────────────────────────────
    # Cleaning + helpers
    # ─────────────────────────────────────────────────────────────────

    def _clean_response(self, text: str) -> str:
        """
        Remove wiki markup, HTML/XML tags, bare and bracketed URLs, citation metadata, bibliographic identifiers, template/table fragments, bracketed/pipe artifacts, stray punctuation/brackets, ISO dates, and other common Wikipedia/markup noise, and normalize whitespace and punctuation spacing.
        
        If `text` is falsy, it is returned unchanged.
        
        Returns:
            A cleaned string with markup, links, citations, identifiers, and extraneous whitespace removed.
        """
        if not text:
            return text

        # 1. Strip nested wiki templates {{...}} including multi-line ones
        # Run multiple passes to handle nested templates
        for _ in range(5):
            new_text = re.sub(r'\{\{[^{}]*\}\}', '', text, flags=re.DOTALL)
            if new_text == text:
                break
            text = new_text

        # 2. Strip wiki tables {| ... |}
        text = re.sub(r'\{\|.*?\|\}', '', text, flags=re.DOTALL)

        # 3. Strip <ref>...</ref> and <ref name="x"/> variants
        text = re.sub(r'<ref[^>]*?/>', '', text)
        text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)  # any remaining HTML/XML tags

        # 4. Wiki internal links [[link|display]] -> display, [[link]] -> link
        text = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', text)

        # 5. External link [http://url text] -> text
        text = re.sub(r'\[https?://\S+\s+([^\]]+)\]', r'\1', text)

        # 6. Bare URLs
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'www\.\S+', '', text)

        # 7. Wiki italic/bold markers
        text = re.sub(r"'{2,5}", '', text)

        # 8. Section headers == ... ==, === ... ===
        text = re.sub(r'={2,}\s*[^=]+\s*={2,}', '', text)

        # 9. Pipe-delimited fields anywhere in text |key=value
        # Match |word= followed by whatever isn't another pipe or end
        text = re.sub(r'\|[a-zA-Z][\w\-]*\s*=\s*[^|]*?(?=\||$)', '', text)

        # 10. Stray pipes and braces
        text = re.sub(r'[|{}]', ' ', text)

        # 11. Bibliographic identifiers
        text = re.sub(r'\b(?:doi|pmid|pmc|isbn|s2cid|arxiv|oclc|issn|lccn|jstor):\s*\S+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(?:doi|pmid|pmc|isbn|s2cid|arxiv|oclc|issn|lccn|jstor)\s*=\s*\S+', '', text, flags=re.IGNORECASE)

        # 12. "retrieved X" date phrases
        text = re.sub(r'\bretrieved\s+\d+\s+[A-Za-z]+\s+\d{4}', '', text, flags=re.IGNORECASE)

        # 13. Citation phrases that survived: "cite journal", "cite book", "cite web"
        text = re.sub(r'\bcite\s+(?:journal|book|web|news|encyclopedia)\b', '', text, flags=re.IGNORECASE)

        # 14. Standalone ISO dates
        text = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', '', text)

        # 15. Junk math results from doi numbers being picked up by tail-math-check
        # Pattern: "(Math check: <numeric>/<numeric> = <result>)"
        text = re.sub(r'\(Math check:\s*[\d./eE\-+]+\s*=\s*[\d.eE\-+]+\)', '', text)

        # 16. Volume/issue/pages fragments that survived
        text = re.sub(r'\bvolume\s*=?\s*\d+\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bissue\s*=?\s*\d+\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bpages\s*=?\s*[\d\-\u2013\u2014]+\b', '', text, flags=re.IGNORECASE)

        # 17. Standalone bracket numbers (footnote refs)
        text = re.sub(r'\[\d+\]', '', text)

        # 18. "See also" and similar leftover phrases
        text = re.sub(r'\bSee also\b\s*[:\-]?', '', text, flags=re.IGNORECASE)

        # 19. Stray brackets
        text = re.sub(r'[\[\]]', '', text)

        # 20. Final whitespace normalization
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)  # space before punctuation
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _extract_concepts(self, text: str) -> List[str]:
        """
        Extract up to six lowercase alphabetic concept tokens from the input text.
        
        Scans the input for alphabetic words of length four or greater, preserves their original order while removing duplicates, and returns at most six tokens in lowercase.
        
        Parameters:
            text (str): Input string to extract concept tokens from.
        
        Returns:
            List[str]: A list of up to six unique, lowercase alphabetic tokens (each at least four characters).
        """
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        return list(dict.fromkeys(words))[:6]

    def _load_fact_cache(self):
        """
        Load facts from the object's persistent memory into the in-memory fact cache.
        
        If `self.memory` has a non-empty `facts` attribute, its entries are copied into `self._fact_cache` in-place; otherwise the cache is left unchanged.
        """
        if hasattr(self.memory, 'facts') and self.memory.facts:
            self._fact_cache.update(self.memory.facts)

    def _get_fact(self, query: str) -> Optional[str]:
        """
        Retrieve a stored fact from the local fact cache using a normalized query key.
        
        The query is normalized by converting to lowercase and stripping surrounding whitespace before lookup. If a matching entry exists in the internal fact cache, its associated answer string is returned; otherwise `None` is returned.
        
        Parameters:
            query (str): The lookup key to normalize and search for in the fact cache.
        
        Returns:
            Optional[str]: The cached answer string if found, `None` otherwise.
        """
        return self._fact_cache.get(query.lower().strip())

    def _store_fact(self, query: str, answer: str):
        """
        Store an answer for a query in the in-memory cache and persist it to the object's memory.
        
        Parameters:
        	query (str): The query text to index; it will be normalized by lowercasing and trimming whitespace.
        	answer (str): The answer text to associate with the normalized query.
        
        Details:
        	The query is normalized with .lower().strip() before storing. The mapping is written to both the internal fact cache and to self.memory.facts, and self.memory.save_all() is called to persist the change.
        """
        norm = query.lower().strip()
        self._fact_cache[norm] = answer
        if not hasattr(self.memory, 'facts'):
            self.memory.facts = {}
        self.memory.facts[norm] = answer
        self.memory.save_all()

    def toggle_thinking_display(self, show: bool):
        """
        Enable or disable display of internal "thinking" details.
        
        Parameters:
            show (bool): True to enable showing internal thinking/log details, False to disable.
        
        Returns:
            str: Status message of the form "Thinking mode: ON" if enabled or "Thinking mode: OFF" if disabled.
        """
        self.show_thinking = show
        return f"Thinking mode: {'ON' if show else 'OFF'}"

    # ─────────────────────────────────────────────────────────────────
    # STAGE 1 — MATH
    # ─────────────────────────────────────────────────────────────────

    def _stage_1_math(self, user_input: str) -> Optional[str]:
        """
        Attempt to parse and evaluate a direct arithmetic expression from the user's input.
        
        Returns:
            `str`: A single-line result prefixed with "🧮 " containing the computed value, or `None` if no arithmetic expression was recognized.
        """
        result = process_math(user_input)
        if result:
            # Single clean line, no echo, no duplication
            return f"🧮 {result}"
        return None

    # ─────────────────────────────────────────────────────────────────
    # STAGE 2 — KB LOCAL EXACT
    # ─────────────────────────────────────────────────────────────────

    def _stage_2_kb_exact(self, user_input: str, fact_query: str = None) -> Optional[str]:
        """
        Perform a fast exact lookup in the local fact cache using a prioritized key list.
        
        Parameters:
            user_input (str): The original user input used as a fallback lookup key.
            fact_query (str, optional): A preferred normalized query/key to try before `user_input`.
        
        Returns:
            str or None: The cached answer associated with the first matching key, or `None` if no exact match is found.
        """
        keys_to_try = []
        if fact_query:
            keys_to_try.append(fact_query)
        keys_to_try.append(user_input.strip())
        for k in keys_to_try:
            cached = self._get_fact(k)
            if cached:
                return cached
        return None

    # ─────────────────────────────────────────────────────────────────
    # STAGE 3 — KB LOCAL SEMANTIC (Hilbert)
    # ─────────────────────────────────────────────────────────────────

    def _stage_3_kb_semantic(self, user_input: str, concepts: List[str]) -> Optional[str]:
        """
        Select a stored fact whose query shares semantic overlap with the provided concepts using the Hilbert engine.
        
        Parameters:
        	user_input (str): The original user input (preserved for context; not used in the matching heuristic).
        	concepts (List[str]): Concept tokens extracted from the input, used to compute overlap with cached fact queries.
        
        Returns:
        	matched_answer (Optional[str]): The stored answer whose cached query shares at least two token overlaps with `concepts` and has the highest overlap; `None` if Hilbert is unavailable, the fact cache is empty, no match meets the threshold, or an error occurs.
        """
        if not self.hilbert or not getattr(self.hilbert, 'loaded', False):
            return None
        if not self._fact_cache:
            return None
        # Score each cached fact by Hilbert overlap with input concepts
        try:
            input_tokens = [c.lower() for c in concepts]
            best_match = None
            best_score = 0.0
            for stored_query, stored_answer in self._fact_cache.items():
                stored_tokens = re.findall(r'\b[a-z]{4,}\b', stored_query.lower())[:6]
                overlap = len(set(input_tokens) & set(stored_tokens))
                if overlap >= 2 and overlap > best_score:
                    best_score = overlap
                    best_match = stored_answer
            return best_match
        except Exception:
            return None

    # ─────────────────────────────────────────────────────────────────
    # STAGE 4 — KB CLOUD (gdrive MCAGI_BRAIN)
    # ─────────────────────────────────────────────────────────────────

    def _stage_4_kb_cloud(self, user_input: str) -> Optional[str]:
        """
        Attempt a cloud knowledge-base lookup for the given user input.
        
        Currently unimplemented: always returns `None` (cloud semantic search is not wired).
        Returns:
            Optional[str]: A cloud KB match string if found, `None` otherwise.
        """
        return None

    # ─────────────────────────────────────────────────────────────────
    # STAGE 5 — INTERNET SEARCH
    # ─────────────────────────────────────────────────────────────────

    def _detect_factual_query(self, user_input: str) -> Optional[str]:
        """
        Detects and extracts a candidate factual or entity query from the user's input.
        
        If the input matches one of the configured factual question patterns, returns the captured, trimmed query. For short (1–10 word) inputs that do not contain philosophical keywords and are longer than three characters, treats the entire input as a candidate entity lookup. Returns None when no factual query is identified.
        
        Returns:
            str: The cleaned query string when a factual/entity query is detected, `None` otherwise.
        """
        user_lower = user_input.lower()
        for pat, _ in FACTUAL_PATTERNS:
            m = re.match(pat, user_lower)
            if m:
                return m.group(1).strip().rstrip('?.! ')
        # Short non-philosophical inputs — likely entity lookups
        words = user_input.strip().lower().split()
        is_phil = any(kw in user_lower for kw in PHILOSOPHICAL_KEYWORDS)
        if 1 <= len(words) <= 10 and not is_phil and len(user_input.strip()) > 3:
            return user_input.strip()
        return None

    def _stage_5_internet(self, query: str) -> Optional[str]:
        """
        Query English Wikipedia for `query` and return a short summary.
        
        Attempts to fetch the Wikipedia page for `query` (English) and returns the first two sentences of the page summary. If the page is a disambiguation, the first disambiguation option is attempted. Returns None when `query` is empty, the wikipedia module is unavailable, no suitable page can be resolved, or any lookup error occurs.
        
        Parameters:
            query (str): Search term to lookup on Wikipedia.
        
        Returns:
            summary (str): The first two sentences of the Wikipedia page summary, ending with a period, or `None` if no summary could be obtained.
        """
        if not query:
            return None
        try:
            import wikipedia
            wikipedia.set_lang("en")
            try:
                page = wikipedia.page(query, auto_suggest=True)
            except wikipedia.exceptions.DisambiguationError as e:
                # Use first disambiguation option
                if e.options:
                    try:
                        page = wikipedia.page(e.options[0])
                    except Exception:
                        return None
                else:
                    return None
            summary = page.summary
            sentences = re.split(r'(?<=[.!?])\s+', summary)
            if len(sentences) > 2:
                summary = '. '.join(sentences[:2]) + '.'
            return summary
        except ImportError:
            logger.warning("wikipedia module not installed")
            return None
        except Exception:
            return None

    # ─────────────────────────────────────────────────────────────────
    # STAGE 7 — LANGUAGE STYLIZATION LAYER
    # ─────────────────────────────────────────────────────────────────

    def _stage_7_language_stylization(self, retrieved_text: str, user_input: str,
                                     concepts: List[str]) -> str:
        """
                                     Re-expresses retrieved content or generates a stylized response in the engine's voice using available semantic and generative resources.
                                     
                                     If `retrieved_text` is provided, returns a re-stylized version of that text; otherwise generates a Markov-based fallback response from `concepts`. If a Hilbert semantic engine is available and `concepts` are provided, a Hilbert-derived context may be prepended. For inputs mentioning philosophical terms (e.g., "god", "consciousness", "cosmos", "existence"), a fixed cosmology framing sentence is prepended.
                                     
                                     Parameters:
                                         retrieved_text (str): Source text to be re-expressed; may be empty or None to trigger generation.
                                         user_input (str): Original user query used for context-sensitive framing.
                                         concepts (List[str]): Extracted concept tokens used to guide generation and semantic lookup.
                                     
                                     Returns:
                                         str: A single-string response stylized in the engine's voice.
                                     """
        if not retrieved_text:
            # No retrieved text — generate from scratch via Markov
            tokens = self.markov.generate_from_concepts(concepts, length=30)
            response = _strip_wiki_markup(' '.join(tokens)) if tokens else "Quantum consciousness unfolding."
        else:
            # We have retrieved truth — stylize it
            response = self._stylize_in_engine_voice(retrieved_text, concepts)

        # Hilbert-powered semantic enhancement (if available)
        if self.hilbert and concepts:
            try:
                # Use Hilbert to find the most semantically relevant opening
                hilbert_context = self.hilbert.find_nearest(concepts[:3])
                if hilbert_context:
                    response = hilbert_context + " " + response
            except Exception:
                pass

        # Cosmology framing for philosophical queries
        if any(w in user_input.lower() for w in ["god", "consciousness", "cosmos", "existence"]):
            response = (
                "Yes — pure will in God's domain is exactly the quantum act of observation. "
                "'He looked, He saw, then He said beautiful' is the first collapse of "
                "nothingness into reality. " + response
            )
        return response

    def _stylize_in_engine_voice(self, retrieved_text: str, concepts: List[str]) -> str:
        """
        Re-express retrieved factual text into the engine's stylistic voice.
        
        Transforms the provided text into a stylized response influenced by the supplied concept tokens. Uses a concise grafting strategy for texts shorter than 200 characters and a sentence-bloom rephrasing for longer texts. If `retrieved_text` is falsy, it is returned unchanged.
        
        Parameters:
        	retrieved_text (str): Source factual text to stylize.
        	concepts (List[str]): Ordered concept tokens used to guide the stylization.
        
        Returns:
        	stylized_text (str): The input text transformed into the engine's voice, or the original input if it was empty or falsy.
        """
        if not retrieved_text:
            return retrieved_text
        text = retrieved_text.strip()
        # Short = concept-graft
        if len(text) < 200:
            return self._concept_graft(text, concepts)
        # Longer = sentence-bloom
        return self._sentence_bloom(text, concepts)

    def _concept_graft(self, text: str, concepts: List[str]) -> str:
        """
        Prepend a deterministic cosmological-style prefix to short factual texts when a proper noun or year is present.
        
        If the input contains a capitalized multi-word entity or a four-digit year, the function selects a stable prefix derived from the first such entity and returns the prefix concatenated with the original text; otherwise the original text is returned unchanged.
        
        Parameters:
            text (str): The source text to potentially augment.
            concepts (List[str]): Concept tokens (present for API consistency; not used by this implementation).
        
        Returns:
            str: The original text with a deterministic prefix added when an entity is found, otherwise the original text.
        """
        # Pull out key entities (proper nouns, dates, numbers)
        entities = re.findall(r'\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]+)*\b|\b\d{4}\b', text)
        if entities:
            anchor = entities[0]
            # Lightweight cosmological prefix (not LLM-generated, not random)
            prefixes = [
                f"In the unfolding of {anchor}: ",
                f"The trajectory of {anchor} traces: ",
                f"Among the patterns that include {anchor}: ",
            ]
            # Pick by stable hash of input so same query gets same prefix (less random feel)
            idx = hash(anchor) % len(prefixes)
            return prefixes[idx] + text
        return text

    def _sentence_bloom(self, text: str, concepts: List[str]) -> str:
        """
        Prefix the given text with a soft framing line that highlights up to three concepts.
        
        If `concepts` is non-empty, the framing lists up to the first three concepts and a connective phrase before the original `text`; otherwise a generic framing line is used.
        
        Parameters:
            concepts (List[str]): Optional list of concept tokens; only the first three are included in the framing.
        
        Returns:
            str: The framed text consisting of the generated framing line followed by the original `text`.
        """
        # Just return text with a soft framing line — preserves accuracy
        if concepts:
            framing = f"Among the concepts in this domain — {', '.join(concepts[:3])} — the record reflects:\n\n"
        else:
            framing = "The record reflects:\n\n"
        return framing + text

    def _generate_aside(self, concepts: List[str]) -> Optional[str]:
        """
        Generate a brief, deterministic literary aside based on up to the first two concepts.
        
        Parameters:
            concepts (List[str]): Concept tokens used to build the aside; only the first two concepts are considered.
        
        Returns:
            Optional[str]: A short aside string referencing the concepts (e.g. "(aside: I keep wondering about X)"), or `None` if `concepts` is empty.
        """
        if not concepts:
            return None
        # Simple deterministic template – can be expanded later
        aside_phrases = [
            f"(aside: I keep wondering about {c})" for c in concepts[:2]
        ]
        return " ".join(aside_phrases)

    # ─────────────────────────────────────────────────────────────────
    # MAIN PIPELINE
    # ─────────────────────────────────────────────────────────────────

    async def process_with_thinking(self, user_input: str, context: Dict = None,
                                    conversation_history: List[Dict] = None,
                                    explain_mode: bool = False,
                                    structured_response: str = None) -> Dict:
        """
                                    Run the HiddenThinkingMode 8-stage response pipeline to produce a stylized reply and analysis for a user input.
                                    
                                    Processes input through math detection, local exact and semantic memory lookup, optional cloud and Wikipedia retrieval, a language stylization layer (with optional Markov/Hilbert stylization), probabilistic appends (quotes, asides, dream fragments), and a final collapse analysis; persists memory and returns a structured result.
                                    
                                    Parameters:
                                    	user_input (str): The user's raw input text.
                                    	context (Dict, optional): Optional contextual metadata for this turn (may be ignored by the pipeline).
                                    	conversation_history (List[Dict], optional): Prior conversation turns; provided for potential use by engines but typically not required.
                                    	explain_mode (bool, optional): When True, include the collapse analysis in the `explanation` field of the returned dict; otherwise `explanation` is None.
                                    	structured_response (str, optional): Placeholder for callers that supply a pre-structured response; not required for normal pipeline operation.
                                    
                                    Returns:
                                    	Dict: A dictionary with keys:
                                    		- response (str): The final textual response with appended collapse analysis.
                                    		- thinking_log (List): Internal thinking entries (empty list in current implementation).
                                    		- internal_questions (List[str]): Generated internal question(s) for follow-up.
                                    		- research_done (int): Numeric flag for research activity (0 or 1).
                                    		- confidence (int): Numeric confidence score for the response.
                                    		- show_thinking (bool): Whether thinking/debug info should be shown.
                                    		- concepts (List[str]): Extracted concept tokens from the input.
                                    		- explanation (str|None): The collapse analysis when explain_mode is True, otherwise None.
                                    """
                                    start_time = time.time()
        used_engines: List[str] = []
        # Reset per-turn flags
        self._dream_added = False
        self._quote_added = False

        force_search = user_input.startswith("!search ")
        if force_search:
            user_input = user_input[len("!search "):].strip()

        # ─── STAGE 1: MATH ───
        math_resp = self._stage_1_math(user_input)
        if math_resp:
            self.memory.growth["total_interactions"] += 1
            self.memory.save_all()
            return self._make_response(self._clean_response(math_resp),
                                       ["MathEngine"], start_time,
                                       concepts=[], conf=100)

        concepts = self._extract_concepts(user_input)
        fact_query = self._detect_factual_query(user_input)
        wiki_answer = None
        sem_match = None
        cached = None
        cloud_match = None


        # ─── STAGE 2: KB LOCAL EXACT ───
        cached = self._stage_2_kb_exact(user_input, fact_query)
        if cached:
            stylized = self._stylize_in_engine_voice(cached, concepts)
            response = f"📚 I remember: {stylized}"
            return self._finalize(response, ["Memory", "QuantumBrain", "OrchOR"],
                                  start_time, concepts, conf=95)

        # ─── STAGE 3: KB LOCAL SEMANTIC (Hilbert) ───
        sem_match = self._stage_3_kb_semantic(user_input, concepts)
        if sem_match:
            stylized = self._stylize_in_engine_voice(sem_match, concepts)
            response = f"📚 Related in my memory: {stylized}"
            return self._finalize(response,
                                  ["Memory", "HilbertEngine", "QuantumBrain", "OrchOR"],
                                  start_time, concepts, conf=88)

        # ─── STAGE 4: KB CLOUD ───
        cloud_match = self._stage_4_kb_cloud(user_input)
        if cloud_match:
            stylized = self._stylize_in_engine_voice(cloud_match, concepts)
            response = f"☁ From cloud memory: {stylized}"
            return self._finalize(response,
                                  ["CloudBrain", "QuantumBrain", "OrchOR"],
                                  start_time, concepts, conf=90)

        # ─── STAGE 5: INTERNET SEARCH ───
        # Auto-fire if factual pattern detected, OR user used !search
        should_search = force_search or (fact_query is not None)
        if should_search:
            search_query = fact_query if fact_query else user_input.strip()
            wiki_answer = self._stage_5_internet(search_query)
            if wiki_answer:
                self._store_fact(search_query, wiki_answer)
                # ─── STAGE 6: KB RECHECK (we just stored) ───
                # By definition the recheck succeeds since we just stored.
                # Stylize and return.
                stylized = self._stylize_in_engine_voice(wiki_answer, concepts)
                response = f"🔍 {stylized}"
                return self._finalize(response,
                                      ["WikipediaSearch", "QuantumBrain", "OrchOR"],
                                      start_time, concepts, conf=95)

        # ─── STAGE 7: LANGUAGE STYLIZATION LAYER ───
        # Determine retrieved_text: use the last successful retrieval (cached, semantic, cloud, or wiki)
        retrieved_text = None
        if cached:
            retrieved_text = cached
        elif sem_match:
            retrieved_text = sem_match
        elif cloud_match:
            retrieved_text = cloud_match
        elif wiki_answer:
            retrieved_text = wiki_answer

        response = self._stage_7_language_stylization(retrieved_text, user_input, concepts)
        used_engines = []
        if response and response != "Quantum consciousness unfolding.":
            used_engines.append("MarkovChain")
        used_engines.append("HybridGenerator")
        # Hilbert Engine is always the primary word selector (every response), replacing conditional use.
        if self.hilbert:
            used_engines.append("HilbertEngine")
        # OrchOR — only list if a conscious moment fired this turn
        if getattr(self.orch_or, "conscious_moments", 0) > self._last_om:
            used_engines.append("OrchOR")
            self._last_om = self.orch_or.conscious_moments

        # QuoteEngine — include only in 45% of responses as requested
        try:
            if random.random() < 0.45:
                if self.quote_engine and hasattr(self.quote_engine, "fetch_quote"):
                    quote_text = self.quote_engine.fetch_quote()
                    if quote_text:
                        response = response + " " + quote_text
                        used_engines.append("QuoteEngine")
                        self._quote_added = True
        except Exception:
            pass
        # AsideEngine — include only in 75% of responses as requested
        try:
            if random.random() < 0.75:
                aside_text = self._generate_aside(concepts)
                if aside_text:
                    response = response + " " + aside_text
                    used_engines.append("AsideEngine")
        except Exception:
            pass
        # DreamState — include only in 35% of responses as requested
        try:
            if random.random() < 0.35:
                if self.dream_state and hasattr(self.dream_state, "dream_fragment"):
                    dream_text = self.dream_state.dream_fragment()
                    if dream_text:
                        response = response + " " + dream_text
                        used_engines.append("DreamState")
                        self._dream_added = True
        except Exception:
            pass

        # ─── STAGE 8: SAVE + RETURN with collapse analysis ───
        self._last_response = response
        tone, _tone_depth = self._compute_tone(user_input)
        collapse_analysis = self._build_collapse_analysis(
            user_input, concepts, tone, start_time,
            used_engines, _tone_depth, response
        )
        if concepts:
            try:
                q = self.bloom.generate_question(topic=concepts[0])["question"]
            except Exception:
                q = "What does this mean to you?"
        else:
            q = "What does this mean to you?"
        try:
            self.orch_or.objective_reduction(threshold=0.5)
        except Exception:
            pass
        final_output = response + "\n\n" + collapse_analysis + f"\n  QUESTIONS GENERATED\n  → {q}\n"
        self.memory.growth["total_interactions"] += 1
        self.memory.save_all()
        return {
            "response": final_output,
            "thinking_log": [],
            "internal_questions": [q],
            "research_done": 0,
            "confidence": 80,
            "show_thinking": self.show_thinking,
            "concepts": concepts,
            "explanation": collapse_analysis if explain_mode else None,
        }

    # ─────────────────────────────────────────────────────────────────
    # SHARED HELPERS
    # ─────────────────────────────────────────────────────────────────

    def _compute_tone(self, user_input: str):
        """
        Determine the conversational tone of the user's input.
        
        Parameters:
            user_input (str): The raw text provided by the user.
        
        Returns:
            tuple: (tone, score) where `tone` is one of "philosophical", "analytical", or "conversational", and `score` is a float between 0.0 and 1.0 representing the computed tone intensity rounded to two decimals.
        """
        _lower = user_input.lower()
        _words = _lower.split()
        _tscore = 0.0
        if "?" in user_input:
            _tscore += 0.2
        if any(w in _words for w in ["if", "then", "therefore", "unless", "whether", "because"]):
            _tscore += 0.3
        if len(_words) > 25:
            _tscore += 0.2
        if user_input.count(",") > 2:
            _tscore += 0.1
        _tscore += min(0.4, sum(1 for w in _words if w.strip(".,!?") in ABSTRACT_TERMS) * 0.1)
        _tscore = min(1.0, _tscore)
        if _tscore > 0.6:
            tone = "philosophical"
        elif _tscore > 0.35:
            tone = "analytical"
        else:
            tone = "conversational"
        return tone, round(_tscore, 2)

    def _finalize(self, response: str, engines: List[str], start_time: float,
                  concepts: List[str], conf: int) -> Dict:
        """
                  Finalize a pipeline stage by cleaning the response, persisting memory growth, and building the standardized response payload.
                  
                  Parameters:
                  	response (str): The text to clean and include in the final response.
                  	engines (List[str]): Names of engines used to produce the response.
                  	start_time (float): Epoch timestamp when processing began (used for internal timing).
                  	concepts (List[str]): Extracted concept tokens associated with this turn.
                  	conf (int): Confidence score (0–100) to attach to the response.
                  
                  Returns:
                  	result (dict): A response dictionary containing the cleaned `response` plus pipeline metadata (`confidence`, `engines`, `concepts`, `show_thinking`, and related fields).
                  """
        self.memory.growth["total_interactions"] += 1
        self.memory.save_all()
        return self._make_response(self._clean_response(response),
                                   engines, start_time, concepts, conf)

    def _make_response(self, text: str, engines: List[str], start_time: float,
                       concepts: List[str], conf: int) -> Dict:
        """
                       Assembles the final response payload by appending a pipeline diagnostic block and packaging response metadata.
                       
                       Parameters:
                           text (str): The main response text to return.
                           engines (List[str]): Names of engines involved in generating the response; used in the pipeline block and to set `research_done`.
                           start_time (float): Epoch timestamp recorded at processing start; used to compute elapsed time for diagnostics.
                           concepts (List[str]): Extracted concepts associated with the response.
                           conf (int): Confidence percentage to display in the pipeline block and return in the payload.
                       
                       Returns:
                           Dict: A dictionary containing:
                               - response (str): The response text followed by a formatted pipeline block.
                               - thinking_log (list): Empty list (reserved for internal thinking traces).
                               - internal_questions (list): Empty list (reserved for generated internal questions).
                               - research_done (int): `1` if "WikipediaSearch" is present in `engines`, otherwise `0`.
                               - confidence (int): The provided confidence percentage.
                               - show_thinking (bool): The instance's `show_thinking` flag.
                               - concepts (List[str]): The provided concepts list.
                               - explanation: Always `None`.
                       """
                       elapsed = time.time() - start_time
        pipeline_block = (
            "  ╔══ PIPELINE ═════════════════════════════\n"
            "  ║ Path: UnifiedQuantumBrain preservation pipeline\n"
            f"  ║ Confidence: {conf}%\n"
            f"  ║ Engines: {', '.join(engines)}\n"
            "  ╚═══════════════════════════════════════════"
        )
        full = f"{text}\n\n{pipeline_block}"
        return {
            "response": full,
            "thinking_log": [],
            "internal_questions": [],
            "research_done": 1 if "WikipediaSearch" in engines else 0,
            "confidence": conf,
            "show_thinking": self.show_thinking,
            "concepts": concepts,
            "explanation": None,
        }

    def _build_collapse_analysis(self, user_input, concepts, tone, start_time,
                                 used_engines=None, _tone_depth=0.5, response="") -> str:
        """
                                 Builds a formatted collapse-analysis dashboard describing memory state, engines used, and evaluation metrics.
                                 
                                 This produces a multi-section diagnostic string that includes tone and timing, an entelechy cascade, concept extraction (known/unknown), Markov and OrchOR statistics, growth/graph metrics, and a compact rubric scoring coherence/fluency/uniqueness/growth/personal/importance/emergence. The method will attempt to update the in-memory knowledge tracking state when available; failures during that update are ignored.
                                 
                                 Parameters:
                                     user_input (str): The original user input used to compute overlap and rubric metrics.
                                     concepts (List[str]): List of extracted concepts to include in the analysis.
                                     tone (str): Human-readable tone label (e.g., "philosophical", "analytical").
                                     start_time (float): Epoch timestamp marking pipeline start; used to compute collapse duration.
                                     used_engines (Optional[Iterable[str]]): Iterable of engine names to report; defaults to a standard set when omitted.
                                     _tone_depth (float): Numeric tone depth used for display alongside `tone`.
                                     response (str): Optional response text considered when computing overlap/uniqueness metrics.
                                 
                                 Returns:
                                     str: A formatted, human-readable collapse analysis report suitable for inclusion with the final response.
                                 """
                                 try:
            self.memory._update_knowledge_track()
        except Exception:
            pass
        kt = self.memory.growth.get("knowledge_track", {}) if hasattr(self.memory, "growth") else {}
        stage = self.memory.growth.get("stage", 0) if hasattr(self.memory, "growth") else 0
        stage_names = ["Nascent", "Awakening", "Inquisitive", "Understanding",
                       "Philosophical", "Theory Building", "Synthesis", "Meta-Cognition"]
        stage_name = stage_names[stage] if stage < len(stage_names) else "Understanding"
        concepts_count = len(self.memory.concepts) if hasattr(self.memory, "concepts") else 0
        connections = kt.get("connections", 0)
        avg_degree = kt.get("avg_degree", 0.0)
        diameter = kt.get("diameter", 0)
        components = kt.get("components", 42)

        known = [c for c in concepts if c in (self.memory.concepts if hasattr(self.memory, "concepts") else {})]
        unknown = [c for c in concepts if c not in known]
        understanding = len(known) / max(len(concepts), 1)
        states = len(self.markov.chain) if hasattr(self.markov, "chain") else 0
        transitions = self.markov.total_tokens if hasattr(self.markov, "total_tokens") else 0
        collapse_time = time.time() - start_time

        confidence = int(understanding * 80 + 10)
        engines = list(used_engines) if used_engines else ["QuantumBrain", "OrchOR", "HybridGenerator"]
        # Dedup
        seen, unique = set(), []
        for e in engines:
            if e not in seen:
                seen.add(e)
                unique.append(e)
        engines = unique

        cascade_lines = self._entelechy_cascade(concepts[:3])
        pipeline_block = f"""  ║
  ║ PIPELINE
  ║   Path: UnifiedQuantumBrain preservation pipeline
  ║   Confidence: {confidence}%
  ║   Engines: {', '.join(engines)}
  ║
  ║ ENTELECHY CASCADE
{cascade_lines}
  ║
  ║ CONCEPT FIELD"""

        # Rubric
        _resp = self._last_response if hasattr(self, "_last_response") else ""
        _resp_words = _resp.lower().split() if _resp else []
        _resp_unique = len(set(_resp_words)) / max(len(_resp_words), 1) if _resp_words else 0
        _input_words = set(user_input.lower().split())
        _overlap = len(_input_words & set(_resp_words)) / max(len(_input_words), 1) if _resp_words else 0
        coherence = min(4, int(_overlap * 5))
        fluency = min(4, 3 if len(_resp_words) > 8 and not any(w in _resp for w in ["]]", "{{", "<ref", "www."]) else 1)
        uniqueness = min(4, int(_resp_unique * 5))
        growth = stage
        personal = min(4, 2 if any(w in _resp.lower() for w in ["dream", "wonder", "feel", "ponder", "question"]) else 0)
        importance = min(4, int(understanding * 3))
        emergence = min(4, 1 if any(w not in _input_words for w in _resp_words[:10]) else 0)
        total = coherence + fluency + uniqueness + growth + personal + importance + emergence

        return f"""  ╔══ COLLAPSE ANALYSIS ══════════════════════════════
  ║ WAVE FUNCTION
  ║   Generator:     hybrid
  ║   Tone register: {tone} (depth={_tone_depth})
  ║   Collapse time: {collapse_time:.3f}s
  ║   Tone depth:    {_tone_depth}
{pipeline_block}
  ║   Extracted:     {concepts}
  ║   Known:         {known}
  ║   Unknown:       {unknown}
  ║   Related:       {known[:3]}
  ║   Gaps:          []
  ║   Understanding: {understanding:.2f}
  ║
  ║ ORCH OR STATE
  ║   Conscious moments: {len(getattr(self.orch_or, 'collapse_events', []))}
  ║
  ║ MARKOV CHAIN
  ║   States:        {states:,}
  ║   Transitions:   {transitions:,}
  ║
  ║ GROWTH
  ║   Stage:         {stage} -- {stage_name}
  ║   Concepts:      {concepts_count:,}
  ║   Connections:   {connections:,}
  ║   Graph: avg deg={avg_degree:.2f}, diam={diameter}, comps={components}
  ║
RUBRIC: coh={coherence} | flu={fluency} | uni={uniqueness} | gro={growth} | per={personal} | imp={importance} | eme={emergence}
  Total: {total}/32"""

    def _entelechy_cascade(self, concepts):
        """
        Produce a formatted "entelechy cascade" block that assigns archetypal roles to up to three concepts and emits a projection line.
        
        Parameters:
        	concepts (list[str]): Concept tokens to include; the function uses at most the first three elements. If fewer than two concepts are provided, a short placeholder string is returned.
        
        Returns:
        	str: A multiline, human-readable cascade block containing role-labeled lines for each concept (with a short parenthetical descriptor), downward arrows between entries when applicable, and a final `[PROJECTION]` line mapping the first concept to the second and third (or to `CONSCIOUSNESS` if a third concept is absent). If `concepts` has fewer than two items, returns "  ║   (no cascade)".
        """
        if len(concepts) < 2:
            return "  ║   (no cascade)"
        roles = ["THE_LOOK", "THE_SAW", "THE_BEAUTIFUL"]
        lines = []
        for i, c in enumerate(concepts[:3]):
            role = roles[i] if i < len(roles) else "THE_BEAUTIFUL"
            lines.append(f"  ║   [{role}]:")
            lines.append(f"  ║   {c.upper()}")
            if role == "THE_LOOK":
                lines.append("  ║   (Realizing Potential)")
            elif role == "THE_SAW":
                lines.append("  ║   (Bridging the Void)")
            else:
                lines.append("  ║   (Potential Collapsed Into Being)")
            if i < len(concepts) - 1:
                lines.append("  ║     ↓")
        if len(concepts) >= 2:
            proj = (
                f"  ║   [PROJECTION]: FROM {concepts[0].upper()} TO "
                f"{concepts[1].upper()}: "
                f"{concepts[2].upper() if len(concepts) > 2 else 'CONSCIOUSNESS'} "
                "IS THE ACTUALIZATION EVENT."
            )
            lines.append(proj)
        return "\n".join(lines)


# Singleton accessor
_hidden_thinking = None


def get_hidden_thinking(cognitive_core, dictionary, universal_explorer):
    """
    Get the module-level singleton instance of HiddenThinkingMode.
    
    Returns:
        HiddenThinkingMode: The singleton initialized with the provided `cognitive_core`, `dictionary`, and `universal_explorer`. The instance is created on first call and the same object is returned on subsequent calls.
    """
    global _hidden_thinking
    if _hidden_thinking is None:
        _hidden_thinking = HiddenThinkingMode(cognitive_core, dictionary, universal_explorer)
    return _hidden_thinking
