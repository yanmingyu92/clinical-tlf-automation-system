#!/usr/bin/env python3
# Author: Jaime Yan
"""
Session-Aware Result Manager for Persistent Sessions
Handles result display and file management across persistent sessions
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SessionResultManager:
    """
    Manages results and files for persistent sessions
    Ensures proper file paths and result tracking across session reuse
    """
    
    def __init__(self):
        self.session_results: Dict[str, Dict] = {}
        self.base_output_dir = "outputs"
        logger.info("📊 Session Result Manager initialized")
    
    def register_session_result(self, session_id: str, result_data: Dict[str, Any]):
        """Register execution results for a session"""
        if session_id not in self.session_results:
            self.session_results[session_id] = {
                'executions': [],
                'total_files': 0,
                'last_updated': time.time(),
                'session_directory': f"{self.base_output_dir}/execution_{session_id}"
            }
        
        # Add execution result
        execution_result = {
            'timestamp': time.time(),
            'execution_count': len(self.session_results[session_id]['executions']) + 1,
            'files_generated': result_data.get('files_generated', []),
            'output_directory': result_data.get('output_directory', ''),
            'success': result_data.get('success', False),
            'output': result_data.get('output', ''),
            'error': result_data.get('error', '')
        }
        
        self.session_results[session_id]['executions'].append(execution_result)
        self.session_results[session_id]['total_files'] += len(execution_result['files_generated'])
        self.session_results[session_id]['last_updated'] = time.time()
        
        logger.info(f"📊 Registered result for session {session_id}: {len(execution_result['files_generated'])} files")
        return execution_result
    
    def get_session_results(self, session_id: str) -> Dict[str, Any]:
        """Get all results for a session"""
        if session_id not in self.session_results:
            return {
                'session_id': session_id,
                'executions': [],
                'total_files': 0,
                'session_directory': f"{self.base_output_dir}/execution_{session_id}"
            }
        
        return {
            'session_id': session_id,
            **self.session_results[session_id]
        }
    
    def get_latest_execution_result(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest execution result for a session"""
        if session_id not in self.session_results or not self.session_results[session_id]['executions']:
            return None
        
        return self.session_results[session_id]['executions'][-1]
    
    def get_all_session_files(self, session_id: str) -> List[str]:
        """Get all files generated across all executions in a session"""
        if session_id not in self.session_results:
            return []
        
        all_files = []
        for execution in self.session_results[session_id]['executions']:
            all_files.extend(execution['files_generated'])
        
        return all_files
    
    def get_session_file_paths(self, session_id: str) -> Dict[str, str]:
        """Get file paths for session-aware file loading with nested directory handling"""
        session_dir = f"{self.base_output_dir}/execution_{session_id}"

        # FIXED: Handle nested directory issue
        # Check for nested outputs directories that can occur due to R setwd() issues
        nested_session_dir = f"{session_dir}/outputs/execution_{session_id}"

        # Create multiple path strategies for file loading
        path_strategies = {
            'primary': session_dir,
            'nested_fix': nested_session_dir,  # Handle nested outputs issue
            'nested_any': f"{session_dir}/outputs",  # Any nested outputs
            'fallback_step4': f"{self.base_output_dir}/step4_r",
            'fallback_outputs': self.base_output_dir,
            'cache': f"cache/temp_{session_id}"
        }

        return path_strategies
    
    def prepare_ui_result_data(self, session_id: str, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare result data for UI display with session awareness"""
        session_data = self.get_session_results(session_id)
        
        # Enhanced result data for UI
        ui_data = {
            'session_id': session_id,
            'execution_id': session_id,  # For backward compatibility
            'execution_count': execution_result.get('execution_count', 1),
            'total_session_executions': len(session_data['executions']),
            'files_generated': execution_result.get('files_generated', []),
            'output_directory': execution_result.get('output_directory', session_data['session_directory']),
            'session_directory': session_data['session_directory'],
            'success': execution_result.get('success', False),
            'output': execution_result.get('output', ''),
            'error': execution_result.get('error', ''),
            'timestamp': execution_result.get('timestamp', time.time()),
            'total_session_files': session_data['total_files'],
            'all_session_files': self.get_all_session_files(session_id),
            'file_paths': self.get_session_file_paths(session_id)
        }
        
        logger.info(f"📊 Prepared UI data for session {session_id}: {len(ui_data['files_generated'])} new files, {ui_data['total_session_files']} total")
        return ui_data
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old session results"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        sessions_to_remove = []
        for session_id, session_data in self.session_results.items():
            if current_time - session_data['last_updated'] > max_age_seconds:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.session_results[session_id]
            logger.info(f"🧹 Cleaned up old session results: {session_id}")
        
        if sessions_to_remove:
            logger.info(f"🧹 Cleaned up {len(sessions_to_remove)} old session results")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of all sessions"""
        return {
            'total_sessions': len(self.session_results),
            'total_executions': sum(len(s['executions']) for s in self.session_results.values()),
            'total_files': sum(s['total_files'] for s in self.session_results.values()),
            'sessions': {
                session_id: {
                    'executions': len(data['executions']),
                    'files': data['total_files'],
                    'last_updated': data['last_updated']
                }
                for session_id, data in self.session_results.items()
            }
        }

class SessionAwareFileLoader:
    """
    Enhanced file loader that works with persistent sessions
    """
    
    def __init__(self, result_manager: SessionResultManager):
        self.result_manager = result_manager
    
    def get_file_content(self, session_id: str, filename: str) -> Optional[str]:
        """Load file content using session-aware path strategies with nested directory search"""
        path_strategies = self.result_manager.get_session_file_paths(session_id)

        # Try each path strategy
        for strategy_name, base_path in path_strategies.items():
            file_path = os.path.join(base_path, filename)

            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    logger.info(f"📄 Loaded {filename} from {strategy_name}: {file_path}")
                    return content
            except Exception as e:
                logger.debug(f"Failed to load {filename} from {file_path}: {e}")
                continue

        # ENHANCED: Search for files in nested directories if not found in standard paths
        session_base = f"{self.result_manager.base_output_dir}/execution_{session_id}"
        if os.path.exists(session_base):
            for root, dirs, files in os.walk(session_base):
                if filename in files:
                    nested_file_path = os.path.join(root, filename)
                    try:
                        with open(nested_file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        logger.info(f"📄 Found {filename} in nested directory: {nested_file_path}")
                        return content
                    except Exception as e:
                        logger.debug(f"Failed to load {filename} from nested path {nested_file_path}: {e}")
                        continue

        # SUPER ENHANCED: Search across ALL execution directories for the file (handles session ID mismatches)
        outputs_base = self.result_manager.base_output_dir
        if os.path.exists(outputs_base):
            logger.info(f"🔍 Searching across all execution directories for {filename}")
            for execution_dir in os.listdir(outputs_base):
                if execution_dir.startswith('execution_'):
                    execution_path = os.path.join(outputs_base, execution_dir)
                    if os.path.isdir(execution_path):
                        for root, dirs, files in os.walk(execution_path):
                            if filename in files:
                                cross_session_path = os.path.join(root, filename)
                                try:
                                    with open(cross_session_path, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                    logger.info(f"📄 Found {filename} across sessions: {cross_session_path}")
                                    return content
                                except Exception as e:
                                    logger.debug(f"Failed to load {filename} from cross-session path {cross_session_path}: {e}")
                                    continue

        logger.warning(f"⚠️ Could not load {filename} for session {session_id} (searched all directories)")
        return None
    
    def get_file_url(self, session_id: str, filename: str) -> str:
        """Get URL for file access with session awareness"""
        # Return URL that includes session context
        return f"/get_file_content?session_id={session_id}&file={filename}"

# Global instances
session_result_manager = SessionResultManager()
session_file_loader = SessionAwareFileLoader(session_result_manager)

def get_session_result_manager() -> SessionResultManager:
    """Get the global session result manager"""
    return session_result_manager

def get_session_file_loader() -> SessionAwareFileLoader:
    """Get the global session file loader"""
    return session_file_loader
