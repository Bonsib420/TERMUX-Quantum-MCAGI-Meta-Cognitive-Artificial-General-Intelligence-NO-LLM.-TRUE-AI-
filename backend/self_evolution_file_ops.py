"""
🧬 Self-Evolution Engine — File Operations Module
===================================================
Operations for splitting long files and large classes.
"""

import ast
import re
from typing import Dict, List, Tuple, Optional


class FileOpsMixin:
    """Mixin providing file-level and class-level splitting operations."""

    async def _split_long_file(self, filename: str, code: str) -> Dict:
        """Split a file exceeding max lines into parts with proper imports."""
        # COVENANT: Never split protected files
        if filename in self.protected_files:
            self._record_covenant_violation(filename, 'file_too_long split attempted on protected file')
            return {'success': False, 'reason': f'{filename} is protected — cannot split'}
        lines = code.split('\n')
        if len(lines) <= self.max_file_lines:
            return {'success': False, 'reason': f'File is {len(lines)} lines, under {self.max_file_lines} limit'}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {'success': False, 'reason': 'Cannot parse file'}

        base_name = filename.replace('.py', '')
        existing_parts = [f.name for f in self.code_dir.iterdir()
                         if f.name.startswith(base_name + '_pt') and f.name.endswith('.py')]
        next_part_num = len(existing_parts) + 2
        part_filename = f'{base_name}_pt{next_part_num}.py'

        import_lines = self._collect_import_lines(tree, lines)
        top_level_items = self._collect_top_level_items(tree)

        if not top_level_items:
            return {'success': False, 'reason': 'No top-level items to split'}

        split_idx = self._find_split_point(top_level_items, lines)
        if split_idx >= len(top_level_items):
            return {'success': False, 'reason': 'Cannot find a good split point'}

        items_to_move = top_level_items[split_idx:]

        part_code = self._build_part_file(filename, next_part_num, import_lines, items_to_move, lines)
        main_code = self._build_trimmed_main(lines, items_to_move, part_filename)

        try:
            ast.parse(main_code)
            ast.parse(part_code)
        except SyntaxError as e:
            return {'success': False, 'reason': f'Split produced invalid Python: {e}'}

        self.backup_file(filename)
        result_main = self.rewrite_code(filename, main_code,
                                        f'Auto-split: moved {len(items_to_move)} items to {part_filename}')

        with open(self.code_dir / part_filename, 'w') as f:
            f.write(part_code)

        if part_filename not in self.modifiable_files:
            self.modifiable_files.append(part_filename)

        return {
            'success': True,
            'change': f'Split {filename} ({len(lines)} lines) -> main + {part_filename}',
            'new_file': part_filename,
            'items_moved': [i['name'] for i in items_to_move]
        }

    def _collect_import_lines(self, tree, lines: List[str]) -> List[str]:
        """Collect all import lines from AST."""
        import_lines = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for ln in range(node.lineno - 1, node.end_lineno):
                    import_lines.append(lines[ln])
        return import_lines

    def _collect_top_level_items(self, tree) -> List[Dict]:
        """Find top-level classes and functions with line ranges."""
        items = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                items.append({
                    'name': node.name,
                    'type': type(node).__name__,
                    'start': node.lineno - 1,
                    'end': node.end_lineno,
                    'lines': node.end_lineno - node.lineno + 1
                })
        return items

    def _find_split_point(self, items: List[Dict], lines: List[str]) -> int:
        """Find the index at which to split items so main stays under limit."""
        split_idx = len(items)
        cumulative = 0
        for i in range(len(items) - 1, 0, -1):
            cumulative += items[i]['lines']
            remaining = len(lines) - cumulative
            if remaining <= self.max_file_lines:
                split_idx = i
                break
        return split_idx

    def _build_part_file(self, filename, part_num, import_lines, items_to_move, lines) -> str:
        """Build the content for a split part file."""
        part_lines = [
            '"""',
            f'Auto-split from {filename} by self-evolution engine.',
            f'Part {part_num} — contains: {", ".join(i["name"] for i in items_to_move)}',
            '"""', ''
        ]
        part_lines.extend(import_lines)
        part_lines.append('')
        for item in items_to_move:
            part_lines.extend(lines[item['start']:item['end']])
            part_lines.extend(['', ''])
        return '\n'.join(part_lines)

    def _build_trimmed_main(self, lines, items_to_move, part_filename) -> str:
        """Build the trimmed main file with import for split items."""
        main_lines = lines[:items_to_move[0]['start']]
        part_module = part_filename.replace('.py', '')
        moved_names = [i['name'] for i in items_to_move]
        main_lines.append(f'from {part_module} import {", ".join(moved_names)}  # Auto-split by self-evolution')
        main_lines.append('')
        last_end = items_to_move[-1]['end']
        if last_end < len(lines):
            remaining = lines[last_end:]
            if any(line.strip() for line in remaining):
                main_lines.extend(remaining)
        return '\n'.join(main_lines)

    def _split_large_class(self, code: str, target: str, filename: str) -> Tuple[str, Optional[str]]:
        """Split a class with too many methods into a mixin in a separate file."""
        class_name = target.replace('class ', '').split()[0] if 'class' in target else target

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return code, None

        target_class = None
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                target_class = node
                break
        if not target_class:
            return code, None

        methods = [n for n in target_class.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if len(methods) <= 15:
            return code, None

        keep_methods = methods[:10]
        move_methods = methods[10:]
        lines = code.split('\n')

        return self.__split_large_class_continued(class_name, lines, methods, move_methods, tree, code, filename)

    def __split_large_class_continued(self, class_name, lines, methods, move_methods, tree, code, filename):
        """Continuation of _split_large_class — auto-extracted by self-evolution."""
        import_lines = self._collect_import_lines(tree, lines)
        moved_source = []
        for m in move_methods:
            moved_source.extend(lines[m.lineno - 1:m.end_lineno])
            moved_source.append('')

        base_name = filename.replace('.py', '')
        mixin_name = f'{class_name}ExtMixin'
        part_filename = f'{base_name}_ext.py'
        part_path = self.code_dir / part_filename
        if part_path.exists():
            part_num = 2
            while (self.code_dir / f'{base_name}_ext{part_num}.py').exists():
                part_num += 1
            part_filename = f'{base_name}_ext{part_num}.py'
            mixin_name = f'{class_name}Ext{part_num}Mixin'

        part_lines = [
            '"""',
            f'Auto-split from {filename} by self-evolution engine.',
            f'Contains extended methods for {class_name}.',
            '"""', ''
        ]
        part_lines.extend(import_lines)
        part_lines.extend(['', '',
            f'class {mixin_name}:',
            f'    """Extended methods for {class_name} — auto-extracted by self-evolution."""', ''
        ])
        part_lines.extend(moved_source)
        part_code = '\n'.join(part_lines)

        try:
            ast.parse(part_code)
        except SyntaxError:
            return code, None

        new_lines = list(lines)
        remove_ranges = [(m.lineno - 1, m.end_lineno) for m in move_methods]
        for start, end in reversed(remove_ranges):
            del new_lines[start:end]

        part_module = part_filename.replace('.py', '')
        import_stmt = f'from {part_module} import {mixin_name}  # Auto-split by self-evolution'

        class_line_idx = None
        for i, line in enumerate(new_lines):
            if re.match(rf'^class\s+{re.escape(class_name)}\s*(\(|:)', line):
                class_line_idx = i
                break

        if class_line_idx is not None:
            new_lines.insert(class_line_idx, import_stmt)
            new_lines.insert(class_line_idx + 1, '')
            class_line_idx += 2

        for i, line in enumerate(new_lines):
            if re.match(rf'^class\s+{re.escape(class_name)}\s*(\(|:)', line):
                if '(' in line and ')' in line:
                    new_lines[i] = line.replace(')', f', {mixin_name})')
                elif ':' in line:
                    new_lines[i] = line.replace(':', f'({mixin_name}):')
                break

        new_code = '\n'.join(new_lines)
        try:
            ast.parse(new_code)
        except SyntaxError:
            return code, None

        with open(self.code_dir / part_filename, 'w') as f:
            f.write(part_code)

        if part_filename not in self.modifiable_files:
            self.modifiable_files.append(part_filename)

        return new_code, f"Extracted {len(move_methods)} methods from {class_name} into {part_filename}"

