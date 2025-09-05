#!/usr/bin/env python3
# Author: Jaime Yan
"""
Simple Session Pool Manager for Persistent R Handler Sessions
Phase 2 of systematic optimization
"""

import time
import logging
from typing import Dict, Optional
from app.handlers.r_reference_handler import RReferenceHandler
from app.api.unified_llm_client import UnifiedLLMClient

logger = logging.getLogger(__name__)

class SessionPool:
    """
    Simple session pool for persistent R handlers
    Manages reusable R handler instances across multiple requests
    """
    
    def __init__(self, max_sessions=10, session_timeout=3600):
        self.sessions: Dict[str, Dict] = {}
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout  # 1 hour default
        logger.info(f"🏊 Session Pool initialized (max: {max_sessions}, timeout: {session_timeout}s)")
    
    def get_or_create_session(self, session_id: str, llm_client: UnifiedLLMClient, session_context: Dict) -> RReferenceHandler:
        """
        Get existing session or create new one
        Simple and efficient approach
        """
        current_time = time.time()
        
        # Check if session exists and is still valid
        if session_id in self.sessions:
            session_data = self.sessions[session_id]
            logger.info(f"🔍 SESSION POOL: Found existing session {session_id}")
            logger.info(f"🔍 SESSION POOL: Session status: {session_data.get('status', 'unknown')}")
            logger.info(f"🔍 SESSION POOL: Last used: {current_time - session_data['last_used']:.1f}s ago")
            logger.info(f"🔍 SESSION POOL: Request count: {session_data.get('request_count', 0)}")

            # Check if session has expired
            if current_time - session_data['last_used'] > self.session_timeout:
                logger.info(f"🕐 Session {session_id} expired, creating new one")
                self._cleanup_session(session_id)
            else:
                # Update last used time and return existing handler
                session_data['last_used'] = current_time
                logger.info(f"♻️ REUSING EXISTING SESSION {session_id} - Handler preserved")
                return session_data['handler']
        
        # Create new session
        logger.info(f"🆕 CREATING NEW PERSISTENT SESSION {session_id}")
        logger.info(f"🔍 SESSION POOL: Current sessions in pool: {list(self.sessions.keys())}")
        logger.info(f"🔍 SESSION POOL: Total sessions: {len(self.sessions)}/{self.max_sessions}")

        # Clean up old sessions if we're at the limit
        if len(self.sessions) >= self.max_sessions:
            logger.info(f"🧹 SESSION POOL: At session limit, cleaning up oldest session")
            self._cleanup_oldest_session()
        
        # Create new R handler in persistent mode
        handler = RReferenceHandler(
            llm_client=llm_client,
            session_context=session_context,
            persistent_mode=True  # Enable persistent mode
        )
        
        # Store in pool with enhanced state management
        self.sessions[session_id] = {
            'handler': handler,
            'created': current_time,
            'last_used': current_time,
            'request_count': 0,
            'status': 'ready',  # ready, busy, error
            'state_data': {},   # For session state persistence
            'connection_count': 0
        }
        
        logger.info(f"✅ Session {session_id} created and stored in pool")
        return handler
    
    def reset_session_for_new_task(self, session_id: str):
        """Reset session state for new task while keeping R environment"""
        if session_id in self.sessions:
            handler = self.sessions[session_id]['handler']
            handler.reset_for_new_task()
            self.sessions[session_id]['last_used'] = time.time()
            logger.info(f"🔄 Session {session_id} reset for new task")
        else:
            logger.warning(f"⚠️ Attempted to reset non-existent session {session_id}")

    def increment_request_count(self, session_id: str):
        """Track request count for session"""
        if session_id in self.sessions:
            self.sessions[session_id]['request_count'] += 1
            self.sessions[session_id]['last_used'] = time.time()

    def save_session_state(self, session_id: str, state_data: Dict):
        """Save session state for recovery"""
        if session_id in self.sessions:
            if 'state_data' not in self.sessions[session_id]:
                self.sessions[session_id]['state_data'] = {}
            self.sessions[session_id]['state_data'].update(state_data)
            logger.info(f"💾 Session state saved for {session_id}")

    def get_session_state(self, session_id: str) -> Dict:
        """Get saved session state"""
        if session_id in self.sessions:
            return self.sessions[session_id].get('state_data', {})
        return {}

    def mark_session_ready(self, session_id: str):
        """Mark session as ready for new requests"""
        if session_id in self.sessions:
            self.sessions[session_id]['status'] = 'ready'
            self.sessions[session_id]['last_used'] = time.time()
            logger.info(f"✅ Session {session_id} marked as ready")

    def mark_session_busy(self, session_id: str):
        """Mark session as busy processing request"""
        if session_id in self.sessions:
            self.sessions[session_id]['status'] = 'busy'
            self.sessions[session_id]['last_used'] = time.time()
            logger.info(f"⏳ Session {session_id} marked as busy")

    def is_session_ready(self, session_id: str) -> bool:
        """Check if session is ready for new requests"""
        if session_id in self.sessions:
            return self.sessions[session_id].get('status', 'ready') == 'ready'
        return False
    
    def _cleanup_session(self, session_id: str):
        """Clean up a specific session"""
        if session_id in self.sessions:
            try:
                handler = self.sessions[session_id]['handler']
                # FIXED: Do NOT destroy R kernel - let it be garbage collected naturally
                # The R kernel should persist until the handler is completely destroyed
                # Only remove from pool tracking
                del self.sessions[session_id]
                logger.info(f"🧹 Session {session_id} removed from pool (R environment preserved until garbage collection)")
            except Exception as e:
                logger.warning(f"⚠️ Error cleaning up session {session_id}: {e}")
                # Force remove from pool even if cleanup failed
                if session_id in self.sessions:
                    del self.sessions[session_id]
    
    def _cleanup_oldest_session(self):
        """Clean up the oldest session to make room for new one"""
        if not self.sessions:
            return
        
        oldest_session_id = min(self.sessions.keys(), 
                               key=lambda sid: self.sessions[sid]['last_used'])
        logger.info(f"🧹 Cleaning up oldest session {oldest_session_id} to make room")
        self._cleanup_session(oldest_session_id)
    
    def cleanup_expired_sessions(self):
        """Clean up all expired sessions"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session_data in self.sessions.items():
            if current_time - session_data['last_used'] > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            logger.info(f"🕐 Cleaning up expired session {session_id}")
            self._cleanup_session(session_id)
        
        if expired_sessions:
            logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_session_info(self) -> Dict:
        """Get information about current sessions"""
        current_time = time.time()
        session_info = {}
        
        for session_id, session_data in self.sessions.items():
            session_info[session_id] = {
                'age_seconds': current_time - session_data['created'],
                'last_used_seconds_ago': current_time - session_data['last_used'],
                'request_count': session_data['request_count'],
                'is_expired': (current_time - session_data['last_used']) > self.session_timeout
            }
        
        return {
            'total_sessions': len(self.sessions),
            'max_sessions': self.max_sessions,
            'session_timeout': self.session_timeout,
            'sessions': session_info
        }

# Global session pool instance
session_pool = SessionPool()

def get_session_pool() -> SessionPool:
    """Get the global session pool instance"""
    return session_pool
