#!/usr/bin/env python3
"""
training_engine.py - Quantum MCAGI
=====================================
Unified training engine.
Merges: training_pipeline.py + batch_ingest.py + fact_extractors.py

TWO-WAY TRAINING PIPELINE:
  Language pipeline (Markov, Hilbert, FunctionWord) - natural language only
  Knowledge pipeline (fact store, concept graph) - all content types

BATCH INGESTION:
  Reads URLs from JSON feeds, ingests with checkpoint/resume

FACT EXTRACTION:
  SVO extractor - natural language triples
  Code extractor - Python patterns and error fixes
  Knowledge extractor - definitions and relationships

Usage:
  python training_engine.py feeds.json           # batch ingest
  python training_engine.py feeds.json --resume  # resume from checkpoint
  python training_engine.py feeds.json --dry-run # list URLs only
"""



# ======================================================================
# FROM: training_pipeline.py
# ======================================================================

import os
import re
import json
import math
from typing import Optional, Dict, List, Tuple


# ── Backend configuration ─────────────────────────────────────────────────

SUPPORTED_BACKENDS = {
    'lightning.qubit',
    'lightning.kokkos',
    'lightning.gpu',
    'lightning.tensor',
    'default.qubit',
}
ACTIVE_BACKEND = 'lightning.qubit'
def set_backend(backend: str) -> bool:
    """Switch PennyLane backend. Returns True if available."""
    global ACTIVE_BACKEND
    if backend not in SUPPORTED_BACKENDS:
        return False
    try:
        import pennylane as qml
        qml.device(backend, wires=2)
        ACTIVE_BACKEND = backend
        return True
    except Exception:
        return False
def get_backend() -> str:
    return ACTIVE_BACKEND


# ── Natural language detector ─────────────────────────────────────────────

CODE_SIGNALS = [
    'def ', 'class ', 'import ', '#!/ ', 'return ', 'self.',
    '```', '|isbn', '{{cite', 'http://', 'https://',
    '.py', 'if __name__'
]

MARKUP_SIGNALS = [
    '{{', '}}', '[[', ']]', '<ref', '</ref>'
]

def detect_content_type(text: str) -> str:
    """
    Detect whether text is natural language, code, or markup.
    Returns: 'natural', 'code', 'markup', or 'mixed'
    """
    code_hits = sum(1 for s in CODE_SIGNALS if s in text)
    markup_hits = sum(1 for s in MARKUP_SIGNALS if s in text)

    total_chars = max(len(text), 1)
    word_chars = len(re.findall(r'[a-zA-Z\s]', text))
    prose_ratio = word_chars / total_chars

    if code_hits >= 3:
        return 'code'
    if markup_hits >= 3:
        return 'markup'
    if prose_ratio < 0.5:
        return 'mixed'
    return 'natural'
def clean_for_language(text: str) -> str:
    """
    Strip markup, code fragments, and Wikipedia artifacts
    before feeding to Markov/Hilbert/FunctionWord.
    """
    # Remove YouTube/WEBVTT transcript artifacts
    text = re.sub(r'WEBVTT.*?Kind:.*?\n', '', text, flags=re.DOTALL)
    text = re.sub(r'>>\s*', '', text)
    text = re.sub(r'&gt;&gt;\s*', '', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'\[Music\]', '', text)
    text = re.sub(r'\[Applause\]', '', text)
    text = re.sub(r'\[Laughter\]', '', text)
    text = re.sub(r'\[\w+\]', '', text)

    # Remove Wikipedia markup
    text = re.sub(r'\{\{[^}]*\}\}', '', text)
    text = re.sub(r'\[\[[^\]]*\]\]', '', text)
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\|[a-z_]+=\S+', '', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'&\w+;', ' ', text)

    # Remove code fragments
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`[^`]+`', '', text)
    text = re.sub(r'^\s*(def |class |import |from |#!)', '', text, flags=re.MULTILINE)

    # Remove citation artifacts
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\(\s*\)', '', text)

    # Clean whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text
def filter_language_tokens(tokens: List[str]) -> List[str]:
    """
    Removes specific code and markup tokens that leaked into the chain.
    """
    bad_patterns = {
        '{{', '}}', '|isbn', '|doi', '[[', ']]',
        '<ref', '</ref', 'import ', 'def ', 'class ',
        '"""', "'''", '#!/', '.py', 'http://', 'https://',
        '&nbsp;', '%7C', 'bgcolor', 'colspan',
    }
    return [t for t in tokens if t not in bad_patterns]

def train_language(text: str, engine) -> Dict:
    """
    Train the language pipeline: Markov, Hilbert, FunctionWord.
    Only accepts clean natural language - strips code and markup first.

    Returns dict with counts of what was trained.
    """
    result = {'markov_words': 0, 'hilbert': False, 'function_words': False}

    content_type = detect_content_type(text)

    if content_type == 'code':
        # Code goes to knowledge pipeline only
        return result

    # Clean for language processing
    cleaned = clean_for_language(text)
    if len(cleaned.split()) < 5:
        return result

    # Markov training
    try:
        engine.markov.train(cleaned)
        result['markov_words'] = len(cleaned.split())
    except Exception:
        pass

    # TF-IDF
    try:
        engine.tfidf.learn(text)
    except Exception:
        pass

    # Collapse observer
    try:
        first_word = cleaned.split()[0] if cleaned.split() else 'input'
        engine.collapse.observe(first_word)
    except Exception:
        pass

    # Function word engine
    try:
        if not hasattr(engine, '_fwe') or engine._fwe is None:
            from function_word_engine import FunctionWordEngine
            engine._fwe = FunctionWordEngine()
            fwe_path = os.path.expanduser('~/.quantum-mcagi/function_words.json')
            if os.path.exists(fwe_path):
                engine._fwe.load(fwe_path)
        engine._fwe.update_from_text(cleaned)
        result['function_words'] = True
    except Exception:
        pass

    # Hilbert semantic engine (batch update, not per-token)
    try:
        if hasattr(engine, 'hilbert_semantic') and engine.hilbert_semantic:
            words = cleaned.split()[:50]
            for word in words:
                if len(word) > 3 and word.isalpha():
                    engine.hilbert_semantic.evolve(word)
            result['hilbert'] = True
    except Exception:
        pass

    return result


# ── Knowledge training pipeline ───────────────────────────────────────────

FACT_STORE_PATH = os.path.expanduser('~/.quantum-mcagi/fact_store.json')

SVO_VERBS = {
    'is', 'are', 'was', 'were', 'has', 'have', 'contains',
    'includes', 'consists', 'means', 'refers', 'represents',
    'located', 'found', 'known', 'called', 'defined', 'describes',
    'provides', 'requires', 'enables', 'produces', 'creates',
    'affects', 'causes', 'prevents', 'allows', 'supports',
    'involves', 'relates', 'connects', 'influences', 'determines',
}

SVO_SKIP = {
    'this book', 'the book', 'our company', 'the cover', 'the author',
    'the publisher', 'this text', 'the text', 'this page', 'the page',
    'we', 'it', 'this', 'that', 'he', 'she', 'they', 'i', 'you',
    'the following', 'the above', 'also', 'doi', 'ref',
}

GARBAGE_PATTERNS = [
    r'^\d+(\.\d+)?$',      # Pure numbers
    r'^10\.\d{4}',          # DOI numbers
    r'\{\{',                # Wikipedia templates
    r'\[\[',                # Wikipedia links
    r'^[A-Z]{1,4}[\s\-]',  # Citation codes
    r'\|[a-z]+=',           # Template parameters
]
_GARBAGE_RE = re.compile('|'.join(GARBAGE_PATTERNS))
def is_garbage(text: str) -> bool:
    return bool(_GARBAGE_RE.search(text)) or len(text) > 80 or '\n' in text


SVO_SKIP_SUBJECTS = {
    'this book', 'the book', 'our company', 'the cover', 'the author',
    'the publisher', 'this text', 'the text', 'this page', 'the page',
    'we', 'it', 'this', 'that', 'he', 'she', 'they', 'i', 'you',
    'the following', 'the above', 'the below'
}
def extract_svo_facts(text: str, skip_first_chars: int = 500) -> List[Tuple[str, str, str]]:
    """Extract subject-verb-object triples from natural language text."""
    facts = []
    content = text[skip_first_chars:]
    sentences = re.split(r'[.!?]+', content)

    for sentence in sentences:
        words = sentence.strip().split()
        if not (4 <= len(words) <= 40):
            continue

        for i, word in enumerate(words):
            if word.lower() in SVO_VERBS and i >= 1:
                subject = ' '.join(words[:i]).strip().lower()
                verb = word.lower()
                obj = ' '.join(words[i+1:]).strip().lower()
                subj_words = subject.split()

                if (subject
                        and obj
                        and 1 <= len(subj_words) <= 5
                        and subject not in SVO_SKIP_SUBJECTS
                        and not subject.startswith('this ')
                        and not subject.startswith('the following')
                        and len(obj) > 8
                        and not any(c.isdigit() for c in subject)):
                    facts.append((subject, verb, obj[:150]))
                break

    return facts


# ── 2. Code Extractor - Python patterns ───────────────────────────────────

CODE_PATTERNS = [
    # Function definitions
    (r'def\s+(\w+)\s*\(([^)]*)\)', 'function', '{name} is a Python function with parameters {params}'),
    # Class definitions
    (r'class\s+(\w+)(?:\s*\(([^)]*)\))?', 'class', '{name} is a Python class'),
    # Import statements
    (r'import\s+([\w.]+)', 'import', '{name} is a Python module'),
    (r'from\s+([\w.]+)\s+import\s+([\w,\s]+)', 'from_import', '{name} exports {exports}'),
    # Exception handling
    (r'except\s+([\w.]+)', 'exception', '{name} is a Python exception type'),
    # Decorators
    (r'@(\w+)', 'decorator', '{name} is a Python decorator'),
]

SYNTAX_RULES = [
    ("f-string", "f-string must have closing quote on same line unless triple-quoted"),
    ("def", "def keyword must be followed by function name and parentheses"),
    ("class", "class body must be indented with consistent spaces"),
    ("try", "try block must be followed by except or finally"),
    ("with", "with statement creates a context manager that handles cleanup"),
    ("yield", "yield turns a function into a generator"),
    ("lambda", "lambda creates an anonymous function inline"),
    ("list comprehension", "list comprehension creates list with [expression for item in iterable]"),
    ("dictionary comprehension", "dictionary comprehension creates dict with {key: value for item in iterable}"),
    ("decorator", "decorator modifies function behavior using @decorator_name syntax"),
    ("context manager", "context manager uses with statement and implements __enter__ and __exit__"),
    ("generator", "generator uses yield to produce values lazily one at a time"),
    ("ast.parse", "ast.parse validates Python syntax without executing code"),
    ("getattr", "getattr safely accesses attribute with default if missing"),
    ("isinstance", "isinstance checks if object is instance of class or tuple of classes"),
]

ERROR_PATTERNS = [
    ("SyntaxError unterminated f-string", "join the broken line with next line merging into single line"),
    ("SyntaxError unterminated string", "find the opening quote and close it on same line"),
    ("IndentationError unexpected indent", "check that all lines in block use same indentation"),
    ("AttributeError has no attribute", "use getattr with default value to handle missing attributes"),
    ("KeyError", "use dict.get with default value instead of dict[key]"),
    ("TypeError NoneType", "check for None before calling methods on return values"),
    ("ImportError circular", "move shared code to separate module or use lazy imports"),
    ("NameError not defined", "check variable is defined before use or import is at top of file"),
    ("RecursionError maximum depth", "add base case or use iterative approach instead of recursion"),
    ("def with no name", "add function name after def keyword before parentheses"),

]
def extract_code_facts(text: str) -> List[Tuple[str, str, str]]:
    """Extract Python code patterns and syntax rules from text."""
    facts = []

    # Extract function and class definitions from code blocks
    code_blocks = re.findall(r'```python(.*?)```', text, re.DOTALL)
    code_blocks += re.findall(r'```(.*?)```', text, re.DOTALL)

    for block in code_blocks:
        for pattern, fact_type, template in CODE_PATTERNS:
            for match in re.finditer(pattern, block):
                if fact_type == 'function':
                    name = match.group(1)
                    params = match.group(2) if match.group(2) else ''
                    facts.append((name, 'is', f'a Python function with parameters ({params})'))
                elif fact_type == 'class':
                    name = match.group(1)
                    facts.append((name, 'is', 'a Python class'))
                elif fact_type == 'import':
                    name = match.group(1)
                    facts.append((name, 'is', 'a Python module'))
                elif fact_type == 'exception':
                    name = match.group(1)
                    facts.append((name, 'is', 'a Python exception type'))
                elif fact_type == 'decorator':
                    name = match.group(1)
                    facts.append((name, 'is', 'a Python decorator'))

    # Add syntax rules as facts
    for term, rule in SYNTAX_RULES:
        if term.lower() in text.lower():
            facts.append((term, 'requires', rule))

    # Add error pattern facts
    for error, fix in ERROR_PATTERNS:
        if any(word in text.lower() for word in error.lower().split()[:2]):
            facts.append((error, 'fix', fix))

    return facts


# ── 3. Knowledge Extractor - definitions and relationships ─────────────────

DEFINITION_PATTERNS = [
    r'(\w[\w\s]{2,30})\s+(?:is|are)\s+(?:a|an|the)\s+(.{10,150}?)(?:\.|,|\n)',
    r'(\w[\w\s]{2,30})\s+(?:refers to|defined as|known as|called)\s+(.{10,150}?)(?:\.|,|\n)',
    r'(\w[\w\s]{2,30}):\s+(.{10,150}?)(?:\.|,|\n)',
]

RELATIONSHIP_WORDS = [
    'part of', 'type of', 'form of', 'kind of', 'example of',
    'related to', 'based on', 'derived from', 'used in', 'applied to',
    'contrasted with', 'compared to', 'similar to', 'opposite of',
    'depends on', 'requires', 'enables', 'produces', 'causes',
]
def extract_knowledge_facts(text: str) -> List[Tuple[str, str, str]]:
    """Extract definitions and conceptual relationships from knowledge text."""
    facts = []

    # Extract definitions
    for pattern in DEFINITION_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            subject = match.group(1).strip().lower()
            definition = match.group(2).strip().lower()
            words = subject.split()
            if (1 <= len(words) <= 4
                    and len(definition) > 10
                    and len(definition) < 200
                    and not any(c.isdigit() for c in subject)):
                facts.append((subject, 'is', definition[:150]))

    # Extract relationships
    sentences = re.split(r'[.!?]+', text)
    for sentence in sentences:
        sentence_lower = sentence.lower()
        for rel in RELATIONSHIP_WORDS:
            if rel in sentence_lower:
                parts = sentence_lower.split(rel, 1)
                if len(parts) == 2:
                    subject = parts[0].strip().split()[-3:]
                    obj = parts[1].strip().split()[:5]
                    if subject and obj:
                        subj_str = ' '.join(subject).strip('.,;: ')
                        obj_str = ' '.join(obj).strip('.,;: ')
                        if (len(subj_str) > 3
                                and len(obj_str) > 3
                                and not any(c.isdigit() for c in subj_str)):
                            facts.append((subj_str, rel, obj_str))

    return facts


# ── Main extraction pipeline ───────────────────────────────────────────────
def extract_all_facts(text: str, source_type: str = 'auto') -> int:
    """
    Run all three extractors on text and save to fact store.

    source_type: 'code', 'knowledge', 'natural', or 'auto' (detect)

    Returns number of new facts added.
    """
    fs = load_fact_store()
    new_facts = 0

    # Auto-detect source type
    if source_type == 'auto':
        code_indicators = text.count('def ') + text.count('class ') + text.count('import ')
        if code_indicators > 5:
            source_type = 'code'
        elif any(w in text.lower() for w in ['therefore', 'hence', 'thus', 'whereas', 'however']):
            source_type = 'knowledge'
        else:
            source_type = 'natural'

    # Run appropriate extractors
    all_facts = []

    if source_type in ('natural', 'auto'):
        all_facts.extend(extract_svo_facts(text))

    if source_type in ('code', 'auto'):
        all_facts.extend(extract_code_facts(text))

    if source_type in ('knowledge', 'auto'):
        all_facts.extend(extract_knowledge_facts(text))

    # Save to fact store
    for subject, verb, obj in all_facts:
        if not subject or not obj:
            continue
        if subject not in fs:
            fs[subject] = []
        triple = [verb, obj]
        if triple not in fs[subject]:
            fs[subject].append(triple)
            new_facts += 1

    if new_facts > 0:
        save_fact_store(fs)

    return new_facts


if __name__ == '__main__':
    # Test
    test_text = """
    Python is a high-level programming language.
    A function is defined using the
def keyword.
def greet(name):
        return f"Hello {name}"
    Recursion is a technique where a function calls itself.
    A list comprehension creates a list from an iterable.
    The SyntaxError unterminated f-string occurs when a string is split across lines.
    """
    n = extract_all_facts(test_text)
    print(f"Extracted {n} facts")
    fs = load_fact_store()
    for k, v in list(fs.items())[-5:]:
        print(f"  {k}: {v}")


# ======================================================================
# FROM: batch_ingest.py
# ======================================================================

import sys
import os
import re
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quantum_language_engine import QuantumLanguageEngine
from document_engine import ingest_document


# ============================================================================
# CONFIG
# ============================================================================

SAVE_EVERY = 10          # Save engine state every N successful ingestions
CLOUD_SAVE_EVERY = 50    # Cloud save every N successful ingestions
CHECKPOINT_FILE = os.path.expanduser('~/.quantum-mcagi/batch_checkpoint.json')
ERROR_LOG = os.path.expanduser('~/.quantum-mcagi/batch_errors.log')
STATE_DIR = os.path.expanduser('~/.quantum-mcagi/engine_state')


# ============================================================================
# KNOWLEDGE TRAINING
# ============================================================================
def train_knowledge(text: str, memory=None) -> int:
    """
    Train the knowledge pipeline: fact store, concept graph, knowledge base.
    Accepts all content types including code and markup.

    Returns number of new facts added.
    """
    # Detect content type for appropriate extractor
    content_type = detect_content_type(text)

    all_facts = []

    if content_type == 'code':
        all_facts.extend(extract_code_facts(text))
    elif content_type in ('natural', 'mixed'):
        all_facts.extend(extract_svo_facts(text))
        all_facts.extend(extract_knowledge_facts(text))
    else:  # markup
        # Clean markup then extract
        cleaned = clean_for_language(text)
        all_facts.extend(extract_svo_facts(cleaned))

    # Save to fact store
    new_facts = 0
    if all_facts:
        try:
            try:
                with open(FACT_STORE_PATH) as f:
                    fs = json.load(f)
            except Exception:
                fs = {}

            for subject, verb, obj in all_facts:
                if is_garbage(subject) or is_garbage(obj):
                    continue
                if subject not in fs:
                    fs[subject] = []
                triple = [verb, obj]
                if triple not in fs[subject]:
                    fs[subject].append(triple)
                    new_facts += 1

            with open(FACT_STORE_PATH, 'w') as f:
                json.dump(fs, f)
        except Exception:
            pass

    # Update concept graph if memory available
    if memory and new_facts > 0:
        try:
            concepts_found = [s for s, v, o in all_facts if len(s.split()) == 1]
            for concept in concepts_found[:10]:
                if concept not in memory.concepts:
                    memory.concepts[concept] = {'count': 1, 'strength': 1.0, 'relationships': {}}
                else:
                    memory.concepts[concept]['count'] = memory.concepts[concept].get('count', 0) + 1
        except Exception:
            pass

    return new_facts


# ── Unified training entry point ──────────────────────────────────────────
def train_all(text: str, engine, memory=None) -> Dict:
    """
    Run both pipelines on ingested text.
    Language pipeline: only on clean natural language.
    Knowledge pipeline: on everything.

    This is the single entry point replacing learn_from_text().
    """
    if not text or len(text.strip()) < 10:
        return {'language': {}, 'knowledge': 0}

    lang_result = train_language(text, engine)
    knowledge_facts = train_knowledge(text, memory)

    return {
        'language': lang_result,
        'knowledge': knowledge_facts,
        'content_type': detect_content_type(text),
    }


# ── Backend command for chat.py ───────────────────────────────────────────
def handle_backend_command(cmd_parts: List[str]) -> str:
    """
    Handle /backend command from chat.py

    /backend              - show current backend and available options
    /backend lightning.qubit  - switch backend
    """
    if len(cmd_parts) == 1:
        available = []
        for b in SUPPORTED_BACKENDS:
            try:
                import pennylane as qml
                qml.device(b, wires=2)
                available.append(f"  ✓ {b}" + (" [ACTIVE]" if b == ACTIVE_BACKEND else ""))
            except Exception:
                available.append(f"  ✗ {b} (not installed)")
        return f"  Current backend: {ACTIVE_BACKEND}\n" + "\n".join(available)

    new_backend = cmd_parts[1]
    if set_backend(new_backend):
        # Also update pennylane_quantum module
        try:
            import pennylane_quantum as _pq
            _pq.ACTIVE_BACKEND = new_backend
            _pq.default_backend = new_backend
        except Exception:
            pass
        return f"  Backend switched to: {new_backend}"
    else:
        return f"  Backend not available: {new_backend}. Options: {', '.join(SUPPORTED_BACKENDS)}"


if __name__ == '__main__':
    print("Training Pipeline - Quantum MCAGI")
    print(f"Active backend: {ACTIVE_BACKEND}")

    # Test content detection
    test_natural = "DNA is the molecule that carries genetic information. Evolution is the process of natural selection."
    test_code = "def process():\n    import re\n    return re.findall(r'\\w+', text)"
    test_markup = "{{cite book|title=Example|author=Smith|doi=10.1234/example}}"

    print(f"Natural: {detect_content_type(test_natural)}")
    print(f"Code: {detect_content_type(test_code)}")
    print(f"Markup: {detect_content_type(test_markup)}")

    # Test SVO extraction
    facts = extract_svo_facts(test_natural)
    print(f"SVO facts: {facts}")

    print("Pipeline OK")


# ======================================================================
# FROM: fact_extractors.py
# ======================================================================

import re
import os
import json
from typing import List, Dict, Tuple

FACT_STORE_PATH = os.path.join(os.path.expanduser('~/.quantum-mcagi'), 'fact_store.json')
def load_fact_store() -> Dict:
    try:
        with open(FACT_STORE_PATH) as f:
            return json.load(f)
    except Exception:
        return {}
def save_fact_store(fs: Dict):
    os.makedirs(os.path.dirname(FACT_STORE_PATH), exist_ok=True)
    with open(FACT_STORE_PATH, 'w') as f:
        json.dump(fs, f)


# ── 1. SVO Extractor - natural language ───────────────────────────────────

SVO_VERBS = {
    'is', 'are', 'was', 'were', 'has', 'have', 'contains',
    'includes', 'consists', 'means', 'refers', 'represents',
    'located', 'found', 'known', 'called', 'defined', 'describes',
    'provides', 'requires', 'enables', 'produces', 'creates',
    'affects', 'causes', 'prevents', 'allows', 'supports'
}
def extract_urls(filepath):
    """Extract all URLs from a text/markdown file."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()

    # Match http and https URLs
    urls = re.findall(r'https?://[^\s\)\]\>\"\'\,]+', text)

    # Clean trailing punctuation
    cleaned = []
    for url in urls:
        url = url.rstrip('.')
        url = url.rstrip(',')
        url = url.rstrip(')')
        url = url.rstrip(']')
        url = url.rstrip('>')
        # Skip non-content URLs
        if any(skip in url.lower() for skip in [
            'rapidapi.com', 'localhost', '127.0.0.1',
            'fonts.googleapis', 'cdnjs.cloudflare',
            '.css', '.js', '.svg', '.ico',
        ]):
            continue
        cleaned.append(url)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for url in cleaned:
        if url not in seen:
            seen.add(url)
            unique.append(url)

    return unique


# ============================================================================
# CHECKPOINT
# ============================================================================
def load_checkpoint():
    """Load the checkpoint file."""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {'completed': [], 'failed': [], 'last_index': 0}
def save_checkpoint(checkpoint):
    """Save checkpoint to disk."""
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)
def log_error(url, error):
    """Log an error to the error file."""
    os.makedirs(os.path.dirname(ERROR_LOG), exist_ok=True)
    with open(ERROR_LOG, 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] {url}\nError: {error}\n")



# ============================================================================
# BATCH INGEST
# ============================================================================
def batch_ingest(filepath, resume=True, dry_run=False, start_at=0):
    """Run batch ingestion from a URL list file."""

    print(f"╔══ QUANTUM MCAGI - BATCH INGESTION ══════════════════")
    print(f"  ║ Source: {os.path.basename(filepath)}")

    # Extract URLs
    urls = extract_urls(filepath)
    total = len(urls)
    print(f"  ║ URLs found: {total}")

    if dry_run:
        print(f"  ║ DRY RUN - listing URLs only")
        print(f"  ╚═══════════════════════════════════════════════════")

        for i, url in enumerate(urls):
            print(f"  {i+1:4d}. {url}")
        return

    # Load checkpoint
    checkpoint = load_checkpoint() if resume else {'completed': [], 'failed': [], 'last_index': 0}
    completed_set = set(checkpoint['completed'])
    skip_count = len(completed_set)

    if start_at > 0:
        print(f"  ║ Starting from URL #{start_at}")
    elif skip_count > 0:
        print(f"  ║ Resuming: {skip_count} already completed")

    # Initialize engine
    print(f"  ║ Loading engine...")
    engine = QuantumLanguageEngine()
    try:
        from hilbert_bridge import wire_hilbert
        wire_hilbert(engine)
    except Exception:
        pass

    # Load saved state
    if os.path.exists(STATE_DIR):
        try:
            engine.load_state(STATE_DIR)
            states = len(engine.markov.chain) if hasattr(engine.markov, 'chain') else 0
            print(f"  ║ Engine loaded: {states} Markov states")
        except Exception as e:
            print(f"  ║ Engine load warning: {e}")
            print(f"  ║ Starting with fresh engine")

    print(f"  ║ Save every: {SAVE_EVERY} ingestions")
    print(f"  ║ Cloud save every: {CLOUD_SAVE_EVERY} ingestions")
    print(f"  ╠═══════════════════════════════════════════════════")

    # Track stats
    success_count = 0
    fail_count = 0
    total_words = 0
    start_time = time.time()

    for i, url in enumerate(urls):
        # Skip if before start point
        if i < start_at:
            continue

        # Skip if already completed
        if url in completed_set:
            continue

        # Progress
        remaining = total - i
        elapsed = time.time() - start_time
        if success_count > 0:
            avg_time = elapsed / success_count
            eta = avg_time * remaining
            eta_str = f"~{int(eta/60)}m{int(eta%60)}s"
        else:
            eta_str = "calculating..."

        print(f"  ║ [{i+1}/{total}] {url[:60]}...")

        # Ingest
        try:
            raw = ingest_document(url)
            # Normalize return type
            if isinstance(raw, tuple):
                result = {'text': raw[0] if raw[0] else None}
            elif isinstance(raw, dict):
                result = raw
            elif isinstance(raw, str):
                result = {'text': raw}
            else:
                result = {'text': None}

            # Handle tuple, dict, or string returns
            text = None
            if isinstance(result, tuple):
                text = result[0] if len(result) > 0 and result[0] else None
            elif isinstance(result, dict):
                text = result.get('text')
            elif isinstance(result, str):
                text = result

            if text and len(text.strip()) > 20:
                words = len(text.split())
                engine.learn_from_text(text)
                total_words += words

                # Extract facts using dedicated extractors
                try:
                    from training_engine import extract_all_facts
                    _new = extract_all_facts(text)
                except Exception as _e:
                    print(f"FACT ERROR: {_e}")
                    _new = 0

                states = len(engine.markov.chain) if hasattr(engine.markov, 'chain') else 0
                print(f'  ║   ✓ {words:,} words → {states:,} states | facts +{_new}')

                success_count += 1
                checkpoint['completed'].append(url)
                completed_set.add(url)
                checkpoint['last_index'] = i
            else:
                print(f'  ║   ✗ No usable text')
                fail_count += 1
                checkpoint['failed'].append(url)

        except Exception as e:
            error_msg = str(e)[:100]
            print(f"  ║   ✗ {error_msg}")
            fail_count += 1
            checkpoint['failed'].append(url)
            log_error(url, error_msg)

        # Save checkpoint every time
        save_checkpoint(checkpoint)

        # Save engine state periodically
        if success_count > 0 and success_count % SAVE_EVERY == 0:
            try:
                engine.save_state(STATE_DIR)
                engine.markov.save_state()
                states = len(engine.markov.chain) if hasattr(engine.markov, 'chain') else 0
                print(f"  ║   💾 Saved ({states:,} states)")
            except Exception as e:
                print(f"  ║   ⚠ Save failed: {e}")

        # Cloud save periodically
        if success_count > 0 and success_count % CLOUD_SAVE_EVERY == 0:
            try:
                cloud.save_state(engine)
                print(f"  ║   ☁ Cloud saved")
            except Exception as e:
                print(f"  ║   ⚠ Cloud save skipped: {e}")

        # ETA display every 10
        if (i + 1) % 10 == 0:
            elapsed = time.time() - start_time
            print(f"  ║   ⏱ {elapsed:.0f}s elapsed | {success_count} ok | {fail_count} fail | ETA: {eta_str}")

    # Final save
    try:
        engine.save_state(STATE_DIR)
        states = len(engine.markov.chain) if hasattr(engine.markov, 'chain') else 0
    except Exception:
        states = '?'

    elapsed = time.time() - start_time

    print(f"  ╠═══════════════════════════════════════════════════")
    print(f"  ║ COMPLETE")
    print(f"  ║ Successful: {success_count}/{total}")
    print(f"  ║ Failed: {fail_count}")
    print(f"  ║ Words ingested: {total_words:,}")
    print(f"  ║ Markov states: {states}")
    print(f"  ║ Time: {elapsed/60:.1f} minutes")
    print(f"  ║ Checkpoint: {CHECKPOINT_FILE}")
    if fail_count > 0:
        print(f"  ║ Error log: {ERROR_LOG}")
    print(f"  ╚═══════════════════════════════════════════════════")


    # Final cloud save
    try:
        cloud.save_state(engine)
        print("  ☁ Final cloud save complete")
    except Exception:
        pass


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Quantum MCAGI - Batch Ingestion")
        print("Usage:")
        print("  python batch_ingest.py domains.md              # ingest all")
        print("  python batch_ingest.py domains.md --resume     # resume from checkpoint")
        print("  python batch_ingest.py domains.md --dry-run    # list URLs only")
        print("  python batch_ingest.py domains.md --start 50   # start from #50")
        sys.exit(0)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        sys.exit(1)

    resume = '--resume' in sys.argv
    dry_run = '--dry-run' in sys.argv
    start_at = 0
    if '--start' in sys.argv:
        idx = sys.argv.index('--start')
        if idx + 1 < len(sys.argv):
            start_at = int(sys.argv[idx + 1])

    batch_ingest(filepath, resume=resume, dry_run=dry_run, start_at=start_at)

