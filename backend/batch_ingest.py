#!/usr/bin/env python3
"""
Quantum MCAGI — Batch Ingestion Script
Feeds all URLs from a domain list file through the engine unattended.

Features:
  - Reads URLs from any text/markdown file (extracts all https:// URLs)
  - Checkpoint file so it resumes where it left off
  - Progress display with ETA
  - Error logging without stopping
  - Saves engine state every N ingestions
  - Cloud save at intervals

Usage:
    python batch_ingest.py domains.md              # ingest all URLs
    python batch_ingest.py domains.md --resume     # resume from checkpoint
    python batch_ingest.py domains.md --dry-run    # list URLs without ingesting
    python batch_ingest.py domains.md --start 50   # start from URL #50
"""

import sys
import os
import re
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quantum_language_engine import QuantumLanguageEngine
from document_ingester import ingest_document


# ============================================================================
# CONFIG
# ============================================================================

SAVE_EVERY = 10          # Save engine state every N successful ingestions
CLOUD_SAVE_EVERY = 50    # Cloud save every N successful ingestions
CHECKPOINT_FILE = os.path.expanduser('~/.quantum-mcagi/batch_checkpoint.json')
ERROR_LOG = os.path.expanduser('~/.quantum-mcagi/batch_errors.log')
STATE_DIR = os.path.expanduser('~/.quantum-mcagi/engine_state')


# ============================================================================
# URL EXTRACTION
# ============================================================================

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
            'github.com', 'wolfram.com/cloud', 'replit.com',
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
        except:
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
        f.write(f"[{datetime.now().isoformat()}] {url}\n  Error: {error}\n\n")


# ============================================================================
# BATCH INGEST
# ============================================================================

def batch_ingest(filepath, resume=True, dry_run=False, start_at=0):
    """Run batch ingestion from a URL list file."""

    print(f"\n  ╔══ QUANTUM MCAGI — BATCH INGESTION ══════════════════")
    print(f"  ║ Source: {os.path.basename(filepath)}")

    # Extract URLs
    urls = extract_urls(filepath)
    total = len(urls)
    print(f"  ║ URLs found: {total}")

    if dry_run:
        print(f"  ║ DRY RUN — listing URLs only")
        print(f"  ╚═══════════════════════════════════════════════════\n")
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

                # Extract SVO facts into fact_store
                try:
                    import re as _re, json as _json
                    _fact_path = os.path.join(os.path.expanduser('~/.quantum-mcagi'), 'fact_store.json')
                    try:
                        with open(_fact_path) as _f:
                            _fs = _json.load(_f)
                    except Exception:
                        _fs = {}
                    _VERBS = {'is','are','was','were','has','have','contains',
                              'includes','consists','means','refers','represents',
                              'located','found','known','called','defined'}
                    _SKIP = {'this book','the book','our company','the cover',
                             'the author','the publisher','this text','the text',
                             'this page','the page','we','it','this','that','he','she','they'}
                    _new = 0
                    for _sent in _re.split(r'[.!?]+', text[2000:]):
                        _words = _sent.strip().split()
                        if not (4 <= len(_words) <= 40):
                            continue
                        for _i, _w in enumerate(_words):
                            if _w.lower() in _VERBS and _i >= 1:
                                _subj = ' '.join(_words[:_i]).strip().lower()
                                _obj = ' '.join(_words[_i+1:]).strip().lower()
                                _sw = _subj.split()
                                if (1 <= len(_sw) <= 5 and _subj not in _SKIP
                                        and not _subj.startswith('this ')
                                        and len(_obj) > 10
                                        and not any(c.isdigit() for c in _subj)):
                                    _fs.setdefault(_subj, [])
                                    _t = [_w.lower(), _obj[:120]]
                                    if _t not in _fs[_subj]:
                                        _fs[_subj].append(_t)
                                        _new += 1
                                break
                    with open(_fact_path, 'w') as _f:
                        _json.dump(_fs, _f)
                except Exception:
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
                states = len(engine.markov.chain) if hasattr(engine.markov, 'chain') else 0
                print(f"  ║   💾 Saved ({states:,} states)")
            except Exception as e:
                print(f"  ║   ⚠ Save failed: {e}")

        # Cloud save periodically
        if success_count > 0 and success_count % CLOUD_SAVE_EVERY == 0:
            try:
                from wolfram_cloud import WolframCloudProvider
                cloud = WolframCloudProvider()
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
    except:
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
    print(f"  ╚═══════════════════════════════════════════════════\n")

    # Final cloud save
    try:
        from wolfram_cloud import WolframCloudProvider
        cloud = WolframCloudProvider()
        cloud.save_state(engine)
        print("  ☁ Final cloud save complete")
    except:
        pass


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Quantum MCAGI — Batch Ingestion")
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
