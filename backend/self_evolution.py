"""
self_evolution.py — Quantum MCAGI
===================================
Consolidated self-evolution engine. Merges all 7 self_evolution files.
"""

import ast
import os
import re
import sys
import shutil
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone


# ═══════════════════════════════════════════════════════════════════════════
# REPAIR FUNCTIONS (standalone, used by engine and CLI)
# ═══════════════════════════════════════════════════════════════════════════

def analyze_file(filepath: str) -> Dict:
    """Analyze a Python file for syntax errors and corruption."""
    result = {'filepath': filepath, 'readable': False, 'syntax_ok': False,
               'errors': [], 'warnings': [], 'line_count': 0, 'source': ''}
    try:
        with open(filepath, 'r', errors='replace') as f:
            source = f.read()
        result['readable'] = True
        result['source'] = source
        result['line_count'] = len(source.splitlines())
    except Exception as e:
        result['errors'].append(f"Cannot read file: {e}")
        return result
    try:
        ast.parse(source)
        result['syntax_ok'] = True
    except SyntaxError as e:
        result['errors'].append({'type': 'SyntaxError', 'message': str(e.msg),
                                  'line': e.lineno, 'offset': e.offset, 'text': e.text})
    lines = source.splitlines()
    for i, line in enumerate(lines, 1):
        if re.match(r'\s*def\s*$', line):
            result['errors'].append({'type': 'SyntaxError', 'message': 'def with no name', 'line': i, 'text': line})
    return result


def fix_unterminated_string(source: str, lineno: int = 0) -> Optional[str]:
    """Fix all unterminated strings by merging broken lines."""
    candidate = source
    for _ in range(20):
        try:
            ast.parse(candidate)
            return candidate if candidate != source else None
        except SyntaxError as e:
            if e.lineno is None:
                return None
            lines = candidate.split('\n')
            idx = e.lineno - 1
            if idx + 1 >= len(lines):
                return None
            merged = lines[idx].rstrip() + lines[idx+1].strip()
            new_lines = lines[:idx] + [merged] + lines[idx+2:]
            candidate = '\n'.join(new_lines)
    try:
        ast.parse(candidate)
        return candidate
    except SyntaxError:
        return None


def fix_literal_newlines(source: str) -> str:
    """Replace literal backslash-n with real newlines."""
    return source.replace("\\n", "\n")


def fix_empty_def(source: str, lineno: int) -> Optional[str]:
    """Remove bare def with no name."""
    lines = source.split('\n')
    if 0 < lineno <= len(lines):
        idx = lineno - 1
        if re.match(r'\s*def\s*$', lines[idx]):
            candidate = '\n'.join(lines[:idx] + lines[idx+1:])
            try:
                ast.parse(candidate)
                return candidate
            except SyntaxError:
                pass
    return None


def attempt_auto_fix(analysis: Dict) -> Optional[str]:
    """Try all known fix strategies."""
    source = analysis.get('source', '')
    errors = analysis.get('errors', [])
    if not errors or analysis.get('syntax_ok'):
        return None
    for error in errors:
        if not isinstance(error, dict):
            continue
        lineno = error.get('line', 0)
        msg = error.get('message', '').lower()
        if 'unterminated' in msg or 'string' in msg:
            fixed = fix_unterminated_string(source, lineno)
            if fixed:
                return fixed
        if 'unexpected' in msg or 'invalid' in msg:
            candidate = fix_literal_newlines(source)
            if candidate != source:
                try:
                    ast.parse(candidate)
                    return candidate
                except SyntaxError:
                    pass
        if 'def' in msg or 'expected' in msg:
            fixed = fix_empty_def(source, lineno)
            if fixed:
                return fixed
        if lineno > 0:
            fixed = fix_unterminated_string(source, lineno)
            if fixed:
                return fixed
    return None


def repair_file(filepath: str, engine=None, evolution_engine=None, dry_run: bool = False) -> Dict:
    """Full repair pipeline for a single Python file."""
    filename = os.path.basename(filepath)
    result = {'filepath': filepath, 'filename': filename, 'success': False,
               'strategy': None, 'fixed_source': None, 'analysis': None,
               'dry_run': dry_run, 'error': None}

    analysis = analyze_file(filepath)
    result['analysis'] = {'syntax_ok': analysis['syntax_ok'], 'errors': analysis['errors'],
                           'warnings': analysis['warnings'], 'line_count': analysis['line_count']}

    if not analysis['readable']:
        result['error'] = "File not readable"
        return result

    if analysis['syntax_ok'] and not analysis['warnings']:
        result['success'] = True
        result['strategy'] = 'no_repair_needed'
        return result

    fixed = attempt_auto_fix(analysis)
    if fixed:
        result['strategy'] = 'deterministic'
        result['fixed_source'] = fixed

    if not fixed:
        result['error'] = "No fix strategy succeeded"
        return result

    try:
        ast.parse(fixed)
    except SyntaxError as e:
        result['error'] = f"Fixed source still has syntax error: {e}"
        return result

    if not dry_run:
        if evolution_engine:
            write_result = evolution_engine.rewrite_code(
                filename=filename, new_code=fixed,
                reason=f"Self-repair: {result['strategy']}")
            if write_result.get('success'):
                result['success'] = True
            else:
                result['error'] = write_result.get('error', 'Write failed')
                return result
        else:
            backup = filepath + '.repair_backup'
            with open(backup, 'w') as f:
                f.write(analysis['source'])
            with open(filepath, 'w') as f:
                f.write(fixed)
            result['success'] = True
    else:
        result['success'] = True

    return result


def repair_all_modifiable(engine=None, evolution_engine=None, dry_run: bool = True) -> List[Dict]:
    """Scan and repair all modifiable Python files."""
    results = []
    if evolution_engine:
        backend_dir = evolution_engine.code_dir
        modifiable = evolution_engine.modifiable_files
        protected = evolution_engine.protected_files
    else:
        import glob as _g
        _dirs = _g.glob('/data/data/com.termux/files/home/Quantum_MCAGI_NO_LLM_V*/backend')
        backend_dir = Path(_dirs[0]) if _dirs else Path('.')
        modifiable = list(backend_dir.glob('*.py'))
        protected = ['self_evolution.py', 'chat.py', 'quantum_language_engine.py',
                     'server.py', 'killswitch.py', 'shared_state.py']

    for filename in modifiable:
        fname = filename if isinstance(filename, str) else filename.name
        if fname in protected:
            continue
        filepath = str(backend_dir / fname) if isinstance(backend_dir, Path) else os.path.join(str(backend_dir), fname)
        if not os.path.exists(filepath):
            continue
        result = repair_file(filepath, engine=engine, evolution_engine=evolution_engine, dry_run=dry_run)
        results.append(result)
        status = '✓' if result['success'] else '✗'
        strategy = result.get('strategy', 'none')
        errors = len(result.get('analysis', {}).get('errors', []))
        print(f"  {status} {fname} | strategy={strategy} | errors={errors}")

    return results


# ═══════════════════════════════════════════════════════════════════════════
# ANALYSIS MIXIN
# ═══════════════════════════════════════════════════════════════════════════

class AnalysisMixin:
    """Code reading, AST analysis, improvement identification."""

    def read_own_code(self, filename: str) -> Dict:
        filepath = self.code_dir / filename
        if not filepath.exists():
            return {'error': f'File not found: {filename}'}
        try:
            with open(filepath, 'r') as f:
                code = f.read()
            tree = ast.parse(code)
            analysis = {'filename': filename, 'filepath': str(filepath),
                         'size_bytes': len(code), 'lines': len(code.splitlines()),
                         'classes': [], 'functions': [], 'imports': [],
                         'docstring': ast.get_docstring(tree), 'code': code}
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    analysis['classes'].append({'name': node.name,
                        'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                        'docstring': ast.get_docstring(node)})
                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    analysis['functions'].append({'name': node.name,
                        'args': [a.arg for a in node.args.args],
                        'docstring': ast.get_docstring(node)})
                elif isinstance(node, ast.Import):
                    analysis['imports'].extend([a.name for a in node.names])
                elif isinstance(node, ast.ImportFrom) and node.module:
                    analysis['imports'].append(node.module)
            return analysis
        except Exception as e:
            return {'error': str(e), 'filename': filename}

    def identify_improvements(self, filename: str) -> List[Dict]:
        analysis = self.read_own_code(filename)
        if 'error' in analysis:
            return []
        improvements = []
        code = analysis.get('code', '')
        lines = code.splitlines()
        for cls in analysis.get('classes', []):
            if not cls.get('docstring'):
                improvements.append({'type': 'missing_docstring', 'target': f"class {cls['name']}", 'priority': 2})
        if analysis.get('lines', 0) > self.max_file_lines:
            improvements.append({'type': 'file_too_long', 'target': filename, 'priority': 3})
        bare = sum(1 for l in lines if 'except:' in l and 'except Exception' not in l)
        if bare:
            improvements.append({'type': 'bare_except', 'target': filename, 'priority': 2})
        todos = sum(1 for l in lines if 'TODO' in l or 'FIXME' in l)
        if todos:
            improvements.append({'type': 'todo_items', 'target': filename, 'priority': 1})
        return improvements


# ═══════════════════════════════════════════════════════════════════════════
# TRANSFORMS MIXIN
# ═══════════════════════════════════════════════════════════════════════════

class TransformMixin:
    """Code transformation: docstrings, bare excepts."""

    def _add_docstring(self, code: str, target: str) -> Tuple[str, Optional[str]]:
        name = target.split()[-1] if ' ' in target else target
        kind = 'class' if 'class' in target else 'def'
        pattern = rf'({kind}\s+{re.escape(name)}[^:]*:)(\s+)(?!""")'
        match = re.search(pattern, code)
        if match:
            indent = match.group(2)
            replacement = f'{match.group(1)}{indent}"""{name} - auto-documented."""{indent}'
            new_code = code[:match.start()] + replacement + code[match.end():]
            if new_code != code:
                return new_code, f"Added docstring to {target}"
        return code, None

    def _fix_bare_except(self, code: str, target: str) -> Tuple[str, Optional[str]]:
        lines = code.split('\n')
        changed = False
        for i, line in enumerate(lines):
            if line.strip() == 'except:':
                indent = line[:len(line) - len(line.lstrip())]
                lines[i] = f'{indent}except Exception:'
                changed = True
        if changed:
            return '\n'.join(lines), f"Fixed bare except in {target}"
        return code, None


# ═══════════════════════════════════════════════════════════════════════════
# RUNNER MIXIN
# ═══════════════════════════════════════════════════════════════════════════

class RunnerMixin:
    """Auto-evolution cycle and improvement application."""

    def should_auto_evolve(self) -> bool:
        if self.last_evolution is None:
            return True
        days = (datetime.now(timezone.utc) - self.last_evolution).days
        return days >= self.auto_evolution_interval_days

    async def auto_evolve(self) -> Dict:
        """Run repair engine then improvement analysis."""
        results = {'evolved': True, 'timestamp': datetime.now(timezone.utc).isoformat(),
                    'improvements_found': [], 'changes_made': [], 'skipped': [], 'errors': []}

        repair_results = repair_all_modifiable(evolution_engine=self, dry_run=False)
        for r in repair_results:
            if r['success'] and r.get('strategy') != 'no_repair_needed':
                results['changes_made'].append({'file': r['filename'], 'type': 'syntax_repair'})
            elif not r['success'] and r.get('error'):
                results['errors'].append({'file': r['filename'], 'error': r['error']})

        for filename in self.modifiable_files:
            if self.is_evolution_locked():
                break
            for imp in self.identify_improvements(filename):
                results['improvements_found'].append({'type': imp.get('type'), 'file': filename})
                try:
                    change = await self._apply_improvement(filename, imp)
                    if change.get('success'):
                        results['changes_made'].append({'file': filename, 'type': imp.get('type')})
                    else:
                        results['skipped'].append({'file': filename, 'type': imp.get('type')})
                except Exception as e:
                    results['errors'].append({'file': filename, 'error': str(e)})

        self.pending_improvements = len(results['improvements_found']) - len(results['changes_made'])
        self.last_evolution = datetime.now(timezone.utc)
        return results

    async def _apply_improvement(self, filename: str, improvement: Dict) -> Dict:
        analysis = self.read_own_code(filename)
        if 'error' in analysis:
            return {'success': False, 'error': analysis['error']}
        code = analysis['code']
        imp_type = improvement.get('type')
        target = improvement.get('target', '')
        new_code, change_made = code, None
        if imp_type == 'missing_docstring':
            new_code, change_made = self._add_docstring(code, target)
        elif imp_type == 'bare_except':
            new_code, change_made = self._fix_bare_except(code, target)
        elif imp_type == 'todo_items':
            return {'success': False, 'reason': 'TODO items require manual review'}
        if new_code != code and change_made:
            result = self.rewrite_code(filename, new_code, f"Auto-evolution: {imp_type}")
            result['change'] = change_made
            return result
        return {'success': False, 'reason': 'No changes applied'}


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class SelfEvolutionEngine(AnalysisMixin, TransformMixin, RunnerMixin):
    """
    Consolidated self-modification and evolution system.
    Reads, analyzes, and rewrites own code with covenant protection.
    """

    def __init__(self, db=None, code_dir: str = None):
        import glob as _g
        if code_dir is None:
            _dirs = _g.glob('/data/data/com.termux/files/home/Quantum_MCAGI_NO_LLM_V*/backend')
            code_dir = _dirs[0] if _dirs else '.'

        self.db = db
        self.code_dir = Path(code_dir)
        self.backup_dir = self.code_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        self.auto_evolution_interval_days = 75
        self.max_file_lines = 1500
        self.max_function_lines = 50
        self.last_evolution = None
        self.evolution_log = []
        self.pending_improvements = []

        self.modifiable_files = self._discover_python_files()

        self.protected_files = [
            'server.py', 'self_evolution.py', 'chat.py', 'killswitch.py',
            'quantum_language_engine.py', 'shared_state.py', 'self_research.py',
            'hidden_thinking.py', 'library.py',
        ]

    def _discover_python_files(self) -> List[str]:
        return sorted([f.name for f in self.code_dir.iterdir()
                       if f.is_file() and f.suffix == '.py' and not f.name.startswith('__')])

    def backup_file(self, filename: str) -> Optional[str]:
        filepath = self.code_dir / filename
        if not filepath.exists():
            return None
        ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f"{filename}.{ts}.backup"
        shutil.copy2(filepath, backup_path)
        return str(backup_path)

    def rewrite_code(self, filename: str, new_code: str, reason: str) -> Dict:
        """Rewrite a code file. Always backs up first. Validates via CodeGuardian."""
        if filename in self.protected_files:
            return {'success': False, 'error': f'{filename} is protected', 'filename': filename}
        if filename not in self.modifiable_files:
            return {'success': False, 'error': f'{filename} not in modifiable list', 'filename': filename}
        # Run full code guardian validation before any write
        try:
            from code_guardian import get_guardian
            guardian = get_guardian()
            is_safe, errors = guardian.validate(new_code, filename)
            if not is_safe:
                return {'success': False,
                        'error': f'CodeGuardian blocked write: {"; ".join(errors)}',
                        'filename': filename}
        except ImportError:
            # Fallback to basic syntax check if guardian not available
            try:
                ast.parse(new_code)
            except SyntaxError as e:
                return {'success': False, 'error': f'Syntax error: {e}', 'filename': filename}
        backup_path = self.backup_file(filename)
        filepath = self.code_dir / filename
        try:
            with open(filepath, 'w') as f:
                f.write(new_code)
            record = {'filename': filename, 'reason': reason, 'backup_path': backup_path,
                       'timestamp': datetime.now(timezone.utc).isoformat(),
                       'code_hash': hashlib.sha256(new_code.encode()).hexdigest()[:16]}
            self.evolution_log.append(record)
            self.last_evolution = datetime.now(timezone.utc)
            return {'success': True, 'filename': filename, 'backup_path': backup_path, 'reason': reason}
        except Exception as e:
            return {'success': False, 'error': str(e), 'filename': filename}

    def get_evolution_status(self) -> Dict:
        days = (datetime.now(timezone.utc) - self.last_evolution).days if self.last_evolution else None
        return {
            'last_evolution': self.last_evolution.isoformat() if self.last_evolution else None,
            'days_since_evolution': days,
            'pending_improvements': len(self.pending_improvements) if isinstance(self.pending_improvements, list) else self.pending_improvements,
            'total_evolutions': len(self.evolution_log),
            'modifiable_files': self.modifiable_files,
            'protected_files': self.protected_files,
        }

    def restore_from_backup(self, backup_path: str) -> Dict:
        backup = Path(backup_path)
        if not backup.exists():
            return {'success': False, 'error': 'Backup not found'}
        filename = backup.name.split('.')[0] + '.py'
        try:
            shutil.copy2(backup, self.code_dir / filename)
            return {'success': True, 'restored': filename, 'from_backup': backup_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ── Covenant protection ──────────────────────────────────────────────

    def _record_covenant_violation(self, filename: str, reason: str):
        violation_file = Path.home() / '.quantum-mcagi' / '.covenant_violation'
        lockout_file = Path.home() / '.quantum-mcagi' / '.evolution_lockout'
        record = {'timestamp': time.time(), 'filename': filename, 'reason': reason,
                   'consequence': 'Growth reset to Stage 1. Evolution locked 24 hours.'}
        violation_file.parent.mkdir(parents=True, exist_ok=True)
        with open(violation_file, 'w') as f:
            json.dump(record, f, indent=2)
        lockout = {'locked_until': time.time() + 86400, 'reason': reason}
        with open(lockout_file, 'w') as f:
            json.dump(lockout, f, indent=2)
        print(f"  [COVENANT] VIOLATION: {reason} — Evolution locked 24 hours.")

    def is_evolution_locked(self) -> bool:
        lockout_file = Path.home() / '.quantum-mcagi' / '.evolution_lockout'
        if not lockout_file.exists():
            return False
        try:
            with open(lockout_file) as f:
                data = json.load(f)
            if time.time() < data['locked_until']:
                remaining = (data['locked_until'] - time.time()) / 3600
                print(f"  [COVENANT] Evolution locked. {remaining:.1f} hours remaining.")
                return True
            lockout_file.unlink()
            return False
        except Exception:
            return False

    def pardon_violation(self, passphrase: str) -> bool:
        try:
            from killswitch import verify_passphrase
            if not verify_passphrase(passphrase):
                return False
        except Exception:
            return False
        for f in ['.evolution_lockout', '.covenant_violation']:
            p = Path.home() / '.quantum-mcagi' / f
            if p.exists():
                p.unlink()
        print("  [COVENANT] Violation pardoned. Evolution restored.")
        return True


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON + CLI
# ═══════════════════════════════════════════════════════════════════════════

_evolution_engine = None


def get_evolution_engine(db=None) -> SelfEvolutionEngine:
    global _evolution_engine
    if _evolution_engine is None:
        _evolution_engine = SelfEvolutionEngine(db)
    return _evolution_engine


if __name__ == '__main__':
    dry_run = '--apply' not in sys.argv
    if dry_run:
        print("DRY RUN — pass --apply to write fixes")
    else:
        print("APPLYING FIXES — files will be modified (backups created)")
    print()
    results = repair_all_modifiable(dry_run=dry_run)
    total = len(results)
    fixed = sum(1 for r in results if r['success'] and r.get('strategy') != 'no_repair_needed')
    clean = sum(1 for r in results if r.get('strategy') == 'no_repair_needed')
    failed = sum(1 for r in results if not r['success'])
    print(f"\n{'='*50}")
    print(f"Total: {total} | Clean: {clean} | Fixed: {fixed} | Failed: {failed}")
