"""
Conversation memory management using LangChain.

Provides session-based memory for chatbot conversations.
"""
from __future__ import annotations

import uuid
from threading import Lock
from typing import Dict, List, Optional

from langchain.memory import ConversationBufferMemory


class MemoryService:
    """Single session memory wrapper around LangChain's ConversationBufferMemory."""
    
    def __init__(self):
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
    def add_user_message(self, message: str) -> None:
        """Add a user message to the conversation history."""
        self.memory.chat_memory.add_user_message(message)
        
    def add_ai_message(self, message: str) -> None:
        """Add an AI message to the conversation history."""
        self.memory.chat_memory.add_ai_message(message)
        
    def get_chat_history(self) -> List[Dict]:
        """Get the current chat history."""
        messages = self.memory.chat_memory.messages
        return [{"role": msg.type, "content": msg.content} for msg in messages]
    
    def get_history_as_string(self) -> str:
        """Get conversation history as a formatted string."""
        messages = self.memory.chat_memory.messages
        if not messages:
            return ""
        
        lines = []
        for msg in messages:
            prefix = "User" if msg.type == "human" else "Assistant"
            lines.append(f"{prefix}: {msg.content}")
        
        return "\n".join(lines)
        
    def clear(self) -> None:
        """Clear the conversation history."""
        self.memory.clear()


class MemoryManager:
    """
    Manages conversation memory across multiple sessions.
    
    Each session gets its own MemoryService instance.
    Thread-safe for concurrent access.
    """
    
    _sessions: Dict[str, MemoryService] = {}
    _lock: Lock = Lock()
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> tuple[str, MemoryService]:
        """
        Get existing session or create a new one.
        
        Args:
            session_id: Optional existing session ID
            
        Returns:
            Tuple of (session_id, memory_service)
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = MemoryService()
            return session_id, self._sessions[session_id]
    
    def add_interaction(self, session_id: str, user_message: str, ai_response: str) -> None:
        """Add a user-AI interaction to session memory."""
        with self._lock:
            if session_id in self._sessions:
                memory = self._sessions[session_id]
                memory.add_user_message(user_message)
                memory.add_ai_message(ai_response)
    
    def get_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session."""
        with self._lock:
            if session_id not in self._sessions:
                return []
            return self._sessions[session_id].get_chat_history()
    
    def get_history_as_string(self, session_id: str) -> str:
        """Get conversation history as a formatted string."""
        with self._lock:
            if session_id not in self._sessions:
                return ""
            return self._sessions[session_id].get_history_as_string()
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a specific session's memory."""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].clear()
                del self._sessions[session_id]
                return True
            return False
    
    def clear_all(self) -> None:
        """Clear all session memories."""
        with self._lock:
            for session in self._sessions.values():
                session.clear()
            self._sessions.clear()


# Global memory manager instance
memory_manager = MemoryManager()


__all__ = ["MemoryService", "MemoryManager", "memory_manager"]
