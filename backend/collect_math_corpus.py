#!/data/data/com.termux/files/usr/bin/env python3
"""
🎓 Math Corpus Collector
=========================
Downloads a wide math corpus to ~/training/math/ from every legit free source:

  • Wikipedia math articles (~60 topics)
  • Stanford Encyclopedia of Philosophy (math/logic entries)
  • Project Gutenberg classical math books
  • arXiv math abstracts (recent papers)
  • The Stacks Project (open algebraic geometry textbook)
  • nLab category theory pages
  • ProofWiki (proofs and theorems)
  • Math Stack Exchange high-voted Q&A samples

Each file lands as plain text, ready for /ingest.

Usage:
    python collect_math_corpus.py
    python collect_math_corpus.py --skip-existing
    python collect_math_corpus.py --topic-filter calculus

After collection, ingest into engine via:
    /ingest ~/training/math/<filename>.txt
or batch:
    for f in ~/training/math/*.txt; do echo "/ingest $f"; done | python chat.py
"""

import os
import sys
import time
import argparse
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

# ────────────────────────────────────────────────────────────────────
TARGET_DIR = Path("~/training/math").expanduser()
TARGET_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "QuantumMCAGI-MathCollector/1.0 (research/training)"

# Topics for Wikipedia (will fetch plain text via REST API)
WIKI_TOPICS = [
    # Foundations
    "Mathematics", "Logic", "Set_theory", "Naive_set_theory", "Axiomatic_set_theory",
    "Zermelo-Fraenkel_set_theory", "Cardinality", "Continuum_hypothesis",
    "Cantor_set", "Cantor's_diagonal_argument",
    # Analysis
    "Calculus", "Real_analysis", "Complex_analysis", "Functional_analysis",
    "Measure_(mathematics)", "Lebesgue_integration", "Fourier_transform",
    "Laplace_transform", "Differential_equation", "Partial_differential_equation",
    "Integral", "Derivative", "Limit_(mathematics)", "Continuous_function",
    "Uniform_continuity", "Total_disconnectedness",
    # Algebra
    "Algebra", "Linear_algebra", "Abstract_algebra", "Group_(mathematics)",
    "Ring_(mathematics)", "Field_(mathematics)", "Vector_space", "Module_(mathematics)",
    "Galois_theory", "Tensor",
    # Geometry & Topology
    "Geometry", "Euclidean_geometry", "Non-Euclidean_geometry", "Topology",
    "Algebraic_topology", "Differential_geometry", "Manifold", "Homotopy",
    "Homology_(mathematics)", "Fiber_bundle",
    # Number Theory
    "Number_theory", "Prime_number", "Riemann_hypothesis", "Modular_arithmetic",
    "Diophantine_equation",
    # Discrete & Combinatorics
    "Combinatorics", "Graph_theory", "Combinatorial_game_theory",
    # Probability & Statistics
    "Probability_theory", "Statistics", "Bayes'_theorem", "Central_limit_theorem",
    "Markov_chain", "Stochastic_process", "Random_variable",
    # Category & Foundations
    "Category_theory", "Functor", "Natural_transformation", "Topos",
    "Type_theory", "Mathematical_logic", "Computability_theory",
    "Gödel's_incompleteness_theorems", "Turing_machine",
    # Applied / mathematical physics
    "Mathematical_physics", "Quantum_mechanics", "Hilbert_space",
    "Density_matrix", "Born_rule", "Quantum_entanglement",
]

# Stanford Encyclopedia of Philosophy entries (math/logic philosophy)
SEP_ENTRIES = [
    "philosophy-mathematics",
    "set-theory",
    "continuum-hypothesis",
    "logic-classical",
    "logic-intuitionistic",
    "computability",
    "mathematics-constructive",
    "platonism-mathematics",
    "category-theory",
    "infinity",
    "mathematics-inconsistent",
    "proof-theoretic-semantics",
]

# Project Gutenberg classical math texts (direct .txt URLs)
GUTENBERG_BOOKS = [
    ("euclid_elements", "https://www.gutenberg.org/files/21076/21076-0.txt"),
    ("boole_laws_of_thought", "https://www.gutenberg.org/files/15114/15114-0.txt"),
    ("euler_algebra", "https://www.gutenberg.org/files/45252/45252-0.txt"),
    ("cajori_history_of_math", "https://www.gutenberg.org/files/31246/31246-0.txt"),
    ("russell_principles_of_math", "https://www.gutenberg.org/files/41568/41568-0.txt"),
    ("dedekind_continuity", "https://www.gutenberg.org/files/21016/21016-0.txt"),
    ("poincare_science_hypothesis", "https://www.gutenberg.org/files/37157/37157-0.txt"),
    ("whitehead_introduction_to_math", "https://www.gutenberg.org/files/18750/18750-0.txt"),
    ("demorgan_formal_logic", "https://www.gutenberg.org/files/30207/30207-0.txt"),
    ("klein_lectures_on_math", "https://www.gutenberg.org/files/36154/36154-0.txt"),
]

# arXiv math feed — recent abstracts
ARXIV_FEEDS = [
    ("arxiv_math_recent", "https://export.arxiv.org/list/math/26"),
    ("arxiv_math_AG_recent", "https://export.arxiv.org/list/math.AG/26"),
    ("arxiv_math_GT_recent", "https://export.arxiv.org/list/math.GT/26"),
    ("arxiv_math_NT_recent", "https://export.arxiv.org/list/math.NT/26"),
    ("arxiv_math_LO_recent", "https://export.arxiv.org/list/math.LO/26"),
]


# ────────────────────────────────────────────────────────────────────
def fetch(url: str, timeout: int = 30) -> str:
    """
    Download the resource at `url` using the configured User-Agent and return the response body decoded to a Python string.
    
    Attempts to decode using 'utf-8' first, then 'latin-1', and finally falls back to decoding with 'utf-8' while ignoring errors if necessary.
    
    Parameters:
        url (str): The target URL to fetch.
        timeout (int): Seconds to wait for the request before timing out (default: 30).
    
    Returns:
        str: The decoded response body.
    
    Raises:
        urllib.error.HTTPError: If the HTTP request returns an error status.
        urllib.error.URLError: For other network-related errors.
    """
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    # Try utf-8, fall back to latin-1
    for enc in ("utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def save(filename: str, content: str) -> Path:
    """
    Write content to TARGET_DIR as a UTF-8 text file named "<filename>.txt".
    
    Returns:
        Path: Path to the written file.
    """
    path = TARGET_DIR / f"{filename}.txt"
    path.write_text(content, encoding="utf-8")
    return path


def already_have(filename: str) -> bool:
    """
    Check whether a previously saved text file for the given slug exists and is larger than 1000 bytes.
    
    Parameters:
        filename (str): Base filename/slug (without extension) to check inside the target directory.
    
    Returns:
        bool: `true` if TARGET_DIR/<filename>.txt exists and its size is greater than 1000 bytes, `false` otherwise.
    """
    p = TARGET_DIR / f"{filename}.txt"
    return p.exists() and p.stat().st_size > 1000


# ────────────────────────────────────────────────────────────────────
def collect_wikipedia(skip_existing: bool, filter_text: str = None) -> int:
    """
    Collect plain-text extracts of the configured Wikipedia topics and save them as files.
    
    Applies an optional case-insensitive substring filter to topic titles and, when
    skip_existing is True, skips topics whose output file already exists and meets
    the cache criteria. Only extracts that meet the script's minimum-length check
    are saved.
    
    Parameters:
        skip_existing (bool): If True, do not re-download topics that already exist.
        filter_text (str | None): Case-insensitive substring used to limit which topics are processed.
    
    Returns:
        int: Number of topics that were saved or counted as cached.
    """
    print(f"\n[Wikipedia] {len(WIKI_TOPICS)} topics")
    count = 0
    for topic in WIKI_TOPICS:
        if filter_text and filter_text.lower() not in topic.lower():
            continue
        slug = f"wiki_{topic.lower().replace('/', '_')}"
        if skip_existing and already_have(slug):
            print(f"  ✓ {slug} (cached)")
            count += 1
            continue
        # Use action API with extract endpoint (returns plain text reliably)
        url = ("https://en.wikipedia.org/w/api.php?"
               "action=query&prop=extracts&explaintext=1&exsectionformat=plain&"
               f"format=json&titles={urllib.parse.quote(topic)}")
        try:
            import json as _json
            raw = fetch(url)
            data = _json.loads(raw)
            pages = data.get("query", {}).get("pages", {})
            text = ""
            for pid, pdata in pages.items():
                if pid != "-1":
                    text = pdata.get("extract", "")
                    break
            if not text:
                raise ValueError("empty extract")
            if len(text) < 500:
                print(f"  ✗ {slug}: too short ({len(text)}b)")
                continue
            save(slug, text)
            print(f"  ✓ {slug} ({len(text):,}b)")
            count += 1
            time.sleep(0.4)
        except urllib.error.HTTPError as e:
            print(f"  ✗ {slug}: HTTP {e.code}")
        except Exception as e:
            print(f"  ✗ {slug}: {e}")
    return count


def collect_sep(skip_existing: bool, filter_text: str = None) -> int:
    """
    Download and save plain-text main content for the configured Stanford Encyclopedia of Philosophy entries.
    
    Fetches each entry page, extracts the section between the page's main content and its bibliography, strips scripts/styles and HTML tags, collapses whitespace, and saves the cleaned text as "sep_<entry>.txt" when the resulting content length exceeds 1000 bytes.
    
    Parameters:
        skip_existing (bool): If True, skip entries that already exist locally with sufficient size.
        filter_text (str | None): Optional case-insensitive substring filter applied to the entry slug; only matching entries are processed.
    
    Returns:
        int: Number of entries saved or counted as cached.
    """
    print(f"\n[Stanford Encyclopedia of Philosophy] {len(SEP_ENTRIES)} entries")
    count = 0
    for entry in SEP_ENTRIES:
        if filter_text and filter_text.lower() not in entry.lower():
            continue
        slug = f"sep_{entry.replace('-', '_')}"
        if skip_existing and already_have(slug):
            print(f"  ✓ {slug} (cached)")
            count += 1
            continue
        url = f"https://plato.stanford.edu/entries/{entry}/"
        try:
            html = fetch(url)
            # SEP main content is between <div id="main-text"> and the bibliography.
            # Crude but effective extraction:
            start = html.find('id="main-text"')
            end = html.find('id="bibliography"')
            if start > 0 and end > start:
                excerpt = html[start:end]
                # Strip HTML tags
                import re
                excerpt = re.sub(r"<script[^>]*>.*?</script>", "", excerpt, flags=re.S)
                excerpt = re.sub(r"<style[^>]*>.*?</style>", "", excerpt, flags=re.S)
                excerpt = re.sub(r"<[^>]+>", " ", excerpt)
                excerpt = re.sub(r"\s+", " ", excerpt).strip()
                if len(excerpt) > 1000:
                    save(slug, excerpt)
                    print(f"  ✓ {slug} ({len(excerpt):,}b)")
                    count += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"  ✗ {slug}: {e}")
    return count


def collect_gutenberg(skip_existing: bool, filter_text: str = None) -> int:
    """
    Downloads selected Project Gutenberg books from the predefined list and saves them as UTF-8 `.txt` files in the target directory.
    
    Parameters:
        skip_existing (bool): If True, skip books whose output file already exists and exceeds the minimum cached size.
        filter_text (str | None): Optional case-insensitive substring to filter which book slugs are processed.
    
    Returns:
        int: Number of books that were saved or found cached.
    """
    print(f"\n[Project Gutenberg] {len(GUTENBERG_BOOKS)} books")
    count = 0
    for slug, url in GUTENBERG_BOOKS:
        if filter_text and filter_text.lower() not in slug.lower():
            continue
        full = f"gutenberg_{slug}"
        if skip_existing and already_have(full):
            print(f"  ✓ {full} (cached)")
            count += 1
            continue
        try:
            text = fetch(url)
            if len(text) < 5000:
                print(f"  ✗ {full}: too short ({len(text)}b)")
                continue
            save(full, text)
            print(f"  ✓ {full} ({len(text):,}b)")
            count += 1
            time.sleep(1.0)
        except Exception as e:
            print(f"  ✗ {full}: {e}")
    return count


def collect_arxiv(skip_existing: bool, filter_text: str = None) -> int:
    """
    Collects arXiv listing pages, cleans them to plain text, and saves each as "<slug>.txt" in the target directory.
    
    Parameters:
        skip_existing (bool): If True, skip items whose output file already exists and appears complete.
        filter_text (str | None): If provided, only process feeds whose slug contains this substring (case-insensitive).
    
    Returns:
        int: Number of feeds saved or counted as cached.
    """
    print(f"\n[arXiv math feeds] {len(ARXIV_FEEDS)} feeds")
    count = 0
    for slug, url in ARXIV_FEEDS:
        if filter_text and filter_text.lower() not in slug.lower():
            continue
        if skip_existing and already_have(slug):
            print(f"  ✓ {slug} (cached)")
            count += 1
            continue
        try:
            html = fetch(url)
            import re
            # Strip everything but text content
            text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.S)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.S)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) < 1000:
                print(f"  ✗ {slug}: too short")
                continue
            save(slug, text)
            print(f"  ✓ {slug} ({len(text):,}b)")
            count += 1
            time.sleep(1.0)
        except Exception as e:
            print(f"  ✗ {slug}: {e}")
    return count


def collect_stacks_project(skip_existing: bool) -> int:
    """
    Download selected chapters from the Stacks Project, clean HTML to plain text, and save each as a UTF-8 `.txt` file.
    
    Parameters:
    	skip_existing (bool): If True, skip chapters whose output file already exists and appears populated.
    
    Returns:
    	int: Number of chapters saved or counted as cached.
    """
    print("\n[Stacks Project] selected chapters")
    chapters = [
        ("stacks_intro", "https://stacks.math.columbia.edu/tag/0001"),
        ("stacks_set_theory", "https://stacks.math.columbia.edu/tag/0009"),
        ("stacks_categories", "https://stacks.math.columbia.edu/tag/0011"),
        ("stacks_algebra", "https://stacks.math.columbia.edu/tag/00AO"),
        ("stacks_topology", "https://stacks.math.columbia.edu/tag/0067"),
    ]
    count = 0
    for slug, url in chapters:
        if skip_existing and already_have(slug):
            print(f"  ✓ {slug} (cached)")
            count += 1
            continue
        try:
            html = fetch(url)
            import re
            text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.S)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.S)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) > 1000:
                save(slug, text)
                print(f"  ✓ {slug} ({len(text):,}b)")
                count += 1
            time.sleep(0.8)
        except Exception as e:
            print(f"  ✗ {slug}: {e}")
    return count


def collect_nlab(skip_existing: bool) -> int:
    """
    Download a curated set of nLab pages, clean their HTML, and save each as a UTF-8 plain-text file.
    
    Iterates a fixed list of nLab page slugs, optionally skips items that already exist locally, removes script/style blocks and HTML tags, collapses whitespace, and writes pages that exceed an 800-byte content threshold as "<slug>.txt" in the target directory.
    
    Parameters:
        skip_existing (bool): If True, skip pages that are already present (and considered complete) in the target directory.
    
    Returns:
        int: Number of pages saved or counted as cached.
    """
    print("\n[nLab] selected pages")
    pages = [
        "category", "functor", "natural_transformation", "topos",
        "type_theory", "homotopy_type_theory", "monoid", "limit",
        "adjoint_functor", "Yoneda_lemma", "monad",
    ]
    count = 0
    for page in pages:
        slug = f"nlab_{page}"
        if skip_existing and already_have(slug):
            print(f"  ✓ {slug} (cached)")
            count += 1
            continue
        url = f"https://ncatlab.org/nlab/show/{page}"
        try:
            html = fetch(url)
            import re
            text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.S)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.S)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) > 800:
                save(slug, text)
                print(f"  ✓ {slug} ({len(text):,}b)")
                count += 1
            time.sleep(0.8)
        except Exception as e:
            print(f"  ✗ {slug}: {e}")
    return count


# ────────────────────────────────────────────────────────────────────
def main():
    """
    Parse command-line options, run the selected collection routines, and print a summary and next-step instructions.
    
    Parses --skip-existing, --topic-filter, and --source flags, invokes the corresponding collectors (wiki, sep, gutenberg, arxiv, stacks, nlab or all), accumulates the number of saved or cached files, prints the target directory and a final "COLLECTED N FILES" summary, and shows example /ingest commands for the saved files.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-existing", action="store_true",
                        help="don't re-download files already in target dir")
    parser.add_argument("--topic-filter", default=None,
                        help="only download topics whose slug contains this string")
    parser.add_argument("--source", default="all",
                        choices=["all", "wiki", "sep", "gutenberg", "arxiv",
                                 "stacks", "nlab"],
                        help="which source to collect (default: all)")
    args = parser.parse_args()

    print(f"Target: {TARGET_DIR}")
    total = 0

    if args.source in ("all", "wiki"):
        total += collect_wikipedia(args.skip_existing, args.topic_filter)
    if args.source in ("all", "sep"):
        total += collect_sep(args.skip_existing, args.topic_filter)
    if args.source in ("all", "gutenberg"):
        total += collect_gutenberg(args.skip_existing, args.topic_filter)
    if args.source in ("all", "arxiv"):
        total += collect_arxiv(args.skip_existing, args.topic_filter)
    if args.source in ("all", "stacks"):
        total += collect_stacks_project(args.skip_existing)
    if args.source in ("all", "nlab"):
        total += collect_nlab(args.skip_existing)

    print(f"\n{'═'*60}")
    print(f"  COLLECTED {total} FILES → {TARGET_DIR}")
    print(f"{'═'*60}")
    print("\nNext: ingest into engine. Run chat.py and:")
    print("  for f in ~/training/math/*.txt; do")
    print("      echo /ingest \"$f\" | python chat.py")
    print("  done")


if __name__ == "__main__":
    main()
