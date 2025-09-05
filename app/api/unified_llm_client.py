#!/usr/bin/env python3
# Author: Jaime Yan
"""
Unified LLM Client with User Selection

This client allows users to select their preferred LLM provider:
1. DeepSeek API
2. Claude API (Anthropic)

Provides a consistent interface regardless of the selected provider.
"""

import os
import json
import logging
import requests
import time
import random
from typing import Dict, Any, List

# Optional Claude support
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    anthropic = None

# Optional local embedding support
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    SentenceTransformer = None

logger = logging.getLogger(__name__)

class UnifiedLLMClient:
    """Unified LLM client with user-selectable provider"""
    
    def __init__(self, config_path: str = "config/config.json", preferred_provider: str = "deepseek"):
        """
        Initialize the unified LLM client

        Args:
            config_path: Path to configuration file
            preferred_provider: "deepseek" or "claude"
        """
        self.config = self._load_config(config_path)
        self.preferred_provider = preferred_provider.lower()

        # Initialize session lazily to avoid initialization issues
        self._session = None

        # Initialize providers
        self._init_deepseek()
        self._init_claude()
        self._init_embeddings()

        # Validate selected provider
        if self.preferred_provider == "claude" and not self.claude_available:
            logger.warning("Claude not available, falling back to DeepSeek")
            self.preferred_provider = "deepseek"
        elif self.preferred_provider == "deepseek" and not self.deepseek_available:
            logger.warning("DeepSeek not available, falling back to Claude")
            self.preferred_provider = "claude"

        logger.info(f"✅ Unified LLM Client initialized with provider: {self.preferred_provider}")
        if self.embedding_available:
            logger.info(f"✅ Local embeddings available with model: {self.embedding_model}")

    def _get_session(self):
        """Get or create session lazily"""
        if self._session is None:
            self._session = requests.Session()
        return self._session
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Config file not found: {config_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def _init_deepseek(self):
        """Initialize DeepSeek client"""
        try:
            # Get DeepSeek configuration
            deepseek_config = self.config.get("apis", {}).get("deepseek", {})
            
            self.deepseek_api_key = deepseek_config.get("api_key", os.getenv("DEEPSEEK_API_KEY", ""))
            self.deepseek_base_url = deepseek_config.get("base_url", "https://api.deepseek.com")
            self.deepseek_model = deepseek_config.get("model", "deepseek-chat")
            
            self.deepseek_headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            self.deepseek_available = bool(self.deepseek_api_key)
            if self.deepseek_available:
                logger.info("✅ DeepSeek provider initialized")
            else:
                logger.warning("⚠️ DeepSeek API key not found")
                
        except Exception as e:
            logger.error(f"❌ DeepSeek initialization failed: {e}")
            self.deepseek_available = False
    
    def _init_claude(self):
        """Initialize Claude client"""
        try:
            if not CLAUDE_AVAILABLE:
                self.claude_available = False
                logger.info("📦 Claude library not installed")
                return
            
            # Get Claude configuration
            claude_config = self.config.get("apis", {}).get("anthropic", {})
            
            claude_api_key = claude_config.get("api_key", os.getenv("ANTHROPIC_API_KEY", ""))
            claude_enabled = claude_config.get("enabled", bool(claude_api_key))
            
            if claude_enabled and claude_api_key:
                self.claude_client = anthropic.Anthropic(api_key=claude_api_key)
                self.claude_available = True
                logger.info("✅ Claude provider initialized")
            else:
                self.claude_available = False
                logger.info("⚠️ Claude API key not found or disabled")
                
        except Exception as e:
            logger.error(f"❌ Claude initialization failed: {e}")
            self.claude_available = False
            self.claude_client = None

    def _init_embeddings(self):
        """Initialize local embedding model"""
        try:
            if not EMBEDDINGS_AVAILABLE:
                self.embedding_available = False
                logger.info("📦 sentence-transformers not installed - embeddings disabled")
                return

            # Get embedding model from config
            embedding_config = self.config.get("rag", {})
            self.embedding_model = embedding_config.get("embedding_model", "BAAI/bge-base-zh-v1.5")

            # Initialize the model lazily (load when first needed)
            self._embedding_model_instance = None
            self.embedding_available = True

            logger.info(f"✅ Embedding model configured: {self.embedding_model}")

        except Exception as e:
            logger.error(f"❌ Embedding initialization failed: {e}")
            self.embedding_available = False
    
    def chat_completion(self, messages: List[Dict[str, str]], functions: List[Dict] = None, **kwargs) -> Dict[str, Any]:
        """
        Generate chat completion using selected provider

        Args:
            messages: List of messages in the conversation
            functions: List of functions for function calling (optional)
            **kwargs: Additional parameters (max_tokens, temperature, etc.)

        Returns:
            Standardized response dictionary
        """
        # ROBUST FALLBACK LOGIC: Try preferred provider first, then fallback
        if self.preferred_provider == "claude" and self.claude_available:
            logger.info(f"🎯 Using preferred provider: Claude")
            return self._claude_chat_completion(messages, functions, **kwargs)
        elif self.preferred_provider == "deepseek" and self.deepseek_available:
            logger.info(f"🎯 Using preferred provider: DeepSeek")
            return self._deepseek_chat_completion(messages, functions, **kwargs)
        elif self.claude_available:
            logger.warning(f"⚠️ FALLBACK: Preferred provider {self.preferred_provider} unavailable, using Claude")
            return self._claude_chat_completion(messages, functions, **kwargs)
        elif self.deepseek_available:
            logger.warning(f"⚠️ FALLBACK: Preferred provider {self.preferred_provider} unavailable, using DeepSeek")
            return self._deepseek_chat_completion(messages, functions, **kwargs)
        else:
            # CRITICAL: This should never happen in production, but handle gracefully
            error_msg = f"❌ CRITICAL: No LLM providers available (preferred: {self.preferred_provider})"
            logger.error(error_msg)
            # Return error response instead of raising exception
            return {
                'type': 'error',
                'content': 'LLM service temporarily unavailable. Please try again in a moment.',
                'error_code': 'NO_PROVIDERS_AVAILABLE',
                'timestamp': time.time()
            }

    def chat_completion_stream(self, messages: List[Dict[str, str]], functions: List[Dict] = None, **kwargs):
        """
        Generate streaming chat completion with function calling support
        ROBUST FALLBACK: Automatically switches to available provider if preferred is unavailable

        Args:
            messages: List of messages in the conversation
            functions: List of function definitions for function calling
            **kwargs: Additional parameters (max_tokens, temperature, etc.)

        Yields:
            Streaming response chunks
        """
        # ROBUST FALLBACK LOGIC: Try preferred provider first, then fallback
        if self.preferred_provider == "claude" and self.claude_available:
            logger.info(f"🎯 Using preferred provider: Claude")
            yield from self._claude_chat_completion_stream(messages, functions, **kwargs)
        elif self.preferred_provider == "deepseek" and self.deepseek_available:
            logger.info(f"🎯 Using preferred provider: DeepSeek")
            yield from self._deepseek_chat_completion_stream(messages, functions, **kwargs)
        elif self.claude_available:
            logger.warning(f"⚠️ FALLBACK: Preferred provider {self.preferred_provider} unavailable, using Claude")
            yield from self._claude_chat_completion_stream(messages, functions, **kwargs)
        elif self.deepseek_available:
            logger.warning(f"⚠️ FALLBACK: Preferred provider {self.preferred_provider} unavailable, using DeepSeek")
            yield from self._deepseek_chat_completion_stream(messages, functions, **kwargs)
        else:
            # CRITICAL: This should never happen in production, but handle gracefully
            error_msg = f"❌ CRITICAL: No LLM providers available (preferred: {self.preferred_provider})"
            logger.error(error_msg)
            # Yield error event instead of raising exception to prevent SSE termination
            yield {
                'type': 'error',
                'content': 'LLM service temporarily unavailable. Please try again in a moment.',
                'error_code': 'NO_PROVIDERS_AVAILABLE',
                'timestamp': time.time()
            }

    def _convert_messages_for_deepseek(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert conversation history for DeepSeek compatibility

        DeepSeek uses a different function calling pattern than our internal format:
        - Our format: role="function" with name and content
        - DeepSeek format: role="tool" with tool_call_id and content

        Since we don't have the original tool_call_id, we'll filter out function messages
        to prevent API errors while preserving the conversation flow.
        """
        logger.info(f"🔍 DEEPSEEK CONVERSION: Processing {len(messages)} messages")
        converted_messages = []
        function_count = 0

        for i, message in enumerate(messages):
            role = message.get("role", "unknown")
            logger.info(f"🔍 DEEPSEEK CONVERSION: Message {i}: role={role}")

            if role == "function":
                function_count += 1
                # DeepSeek requires tool messages to have matching tool_call_id from previous assistant message
                # Since we don't track tool_call_ids in our conversation history, we filter these out
                # This prevents 422/400 errors while maintaining conversation context
                logger.info(f"🔄 DEEPSEEK CONVERSION: Filtered out function message {function_count} (no matching tool_call_id)")
                continue
            else:
                # Keep other messages as-is (system, user, assistant)
                converted_messages.append(message)

        logger.info(f"🔍 DEEPSEEK CONVERSION: Filtered out {function_count} function messages, kept {len(converted_messages)} messages")
        return converted_messages

    def _deepseek_chat_completion(self, messages: List[Dict[str, str]], functions: List[Dict] = None, **kwargs) -> Dict[str, Any]:
        """DeepSeek chat completion with function calling support"""
        try:
            # CRITICAL FIX: Convert function role messages to tool role for DeepSeek compatibility
            deepseek_messages = self._convert_messages_for_deepseek(messages)

            payload = {
                "model": self.deepseek_model,
                "messages": deepseek_messages,
                "max_tokens": kwargs.get("max_tokens", 4000),
                "temperature": kwargs.get("temperature", 0.1),
                "stream": False
            }

            # Add function calling if provided
            if functions:
                payload["tools"] = functions
                payload["tool_choice"] = "auto"

            # Debug: Log the payload being sent
            logger.info(f"🔍 DeepSeek non-streaming payload: {json.dumps(payload, indent=2)}")

            # Use session for connection reuse, but fallback to requests if needed
            try:
                response = self._get_session().post(
                    f"{self.deepseek_base_url}/chat/completions",
                    headers=self.deepseek_headers,
                    json=payload,
                    timeout=60  # Increased timeout for complex template generation
                )
            except Exception as session_error:
                logger.warning(f"⚠️ Session request failed, falling back to direct requests: {session_error}")
                response = requests.post(
                    f"{self.deepseek_base_url}/chat/completions",
                    headers=self.deepseek_headers,
                    json=payload,
                    timeout=60
                )

            if response.status_code == 200:
                result = response.json()
                logger.info("✅ DeepSeek API call successful")
                return result
            else:
                error_text = response.text
                logger.error(f"❌ DeepSeek API error {response.status_code}: {error_text}")
                if response.status_code == 422:
                    logger.error("❌ 422 Unprocessable Entity - function calling format issue")
                raise RuntimeError(f"DeepSeek API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"DeepSeek API call failed: {e}")
            # Try Claude fallback if available and this is a timeout/connection error
            if self.claude_available and ("timeout" in str(e).lower() or "connection" in str(e).lower()):
                logger.info("🔄 Trying Claude fallback due to DeepSeek timeout...")
                return self._claude_chat_completion(messages, **kwargs)
            raise RuntimeError(f"DeepSeek API call failed: {e}")

    def _deepseek_chat_completion_stream(self, messages: List[Dict[str, str]], functions: List[Dict] = None, **kwargs):
        """DeepSeek streaming chat completion with function calling"""
        try:
            # CRITICAL FIX: Convert function role messages to tool role for DeepSeek compatibility
            deepseek_messages = self._convert_messages_for_deepseek(messages)

            payload = {
                "model": self.deepseek_model,
                "messages": deepseek_messages,
                "max_tokens": kwargs.get("max_tokens", 4000),
                "temperature": kwargs.get("temperature", 0.1),
                "stream": True
            }

            # Add function calling if provided
            if functions:
                payload["tools"] = functions
                payload["tool_choice"] = "auto"

            # Debug: Log the payload being sent
            logger.info(f"🔍 DeepSeek payload: {json.dumps(payload, indent=2)}")

            # Use session for connection reuse, but fallback to requests if needed
            try:
                response = self._get_session().post(
                    f"{self.deepseek_base_url}/chat/completions",
                    headers=self.deepseek_headers,
                    json=payload,
                    stream=True,
                    timeout=60
                )
            except Exception as session_error:
                logger.warning(f"⚠️ Session streaming request failed, falling back to direct requests: {session_error}")
                response = requests.post(
                    f"{self.deepseek_base_url}/chat/completions",
                    headers=self.deepseek_headers,
                    json=payload,
                    stream=True,
                    timeout=60
                )

            if response.status_code != 200:
                error_text = response.text
                logger.error(f"❌ DeepSeek API error {response.status_code}: {error_text}")
                if response.status_code == 422:
                    logger.error("❌ 422 Unprocessable Entity - likely function calling format issue")
                    logger.error(f"❌ Payload that caused error: {json.dumps(payload, indent=2)}")
                response.raise_for_status()

            # CRITICAL FIX: Parse streaming response with proper cleanup
            try:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            if data_str.strip() == '[DONE]':
                                break
                            try:
                                chunk_data = json.loads(data_str)
                                # Convert to OpenAI-like format for compatibility
                                if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                    choice = chunk_data['choices'][0]
                                    # Create a mock response object
                                    class MockChoice:
                                        def __init__(self, choice_data):
                                            self.delta = MockDelta(choice_data.get('delta', {}))
                                            self.finish_reason = choice_data.get('finish_reason')

                                    class MockDelta:
                                        def __init__(self, delta_data):
                                            self.content = delta_data.get('content')
                                            # Handle tool_calls properly
                                            tool_calls_data = delta_data.get('tool_calls')
                                            if tool_calls_data:
                                                self.tool_calls = [MockToolCall(tc) for tc in tool_calls_data]
                                            else:
                                                self.tool_calls = None

                                    class MockToolCall:
                                        def __init__(self, tool_call_data):
                                            self.function = MockFunction(tool_call_data)
                                            self.index = tool_call_data.get('index', 0)

                                    class MockFunction:
                                        def __init__(self, tool_call_data):
                                            if 'function' in tool_call_data:
                                                self.name = tool_call_data['function'].get('name')
                                                self.arguments = tool_call_data['function'].get('arguments')
                                            else:
                                                self.name = None
                                                self.arguments = None

                                    class MockResponse:
                                        def __init__(self, choices):
                                            self.choices = choices

                                    yield MockResponse([MockChoice(choice)])
                            except json.JSONDecodeError:
                                continue
            finally:
                # Conservative cleanup - only close if response exists and has close method
                try:
                    if hasattr(response, 'close') and callable(getattr(response, 'close', None)):
                        response.close()
                        logger.debug("🔍 DeepSeek streaming response closed")
                except Exception as close_error:
                    logger.debug(f"⚠️ Response cleanup warning: {close_error}")

        except Exception as e:
            logger.error(f"DeepSeek streaming error: {e}")
            # Try Claude fallback if available
            if self.claude_available:
                logger.info("🔄 Trying Claude fallback due to DeepSeek streaming error...")
                yield from self._claude_chat_completion_stream(messages, functions, **kwargs)
            else:
                raise RuntimeError(f"DeepSeek streaming API call failed: {e}")
    
    def _claude_chat_completion(self, messages: List[Dict[str, str]], functions: List[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Claude chat completion with function calling support"""
        try:
            # Prepare Claude API parameters (optimized for code generation)
            claude_params = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": kwargs.get("max_tokens", 2000),  # Reduced from 4000 to prevent overload
                "temperature": kwargs.get("temperature", 0.1),  # Lower temperature for code generation
                "messages": self._convert_messages_to_claude_format(messages)
            }

            # Add tools (function calling) if provided
            if functions:
                claude_tools = self._convert_functions_to_claude_tools(functions)
                claude_params["tools"] = claude_tools

            response = self.claude_client.messages.create(**claude_params)

            # Handle function calls in response
            content = ""
            tool_calls = []

            for content_block in response.content:
                if content_block.type == "text":
                    content += content_block.text
                elif content_block.type == "tool_use":
                    tool_calls.append({
                        "id": content_block.id,
                        "type": "function",
                        "function": {
                            "name": content_block.name,
                            "arguments": json.dumps(content_block.input)
                        }
                    })

            # Build response message
            message = {
                "content": content,
                "role": "assistant"
            }
            if tool_calls:
                message["tool_calls"] = tool_calls

            logger.info("✅ Claude API call successful")
            return {
                "choices": [
                    {
                        "message": message,
                        "finish_reason": "tool_calls" if tool_calls else "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": response.usage.input_tokens if hasattr(response, 'usage') else 0,
                    "completion_tokens": response.usage.output_tokens if hasattr(response, 'usage') else 0,
                    "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if hasattr(response, 'usage') else 0
                },
                "model": "claude-3-5-sonnet-20241022"
            }

        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise RuntimeError(f"Claude API call failed: {e}")

    def _convert_messages_to_claude_format(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert messages to Claude API format"""
        claude_messages = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            # Claude doesn't support system messages in the messages array
            # System messages should be passed as system parameter
            if role == "system":
                continue  # Handle system messages separately
            elif role in ["user", "assistant"]:
                claude_messages.append({
                    "role": role,
                    "content": content
                })
            elif role == "tool":
                # Handle tool response messages
                claude_messages.append({
                    "role": "user",
                    "content": f"Tool result: {content}"
                })

        return claude_messages

    def _convert_functions_to_claude_tools(self, functions: List[Dict]) -> List[Dict]:
        """Convert OpenAI-style functions to Claude tools format"""
        claude_tools = []

        for func in functions:
            if func.get("type") == "function":
                function_def = func["function"]
                claude_tool = {
                    "name": function_def["name"],
                    "description": function_def["description"],
                    "input_schema": function_def.get("parameters", {})
                }
                claude_tools.append(claude_tool)

        return claude_tools

    def _claude_chat_completion_stream(self, messages: List[Dict[str, str]], functions: List[Dict] = None, **kwargs):
        """Claude streaming chat completion with function calling and rate limiting"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return self._claude_chat_completion_stream_impl(messages, functions, **kwargs)
            except Exception as e:
                error_str = str(e).lower()
                if ("overloaded" in error_str or "rate" in error_str) and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Claude overloaded, waiting {wait_time:.1f}s before retry {attempt + 2}/{max_retries}")
                    time.sleep(wait_time)
                    continue
                raise

    def _claude_chat_completion_stream_impl(self, messages: List[Dict[str, str]], functions: List[Dict] = None, **kwargs):
        """Claude streaming chat completion implementation"""
        try:
            # Prepare Claude API parameters (optimized for code generation)
            claude_params = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": kwargs.get("max_tokens", 2000),  # Reduced from 4000 to prevent overload
                "temperature": kwargs.get("temperature", 0.1),  # Lower temperature for code generation
                "messages": self._convert_messages_to_claude_format(messages),
                "stream": True
            }

            # Add tools (function calling) if provided
            if functions:
                claude_tools = self._convert_functions_to_claude_tools(functions)
                claude_params["tools"] = claude_tools

            # Create streaming response
            stream = self.claude_client.messages.create(**claude_params)

            # Process streaming response
            current_content = ""
            current_tool_calls = []

            for event in stream:
                if event.type == "message_start":
                    yield {"type": "start", "content": ""}

                elif event.type == "content_block_start":
                    if event.content_block.type == "text":
                        yield {"type": "content", "content": ""}
                    elif event.content_block.type == "tool_use":
                        # Start of tool use block
                        tool_call = {
                            "id": event.content_block.id,
                            "type": "function",
                            "function": {
                                "name": event.content_block.name,
                                "arguments": ""
                            }
                        }
                        current_tool_calls.append(tool_call)
                        yield {"type": "function_call_start", "tool_call": tool_call}

                elif event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        current_content += event.delta.text
                        yield {"type": "content", "content": event.delta.text}
                    elif event.delta.type == "input_json_delta":
                        # Tool arguments being streamed
                        if current_tool_calls:
                            current_tool_calls[-1]["function"]["arguments"] += event.delta.partial_json
                            yield {"type": "function_call_delta", "delta": event.delta.partial_json}

                elif event.type == "content_block_stop":
                    # Content block finished
                    pass

                elif event.type == "message_delta":
                    if event.delta.stop_reason:
                        finish_reason = "tool_calls" if current_tool_calls else "stop"
                        yield {"type": "complete", "finish_reason": finish_reason}

                elif event.type == "message_stop":
                    yield {"type": "end", "content": ""}

        except Exception as e:
            logger.error(f"Claude streaming error: {e}")
            raise RuntimeError(f"Claude streaming API call failed: {e}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using local sentence-transformers model

        Args:
            text: Text to generate embedding for

        Returns:
            List of floats representing the embedding
        """
        if not self.embedding_available:
            raise RuntimeError("Embeddings not available - install sentence-transformers: pip install sentence-transformers")

        try:
            # Load model if not already loaded (lazy loading)
            if self._embedding_model_instance is None:
                logger.info(f"Loading embedding model: {self.embedding_model}")
                self._embedding_model_instance = SentenceTransformer(self.embedding_model)
                logger.info(f"✅ Embedding model loaded: {self.embedding_model}")

            # Generate embedding
            embeddings = self._embedding_model_instance.encode([text], normalize_embeddings=True)
            return embeddings[0].tolist()

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise RuntimeError(f"Embedding generation failed: {e}")
    
    def set_provider(self, provider: str):
        """
        Change the preferred provider
        
        Args:
            provider: "deepseek" or "claude"
        """
        provider = provider.lower()
        if provider == "claude" and not self.claude_available:
            raise ValueError("Claude provider not available")
        elif provider == "deepseek" and not self.deepseek_available:
            raise ValueError("DeepSeek provider not available")
        elif provider not in ["deepseek", "claude"]:
            raise ValueError("Provider must be 'deepseek' or 'claude'")
        
        self.preferred_provider = provider
        logger.info(f"🔄 Provider changed to: {provider}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        providers = []
        if self.deepseek_available:
            providers.append("deepseek")
        if self.claude_available:
            providers.append("claude")
        return providers
    
    def get_current_provider(self) -> str:
        """Get current provider"""
        return self.preferred_provider

    def cleanup(self):
        """Cleanup resources and close connections"""
        try:
            if hasattr(self, '_session') and self._session is not None:
                self._session.close()
                self._session = None
                logger.info("🔍 LLM client session closed")
        except Exception as e:
            logger.warning(f"⚠️ Error during LLM client cleanup: {e}")

    def generate_response(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.1) -> Dict[str, Any]:
        """
        Generate response using selected provider (compatibility method)

        Args:
            prompt: Text prompt
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation

        Returns:
            Response dictionary with 'success', 'content', and other fields
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.chat_completion(messages, max_tokens=max_tokens, temperature=temperature)

            if "choices" in response and len(response["choices"]) > 0:
                content = response["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "content": content,
                    "api_used": self.preferred_provider,
                    "model": response.get("model", "unknown"),
                    "used_fallback": False
                }
            else:
                return {
                    "success": False,
                    "error": "No response from LLM",
                    "content": ""
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": ""
            }

# Create a singleton instance with default provider
unified_llm_client = UnifiedLLMClient(preferred_provider="deepseek")
