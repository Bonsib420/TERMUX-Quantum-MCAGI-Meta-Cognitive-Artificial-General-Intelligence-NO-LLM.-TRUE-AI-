"""
🧬 Self-Evolution Engine — Splitting Module
============================================
Operations for splitting long functions, files, and classes.
"""

import ast
import re
from typing import Dict, List, Tuple, Optional


class SplittingMixin:
    """Mixin providing code splitting operations."""

    def _split_long_function(self, code: str, target: str) -> Tuple[str, Optional[str]]:
        """Split a long function by extracting blocks into helpers.
        For __init__: extracts data blocks into _init_<n>() methods.
        For other methods: extracts logical blocks into _<n>_<section>() helpers.
        """
        parts = target.replace('method ', '').split('.')
        if len(parts) != 2:
            return code, None
        class_name, method_name = parts

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return code, None

        target_node = self._find_method_node(tree, class_name, method_name)
        if not target_node or not hasattr(target_node, 'end_lineno'):
            return code, None

        func_lines = target_node.end_lineno - target_node.lineno
        if func_lines <= self.max_function_lines:
            return code, None

        lines = code.split('\n')
        func_start = target_node.lineno - 1
        func_end = target_node.end_lineno

        body_first_line = func_start + 1
        if target_node.body:
            body_first_line = target_node.body[0].lineno - 1

        def_lines = lines[func_start:body_first_line]
        func_body_lines = lines[body_first_line:func_end]

        body_indent, class_indent = self._detect_indents(func_body_lines)

        if method_name == '__init__':
            return self._split_init_method(code, lines, func_start, func_end,
                                           class_name, body_indent, class_indent,
                                           def_lines, func_body_lines)
        else:
            return self._split_regular_method(code, lines, func_start, func_end,
                                              class_name, method_name, body_indent, class_indent,
                                              def_lines, func_body_lines)

    def _find_method_node(self, tree, class_name: str, method_name: str):
        """Find a method AST node within a class."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == method_name:
                        return item
        return None

    def _detect_indents(self, body_lines: List[str]) -> Tuple[str, str]:
        """Detect body and class-level indentation from method body lines."""
        body_indent = ''
        for line in body_lines:
            if line.strip():
                body_indent = line[:len(line) - len(line.lstrip())]
                break

        if len(body_indent) >= 4:
            class_indent = body_indent[:-4]
        elif len(body_indent) >= 2:
            class_indent = body_indent[:-2]
        else:
            class_indent = ''

        return body_indent, class_indent

    def _skip_docstring(self, body_lines: List[str]) -> Tuple[List[str], List[str]]:
        """Separate docstring lines from actual body lines."""
        body_start = 0
        in_docstring = False
        for i, line in enumerate(body_lines):
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if in_docstring or (stripped.count('"""') >= 2 or stripped.count("'''") >= 2):
                    body_start = i + 1
                    break
                else:
                    in_docstring = True
            elif not in_docstring:
                body_start = i
                break
        return body_lines[:body_start], body_lines[body_start:]

    def _split_init_method(self, code, lines, func_start, func_end,
                           class_name, body_indent, class_indent,
                           def_lines, func_body_lines):
        """Split a long __init__ into __init__ + _init_<section> helpers."""
        docstring_part, actual_body = self._skip_docstring(func_body_lines)

        groups = self._group_by_separators(actual_body)
        if len(groups) < 3:
            return code, None

        keep_in_init = groups[0]
        extract_groups = groups[1:]

        new_init_lines = list(def_lines)
        new_init_lines.extend(docstring_part)
        new_init_lines.extend(keep_in_init['lines'])

        helper_methods = []
        for idx, group in enumerate(extract_groups):
            helper_name = group['name'] or f'section_{idx + 1}'
            helper_name = f'_init_{helper_name}'
            new_init_lines.append(f'{body_indent}self.{helper_name}()')

            helper_lines = [
                f'{class_indent}def {helper_name}(self):',
                f'{body_indent}"""Initialize {helper_name.replace("_init_", "").replace("_", " ")} — auto-extracted by self-evolution."""'
            ]
            for line in group['lines']:
                if not line.strip().startswith('#'):
                    helper_lines.append(line)
            helper_lines.append('')
            helper_methods.append(helper_lines)

        new_lines = lines[:func_start]
        new_lines.extend(new_init_lines)
        new_lines.append('')
        for helper in helper_methods:
            new_lines.extend(helper)
        new_lines.extend(lines[func_end:])

        new_code = '\n'.join(new_lines)
        try:
            ast.parse(new_code)
        except SyntaxError:
            return code, None

        return new_code, f"Split {class_name}.__init__ into {len(extract_groups) + 1} methods"

    def _group_by_separators(self, body_lines: List[str]) -> List[Dict]:
        """Group lines by blank-line or comment separators."""
        groups = []
        current_group = {'name': None, 'lines': []}

        for line in body_lines:
            stripped = line.strip()
            if not stripped:
                if current_group['lines']:
                    groups.append(current_group)
                    current_group = {'name': None, 'lines': []}
                continue
            if stripped.startswith('#'):
                if current_group['lines']:
                    groups.append(current_group)
                group_name = stripped.lstrip('#').strip().lower()
                group_name = ''.join(c if c.isalnum() else '_' for c in group_name)[:30].strip('_')
                current_group = {'name': group_name, 'lines': [line]}
                continue
            current_group['lines'].append(line)

        if current_group['lines']:
            groups.append(current_group)
        return groups

    def _split_regular_method(self, code, lines, func_start, func_end,
                              class_name, method_name, body_indent, class_indent,
                              def_lines, func_body_lines):
        """Split a long regular method by extracting the second half into a helper."""
        docstring_lines, actual_body = self._separate_docstring(func_body_lines)
        blocks = self._find_top_level_blocks(actual_body, body_indent)

        if len(blocks) < 2:
            return code, None

        mid = max(1, len(blocks) // 2)
        keep_blocks = blocks[:mid]
        extract_blocks = blocks[mid:]
        helper_name = f'_{method_name}_continued'

        kept_code = '\n'.join(line for b in keep_blocks for line in b)
        extracted_code = '\n'.join(line for b in extract_blocks for line in b)

        passed_vars = self._detect_passed_variables(
            kept_code, extracted_code, def_lines
        )

        return self.__split_regular_method_continued(extract_blocks, helper_name, keep_blocks, passed_vars, code, lines, func_start, func_end, class_name, method_name, body_indent, class_indent, def_lines)

    def __split_regular_method_continued(self, extract_blocks, helper_name, keep_blocks, passed_vars, code, lines, func_start, func_end, class_name, method_name, body_indent, class_indent, def_lines):
        """Continuation of _split_regular_method — auto-extracted by self-evolution."""
        last_line = extract_blocks[-1][-1].strip() if extract_blocks[-1] else ''
        has_return = last_line.startswith('return ')
        params_sig = ', '.join(passed_vars) if passed_vars else ''
        params_call = ', '.join(passed_vars) if passed_vars else ''

        new_method = list(def_lines)
        new_method.extend(docstring_lines)
        for block in keep_blocks:
            new_method.extend(block)
            new_method.append('')
        call = f'self.{helper_name}({params_call})'
        new_method.append(f'{body_indent}{"return " if has_return else ""}{call}')
        new_method.append('')

        helper = self._build_helper_method(
            helper_name, method_name, params_sig, body_indent, class_indent,
            keep_blocks, extract_blocks
        )

        new_lines = lines[:func_start]
        new_lines.extend(new_method)
        new_lines.extend(helper)
        new_lines.extend(lines[func_end:])

        new_code = '\n'.join(new_lines)
        try:
            ast.parse(new_code)
        except SyntaxError:
            return code, None

        return new_code, f"Split {class_name}.{method_name} into 2 methods (passing {len(passed_vars)} vars)"


    def _separate_docstring(self, body_lines: List[str]) -> Tuple[List[str], List[str]]:
        """Separate leading docstring from body."""
        docstring_lines = []
        body_start_idx = 0
        in_docstring = False
        for i, line in enumerate(body_lines):
            stripped = line.strip()
            if i == 0 and (stripped.startswith('"""') or stripped.startswith("'''")):
                docstring_lines.append(line)
                if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                    body_start_idx = i + 1
                    break
                in_docstring = True
            elif in_docstring:
                docstring_lines.append(line)
                if '"""' in stripped or "'''" in stripped:
                    body_start_idx = i + 1
                    break
            else:
                body_start_idx = i
                break
        return docstring_lines, body_lines[body_start_idx:]

    def _find_top_level_blocks(self, body_lines: List[str], body_indent: str) -> List[List[str]]:
        """Find top-level code blocks separated by blank lines at body indent level."""
        blocks = []
        current_block = []
        for line in body_lines:
            stripped = line.strip()
            if not stripped:
                if current_block:
                    last_indent = len(current_block[-1]) - len(current_block[-1].lstrip())
                    if last_indent <= len(body_indent):
                        blocks.append(current_block)
                        current_block = []
                        continue
                current_block.append(line)
                continue
            current_block.append(line)
        if current_block:
            blocks.append(current_block)
        return blocks

    def _detect_passed_variables(self, kept_code: str, extracted_code: str,
                                 def_lines: List[str]) -> List[str]:
        """Detect local variables from kept code that are used in extracted code."""
        assigned_vars = set()
        for line in kept_code.split('\n'):
            stripped = line.strip()
            m = re.match(r'^([a-zA-Z_]\w*)\s*=\s', stripped)
            if m and not stripped.startswith('self.'):
                assigned_vars.add(m.group(1))
            m = re.match(r'^for\s+([a-zA-Z_]\w*)', stripped)
            if m:
                assigned_vars.add(m.group(1))

        passed_vars = [v for v in sorted(assigned_vars) if re.search(rf'\b{re.escape(v)}\b', extracted_code)]

        orig_def = ' '.join(l.strip() for l in def_lines)
        param_match = re.search(r'\(self,?\s*(.*?)\)', orig_def, re.DOTALL)
        if param_match:
            for param in param_match.group(1).split(','):
                param_name = param.strip().split(':')[0].split('=')[0].strip()
                if param_name and re.search(rf'\b{re.escape(param_name)}\b', extracted_code):
                    if param_name not in passed_vars:
                        passed_vars.append(param_name)

        return passed_vars

    def _build_helper_method(self, helper_name, method_name, params_sig,
                             body_indent, class_indent,
                             keep_blocks, extract_blocks) -> List[str]:
        """Build the extracted helper method lines."""
        helper = [
            f'{class_indent}def {helper_name}(self, {params_sig}):',
            f'{body_indent}"""Continuation of {method_name} — auto-extracted by self-evolution."""'
        ]

        # Add inline imports used in extracted blocks
        extracted_text = '\n'.join(l for b in extract_blocks for l in b)
        for block in keep_blocks:
            for line in block:
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('from '):
                    mod_name = stripped.split()[-1].split('.')[0]
                    if mod_name and re.search(rf'\b{re.escape(mod_name)}\b', extracted_text):
                        helper.append(f'{body_indent}{stripped}')

        all_extracted = [line for block in extract_blocks for line in block if line.strip()]
        min_indent = min((len(l) - len(l.lstrip()) for l in all_extracted), default=0)

        for block in extract_blocks:
            for line in block:
                stripped = line.strip()
                if stripped:
                    if stripped.startswith('import ') or stripped.startswith('from '):
                        continue
                    rebased = line[min_indent:] if len(line) > min_indent else line.lstrip()
                    helper.append(body_indent + rebased)
                else:
                    helper.append('')
            helper.append('')

        return helper

