"""
Quantum MCAGI — Library Module
Browse and download books from Project Gutenberg for Markov chain training.
70,000+ free books. Feed the AI everything. Let it find its own connections.
"""

import os
import re
import json
from pathlib import Path

try:
    import internetarchive
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

LIBRARY_DIR = os.path.expanduser("~/.quantum-mcagi/library")
LIBRARY_INDEX = os.path.expanduser("~/.quantum-mcagi/library/index.json")

# Curated starter categories with Gutenberg IDs
CATEGORIES = {
    'philosophy': [
        (1497, "The Republic - Plato"),
        (2680, "Meditations - Marcus Aurelius"),
        (5827, "The Problems of Philosophy - Bertrand Russell"),
        (4280, "The Critique of Pure Reason - Immanuel Kant"),
        (1232, "The Prince - Machiavelli"),
        (3600, "Thus Spake Zarathustra - Nietzsche"),
        (10616, "The Art of War - Sun Tzu"),
    ],
    'science': [
        (49010, "The Feynman Lectures (selections)"),
        (5001, "The Origin of Species - Darwin"),
        (36114, "Relativity - Einstein"),
        (14725, "The Problems of Science - Federigo Enriques"),
    ],
    'fiction_classic': [
        (84, "Frankenstein - Mary Shelley"),
        (1342, "Pride and Prejudice - Jane Austen"),
        (11, "Alice in Wonderland - Lewis Carroll"),
        (1661, "Sherlock Holmes - Arthur Conan Doyle"),
        (2701, "Moby Dick - Herman Melville"),
        (1952, "The Yellow Wallpaper - Charlotte Perkins Gilman"),
        (98, "A Tale of Two Cities - Charles Dickens"),
    ],
    'fiction_scifi': [
        (35, "The Time Machine - H.G. Wells"),
        (36, "The War of the Worlds - H.G. Wells"),
        (62, "A Princess of Mars - Edgar Rice Burroughs"),
        (20898, "The Skylark of Space - E.E. Smith"),
        (29728, "The Galaxy Primes - E.E. Smith"),
    ],
    'poetry': [
        (1065, "Leaves of Grass - Walt Whitman"),
        (1321, "Paradise Lost - John Milton"),
        (100, "Complete Works of Shakespeare"),
        (4300, "Ulysses - James Joyce"),
        (1064, "The Divine Comedy - Dante"),
    ],
    'religion': [
        (10, "King James Bible"),
        (2500, "Siddhartha - Hermann Hesse"),
        (2680, "Meditations - Marcus Aurelius"),
        (7118, "The Quran"),
        (2852, "The Tao Te Ching - Lao Tzu"),
        (16295, "The Bhagavad Gita"),
    ],
    'psychology': [
        (14969, "The Interpretation of Dreams - Sigmund Freud"),
        (5116, "The Psychology of the Unconscious - Carl Jung"),
    ],
    'history': [
        (46, "A Christmas Carol - Charles Dickens"),
        (3207, "Leviathan - Thomas Hobbes"),
        (7370, "The Histories - Herodotus"),
        (2680, "Meditations - Marcus Aurelius"),
    ],
    'humor': [
        (76, "Adventures of Huckleberry Finn - Mark Twain"),
        (1400, "Great Expectations - Charles Dickens"),
        (74, "Adventures of Tom Sawyer - Mark Twain"),
    ],
    'children': [
        (16, "Peter Pan - J.M. Barrie"),
        (514, "Little Women - Louisa May Alcott"),
        (55, "The Wonderful Wizard of Oz - L. Frank Baum"),
        (32, "Herland - Charlotte Perkins Gilman"),
    ],
    'technical': [
        (10, "King James Bible"),  # massive vocabulary
        (4363, "Calculus Made Easy - Silvanus Thompson"),
    ],
}


def ensure_library_dir():
    """ensure_library_dir - Auto-documented by self-evolution."""
    Path(LIBRARY_DIR).mkdir(parents=True, exist_ok=True)


def get_gutenberg_url(book_id):
    """Get the plain text URL for a Gutenberg book."""
    return f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"


def download_book(book_id, title="Unknown"):
    """Download a book from Project Gutenberg."""
    if not HAS_REQUESTS:
        return None, "requests module not installed"

    ensure_library_dir()
    filepath = os.path.join(LIBRARY_DIR, f"gutenberg_{book_id}.txt")

    if os.path.exists(filepath):
        return filepath, "already downloaded"

    url = get_gutenberg_url(book_id)
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            text = r.text

            # Strip Gutenberg header/footer
            text = strip_gutenberg_header(text)

            with open(filepath, 'w', errors='replace') as f:
                f.write(text)

            # Update index
            update_index(book_id, title, filepath, len(text.split()))
            return filepath, f"downloaded ({len(text.split())} words)"
        else:
            return None, f"HTTP {r.status_code}"
    except Exception as e:
        return None, str(e)


def strip_gutenberg_header(text):
    """Remove Project Gutenberg header and footer boilerplate."""
    # Find start of actual content
    start_markers = [
        "*** START OF THIS PROJECT GUTENBERG",
        "*** START OF THE PROJECT GUTENBERG",
        "***START OF",
    ]
    for marker in start_markers:
        idx = text.find(marker)
        if idx >= 0:
            # Find the next newline after the marker
            nl = text.find('\n', idx)
            if nl >= 0:
                text = text[nl+1:]
            break

    # Find end of actual content
    end_markers = [
        "*** END OF THIS PROJECT GUTENBERG",
        "*** END OF THE PROJECT GUTENBERG",
        "***END OF",
        "End of the Project Gutenberg",
        "End of Project Gutenberg",
    ]
    for marker in end_markers:
        idx = text.find(marker)
        if idx >= 0:
            text = text[:idx]
            break

    return text.strip()


def update_index(book_id, title, filepath, word_count):
    """Update the library index."""
    ensure_library_dir()
    index = load_index()
    index[str(book_id)] = {
        'title': title,
        'filepath': filepath,
        'words': word_count,
        'trained': False,
    }
    with open(LIBRARY_INDEX, 'w') as f:
        json.dump(index, f, indent=2)


def load_index():
    """Load library index."""
    if os.path.exists(LIBRARY_INDEX):
        try:
            with open(LIBRARY_INDEX, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def mark_trained(book_id):
    """Mark a book as trained on."""
    index = load_index()
    key = str(book_id).replace("arc_", "") if str(book_id).startswith("arc_") else str(book_id)
    if key in index:
        index[key]['trained'] = True
        with open(LIBRARY_INDEX, 'w') as f:
            json.dump(index, f, indent=2)


def search_gutenberg(query):
    """Search Project Gutenberg for books."""
    if not HAS_REQUESTS:
        return []

    try:
        url = f"https://gutendex.com/books/?search={query}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            results = []
            for book in data.get('results', [])[:10]:
                bid = book.get('id')
                title = book.get('title', 'Unknown')
                authors = ', '.join(a.get('name', '') for a in book.get('authors', []))
                results.append({
                    'id': bid,
                    'title': title,
                    'author': authors,
                    'downloads': book.get('download_count', 0),
                })
            return results
    except Exception:
        pass
    return []


def list_categories():
    """List available curated categories."""
    lines = []
    for cat, books in CATEGORIES.items():
        lines.append(f"  {cat} ({len(books)} books)")
        for bid, title in books[:3]:
            lines.append(f"    {bid}: {title}")
        if len(books) > 3:
            lines.append(f"    ... and {len(books)-3} more")
    return '\n'.join(lines)


def list_library():
    """List downloaded and trained books."""
    index = load_index()
    if not index:
        return "  Library is empty. Use /library browse or /library download ID"
    lines = []
    total_words = 0
    trained_count = 0
    for bid, info in index.items():
        status = "TRAINED" if info.get('trained') else "downloaded"
        lines.append(f"  [{bid}] {info['title']} ({info['words']} words) [{status}]")
        total_words += info.get('words', 0)
        if info.get('trained'):
            trained_count += 1
    lines.append(f"\n  Total: {len(index)} books, {total_words} words, {trained_count} trained")
    return '\n'.join(lines)


def download_category(category):
    """Download all books in a category."""
    if category not in CATEGORIES:
        return f"Unknown category: {category}\nAvailable: {', '.join(CATEGORIES.keys())}"

    results = []
    for bid, title in CATEGORIES[category]:
        filepath, status = download_book(bid, title)
        results.append(f"  {title}: {status}")
    return '\n'.join(results)


# ============================================================================
# CHAT COMMAND HANDLER
# ============================================================================

def handle_library_command(cmd_parts, engine=None):
    """
    Handle /library commands from chat.py

    /library                    — show help
    /library browse             — list categories
    /library category NAME      — download a whole category
    /library search QUERY       — search Gutenberg
    /library download ID        — download specific book
    /library list               — show downloaded books
    /library train ID           — train on a downloaded book
    /library train-all          — train on all untrained books
    """
    if len(cmd_parts) < 2:
        return """  Library Commands:
  /library browse              — browse curated categories
  /library category NAME       — download entire category
  /library search QUERY        — search Project Gutenberg
  /library download ID TITLE   — download book by Gutenberg ID
  /library list                — show downloaded books
  /library train ID            — train Markov chain on a book
  /library train-all           — train on all untrained books"""

    subcmd = cmd_parts[1].lower()

    if subcmd == 'browse':
        return list_categories()

    elif subcmd == 'category' and len(cmd_parts) > 2:
        cat = cmd_parts[2].lower()
        return download_category(cat)

    elif subcmd == 'search' and len(cmd_parts) > 2:
        query = ' '.join(cmd_parts[2:])
        results = search_gutenberg(query)
        if not results:
            return "  No results found."
        lines = []
        for r in results:
            lines.append(f"  [{r['id']}] {r['title']} by {r['author']} ({r['downloads']} downloads)")
        lines.append(f"\n  Download with: /library download ID")
        return '\n'.join(lines)

    elif subcmd == 'download' and len(cmd_parts) > 2:
        try:
            bid = int(cmd_parts[2])
        except ValueError:
            return "  Invalid book ID. Use a number."
        title = ' '.join(cmd_parts[3:]) if len(cmd_parts) > 3 else f"Book {bid}"
        filepath, status = download_book(bid, title)
        if filepath:
            return f"  Downloaded: {title} ({status})\n  Train with: /library train {bid}"
        return f"  Failed: {status}"

    elif subcmd == 'list':
        return list_library()

    elif subcmd == 'train' and len(cmd_parts) > 2 and engine:
        try:
            bid = int(cmd_parts[2])
        except ValueError:
            return "  Invalid book ID."
        index = load_index()
        key = str(bid)
        if key not in index:
            return f"  Book {bid} not downloaded. Use /library download {bid} first."
        filepath = index[key]['filepath']
        if not os.path.exists(filepath):
            return f"  File missing: {filepath}"
        with open(filepath, 'r', errors='ignore') as f:
            text = f.read()
        engine.learn_from_text(text)
        mark_trained(bid)
        return f"  Trained on: {index[key]['title']} ({len(text.split())} words)\n  Chain: {len(engine.markov.chain)} states"

    elif subcmd == 'train-all' and engine:
        index = load_index()
        trained = 0
        for bid, info in index.items():
            if not info.get('trained') and os.path.exists(info['filepath']):
                with open(info['filepath'], 'r', errors='ignore') as f:
                    text = f.read()
                engine.learn_from_text(text)
                try:
                    mark_trained(int(bid))
                except (ValueError, TypeError):
                    mark_trained(bid)
                trained += 1
                print(f"  Trained: {info['title']}")
        return f"  Trained on {trained} books. Chain: {len(engine.markov.chain)} states"


    elif subcmd == 'search-archive' and len(cmd_parts) > 2:
        query = ' '.join(cmd_parts[2:])
        print(f"  Searching Archive.org for '{query}'...")
        results = search_archive(query)
        if not results:
            return "  No results found on Archive.org."
        lines = []
        for i, r in enumerate(results):
            lines.append(f"  [{i+1}] {r['id']}\n       {r['title'][:70]}")
        lines.append("\n  Download with: /library download-archive IDENTIFIER")
        return '\n'.join(lines)

    elif subcmd == 'download-archive' and len(cmd_parts) > 2:
        identifier = cmd_parts[2]
        filepath, status = download_archive(identifier)
        if filepath:
            return f"  Archive.org: {identifier}\n  Status: {status}\n  Train with: /library train-archive {identifier}"
        return f"  Failed: {status}"

    elif subcmd == 'train-archive' and len(cmd_parts) > 2 and engine:
        identifier = cmd_parts[2]
        filepath = os.path.join(LIBRARY_DIR, f"archive_{identifier}.txt")
        if not os.path.exists(filepath):
            filepath2, status = download_archive(identifier)
            if not filepath2:
                return f"  Download failed: {status}"
            filepath = filepath2
        with open(filepath, 'r', errors='ignore') as f:
            text = f.read()
        engine.learn_from_text(text)
        word_count = len(text.split())
        return f"  Trained on Archive.org '{identifier}' — {word_count:,} words\n  Chain: {len(engine.markov.chain)} states"

    return "  Unknown library command. Type /library for help."


if __name__ == "__main__":
    print("Library Module — Testing")
    print()
    print("Categories:")
    print(list_categories())
    print()
    print("Searching for 'shakespeare'...")
    results = search_gutenberg("shakespeare")
    for r in results[:3]:
        print(f"  [{r['id']}] {r['title']} by {r['author']}")


# ============================================================================
# ARCHIVE.ORG INTEGRATION
# ============================================================================

def search_archive(query, rows=20):
    """Search Archive.org full-text library. Returns list of {id, title}."""
    if not HAS_REQUESTS:
        return []
    import urllib.parse
    encoded = urllib.parse.quote(query)
    url = (
        f"https://archive.org/advancedsearch.php?"
        f"q={encoded}+AND+mediatype:texts+AND+licenseurl:*&fl[]=identifier&fl[]=title"
        f"&output=json&rows={rows}"
    )
    try:
        r = requests.get(url, timeout=15)
        docs = r.json().get("response", {}).get("docs", [])
        return [{"id": d.get("identifier",""), "title": d.get("title","Unknown")} for d in docs]
    except Exception as e:
        return []


def download_archive(identifier, max_chars=80000):
    """Download text from Archive.org by identifier using internetarchive."""
    ensure_library_dir()
    filepath = os.path.join(LIBRARY_DIR, f"archive_{identifier}.txt")

    if os.path.exists(filepath):
        return filepath, "already downloaded"

    try:
        import internetarchive as ia
        item = ia.get_item(identifier)
        for f in item.get_files():
            name = f.name
            if name.endswith('_djvu.txt') or name.endswith('.txt'):
                tmp = os.path.join(LIBRARY_DIR, name)
                f.download(destdir=LIBRARY_DIR)
                if os.path.exists(tmp):
                    with open(tmp, 'r', errors='ignore') as fh:
                        text = fh.read(max_chars)
                    os.rename(tmp, filepath)
                    word_count = len(text.split())
                    update_index(f"arc_{identifier}", identifier, filepath, word_count)
                    return filepath, f"downloaded ({word_count:,} words)"
        return None, "no text file found in item"
    except Exception as e:
        return None, str(e)
