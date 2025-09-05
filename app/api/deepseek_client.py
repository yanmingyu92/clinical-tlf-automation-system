#!/usr/bin/env python
# Author: Jaime Yan
"""
DeepSeek API Client

This module provides a client for the DeepSeek API, which is used for natural language
processing tasks including text generation, chat completion, and embedding generation.
"""

import os
import json
import logging
import requests
import time
from typing import Dict, Any, List, Optional, Union

# Optional Claude fallback support
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    anthropic = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class DeepSeekClient:
    """Client for interacting with the DeepSeek API"""

    def __init__(self, config=None):
        """Initialize the DeepSeek client"""
        # Import config here to avoid circular imports
        if config is None:
            try:
                from app.core.config_loader import config as app_config
                config = app_config
            except ImportError:
                logger.warning("Could not import config, using environment variables")
                config = None

        # Load configuration from config.json or environment variables
        if config and config.is_initialized():
            # Try to get API key from the correct config path
            self.api_key = config.get("apis.deepseek.api_key", "")
            if not self.api_key:
                # Fallback to old path
                self.api_key = config.get("API.API_KEY", "")
            
            self.api_base = config.get("apis.deepseek.base_url", "https://api.deepseek.com")
            if not self.api_base or self.api_base == "https://api.deepseek.com":
                # Fallback to old path
                self.api_base = config.get("API.base_url", "https://api.deepseek.com")
            
            self.model = config.get("models.deepseek.default.model_name", "deepseek-chat")
            if not self.model:
                # Fallback to old path
                self.model = config.get("model.default.model_name", "deepseek-chat")
            
            self.embedding_model = config.get("rag.embedding_model", "deepseek-embedding")
            logger.info("DeepSeek client initialized with config.json settings")
        else:
            # Fallback to environment variables
            self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
            self.api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
            self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
            self.embedding_model = os.getenv("DEEPSEEK_EMBEDDING_MODEL", "deepseek-embedding")
            logger.warning("DeepSeek client initialized with environment variables")

        # Validate configuration
        if not self.api_key:
            logger.error("No API key found in configuration or environment variables")
            raise ValueError("DeepSeek API key is required but not found")

        # Initialize Claude fallback if available
        self.claude_client = None
        if CLAUDE_AVAILABLE and config:
            claude_config = config.get("apis.anthropic", {})
            if claude_config.get("enabled", False) and claude_config.get("api_key"):
                try:
                    self.claude_client = anthropic.Anthropic(api_key=claude_config["api_key"])
                    logger.info("✅ Claude fallback initialized")
                except Exception as e:
                    logger.warning(f"⚠️ Claude fallback failed: {e}")
        elif CLAUDE_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            try:
                self.claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                logger.info("✅ Claude fallback initialized from environment")
            except Exception as e:
                logger.warning(f"⚠️ Claude fallback failed: {e}")

        logger.info(f"DeepSeek client initialized with base URL: {self.api_base}")
        logger.info(f"Using model: {self.model}, embedding model: {self.embedding_model}")
        if self.claude_client:
            logger.info("🔄 Claude fallback available")
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Generate a chat completion using the DeepSeek API with optimized retry logic

        Args:
            messages: List of messages in the conversation
            **kwargs: Additional parameters to pass to the API

        Returns:
            API response as a dictionary
        """
        max_retries = 2  # Reduced from 3 for speed
        base_timeout = 15  # Reduced from 120 to 15 seconds for speed

        for attempt in range(max_retries):
            try:
                # Set up API call
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }

                payload = {
                    "model": self.model,
                    "messages": messages,
                    **kwargs
                }

                # Optimized timeout progression
                timeout = base_timeout + (attempt * 10)  # 15s, 25s instead of 120s, 150s, 180s
                logger.info(f"Attempt {attempt + 1}/{max_retries} with timeout {timeout}s")

                # Make API call
                response = requests.post(
                    f"{self.api_base}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=timeout
                )

                # Check for errors
                response.raise_for_status()

                # Return response as dictionary
                return response.json()

            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 1  # Reduced wait time from exponential backoff
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"All {max_retries} attempts failed due to timeout")
                    # Try Claude fallback if available
                    if self.claude_client:
                        logger.info("🔄 Trying Claude fallback after timeout...")
                        return self._try_claude_fallback(messages, **kwargs)
                    raise RuntimeError(f"DeepSeek API call failed after {max_retries} attempts: {str(e)}")

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error on attempt {attempt + 1}/{max_retries}: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"All {max_retries} attempts failed due to connection error")
                    # Try Claude fallback if available
                    if self.claude_client:
                        logger.info("🔄 Trying Claude fallback after connection error...")
                        return self._try_claude_fallback(messages, **kwargs)
                    raise RuntimeError(f"DeepSeek API call failed after {max_retries} attempts: {str(e)}")

            except Exception as e:
                logger.error(f"Error in chat completion API call: {str(e)}", exc_info=True)
                # Try Claude fallback if available
                if self.claude_client:
                    logger.info("🔄 Trying Claude fallback...")
                    return self._try_claude_fallback(messages, **kwargs)
                raise RuntimeError(f"DeepSeek API call failed: {str(e)}")
    
    def chat_completion_with_functions(self, messages: List[Dict[str, str]], functions: List[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Generate a chat completion with function calling support

        Args:
            messages: List of messages in the conversation
            functions: List of function definitions for function calling
            **kwargs: Additional parameters to pass to the API

        Returns:
            API response as a dictionary
        """
        # For now, we'll simulate function calling by using regular chat completion
        # and parsing the response for function calls
        try:
            # If functions are provided, add them to the system message
            if functions:
                function_descriptions = []
                for func in functions:
                    func_desc = f"Function: {func['name']}\nDescription: {func['description']}\nParameters: {func.get('parameters', {})}"
                    function_descriptions.append(func_desc)

                # Add function information to the system message
                system_message = {
                    "role": "system",
                    "content": f"You have access to the following functions. When you need to use a function, respond with a function call in the format: FUNCTION_CALL: function_name(param1=value1, param2=value2)\n\nAvailable functions:\n" + "\n\n".join(function_descriptions)
                }

                # Insert system message at the beginning if not present
                if not messages or messages[0]["role"] != "system":
                    messages = [system_message] + messages
                else:
                    # Update existing system message
                    messages[0]["content"] = system_message["content"] + "\n\n" + messages[0]["content"]

            # Use regular chat completion
            response = self.chat_completion(messages, **kwargs)

            # Create a mock response object that mimics OpenAI's structure
            class MockChoice:
                def __init__(self, message_content):
                    self.message = MockMessage(message_content)

            class MockMessage:
                def __init__(self, content):
                    self.content = content
                    self.tool_calls = None
                    # Parse for function calls in the content
                    if "FUNCTION_CALL:" in content:
                        self.tool_calls = self._parse_function_calls(content)

                def _parse_function_calls(self, content):
                    """Parse function calls from text content"""
                    import re
                    import uuid

                    tool_calls = []
                    # Look for FUNCTION_CALL: function_name(param1=value1, param2=value2)
                    # Use a more robust pattern that handles nested parentheses
                    pattern = r'FUNCTION_CALL:\s*(\w+)\s*\((.*)\)'
                    matches = []

                    # Find all FUNCTION_CALL occurrences
                    for match in re.finditer(r'FUNCTION_CALL:\s*(\w+)\s*\(', content):
                        function_name = match.group(1)
                        start_pos = match.end() - 1  # Position of opening parenthesis

                        # Find matching closing parenthesis
                        paren_count = 0
                        end_pos = start_pos
                        for i, char in enumerate(content[start_pos:]):
                            if char == '(':
                                paren_count += 1
                            elif char == ')':
                                paren_count -= 1
                                if paren_count == 0:
                                    end_pos = start_pos + i
                                    break

                        if paren_count == 0:  # Found matching parenthesis
                            args_str = content[start_pos + 1:end_pos]
                            matches.append((function_name, args_str))

                    for function_name, args_str in matches:
                        try:
                            # Parse arguments
                            args_dict = {}
                            if args_str.strip():
                                # Simple argument parsing - handle key=value pairs
                                arg_pairs = []
                                current_arg = ""
                                paren_count = 0
                                quote_char = None

                                for char in args_str:
                                    if char in ['"', "'"] and quote_char is None:
                                        quote_char = char
                                        current_arg += char
                                    elif char == quote_char:
                                        quote_char = None
                                        current_arg += char
                                    elif quote_char is not None:
                                        current_arg += char
                                    elif char == '(':
                                        paren_count += 1
                                        current_arg += char
                                    elif char == ')':
                                        paren_count -= 1
                                        current_arg += char
                                    elif char == ',' and paren_count == 0 and quote_char is None:
                                        arg_pairs.append(current_arg.strip())
                                        current_arg = ""
                                    else:
                                        current_arg += char

                                if current_arg.strip():
                                    arg_pairs.append(current_arg.strip())

                                for pair in arg_pairs:
                                    if '=' in pair:
                                        key, value = pair.split('=', 1)
                                        key = key.strip()
                                        value = value.strip()
                                        # Remove quotes if present
                                        if value.startswith('"') and value.endswith('"'):
                                            value = value[1:-1]
                                        elif value.startswith("'") and value.endswith("'"):
                                            value = value[1:-1]
                                        args_dict[key] = value

                            # Create mock tool call
                            class MockToolCall:
                                def __init__(self, func_name, arguments):
                                    self.id = str(uuid.uuid4())
                                    self.function = MockFunction(func_name, arguments)

                            class MockFunction:
                                def __init__(self, name, arguments):
                                    self.name = name
                                    self.arguments = json.dumps(arguments)

                            tool_calls.append(MockToolCall(function_name, args_dict))

                        except Exception as e:
                            logger.warning(f"Failed to parse function call: {function_name}({args_str}) - {e}")
                            continue

                    return tool_calls if tool_calls else None

            class MockResponse:
                def __init__(self, response_dict):
                    if "choices" in response_dict and response_dict["choices"]:
                        content = response_dict["choices"][0]["message"]["content"]
                        self.choices = [MockChoice(content)]
                    else:
                        self.choices = []

            return MockResponse(response)

        except Exception as e:
            logger.error(f"Error in chat completion with functions: {str(e)}", exc_info=True)
            raise RuntimeError(f"DeepSeek function calling failed: {str(e)}")

    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using the DeepSeek API (simplified wrapper)

        Args:
            prompt: Text prompt to generate from
            **kwargs: Additional parameters to pass to the API

        Returns:
            Generated text as a string
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.chat_completion(messages, **kwargs)

        if "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"]
        else:
            return "Error generating text"
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for a given text

        Args:
            text: Text to generate an embedding for

        Returns:
            List of floats representing the embedding
        """
        try:
            # Check if this is a local embedding model (BGE, M3E, etc.)
            if self._is_local_embedding_model(self.embedding_model):
                return self._generate_local_embedding(text)
            else:
                return self._generate_api_embedding(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}", exc_info=True)
            raise RuntimeError(f"Embedding generation failed: {str(e)}")

    def _is_local_embedding_model(self, model_name: str) -> bool:
        """Check if the embedding model is a local model that needs sentence-transformers"""
        local_models = [
            "BAAI/bge-",
            "moka-ai/m3e",
            "jinaai/jina-embeddings",
            "TaylorAI/bge-",
            "sentence-transformers/",
            "text2vec",
        ]
        return any(model_name.startswith(prefix) for prefix in local_models)

    def _generate_local_embedding(self, text: str) -> List[float]:
        """Generate embedding using local sentence-transformers model"""
        try:
            # Initialize model if not already done
            if not hasattr(self, '_local_embedding_model') or self._local_embedding_model is None:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading local embedding model: {self.embedding_model}")
                self._local_embedding_model = SentenceTransformer(self.embedding_model)
                logger.info(f"Successfully loaded {self.embedding_model}")

            # Generate embedding
            embeddings = self._local_embedding_model.encode([text], normalize_embeddings=True)
            return embeddings[0].tolist()

        except ImportError:
            logger.error("sentence-transformers library not installed. Please install it: pip install sentence-transformers")
            raise RuntimeError("sentence-transformers library required for local embedding models")
        except Exception as e:
            logger.error(f"Error with local embedding model {self.embedding_model}: {str(e)}")
            raise RuntimeError(f"Local embedding generation failed: {str(e)}")

    def _generate_api_embedding(self, text: str) -> List[float]:
        """Generate embedding using DeepSeek API with retry logic"""
        max_retries = 3
        base_timeout = 60

        for attempt in range(max_retries):
            try:
                # Set up API call
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }

                payload = {
                    "model": self.embedding_model,
                    "input": text
                }

                # Increase timeout for each retry
                timeout = base_timeout + (attempt * 20)
                logger.info(f"Embedding attempt {attempt + 1}/{max_retries} with timeout {timeout}s")

                # Make API call
                response = requests.post(
                    f"{self.api_base}/v1/embeddings",
                    headers=headers,
                    json=payload,
                    timeout=timeout
                )

                # Check for errors
                response.raise_for_status()

                # Parse response
                result = response.json()

                # Return embedding
                if "data" in result and len(result["data"]) > 0:
                    return result["data"][0]["embedding"]
                else:
                    raise ValueError("No embedding found in API response")

            except requests.exceptions.Timeout as e:
                logger.warning(f"Embedding timeout on attempt {attempt + 1}/{max_retries}: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"All {max_retries} embedding attempts failed due to timeout")
                    raise RuntimeError(f"DeepSeek embedding API call failed after {max_retries} attempts: {str(e)}")

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Embedding connection error on attempt {attempt + 1}/{max_retries}: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"All {max_retries} embedding attempts failed due to connection error")
                    raise RuntimeError(f"DeepSeek embedding API call failed after {max_retries} attempts: {str(e)}")

            except Exception as e:
                logger.error(f"Error with API embedding: {str(e)}", exc_info=True)
                raise RuntimeError(f"DeepSeek embedding API call failed: {str(e)}")

    def _try_claude_fallback(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Try Claude as fallback when DeepSeek fails"""
        if not self.claude_client:
            raise RuntimeError("Claude fallback not available")

        try:
            logger.info("🔄 Using Claude fallback...")

            # Convert messages to Claude format
            if len(messages) == 1 and messages[0]["role"] == "user":
                prompt = messages[0]["content"]
            else:
                # Handle multi-message conversations
                prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

            # Call Claude API
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=kwargs.get("max_tokens", 4000),
                temperature=kwargs.get("temperature", 0.7),
                messages=[{"role": "user", "content": prompt}]
            )

            # Convert Claude response to DeepSeek format
            content = response.content[0].text if response.content else ""

            logger.info("✅ Claude fallback successful")
            return {
                "choices": [
                    {
                        "message": {
                            "content": content,
                            "role": "assistant"
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": response.usage.input_tokens if hasattr(response, 'usage') else 0,
                    "completion_tokens": response.usage.output_tokens if hasattr(response, 'usage') else 0,
                    "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if hasattr(response, 'usage') else 0
                },
                "model": "claude-3-5-sonnet-20241022",
                "api_used": "claude_fallback"
            }

        except Exception as e:
            logger.error(f"Claude fallback failed: {str(e)}")
            raise RuntimeError(f"Both DeepSeek and Claude failed: {str(e)}")

# Create a singleton instance for global use
deepseek_client = DeepSeekClient()

# DEPRECATED: Use UnifiedLLMClient instead
# This is kept for backward compatibility only
class DeprecatedDeepSeekClientWrapper:
    """Wrapper to redirect to UnifiedLLMClient for backward compatibility"""

    def __init__(self):
        from app.api.unified_llm_client import UnifiedLLMClient
        self._client = UnifiedLLMClient(preferred_provider="deepseek")
        import warnings
        warnings.warn(
            "DeepSeekClient is deprecated. Use UnifiedLLMClient instead.",
            DeprecationWarning,
            stacklevel=2
        )

    def chat_completion(self, messages, **kwargs):
        return self._client.chat_completion(messages, **kwargs)

    def generate_text(self, prompt, **kwargs):
        response = self._client.generate_response(prompt, **kwargs)
        return response.get("content", "") if response.get("success") else ""

    def generate_embedding(self, text):
        return self._client.generate_embedding(text)