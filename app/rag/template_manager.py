"""
Template Manager for R TLF System

This module handles only the essential template management operations:
- Loading templates from files
- Vector search functionality
- Basic initialization and cleanup
"""
# Author: Jaime Yan

import os
import json
import logging
from typing import List, Dict, Any, Optional

from app.core.config_loader import config
from app.rag.vector_store import vector_store

# Configure logging
logger = logging.getLogger(__name__)

class TemplateManager:
    """Simplified Template Manager class for managing templates"""
    
    def __init__(self):
        """Initialize the Template Manager"""
        # Get templates directory from config
        self.templates_dir = config.get("paths.templates_dir", "./templates")
        self.index_path = os.path.join(self.templates_dir, "index.json")
        
        # Create directories if they don't exist
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Initialize template index
        self.template_index = self._load_index()
        
        # Initialize unified LLM client for embeddings
        from app.api.unified_llm_client import UnifiedLLMClient
        self.llm_client = UnifiedLLMClient(preferred_provider="deepseek")
        
        # Initialize vector search
        self.use_vector_search = config.get("rag.use_vector_search", True)

        # Clean up template index
        self._cleanup_template_index()

        # Check if vector store needs rebuilding
        self._ensure_vector_store_sync()
    
    def _load_index(self) -> Dict[str, Any]:
        """Load the template index from disk"""
        try:
            if os.path.exists(self.index_path):
                with open(self.index_path, 'r') as f:
                    return json.load(f)
            else:
                # Create a new index
                return {"templates": []}
        except Exception as e:
            logger.error(f"Error loading template index: {str(e)}")
            return {"templates": []}
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a template by ID
        
        Args:
            template_id: ID of the template to get
            
        Returns:
            Template dict or None if not found
        """
        try:
            # Find template in index
            template_entry = None
            for entry in self.template_index["templates"]:
                if entry["id"] == template_id:
                    template_entry = entry
                    break
            
            if not template_entry:
                logger.warning(f"Template not found: {template_id}")
                return None
            
            # Load template from file
            template_path = os.path.join(self.templates_dir, template_entry["path"])
            
            if not os.path.exists(template_path):
                logger.warning(f"Template file not found: {template_path}")
                return None
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            return template_data
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return None
    
    def search_templates(self, query: str, filter_type: str = "All") -> List[Dict[str, Any]]:
        """
        Search for templates using vector similarity
        
        Args:
            query: Search query
            filter_type: Type filter (All, Table, Listing, Figure)
            
        Returns:
            List of matching templates
        """
        try:
            # Use vector search if enabled and query provided
            if self.use_vector_search and query and len(query.strip()) > 0:
                return self._search_templates_vector(query, filter_type)
            else:
                # Return all templates if no query
                templates = self.template_index.get("templates", [])
                if filter_type.lower() != "all":
                    templates = [t for t in templates if t.get("type", "").lower() == filter_type.lower()]
                return templates
        except Exception as e:
            logger.error(f"Error searching templates: {str(e)}")
            return []
    
    def _search_templates_vector(self, query: str, filter_type: str = "All") -> List[Dict[str, Any]]:
        """
        Search for templates using vector similarity
        
        Args:
            query: Search query
            filter_type: Type filter
            
        Returns:
            List of matching templates
        """
        try:
            # Generate query embedding
            query_embedding = self.llm_client.generate_embedding(query)
            
            # Search vector store
            results = vector_store.search(query_embedding, k=10)
            
            # Filter by type if needed
            if filter_type.lower() != "all":
                results = [
                    result for result in results
                    if result["metadata"].get("type", "").lower() == filter_type.lower()
                ]
            
            # Format results
            formatted_results = []
            for result in results:
                template_id = result["id"]
                template_data = self._get_template_from_vector_metadata(result["metadata"])
                if template_data:
                    template_type = template_data.get("type", result["metadata"].get("type", "table"))
                    r_code = template_data.get("r_code", template_data.get("r_code_content", ""))

                    formatted_results.append({
                        "id": template_id,
                        "title": result["metadata"].get("title", "Untitled"),
                        "description": template_data.get("description", "No description available"),
                        "type": template_type,
                        "template_type": template_type,
                        "similarity": result["similarity"],
                        "r_code": r_code,
                        "path": result["metadata"].get("file_path", ""),
                        "dataset_name": template_data.get("dataset_name", ""),
                        "r_libraries": template_data.get("r_libraries", []),
                        "validated": template_data.get("validated", False)
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
            return []

    def _get_template_from_vector_metadata(self, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get template data from vector store metadata"""
        try:
            file_path = metadata.get("file_path", "")
            if not file_path:
                return None

            # Simple path resolution - try direct path first
            full_path = os.path.join(self.templates_dir, file_path)
            
            # If not found, try common subdirectories
            if not os.path.exists(full_path):
                for subdir in ["fda_templates", "user_templates"]:
                    alt_path = os.path.join(self.templates_dir, subdir, os.path.basename(file_path))
                    if os.path.exists(alt_path):
                        full_path = alt_path
                        break

            if not os.path.exists(full_path):
                logger.warning(f"Template file not found: {full_path}")
                return None

            with open(full_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)

            return template_data
        except Exception as e:
            logger.error(f"Error loading template from vector metadata: {str(e)}")
            return None

    def _ensure_vector_store_sync(self):
        """Ensure vector store is synchronized with template index"""
        try:
            # Get counts
            vector_count = len(vector_store.embeddings)

            # Count existing templates
            existing_templates = []
            for template in self.template_index.get("templates", []):
                file_path = template.get("path", "")
                if file_path:
                    full_path = os.path.join(self.templates_dir, file_path)
                    if os.path.exists(full_path):
                        existing_templates.append(template)

            existing_template_count = len(existing_templates)

            logger.info(f"Vector store: {vector_count} items, Existing templates: {existing_template_count} items")

            # Check if vector store is recent (within 24 hours)
            if vector_store.is_recent(24):
                logger.info("Vector store is recent - skipping rebuild")
                return

            # If counts don't match significantly, rebuild
            if vector_count < existing_template_count * 0.9:
                logger.warning(f"Vector store outdated ({vector_count} vs {existing_template_count}). Rebuilding...")
                self._rebuild_vector_store(existing_templates)
            else:
                logger.info("Vector store is synchronized")

        except Exception as e:
            logger.error(f"Error checking vector store sync: {str(e)}")
            self.use_vector_search = False

    def _rebuild_vector_store(self, existing_templates: List[Dict[str, Any]]):
        """Rebuild vector store from existing templates"""
        try:
            logger.info(f"Starting vector store rebuild for {len(existing_templates)} templates...")

            # Clear existing vector store
            vector_store.embeddings.clear()
            vector_store.metadata.clear()

            successful_count = 0

            for template in existing_templates:
                try:
                    template_id = template.get("id")
                    if not template_id:
                        continue

                    # Create search text from template metadata
                    title = template.get("title", "")
                    template_type = template.get("type", "")
                    keywords = template.get("keywords", [])

                    # Combine text for embedding
                    search_text = f"{title} {template_type} {' '.join(keywords)}"

                    # Generate embedding
                    embedding = self.llm_client.generate_embedding(search_text)

                    # Add to vector store
                    vector_store.add(
                        id=template_id,
                        embedding=embedding,
                        metadata={
                            "title": title,
                            "type": template_type,
                            "keywords": keywords,
                            "file_path": template.get("path", "")
                        }
                    )

                    successful_count += 1

                except Exception as e:
                    logger.warning(f"Failed to process template {template.get('id', 'unknown')}: {str(e)}")
                    continue

            logger.info(f"Vector store rebuild complete: {successful_count}/{len(existing_templates)} templates processed")

        except Exception as e:
            logger.error(f"Error rebuilding vector store: {str(e)}")
            self.use_vector_search = False

    def _cleanup_template_index(self):
        """Remove non-existent templates from the index"""
        try:
            templates = self.template_index.get("templates", [])
            existing_templates = []
            removed_count = 0

            for template in templates:
                file_path = template.get("path", "")
                if file_path:
                    full_path = os.path.join(self.templates_dir, file_path)
                    if os.path.exists(full_path):
                        existing_templates.append(template)
                    else:
                        removed_count += 1
                else:
                    removed_count += 1

            if removed_count > 0:
                logger.info(f"Cleaned up template index: removed {removed_count} non-existent templates")
                self.template_index["templates"] = existing_templates
            else:
                logger.info("Template index is clean - all templates exist")

        except Exception as e:
            logger.error(f"Error cleaning up template index: {str(e)}")

# Create a singleton instance
template_manager = TemplateManager()
