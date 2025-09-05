"""
Vector Store module for template management

This module provides vector database functionality for storing and retrieving
template embeddings, enabling semantic search of templates.
"""
# Author: Jaime Yan

import os
import json
import pickle
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from app.core.config_loader import config

# Configure logging
logger = logging.getLogger(__name__)

class SimpleVectorStore:
    """
    A simple vector store implementation using numpy arrays.
    For production use, this would be replaced with FAISS, Chroma, or another vector database.
    """
    
    def __init__(self):
        """Initialize the vector store"""
        self.vector_db_dir = config.get("paths.vector_db_dir", "./data/vector_db")
        self.embeddings_file = os.path.join(self.vector_db_dir, "embeddings.pkl")
        self.metadata_file = os.path.join(self.vector_db_dir, "metadata.json")
        self.timestamp_file = os.path.join(self.vector_db_dir, "last_update.txt")

        # Create vector db directory if it doesn't exist
        os.makedirs(self.vector_db_dir, exist_ok=True)

        # Initialize storage
        self.embeddings = {}  # id -> embedding vector
        self.metadata = {}    # id -> metadata dict
        self.last_update = None  # timestamp of last update

        # Load existing data if available
        self._load()
    
    def _load(self):
        """Load embeddings and metadata from disk"""
        try:
            if os.path.exists(self.embeddings_file):
                with open(self.embeddings_file, 'rb') as f:
                    self.embeddings = pickle.load(f)
                logger.info(f"Loaded {len(self.embeddings)} embeddings")

            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded metadata for {len(self.metadata)} items")

            # Load timestamp
            if os.path.exists(self.timestamp_file):
                with open(self.timestamp_file, 'r') as f:
                    self.last_update = f.read().strip()

        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}", exc_info=True)
            # Initialize with empty data if loading fails
            self.embeddings = {}
            self.metadata = {}
            self.last_update = None
    
    def _save(self):
        """Save embeddings and metadata to disk"""
        try:
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump(self.embeddings, f)

            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)

            # Save timestamp
            import time
            current_time = str(int(time.time()))
            with open(self.timestamp_file, 'w') as f:
                f.write(current_time)
            self.last_update = current_time

            logger.info(f"Saved {len(self.embeddings)} embeddings and metadata")
            return True
        except Exception as e:
            logger.error(f"Error saving vector store: {str(e)}", exc_info=True)
            return False

    def is_recent(self, max_age_hours: int = 24) -> bool:
        """Check if vector store was updated recently"""
        if not self.last_update:
            return False

        try:
            import time
            current_time = int(time.time())
            last_update_time = int(self.last_update)
            age_hours = (current_time - last_update_time) / 3600

            return age_hours < max_age_hours
        except:
            return False
    
    def add(self, id: str, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        """
        Add an item to the vector store
        
        Args:
            id: Unique identifier for the item
            embedding: Vector embedding
            metadata: Metadata for the item
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Store as numpy array for efficient computation
            self.embeddings[id] = np.array(embedding, dtype=np.float32)
            self.metadata[id] = metadata
            
            # Save to disk
            return self._save()
        except Exception as e:
            logger.error(f"Error adding item to vector store: {str(e)}", exc_info=True)
            return False
    
    def update(self, id: str, embedding: Optional[List[float]] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update an item in the vector store
        
        Args:
            id: Unique identifier for the item
            embedding: New vector embedding (optional)
            metadata: New metadata (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if id not in self.embeddings:
            logger.warning(f"Item {id} not found in vector store")
            return False
        
        try:
            if embedding is not None:
                self.embeddings[id] = np.array(embedding, dtype=np.float32)
            
            if metadata is not None:
                if id in self.metadata:
                    self.metadata[id].update(metadata)
                else:
                    self.metadata[id] = metadata
            
            # Save to disk
            return self._save()
        except Exception as e:
            logger.error(f"Error updating item in vector store: {str(e)}", exc_info=True)
            return False
    
    def delete(self, id: str) -> bool:
        """
        Delete an item from the vector store
        
        Args:
            id: Unique identifier for the item
            
        Returns:
            True if successful, False otherwise
        """
        if id not in self.embeddings:
            logger.warning(f"Item {id} not found in vector store")
            return False
        
        try:
            if id in self.embeddings:
                del self.embeddings[id]
            
            if id in self.metadata:
                del self.metadata[id]
            
            # Save to disk
            return self._save()
        except Exception as e:
            logger.error(f"Error deleting item from vector store: {str(e)}", exc_info=True)
            return False
    
    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar items using cosine similarity
        
        Args:
            query_embedding: Query vector embedding
            k: Number of results to return
            
        Returns:
            List of search results with id, similarity score, and metadata
        """
        if not self.embeddings:
            logger.warning("Vector store is empty")
            return []
        
        try:
            query_vector = np.array(query_embedding, dtype=np.float32)
            
            # Calculate cosine similarity with all embeddings
            results = []
            for id, embedding in self.embeddings.items():
                # Normalize vectors
                norm_query = np.linalg.norm(query_vector)
                norm_embedding = np.linalg.norm(embedding)
                
                if norm_query > 0 and norm_embedding > 0:
                    # Calculate cosine similarity
                    similarity = np.dot(query_vector, embedding) / (norm_query * norm_embedding)
                    
                    results.append({
                        "id": id,
                        "similarity": float(similarity),
                        "metadata": self.metadata.get(id, {})
                    })
            
            # Sort by similarity (highest first)
            results.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Return top k results
            return results[:k]
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}", exc_info=True)
            return []
    
    def get(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Get an item from the vector store
        
        Args:
            id: Unique identifier for the item
            
        Returns:
            Item data or None if not found
        """
        if id not in self.embeddings:
            return None
        
        return {
            "id": id,
            "embedding": self.embeddings[id].tolist(),
            "metadata": self.metadata.get(id, {})
        }
    
    def list_items(self) -> List[Dict[str, Any]]:
        """
        List all items in the vector store
        
        Returns:
            List of items with id and metadata
        """
        return [
            {"id": id, "metadata": self.metadata.get(id, {})}
            for id in self.embeddings.keys()
        ]

# Create a singleton instance
vector_store = SimpleVectorStore() 