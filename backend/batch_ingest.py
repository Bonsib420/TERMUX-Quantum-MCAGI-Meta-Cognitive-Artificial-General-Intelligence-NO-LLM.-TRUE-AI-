"""
📦 BATCH INGEST — Bulk Document Ingestion
==========================================
Processes multiple documents at once for feeding the Markov chain.

Supports:
  - Directory scanning (all supported file types)
  - Glob patterns: *.txt, docs/**/*.md
  - URL lists from a file
  - Progress reporting for large batches
  - Resume capability (skips already-ingested files)

Usage:
    from batch_ingest import batch_ingest_directory, batch_ingest_files

    # Ingest entire directory
    stats = batch_ingest_directory("/path/to/docs", engine)

    # Ingest specific files
    stats = batch_ingest_files(["file1.txt", "file2.pdf"], engine)
"""

import os
import glob
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable

logger = logging.getLogger("quantum_ai")

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    '.txt', '.md', '.py', '.pdf', '.docx', '.xlsx',
    '.csv', '.pptx', '.json', '.html', '.xml', '.rst',
    '.tex', '.log', '.cfg', '.ini', '.yaml', '.yml',
}

try:
    from document_ingester import handle_ingest_command, extract_txt
    HAS_INGESTER = True
except ImportError:
    HAS_INGESTER = False

    def extract_txt(filepath):
        """Fallback: read plain text files."""
        with open(filepath, 'r', errors='ignore') as f:
            return f.read()


def _extract_file_text(filepath: str) -> Optional[str]:
    """
    Extract text from a file using the document ingester.
    Falls back to plain text read for unsupported formats.
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext in ('.txt', '.md', '.py', '.log', '.cfg', '.ini',
               '.yaml', '.yml', '.rst', '.tex', '.csv'):
        try:
            with open(filepath, 'r', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Failed to read {filepath}: {e}")
            return None

    if ext == '.pdf':
        try:
            import PyPDF2
            text = []
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text.append(page.extract_text() or '')
            return '\n'.join(text)
        except Exception as e:
            logger.warning(f"Failed to read PDF {filepath}: {e}")
            return None

    if ext == '.docx':
        try:
            import docx
            doc = docx.Document(filepath)
            return '\n'.join(p.text for p in doc.paragraphs)
        except Exception as e:
            logger.warning(f"Failed to read DOCX {filepath}: {e}")
            return None

    if ext == '.json':
        try:
            import json
            with open(filepath, 'r') as f:
                data = json.load(f)
            return json.dumps(data, indent=2) if isinstance(data, (dict, list)) else str(data)
        except Exception as e:
            logger.warning(f"Failed to read JSON {filepath}: {e}")
            return None

    # Fallback: try reading as text
    try:
        with open(filepath, 'r', errors='ignore') as f:
            return f.read()
    except Exception:
        return None


def batch_ingest_directory(directory: str, engine: Any,
                           pattern: str = None,
                           progress_callback: Callable = None,
                           skip_ingested: bool = True) -> Dict:
    """
    Ingest all supported files from a directory into the engine.

    Args:
        directory: Path to scan
        engine: QuantumLanguageEngine (must have .train() or .markov.train())
        pattern: Optional glob pattern (e.g. "**/*.txt")
        progress_callback: Optional callback(current, total, filename)
        skip_ingested: Skip files already in the ingested set

    Returns:
        Stats dict with counts of processed, skipped, failed files
    """
    if not os.path.isdir(directory):
        return {"error": f"Not a directory: {directory}"}

    # Collect files
    if pattern:
        files = list(glob.glob(os.path.join(directory, pattern), recursive=True))
    else:
        files = []
        for root, _dirs, filenames in os.walk(directory):
            for fname in filenames:
                fpath = os.path.join(root, fname)
                ext = os.path.splitext(fname)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    files.append(fpath)

    return batch_ingest_files(
        files, engine,
        progress_callback=progress_callback,
        skip_ingested=skip_ingested,
    )


def batch_ingest_files(files: List[str], engine: Any,
                        progress_callback: Callable = None,
                        skip_ingested: bool = True) -> Dict:
    """
    Ingest a list of files into the engine's Markov chain.

    Args:
        files: List of file paths
        engine: Engine with .markov.train() method
        progress_callback: Optional callback(current, total, filename)
        skip_ingested: Skip files in engine._ingested_files set

    Returns:
        Stats dict
    """
    stats = {
        "total": len(files),
        "processed": 0,
        "skipped": 0,
        "failed": 0,
        "total_words": 0,
        "total_chars": 0,
        "elapsed": 0.0,
        "files_processed": [],
        "files_failed": [],
    }

    # Track already-ingested files
    ingested = set()
    if skip_ingested and hasattr(engine, '_ingested_files'):
        ingested = engine._ingested_files

    start_time = time.time()

    for idx, filepath in enumerate(files):
        filename = os.path.basename(filepath)

        # Progress callback
        if progress_callback:
            progress_callback(idx + 1, len(files), filename)

        # Skip already ingested
        if skip_ingested and filepath in ingested:
            stats["skipped"] += 1
            continue

        # Extract text
        text = _extract_file_text(filepath)
        if not text or len(text.strip()) < 10:
            stats["failed"] += 1
            stats["files_failed"].append(filename)
            continue

        # Feed to engine
        try:
            _feed_text_to_engine(text, engine)
            stats["processed"] += 1
            stats["total_words"] += len(text.split())
            stats["total_chars"] += len(text)
            stats["files_processed"].append(filename)

            # Track as ingested
            if hasattr(engine, '_ingested_files'):
                engine._ingested_files.add(filepath)
            else:
                engine._ingested_files = {filepath}
                ingested = engine._ingested_files

        except Exception as e:
            logger.warning(f"Failed to ingest {filename}: {e}")
            stats["failed"] += 1
            stats["files_failed"].append(filename)

    stats["elapsed"] = round(time.time() - start_time, 2)
    return stats


def _feed_text_to_engine(text: str, engine: Any):
    """Feed text into the engine's Markov chain."""
    if hasattr(engine, 'train'):
        engine.train(text)
    elif hasattr(engine, 'markov') and hasattr(engine.markov, 'train'):
        engine.markov.train(text)
    else:
        raise AttributeError("Engine has no train() or markov.train() method")


def format_ingest_stats(stats: Dict) -> str:
    """Format ingestion stats for terminal display."""
    lines = [
        f"  Batch ingestion complete:",
        f"    Processed: {stats['processed']} files",
        f"    Skipped:   {stats['skipped']} (already ingested)",
        f"    Failed:    {stats['failed']}",
        f"    Words:     {stats['total_words']:,}",
        f"    Time:      {stats['elapsed']:.1f}s",
    ]
    if stats.get('files_failed'):
        lines.append(f"    Failed files: {', '.join(stats['files_failed'][:5])}")
    return '\n'.join(lines)
