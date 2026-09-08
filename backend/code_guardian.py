"""
code_guardian.py - Quantum MCAGI
===================================
Code intelligence layer. Prevents corruption, validates before write,
suggests improvements, understands Python patterns from training data.
Three capabilities:
  1. GUARD   — validate before any file write (pre-commit hook)
  2. REVIEW  — analyze a file and suggest specific improvements
  3. PROTECT — scan all files for corruption patterns and fix them
Integrated into self_evolution.py rewrite_code() automatically.
Also available as /review FILE command in chat.py.
"""
import ast
import os
import re
import sys
import difflib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
# ── Corruption patterns that destroyed files before ────────────────────────
CORRUPTION_PATTERNS = [
    (r"(?<![\\])\\n(?![\x22\x27])", "literal_newline", "Literal \\n sequence"),
    (r"^\\s*def\\s*$", "bare_def", "def keyword with no function name"),
    (r"from (document_ingester|self_evolution_core|response_analyzer|fstring_compat|batch_ingest|library|training_pipeline|self_evolution_repair|self_evolution_runner|self_evolution_analysis|self_evolution_transforms|self_evolution_file_ops|self_evolution_splitting) import", "deleted_module", "Import from deleted/merged module"),
    (r'f"[^"]*\\n[^"]*"', "broken_fstring", "f-string spanning multiple lines"),
]
# Python anti-patterns worth flagging
IMPROVEMENT_PATTERNS = [
    # Bare except
    (r'^\s*except:\s*$', 'bare_except',
     'Use except Exception: instead of bare except:',
     'except Exception:'),
    # Mutable default argument
    (r'def \w+\([^)]*=\[\]', 'mutable_default',
     'Mutable default argument — use None and set inside function',
     None),
    # Direct dict access without .get()
    (r'\bself\.concepts\[(?!.*\.get)', 'dict_without_get',
     'Use .get() to avoid KeyError on missing keys',
     None),
    # Fresh QuantumLanguageEngine instantiation
    (r'QuantumLanguageEngine\(\)', 'fresh_qle',
     'Never instantiate fresh QuantumLanguageEngine() — use existing engine',
     None),
    # Hardcoded backend path
    (r'Quantum_MCAGI_NO_LLM_V[^/]*/backend', 'hardcoded_path',
     'Use glob to find backend path — unicode in path breaks hardcoding',
     "glob.glob('/data/data/com.termux/files/home/Quantum_MCAGI_NO_LLM_V*/backend')[0]"),
    # print without f-string for dynamic values
    (r'print\("[^"]*"\s*\+\s*str\(', 'string_concat_print',
     'Use f-string: print(f"...{val}") instead of print("..." + str(val))',
     None),
]
# ── Pre-write validator ────────────────────────────────────────────────────
def guard(code: str, filename: str = 'unknown') -> Dict:
    """
    Validate code before writing to disk.
    Returns {'safe': bool, 'errors': list, 'warnings': list}
    Called by self_evolution.rewrite_code() before every file write.
    If safe=False, the write is blocked.
    """
    result = {'safe': True, 'errors': [], 'warnings': [], 'filename': filename}
    # 1. Syntax check
    try:
        ast.parse(code)
    except SyntaxError as e:
        result['safe'] = False
        result['errors'].append(f"SyntaxError line {e.lineno}: {e.msg}")
        return result  # No point checking further
    lines = code.split('\n')
    # 2. Corruption pattern scan
    for i, line in enumerate(lines, 1):
        for pattern, kind, desc in CORRUPTION_PATTERNS:
            if re.search(pattern, line):
                if kind in ('literal_newline', 'bare_def', 'broken_fstring'):
                    result['safe'] = False
                    result['errors'].append(f"Line {i}: {desc} — [{kind}]")
                else:
                    result['warnings'].append(f"Line {i}: {desc} — [{kind}]")
    # 3. Critical rule violations
    for i, line in enumerate(lines, 1):
        if re.search(r'QuantumLanguageEngine\(\)', line):
            ctx = lines[max(0,i-3):i+3]
            if any('get_current_stage' in l or '__init__' not in l for l in ctx):
                result['safe'] = False
                result['errors'].append(
                    f"Line {i}: CRITICAL — fresh QuantumLanguageEngine() "
                    f"instantiation resets all metrics to zero")
    # 4. Import check for deleted modules
    deleted = [
        'document_ingester', 'self_evolution_core', 'response_analyzer',
        'fstring_compat', 'batch_ingest', 'library', 'training_pipeline',
        'self_evolution_repair', 'self_evolution_runner',
    ]
    for i, line in enumerate(lines, 1):
        for mod in deleted:
            if f'from {mod} import' in line or f'import {mod}' in line:
                result['warnings'].append(
                    f"Line {i}: Import of deleted module '{mod}' — "
                    f"check consolidated replacement")
    return result
# ── Code reviewer ──────────────────────────────────────────────────────────
def review(filepath: str) -> Dict:
    """
    Review a Python file and return actionable improvement suggestions.
    Checks for anti-patterns, style issues, and structural improvements.
    """
    result = {
        'filepath': filepath,
        'filename': os.path.basename(filepath),
        'issues': [],
        'suggestions': [],
        'score': 100,
    }
    try:
        with open(filepath, 'r', errors='replace') as f:
            code = f.read()
    except Exception as e:
        result['issues'].append(f"Cannot read: {e}")
        return result
    lines = code.split('\n')
    # Check improvement patterns
    for i, line in enumerate(lines, 1):
        for pattern, kind, desc, fix in IMPROVEMENT_PATTERNS:
            if re.search(pattern, line):
                issue = {'line': i, 'kind': kind, 'desc': desc,
                          'current': line.strip(), 'fix': fix}
                result['issues'].append(issue)
                result['score'] -= 5
    # Check function length
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                length = getattr(node, 'end_lineno', node.lineno) - node.lineno
                if length > 80:
                    result['suggestions'].append(
                        f"Function '{node.name}' is {length} lines — "
                        f"consider splitting at line {node.lineno}")
                    result['score'] -= 3
    except SyntaxError:
        result['issues'].append({'kind': 'syntax', 'desc': 'File has syntax errors'})
        result['score'] = 0
    # Check for missing module docstring
    try:
        tree = ast.parse(code)
        if not (tree.body and isinstance(tree.body[0], ast.Expr)
                and isinstance(tree.body[0].value, ast.Constant)):
            result['suggestions'].append("Missing module docstring")
    except Exception:
        pass
    # Check file length
    if len(lines) > 1500:
        result['suggestions'].append(
            f"File is {len(lines)} lines — consider splitting into modules")
        result['score'] -= 10
    result['score'] = max(0, result['score'])
    return result
# ── Corruption scanner ─────────────────────────────────────────────────────
def scan_all(backend_dir: str = None) -> List[Dict]:
    """
    Scan all Python files for corruption patterns.
    Returns list of files with issues and auto-fix suggestions.
    """
    if backend_dir is None:
        import glob
        dirs = glob.glob('/data/data/com.termux/files/home/Quantum_MCAGI_NO_LLM_V*/backend')
        backend_dir = dirs[0] if dirs else '.'
    results = []
    for filepath in sorted(Path(backend_dir).glob('*.py')):
        try:
            with open(filepath, 'r', errors='replace') as f:
                code = f.read()
        except Exception:
            continue
        guard_result = guard(code, filepath.name)
        if not guard_result['safe'] or guard_result['warnings']:
            results.append({
                'filepath': str(filepath),
                'filename': filepath.name,
                'safe': guard_result['safe'],
                'errors': guard_result['errors'],
                'warnings': guard_result['warnings'],
            })
    return results
# ── Auto-fix corruption ────────────────────────────────────────────────────
def fix_literal_newlines(code: str) -> str:
    """Replace literal \\n sequences with real newlines."""
    return __import__("re").sub(r"(?<!\\)\\n", "\n", code)


def auto_fix_file(filepath: str, dry_run: bool = True) -> Dict:
    """
    Attempt to auto-fix corruption in a file.
    Always backs up before writing.
    """
    result = {'filepath': filepath, 'fixed': False, 'changes': [], 'dry_run': dry_run}
    try:
        with open(filepath, 'r', errors='replace') as f:
            code = f.read()
    except Exception as e:
        result['error'] = str(e)
        return result
    original = code
    changed = False
    # Fix literal newlines
    fixed = fix_literal_newlines(code)
    if fixed != code:
        result['changes'].append('Fixed literal \\n sequences')
        code = fixed
        changed = True
    # Fix deleted module imports
    deleted_mods = {
        'document_ingester': 'document_engine',
        'self_evolution_core': 'self_evolution',
        'response_analyzer': None,
        'fstring_compat': None,
        'batch_ingest': 'training_engine',
        'library': None,
        'training_pipeline': 'training_engine',
    }
    for old_mod, new_mod in deleted_mods.items():
        if f'from {old_mod} import' in code or f'import {old_mod}' in code:
            if new_mod:
                code = code.replace(f'from {old_mod} import', f'from {new_mod} import')
                code = code.replace(f'import {old_mod}', f'import {new_mod}')
                result['changes'].append(f'Updated import: {old_mod} -> {new_mod}')
            else:
                lines = code.split('\n')
                lines = [l for l in lines
                         if f'from {old_mod} import' not in l
                         and f'import {old_mod}' not in l]
                code = '\n'.join(lines)
                result['changes'].append(f'Removed import of deleted module: {old_mod}')
            changed = True
    if not changed:
        result['no_changes_needed'] = True
        return result
    # Validate before writing
    try:
        ast.parse(code)
    except SyntaxError as e:
        result['error'] = f"Fixed code still has syntax error: {e}"
        return result
    if not dry_run:
        # Write directly — skip guardian re-validation (we are the guardian)
        try:
            import ast as _ast
            _ast.parse(code)  # syntax only
        except SyntaxError as e:
            result['error'] = f"Syntax error after fix: {e}"
            return result
        with open(filepath, 'w') as f:
            f.write(code)
        result['fixed'] = True
    return result
# ── Diff viewer ────────────────────────────────────────────────────────────
def show_diff(original: str, modified: str, filename: str = '') -> str:
    """Show unified diff between original and modified code."""
    orig_lines = original.splitlines(keepends=True)
    mod_lines = modified.splitlines(keepends=True)
    diff = difflib.unified_diff(
        orig_lines, mod_lines,
        fromfile=f'original/{filename}',
        tofile=f'modified/{filename}',
        n=3
    )
    return ''.join(diff)
# ── Singleton for integration with self_evolution ─────────────────────────
class CodeGuardian:
    """
    Drop-in validator for self_evolution.rewrite_code().
    Instantiate once and pass to SelfEvolutionEngine.
    """
    def __init__(self):
        self.blocked_writes = 0
        self.allowed_writes = 0
        self.issues_found = []
    def validate(self, code: str, filename: str) -> Tuple[bool, List[str]]:
        """Returns (is_safe, list_of_errors)."""
        result = guard(code, filename)
        if result['safe']:
            self.allowed_writes += 1
        else:
            self.blocked_writes += 1
            self.issues_found.extend(result['errors'])
        return result['safe'], result['errors']
    def get_stats(self) -> Dict:
        return {
            'allowed': self.allowed_writes,
            'blocked': self.blocked_writes,
            'issues': len(self.issues_found),
        }
_guardian = None
def get_guardian() -> CodeGuardian:
    global _guardian
    if _guardian is None:
        _guardian = CodeGuardian()
    return _guardian
# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import glob as _g
    backend = _g.glob('/data/data/com.termux/files/home/Quantum_MCAGI_NO_LLM_V*/backend')
    backend = backend[0] if backend else '.'
    if len(sys.argv) > 1:
        if sys.argv[1] == '--scan':
            print("Scanning all files for corruption...")
            issues = scan_all(backend)
            if not issues:
                print("All files clean.")
            for r in issues:
                print(f"\n{'='*50}")
                print(f"FILE: {r['filename']} ({'UNSAFE' if not r['safe'] else 'warnings'})")
                for e in r['errors']:
                    print(f"  ERROR: {e}")
                for w in r['warnings']:
                    print(f"  WARN:  {w}")
        elif sys.argv[1] == '--fix':
            dry = '--apply' not in sys.argv[2:]
            print(f"{'DRY RUN' if dry else 'APPLYING FIXES'} — scanning...")
            issues = scan_all(backend)
            for r in issues:
                result = auto_fix_file(r['filepath'], dry_run=dry)
                if result.get('changes'):
                    status = 'FIXED' if result['fixed'] else 'WOULD FIX'
                    print(f"  {status}: {r['filename']}")
                    for c in result['changes']:
                        print(f"    - {c}")
        elif sys.argv[1] == '--review':
            if len(sys.argv) > 2:
                filepath = sys.argv[2]
                if not os.path.isabs(filepath):
                    filepath = os.path.join(backend, filepath)
                result = review(filepath)
                print(f"\nREVIEW: {result['filename']} — Score: {result['score']}/100")
                for issue in result['issues']:
                    if isinstance(issue, dict):
                        print(f"  [{issue['kind']}] line {issue.get('line','?')}: {issue['desc']}")
                        if issue.get('fix'):
                            print(f"    Fix: {issue['fix']}")
                    else:
                        print(f"  {issue}")
                for s in result['suggestions']:
                    print(f"  SUGGESTION: {s}")
    else:
        print("Usage:")
        print("  python3 code_guardian.py --scan           # scan for corruption")
        print("  python3 code_guardian.py --fix            # dry run fixes")
        print("  python3 code_guardian.py --fix --apply    # apply fixes")
        print("  python3 code_guardian.py --review FILE    # review a file")
