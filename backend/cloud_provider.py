"""
☁️ Cloud Provider Abstraction Layer
Provider-agnostic cloud storage that can grow with each user and eventually
separate from any single cloud vendor (Wolfram, S3, Firebase, etc.).

Architecture:
  - CloudProvider: Abstract base — any backend implements save/load/list/delete
  - WolframCloudProvider: Current primary (wraps wolfram_cloud.py)
  - LocalProvider: Local JSON-file fallback (always available)
  - CloudProviderRegistry: Manages multiple providers, auto-failover

Growth model (like Internet/Facebook/email):
  - Each user gets a namespace: QuantumMCAGI/users/{user_id}/...
  - Each node gets a namespace: QuantumMCAGI/nodes/{node_id}/...
  - Shared knowledge lives in: QuantumMCAGI/shared/...
  - New users/nodes auto-expand the namespace — no config needed
  - Providers can be swapped or added without changing callers
"""

import os
import json
import logging
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("quantum_ai")


# ── Abstract base ────────────────────────────────────────────────────────────

class CloudProvider(ABC):
    """
    Abstract cloud provider. Implement this to add any storage backend.
    All paths are logical (e.g. 'QuantumMCAGI/brain') — the provider maps
    them to its own storage scheme.
    """

    @abstractmethod
    def save(self, path: str, data: dict) -> bool:
        """Save JSON-serializable data to a logical path. Returns success."""
        ...

    @abstractmethod
    def load(self, path: str) -> Optional[dict]:
        """Load data from a logical path. Returns dict or None."""
        ...

    @abstractmethod
    def list_objects(self, prefix: str) -> List[str]:
        """List all logical paths under a prefix."""
        ...

    @abstractmethod
    def delete(self, path: str) -> bool:
        """Delete data at a logical path. Returns success."""
        ...

    @abstractmethod
    def status(self) -> Dict[str, Any]:
        """Return provider status (connected, object count, etc.)."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...


# ── Wolfram Cloud implementation ─────────────────────────────────────────────

class WolframCloudProvider(CloudProvider):
    """
    Wolfram Cloud storage via wolframclient.
    Wraps the existing wolfram_cloud.py functions.
    """

    @property
    def name(self) -> str:
        return "Wolfram Cloud"

    def _get_session(self):
        from wolfram_cloud import get_cloud_session
        return get_cloud_session()

    def save(self, path: str, data: dict) -> bool:
        try:
            from wolframclient.language import wl
            from wolfram_cloud import _serialize_dates
            session = self._get_session()
            serialized = _serialize_dates(data)
            session.evaluate(wl.CloudPut(json.dumps(serialized), path))
            session.stop()
            return True
        except Exception as e:
            logger.warning(f"[WolframCloud] save({path}) failed: {e}")
            return False

    def load(self, path: str) -> Optional[dict]:
        try:
            from wolframclient.language import wl
            session = self._get_session()
            raw = session.evaluate(wl.CloudGet(path))
            session.stop()
            if raw:
                return json.loads(raw)
        except Exception as e:
            logger.warning(f"[WolframCloud] load({path}) failed: {e}")
        return None

    def list_objects(self, prefix: str) -> List[str]:
        try:
            from wolframclient.language import wl
            session = self._get_session()
            objects = session.evaluate(wl.CloudObjects(f'{prefix}*'))
            session.stop()
            if isinstance(objects, (list, tuple)):
                return [str(o) for o in objects]
            return [str(objects)] if objects else []
        except Exception as e:
            logger.warning(f"[WolframCloud] list({prefix}) failed: {e}")
            return []

    def delete(self, path: str) -> bool:
        try:
            from wolframclient.language import wl
            session = self._get_session()
            session.evaluate(wl.DeleteObject(wl.CloudObject(path)))
            session.stop()
            return True
        except Exception as e:
            logger.warning(f"[WolframCloud] delete({path}) failed: {e}")
            return False

    def status(self) -> Dict[str, Any]:
        try:
            objects = self.list_objects('QuantumMCAGI/')
            return {
                'provider': self.name,
                'connected': True,
                'objects': len(objects),
                'paths': objects[:20],
            }
        except Exception as e:
            return {'provider': self.name, 'connected': False, 'error': str(e)}


# ── Local filesystem fallback ────────────────────────────────────────────────

class LocalProvider(CloudProvider):
    """
    Local JSON file storage. Always available, zero dependencies.
    Stores at ~/.quantum-mcagi-cloud/{path}.json
    """

    def __init__(self, base_dir: str = None):
        self._base = Path(base_dir or os.path.expanduser('~/.quantum-mcagi-cloud'))
        self._base.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "Local Storage"

    def _resolve(self, path: str) -> Path:
        safe = path.replace('/', os.sep)
        target = self._base / f"{safe}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def save(self, path: str, data: dict) -> bool:
        try:
            target = self._resolve(path)
            with open(target, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.warning(f"[Local] save({path}) failed: {e}")
            return False

    def load(self, path: str) -> Optional[dict]:
        try:
            target = self._resolve(path)
            if target.exists():
                with open(target) as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"[Local] load({path}) failed: {e}")
        return None

    def list_objects(self, prefix: str) -> List[str]:
        try:
            safe_prefix = prefix.replace('/', os.sep)
            search_dir = self._base / safe_prefix
            if not search_dir.exists():
                # Search parent for matching files
                search_dir = self._base
            results = []
            for p in search_dir.rglob('*.json'):
                rel = str(p.relative_to(self._base)).replace(os.sep, '/').replace('.json', '')
                if rel.startswith(prefix.rstrip('/')):
                    results.append(rel)
            return results
        except Exception as e:
            logger.warning(f"[Local] list({prefix}) failed: {e}")
            return []

    def delete(self, path: str) -> bool:
        try:
            target = self._resolve(path)
            if target.exists():
                target.unlink()
                return True
        except Exception as e:
            logger.warning(f"[Local] delete({path}) failed: {e}")
        return False

    def status(self) -> Dict[str, Any]:
        objects = self.list_objects('QuantumMCAGI/')
        return {
            'provider': self.name,
            'connected': True,
            'base_dir': str(self._base),
            'objects': len(objects),
        }


# ── Provider Registry (multi-provider with failover) ─────────────────────────

class CloudProviderRegistry:
    """
    Manages multiple cloud providers. Writes to ALL, reads from FIRST success.
    This is how growth works: add a new provider and it auto-replicates.

    Usage:
        registry = get_cloud_registry()
        registry.save('QuantumMCAGI/brain', brain_data)
        data = registry.load('QuantumMCAGI/brain')
    """

    def __init__(self):
        self._providers: List[CloudProvider] = []
        self._primary_index = 0

    def register(self, provider: CloudProvider, primary: bool = False):
        """Register a cloud provider. First registered or primary=True is the primary."""
        if primary:
            self._providers.insert(0, provider)
            self._primary_index = 0
        else:
            self._providers.append(provider)

    @property
    def providers(self) -> List[CloudProvider]:
        return list(self._providers)

    def save(self, path: str, data: dict) -> bool:
        """Save to ALL providers (replication for growth). Returns True if any succeed."""
        any_success = False
        for provider in self._providers:
            try:
                if provider.save(path, data):
                    any_success = True
            except Exception as e:
                logger.warning(f"[Registry] {provider.name} save failed: {e}")
        return any_success

    def load(self, path: str) -> Optional[dict]:
        """Load from first provider that succeeds (failover chain)."""
        for provider in self._providers:
            try:
                data = provider.load(path)
                if data is not None:
                    return data
            except Exception as e:
                logger.warning(f"[Registry] {provider.name} load failed: {e}")
        return None

    def list_objects(self, prefix: str) -> List[str]:
        """Merge object lists from all providers (union)."""
        all_paths = set()
        for provider in self._providers:
            try:
                all_paths.update(provider.list_objects(prefix))
            except Exception:
                pass
        return sorted(all_paths)

    def delete(self, path: str) -> bool:
        """Delete from all providers."""
        any_success = False
        for provider in self._providers:
            try:
                if provider.delete(path):
                    any_success = True
            except Exception:
                pass
        return any_success

    def status(self) -> Dict[str, Any]:
        """Status from all providers."""
        return {
            'providers': [p.status() for p in self._providers],
            'total_providers': len(self._providers),
            'provider_names': [p.name for p in self._providers],
        }

    # ── User/node namespacing (auto-growth) ──────────────────────────────────

    def user_path(self, user_id: str, sub_path: str) -> str:
        """Generate a user-namespaced path. Each user auto-expands the brain."""
        safe_id = hashlib.sha256(user_id.encode()).hexdigest()[:12]
        return f"QuantumMCAGI/users/{safe_id}/{sub_path}"

    def node_path(self, node_id: str, sub_path: str) -> str:
        """Generate a node-namespaced path for distributed expansion."""
        return f"QuantumMCAGI/nodes/{node_id}/{sub_path}"

    def save_user_knowledge(self, user_id: str, domain: str, data: dict) -> bool:
        """Save knowledge contributed by a user for a specific domain."""
        data['_meta'] = {
            'user_id': user_id,
            'domain': domain,
            'contributed_at': datetime.now(timezone.utc).isoformat(),
        }
        path = self.user_path(user_id, f"knowledge/{domain}")
        return self.save(path, data)

    def load_user_knowledge(self, user_id: str, domain: str) -> Optional[dict]:
        """Load a user's contributed knowledge for a domain."""
        path = self.user_path(user_id, f"knowledge/{domain}")
        return self.load(path)

    def list_users(self) -> List[str]:
        """List all user namespaces (growth indicator)."""
        return self.list_objects('QuantumMCAGI/users/')

    def list_nodes(self) -> List[str]:
        """List all node namespaces (distributed expansion indicator)."""
        return self.list_objects('QuantumMCAGI/nodes/')

    def merge_shared_knowledge(self, domain: str) -> Optional[dict]:
        """
        Merge all user contributions for a domain into shared knowledge.
        This is how the brain grows with each new user — like Facebook or email.
        """
        user_paths = self.list_objects(f'QuantumMCAGI/users/')
        domain_suffix = f"knowledge/{domain}"

        merged = {
            'domain': domain,
            'merged_at': datetime.now(timezone.utc).isoformat(),
            'contributors': 0,
            'concepts': [],
            'insights': [],
        }

        for path in user_paths:
            if path.endswith(domain_suffix):
                data = self.load(path)
                if data:
                    merged['contributors'] += 1
                    merged['concepts'].extend(data.get('concepts', []))
                    merged['insights'].extend(data.get('insights', []))

        if merged['contributors'] > 0:
            # Deduplicate concepts
            merged['concepts'] = list(set(merged['concepts']))
            shared_path = f"QuantumMCAGI/shared/{domain}"
            self.save(shared_path, merged)
            return merged
        return None


# ── Global singleton ─────────────────────────────────────────────────────────

_cloud_registry = None

def get_cloud_registry() -> CloudProviderRegistry:
    """
    Get or create the global cloud provider registry.
    Initializes with local storage (always available) + Wolfram Cloud (if configured).
    """
    global _cloud_registry
    if _cloud_registry is None:
        _cloud_registry = CloudProviderRegistry()

        # Local storage is always available (zero-dependency fallback)
        _cloud_registry.register(LocalProvider())

        # Try to add Wolfram Cloud
        try:
            _cloud_registry.register(WolframCloudProvider(), primary=True)
            logger.info("☁️ Cloud registry: Wolfram Cloud + Local Storage")
        except Exception:
            logger.info("☁️ Cloud registry: Local Storage only (Wolfram unavailable)")

    return _cloud_registry
