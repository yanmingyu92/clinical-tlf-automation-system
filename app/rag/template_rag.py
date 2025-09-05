"""
Template RAG system for retrieving relevant reference templates
Uses vector store and template manager for semantic and keyword search
"""
# Author: Jaime Yan
import os
import re
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config_loader import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class TemplateRAG:
    """
    RAG system for retrieving relevant reference templates based on user queries
    Uses template manager and vector store for semantic and keyword search
    """
    def __init__(self):
        """Initialize the Template RAG system"""
        # Lazy load to avoid circular imports
        self._template_manager = None
        self._vector_store = None
        
    @property
    def template_manager(self):
        """Get template manager (lazy loaded)"""
        if self._template_manager is None:
            from app.rag.template_manager import template_manager
            self._template_manager = template_manager
        return self._template_manager
    
    @property
    def vector_store(self):
        """Get vector store (lazy loaded)"""
        if self._vector_store is None:
            from app.rag.vector_store import vector_store
            self._vector_store = vector_store
        return self._vector_store
    
    @property
    def templates(self):
        """Get templates from template manager"""
        return self.template_manager.template_index.get("templates", [])
    
    def retrieve_relevant_templates(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant templates based on a query
        
        Args:
            query: Query string
            top_k: Maximum number of templates to return (default: 5)
            
        Returns:
            List of relevant templates with similarity scores
        """
        logger.info(f"🔍 RAG: Retrieving templates for query: '{query}'")

        try:
            # Get all templates and do smart matching
            all_templates = self.templates
            logger.info(f"🔍 RAG: Total templates available: {len(all_templates)}")

            if not all_templates:
                logger.warning("🔍 RAG: No templates found!")
                return []

            # Enhanced keyword matching
            query_lower = query.lower()
            query_words = set(query_lower.split())

            scored_results = []

            for template_entry in all_templates:
                try:
                    template_id = template_entry.get("id")
                    if not template_id:
                        continue

                    # Get full template data
                    template_data = self.template_manager.get_template(template_id)
                    if not template_data:
                        continue

                    title = template_data.get("title", "").lower()
                    description = template_data.get("description", "").lower()
                    dataset_name = template_data.get("dataset_name", "").lower()

                    # Calculate relevance score
                    score = 0.0

                    # Title word matching (high weight)
                    title_words = set(title.split())
                    common_title_words = query_words.intersection(title_words)
                    score += len(common_title_words) * 0.3

                    # Specific domain matching
                    if "vital" in query_lower and ("vital" in title or "advs" in dataset_name):
                        score += 0.5
                    if "adverse" in query_lower and ("adverse" in title or "adae" in dataset_name):
                        score += 0.5
                    if "demographic" in query_lower and ("demographic" in title or "adsl" in dataset_name):
                        score += 0.5
                    if "lab" in query_lower and ("lab" in title or "adlb" in dataset_name):
                        score += 0.5

                    # Table type matching
                    if "table" in query_lower and "table" in title:
                        score += 0.2

                    if score > 0:
                        # Convert to expected RAG format
                        rag_result = {
                            "filename": f"{template_id}.json",
                            "metadata": {
                                "title": template_data.get("title", "Untitled Template"),
                                "doc_type": template_data.get("type", "table"),
                                "dataset_name": template_data.get("dataset_name", "unknown"),
                                "keywords": template_data.get("keywords", [])
                            },
                            "similarity": min(score, 1.0),
                            "data": {
                                "rows": template_data.get("data", []),
                                "footers": template_data.get("footnotes", []),
                                "headers": template_data.get("column_headers", [])
                            },
                            "text": self._generate_text_representation(template_data)
                        }
                        scored_results.append(rag_result)

                except Exception as e:
                    logger.warning(f"🔍 RAG: Error processing template {template_id}: {e}")
                    continue

            # Sort by similarity score
            scored_results.sort(key=lambda x: x["similarity"], reverse=True)

            # Return top results
            results = scored_results[:top_k]

            logger.info(f"🔍 RAG: Found {len(results)} relevant templates")
            for i, result in enumerate(results[:3]):
                logger.info(f"🔍 RAG: {i+1}. '{result['metadata']['title']}' (score: {result['similarity']:.3f}, dataset: {result['metadata']['dataset_name']})")

            return results
            
        except Exception as e:
            logger.error(f"Error retrieving relevant templates: {str(e)}", exc_info=True)
            return []
    
    def _generate_text_representation(self, template_data: Dict[str, Any]) -> str:
        """
        Generate a text representation of a template for compatibility
        
        Args:
            template_data: Template data dictionary
            
        Returns:
            Text representation of the template
        """
        try:
            text_parts = []
            
            # Add title
            title = template_data.get("title", "")
            if title:
                text_parts.append(f"Title: {title}")
            
            # Add column headers
            headers = template_data.get("column_headers", [])
            if headers:
                text_parts.append(f"Column Headers: {' | '.join(headers)}")
            
            # Add sample data (first few rows)
            data = template_data.get("data", [])
            if data:
                text_parts.append("Sample Data:")
                for i, row in enumerate(data[:3]):  # First 3 rows
                    if isinstance(row, list):
                        text_parts.append(" | ".join(str(cell) for cell in row))
                    
                if len(data) > 3:
                    text_parts.append("... (more rows)")
            
            # Add footnotes
            footnotes = template_data.get("footnotes", [])
            if footnotes:
                text_parts.append("Footnotes:")
                for footnote in footnotes:
                    text_parts.append(f"- {footnote}")
            
            return "\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"Error generating text representation: {str(e)}")
            return template_data.get("title", "Template")
    
    def generate_enhanced_prompt(self, query: str, relevant_templates: List[Dict[str, Any]]) -> str:
        """
        Generate an enhanced prompt for the LLM using the user query and relevant templates
        
        Args:
            query: User query
            relevant_templates: List of relevant templates
            
        Returns:
            Enhanced prompt
        """
        # Start with system instruction
        prompt = "You are an expert in clinical trial reporting, specializing in Tables, Listings, and Figures (TLFs). "
        prompt += "You will help the user create TLF outputs based on their requirements and the reference templates provided.\n\n"
        
        # Add the user query
        prompt += f"User query: {query}\n\n"
        
        # Add relevant templates
        if relevant_templates:
            prompt += "Here are some relevant reference templates that might help:\n\n"
            
            for i, template in enumerate(relevant_templates, 1):
                prompt += f"TEMPLATE {i} - {template['metadata'].get('title', 'Unknown')}:\n"
                prompt += f"Type: {template['metadata'].get('doc_type', 'Unknown')}\n"
                
                # Add the table structure if available
                if template['data'].get('rows'):
                    prompt += "Content:\n"
                    rows = template['data']['rows']
                    for row in rows[:min(10, len(rows))]:  # Show at most 10 rows
                        if isinstance(row, list):
                            prompt += " | ".join(str(cell) for cell in row) + "\n"
                    
                    if len(rows) > 10:
                        prompt += "... (more rows)\n"
                else:
                    # Otherwise use the plain text (truncated)
                    text = template.get('text', '')
                    prompt += f"Content:\n{text[:500]}...\n"
                
                # Add footnotes if available
                if template['data'].get('footers'):
                    prompt += "Footnotes:\n"
                    for footer in template['data']['footers']:
                        prompt += f"- {footer}\n"
                
                prompt += "\n"
        else:
            prompt += "No specific reference templates found for this query.\n\n"
        
        # Add instructions for the response
        prompt += "\nBased on the user query and these reference templates, please generate a TLF mock that meets the user's requirements. "
        prompt += "The mock should include:\n"
        prompt += "1. A clear title\n"
        prompt += "2. Appropriate column headers\n"
        prompt += "3. Sample data rows\n"
        prompt += "4. Necessary footnotes\n\n"
        prompt += "Format your response as valid HTML that can be directly displayed. Make sure to use <table>, <tr>, <th>, and <td> tags appropriately.\n"
        
        return prompt

# Create a singleton instance for global use
template_rag = TemplateRAG()

if __name__ == "__main__":
    # Test the RAG system
    rag = TemplateRAG()
    
    # Test retrieval
    query = "Adverse events table by treatment group"
    results = rag.retrieve_relevant_templates(query)
    
    print(f"Query: {query}")
    print(f"Found {len(results)} relevant templates:")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['metadata']['title']} (Score: {result['similarity']:.4f})")
    
    # Generate enhanced prompt
    if results:
        prompt = rag.generate_enhanced_prompt(query, results)
        print("\nEnhanced Prompt (first 500 chars):")
        print(prompt[:500] + "...") 