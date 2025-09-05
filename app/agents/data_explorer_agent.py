#!/usr/bin/env python3
# Author: Jaime Yan
"""
Data Explorer Agent - Specialized agent for dataset analysis and variable exploration

This agent handles:
- Dataset structure analysis
- Variable name and label extraction
- Data type identification
- Statistical summaries
- Template-data alignment validation
"""

import logging
import pandas as pd
import os
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DataExplorerAgent:
    """Specialized agent for data exploration operations"""
    
    def __init__(self, deepseek_client, r_interpreter):
        """Initialize the Data Explorer Agent"""
        self.deepseek_client = deepseek_client
        self.r_interpreter = r_interpreter
        self.agent_name = "Data Explorer Agent"
        
        logger.info("🔍 Data Explorer Agent initialized")
    
    def explore_dataset(self, dataset_path: str, template_structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Explore dataset and extract basic information

        Args:
            dataset_path: Path to the dataset file
            template_structure: Template structure (not used in current implementation)

        Returns:
            Dataset exploration results with basic info needed by UI
        """
        try:
            start_time = datetime.now()
            logger.info(f"🔍 Exploring dataset: {dataset_path}")

            # Analyze dataset structure - this is all the UI needs
            dataset_info = self._analyze_dataset_structure(dataset_path)

            if not dataset_info.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to analyze dataset: {dataset_info.get('error')}"
                }

            duration = (datetime.now() - start_time).total_seconds()

            # Return only what the UI actually uses
            return {
                "success": True,
                "dataset_info": dataset_info,
                "duration": duration,
                "agent": self.agent_name
            }

        except Exception as e:
            logger.error(f"Error exploring dataset: {str(e)}")
            return {
                "success": False,
                "error": f"Dataset exploration error: {str(e)}"
            }


    
    def _analyze_dataset_structure(self, dataset_path: str) -> Dict[str, Any]:
        """Analyze dataset structure using Python"""
        try:
            logger.info(f"🐍 Analyzing dataset structure: {dataset_path}")

            import pandas as pd

            # Extract dataset name from path
            dataset_name = os.path.basename(dataset_path).split('.')[0]

            # Check if file exists
            if not os.path.exists(dataset_path):
                logger.warning(f"⚠️ Dataset file not found: {dataset_path}")
                return {
                    "success": False,
                    "error": f"Dataset file not found: {dataset_path}",
                    "dataset_name": dataset_name
                }

            # Load dataset based on file extension
            try:
                if dataset_path.endswith('.sas7bdat'):
                    data = pd.read_sas(dataset_path)
                    logger.info(f"✅ Successfully loaded SAS file: {dataset_path}")
                elif dataset_path.endswith('.csv'):
                    data = pd.read_csv(dataset_path)
                    logger.info(f"✅ Successfully loaded CSV file: {dataset_path}")
                else:
                    # Try to infer format
                    data = pd.read_csv(dataset_path)
                    logger.info(f"✅ Successfully loaded file as CSV: {dataset_path}")

            except Exception as e:
                logger.warning(f"⚠️ Failed to load dataset {dataset_path}: {str(e)}")
                return {
                    "success": False,
                    "error": f"Failed to load dataset: {str(e)}",
                    "dataset_name": dataset_name
                }

            # Analyze dataset structure
            dataset_info = {
                "success": True,
                "name": dataset_name,
                "nrows": len(data),
                "ncols": len(data.columns),
                "variables": {},
                "file_path": dataset_path
            }

            # Extract variable information
            for col in data.columns:
                col_data = data[col]

                # Determine data type
                if pd.api.types.is_numeric_dtype(col_data):
                    var_type = "numeric"
                elif pd.api.types.is_datetime64_any_dtype(col_data):
                    var_type = "datetime"
                else:
                    var_type = "character"

                # Get unique values (limit to first 5)
                unique_vals = col_data.dropna().unique()
                if len(unique_vals) > 5:
                    sample_values = unique_vals[:5].tolist()
                else:
                    sample_values = unique_vals.tolist()

                # Convert numpy types to Python types for JSON serialization
                sample_values = [
                    item.item() if hasattr(item, 'item') else str(item)
                    for item in sample_values
                ]

                var_info = {
                    "name": col,
                    "label": col,  # SAS labels not available in pandas, use column name
                    "type": var_type,
                    "unique_values": int(col_data.nunique()),
                    "missing_count": int(col_data.isnull().sum()),
                    "sample_values": sample_values
                }

                dataset_info["variables"][col] = var_info

            logger.info(f"✅ Dataset analysis complete: {dataset_info['nrows']} rows, {dataset_info['ncols']} columns")

            return {
                "success": True,
                "name": dataset_info["name"],
                "nrows": dataset_info["nrows"],
                "ncols": dataset_info["ncols"],
                "variables": dataset_info["variables"],
                "file_path": dataset_info["file_path"]
            }
                
        except Exception as e:
            logger.error(f"Error analyzing dataset structure: {str(e)}")
            return {
                "success": False,
                "error": f"Dataset analysis error: {str(e)}"
            }


