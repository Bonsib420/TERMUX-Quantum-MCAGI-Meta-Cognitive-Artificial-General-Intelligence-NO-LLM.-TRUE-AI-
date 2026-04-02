"""
🔮 QUANTUM AI — Shared State
==============================
Central state holder for all shared instances.
Route modules import from here to access db, engines, etc.
"""

import os
import json
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

logger = logging.getLogger("quantum_ai")

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ============================================================================
# LOCAL MEMORY BACKEND (MongoDB-free operation)
# ============================================================================

class SimpleLocalDB:
    """
    Simple file-based database that mimics MongoDB's async interface.
    Uses JSON files stored in ~/.quantum-mcagi-backend/.
    """
    
    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir or os.path.expanduser("~/.quantum-mcagi-backend"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._collections = {}
    
    def __getattr__(self, name: str) -> 'SimpleCollection':
        if name not in self._collections:
            self._collections[name] = SimpleCollection(name, self.data_dir)
        return self._collections[name]
    
    async def command(self, command: str) -> Dict[str, Any]:
        """Mimics MongoDB command interface."""
        if command == "ping":
            return {"ok": 1}
        raise NotImplementedError(f"Command {command} not supported")


class SimpleCollection:
    """A collection that stores documents in a JSON file."""
    
    def __init__(self, name: str, data_dir: Path):
        self.name = name
        self.filepath = data_dir / f"{name}.json"
        self._data: List[Dict] = []
        self._lock = asyncio.Lock()
        self._load()
    
    def _load(self):
        """Load data from disk (synchronous)."""
        if self.filepath.exists():
            try:
                with open(self.filepath, 'r') as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = []
        else:
            self._data = []
    
    async def _save(self):
        """Save data to disk (async)."""
        async with self._lock:
            try:
                # Convert to JSON-serializable format
                serializable = []
                for doc in self._data:
                    serializable.append(self._serialize_doc(doc))
                with open(self.filepath, 'w') as f:
                    json.dump(serializable, f, indent=2, default=str)
            except Exception as e:
                print(f"Error saving {self.name}: {e}")
    
    def _serialize_doc(self, doc: Dict) -> Dict:
        """Convert datetime objects to ISO strings for JSON."""
        result = {}
        for k, v in doc.items():
            if isinstance(v, datetime):
                result[k] = v.isoformat()
            elif isinstance(v, dict):
                result[k] = self._serialize_doc(v)
            else:
                result[k] = v
        return result
    
    def _deserialize_doc(self, doc: Dict) -> Dict:
        """Convert ISO strings back to datetime objects."""
        result = {}
        for k, v in doc.items():
            if isinstance(v, str) and 'T' in v and len(v) > 19:
                try:
                    result[k] = datetime.fromisoformat(v.replace('Z', '+00:00'))
                except:
                    result[k] = v
            elif isinstance(v, dict):
                result[k] = self._deserialize_doc(v)
            else:
                result[k] = v
        return result
    
    def _ensure_ids(self):
        """Ensure all documents have _id fields (synchronous)."""
        for doc in self._data:
            if '_id' not in doc:
                doc['_id'] = str(uuid.uuid4())
    
    def find(self, filter: Optional[Dict] = None, projection: Optional[Dict] = None) -> 'AsyncCursor':
        """Find documents matching filter."""
        self._ensure_ids()
        results = []
        for doc in self._data:
            if self._matches(doc, filter):
                # Apply projection if provided (simple: exclude _id if specified)
                result_doc = self._deserialize_doc(doc.copy())
                if projection:
                    # Very basic projection: only include fields where value is 1 (or exclude if 0)
                    # For simplicity, we'll just ignore projection and return full doc
                    pass
                results.append(result_doc)
        return AsyncCursor(results)
    
    async def find_one(self, filter: Optional[Dict] = None, projection: Optional[Dict] = None) -> Optional[Dict]:
        """Find first matching document."""
        self._ensure_ids()
        for doc in self._data:
            if self._matches(doc, filter):
                result = self._deserialize_doc(doc.copy())
                # For now, ignore projection (Motor includes _id by default unless excluded)
                return result
        return None
    
    async def insert_one(self, document: Dict) -> Any:
        """Insert a document."""
        doc = document.copy()
        if '_id' not in doc:
            doc['_id'] = str(uuid.uuid4())
        # Ensure timestamps are datetime objects
        if 'timestamp' in doc and isinstance(doc['timestamp'], str):
            try:
                doc['timestamp'] = datetime.fromisoformat(doc['timestamp'].replace('Z', '+00:00'))
            except:
                pass
        
        # Append to data (no lock needed for list append in CPython due to GIL)
        self._data.append(doc)
        # Save to disk (handles its own lock)
        await self._save()
        
        class InsertOneResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        return InsertOneResult(doc['_id'])
    
    async def insert_many(self, documents: List[Dict]) -> List[Any]:
        """Insert multiple documents."""
        results = []
        for doc in documents:
            result = await self.insert_one(doc)
            results.append(result)
        return results
    
    async def update_one(self, filter: Dict, update: Dict, upsert: bool = False) -> Any:
        """Update first matching document. If upsert=True and no match, insert new doc."""
        for i, doc in enumerate(self._data):
            if self._matches(doc, filter):
                # Apply $set operations
                if '$set' in update:
                    for k, v in update['$set'].items():
                        doc[k] = v
                # Apply $inc operations
                if '$inc' in update:
                    for k, v in update['$inc'].items():
                        doc[k] = doc.get(k, 0) + v
                # Apply $addToSet operations (add to array if not present)
                if '$addToSet' in update:
                    for key, val in update['$addToSet'].items():
                        current = doc.get(key, [])
                        if not isinstance(current, list):
                            current = []
                        items = val.get('$each') if isinstance(val, dict) and '$each' in val else [val]
                        for item in items:
                            if item not in current:
                                current.append(item)
                        doc[key] = current
                self._data[i] = doc
                await self._save()
                class UpdateResult:
                    def __init__(self, matched_count, modified_count, upserted_id=None):
                        self.matched_count = matched_count
                        self.modified_count = modified_count
                        self.upserted_id = upserted_id
                return UpdateResult(1, 1)
        
        # No match found
        if upsert:
            # Create new document by merging filter and update operations
            new_doc = {}
            # Start with filter fields (simple equality)
            new_doc.update(filter)
            # Apply $set
            if '$set' in update:
                new_doc.update(update['$set'])
            # Apply $inc (initialize then add)
            if '$inc' in update:
                for k, v in update['$inc'].items():
                    new_doc[k] = v  # new doc starts at 0 + v = v
            # Ensure _id
            if '_id' not in new_doc:
                new_doc['_id'] = str(uuid.uuid4())
            # Append and save
            self._data.append(new_doc)
            await self._save()
            class UpdateResult:
                def __init__(self, matched_count, modified_count, upserted_id):
                    self.matched_count = matched_count
                    self.modified_count = 0
                    self.upserted_id = upserted_id
            return UpdateResult(0, 0, new_doc['_id'])
        
        class UpdateResult:
            def __init__(self, matched_count, modified_count):
                self.matched_count = matched_count
                self.modified_count = modified_count
                self.upserted_id = None
        return UpdateResult(0, 0)
    
    async def delete_many(self, filter: Dict) -> Any:
        """Delete all matching documents."""
        initial_len = len(self._data)
        self._data = [doc for doc in self._data if not self._matches(doc, filter)]
        deleted = initial_len - len(self._data)
        await self._save()
        class DeleteResult:
            def __init__(self, deleted_count):
                self.deleted_count = deleted_count
        return DeleteResult(deleted)
    
    async def count_documents(self, filter: Optional[Dict] = None) -> int:
        """Count matching documents."""
        if filter:
            return sum(1 for doc in self._data if self._matches(doc, filter))
        return len(self._data)
    
    async def distinct(self, field: str) -> List[Any]:
        """Get distinct values for a field."""
        values = set()
        for doc in self._data:
            if field in doc:
                values.add(doc[field])
        return list(values)
    
    async def aggregate(self, pipeline: List[Dict]) -> 'AsyncCursor':
        """Basic aggregation pipeline support."""
        results = [self._deserialize_doc(doc.copy()) for doc in self._data]
        for stage in pipeline:
            if '$group' in stage:
                # Very basic grouping
                group_spec = stage['$group']
                group_id = group_spec.get('_id')
                group_fields = {k: v for k, v in group_spec.items() if k != '_id'}
                grouped = {}
                for doc in results:
                    if group_id is None:
                        key = None
                    elif isinstance(group_id, str) and group_id.startswith('$'):
                        field = group_id[1:]
                        key = doc.get(field)
                    else:
                        key = group_id
                    if key not in grouped:
                        grouped[key] = []
                    grouped[key].append(doc)
                # Build output documents
                output = []
                for key, docs in grouped.items():
                    out_doc = {'_id': key}
                    for field, agg in group_fields.items():
                        if isinstance(agg, dict):
                            op = list(agg.keys())[0]
                            expr = agg[op]
                            if op == '$sum':
                                total = 0
                                for d in docs:
                                    if isinstance(expr, str) and expr.startswith('$'):
                                        field = expr[1:]
                                        total += d.get(field, 0)
                                out_doc[field] = total
                            elif op == '$avg':
                                total = 0
                                count = 0
                                for d in docs:
                                    if isinstance(expr, str) and expr.startswith('$'):
                                        field = expr[1:]
                                        total += d.get(field, 0)
                                        count += 1
                                out_doc[field] = total / count if count > 0 else 0
                            elif op == '$push':
                                if isinstance(expr, str) and expr.startswith('$'):
                                    field = expr[1:]
                                    out_doc[field] = [d.get(field) for d in docs]
                    output.append(out_doc)
                results = output
            if '$sort' in stage:
                sort_spec = stage['$sort']
                # sort_spec is like {"last_message": -1} or [("field", 1), ...]
                if isinstance(sort_spec, dict):
                    for field, direction in sort_spec.items():
                        reverse = direction == -1
                        results.sort(key=lambda x: x.get(field, None), reverse=reverse)
                elif isinstance(sort_spec, list):
                    # Multi-field sort (simplified - only first field)
                    field, direction = sort_spec[0]
                    reverse = direction == -1
                    results.sort(key=lambda x: x.get(field, None), reverse=reverse)
            if '$limit' in stage:
                results = results[:stage['$limit']]
            if '$match' in stage:
                filter = stage['$match']
                results = [doc for doc in results if self._matches(doc, filter)]
        return AsyncCursor(results)
    
    def _matches(self, doc: Dict, filter: Optional[Dict]) -> bool:
        """Simple filter matching (supports equality, $exists, $gte, $lte, $ne, $in, $regex)."""
        if not filter:
            return True
        for key, value in filter.items():
            if key == '$exists':
                # Handle {$exists: True/False}
                for exist_key, should_exist in value.items():
                    exists = exist_key in doc
                    if exists != should_exist:
                        return False
            elif isinstance(value, dict):
                # Handle operators like $gte, $lte, $ne, $in, $regex
                for op, op_val in value.items():
                    doc_val = doc.get(key)
                    
                    # If doc_val is None, most comparison operators should fail (field missing)
                    if doc_val is None:
                        # For $gte/$lte, missing field cannot satisfy condition
                        if op in ('$gte', '$lte', '$ne', '$in'):
                            return False
                        # For $regex, None doesn't match
                        if op == '$regex':
                            return False
                    
                    # Handle datetime comparisons: if doc_val is datetime, try to convert op_val
                    if isinstance(doc_val, datetime) and isinstance(op_val, str):
                        try:
                            # Try to parse ISO format string
                            op_val_dt = datetime.fromisoformat(op_val.replace('Z', '+00:00'))
                            # Use the datetime for comparison
                            comparison_val = op_val_dt
                        except (ValueError, TypeError):
                            comparison_val = op_val
                    else:
                        comparison_val = op_val
                    
                    if op == '$gte':
                        if doc_val < comparison_val:
                            return False
                    elif op == '$lte':
                        if doc_val > comparison_val:
                            return False
                    elif op == '$ne':
                        if doc_val == op_val:
                            return False
                    elif op == '$in':
                        if doc_val not in op_val:
                            return False
                    elif op == '$regex':
                        import re
                        if not re.search(op_val, str(doc_val), re.IGNORECASE):
                            return False
            else:
                # Simple equality
                if key not in doc or doc[key] != value:
                    return False
        return True


class AsyncCursor:
    """Mimics Motor's async cursor."""
    
    def __init__(self, data: List[Dict]):
        self._data = data
        self._sort_spec = None
        self._limit_val = None
    
    def sort(self, key_or_list, direction: int = 1):
        """Sort the results."""
        self._sort_spec = (key_or_list, direction)
        return self
    
    def limit(self, n: int):
        """Limit number of results."""
        self._limit_val = n
        return self
    
    async def to_list(self, length: Optional[int] = None) -> List[Dict]:
        """Get results as list."""
        data = self._data.copy()
        if self._sort_spec:
            key_or_list, direction = self._sort_spec
            reverse = direction == -1
            if isinstance(key_or_list, str):
                data.sort(key=lambda x: x.get(key_or_list, None), reverse=reverse)
            elif isinstance(key_or_list, list):
                # Multi-field sort - apply in reverse order
                for field, direction in reversed(key_or_list):
                    reverse = direction == -1
                    data.sort(key=lambda x: x.get(field, None), reverse=reverse)
        if self._limit_val:
            data = data[:self._limit_val]
        if length:
            data = data[:length]
        return data


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

# Always use local file-based storage (MongoDB removed)
db = SimpleLocalDB()

# Lazy-initialized singletons (set during startup)
cognitive_core = None
universal_explorer = None
covenant_manager = None
operational_guidelines = None
dictionary = None
shared_link = None
hidden_thinking = None

# Idle/dream state management
last_activity_time = None
is_idle = False
dream_task = None


def initialize():
    """Initialize all Quantum AI systems. Called once at startup."""
    global cognitive_core, universal_explorer, covenant_manager
    global operational_guidelines, dictionary, shared_link, hidden_thinking
    global last_activity_time, dream_task, is_idle

    from quantum_cognitive_core import QuantumCognitiveCore
    from universal_explorer import UniversalExplorer
    from covenant_manager import CovenantManager, OperationalGuidelines
    from dictionary_integration import get_dictionary_integration
    from shared_link_handler import get_shared_link_handler
    from hidden_thinking import get_hidden_thinking
    from dream_state import get_dream_engine

    cognitive_core = QuantumCognitiveCore(db)
    universal_explorer = UniversalExplorer(db)
    covenant_manager = CovenantManager(db)
    operational_guidelines = OperationalGuidelines(db)
    dictionary = get_dictionary_integration(cognitive_core.semantic_memory)
    shared_link = get_shared_link_handler()
    hidden_thinking = get_hidden_thinking(cognitive_core, dictionary, universal_explorer)
    
    # Initialize dream engine
    dream_engine = get_dream_engine(db)
    
    # Start background idle/dream monitoring
    last_activity_time = datetime.now(timezone.utc)
    is_idle = False
    
    async def monitor_idle():
        """Background task: check idle status and manage dream state.
        When idle, runs dream cycles which now include:
        - dream_driven_research (auto-fetches web content from ideas)
        - cloud_sync (auto-saves brain to Wolfram Cloud)
        - plus the original activities (consolidation, reflection, ideas, etc.)
        """
        global last_activity_time, is_idle, dream_task
        
        while True:
            await asyncio.sleep(60)  # Check every minute
            
            now = datetime.now(timezone.utc)
            idle_minutes = (now - last_activity_time).total_seconds() / 60
            
            if idle_minutes >= 5 and not is_idle:
                # Enter dream state
                is_idle = True
                try:
                    dream_engine.enter_dream_state()
                    logger.info("🌙 Entering dream state (idle for 5+ min)")
                except Exception as e:
                    logger.error(f"Dream state entry failed: {e}")
            
            elif idle_minutes < 5 and is_idle:
                # Exit dream state (user became active)
                is_idle = False
                try:
                    result = await dream_engine.exit_dream_state()
                    if result.get('dream_summary'):
                        logger.info(f"☀️ Awakened from dream. Insights: {len(result['dream_summary'].get('insights',[]))}")
                except Exception as e:
                    logger.error(f"Dream state exit failed: {e}")
            
            # While dreaming, run dream cycles periodically
            if is_idle:
                try:
                    cycle_result = await dream_engine.dream_cycle()
                    if cycle_result and not cycle_result.get('error'):
                        activity = cycle_result.get('activity', '')
                        logger.info(f"Dream cycle: {activity} - {str(cycle_result)[:80]}")
                except Exception as e:
                    logger.error(f"Dream cycle error: {e}")
    
    # Start the monitor task
    dream_task = asyncio.create_task(monitor_idle())
    logger.info("✅ Background idle/dream monitor started (autonomous research + cloud sync enabled)")
