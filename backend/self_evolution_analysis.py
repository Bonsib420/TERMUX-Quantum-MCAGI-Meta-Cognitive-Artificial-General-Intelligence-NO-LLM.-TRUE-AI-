"""
🧬 Self-Evolution Engine — Analysis Module
==========================================
Code reading, AST analysis, and improvement identification.
"""

import ast
import re
from typing import Dict, List


class AnalysisMixin:
    """Mixin providing code analysis and improvement identification."""

    def read_own_code(self, filename: str) -> Dict:
        """Read and analyze a source file."""
        filepath = self.code_dir / filename

        if not filepath.exists():
            return {'error': f'File not found: {filename}'}

        try:
            with open(filepath, 'r') as f:
                code = f.read()

            tree = ast.parse(code)

            analysis = {
                'filename': filename,
                'filepath': str(filepath),
                'size_bytes': len(code),
                'lines': len(code.split('\n')),
                'classes': [],
                'functions': [],
                'imports': [],
                'docstring': ast.get_docstring(tree),
                'code': code
            }

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    analysis['classes'].append({
                        'name': node.name,
                        'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                        'docstring': ast.get_docstring(node)
                    })
                elif isinstance(node, ast.FunctionDef) and not isinstance(node, ast.AsyncFunctionDef):
                    if node.col_offset == 0:
                        analysis['functions'].append({
                            'name': node.name,
                            'args': [a.arg for a in node.args.args],
                            'docstring': ast.get_docstring(node)
                        })
                elif isinstance(node, ast.Import):
                    analysis['imports'].extend([alias.name for alias in node.names])
                elif isinstance(node, ast.ImportFrom):
                    analysis['imports'].append(f"{node.module}")

            return analysis

        except Exception as e:
            return {'error': str(e), 'filename': filename}

    def analyze_all_code(self) -> Dict:
        """Analyze all modifiable code files."""
        analyses = {}

        for filename in self.modifiable_files:
            analyses[filename] = self.read_own_code(filename)

        return {
            'files_analyzed': len(analyses),
            'total_lines': sum(a.get('lines', 0) for a in analyses.values() if 'error' not in a),
            'total_classes': sum(len(a.get('classes', [])) for a in analyses.values() if 'error' not in a),
            'total_functions': sum(len(a.get('functions', [])) for a in analyses.values() if 'error' not in a),
            'analyses': analyses
        }

    def identify_improvements(self, filename: str) -> List[Dict]:
        """Identify potential improvements in a file."""
        analysis = self.read_own_code(filename)

        if 'error' in analysis:
            return []

        improvements = []
        code = analysis.get('code', '')
        lines = code.split('\n')

        self._check_missing_docstrings(analysis, improvements)
        self._check_file_length(analysis, filename, improvements)
        self._check_class_size(analysis, improvements)
        self._check_bare_excepts(lines, filename, improvements)
        self._check_long_functions(analysis, code, improvements)
        self._check_todo_items(lines, filename, improvements)
        self._check_unused_imports(analysis, improvements)

        return improvements

    def _check_missing_docstrings(self, analysis: Dict, improvements: List[Dict]):
        """Check for missing docstrings on classes and functions."""
        for cls in analysis.get('classes', []):
            if not cls.get('docstring'):
                improvements.append({
                    'type': 'missing_docstring',
                    'target': f"class {cls['name']}",
                    'suggestion': f"Add docstring to class {cls['name']}",
                    'priority': 2
                })

        for func in analysis.get('functions', []):
            if not func.get('docstring'):
                improvements.append({
                    'type': 'missing_docstring',
                    'target': f"function {func['name']}",
                    'suggestion': f"Add docstring to function {func['name']}",
                    'priority': 2
                })

    def _check_file_length(self, analysis: Dict, filename: str, improvements: List[Dict]):
        """Check if file exceeds max line count."""
        if analysis.get('lines', 0) > self.max_file_lines:
            improvements.append({
                'type': 'file_too_long',
                'target': filename,
                'suggestion': f'File has {analysis["lines"]} lines (max {self.max_file_lines}) — will auto-split',
                'priority': 3
            })

    def _check_class_size(self, analysis: Dict, improvements: List[Dict]):
        """Check for classes with too many methods."""
        for cls in analysis.get('classes', []):
            if len(cls.get('methods', [])) > 15:
                improvements.append({
                    'type': 'class_too_large',
                    'target': f"class {cls['name']}",
                    'suggestion': f"Class {cls['name']} has {len(cls['methods'])} methods - consider splitting",
                    'priority': 3
                })

    def _check_bare_excepts(self, lines: List[str], filename: str, improvements: List[Dict]):
        """Check for bare except clauses."""
        bare_excepts = sum(1 for line in lines if 'except:' in line and 'except Exception' not in line)
        if bare_excepts > 0:
            improvements.append({
                'type': 'bare_except',
                'target': filename,
                'suggestion': f'{bare_excepts} bare except clause(s) - should catch specific exceptions',
                'priority': 2
            })

    def _check_long_functions(self, analysis: Dict, code: str, improvements: List[Dict]):
        """Check for functions exceeding max line count."""
        for cls in analysis.get('classes', []):
            for method_name in cls.get('methods', []):
                try:
                    tree = ast.parse(code)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if node.name == method_name:
                                func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                                if func_lines > self.max_function_lines:
                                    improvements.append({
                                        'type': 'long_function',
                                        'target': f"method {cls['name']}.{method_name}",
                                        'suggestion': f'Method is {func_lines} lines (max {self.max_function_lines}) — will auto-split',
                                        'priority': 2
                                    })
                except Exception:
                    pass

    def _check_todo_items(self, lines: List[str], filename: str, improvements: List[Dict]):
        """Check for TODO/FIXME comments."""
        todo_count = sum(1 for line in lines if 'TODO' in line or 'FIXME' in line or 'HACK' in line)
        if todo_count > 0:
            improvements.append({
                'type': 'todo_items',
                'target': filename,
                'suggestion': f'{todo_count} TODO/FIXME comment(s) need attention',
                'priority': 1
            })

    def _check_unused_imports(self, analysis: Dict, improvements: List[Dict]):
        """Check for unused imports."""
        code_text = analysis.get('code', '')

        for imp in analysis.get('imports', []):
            if not imp or imp in ('os', 'sys', 're', 'json', 'typing'):
                continue

            imp_name = imp.split('.')[-1] if '.' in imp else imp
            import_line = None
            for line in code_text.split('\n'):
                stripped = line.strip()
                if f'from {imp} import' in stripped:
                    import_line = stripped
                    break
                elif stripped == f'import {imp}':
                    import_line = stripped
                    break

            if not import_line:
                continue

            if import_line.startswith('from '):
                from_match = re.match(r'^from\s+\S+\s+import\s+(.+)$', import_line)
                if from_match:
                    names = [n.strip().split(' as ')[-1].strip() for n in from_match.group(1).split(',')]
                    other_code = '\n'.join(l for l in code_text.split('\n') if l.strip() != import_line)
                    all_unused = all(not re.search(rf'\b{re.escape(n)}\b', other_code) for n in names)
                    if all_unused:
                        improvements.append({
                            'type': 'unused_import',
                            'target': f"import {imp}",
                            'suggestion': f'Import {imp} ({", ".join(names)}) may be unused',
                            'priority': 1
                        })
            elif import_line.startswith('import '):
                other_code = '\n'.join(l for l in code_text.split('\n') if l.strip() != import_line)
                if not re.search(rf'\b{re.escape(imp_name)}\b', other_code):
                    improvements.append({
                        'type': 'unused_import',
                        'target': f"import {imp}",
                        'suggestion': f'Import {imp} may be unused',
                        'priority': 1
                    })
