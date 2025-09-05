#!/usr/bin/env python3
# Author: Jaime Yan
"""
Enhanced Connection Manager for Persistent Sessions
Phase 3 of systematic optimization
"""

import json
import time
import logging
from typing import Dict, Any, Optional, Generator
from threading import Lock

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Enhanced connection manager for persistent SSE sessions
    Handles connection state, recovery, and proper event streaming
    """
    
    def __init__(self):
        self.active_connections: Dict[str, Dict] = {}
        self.connection_lock = Lock()
        logger.info("🔗 Connection Manager initialized")
    
    def register_connection(self, session_id: str, request_handler) -> bool:
        """Register a new connection for a session"""
        with self.connection_lock:
            self.active_connections[session_id] = {
                'handler': request_handler,
                'start_time': time.time(),
                'last_activity': time.time(),
                'event_count': 0,
                'is_active': True
            }
            logger.info(f"🔗 Connection registered for session {session_id}")
            return True
    
    def update_activity(self, session_id: str):
        """Update last activity time for a session"""
        with self.connection_lock:
            if session_id in self.active_connections:
                self.active_connections[session_id]['last_activity'] = time.time()
    
    def increment_event_count(self, session_id: str):
        """Increment event count for a session"""
        with self.connection_lock:
            if session_id in self.active_connections:
                self.active_connections[session_id]['event_count'] += 1
    
    def is_connection_active(self, session_id: str) -> bool:
        """Check if connection is still active"""
        with self.connection_lock:
            if session_id not in self.active_connections:
                return False
            return self.active_connections[session_id]['is_active']
    
    def close_connection(self, session_id: str):
        """Mark connection as closed"""
        with self.connection_lock:
            if session_id in self.active_connections:
                self.active_connections[session_id]['is_active'] = False
                logger.info(f"🔗 Connection closed for session {session_id}")
    
    def cleanup_connection(self, session_id: str):
        """Remove connection from active list"""
        # DIAGNOSTIC: Log call stack to find who's calling cleanup
        import traceback
        call_stack = traceback.format_stack()
        logger.info(f"🔍 DIAGNOSTIC: cleanup_connection called for session {session_id}")
        logger.info(f"🔍 DIAGNOSTIC: Call stack (last 3 frames):")
        for frame in call_stack[-3:]:
            logger.info(f"🔍 DIAGNOSTIC: {frame.strip()}")

        with self.connection_lock:
            if session_id in self.active_connections:
                del self.active_connections[session_id]
                logger.info(f"🧹 Connection cleaned up for session {session_id}")
            else:
                logger.info(f"🔍 DIAGNOSTIC: Session {session_id} not in active connections (already cleaned up?)")
    
    def get_connection_info(self) -> Dict:
        """Get information about active connections"""
        with self.connection_lock:
            current_time = time.time()
            connection_info = {}
            
            for session_id, conn_data in self.active_connections.items():
                connection_info[session_id] = {
                    'duration_seconds': current_time - conn_data['start_time'],
                    'last_activity_seconds_ago': current_time - conn_data['last_activity'],
                    'event_count': conn_data['event_count'],
                    'is_active': conn_data['is_active']
                }
            
            return {
                'total_connections': len(self.active_connections),
                'active_connections': sum(1 for c in self.active_connections.values() if c['is_active']),
                'connections': connection_info
            }

class EnhancedSSEStreamer:
    """
    Enhanced SSE streamer with better error handling and connection management
    """
    
    def __init__(self, request_handler, session_id: str, connection_manager: ConnectionManager):
        self.request_handler = request_handler
        self.session_id = session_id
        self.connection_manager = connection_manager
        self.event_count = 0
        self.start_time = time.time()
        
    def send_event(self, event_type: str, content: Any = None, **kwargs) -> bool:
        """
        Send SSE event with enhanced error handling
        Returns True if successful, False if connection is closed
        """
        try:
            # Check if connection is still active
            if not self.connection_manager.is_connection_active(self.session_id):
                logger.warning(f"⚠️ Connection inactive for session {self.session_id}, skipping event")
                return False
            
            # Check if wfile is closed
            if hasattr(self.request_handler.wfile, 'closed') and self.request_handler.wfile.closed:
                logger.warning(f"⚠️ Connection closed for session {self.session_id}, marking inactive")
                self.connection_manager.close_connection(self.session_id)
                return False
            
            # Prepare event data
            event_data = {
                'type': event_type,
                'session_id': self.session_id,
                'timestamp': time.time()
            }
            
            if content is not None:
                event_data['content'] = content
            
            # Add any additional kwargs
            event_data.update(kwargs)
            
            # Format as SSE
            sse_data = f"data: {json.dumps(event_data)}\n\n"
            
            # Send the event
            self.request_handler.wfile.write(sse_data.encode())
            self.request_handler.wfile.flush()
            
            # Update tracking
            self.event_count += 1
            self.connection_manager.increment_event_count(self.session_id)
            self.connection_manager.update_activity(self.session_id)

            # Track last event type for session_ready handling
            self._last_event_type = event_type

            # ENHANCED: Special tracking for session_ready events
            if event_type == 'session_ready':
                self._session_ready_sent = True
                logger.info(f"🔄 SESSION_READY event tracked for session {self.session_id} - will NOT send end event")

            logger.debug(f"📡 SSE event sent: {event_type} (#{self.event_count}) to session {self.session_id}")
            return True
            
        except (BrokenPipeError, ConnectionResetError, OSError, ValueError) as e:
            logger.warning(f"⚠️ Connection error for session {self.session_id}: {e}")
            self.connection_manager.close_connection(self.session_id)
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error sending SSE event to session {self.session_id}: {e}")
            return False
    
    def stream_handler_events(self, handler, message: str, context: Dict) -> Generator[bool, None, None]:
        """
        Stream events from handler with enhanced connection management
        Yields True for successful events, False when connection closes
        """
        try:
            logger.info(f"🔄 Starting event stream for session {self.session_id}")

            # Send start event
            if not self.send_event('stream_start', f"Processing request for session {self.session_id}"):
                yield False
                return

            # Process handler events
            timeout_seconds = 120
            start_time = time.time()

            for event in handler.process_message(message, context):
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    logger.warning(f"⏱️ Timeout reached for session {self.session_id} after {elapsed:.1f}s")
                    if not self.send_event('timeout', f'Processing timeout after {elapsed:.1f} seconds'):
                        yield False
                        return
                    break
                
                # Send the event
                event_type = event.get('type', 'unknown')
                content = event.get('content', '')
                
                # Send event with all original data
                if not self.send_event(event_type, content, **{k: v for k, v in event.items() if k not in ['type', 'content']}):
                    logger.warning(f"⚠️ Failed to send event {event_type} to session {self.session_id}")
                    yield False
                    return

                yield True

            # CRITICAL FIX: Don't send stream_complete for persistent sessions (it overwrites session_ready)
            total_time = time.time() - start_time

            # Check if this is a persistent session (session_ready was sent)
            if hasattr(self, '_session_ready_sent') and self._session_ready_sent:
                logger.info(f"🔄 PERSISTENT SESSION: Skipping stream_complete event to preserve session_ready state")
                logger.info(f"🔄 PERSISTENT SESSION: Stream completed in {total_time:.1f}s with {self.event_count} events")
            else:
                # Non-persistent session: send normal completion event
                if not self.send_event('stream_complete', f"Stream completed in {total_time:.1f}s with {self.event_count} events"):
                    yield False
                    return

            logger.info(f"✅ Event stream completed for session {self.session_id}: {self.event_count} events in {total_time:.1f}s")
            yield True

        except Exception as e:
            logger.error(f"❌ Error in event stream for session {self.session_id}: {e}")
            self.send_event('stream_error', f"Stream error: {str(e)}")
            yield False

        finally:
            # CRITICAL FIX: Never send 'end' event for persistent sessions (ChatGPT Code Interpreter style)
            # Check multiple indicators for session_ready state
            session_ready_by_type = hasattr(self, '_last_event_type') and self._last_event_type == 'session_ready'
            session_ready_by_flag = hasattr(self, '_session_ready_sent') and self._session_ready_sent

            if session_ready_by_type or session_ready_by_flag:
                logger.info(f"🔄 PERSISTENT SESSION: Session ready detected - NOT sending 'end' event for session {self.session_id}")
                logger.info(f"🔄 PERSISTENT SESSION: Last event type: {getattr(self, '_last_event_type', 'unknown')}")
                logger.info(f"🔄 PERSISTENT SESSION: Session ready flag: {getattr(self, '_session_ready_sent', False)}")
                logger.info(f"🔄 PERSISTENT SESSION: Connection will remain available for follow-up requests")
            else:
                logger.info(f"🔚 NON-PERSISTENT SESSION: Sending 'end' event for session {self.session_id}")
                logger.info(f"🔚 NON-PERSISTENT SESSION: Last event type: {getattr(self, '_last_event_type', 'unknown')}")
                self.send_event('end', "Stream ended")
    
    def get_stream_stats(self) -> Dict:
        """Get statistics about the current stream"""
        return {
            'session_id': self.session_id,
            'event_count': self.event_count,
            'duration_seconds': time.time() - self.start_time,
            'is_active': self.connection_manager.is_connection_active(self.session_id)
        }

# Global connection manager instance
connection_manager = ConnectionManager()

def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance"""
    return connection_manager
