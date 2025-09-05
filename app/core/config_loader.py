"""
Configuration loader for R TLF System
"""
# Author: Jaime Yan
import os
import json
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ConfigLoader:
    """
    Configuration loader for R TLF System
    """
    def __init__(self):
        """Initialize the config loader"""
        self.config_path = os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config"
        ))
        self.config_file = os.path.join(self.config_path, "config.json")
        self.config = {}
        self.initialized = False
        
        # Load config on initialization
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file"""
        try:
            # Create config directory if it doesn't exist
            if not os.path.exists(self.config_path):
                os.makedirs(self.config_path)
                logger.info(f"Created config directory: {self.config_path}")
            
            # Create default config if file doesn't exist
            if not os.path.exists(self.config_file):
                self._create_default_config()
            
            # Load config from file
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            
            # Check for environment variables that can override config
            self._check_environment_variables()
            
            # Add paths section if not present
            if "paths" not in self.config:
                self.config["paths"] = {
                    "templates_dir": "./templates",
                    "datasets_dir": "./data/adam",
                    "output_dir": "./output",
                    "cache_dir": "./data/cache"
                }
                self._save_config()
            
            self.initialized = True
            logger.info("Configuration loaded successfully")
        
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            self.initialized = False
    
    def _create_default_config(self) -> None:
        """Create default configuration file"""
        default_config = {
            "API": {
                "API_KEY": "",
                "API_VERSION": "v1",
                "base_url": "https://dseek.aikeji.vip"
            },
            "model": {
                "default": {
                    "model_name": "deepseek-chat",
                    "temperature": 0.7,
                    "max_tokens": 2048
                },
                "code": {
                    "model_name": "deepseek-coder",
                    "temperature": 0.2,
                    "max_tokens": 4096
                }
            },
            "rag": {
                "vector_db_path": "data/vector_db",
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "top_k": 3
            },
            "template_storage": {
                "reference_path": "data/reference_templates"
            },
            "r_interpreter": {
                "use_rpy2": True,
                "r_home": "",
                "default_libraries": [
                    "dplyr",
                    "ggplot2",
                    "haven",
                    "gt"
                ]
            },
            "ui": {
                "title": "R TLF System",
                "description": "Generate clinical trial Tables, Listings, and Figures using R",
                "theme": "gradio/neutral",
                "port": 7860
            },
            "paths": {
                "templates_dir": "./templates",
                "datasets_dir": "./data/adam",
                "output_dir": "./output",
                "cache_dir": "./data/cache"
            }
        }
        
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2)
            
            logger.info(f"Created default configuration: {self.config_file}")
        
        except Exception as e:
            logger.error(f"Error creating default configuration: {str(e)}")
    
    def _check_environment_variables(self) -> None:
        """Check for environment variables that can override config"""
        # Check for API key
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if api_key:
            self.config["API"]["API_KEY"] = api_key
            logger.info("Using API key from environment variable")
        
        # Check for API URL
        api_url = os.environ.get("DEEPSEEK_API_URL")
        if api_url:
            self.config["API"]["base_url"] = api_url
            logger.info("Using API URL from environment variable")
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value by path (e.g., "paths.output_dir")
        
        Args:
            path: Path to configuration value (dot separated)
            default: Default value if path not found
            
        Returns:
            Configuration value or default if not found
        """
        try:
            # Split the path into parts
            parts = path.split(".")
            
            # Start with the full config
            value = self.config
            
            # Traverse the path
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            
            return value
        except Exception as e:
            logger.error(f"Error getting configuration value for {path}: {str(e)}")
            return default
    
    def get_api_config(self) -> Dict[str, str]:
        """
        Get API configuration
        
        Returns:
            API configuration dictionary
        """
        return self.config.get("API", {})
    
    def get_model_config(self) -> Dict[str, Dict[str, Any]]:
        """
        Get model configuration
        
        Returns:
            Model configuration dictionary
        """
        return self.config.get("model", {})
    
    def get_rag_config(self) -> Dict[str, Any]:
        """
        Get RAG configuration
        
        Returns:
            RAG configuration dictionary
        """
        return self.config.get("rag", {})
    
    def get_template_storage_config(self) -> Dict[str, str]:
        """
        Get template storage configuration

        Returns:
            Template storage configuration dictionary
        """
        return self.config.get("template_storage", {})

    def get_paths_config(self) -> Dict[str, str]:
        """
        Get paths configuration

        Returns:
            Paths configuration dictionary
        """
        return self.config.get("paths", {})
    
    def get_r_interpreter_config(self) -> Dict[str, Any]:
        """
        Get R interpreter configuration
        
        Returns:
            R interpreter configuration dictionary
        """
        return self.config.get("r_interpreter", {})
    
    def get_ui_config(self) -> Dict[str, Any]:
        """
        Get UI configuration
        
        Returns:
            UI configuration dictionary
        """
        return self.config.get("ui", {})
    
    def update_config(self, section: str, key: str, value: Any) -> bool:
        """
        Update configuration value
        
        Args:
            section: Configuration section
            key: Configuration key
            value: New value
            
        Returns:
            Success flag
        """
        try:
            if section in self.config:
                self.config[section][key] = value
                
                # Save updated config
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=2)
                
                logger.info(f"Updated config: {section}.{key}")
                return True
            else:
                logger.error(f"Config section not found: {section}")
                return False
        
        except Exception as e:
            logger.error(f"Error updating configuration: {str(e)}")
            return False
    
    def is_initialized(self) -> bool:
        """
        Check if configuration is successfully initialized
        
        Returns:
            True if configuration is initialized, False otherwise
        """
        return self.initialized

    def get_config(self) -> Dict[str, Any]:
        """
        Get the complete configuration dictionary
        
        Returns:
            Complete configuration dictionary
        """
        return self.config.copy()

# Create a singleton instance for global use
config = ConfigLoader()

# Module-level convenience function
def load_config() -> Dict[str, Any]:
    """
    Load configuration - convenience function that returns the config dictionary
    """
    loader = ConfigLoader()
    return loader.get_config()

if __name__ == "__main__":
    # Print the current configuration
    print(json.dumps(config.config, indent=2)) 