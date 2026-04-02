"""
💬 CHAT MODELS - Persistence for conversations, files, and user data
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from bson import ObjectId
import json

# For local storage fallback
import pickle
import os

CHAT_HISTORY_FILE = "chat_history.pkl"


class ChatMessage:
    """Single message in a conversation"""
    def __init__(self, role: str, content: str, timestamp: datetime = None, metadata: Dict = None):
        self.role = role  # 'user' or 'assistant'
        self.content = content
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.metadata = metadata or {}

    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatMessage':
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {})
        )


class ChatConversation:
    """A conversation thread with messages"""
    def __init__(self, title: str = None, created: datetime = None, messages: List[ChatMessage] = None,
                 conversation_id: str = None, user_id: str = "default"):
        self.id = conversation_id or str(ObjectId()) if 'ObjectId' in globals() else str(datetime.now().timestamp())
        self.user_id = user_id
        self.title = title or "New Conversation"
        self.created = created or datetime.now(timezone.utc)
        self.updated = self.created
        self.messages: List[ChatMessage] = messages or []

    def add_message(self, role: str, content: str, metadata: Dict = None):
        msg = ChatMessage(role=role, content=content, metadata=metadata)
        self.messages.append(msg)
        self.updated = msg.timestamp
        if not self.title and len(self.messages) >= 2:
            # Auto-title from first user message
            first_user = next((m.content for m in self.messages if m.role == 'user'), None)
            if first_user:
                self.title = first_user[:50] + ("..." if len(first_user) > 50 else "")

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat(),
            "messages": [m.to_dict() for m in self.messages]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatConversation':
        conv = cls(
            conversation_id=data['id'],
            user_id=data['user_id'],
            title=data['title'],
            created=datetime.fromisoformat(data['created']),
            messages=[ChatMessage.from_dict(m) for m in data['messages']]
        )
        conv.updated = datetime.fromisoformat(data['updated'])
        return conv


class ChatStore:
    """Simple storage for chat conversations using local file only (MongoDB removed)"""
    def __init__(self):
        self.conversations: Dict[str, ChatConversation] = {}  # In-memory cache
        self._load()

    def _load(self):
        """Load from local file"""
        self._load_from_file()

    def _load_from_file(self):
        """Load from pickle file"""
        if os.path.exists(CHAT_HISTORY_FILE):
            try:
                with open(CHAT_HISTORY_FILE, 'rb') as f:
                    data = pickle.load(f)
                    for conv_dict in data.values():
                        conv = ChatConversation.from_dict(conv_dict)
                        self.conversations[conv.id] = conv
            except:
                self.conversations = {}

    def _save(self):
        """Save to local file"""
        self._save_to_file()

    def _save_to_file(self):
        pass

    def _save_to_file(self):
        """Save to pickle file"""
        data = {conv.id: conv.to_dict() for conv in self.conversations.values()}
        with open(CHAT_HISTORY_FILE, 'wb') as f:
            pickle.dump(data, f)

    def get_user_conversations(self, user_id: str) -> List[Dict]:
        """Get all conversations for a user"""
        convs = [c for c in self.conversations.values() if c.user_id == user_id]
        convs.sort(key=lambda x: x.updated, reverse=True)
        return [{
            "id": c.id,
            "title": c.title,
            "created": c.created.isoformat(),
            "updated": c.updated.isoformat(),
            "message_count": len(c.messages)
        } for c in convs]

    def get_conversation(self, conv_id: str) -> Optional[ChatConversation]:
        return self.conversations.get(conv_id)

    def create_conversation(self, user_id: str = "default", title: str = None) -> ChatConversation:
        conv = ChatConversation(user_id=user_id, title=title)
        self.conversations[conv.id] = conv
        self._save()
        return conv

    def add_message(self, conv_id: str, role: str, content: str, metadata: Dict = None):
        conv = self.conversations.get(conv_id)
        if conv:
            conv.add_message(role, content, metadata)
            self._save()
            return True
        return False

    def delete_conversation(self, conv_id: str):
        if conv_id in self.conversations:
            del self.conversations[conv_id]
            self._save()
            return True
        return False


# Global store
_chat_store = None

def get_chat_store() -> ChatStore:
    global _chat_store
    if _chat_store is None:
        _chat_store = ChatStore()
    return _chat_store
