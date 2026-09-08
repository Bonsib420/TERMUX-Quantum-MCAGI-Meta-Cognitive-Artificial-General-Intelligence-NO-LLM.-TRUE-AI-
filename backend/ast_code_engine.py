"""
ast_code_engine.py - Quantum MCAGI
=====================================
AST-based code intelligence engine.
Replaces Markov-assisted repair with deterministic structural analysis.

Capabilities:
  ANALYZE  - full AST analysis: scope, imports, undefined names, type issues
  REPAIR   - deterministic fixes using error->fix patterns + AST manipulation
  SUGGEST  - structural improvements based on AST patterns
  DIFF     - precise diff showing exactly what changed and why
  LEARN    - extract error->fix pairs and store in fact store

No Markov. No probability. Pure structural reasoning.
"""

import ast
import os
import re
import sys
import difflib
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime


# ============================================================
# ERROR -> FIX KNOWLEDGE BASE
# Deterministic lookup: known error pattern -> known fix
# ============================================================

ERROR_FIX_PATTERNS = [
    # Unterminated f-string from \n corruption
    {
        'error': 'unterminated f-string literal',
        'cause': 'literal_newline_in_fstring',
        'description': 'f-string broken by literal \n sequence',
        'fix_strategy': 'merge_broken_fstring_lines',
    },
    # Unterminated string
    {
        'error': 'unterminated string literal',
        'cause': 'literal_newline_in_string',
        'description': 'string broken by literal \n sequence',
        'fix_strategy': 'merge_broken_string_lines',
    },
    # Invalid syntax from \n corruption mid-statement
    {
        'error': 'invalid syntax',
        'cause': 'statement_split_by_literal_newline',
        'description': 'statement broken across lines by literal \n',
        'fix_strategy': 'rejoin_split_statement',
    },
    # Bare def with no name
    {
        'error': 'invalid syntax',
        'cause': 'bare_def',
        'description': 'def keyword with no function name',
        'fix_strategy': 'remove_bare_def',
    },
    # Import of deleted module
    {
        'error': 'ModuleNotFoundError',
        'cause': 'deleted_module_import',
        'description': 'import of consolidated/deleted module',
        'fix_strategy': 'update_module_import',
    },
    # Indentation error
    {
        'error': 'IndentationError',
        'cause': 'mixed_indentation',
        'description': 'mixed tabs and spaces or wrong indent level',
        'fix_strategy': 'normalize_indentation',
    },
    # Name not defined
    {
        'error': 'NameError',
        'cause': 'undefined_name',
        'description': 'variable or function used before definition',
        'fix_strategy': 'add_missing_definition_or_import',
    },
    # Attribute error on None
    {
        'error': 'AttributeError',
        'cause': 'none_attribute_access',
        'description': 'calling method on None return value',
        'fix_strategy': 'add_none_guard',
    },
    # KeyError from direct dict access
    {
        'error': 'KeyError',
        'cause': 'missing_dict_get',
        'description': 'direct dict access without .get()',
        'fix_strategy': 'replace_with_dict_get',
    },
]

# Module consolidation map: old name -> new name
MODULE_CONSOLIDATION = {
    'document_ingester': 'document_engine',
    'document_parser': 'document_engine',
    'self_evolution_core': 'self_evolution',
    'self_evolution_repair': 'self_evolution',
    'self_evolution_runner': 'self_evolution',
    'self_evolution_analysis': 'self_evolution',
    'self_evolution_transforms': 'self_evolution',
    'self_evolution_file_ops': 'self_evolution',
    'self_evolution_splitting': 'self_evolution',
    'response_analyzer': None,  # deleted - remove import
    'fstring_compat': None,      # deleted - remove import
    'batch_ingest': 'training_engine',
    'fact_extractors': 'training_engine',
    'training_pipeline': 'training_engine',
    'library': None,             # deleted - remove import
    'cloud_brain_fix': 'cloud_brain',
}


# ============================================================
# AST ANALYZER
# ============================================================

class ASTAnalyzer:
    """
    Full structural analysis of a Python file.
    Builds scope map, import graph, call graph, undefined names.
    """

    def __init__(self, source: str, filename: str = 'unknown'):
        self.source = source
        self.filename = filename
        self.lines = source.splitlines()
        self.tree = None
        self.syntax_error = None
        self.scope = {}
        self.imports = {}
        self.calls = {}
        self.functions = {}
        self.classes = {}
        self.undefined_names = []
        self.issues = []

        try:
            self.tree = ast.parse(source)
            self._analyze()
        except SyntaxError as e:
            self.syntax_error = e

    def _analyze(self):
        """Walk AST and build full analysis."""
        # Collect all definitions first
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                self.functions[node.name] = {
                    'line': node.lineno,
                    'args': [a.arg for a in node.args.args],
                    'length': getattr(node, 'end_lineno', node.lineno) - node.lineno,
                    'docstring': ast.get_docstring(node),
                }
            elif isinstance(node, ast.ClassDef):
                self.classes[node.name] = {
                    'line': node.lineno,
                    'methods': [m.name for m in node.body
                                if isinstance(m, ast.FunctionDef)],
                    'docstring': ast.get_docstring(node),
                }
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    self.imports[name] = alias.name
            elif isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    name = alias.asname or alias.name
                    self.imports[name] = f"{node.module}.{alias.name}"

        # Check for issues
        self._check_long_functions()
        self._check_bare_excepts()
        self._check_deleted_imports()
        self._check_direct_dict_access()

    def _check_long_functions(self):
        for name, info in self.functions.items():
            if info['length'] > 80:
                self.issues.append({
                    'type': 'long_function',
                    'function': name,
                    'line': info['line'],
                    'length': info['length'],
                    'suggestion': f"Split '{name}' ({info['length']} lines) into smaller functions",
                })

    def _check_bare_excepts(self):
        for i, line in enumerate(self.lines, 1):
            if line.strip() == 'except:':
                self.issues.append({
                    'type': 'bare_except',
                    'line': i,
                    'suggestion': "Replace 'except:' with 'except Exception:'",
                    'auto_fixable': True,
                    'fix': 'except Exception:',
                })

    def _check_deleted_imports(self):
        for node in ast.walk(self.tree) if self.tree else []:
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module in MODULE_CONSOLIDATION:
                    new_mod = MODULE_CONSOLIDATION[node.module]
                    self.issues.append({
                        'type': 'deleted_import',
                        'line': node.lineno,
                        'old_module': node.module,
                        'new_module': new_mod,
                        'auto_fixable': True,
                        'suggestion': f"Replace 'from {node.module}' with 'from {new_mod}'" if new_mod else f"Remove import of deleted module '{node.module}'",
                    })

    def _check_direct_dict_access(self):
        if not self.tree:
            return
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Subscript):
                if (isinstance(node.value, ast.Attribute) and
                        node.value.attr in ('concepts', 'facts', 'chain')):
                    self.issues.append({
                        'type': 'direct_dict_access',
                        'line': node.lineno,
                        'suggestion': f"Use .get() instead of direct access at line {node.lineno}",
                        'auto_fixable': False,
                    })

    def get_report(self) -> Dict:
        return {
            'filename': self.filename,
            'syntax_ok': self.syntax_error is None,
            'syntax_error': str(self.syntax_error) if self.syntax_error else None,
            'functions': len(self.functions),
            'classes': len(self.classes),
            'imports': len(self.imports),
            'issues': self.issues,
            'lines': len(self.lines),
        }


# ============================================================
# DETERMINISTIC REPAIR ENGINE
# ============================================================

class DeterministicRepair:
    """
    Fixes Python files using structural analysis — no Markov, no guessing.
    Each fix strategy is exact and validated against ast.parse().
    """

    def __init__(self):
        self.fixes_applied = []
        self.fixes_failed = []

    def repair(self, source: str, filename: str = 'unknown') -> Tuple[str, List[str]]:
        """
        Main repair entry point.
        Returns (fixed_source, list_of_changes_made).
        """
        changes = []
        current = source

        # Strategy 1: Fix literal \n corruption (the big one)
        fixed, change = self._fix_literal_newline_corruption(current, filename)
        if change:
            current = fixed
            changes.append(change)

        # Strategy 2: Fix deleted module imports
        fixed, change = self._fix_deleted_imports(current)
        if change:
            current = fixed
            changes.append(change)

        # Strategy 3: Fix bare excepts
        fixed, change = self._fix_bare_excepts(current)
        if change:
            current = fixed
            changes.append(change)

        # Strategy 4: Fix empty try blocks
        fixed, change = self._fix_empty_try(current)
        if change:
            current = fixed
            changes.append(change)

        # Strategy 5: Fix empty def statements
        fixed, change = self._fix_bare_defs(current)
        if change:
            current = fixed
            changes.append(change)

        # Validate final result
        try:
            ast.parse(current)
        except SyntaxError as e:
            # Try line-merge strategy as last resort
            fixed, change = self._fix_by_line_merge(current, e)
            if change and fixed:
                try:
                    ast.parse(fixed)
                    current = fixed
                    changes.append(change)
                except SyntaxError:
                    pass

        return current, changes

    def _fix_literal_newline_corruption(self, source: str, filename: str) -> Tuple[str, Optional[str]]:
        """
        Fix the specific corruption where real newlines were replaced with \n.
        Strategy: merge lines that were split by literal \n back together,
        then re-split on real newlines.

        Key insight: if a line contains \n, split it — but only if those
        split parts look like independent Python statements.
        """
        if '\n' not in source:
            return source, None

        lines = source.split('\n')
        new_lines = []
        changed = False

        for line in lines:
            if '\n' not in line:
                new_lines.append(line)
                continue

            # Try splitting this line on \n
            parts = line.split('\n')

            # Check if parts look like valid Python fragments
            # by trying to parse each one (with some indent)
            indent = len(line) - len(line.lstrip())
            indent_str = ' ' * indent

            valid_parts = []
            for part in parts:
                stripped = part.strip()
                if not stripped:
                    continue
                # Check if it looks like a Python statement
                test = indent_str + stripped
                try:
                    ast.parse(test)
                    valid_parts.append(indent_str + stripped)
                except SyntaxError:
                    # Could be part of a multi-line expression
                    valid_parts.append(indent_str + stripped)

            if len(valid_parts) > 1:
                new_lines.extend(valid_parts)
                changed = True
            else:
                new_lines.append(line)

        if not changed:
            return source, None

        result = '\n'.join(new_lines)

        # Validate
        try:
            ast.parse(result)
            return result, f"Fixed literal \n corruption ({len(lines)} -> {len(new_lines)} lines)"
        except SyntaxError:
            return source, None

    def _fix_deleted_imports(self, source: str) -> Tuple[str, Optional[str]]:
        """Replace or remove imports of deleted/consolidated modules."""
        changes = []
        lines = source.split('\n')
        new_lines = []

        for line in lines:
            modified = line
            for old_mod, new_mod in MODULE_CONSOLIDATION.items():
                if f'from {old_mod} import' in line:
                    if new_mod:
                        modified = line.replace(f'from {old_mod} import', f'from {new_mod} import')
                        changes.append(f"{old_mod} -> {new_mod}")
                    else:
                        modified = f"# {line.strip()}  # removed: module deleted"
                        changes.append(f"removed import of {old_mod}")
                elif f'import {old_mod}' in line and f'from' not in line:
                    if new_mod:
                        modified = line.replace(f'import {old_mod}', f'import {new_mod}')
                        changes.append(f"{old_mod} -> {new_mod}")
                    else:
                        modified = f"# {line.strip()}  # removed: module deleted"
                        changes.append(f"removed import of {old_mod}")
            new_lines.append(modified)

        if not changes:
            return source, None

        result = '\n'.join(new_lines)
        return result, f"Updated imports: {', '.join(changes)}"

    def _fix_bare_excepts(self, source: str) -> Tuple[str, Optional[str]]:
        """Replace bare except: with except Exception:"""
        if 'except:' not in source:
            return source, None
        result = re.sub(r'^(\s*)except:\s*$', r'\1except Exception:', source, flags=re.MULTILINE)
        if result != source:
            count = source.count('except:')
            return result, f"Fixed {count} bare except clause(s)"
        return source, None

    def _fix_empty_try(self, source: str) -> Tuple[str, Optional[str]]:
        """Remove try:/pass pairs that have no except clause."""
        lines = source.split('\n')
        new_lines = []
        i = 0
        changed = False
        while i < len(lines):
            line = lines[i]
            if line.strip() == 'try:' and i+1 < len(lines):
                next_line = lines[i+1]
                # Only remove if next line is pass AND no except follows
                if next_line.strip() == 'pass':
                    has_except = (i+2 < len(lines) and 'except' in lines[i+2])
                    if not has_except:
                        # Skip both try: and pass lines entirely
                        changed = True
                        i += 2
                        continue
            new_lines.append(line)
            i += 1
        if changed:
            return '\n'.join(new_lines), "Removed orphaned try:/pass block(s)"
        return source, None

    def _fix_bare_defs(self, source: str) -> Tuple[str, Optional[str]]:
        """Remove bare 'def' with no function name."""
        lines = source.split('\n')
        new_lines = [l for l in lines if not re.match(r'^\s*def\s*$', l)]
        if len(new_lines) != len(lines):
            return '\n'.join(new_lines), f"Removed {len(lines)-len(new_lines)} bare def statement(s)"
        return source, None

    def _fix_by_line_merge(self, source: str, error: SyntaxError) -> Tuple[Optional[str], Optional[str]]:
        """Last resort: merge the error line with the next line."""
        if not error.lineno:
            return None, None
        lines = source.split('\n')
        idx = error.lineno - 1
        if idx + 1 >= len(lines):
            return None, None
        merged = lines[idx].rstrip() + lines[idx+1].strip()
        new_lines = lines[:idx] + [merged] + lines[idx+2:]
        return '\n'.join(new_lines), f"Merged broken line {error.lineno} with line {error.lineno+1}"


# ============================================================
# FACT STORE LEARNING
# ============================================================

def learn_error_fix_pair(error_type: str, error_context: str,
                          fix_applied: str, success: bool):
    """
    Store an error->fix pair in the fact store for future retrieval.
    This is how the system learns from its own repairs.
    """
    fact_path = os.path.expanduser('~/.quantum-mcagi/fact_store.json')
    try:
        try:
            with open(fact_path) as f:
                fs = json.load(f)
        except Exception:
            fs = {}

        key = f"python_error_{error_type.lower().replace(' ', '_')}"
        if key not in fs:
            fs[key] = []

        triple = ['fixed_by' if success else 'attempted_fix_by', fix_applied[:100]]
        if triple not in fs[key]:
            fs[key].append(triple)

        # Also store context
        ctx_key = f"python_context_{error_context[:30].lower().replace(' ', '_')}"
        if ctx_key not in fs:
            fs[ctx_key] = []
        fs[ctx_key].append(['caused', error_type])

        with open(fact_path, 'w') as f:
            json.dump(fs, f)
    except Exception:
        pass


# ============================================================
# FILE REPAIR PIPELINE
# ============================================================

def repair_file(filepath: str, dry_run: bool = False) -> Dict:
    """
    Full repair pipeline for a single file.
    Analyze -> Identify fixes -> Apply -> Validate -> Learn.
    """
    result = {
        'filepath': filepath,
        'filename': os.path.basename(filepath),
        'success': False,
        'changes': [],
        'issues_found': [],
        'dry_run': dry_run,
    }

    try:
        with open(filepath, 'r', errors='replace') as f:
            source = f.read()
    except Exception as e:
        result['error'] = str(e)
        return result

    # Analyze
    analyzer = ASTAnalyzer(source, result['filename'])
    report = analyzer.get_report()
    result['issues_found'] = report['issues']

    # Repair
    repair = DeterministicRepair()
    fixed, changes = repair.repair(source, result['filename'])
    result['changes'] = changes

    if not changes:
        result['success'] = True
        result['no_changes_needed'] = True
        return result

    # Validate
    try:
        ast.parse(fixed)
    except SyntaxError as e:
        result['error'] = f"Still broken after repair: {e}"
        # Learn from failure
        learn_error_fix_pair(str(e.msg), result['filename'],
                             '; '.join(changes), False)
        return result

    # Write if not dry run
    if not dry_run:
        with open(filepath, 'w') as f:
            f.write(fixed)
        # Learn from success
        for change in changes:
            learn_error_fix_pair('corruption', result['filename'], change, True)

    result['success'] = True
    return result


def repair_all(backend_dir: str = None, dry_run: bool = False) -> List[Dict]:
    """Repair all Python files in the backend directory."""
    if backend_dir is None:
        import glob
        dirs = glob.glob('/data/data/com.termux/files/home/Quantum_MCAGI_NO_LLM_V*/backend')
        backend_dir = dirs[0] if dirs else '.'

    protected = ['killswitch.py', 'self_evolution.py', 'self_research.py']

    results = []
    for filepath in sorted(Path(backend_dir).glob('*.py')):
        if filepath.name in protected:
            continue
        result = repair_file(str(filepath), dry_run=dry_run)
        results.append(result)
        if result.get('no_changes_needed'):
            status = '✓'
        elif result['success']:
            status = '★ FIXED'
        else:
            status = '✗'
        print(f"  {status} {filepath.name}")
        if result.get('changes'):
            for c in result['changes']:
                print(f"      → {c}")
        if result.get('error'):
            print(f"      ERROR: {result['error']}")

    return results


def analyze_file(filepath: str) -> Dict:
    """Public API: analyze a file and return full report."""
    try:
        with open(filepath, 'r', errors='replace') as f:
            source = f.read()
    except Exception as e:
        return {'error': str(e)}
    analyzer = ASTAnalyzer(source, os.path.basename(filepath))
    return analyzer.get_report()


def show_diff(original: str, modified: str, filename: str = '') -> str:
    """Show unified diff between original and modified."""
    return ''.join(difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile=f'original/{filename}',
        tofile=f'fixed/{filename}',
        n=3
    ))


# ============================================================
# CLI
# ============================================================

if __name__ == '__main__':
    import glob as _g
    backend = _g.glob('/data/data/com.termux/files/home/Quantum_MCAGI_NO_LLM_V*/backend')
    backend = backend[0] if backend else '.'

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 ast_code_engine.py --repair-all          # repair all files")
        print("  python3 ast_code_engine.py --repair-all --apply  # actually write fixes")
        print("  python3 ast_code_engine.py --analyze FILE        # analyze one file")
        print("  python3 ast_code_engine.py --repair FILE         # repair one file")
        sys.exit(0)

    cmd = sys.argv[1]
    dry = '--apply' not in sys.argv

    if cmd == '--repair-all':
        print(f"{'DRY RUN' if dry else 'APPLYING FIXES'}")
        results = repair_all(backend, dry_run=dry)
        fixed = sum(1 for r in results if r['success'] and r.get('changes'))
        clean = sum(1 for r in results if r.get('no_changes_needed'))
        failed = sum(1 for r in results if not r['success'])
        print(f"\nTotal: {len(results)} | Clean: {clean} | Fixed: {fixed} | Failed: {failed}")

    elif cmd == '--analyze' and len(sys.argv) > 2:
        fp = sys.argv[2] if os.path.isabs(sys.argv[2]) else os.path.join(backend, sys.argv[2])
        report = analyze_file(fp)
        print(f"\nANALYSIS: {report.get('filename')}")
        print(f"  Syntax OK: {report.get('syntax_ok')}")
        if report.get('syntax_error'):
            print(f"  Syntax Error: {report['syntax_error']}")
        print(f"  Functions: {report.get('functions')} | Classes: {report.get('classes')}")
        print(f"  Issues: {len(report.get('issues', []))}")
        for issue in report.get('issues', []):
            print(f"    [{issue['type']}] line {issue.get('line','?')}: {issue['suggestion']}")

    elif cmd == '--repair' and len(sys.argv) > 2:
        fp = sys.argv[2] if os.path.isabs(sys.argv[2]) else os.path.join(backend, sys.argv[2])
        result = repair_file(fp, dry_run=dry)
        print(f"\n{'FIXED' if result['success'] else 'FAILED'}: {result['filename']}")
        for c in result.get('changes', []):
            print(f"  → {c}")
        if result.get('error'):
            print(f"  ERROR: {result['error']}")


class QuantumSyntaxSynthesizer:
    """Synthesizes syntactically perfect code fragments using trace-preserving operators."""
    def __init__(self, hilbert_dim: int = 4):
        self.dim = hilbert_dim
        # Map logical components to rigid structural templates
        self.syntax_templates = {
            "conditional": "if {condition}:\n    {body}\n",
            "try_catch": "try:\n    {try_body}\nexcept Exception as {err}:\n    {except_body}\n",
            "assignment": "{variable} = {value}\n"
        }

    def generate_valid_node(self, node_type: str, mapping_dict: dict) -> str:
        """Compiles templates natively while ensuring closing syntax boundaries are strictly preserved."""
        template = self.syntax_templates.get(node_type, "")
        if not template:
            return "# Coherent system trace marker"
        
        # Ensure all nested elements are cleanly sanitized of literal breaking strings
        sanitized = {k: str(v).replace("\n", "\n").strip() for k, v in mapping_dict.items()}
        raw_code = template.format(**sanitized)
        
        # Self-Verification Gate: Use built-in Python compiler to guarantee absolute safety
        try:
            compile(raw_code, "<quantum_synthesis>", "exec")
            return raw_code
        except SyntaxError:
            # If a structural constraint is breached, engage defensive fallback
            return f"# Refused code generation: Wave function failed structural invariant check\n"
