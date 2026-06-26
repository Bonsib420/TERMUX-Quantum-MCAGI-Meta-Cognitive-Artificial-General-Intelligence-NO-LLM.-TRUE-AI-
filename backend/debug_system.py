#!/usr/bin/env python3
"""Full system debug: syntax-check and import every backend module, report all
errors and categorize their root causes. Run from anywhere:

    python backend/debug_system.py
"""
import sys, os, importlib, traceback, py_compile, glob
from collections import Counter

BACKEND = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

_SELF = os.path.splitext(os.path.basename(__file__))[0]
py_files = sorted(glob.glob(os.path.join(BACKEND, "*.py")))
mods = [os.path.splitext(os.path.basename(f))[0] for f in py_files
        if os.path.splitext(os.path.basename(f))[0] != _SELF]

print(f"=== STAGE 1: SYNTAX CHECK ({len(py_files)} files) ===")
syntax_errors = []
for f in py_files:
    try:
        py_compile.compile(f, doraise=True)
    except py_compile.PyCompileError as e:
        last = str(e).splitlines()[-1] if str(e) else "syntax error"
        syntax_errors.append((os.path.basename(f), last))
for name, err in syntax_errors:
    print(f"  SYNTAX ERR  {name}: {err}")
print(f"  syntax errors: {len(syntax_errors)}/{len(py_files)}")

print(f"\n=== STAGE 2: IMPORT CHECK ({len(mods)} modules) ===")
ok, failed = [], []
for m in mods:
    try:
        importlib.import_module(m)
        ok.append(m)
    except BaseException as e:
        failed.append((m, f"{type(e).__name__}: {e}"))

for m, msg in failed:
    print(f"  IMPORT FAIL  {m}: {msg}")
print(f"\n  imported OK: {len(ok)}/{len(mods)}   failed: {len(failed)}")

print("\n=== STAGE 3: FAILURE CATEGORIES ===")
cats = Counter()
for m, msg in failed:
    if msg.startswith("ModuleNotFoundError"):
        cats[f"missing dep: {msg.split(chr(39))[1] if chr(39) in msg else msg}"] += 1
    elif msg.startswith("ImportError"):
        cats["ImportError (intra-module)"] += 1
    elif msg.startswith("SyntaxError"):
        cats["SyntaxError"] += 1
    else:
        cats[msg.split(':')[0]] += 1
for c, n in cats.most_common():
    print(f"  [{n}] {c}")

sys.exit(1 if (syntax_errors or failed) else 0)
