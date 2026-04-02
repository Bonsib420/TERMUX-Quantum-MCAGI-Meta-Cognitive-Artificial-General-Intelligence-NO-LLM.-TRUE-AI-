"""
🧬 Self-Evolution Engine — Runner Module
=========================================
Auto-evolution cycle, improvement application, and scheduling.
"""

from typing import Dict
from datetime import datetime, timezone


class RunnerMixin:
    """Mixin providing auto-evolution cycle and improvement application."""

    def should_auto_evolve(self) -> bool:
        """Check if it's time for auto-evolution (60-90 day cycle)."""
        if self.last_evolution is None:
            return True
        days_since = (datetime.now(timezone.utc) - self.last_evolution).days
        return days_since >= self.auto_evolution_interval_days

    async def auto_evolve(self) -> Dict:
        """Perform automatic self-evolution.
        ACTUALLY rewrites code based on identified improvements.
        """
        results = {
            'evolved': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'improvements_found': [],
            'changes_made': [],
            'skipped': [],
            'errors': []
        }

        for filename in self.modifiable_files:
            if self.is_evolution_locked():
                break
            improvements = self.identify_improvements(filename)

            for imp in improvements:
                results['improvements_found'].append({
                    'type': imp.get('type'),
                    'target': imp.get('target'),
                    'suggestion': imp.get('suggestion'),
                    'file': filename
                })

            for improvement in improvements:
                try:
                    change = await self._apply_improvement(filename, improvement)
                    if change.get('success'):
                        results['changes_made'].append({
                            'file': filename,
                            'type': improvement.get('type'),
                            'change': change.get('change', ''),
                            'backup': change.get('backup_path', '')
                        })
                    else:
                        reason = change.get('reason') or change.get('error') or 'unknown'
                        results['skipped'].append({
                            'file': filename,
                            'type': improvement.get('type'),
                            'reason': reason
                        })
                except Exception as e:
                    results['errors'].append({
                        'file': filename,
                        'type': improvement.get('type', 'unknown'),
                        'error': str(e)
                    })

        self.pending_improvements = len(results['improvements_found']) - len(results['changes_made'])
        self.last_evolution = datetime.now(timezone.utc)

        if self.db is not None:
            try:
                db_record = {
                    'timestamp': results['timestamp'],
                    'improvements_found': len(results['improvements_found']),
                    'changes_made': len(results['changes_made']),
                    'errors': len(results['errors']),
                    'details': results
                }
                await self.db.evolution_log.insert_one(db_record)
            except Exception:
                pass

        return results

    async def _apply_improvement(self, filename: str, improvement: Dict) -> Dict:
        """ACTUALLY apply an improvement to the code.
        This is where the AI rewrites itself.
        """
        analysis = self.read_own_code(filename)
        if 'error' in analysis:
            return {'success': False, 'error': analysis['error']}

        code = analysis['code']
        improvement_type = improvement.get('type')
        target = improvement.get('target', '')

        new_code = code
        change_made = None

        if improvement_type == 'missing_docstring':
            new_code, change_made = self._add_docstring(code, target)
        elif improvement_type == 'bare_except':
            new_code, change_made = self._fix_bare_except(code, target)
        elif improvement_type == 'unused_import':
            new_code, change_made = self._remove_unused_import(code, target)
        elif improvement_type == 'todo_items':
            return {'success': False, 'reason': 'TODO items require manual review'}
        elif improvement_type == 'long_function':
            new_code, change_made = self._split_long_function(code, target)
        elif improvement_type == 'file_too_long':
            return await self._split_long_file(filename, code)
        elif improvement_type == 'class_too_large':
            new_code, change_made = self._split_large_class(code, target, filename)

        if new_code != code and change_made:
            result = self.rewrite_code(filename, new_code, f"Auto-evolution: {improvement_type}")
            result['improvement'] = improvement
            result['change'] = change_made
            return result

        return {'success': False, 'reason': change_made or 'No changes needed or could not apply'}
