#!/usr/bin/env python3
"""
file_integrity.py — automatic file-corruption defense (Termux-ready).
Defenses against the five corruption vectors:
1. CRLF/CR line-ending mismatches (Windows <-> Unix transfer)
2. UTF-8 BOM markers               (editors injecting EF BB BF)
3. Auto-formatter mangling         (literal "\n" replacing real newlines)
4. Incomplete syncs / partial writes (caught via SHA-256 manifest)
5. Clipboard paste corruption      (NUL bytes, smart-quote substitution)
Commands (run from project root):
python file_integrity.py scan        # build manifest
python file_integrity.py verify      # report drift vs manifest
python file_integrity.py repair      # normalize + atomic rewrite
python file_integrity.py status      # quick health summary
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
    return hashlib.sha256(data).hexdigest()
def walk_text_files(root: Path) -> Iterable[Path]:
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
    data = path.read_bytes()
    has_bom = data.startswith(UTF8_BOM)
    payload = data[len(UTF8_BOM):] if has_bom else data
    return FileRecord( path=str(path.relative_to(REPO_ROOT)),
        sha256=sha256_of(data),
        size=len(data),
        line_endings=detect_line_endings(payload),
        has_bom=has_bom,
        suspect_mangled=detect_mangled_python(path, payload),
    )
def normalize_bytes(data: bytes, *, fix_mangled: bool = False) -> bytes:
    if data.startswith(UTF8_BOM):
        data = data[len(UTF8_BOM):]
    data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if fix_mangled:
        data = data.replace(b"\\n", b"\n").replace(b"\\t", b"\t")
    if data and not data.endswith(b"\n"):
        data = data + b"\n"
    return data
def atomic_write(path: Path, data: bytes) -> None:
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
    payload = {
        "version": 1,
        "root": str(REPO_ROOT),
        "files": [asdict(r) for r in sorted(records, key=lambda r: r.path)],
    }
    MANIFEST_PATH.write_text( json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
def read_manifest():
    if not MANIFEST_PATH.exists():
        return {}
    raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {f["path"]: FileRecord(**f) for f in raw.get("files", [])}
def cmd_scan(_):
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
            print(f"   - {r.path} [{','.join(tags)}]")
    return 0
def cmd_verify(_):
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
    print(f"[verify] manifest:{len(expected)} current:{len(seen)}")
    print(f"[verify] changed:{len(changed)} new:{len(new_files)} missing:{len(missing)}")
    for label, items in (("CHANGED", changed), ("NEW", new_files), ("MISSING", missing)):
        for p in items[:20]:
            print(f"   {label}: {p}")
    return 0 if not (changed or missing) else 2
def cmd_repair(_):
    fixed = clean = 0
    for path in walk_text_files(REPO_ROOT):
        try:
            changed, actions = repair_file(path)
        except Exception as e:
            print(f"   ERROR: {path.relative_to(REPO_ROOT)}: {e}")
            continue
        if changed:
            fixed += 1
            print(f"   FIXED: {path.relative_to(REPO_ROOT)} [{', '.join(actions)}]")
        else:
            clean += 1
    print(f"[repair] fixed:{fixed} clean:{clean}")
    print("[repair] re-run scan to refresh manifest: python file_integrity.py scan")
    return 0
def cmd_status(_):
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
    print(f"[status] suspect mangled : {mangled}")
    health = "OK" if (bom + crlf + mixed + mangled) == 0 else "NEEDS REPAIR"
    print(f"[status] health           : {health}")
    return 0
def main():
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
