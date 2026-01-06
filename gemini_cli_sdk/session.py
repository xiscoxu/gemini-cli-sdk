"""Session management for Gemini CLI SDK."""

import uuid
import time
import logging
from typing import Dict, List, Optional
from .models import Message, SessionInfo, MessageRole
from .exceptions import GeminiSessionError


class SessionManager:
    """Manages conversation sessions for Gemini CLI SDK."""
    
    def __init__(self, max_context_length: int = 50):
        """Initialize session manager.
        
        Args:
            max_context_length: Maximum number of messages to keep in context
        """
        self.max_context_length = max_context_length
        self._sessions: Dict[str, Dict] = {}
        self._logger = logging.getLogger(__name__)
    
    def create_session(self, user_id: Optional[str] = None, 
                      metadata: Optional[Dict] = None) -> str:
        """Create a new conversation session.
        
        Args:
            user_id: Optional user identifier
            metadata: Optional metadata to associate with the session
            
        Returns:
            str: Unique session ID
        """
        session_id = str(uuid.uuid4())
        current_time = time.time()
        
        self._sessions[session_id] = {
            'user_id': user_id,
            'created_at': current_time,
            'last_activity': current_time,
            'messages': [],
            'metadata': metadata or {},
            'process_id': None
        }
        
        self._logger.info(f"Created new session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Dict:
        """Get session data.
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            Dict: Session data
            
        Raises:
            GeminiSessionError: If session not found
        """
        if session_id not in self._sessions:
            raise GeminiSessionError(f"Session {session_id} not found")
        return self._sessions[session_id]
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists.
        
        Args:
            session_id: Session ID to check
            
        Returns:
            bool: True if session exists
        """
        return session_id in self._sessions
    
    def add_message(self, session_id: str, role: MessageRole, 
                   content: str, metadata: Optional[Dict] = None):
        """Add a message to the session.
        
        Args:
            session_id: Session ID
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional message metadata
            
        Raises:
            GeminiSessionError: If session not found
        """
        session = self.get_session(session_id)
        
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        session['messages'].append(message)
        session['last_activity'] = time.time()
        
        # Limit context length
        if len(session['messages']) > self.max_context_length:
            removed_count = len(session['messages']) - self.max_context_length
            session['messages'] = session['messages'][-self.max_context_length:]
            self._logger.debug(f"Trimmed {removed_count} messages from session {session_id}")
        
        self._logger.debug(f"Added {role.value} message to session {session_id}")
    
    def get_context(self, session_id: str, limit: Optional[int] = None) -> List[Message]:
        """Get conversation context for a session.
        
        Args:
            session_id: Session ID
            limit: Optional limit on number of messages to return
            
        Returns:
            List[Message]: List of messages in chronological order
            
        Raises:
            GeminiSessionError: If session not found
        """
        session = self.get_session(session_id)
        messages = session['messages']
        
        if limit and limit > 0:
            return messages[-limit:]
        return messages
    
    def get_session_info(self, session_id: str) -> SessionInfo:
        """Get session information.
        
        Args:
            session_id: Session ID
            
        Returns:
            SessionInfo: Session information object
            
        Raises:
            GeminiSessionError: If session not found
        """
        session = self.get_session(session_id)
        
        return SessionInfo(
            session_id=session_id,
            created_at=session['created_at'],
            last_activity=session['last_activity'],
            message_count=len(session['messages']),
            process_id=session.get('process_id'),
            metadata=session['metadata']
        )
    
    def update_session_metadata(self, session_id: str, metadata: Dict):
        """Update session metadata.
        
        Args:
            session_id: Session ID
            metadata: New metadata to merge with existing
            
        Raises:
            GeminiSessionError: If session not found
        """
        session = self.get_session(session_id)
        session['metadata'].update(metadata)
        session['last_activity'] = time.time()
        
        self._logger.debug(f"Updated metadata for session {session_id}")
    
    def set_process_id(self, session_id: str, process_id: Optional[str]):
        """Associate a process ID with a session.
        
        Args:
            session_id: Session ID
            process_id: Process ID to associate (or None to clear)
            
        Raises:
            GeminiSessionError: If session not found
        """
        session = self.get_session(session_id)
        session['process_id'] = process_id
        session['last_activity'] = time.time()
        
        self._logger.debug(f"Set process_id {process_id} for session {session_id}")
    
    def close_session(self, session_id: str):
        """Close and remove a session.
        
        Args:
            session_id: Session ID to close
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._logger.info(f"Closed session: {session_id}")
    
    def list_sessions(self) -> List[SessionInfo]:
        """List all active sessions.
        
        Returns:
            List[SessionInfo]: List of session information objects
        """
        return [self.get_session_info(sid) for sid in self._sessions.keys()]
    
    def cleanup_inactive_sessions(self, timeout: int = 3600):
        """Clean up sessions that have been inactive for too long.
        
        Args:
            timeout: Inactivity timeout in seconds (default: 1 hour)
        """
        current_time = time.time()
        to_remove = []
        
        for session_id, session in self._sessions.items():
            if current_time - session['last_activity'] > timeout:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            self.close_session(session_id)
            
        if to_remove:
            self._logger.info(f"Cleaned up {len(to_remove)} inactive sessions")
    
    def get_session_count(self) -> int:
        """Get the number of active sessions.
        
        Returns:
            int: Number of active sessions
        """
        return len(self._sessions)
    
    def clear_session_messages(self, session_id: str):
        """Clear all messages from a session while keeping the session active.
        
        Args:
            session_id: Session ID
            
        Raises:
            GeminiSessionError: If session not found
        """
        session = self.get_session(session_id)
        session['messages'] = []
        session['last_activity'] = time.time()
        
        self._logger.info(f"Cleared messages for session {session_id}")
