#!/data/data/com.termux/files/usr/bin/env python3
"""
Patch C — Backfill FunctionWordEngine from existing corpus
============================================================
Walks every .txt file in known training directories, runs each through
FunctionWordEngine.update_from_text(), and saves dossiers to:
~/.quantum-mcagi/function_words.json
Sources scanned (in order):
1. ~/training/math/
— collected math corpus (~102 files)
2. ~/training/
— anything else under training
3. ~/.quantum-mcagi/conversations.json — past chat history (text only)
After completion, the engine has dossiers from day one and Patch B's
generation re-ranker has real data to consult.
Usage:
python backfill_function_words.py
python backfill_function_words.py --dry-run
python backfill_function_words.py --limit 20
"""

# report counts only
# first 20 files

import os
import sys
import argparse
import json
import time
from pathlib import Path
BACKEND = Path(os.path.expanduser("~/Quantum_MCAGI_NO_LLM_V⁰²/backend"))
sys.path.insert(0, str(BACKEND))
OUTPUT = Path(os.path.expanduser("~/.quantum-mcagi/function_words.json"))

def main():
parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true",
help="report what would be ingested without saving")
parser.add_argument("--limit", type=int, default=0,
help="process at most N files (0 = all)")
parser.add_argument("--skip-conversations", action="store_true",
help="don't include past chat history")
args = parser.parse_args()
print("Loading FunctionWordEngine...")
try:
from function_word_engine import FunctionWordEngine
except ImportError as e:
print(f"■ Cannot import function_word_engine: {e}")
return 1
engine = FunctionWordEngine()
# Resume from existing dossiers if present
if OUTPUT.exists() and not args.dry_run:
if engine.load(str(OUTPUT)):
print(f"✓ Resumed from existing dossiers at {OUTPUT}")
else:
print(f"■ Could not load existing dossiers; starting fresh")
# Collect source files
sources = []
for root in [
Path(os.path.expanduser("~/training/math")),
Path(os.path.expanduser("~/training")),
]:
if root.is_dir():
for f in sorted(root.rglob("*.txt")):
if f not in sources:
sources.append(f)
if args.limit:
sources = sources[:args.limit]
if not sources:
print("■ No .txt files found in ~/training/")
if args.skip_conversations:
return 0
print(f"Found {len(sources)} text files\n")
# ■■ Process files ■■
t0 = time.time()
total_chars = 0
success = 0
failed = 0
for i, fp in enumerate(sources, 1):
try:
text = fp.read_text(encoding="utf-8", errors="ignore")
if len(text) < 50:
continue
if not args.dry_run:
engine.update_from_text(text)

total_chars += len(text)
success += 1
if i % 10 == 0 or i == len(sources):
print(f" [{i}/{len(sources)}] processed ({total_chars:,} chars)")
except Exception as e:
print(f" ✗ {fp.name}: {e}")
failed += 1
# ■■ Past chat history ■■
if not args.skip_conversations:
conv_path = Path(os.path.expanduser("~/.quantum-mcagi/conversations.json"))
if conv_path.exists():
try:
conv_data = json.loads(conv_path.read_text())
conv_text = []
if isinstance(conv_data, list):
for item in conv_data:
if isinstance(item, dict):
for k in ("user_input", "response", "text"):
if k in item and isinstance(item[k], str):
conv_text.append(item[k])
if conv_text:
combined = " ".join(conv_text)
if not args.dry_run:
engine.update_from_text(combined)
total_chars += len(combined)
print(f" ✓ conversations.json: "
f"{len(conv_text)} entries ({len(combined):,} chars)")
except Exception as e:
print(f" ■ Could not parse conversations.json: {e}")
elapsed = time.time() - t0
# ■■ Save dossiers ■■
if not args.dry_run:
try:
engine.save(str(OUTPUT))
saved = True
except Exception as e:
print(f"■ Save failed: {e}")
saved = False
else:
saved = False
# ■■ Report ■■
print()
print("■" * 60)
print(" FUNCTION-WORD BACKFILL COMPLETE")
print("■" * 60)
print(f" files processed: {success}")
print(f" files failed:
{failed}")
print(f" total chars:
{total_chars:,}")
print(f" total fn-words: {engine.total_function_words:,}")
print(f" unique stopwords with dossiers: {len(engine.stats):,}")
print(f" elapsed:
{elapsed:.1f}s")
if saved:
size_kb = OUTPUT.stat().st_size / 1024
print(f" saved:
{OUTPUT} ({size_kb:.1f} KB)")
elif args.dry_run:
print(f" dry-run: nothing saved")
print("■" * 60)
print()
print("Inspect a dossier:")
print(' python -c "from function_word_engine import FunctionWordEngine;'
' e=FunctionWordEngine(); e.load(\\"' + str(OUTPUT) + '\\");'
' import json; print(json.dumps(e.get_dossier(\\"the\\"), indent=2))"')
return 0

if __name__ == "__main__":
sys.exit(main())

