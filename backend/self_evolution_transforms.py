"""
🧬 Self-Evolution Engine — Transforms Module
=============================================
Code transformation operations: docstrings, bare excepts, unused imports.
"""

import re
from typing import Tuple, Optional


class TransformMixin:
    """Mixin providing code transformation operations."""

    def _add_docstring(self, code: str, target: str) -> Tuple[str, Optional[str]]:
        """Add docstring to a class or function."""
        name = target.split()[-1] if ' ' in target else target

        if 'class' in target:
            pattern = rf'(class {re.escape(name)}[^:]*:)\n(\s+)(?!""")'
            match = re.search(pattern, code)
            if match:
                indent = match.group(2)
                replacement = f'{match.group(1)}\n{indent}"""{name} - Auto-documented by self-evolution."""\n{indent}'
                new_code = code[:match.start()] + replacement + code[match.end():]
                if new_code != code:
                    return new_code, f"Added docstring to {target}"

        elif 'function' in target:
            pattern = rf'(def {re.escape(name)}\([^)]*\)[^:]*:)\n(\s+)(?!""")'
            match = re.search(pattern, code)
            if match:
                indent = match.group(2)
                replacement = f'{match.group(1)}\n{indent}"""{name} - Auto-documented by self-evolution."""\n{indent}'
                new_code = code[:match.start()] + replacement + code[match.end():]
                if new_code != code:
                    return new_code, f"Added docstring to {target}"

        return code, None

    def _fix_bare_except(self, code: str, target: str) -> Tuple[str, Optional[str]]:
        """Replace bare except: with except Exception:"""
        lines = code.split('\n')
        changed = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == 'except:':
                indent = line[:len(line) - len(line.lstrip())]
                lines[i] = f'{indent}except Exception:'
                changed = True

        if changed:
            return '\n'.join(lines), f"Replaced bare except with except Exception in {target}"
        return code, None

    def _remove_unused_import(self, code: str, target: str) -> Tuple[str, Optional[str]]:
        """Remove an unused import line from the code.
        Only removes simple 'import X' lines where X is truly unused.
        Does NOT touch 'from X import Y' lines (too risky - Y may be used).
        """
        import_str = target.replace('import ', '').strip()
        if not import_str:
            return code, None

        lines = code.split('\n')
        import_line_idx = None
        imported_names = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            if stripped == f'import {import_str}':
                import_line_idx = i
                imported_names = [import_str.split('.')[-1]]
                break

            from_match = re.match(rf'^from\s+{re.escape(import_str)}\s+import\s+(.+)$', stripped)
            if from_match:
                names = [n.strip().split(' as ')[-1].strip() for n in from_match.group(1).split(',')]
                import_line_idx = i
                imported_names = names
                break

        if import_line_idx is None or not imported_names:
            return code, None

        other_lines = lines[:import_line_idx] + lines[import_line_idx + 1:]
        other_code = '\n'.join(other_lines)

        all_unused = True
        for name in imported_names:
            pattern = rf'\b{re.escape(name)}\b'
            if re.search(pattern, other_code):
                all_unused = False
                break

        if not all_unused:
            return code, None

        lines.pop(import_line_idx)
        return '\n'.join(lines), f"Removed unused import: {import_str}"
