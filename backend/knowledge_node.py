"""
🌐 Knowledge Node — Multi-User Federated Knowledge System

Each user is a "knowledge node" that contributes information across domains.
The system automatically grows with each new user — like the Internet, Facebook,
or email services expand with each new participant.

Architecture:
  - KnowledgeNode: Represents one user/contributor
  - KnowledgeNetwork: The collection of all nodes (the "brain")
  - Auto-merges user contributions into shared knowledge
  - Uses CloudProviderRegistry for storage (provider-agnostic)

Growth model:
  - New user → new node → new namespace in cloud
  - Each node can contribute to ANY domain
  - Shared knowledge = union of all node contributions
  - More users = richer, more diverse brain
  - No central bottleneck — nodes are independent but interconnected
"""

import logging
import hashlib
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timezone

logger = logging.getLogger("quantum_ai")


class KnowledgeNode:
    """
    A single knowledge contributor (user, device, or external source).
    Each node has its own namespace and can contribute to any domain.
    """

    def __init__(self, node_id: str, display_name: str = None):
        self.node_id = node_id
        self.display_name = display_name or node_id
        self._hash = hashlib.sha256(node_id.encode()).hexdigest()[:12]
        self.domains_contributed: Set[str] = set()
        self.created_at = datetime.now(timezone.utc)
        self.last_active = self.created_at
        self.contribution_count = 0

    def contribute(self, domain: str, concepts: List[str] = None,
                   insights: List[str] = None, raw_text: str = None) -> Dict:
        """
        Contribute knowledge to a domain. Returns a contribution record
        ready for cloud storage.
        """
        self.last_active = datetime.now(timezone.utc)
        self.domains_contributed.add(domain)
        self.contribution_count += 1

        return {
            'node_id': self.node_id,
            'node_hash': self._hash,
            'display_name': self.display_name,
            'domain': domain,
            'concepts': concepts or [],
            'insights': insights or [],
            'raw_text': raw_text or '',
            'contributed_at': self.last_active.isoformat(),
            'contribution_number': self.contribution_count,
        }

    def to_dict(self) -> Dict:
        return {
            'node_id': self.node_id,
            'node_hash': self._hash,
            'display_name': self.display_name,
            'domains': list(self.domains_contributed),
            'contributions': self.contribution_count,
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat(),
        }


class KnowledgeNetwork:
    """
    The network of all knowledge nodes — this IS the brain.
    Grows automatically with each new user. Provider-agnostic.

    The cloud stores the persistent state (the brain).
    The app/website is just a window into the brain.
    """

    def __init__(self):
        self._nodes: Dict[str, KnowledgeNode] = {}
        self._shared_knowledge: Dict[str, Dict] = {}
        self._registry = None  # Lazy init

    def _get_registry(self):
        """Lazy-load cloud registry to avoid circular imports."""
        if self._registry is None:
            from cloud_provider import get_cloud_registry
            self._registry = get_cloud_registry()
        return self._registry

    # ── Node management ──────────────────────────────────────────────────

    def register_node(self, node_id: str, display_name: str = None) -> KnowledgeNode:
        """
        Register a new knowledge node (user/device/source).
        Auto-expands the network — like a new user joining Facebook.
        """
        if node_id not in self._nodes:
            node = KnowledgeNode(node_id, display_name)
            self._nodes[node_id] = node

            # Persist node registration to cloud
            registry = self._get_registry()
            registry.save(
                f"QuantumMCAGI/nodes/{node._hash}/info",
                node.to_dict()
            )
            logger.info(f"🌐 New knowledge node registered: {display_name or node_id}")

        return self._nodes[node_id]

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        return self._nodes.get(node_id)

    # ── Knowledge contribution ───────────────────────────────────────────

    def contribute(self, node_id: str, domain: str,
                   concepts: List[str] = None, insights: List[str] = None,
                   raw_text: str = None) -> Dict:
        """
        A user contributes knowledge to a domain.
        Stored in their namespace AND merged into shared knowledge.
        """
        node = self._nodes.get(node_id)
        if not node:
            node = self.register_node(node_id)

        contribution = node.contribute(domain, concepts, insights, raw_text)

        # Save to user's cloud namespace
        registry = self._get_registry()
        registry.save_user_knowledge(node_id, domain, contribution)

        # Update shared knowledge for this domain
        self._merge_into_shared(domain, contribution)

        return contribution

    def _merge_into_shared(self, domain: str, contribution: Dict):
        """Merge a single contribution into the shared knowledge pool."""
        if domain not in self._shared_knowledge:
            self._shared_knowledge[domain] = {
                'domain': domain,
                'concepts': [],
                'insights': [],
                'contributors': set(),
                'last_updated': None,
            }

        shared = self._shared_knowledge[domain]
        shared['concepts'].extend(contribution.get('concepts', []))
        shared['concepts'] = list(set(shared['concepts']))  # Deduplicate
        shared['insights'].extend(contribution.get('insights', []))
        shared['contributors'].add(contribution.get('node_id', ''))
        shared['last_updated'] = datetime.now(timezone.utc).isoformat()

        # Persist to cloud
        registry = self._get_registry()
        save_data = {
            **shared,
            'contributors': list(shared['contributors']),
        }
        registry.save(f"QuantumMCAGI/shared/{domain}", save_data)

    # ── Knowledge retrieval ──────────────────────────────────────────────

    def get_shared_knowledge(self, domain: str) -> Optional[Dict]:
        """Get the merged shared knowledge for a domain."""
        if domain in self._shared_knowledge:
            shared = self._shared_knowledge[domain]
            return {
                **shared,
                'contributors': list(shared['contributors']) if isinstance(shared['contributors'], set) else shared['contributors'],
            }

        # Try loading from cloud
        registry = self._get_registry()
        return registry.load(f"QuantumMCAGI/shared/{domain}")

    def get_all_domains(self) -> List[str]:
        """List all domains that have shared knowledge."""
        local_domains = list(self._shared_knowledge.keys())
        registry = self._get_registry()
        cloud_paths = registry.list_objects('QuantumMCAGI/shared/')
        cloud_domains = [p.split('/')[-1] for p in cloud_paths if p.startswith('QuantumMCAGI/shared/')]
        return sorted(set(local_domains + cloud_domains))

    # ── Network status ───────────────────────────────────────────────────

    def get_status(self) -> Dict:
        """
        Network status — how big is the brain?
        Like checking how many users Facebook has.
        """
        registry = self._get_registry()
        node_paths = registry.list_nodes()
        shared_domains = self.get_all_domains()

        return {
            'active_nodes': len(self._nodes),
            'total_registered_nodes': len(node_paths),
            'shared_domains': len(shared_domains),
            'domains': shared_domains,
            'total_shared_concepts': sum(
                len(s.get('concepts', [])) for s in self._shared_knowledge.values()
            ),
            'cloud_status': registry.status(),
        }

    def full_merge(self) -> Dict[str, int]:
        """
        Full merge of all user contributions across all domains.
        Call periodically to consolidate the brain.
        """
        registry = self._get_registry()
        domains = self.get_all_domains()
        results = {}

        for domain in domains:
            merged = registry.merge_shared_knowledge(domain)
            if merged:
                results[domain] = merged.get('contributors', 0)

        return results


# ── Global singleton ─────────────────────────────────────────────────────────

_knowledge_network = None

def get_knowledge_network() -> KnowledgeNetwork:
    """Get or create the global knowledge network."""
    global _knowledge_network
    if _knowledge_network is None:
        _knowledge_network = KnowledgeNetwork()
    return _knowledge_network
