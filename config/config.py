#!/usr/bin/env python3
# Author: Jaime Yan
"""
Configuration Manager for R TLF System
Loads and manages system configuration
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the R TLF System"""
    
    def __init__(self):
        self.config_path = Path(__file__).parent / "config.json"
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"✓ Configuration loaded from {self.config_path}")
                return config
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
            "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
            "llm_models": {
                "claude": "claude-3-5-sonnet-20241022",
                "deepseek": "deepseek-coder",
                "openai": "gpt-4"
            },
            "rag_settings": {
                "vector_db_path": "../data/vector_db",
                "embedding_model": "text-embedding-ada-002",
                "top_k": 5
            },
            "r_settings": {
                "timeout": 60,
                "temp_dir": "temp",
                "required_packages": ["haven", "dplyr", "ggplot2"]
            },
            "experiment_settings": {
                "iterations_per_scenario": 5,
                "max_concurrent": 3,
                "save_intermediate": True
            },
            "logging": {
                "level": "INFO",
                "file": "r_tlf_system.log",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
    
    def _validate_config(self):
        """Validate configuration"""
        required_keys = ["anthropic_api_key", "llm_models", "rag_settings", "r_settings"]
        
        for key in required_keys:
            if key not in self.config:
                logger.warning(f"Missing required config key: {key}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self):
        """Save configuration to file"""
        try:
            self.config_path.parent.mkdir(exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"✓ Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for specific provider"""
        key_map = {
            "anthropic": "anthropic_api_key",
            "deepseek": "deepseek_api_key",
            "openai": "openai_api_key"
        }
        
        key_name = key_map.get(provider.lower())
        if key_name:
            return self.get(key_name)
        
        return None
    
    def get_llm_model(self, provider: str) -> str:
        """Get LLM model for specific provider"""
        models = self.get("llm_models", {})
        return models.get(provider.lower(), "claude-3-5-sonnet-20241022")
    
    def is_api_available(self, provider: str) -> bool:
        """Check if API is available for provider"""
        api_key = self.get_api_key(provider)
        return bool(api_key and api_key.strip())
    
    def get_rag_settings(self) -> Dict[str, Any]:
        """Get RAG settings"""
        return self.get("rag_settings", {})
    
    def get_r_settings(self) -> Dict[str, Any]:
        """Get R settings"""
        return self.get("r_settings", {})
    
    def get_experiment_settings(self) -> Dict[str, Any]:
        """Get experiment settings"""
        return self.get("experiment_settings", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.get("logging", {})
    
    def update_from_env(self):
        """Update configuration from environment variables"""
        env_mappings = {
            "ANTHROPIC_API_KEY": "anthropic_api_key",
            "DEEPSEEK_API_KEY": "deepseek_api_key",
            "OPENAI_API_KEY": "openai_api_key"
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                self.set(config_key, env_value)
                logger.info(f"Updated {config_key} from environment variable")
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate all API keys"""
        providers = ["anthropic", "deepseek", "openai"]
        validation_results = {}
        
        for provider in providers:
            api_key = self.get_api_key(provider)
            validation_results[provider] = bool(api_key and api_key.strip())
            
            if validation_results[provider]:
                logger.info(f"✓ {provider.capitalize()} API key available")
            else:
                logger.warning(f"✗ {provider.capitalize()} API key not available")
        
        return validation_results 