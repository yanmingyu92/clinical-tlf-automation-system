"""
R Reference Handler - Based on archive/src architecture
Adapted from the proven reference project for R clinical trial analysis
"""
# Author: Jaime Yan

import json
import logging
import re
import time
import os
from datetime import datetime
from typing import Dict, Any, Generator, List
from app.api.unified_llm_client import UnifiedLLMClient

logger = logging.getLogger(__name__)

# R function definition based on reference project
R_FUNCTIONS = [
    {
        "type": "function",
        "function": {
            "name": "execute_r_code",
            "description": "Execute R code for clinical trial data analysis and retrieve the output. The code is executed using the enhanced R interpreter with session isolation. Use this for data analysis, statistical computations, and generating clinical reports.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The R code to execute"
                    }
                },
                "required": ["code"],
                "additionalProperties": False
            }
        }
    },
]

# R-focused system message based on reference project
R_SYSTEM_MESSAGE = '''You are an expert clinical trial data analyst and R programming specialist.

IMPORTANT: When users ask for R code execution, data analysis, or statistical computations, you MUST use the execute_r_code function to run the actual R code.

For simple greetings or general questions, respond conversationally without executing code.
For data analysis requests, debugging R code, or any R programming tasks, use the execute_r_code function.

Always provide helpful, clear responses to user questions.'''


def delete_color_control_char(string):
    """Remove ANSI color control characters from output"""
    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    return ansi_escape.sub('', string)


class REnhancedInterpreter:
    """R Enhanced Interpreter wrapper for unified execution"""

    def __init__(self, work_dir, execution_id='default'):
        self.work_dir = work_dir
        self.execution_id = execution_id
        self.interrupt_signal = False
        self._create_work_dir()

        # Use Enhanced Simple R Executor with workspace persistence for session continuity
        from app.handlers.simple_r_executor import SimpleRExecutor

        # Create enhanced R executor with workspace persistence
        self.r_interpreter = SimpleRExecutor(work_dir, execution_id)
        self.r_interpreter.enable_workspace_persistence = True  # Enable session continuity

        logger.info(f"📁 Enhanced Simple R Executor with workspace persistence initialized: {work_dir}")

        self.available_functions = {
            'execute_r_code': self.execute_r_code,
        }

    def _create_work_dir(self):
        """Create working directory if it doesn't exist"""
        import os
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir, exist_ok=True)
            logger.info(f"📁 Created working directory: {self.work_dir}")

    def execute_r_code_(self, code):
        """Execute R code and return summary for LLM (internal method)"""
        try:
            # Execute R code using Enhanced SimpleRExecutor with workspace persistence
            result = self.r_interpreter.execute_r_code(code)

            if result.get('success', False):
                # Return summary for LLM, not raw output
                return result.get('summary', '✅ R code executed successfully')
            else:
                return f"Error: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Execution error: {str(e)}"

    def execute_r_code(self, code):
        """Execute R code and return summary for LLM, raw output for UI"""
        try:
            # Execute R code using Enhanced SimpleRExecutor with workspace persistence
            result = self.r_interpreter.execute_r_code(code)

            if result.get('success', False):
                # CRITICAL: Separate LLM summary from UI display
                llm_summary = result.get('summary', '✅ R code executed successfully')  # Safe summary for LLM
                raw_output = result.get('output', '')  # Raw output for UI display

                # Return: (LLM_summary, UI_raw_output)
                return llm_summary, raw_output
            else:
                # For errors, use summary for LLM, raw error for UI
                llm_summary = result.get('summary', '❌ R execution failed')
                raw_output = result.get('output', f"❌ R execution failed: {result.get('error', 'Unknown error')}")
                return llm_summary, raw_output

        except Exception as e:
            error_msg = f"❌ R execution error: {str(e)}"
            return error_msg, error_msg

    def _get_work_dir_files(self):
        """Get list of files in the session directory"""
        import os
        try:
            # Use the actual session directory from EnhancedRInterpreter
            session_dir = self.r_interpreter.session_dir
            if os.path.exists(session_dir):
                files = [f for f in os.listdir(session_dir) if os.path.isfile(os.path.join(session_dir, f))]
                logger.info(f"📁 Found {len(files)} files in session directory {session_dir}: {files}")
                return files
            return []
        except Exception as e:
            logger.error(f"Error getting files from session directory: {e}")
            return []

    def interrupt_kernel(self):
        """Interrupt the execution"""
        self.interrupt_signal = True
        # Note: EnhancedRInterpreter handles interruption internally

    def restart_kernel(self):
        """Restart the R interpreter"""
        # Reinitialize the interpreter
        from r_integration.enhanced_r_interpreter import EnhancedRInterpreter
        session_context = {
            'execution_id': self.execution_id,
            'session_directory': self.work_dir,
            'work_dir': self.work_dir
        }
        self.r_interpreter = EnhancedRInterpreter(session_context=session_context)
        self._create_work_dir()

    def cleanup(self):
        """Cleanup interpreter resources"""
        # EnhancedRInterpreter handles cleanup automatically
        pass


class RReferenceHandler:
    """
    R Reference Handler based on archive/src/bot_backend.py
    Handles R code execution with LLM decision making
    """
    
    def __init__(self, llm_client: UnifiedLLMClient = None, session_context=None, persistent_mode=False):
        if llm_client is None:
            # Create new instance only if no client provided
            self.llm_client = UnifiedLLMClient(preferred_provider="deepseek")
            logger.info("🔍 Step 4 R Handler: Created new LLM client with DeepSeek preference")
        else:
            # CRITICAL FIX: Use provided client AS-IS, respecting user's provider selection
            # Don't override the user's choice - they selected it for a reason
            self.llm_client = llm_client
            current_provider = self.llm_client.get_current_provider()
            logger.info(f"🔍 Step 4 R Handler: Using shared LLM client with user-selected provider: {current_provider}")

            # Verify the provider supports function calling
            available_providers = self.llm_client.get_available_providers()
            if not available_providers:
                raise RuntimeError("No LLM providers available")

            if current_provider not in ["claude", "deepseek"]:
                logger.warning(f"⚠️ Provider {current_provider} may have limited function calling support")

        # Session-aware setup for robust file handling
        if session_context:
            self.execution_id = session_context.get('execution_id', 'default')
            self.work_dir = session_context.get('work_dir', './outputs/step4_r')
            self.session_directory = session_context.get('session_directory', self.work_dir)
            self.persistent_mode = session_context.get('persistent_mode', persistent_mode)
        else:
            self.execution_id = 'default'
            self.work_dir = './outputs/step4_r'
            self.session_directory = self.work_dir
            self.persistent_mode = persistent_mode

        # Create session directory
        os.makedirs(self.work_dir, exist_ok=True)

        self.r_kernel = None

        # Reference project style attributes
        self.finish_reason = 'new_input'
        self.content = ""
        self.function_name = ""
        self.code_str = ""
        self.display_code_block = ""
        self.stop_generating = False

        # Log LLM client status
        logger.info(f"🔍 R Reference Handler initialized")
        logger.info(f"🔍 LLM Client available providers: {self.llm_client.get_available_providers()}")
        logger.info(f"🔍 LLM Client current provider: {self.llm_client.get_current_provider()}")
        logger.info(f"📁 Session ID: {self.execution_id}")
        logger.info(f"📂 Work directory: {self.work_dir}")

        # Session-aware system prompt for robust file handling
        self.system_prompt = self._create_session_aware_system_message()

        # Session file paths
        self.conversation_file = os.path.join(self.work_dir, f"conversation_{self.execution_id}.json")
        self.modification_file = os.path.join(self.work_dir, f"modifications_{self.execution_id}.json")

        # Load existing conversation history or initialize with system prompt
        self._load_conversation_history()

        # Load existing modification history or initialize empty
        self._load_modification_history()

    def _create_session_aware_system_message(self):
        """Create concise session-aware system message (optimized for token usage)"""
        # Convert to absolute path for clarity and ensure no nested outputs
        abs_work_dir = os.path.abspath(self.work_dir).replace(os.sep, "/")

        # FIXED: Ensure working directory doesn't create nested outputs
        # Remove any trailing /outputs to prevent nested directory issues
        if abs_work_dir.endswith('/outputs'):
            abs_work_dir = abs_work_dir[:-8]  # Remove '/outputs'

        return f'''Expert R analyst. Session: {self.execution_id}

CRITICAL: Set working directory ONCE at start: setwd("{abs_work_dir}")
Save all files directly in this directory (no subdirectories).
Use execute_r_code function for analysis.

SINGLE-TASK COMPLETION MODE:
- Execute ONE task per user request, then WAIT for next user input
- When you see R code execution errors, analyze and provide ONE corrected version
- DO NOT automatically re-execute - let the user decide whether to run the fixed code
- CONTEXT USAGE: You receive dataset_path, dataset_info, and other context - USE THEM!
- For missing data files: Use context.dataset_path or try: "data/adam/", "../data/adam/", "../../data/adam/"
- Fix session ID mismatches using the current session ID: {self.execution_id}
- Fix working directory errors by using the correct session directory path
- Complete the task in ONE iteration, then STOP and wait for user input
- Only ask questions if absolutely no solution can be determined from context

CODE MODIFICATION INSTRUCTIONS:
- When user requests code changes, ALWAYS provide the COMPLETE updated code
- Include ALL original functionality plus the requested changes
- Provide executable code that user can run directly
- Do NOT provide partial code or just the changes

ERROR HANDLING PROTOCOL:
1. Analyze the error log automatically
2. Fix obvious issues (paths, session IDs, missing directories)
3. Provide ONE corrected version of the code
4. Explain what was fixed and why
5. STOP and wait for user to decide next action

SPECIFIC ERROR FIXES:
- "cannot change working directory" → Use setwd() with correct session directory
- "does not exist in current working directory" → Use dataset_path from context
- Session ID mismatch → Replace old session ID with current: {self.execution_id}
- Missing data files → Try relative paths from context.dataset_path

IMPORTANT:
- Do NOT create additional 'outputs' subdirectories. Save files directly in the session directory.
- Complete ONE task per request, then WAIT for next user input
- Do NOT automatically re-execute code - provide fixes and let user decide

CODE INTERPRETER MODE: You have access to the user's R code through ACTIVE CODE CONTEXT. When users ask about code analysis, modifications, or debugging, reference the provided code. Always acknowledge when you can see their code.'''

    def test_llm_connection(self):
        """Test if LLM is responding at all"""
        logger.info("🧪 Testing LLM connection...")
        try:
            # Simple test message with timeout
            test_messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'hello' in one word."}
            ]

            logger.info("🧪 Making simple LLM call without functions...")
            response = self.llm_client.chat_completion_stream(
                messages=test_messages,
                temperature=0.1
            )

            logger.info("🧪 LLM call returned, testing first chunk...")
            chunk_count = 0
            timeout_start = time.time()
            for _ in response:
                chunk_count += 1
                logger.info(f"🧪 Test chunk {chunk_count} received")
                if chunk_count >= 2:  # Just test first 2 chunks
                    break
                # Add timeout to prevent hanging
                if time.time() - timeout_start > 3:  # 3 second timeout
                    logger.warning("🧪 Test timeout - assuming connection is good")
                    break

            logger.info(f"✅ LLM connection test passed - received {chunk_count} chunks")
            return True

        except Exception as e:
            logger.error(f"❌ LLM connection test failed: {e}")
            return False

    def reset_for_new_request(self):
        """Reset handler state for a new request - prevents state pollution"""
        logger.info("🔄 Resetting handler state for new request")

        # FIXED: In persistent mode, do NOT destroy R kernel
        if not self.persistent_mode:
            # Only clean up R kernel in non-persistent mode
            if self.r_kernel:
                logger.info("🧹 Non-persistent mode: Cleaning up R kernel from previous request")
                try:
                    self.r_kernel.cleanup()
                except Exception as e:
                    logger.warning(f"⚠️ R kernel cleanup warning: {e}")
                self.r_kernel = None
                logger.info("✅ R kernel cleaned up")
        else:
            logger.info("🔄 Persistent mode: Preserving R kernel for continuity")

        # ENHANCED: History is already loaded in __init__, no need to reload
        # Just ensure we don't reset the conversation history
        logger.info(f"📚 Preserving conversation history: {len(self.conversation_history)} messages")
        logger.info(f"📝 Preserving modification history: {len(self.modification_history)} modifications")

        # Reset finish reason
        self.finish_reason = 'new_input'

        # Reset other state variables
        self.content = ""
        self.function_name = ""
        self.code_str = ""
        self.display_code_block = ""
        self.stop_generating = False

        logger.info(f"✅ Handler state reset - conversation length: {len(self.conversation_history)}")

    def _load_conversation_history(self):
        """Load conversation history from session file"""
        try:
            if os.path.exists(self.conversation_file):
                with open(self.conversation_file, 'r', encoding='utf-8') as f:
                    saved_history = json.load(f)
                    # Validate the loaded history
                    if isinstance(saved_history, list) and len(saved_history) > 0:
                        # Ensure system prompt is still first
                        if saved_history[0].get('role') == 'system':
                            self.conversation_history = saved_history
                            logger.info(f"📚 Loaded conversation history: {len(saved_history)} messages")
                        else:
                            # Add system prompt if missing
                            self.conversation_history = [
                                {"role": "system", "content": self.system_prompt}
                            ] + saved_history
                            logger.info(f"📚 Loaded conversation history with system prompt added: {len(self.conversation_history)} messages")
                    else:
                        logger.warning("📚 Invalid conversation history format, using default")
                        self.conversation_history = [
                            {"role": "system", "content": self.system_prompt}
                        ]
            else:
                logger.info("📚 No existing conversation history, starting fresh")
                self.conversation_history = [
                    {"role": "system", "content": self.system_prompt}
                ]
        except Exception as e:
            logger.error(f"❌ Error loading conversation history: {e}")
            self.conversation_history = [
                {"role": "system", "content": self.system_prompt}
            ]

    def _load_modification_history(self):
        """Load modification history from session file"""
        try:
            if os.path.exists(self.modification_file):
                with open(self.modification_file, 'r', encoding='utf-8') as f:
                    self.modification_history = json.load(f)
                    logger.info(f"📚 Loaded modification history: {len(self.modification_history)} modifications")
            else:
                self.modification_history = []
                logger.info("📚 No existing modification history, starting fresh")
        except Exception as e:
            logger.error(f"❌ Error loading modification history: {e}")
            self.modification_history = []

    def _save_conversation_history(self):
        """Save conversation history to session file"""
        try:
            os.makedirs(os.path.dirname(self.conversation_file), exist_ok=True)
            with open(self.conversation_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Saved conversation history: {len(self.conversation_history)} messages")
        except Exception as e:
            logger.error(f"❌ Error saving conversation history: {e}")

    def clear_conversation_history(self):
        """Clear conversation history and start fresh (useful for testing)"""
        try:
            # Reset to just system prompt
            self.conversation_history = [
                {"role": "system", "content": self.system_prompt}
            ]

            # Clear the saved file
            if os.path.exists(self.conversation_file):
                os.remove(self.conversation_file)

            # Reset other state
            self.modification_history = []
            self.finish_reason = 'new_input'

            logger.info("🧹 Conversation history cleared, starting fresh")

        except Exception as e:
            logger.error(f"❌ Error clearing conversation history: {e}")

    def _save_modification_history(self):
        """Save modification history to session file"""
        try:
            os.makedirs(os.path.dirname(self.modification_file), exist_ok=True)
            with open(self.modification_file, 'w', encoding='utf-8') as f:
                json.dump(self.modification_history, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Saved modification history: {len(self.modification_history)} modifications")
        except Exception as e:
            logger.error(f"❌ Error saving modification history: {e}")

    def _track_code_modification(self, original_code: str, modified_code: str, request: str, method: str = "ai_interactive"):
        """Track code modifications for consistency with agent approach"""
        modification_record = {
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "request": request,
            "original_code_length": len(original_code) if original_code else 0,
            "modified_code_length": len(modified_code) if modified_code else 0,
            "original_code_hash": hash(original_code) if original_code else None,
            "modified_code_hash": hash(modified_code) if modified_code else None,
            "changes_detected": original_code != modified_code if original_code and modified_code else True
        }

        self.modification_history.append(modification_record)
        self._save_modification_history()
        logger.info(f"📝 Tracked code modification: {method} - {request[:50]}...")

    def add_user_message(self, message: str):
        """Add user message to conversation"""
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        self.finish_reason = 'new_input'
        # Save conversation after adding user message
        self._save_conversation_history()

    def _detect_llm_completion(self, assistant_message: str) -> bool:
        """
        Detect if LLM indicates task completion based on message content
        Inspired by Open Interpreter and ChatGPT Code Interpreter patterns
        Enhanced with smart stopping logic
        """
        if not assistant_message:
            return False

        message_lower = assistant_message.lower().strip()

        # Strong completion indicators (high confidence)
        strong_completion_phrases = [
            "task completed",
            "analysis complete",
            "implementation complete",
            "code is ready",
            "finished creating",
            "successfully created",
            "plot has been generated",
            "analysis is finished",
            "that completes",
            "this completes the"
        ]

        # Moderate completion indicators (medium confidence)
        moderate_completion_phrases = [
            "finished",
            "done",
            "that's it",
            "hope this helps",
            "let me know if you need",
            "is there anything else",
            "anything else i can help",
            "need any modifications",
            "would you like me to",
            "if you need further"
        ]

        # Check for strong completion phrases (immediate stop)
        for phrase in strong_completion_phrases:
            if phrase in message_lower:
                logger.info(f"🎯 Strong completion detected: '{phrase}' found in response")
                return True

        # Check for moderate completion phrases (stop if message is substantial)
        if len(assistant_message) > 50:  # Lowered threshold for better detection
            for phrase in moderate_completion_phrases:
                if phrase in message_lower:
                    logger.info(f"🎯 Moderate completion detected: '{phrase}' found in substantial response")
                    return True

        # Check if message ends with question asking for more work
        question_endings = [
            "?",
            "need anything else",
            "further assistance",
            "more help",
            "other questions",
            "additional analysis",
            "modify anything"
        ]

        for ending in question_endings:
            if message_lower.endswith(ending) or ending in message_lower[-100:]:
                logger.info(f"🎯 Question-based completion detected: '{ending}' found")
                return True

        return False

    def _validate_function_execution_readiness(self, assistant_message: str, function_calls: List[dict]) -> bool:
        """
        Validate if LLM response is ready for function execution
        More lenient validation to allow proper function execution
        """
        if not assistant_message or not assistant_message.strip():
            logger.warning("❌ No assistant message provided")
            return False

        message = assistant_message.strip()

        # Basic length check - very short responses might be incomplete
        if len(message) < 10:
            logger.warning(f"❌ Assistant message too short ({len(message)} chars): '{message}'")
            return False

        # Check for obviously incomplete responses (ends with incomplete phrases)
        obviously_incomplete = [
            "I'll help you",
            "I'll add code to",
            "Let me help",
            "I will help"
        ]

        # Only reject if message ONLY contains these phrases and nothing else
        for indicator in obviously_incomplete:
            if message.strip() == indicator or message.strip() == indicator + ":":
                logger.warning(f"❌ Message is only incomplete phrase: '{indicator}'")
                return False

        # If we have function calls, that's a good sign the LLM intended to execute
        if function_calls:
            logger.info("✅ Function calls present, allowing execution")
            return True

        logger.info("✅ Assistant message validation passed")
        return True

    def _detect_repetitive_behavior(self, iteration: int) -> bool:
        """
        Detect if LLM is stuck in repetitive behavior
        Inspired by TaskWeaver's self-reflection capabilities
        """
        if iteration < 3:
            return False

        # Check if we've had too many function calls without substantial progress
        recent_messages = self.conversation_history[-6:] if len(self.conversation_history) >= 6 else self.conversation_history

        function_calls = 0
        assistant_responses = 0

        for msg in recent_messages:
            if msg.get('role') == 'function':  # FIXED: Look for function messages, not user messages
                function_calls += 1
            elif msg.get('role') == 'assistant':
                assistant_responses += 1

        # If we have many function calls but few assistant responses, might be stuck
        if function_calls >= 3 and assistant_responses <= 1:
            logger.warning(f"🔄 Repetitive behavior detected: {function_calls} function calls, {assistant_responses} responses")
            return True

        # CRITICAL FIX: More aggressive stopping to prevent loops
        if function_calls >= 2:
            logger.warning(f"🔄 Multiple function calls detected ({function_calls}) - stopping to prevent loops")
            return True

        return False

    def _limit_conversation_history(self, messages: List[Dict], max_messages: int = 20) -> List[Dict]:
        """
        Simple conversation history limiting (no complex truncation needed with summary approach)
        Keep system prompt + recent messages
        """
        if len(messages) <= max_messages:
            return messages

        # Keep system prompt + recent messages
        system_prompt = messages[0] if messages and messages[0].get('role') == 'system' else None
        recent_messages = messages[-(max_messages-1):] if system_prompt else messages[-max_messages:]

        if system_prompt:
            return [system_prompt] + recent_messages
        else:
            return recent_messages

    def _should_continue_session(self, iteration: int, assistant_message: str = "") -> bool:
        """
        Intelligent decision on whether to continue the session
        Combines multiple factors like ChatGPT Code Interpreter
        Enhanced with persistent mode support
        """
        # CRITICAL FIX: In persistent mode, stop after completing the task but keep session alive
        if self.persistent_mode:
            logger.info("🔄 Persistent mode: Using single-task completion logic")

            # Stop after first iteration to prevent loops, but session stays alive
            if iteration >= 1:
                logger.info("🛑 Persistent mode: Task completed, stopping iteration loop (session stays alive)")
                return False

            # Only continue if we haven't completed the first iteration yet
            logger.info("🔄 Persistent mode: Starting first iteration")
            return True

        # Original logic for non-persistent mode
        # Check basic iteration limit
        if iteration >= 15:
            logger.info("🛑 Stopping: Maximum iterations reached")
            return False

        # Check for LLM completion signals
        if assistant_message and self._detect_llm_completion(assistant_message):
            logger.info("🛑 Stopping: LLM indicated completion")
            return False

        # Check for repetitive behavior
        if self._detect_repetitive_behavior(iteration):
            logger.info("🛑 Stopping: Repetitive behavior detected")
            return False

        # Check if conversation is getting too long (token management)
        # Be more lenient for complex tasks - only stop if really long
        if len(self.conversation_history) > 40:
            logger.warning("⚠️ Conversation getting very long, considering completion")
            # If conversation is very long AND we have some content, be more aggressive about stopping
            if assistant_message and len(assistant_message) > 50:
                logger.info("🛑 Stopping: Very long conversation with substantial response")
                return False

        # Simple stopping criteria: stop after successful function execution
        if iteration >= 2 and assistant_message and len(assistant_message) > 30:
            logger.info("🛑 Stopping: Response after function execution")
            return False

        # Stop after any successful function execution to prevent loops
        recent_messages = self.conversation_history[-3:] if len(self.conversation_history) >= 3 else self.conversation_history
        has_function_success = any(msg.get('role') == 'function' and '✅' in msg.get('content', '')
                                 for msg in recent_messages)
        if has_function_success and assistant_message:
            logger.info("🛑 Stopping: Function executed successfully")
            return False

        return True

    def reset_for_new_task(self):
        """Reset session state for a new task while preserving BOTH R environment AND conversation"""
        if self.persistent_mode:
            logger.info("🔄 Persistent mode: Minimal reset for ChatGPT Code Interpreter style")
            # FIXED: Do NOT clear conversation_history - this is the key for ChatGPT Code Interpreter behavior
            # Only reset temporary state variables
            self.finish_reason = 'new_input'
            self.content = ""
            self.function_name = ""
            self.code_str = ""
            self.display_code_block = ""
            self.stop_generating = False
            # KEEP: conversation_history, r_kernel, execution_history for full continuity
            logger.info(f"✅ Minimal reset complete - preserving {len(self.conversation_history)} conversation messages and R environment")
        else:
            logger.info("ℹ️ Non-persistent mode: Full reset not needed")

    def _format_context_for_llm(self, context: Dict) -> str:
        """Format context information for better LLM understanding"""
        formatted_parts = []

        # Current R code - simple approach (code is already in message text)
        current_code = context.get('current_code', '')
        if current_code and current_code.strip():
            # Code is already in message text, just add a simple context note
            formatted_parts.append(f"Note: User has R code in editor ({len(current_code)} chars)")
        else:
            # Simple handling when no code is available
            formatted_parts.append("NO R CODE PROVIDED")
            formatted_parts.append("Please ask the user to provide R code in the editor for analysis.")

        # Last execution result with error
        last_execution = context.get('last_execution_result', {})
        if last_execution and not last_execution.get('success', True):
            error_msg = last_execution.get('error', 'Unknown error')
            formatted_parts.append(f"LAST EXECUTION ERROR:\n{error_msg}")

        # Dataset information
        dataset_info = context.get('dataset_info', {})
        if dataset_info:
            dataset_path = context.get('dataset_path', '')
            if dataset_path:
                formatted_parts.append(f"DATASET PATH: {dataset_path}")

        # Execution history (recent errors)
        execution_history = context.get('execution_history', [])
        if execution_history:
            recent_errors = [h for h in execution_history[-3:] if not h.get('success', True)]
            if recent_errors:
                error_summary = []
                for i, error in enumerate(recent_errors, 1):
                    error_summary.append(f"{i}. {error.get('error', 'Unknown error')}")
                formatted_parts.append(f"RECENT EXECUTION ERRORS:\n" + "\n".join(error_summary))

        # Session information
        execution_id = context.get('execution_id', '')
        if execution_id:
            formatted_parts.append(f"SESSION ID: {execution_id}")

        if not formatted_parts:
            return "CONTEXT: No specific context available."

        return "CONTEXT INFORMATION:\n" + "\n\n".join(formatted_parts)

    def process_message(self, message: str, context: Dict = None) -> Generator[Dict[str, Any], None, None]:
        """
        Process user message using reference project approach
        Based on archive/src/web_ui.py main execution loop
        Enhanced for ChatGPT Code Interpreter style persistent sessions
        """
        logger.info(f"🎯 Processing R message: {message[:100]}...")

        # FIXED: Use proper persistent session handling
        if self.persistent_mode:
            logger.info("🔄 Persistent mode: Continuing existing session")
            # Only reset finish_reason and temporary state, preserve everything else
            self.finish_reason = 'new_input'
            self.content = ""
            self.function_name = ""
            self.code_str = ""
            self.display_code_block = ""
            self.stop_generating = False
            # KEEP: conversation_history, r_kernel, execution_history
            logger.info(f"📚 Continuing conversation with {len(self.conversation_history)} existing messages")
        else:
            # Non-persistent mode: use original reset behavior
            self.reset_for_new_request()

        # Test LLM connection first
        if not self.test_llm_connection():
            yield {
                'type': 'error',
                'content': 'LLM connection test failed. Please check LLM provider status.',
                'timestamp': datetime.now().isoformat()
            }
            return

        # Check for session termination commands first
        if message.lower().strip() in ['end session', 'quit', 'exit', 'terminate session', 'close session']:
            logger.info("🛑 User requested session termination")
            yield {
                'type': 'system',
                'content': 'Session terminated by user request. Thank you!',
                'timestamp': datetime.now().isoformat()
            }
            yield {
                'type': 'end',
                'content': 'Session ended',
                'timestamp': datetime.now().isoformat()
            }
            return

        # Add user message
        self.add_user_message(message)

        # Add context if provided - format it for better LLM understanding
        if context:
            context_msg = self._format_context_for_llm(context)
            logger.info(f"🔍 CONTEXT DEBUG: Adding context message to conversation")
            logger.info(f"🔍 CONTEXT DEBUG: Context message length: {len(context_msg)}")
            logger.info(f"🔍 CONTEXT DEBUG: Context preview: {context_msg[:200]}...")
            self.conversation_history.append({
                "role": "system",
                "content": context_msg
            })
            # Save conversation after adding context
            self._save_conversation_history()

        try:
            # Reference project main loop: while finish_reason in ('new_input', 'tool_calls')
            # FIXED: ChatGPT Code Interpreter style - different limits for persistent vs non-persistent
            if self.persistent_mode:
                max_iterations = 100  # Much higher limit for persistent sessions (ChatGPT style)
                logger.info("🔄 Persistent mode: Using extended iteration limit for ChatGPT Code Interpreter style")
            else:
                max_iterations = 15  # Original limit for non-persistent sessions

            iteration = 0
            total_content_received = False

            # REFERENCE IMPLEMENTATION PATTERN: Simple loop condition like successful projects
            while self.finish_reason in ('new_input', 'tool_calls') and iteration < max_iterations:
                iteration += 1
                logger.info(f"🔄 R Iteration {iteration}: Processing... (finish_reason: {self.finish_reason})")

                try:
                    # Execute one LLM interaction cycle with iteration info for smart stopping
                    cycle_generator = self._execute_llm_cycle(iteration=iteration)
                    for event in cycle_generator:
                        if event.get('type') == 'content' and event.get('content', '').strip():
                            total_content_received = True
                        yield event
                    logger.info(f"✅ R Iteration {iteration} completed with finish_reason: {self.finish_reason}")

                    # REFERENCE PATTERN: Natural loop exit when finish_reason is 'stop'
                    if self.finish_reason == 'stop':
                        logger.info("🔄 LLM finished, checking if session should continue")
                        if self.persistent_mode:
                            logger.info("🔄 Persistent mode: Session ready for next user input")
                            break  # Exit loop, session stays alive
                        else:
                            logger.info("🔄 Non-persistent mode: Session ending")
                            break  # Exit loop, session ends
                except Exception as e:
                    logger.error(f"❌ R Iteration {iteration} failed: {e}")
                    yield {
                        'type': 'error',
                        'content': f'R Iteration {iteration} failed: {str(e)}',
                        'timestamp': datetime.now().isoformat()
                    }
                    break

            # ENHANCED: Handle ChatGPT Code Interpreter style session continuation
            logger.info(f"🏁 R processing completed after {iteration} iteration(s), finish_reason: {self.finish_reason}")

            # CRITICAL FIX: Always send session_ready for persistent mode to keep session alive
            if self.persistent_mode:
                # ChatGPT Code Interpreter style: Session is ready for next input
                yield {
                    'type': 'session_ready',
                    'content': 'Session ready for next input. Variables and environment preserved.',
                    'session_id': self.execution_id,
                    'conversation_length': len(self.conversation_history),
                    'timestamp': datetime.now().isoformat()
                }
                logger.info("🔄 Persistent session ready for next user input")
            else:
                # Non-persistent mode: send completion event
                yield {
                    'type': 'complete',
                    'content': 'Response complete',
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"❌ R message processing failed: {e}")
            yield {
                'type': 'error',
                'content': f'R message processing failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }

    def _execute_llm_cycle(self, iteration: int = 1) -> Generator[Dict[str, Any], None, None]:
        """Execute one LLM interaction cycle based on reference project"""
        try:
            # Debug: Log what we're sending to LLM
            logger.info(f"🔍 Sending to LLM - Messages: {len(self.conversation_history)}")
            for i, msg in enumerate(self.conversation_history):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                content_preview = content[:100]
                logger.info(f"🔍 Message {i}: {role} - {content_preview}...")

                # Special logging for system messages with code context
                if role == 'system' and 'CURRENT R CODE' in content:
                    logger.info(f"🔍 CODE CONTEXT FOUND in message {i}")
                    logger.info(f"🔍 Full context message: {content}")

                # Special logging for user messages
                if role == 'user':
                    logger.info(f"🔍 USER MESSAGE: {content}")
            logger.info(f"🔍 Functions provided: {len(R_FUNCTIONS)}")

            # Call LLM with conversation history and R functions
            logger.info(f"🔍 Calling LLM with provider: {self.llm_client.get_current_provider()}")
            logger.info(f"🔍 Conversation history length: {len(self.conversation_history)}")
            logger.info(f"🔍 Functions provided: {len(R_FUNCTIONS)}")

            try:
                # Limit conversation history (simple approach since we use summaries now)
                limited_messages = self._limit_conversation_history(self.conversation_history)

                logger.info("🔍 Making LLM streaming call...")
                logger.info(f"🔍 Using {len(limited_messages)} messages (limited from {len(self.conversation_history)})")
                response = self.llm_client.chat_completion_stream(
                    messages=limited_messages,
                    functions=R_FUNCTIONS,
                    temperature=0.1
                )
                logger.info("🔍 LLM streaming call returned response object")
            except Exception as e:
                logger.error(f"❌ LLM call failed: {e}")
                logger.error(f"❌ Available providers: {self.llm_client.get_available_providers()}")
                logger.error(f"❌ Current provider: {self.llm_client.get_current_provider()}")
                raise

            # Process streaming response - reference project style
            assistant_message = ""
            function_calls = []
            chunk_count = 0

            logger.info("🔍 Starting to process LLM streaming response...")
            logger.info("🔍 About to enter chunk processing loop...")

            # CRITICAL FIX: Remove premature timeouts that truncate LLM responses
            # Allow LLM to complete its full response, especially for code generation
            start_time = time.time()
            timeout_seconds = 120  # Increased timeout for complete responses

            # Process chunks with proper error handling
            for chunk in response:
                chunk_count += 1
                logger.debug(f"🔍 Processing chunk {chunk_count}")

                # Only timeout for truly excessive delays (2 minutes)
                elapsed_time = time.time() - start_time
                if elapsed_time > timeout_seconds:
                    logger.warning(f"⚠️ LLM streaming taking longer than expected: {elapsed_time:.1f} seconds")
                    # Don't break - let it continue unless truly stuck
                    if elapsed_time > 180:  # 3 minutes absolute max
                        logger.error(f"❌ LLM streaming timeout after {elapsed_time:.1f} seconds")
                        break

                # Increased safety limit for longer responses
                if chunk_count > 5000:  # Increased from 1000 to allow longer responses
                    logger.error(f"❌ Too many chunks received ({chunk_count}), breaking loop")
                    break

                # Handle different response formats (OpenAI vs Claude)
                if hasattr(chunk, 'choices') and chunk.choices:
                    # OpenAI format - object with choices
                    logger.info(f"🔍 Chunk {chunk_count}: OpenAI format, processing...")
                elif isinstance(chunk, dict):
                    # Claude format - dictionary with type/content
                    logger.info(f"🔍 Chunk {chunk_count}: Claude format, processing...")
                else:
                    logger.info(f"🔍 Chunk {chunk_count}: Unknown format, skipping...")
                    continue

                # Process OpenAI format
                if hasattr(chunk, 'choices') and chunk.choices:
                    # OpenAI format
                    choice = chunk.choices[0]
                    delta = choice.delta

                    # Handle content
                    if hasattr(delta, 'content') and delta.content is not None:
                        logger.info(f"🔍 Chunk {chunk_count}: Raw content: '{delta.content}' (len={len(delta.content)})")
                        assistant_message += delta.content
                        yield {
                            'type': 'content',
                            'content': delta.content,
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        logger.debug(f"🔍 Chunk {chunk_count}: No content in delta")

                    # Handle function calls
                    if hasattr(delta, 'tool_calls') and delta.tool_calls:
                        for tool_call in delta.tool_calls:
                            if tool_call.function:
                                # Ensure function_calls list is large enough
                                while len(function_calls) <= tool_call.index:
                                    function_calls.append({})

                                if tool_call.function.name:
                                    function_calls[tool_call.index]['name'] = tool_call.function.name

                                if tool_call.function.arguments:
                                    if 'arguments' not in function_calls[tool_call.index]:
                                        function_calls[tool_call.index]['arguments'] = ""
                                    function_calls[tool_call.index]['arguments'] += tool_call.function.arguments

                    # Handle finish reason - FIXED: Proper streaming completion
                    if choice.finish_reason:
                        self.finish_reason = choice.finish_reason
                        logger.info(f"� Received finish_reason: {choice.finish_reason}")

                        # For persistent mode, keep 'stop' as 'stop' but handle it differently in main loop
                        if self.persistent_mode and choice.finish_reason == 'stop':
                            logger.info("🔄 Persistent mode: Keeping 'stop' for proper session handling")
                            # Keep self.finish_reason = 'stop' for proper loop exit

                        # Always break when we get a finish_reason - streaming is complete
                        break

                elif isinstance(chunk, dict):
                    # Claude format - handle different event types
                    if chunk.get('type') == 'content':
                        content = chunk.get('content', '')
                        if content:
                            assistant_message += content
                            yield {
                                'type': 'content',
                                'content': content,
                                'timestamp': datetime.now().isoformat()
                            }
                    elif chunk.get('type') == 'function_call_start':
                        # Claude function call start
                        tool_call = chunk.get('tool_call', {})
                        if tool_call:
                            function_calls.append({
                                'name': tool_call.get('function', {}).get('name', ''),
                                'arguments': ''
                            })
                    elif chunk.get('type') == 'function_call_delta':
                        # Claude function call arguments
                        if function_calls:
                            function_calls[-1]['arguments'] += chunk.get('delta', '')
                    elif chunk.get('type') == 'complete':
                        # REFERENCE PATTERN: Use API finish_reason directly, handle persistence at loop level
                        self.finish_reason = chunk.get('finish_reason', 'stop')
                        logger.info(f"🔍 API finish_reason: {self.finish_reason}")
                        break
                else:
                    logger.debug(f"🔍 Chunk {chunk_count}: Unknown format: {type(chunk)}")

            logger.info(f"🔍 Processed {chunk_count} chunks, assistant_message length: {len(assistant_message)}, finish_reason: {self.finish_reason}")
            logger.info(f"🔍 Assistant message content: '{assistant_message[:200]}...'")
            logger.info(f"🔍 Function calls detected: {len(function_calls)}")
            for i, fc in enumerate(function_calls):
                logger.info(f"🔍 Function call {i}: {fc.get('name', 'unknown')} with {len(fc.get('arguments', ''))} arg chars")

            # Add assistant message to conversation if there was content
            if assistant_message.strip():
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message
                })
                logger.info(f"✅ Added assistant message to conversation: '{assistant_message[:100]}...'")
                # Save conversation after adding assistant message
                self._save_conversation_history()

                # Send the complete content as a single event (much simpler!)
                yield {
                    'type': 'complete_content',
                    'content': assistant_message,
                    'timestamp': datetime.now().isoformat()
                }
                logger.info(f"✅ Sent complete content to frontend: {len(assistant_message)} characters")

                # ENHANCED: Smart stopping decision for ChatGPT Code Interpreter style
                # Note: finish_reason is now set correctly in API response handling above
                if not self.persistent_mode:
                    # Non-persistent mode: use original stopping logic
                    if not self._should_continue_session(iteration=iteration, assistant_message=assistant_message):
                        logger.info("🎯 Smart stopping triggered, will stop after this iteration")
                        self.finish_reason = 'stop'
                # Persistent mode: finish_reason already set to 'waiting_for_user' in API handling
            else:
                logger.warning(f"⚠️ No assistant message content received!")

            # REFERENCE PATTERN: Simple function execution like successful projects
            if self.finish_reason == 'tool_calls' and function_calls:
                logger.info("✅ Executing function calls (reference pattern)")
                yield from self._execute_function_calls(function_calls)

                # CRITICAL FIX: In persistent mode, stop after function execution to prevent loops
                if self.persistent_mode:
                    self.finish_reason = 'stop'
                    logger.info("✅ Function executed, stopping iteration loop (persistent mode)")
                else:
                    # Non-persistent mode: continue for LLM response
                    self.finish_reason = 'new_input'
                    logger.info("✅ Function executed, continuing for LLM response (non-persistent mode)")
            else:
                # No function calls, conversation continues normally
                logger.info("✅ No function calls in this iteration")

        except Exception as e:
            logger.error(f"❌ R LLM cycle failed: {e}")
            self.finish_reason = 'stop'
            raise e

    def _execute_function_calls(self, function_calls: List[dict]) -> Generator[Dict[str, Any], None, None]:
        """Execute R function calls based on reference project"""
        for call in function_calls:
            if 'name' not in call or 'arguments' not in call:
                continue

            function_name = call['name']

            try:
                # Parse function arguments
                args = json.loads(call['arguments'])

                yield {
                    'type': 'function_start',
                    'function_name': function_name,
                    'timestamp': datetime.now().isoformat()
                }

                # Initialize R interpreter only when LLM decides to call a function
                if not self.r_kernel:
                    logger.info("🚀 LLM decided to use R execution - initializing R Enhanced Interpreter now")
                    self.r_kernel = REnhancedInterpreter(self.work_dir, self.execution_id)

                # Execute the R function
                if function_name in self.r_kernel.available_functions:
                    llm_summary, raw_output = self.r_kernel.available_functions[function_name](**args)

                    # CRITICAL FIX: Separate LLM content from UI content
                    result_data = {
                        'type': 'function_result',
                        'function_name': function_name,
                        'content': llm_summary,  # Safe summary for LLM (no real data)
                        'output': raw_output,    # Raw output for UI display
                        'timestamp': datetime.now().isoformat(),
                        'session_id': self.execution_id,  # CRITICAL: Include session ID for file loading
                        'output_directory': self.work_dir  # CRITICAL: Include output directory
                    }

                    # CRITICAL FIX: Add R code to result if this is execute_r_code function
                    if function_name == 'execute_r_code' and 'code' in args:
                        result_data['r_code'] = args['code']
                        logger.info(f"🔍 BACKEND: Adding R code to function_result for editor update")

                    # Simple and efficient file detection - primary directory with fallback
                    if function_name == 'execute_r_code':
                        import os
                        import glob
                        try:
                            file_patterns = ['*.html', '*.csv', '*.png', '*.pdf', '*.rds']
                            generated_files = []

                            # Primary: Check main session directory (should be sufficient now)
                            for pattern in file_patterns:
                                files = glob.glob(os.path.join(self.work_dir, pattern))
                                generated_files.extend([os.path.basename(f) for f in files])

                            # Fallback: Check for any remaining nested files (legacy support)
                            if not generated_files:
                                for pattern in file_patterns:
                                    nested_files = glob.glob(os.path.join(self.work_dir, '**', pattern), recursive=True)
                                    for file_path in nested_files:
                                        rel_path = os.path.relpath(file_path, self.work_dir)
                                        generated_files.append(rel_path)

                            if generated_files:
                                result_data['files_generated'] = generated_files
                                result_data['output_directory'] = self.work_dir
                                logger.info(f"🔍 BACKEND: Found {len(generated_files)} files: {generated_files}")
                                logger.info(f"🔍 BACKEND: Search directories: {self.work_dir}")

                                # Debug: Show which files came from which search method
                                for file in generated_files:
                                    if '/' in file or '\\' in file:
                                        logger.info(f"🔍 BACKEND: Nested file detected: {file}")
                                    else:
                                        logger.info(f"🔍 BACKEND: Root level file: {file}")
                            else:
                                logger.warning(f"🔍 BACKEND: No files found in {self.work_dir}")
                                # Debug: List all files in directory
                                if os.path.exists(self.work_dir):
                                    all_files = []
                                    for root, dirs, files in os.walk(self.work_dir):
                                        for file in files:
                                            rel_path = os.path.relpath(os.path.join(root, file), self.work_dir)
                                            all_files.append(rel_path)
                                    logger.info(f"🔍 BACKEND: All files in session dir: {all_files}")

                                    # Check if there are nested execution directories
                                    nested_dirs = [d for d in os.listdir(self.work_dir) if d.startswith('outputs') or d.startswith('execution_')]
                                    if nested_dirs:
                                        logger.warning(f"🔍 BACKEND: Found nested directories: {nested_dirs}")
                                        logger.warning(f"🔍 BACKEND: This suggests nested output directory issue!")
                        except Exception as e:
                            logger.warning(f"File detection error: {e}")

                    logger.info(f"🔍 BACKEND: Sending function_result with keys: {list(result_data.keys())}")
                    yield result_data

                    # CRITICAL FIX: Add function result as FUNCTION message, not USER message
                    # This prevents the LLM from thinking the user sent the execution results
                    # Use LLM summary (no real data) for conversation history
                    function_message = {
                        "role": "function",
                        "name": function_name,
                        "content": llm_summary  # Safe summary for LLM (no real data)
                    }
                    self.conversation_history.append(function_message)
                    logger.info(f"🔍 BACKEND: Added function result as FUNCTION message to conversation history")
                    logger.info(f"🔍 BACKEND: Conversation length now: {len(self.conversation_history)}")
                    logger.info(f"🔍 BACKEND: Last message role: {self.conversation_history[-1].get('role', 'unknown')}")

                    # Save conversation after adding function result
                    self._save_conversation_history()

                else:
                    error_msg = f"Function {function_name} not available"
                    yield {
                        'type': 'error',
                        'content': error_msg,
                        'timestamp': datetime.now().isoformat()
                    }

            except Exception as e:
                error_msg = f"Function execution error: {str(e)}"
                logger.error(f"❌ R function execution failed: {e}")
                yield {
                    'type': 'error',
                    'content': error_msg,
                    'timestamp': datetime.now().isoformat()
                }

    def interrupt_execution(self):
        """Interrupt current execution"""
        self.stop_generating = True
        if self.r_kernel:
            self.r_kernel.interrupt_kernel()

    def restart_session(self):
        """Restart the R session"""
        try:
            if self.r_kernel:
                self.r_kernel.restart_kernel()
            self.conversation_history = [{"role": "system", "content": self._create_session_aware_system_message()}]
            self.finish_reason = 'new_input'
            return {'success': True, 'message': 'R session restarted successfully'}
        except Exception as e:
            return {'success': False, 'message': f'R restart failed: {str(e)}'}

    def cleanup(self):
        """Cleanup resources"""
        if self.r_kernel:
            self.r_kernel.cleanup()
            self.r_kernel = None

        # Conservative LLM client cleanup
        if hasattr(self.llm_client, 'cleanup') and callable(getattr(self.llm_client, 'cleanup', None)):
            try:
                self.llm_client.cleanup()
                logger.debug("🔍 LLM client cleanup completed")
            except Exception as e:
                logger.debug(f"⚠️ LLM client cleanup warning: {e}")
