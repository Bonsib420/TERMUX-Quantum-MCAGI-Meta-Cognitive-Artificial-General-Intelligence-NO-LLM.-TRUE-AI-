"""Feed downloaded PDFs/TXTs/PYs into the engine to expand Markov + TF-IDF."""
import os, sys, glob, json, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quantum_language_engine import QuantumLanguageEngine

EXTRA = os.path.join(os.path.dirname(__file__), "imported_extra")

def extract_pdf_text(path):
    """
    Extracts and concatenated visible text from every page of a PDF file.
    
    Attempts to read the PDF at `path`, extracts non-empty text from each page, and joins retained page texts with newline separators. If the PDF cannot be read or page extraction fails for all pages, an empty string is returned (an error message is printed on failure).
    
    Parameters:
        path (str): Filesystem path to the PDF file.
    
    Returns:
        str: Concatenated page text with newline separators, or an empty string on failure or when no page text is found.
    """
    try:
        from pypdf import PdfReader
        reader = PdfReader(path)
        chunks = []
        for page in reader.pages:
            try:
                t = page.extract_text() or ""
                if t.strip():
                    chunks.append(t)
            except Exception:
                continue
        return "\n".join(chunks)
    except Exception as e:
        print(f"  [pdf-fail] {path}: {e}")
        return ""

def clean(text):
    # Strip page numbers, excessive whitespace, control chars
    """
    Normalize extracted text by removing null bytes and collapsing excessive whitespace.
    
    Replaces null bytes with spaces, collapses runs of three or more newlines into two newlines,
    collapses runs of two or more spaces into a single space, and strips leading/trailing whitespace.
    
    Parameters:
        text (str): Raw text to clean.
    
    Returns:
        str: The cleaned and normalized text.
    """
    text = re.sub(r'\x00', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()

def main():
    """
    Ingest supplemental files from the imported_extra directory, update a QuantumLanguageEngine with their contents, optionally merge cloudsave concept words, and write an augmented engine snapshot.
    
    This function:
    - Loads PDF, TXT, and PY files under the imported_extra directory, extracts and cleans text, and skips very short inputs.
    - Trains the engine's TF-IDF component on each full cleaned document and trains the Markov component on sentence-like segments.
    - Optionally merges alphabetic concept words from imported_extra/cloudsave/latest.json into the TF-IDF word-frequency map.
    - Writes a JSON snapshot to runtime-data/imported_brain_snapshot.json containing:
      - kb_topics
      - tfidf_word_frequencies
      - tfidf_doc_count
      - markov_chain (stringified keys to dict)
      - markov_starters
    - Emits progress and summary information to standard output.
    """
    print("[feed] Booting engine...")
    eng = QuantumLanguageEngine()
    before_markov = len(eng.markov.chain_2.chain) if hasattr(eng.markov.chain_2.chain, '__len__') else 0
    before_vocab = len(eng.tfidf.extractor.word_frequencies)
    print(f"[feed] Baseline: {before_markov} Markov-2 states, {before_vocab} vocab")

    sources = []
    # PDFs
    for p in sorted(glob.glob(os.path.join(EXTRA, "**/*.pdf"), recursive=True)):
        print(f"[pdf] {os.path.basename(p)}")
        sources.append(("pdf:" + os.path.basename(p), extract_pdf_text(p)))
    # TXTs
    for p in sorted(glob.glob(os.path.join(EXTRA, "**/*.txt"), recursive=True)):
        try:
            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                sources.append(("txt:" + os.path.basename(p), f.read()))
        except Exception:
            pass
    # Python source as text (engine code = great syntactic training)
    for p in sorted(glob.glob(os.path.join(EXTRA, "**/*.py"), recursive=True)):
        try:
            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                sources.append(("py:" + os.path.basename(p), f.read()))
        except Exception:
            pass

    total_chars = 0
    total_sentences = 0
    for tag, raw in sources:
        text = clean(raw)
        if not text or len(text) < 50:
            continue
        total_chars += len(text)
        # Feed into TF-IDF + Markov
        eng.tfidf.learn(text)
        # Markov: split on sentences for better chains
        sents = re.split(r'(?<=[.!?])\s+', text)
        for s in sents:
            s = s.strip()
            if 3 < len(s.split()) < 100:
                eng.markov.learn(s)
                total_sentences += 1
        print(f"  [+] {tag}: {len(text)} chars, {len(sents)} sents")

    after_markov = len(eng.markov.chain_2.chain)
    after_vocab = len(eng.tfidf.extractor.word_frequencies)
    print(f"\n[feed] Fed {total_chars} chars / {total_sentences} sentences")
    print(f"[feed] Markov-2: {before_markov} -> {after_markov} (+{after_markov-before_markov})")
    print(f"[feed] Vocab:    {before_vocab} -> {after_vocab} (+{after_vocab-before_vocab})")

    # Cloudsave snapshot — extract text from .concepts if present
    cs_path = os.path.join(EXTRA, "cloudsave/latest.json")
    if os.path.exists(cs_path):
        try:
            with open(cs_path, 'r') as f:
                cs = json.load(f)
            concepts = cs.get('concepts', {})
            added = 0
            for word, meta in (concepts.items() if isinstance(concepts, dict) else []):
                w = word.lower().strip()
                if 2 < len(w) < 30 and w.isalpha():
                    if w not in eng.tfidf.extractor.word_frequencies:
                        eng.tfidf.extractor.word_frequencies[w] = 1
                        added += 1
                    else:
                        eng.tfidf.extractor.word_frequencies[w] += 1
            print(f"[cloudsave] Merged {added} new concept words from latest.json")
        except Exception as e:
            print(f"[cloudsave] error: {e}")

    # Save augmented snapshot
    out = os.path.join(os.path.dirname(__file__), "runtime-data", "imported_brain_snapshot.json")
    print(f"\n[feed] Saving augmented snapshot to {out}...")
    snap = {
        'kb_topics': dict(eng.knowledge.topics),
        'tfidf_word_frequencies': dict(eng.tfidf.extractor.word_frequencies),
        'tfidf_doc_count': getattr(eng.tfidf.extractor, 'doc_count', getattr(eng.tfidf.extractor, 'document_count', 0)),
        'markov_chain': {(' '.join(k) if isinstance(k, tuple) else str(k)): dict(v) for k, v in eng.markov.chain_2.chain.items()},
        'markov_starters': [(' '.join(s) if isinstance(s, tuple) else str(s)) for s in (eng.markov.chain_2.starters or [])],
    }
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as f:
        json.dump(snap, f)
    print(f"[feed] Snapshot saved: {os.path.getsize(out)/1024/1024:.1f} MB")
    print(f"[feed] Final: {after_markov} Markov-2 states, {after_vocab} vocab terms")

if __name__ == "__main__":
    main()
