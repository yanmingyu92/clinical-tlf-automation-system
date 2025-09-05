#!/usr/bin/env python3
# Author: Jaime Yan
"""
Add FDA Templates to Vector Database

This script adds high-quality FDA-compliant templates to the vector database
to improve the RAG system's ability to generate high-quality mock templates and R code.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_fda_templates() -> List[Dict[str, Any]]:
    """Load FDA templates from the fda_templates directory"""
    templates = []
    fda_templates_dir = project_root / "templates" / "fda_templates"
    
    if not fda_templates_dir.exists():
        logger.error(f"FDA templates directory not found: {fda_templates_dir}")
        return templates
    
    for template_file in fda_templates_dir.glob("*.json"):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template = json.load(f)
                templates.append(template)
                logger.info(f"Loaded FDA template: {template.get('title', 'Unknown')}")
        except Exception as e:
            logger.error(f"Error loading template {template_file}: {str(e)}")
    
    return templates

def add_templates_to_vector_db(templates: List[Dict[str, Any]]) -> bool:
    """Add templates to the vector database"""
    try:
        from app.rag.template_manager import template_manager
        from app.rag.vector_store import vector_store
        
        logger.info(f"Adding {len(templates)} FDA templates to vector database...")
        
        success_count = 0
        for template in templates:
            try:
                # Generate unique ID for the template
                template_id = template.get('id', f"fda-{success_count:03d}")
                
                # Create search text from template metadata
                title = template.get('title', '')
                template_type = template.get('type', '')
                category = template.get('category', '')
                keywords = template.get('keywords', [])
                fda_compliance = template.get('fda_compliance', {})
                
                # Combine text for embedding
                search_text = f"{title} {template_type} {category} {' '.join(keywords)}"
                if fda_compliance:
                    standard = fda_compliance.get('standard', '')
                    population = fda_compliance.get('population', '')
                    method = fda_compliance.get('statistical_method', '')
                    search_text += f" {standard} {population} {method}"
                
                # Add R code to search text
                r_code = template.get('r_code', {})
                if r_code:
                    libraries = r_code.get('libraries', [])
                    data_prep = r_code.get('data_preparation', [])
                    analysis = r_code.get('statistical_analysis', [])
                    table_gen = r_code.get('table_generation', [])
                    
                    search_text += f" {' '.join(libraries)} {' '.join(data_prep)} {' '.join(analysis)} {' '.join(table_gen)}"
                
                # Generate embedding
                from app.api.deepseek_client import DeepSeekClient
                deepseek_client = DeepSeekClient()
                embedding = deepseek_client.generate_embedding(search_text)
                
                # Add to vector store with correct file path
                vector_store.add(
                    id=template_id,
                    embedding=embedding,
                    metadata={
                        "title": title,
                        "type": template_type,
                        "category": category,
                        "keywords": keywords,
                        "fda_compliance": fda_compliance,
                        "template_data": template,
                        "source": "fda_standards",
                        "file_path": f"fda_templates/{template_id}.json"
                    }
                )
                
                success_count += 1
                logger.info(f"Added template: {title}")
                
            except Exception as e:
                logger.error(f"Error adding template {template.get('title', 'Unknown')}: {str(e)}")
        
        logger.info(f"Successfully added {success_count}/{len(templates)} FDA templates")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error adding templates to vector database: {str(e)}")
        return False

def update_template_index(templates: List[Dict[str, Any]]) -> bool:
    """Update the template index with FDA templates"""
    try:
        from app.rag.template_manager import template_manager
        
        logger.info("Updating template index with FDA templates...")
        
        # Load current index
        index_path = template_manager.index_path
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
        else:
            index_data = {"templates": []}
        
        # Add FDA templates to index
        for template in templates:
            template_id = template.get('id', f"fda-{len(index_data['templates']):03d}")
            template_entry = {
                "id": template_id,
                "title": template.get('title', ''),
                "type": template.get('type', ''),
                "path": f"fda_templates/{template_id}.json",
                "keywords": template.get('keywords', []),
                "category": template.get('category', ''),
                "fda_compliance": template.get('fda_compliance', {}),
                "source": "fda_standards"
            }
            index_data['templates'].append(template_entry)
        
        # Save updated index
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Updated template index with {len(templates)} FDA templates")
        return True
        
    except Exception as e:
        logger.error(f"Error updating template index: {str(e)}")
        return False

def main():
    """Main function for adding FDA templates"""
    try:
        logger.info("Starting FDA template addition process...")
        
        # Load FDA templates
        templates = load_fda_templates()
        if not templates:
            logger.error("No FDA templates found")
            return 1
        
        logger.info(f"Loaded {len(templates)} FDA templates")
        
        # Add templates to vector database
        vector_success = add_templates_to_vector_db(templates)
        if not vector_success:
            logger.error("Failed to add templates to vector database")
            return 1
        
        # Update template index
        index_success = update_template_index(templates)
        if not index_success:
            logger.error("Failed to update template index")
            return 1
        
        logger.info("FDA template addition completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error in FDA template addition process: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 