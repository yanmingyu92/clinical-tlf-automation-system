#!/usr/bin/env python
# Author: Jaime Yan
"""
Rebuild Vector Database Script

This script rebuilds the vector database by reindexing all templates.
It's useful after importing new templates or when changing the embedding model.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """Main function for rebuilding the vector database"""
    try:
        # Import template manager
        from app.rag.template_manager import template_manager
        from app.rag.vector_store import vector_store
        
        # Log status
        logger.info("Starting vector database rebuild...")
        logger.info(f"Vector store location: {vector_store.vector_db_dir}")
        
        # Check if the vector DB directory exists
        if not os.path.exists(vector_store.vector_db_dir):
            logger.info(f"Creating vector database directory: {vector_store.vector_db_dir}")
            os.makedirs(vector_store.vector_db_dir, exist_ok=True)
        
        # Reindex all templates
        logger.info("Reindexing templates...")
        result = template_manager.reindex_templates()
        
        if result["success"]:
            logger.info(f"Successfully reindexed {result.get('count', 0)} templates")
            logger.info("Vector database rebuild complete")
        else:
            logger.error(f"Failed to reindex templates: {result.get('error', 'Unknown error')}")
            return 1
        
        return 0
    except Exception as e:
        logger.error(f"Error rebuilding vector database: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 