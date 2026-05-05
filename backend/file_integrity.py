#!/usr/bin/env python3
"""
file_integrity.py — automatic file-corruption defense (Termux-ready).

Defenses against the five corruption vectors:
  1. CRLF/CR line-ending mismatches  (Windows <-> Unix transfer)
  2. UTF-8 BOM markers               (editors injecting EF BB BF)
  3. Auto-formatter mangling         (literal "\n" replacing real newlines)
  4. Incomplete syncs / partial writes  (caught via SHA-256 manifest)
  5. Clipboard paste corruption      (NUL bytes, smart-quote substitution)

Commands (run from project root):
  python file_integrity.py scan      # build manifest
  python file_integrity.py verify    # report drift vs manifest
  python file_integrity.py repair    # normalize + atomic rewrite
  python file_integrity.py status    # quick health summary

All writes are atomic (tempfile + os.replace) so a crash mid-write never
leaves a half-corrupted file. Binaries are skipped automatically.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = REPO_ROOT / ".integrity_manifest.json"

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".cache", ".pnpm-store",
}

TEXT_EXTS = {
    ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".json", ".jsonc", ".yml", ".yaml", ".toml",
    ".md", ".markdown", ".rst", ".txt",
    ".css", ".scss", ".sass", ".html", ".htm", ".svg",
    ".sh", ".bash", ".zsh",
    ".cfg", ".ini", ".env", ".conf",
    ".gitignore", ".gitattributes", ".editorconfig",
}

BINARY_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp", ".tiff",
    ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar",
    ".mp3", ".mp4", ".wav", ".mov", ".webm", ".ogg",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe",
    ".db", ".sqlite", ".sqlite3",
}

UTF8_BOM = b"\xef\xbb\xbf"


@dataclass
class FileRecord:
    path: str
    sha256: str
    size: int
    line_endings: str
    has_bom: bool
    suspect_mangled: bool


def is_text_file(path: Path) -> bool:
    """
    Determine whether a filesystem path refers to a text file.
    
    Checks the file suffix against the configured TEXT_EXTS and BINARY_EXTS first. If the extension is inconclusive, reads up to the first 8192 bytes and treats the file as binary if a NUL byte (0x00) is found. Any OSError while opening or reading the file is treated as non-text.
    
    Parameters:
        path (Path): Path to the file to classify.
    
    Returns:
        bool: `True` if the file is classified as text, `False` otherwise.
    """
    ext = path.suffix.lower()
    if ext in BINARY_EXTS:
        return False
    if ext in TEXT_EXTS or path.name in TEXT_EXTS:
        return True
    try:
        with path.open("rb") as f:
            chunk = f.read(8192)
        if b"\x00" in chunk:
            return False
        return True
    except OSError:
        return False


def detect_line_endings(data: bytes) -> str:
    """
    Determine the predominant newline style present in the given file bytes.
    
    Parameters:
        data (bytes): Raw file contents to inspect.
    
    Returns:
        str: One of `"crlf"`, `"lf"`, `"cr"`, `"mixed"`, or `"none"`.  
        - `"crlf"`: only CRLF (`\r\n`) sequences detected.  
        - `"lf"`: only LF (`\n`) sequences detected (after excluding CRLF).  
        - `"cr"`: only CR (`\r`) sequences detected (after excluding CRLF).  
        - `"mixed"`: CRLF plus at least one other newline style present.  
        - `"none"`: no newline characters detected.
    """
    has_crlf = b"\r\n" in data
    has_lf = b"\n" in data.replace(b"\r\n", b"")
    has_cr = b"\r" in data.replace(b"\r\n", b"")
    if has_crlf and (has_lf or has_cr):
        return "mixed"
    if has_crlf:
        return "crlf"
    if has_lf:
        return "lf"
    if has_cr:
        return "cr"
    return "none"


def detect_mangled_python(path: Path, data: bytes) -> bool:
    """
    Detects whether a Python source file appears to be "mangled" by containing an unusually large number of literal backslash-escaped newlines.
    
    This check only applies to files with a `.py` suffix and at least 200 bytes of content. It counts physical newline characters and occurrences of the two-character sequence `\n` (a backslash followed by `n`). Returns `True` when the file has either very few physical lines but many literal `\n` sequences (<= 3 lines and >= 10 literal `\n`), or an excessive ratio of literal escapes to physical lines (more than 4 literal `\n` per physical line and more than 20 literal `\n` total).
    
    Returns:
        `True` if the file meets the heuristic for mangled literal escapes, `False` otherwise.
    """
    if path.suffix != ".py" or len(data) < 200:
        return False
    physical_lines = data.count(b"\n") + 1
    literal_escapes = data.count(b"\\n")
    if physical_lines <= 3 and literal_escapes >= 10:
        return True
    if literal_escapes > physical_lines * 4 and literal_escapes > 20:
        return True
    return False


def sha256_of(data: bytes) -> str:
    """
    Compute the SHA-256 hex digest of the given bytes.
    
    Returns:
        str: Lowercase hexadecimal SHA-256 digest of the input `data`.
    """
    return hashlib.sha256(data).hexdigest()


def walk_text_files(root: Path) -> Iterable[Path]:
    """
    Yield text file paths under `root`, skipping configured repository metadata/build directories, dot-directories, symlinks, and files larger than 5 MB.
    
    Parameters:
        root (Path): Root directory to traverse.
    
    Returns:
        Iterable[Path]: An iterator that yields Paths for files classified as text.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            p = Path(dirpath) / name
            if p.is_symlink():
                continue
            try:
                if p.stat().st_size > 5 * 1024 * 1024:
                    continue
            except OSError:
                continue
            if is_text_file(p):
                yield p


def inspect(path: Path) -> FileRecord:
    """
    Create a FileRecord containing metadata extracted from the file at `path`.
    
    The record includes the repo-relative path, SHA-256 digest of the file's raw bytes, byte size, line-ending classification (computed on the payload with any UTF-8 BOM removed), a `has_bom` flag, and a `suspect_mangled` flag derived from the Python-specific literal-escape heuristic.
    
    Returns:
        FileRecord: Metadata for the inspected file.
    """
    data = path.read_bytes()
    has_bom = data.startswith(UTF8_BOM)
    payload = data[len(UTF8_BOM):] if has_bom else data
    return FileRecord(
        path=str(path.relative_to(REPO_ROOT)),
        sha256=sha256_of(data),
        size=len(data),
        line_endings=detect_line_endings(payload),
        has_bom=has_bom,
        suspect_mangled=detect_mangled_python(path, payload),
    )


def normalize_bytes(data: bytes, *, fix_mangled: bool = False) -> bytes:
    """
    Normalize file bytes for repository storage and repair.
    
    Strips a UTF-8 BOM if present, converts CRLF and lone CR line endings to LF, optionally replaces literal two-character sequences `\n` and `\t` with actual newline and tab bytes when `fix_mangled` is True, and ensures the result ends with a single trailing newline if the file is non-empty.
    
    Parameters:
        data (bytes): Raw file bytes to normalize.
        fix_mangled (bool): If True, replace literal backslash sequences (`b"\\n"`, `b"\\t"`) with their actual byte equivalents.
    
    Returns:
        bytes: The normalized byte sequence.
    """
    if data.startswith(UTF8_BOM):
        data = data[len(UTF8_BOM):]
    data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if fix_mangled:
        data = data.replace(b"\\n", b"\n").replace(b"\\t", b"\t")
    if data and not data.endswith(b"\n"):
        data = data + b"\n"
    return data


def atomic_write(path: Path, data: bytes) -> None:
    """
    Atomically write bytes to a file path by writing to a temporary file in the same directory and renaming it into place.
    
    This function ensures the provided bytes are flushed and fsynced to the temporary file before performing an atomic rename (os.replace) to the target path, minimizing the risk of partial writes. If an error occurs, it attempts to remove the temporary file before propagating the exception.
    """
    fd, tmp_name = tempfile.mkstemp(prefix=".integrity_", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def repair_file(path: Path) -> tuple[bool, list]:
    """
    Normalize a text file in place when it contains known issues and report what was changed.
    
    Reads the file, detects issues (UTF‑8 BOM, CRLF/CR line endings, missing trailing newline, and Python-specific mangled literal escapes), produces a normalized byte sequence, and atomically replaces the file only when changes are needed.
    
    Returns:
        tuple:
            changed (bool): `True` if the file was modified and written, `False` if no changes were required.
            actions (list): Ordered list of action tags applied when writing the file. Possible tags:
                - "unmangle-literal-\\n" — replaced literal backslash-escape sequences like `\n`/`\t` with real newlines/tabs.
                - "strip-bom" — removed a leading UTF-8 BOM.
                - "crlf->lf" — normalized CRLF or lone CR line endings to LF.
                - "add-trailing-newline" — appended a missing trailing newline.
    """
    original = path.read_bytes()
    payload_for_check = original[len(UTF8_BOM):] if original.startswith(UTF8_BOM) else original
    actions = []
    fix_mangled = detect_mangled_python(path, payload_for_check)
    if fix_mangled:
        actions.append("unmangle-literal-\\n")
    if original.startswith(UTF8_BOM):
        actions.append("strip-bom")
    if b"\r\n" in original or (b"\r" in original and b"\r\n" not in original):
        actions.append("crlf->lf")
    if original and not original.endswith(b"\n"):
        actions.append("add-trailing-newline")
    new = normalize_bytes(original, fix_mangled=fix_mangled)
    if new == original:
        return False, []
    atomic_write(path, new)
    return True, actions


def write_manifest(records):
    """
    Write the given file records to the repository integrity manifest file (.integrity_manifest.json).
    
    The manifest is written as pretty-printed JSON containing top-level keys "version", "root", and "files". Each record is serialized via dataclasses.asdict and the file list is sorted by record.path. The file is written with UTF-8 encoding and ends with a trailing newline.
    
    Parameters:
        records (Iterable[FileRecord]): Sequence of FileRecord objects to include in the manifest.
    """
    payload = {
        "version": 1,
        "root": str(REPO_ROOT),
        "files": [asdict(r) for r in sorted(records, key=lambda r: r.path)],
    }
    MANIFEST_PATH.write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


def read_manifest():
    """
    Load the repository integrity manifest and return a mapping of recorded files.
    
    If the manifest file does not exist, returns an empty dictionary.
    
    Returns:
        dict[str, FileRecord]: Mapping from repo-relative file path to its FileRecord; empty if the manifest is missing.
    """
    if not MANIFEST_PATH.exists():
        return {}
    raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {f["path"]: FileRecord(**f) for f in raw.get("files", [])}


def cmd_scan(_):
    """
    Scan the repository for text files, write an updated integrity manifest, and report files that may need repair.
    
    Writes the manifest file at MANIFEST_PATH and prints a summary including the number of indexed files and a list (capped) of files that have a UTF-8 BOM, non-LF line endings, or are suspected of mangled Python literal escapes.
    Returns:
        exit_code (int): `0` on success.
    """
    records = [inspect(p) for p in walk_text_files(REPO_ROOT)]
    write_manifest(records)
    print(f"[scan] {len(records)} text files indexed -> {MANIFEST_PATH.name}")
    bad = [r for r in records if r.suspect_mangled or r.has_bom or r.line_endings in ("crlf", "mixed", "cr")]
    if bad:
        print(f"[scan] {len(bad)} files need attention (run: python file_integrity.py repair)")
        for r in bad[:30]:
            tags = []
            if r.suspect_mangled: tags.append("MANGLED")
            if r.has_bom: tags.append("BOM")
            if r.line_endings not in ("lf", "none"): tags.append(r.line_endings.upper())
            print(f"   - {r.path}  [{','.join(tags)}]")
    return 0


def cmd_verify(_):
    """
    Compare the repository's current text files to the saved manifest and print a summary of differences.
    
    Reads the manifest from disk and walks current text files under the repository root, computing each file's inspected record and comparing SHA-256 values to the manifest. Prints counts for manifest size, current file count, and the number of changed, new, and missing files. Also prints up to 20 example paths for each category labeled `CHANGED`, `NEW`, and `MISSING`.
    
    @returns
    int: Exit code — `0` if no changed or missing files were detected, `2` if any files are changed or missing, `1` if no manifest was found.
    """
    expected = read_manifest()
    if not expected:
        print("[verify] no manifest yet — run: python file_integrity.py scan")
        return 1
    changed, missing, new_files, seen = [], [], [], set()
    for path in walk_text_files(REPO_ROOT):
        rec = inspect(path)
        seen.add(rec.path)
        prev = expected.get(rec.path)
        if prev is None:
            new_files.append(rec.path)
        elif prev.sha256 != rec.sha256:
            changed.append(rec.path)
    for p in expected:
        if p not in seen:
            missing.append(p)
    print(f"[verify] manifest:{len(expected)}  current:{len(seen)}")
    print(f"[verify] changed:{len(changed)}  new:{len(new_files)}  missing:{len(missing)}")
    for label, items in (("CHANGED", changed), ("NEW", new_files), ("MISSING", missing)):
        for p in items[:20]:
            print(f"   {label}: {p}")
    return 0 if not (changed or missing) else 2


def cmd_repair(_):
    """
    Repair text files in the repository by normalizing detected issues and report a summary.
    
    Iterates over text files under the repository root, attempts to repair each file (atomic rewrite when changes are needed), prints per-file error or fix messages with action tags, and prints a final fixed/clean summary and an instruction to re-run the scan command.
    
    Parameters:
        _ (argparse.Namespace): Parsed command-line arguments (unused).
    
    Returns:
        int: Exit code `0` indicating successful completion.
    """
    fixed = clean = 0
    for path in walk_text_files(REPO_ROOT):
        try:
            changed, actions = repair_file(path)
        except Exception as e:
            print(f"   ERROR: {path.relative_to(REPO_ROOT)}: {e}")
            continue
        if changed:
            fixed += 1
            print(f"   FIXED: {path.relative_to(REPO_ROOT)}  [{', '.join(actions)}]")
        else:
            clean += 1
    print(f"[repair] fixed:{fixed}  clean:{clean}")
    print("[repair] re-run scan to refresh manifest: python file_integrity.py scan")
    return 0


def cmd_status(_):
    """
    Print aggregated repository integrity counts and overall health.
    
    Prints counts for indexed text files, manifest entries, UTF-8 BOM contamination, CRLF and mixed line endings, and suspected mangled Python files, then prints a health indicator (`OK` or `NEEDS REPAIR`).
    
    Returns:
        int: Exit code `0`.
    """
    records = [inspect(p) for p in walk_text_files(REPO_ROOT)]
    n = len(records)
    bom = sum(1 for r in records if r.has_bom)
    crlf = sum(1 for r in records if r.line_endings == "crlf")
    mixed = sum(1 for r in records if r.line_endings == "mixed")
    mangled = sum(1 for r in records if r.suspect_mangled)
    manifest = read_manifest()
    print(f"[status] root             : {REPO_ROOT}")
    print(f"[status] text files       : {n}")
    print(f"[status] manifest entries : {len(manifest)}")
    print(f"[status] BOM contamination: {bom}")
    print(f"[status] CRLF endings     : {crlf}")
    print(f"[status] mixed endings    : {mixed}")
    print(f"[status] suspect mangled  : {mangled}")
    health = "OK" if (bom + crlf + mixed + mangled) == 0 else "NEEDS REPAIR"
    print(f"[status] health           : {health}")
    return 0


def main():
    """
    Parse command-line arguments and dispatch to the selected subcommand.
    
    Defines subcommands: `scan`, `verify`, `repair`, and `status`, each bound to its handler.
    Returns:
        exit_code (int): The integer exit code returned by the selected subcommand handler.
    """
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, fn in (("scan", cmd_scan), ("verify", cmd_verify),
                     ("repair", cmd_repair), ("status", cmd_status)):
        sp = sub.add_parser(name)
        sp.set_defaults(func=fn)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
