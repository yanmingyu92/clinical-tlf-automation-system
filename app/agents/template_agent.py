#!/usr/bin/env python3
# Author: Jaime Yan
"""
Template Agent - Specialized agent for mock template generation and modification

This agent handles:
- Mock template generation from natural language
- Template structure modification
- Template validation and improvement
- HTML rendering and formatting
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TemplateAgent:
    """Specialized agent for template operations"""
    
    def __init__(self, deepseek_client, template_manager, evaluation_integration=None):
        """Initialize the Template Agent"""
        self.deepseek_client = deepseek_client
        self.template_manager = template_manager
        self.evaluation_integration = evaluation_integration
        self.agent_name = "Template Agent"
        
        logger.info("📊 Template Agent initialized")
    
    def _infer_dataset_type(self, dataset_name: str) -> str:
        """Infer dataset type from name"""
        
        dataset_lower = dataset_name.lower()
        
        if "ae" in dataset_lower or "adverse" in dataset_lower:
            return "safety_tables"
        elif "eff" in dataset_lower or "efficacy" in dataset_lower:
            return "efficacy_tables"
        elif "demo" in dataset_lower or "demographic" in dataset_lower:
            return "demographics_tables"
        elif "lab" in dataset_lower or "laboratory" in dataset_lower:
            return "safety_tables"
        else:
            return "unknown"

    def generate_mock_template(self, user_query: str, dataset_name: str, tlf_type: str) -> Dict[str, Any]:
        """
        Generate a mock template from user query
        
        Args:
            user_query: Natural language description
            dataset_name: Target dataset
            tlf_type: Type of TLF
            
        Returns:
            Generated template structure
        """
        # Initialize rag_results to avoid scope issues
        rag_results = {}

        try:
            start_time = datetime.now()
            logger.info(f"📊 Generating mock template for: {user_query}")

            # Step 1: Retrieve relevant examples from RAG
            rag_results = self._retrieve_relevant_examples(user_query, dataset_name, tlf_type)

            # Step 2: Create enhanced prompt for template generation
            prompt = self._create_template_generation_prompt(user_query, dataset_name, tlf_type, rag_results)

            # Step 3: Call LLM for template generation
            response = self.deepseek_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3
            )
            
            if response and response.get("choices"):
                content = response["choices"][0]["message"]["content"]
                logger.info(f"🔍 LLM response received: {len(content)} characters")
                logger.info(f"🔍 LLM response preview: {content[:200]}...")

                # Parse the structured response
                template_data = self._parse_template_response(content)
                logger.info(f"🔍 Template data parsed: {template_data is not None}")

                if template_data:
                    # Generate HTML representation
                    html_output = self._generate_template_html(template_data)
                    
                    duration = (datetime.now() - start_time).total_seconds()
                    
                    # Debug logging
                    logger.info(f"🔍 Template response rag_results: {rag_results.get('success') if rag_results else 'None'}")
                    logger.info(f"🔍 Template response rag_results count: {rag_results.get('count', 0) if rag_results else 0}")

                    # Create result object
                    result = {
                        "success": True,
                        "template": {
                            "id": f"template_{int(datetime.now().timestamp())}",
                            "title": template_data.get("title", "Generated Template"),
                            "structure": template_data,
                            "html": html_output,
                            "metadata": {
                                "user_query": user_query,
                                "dataset": dataset_name,
                                "tlf_type": tlf_type,
                                "generated_at": datetime.now().isoformat(),
                                "agent": self.agent_name
                            }
                        },
                        "rag_results": rag_results,
                        "duration": duration
                    }
                    
                    # Evaluate result if evaluation integration is available
                    if self.evaluation_integration and result.get("success"):
                        dataset_info = {
                            "dataset_name": dataset_name,
                            "tlf_type": tlf_type,
                            "dataset_type": self._infer_dataset_type(dataset_name)
                        }
                        
                        evaluation_result = self.evaluation_integration.evaluate_template_generation(
                            result, user_query, dataset_info, "enhanced"
                        )
                        
                        # Add evaluation to result
                        result["evaluation"] = evaluation_result
                    
                    return result
                else:
                    logger.error(f"🔍 Failed to parse template data from LLM response")
                    logger.error(f"🔍 LLM response content: {content}")
                    return {
                        "success": False,
                        "error": "Failed to parse template from LLM response",
                        "rag_results": rag_results  # Include RAG results even on failure
                    }
            else:
                logger.error(f"🔍 No response from LLM: {response}")
                return {
                    "success": False,
                    "error": "No response from LLM",
                    "rag_results": rag_results  # Include RAG results even on failure
                }
                
        except Exception as e:
            logger.error(f"🔍 Exception in generate_mock_template: {str(e)}")
            logger.error(f"🔍 Exception type: {type(e)}")
            import traceback
            logger.error(f"🔍 Exception traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Template generation error: {str(e)}",
                "rag_results": rag_results  # Include RAG results even on exception
            }
    
    def modify_template(self, current_template: Dict[str, Any], modification_request: str) -> Dict[str, Any]:
        """
        Modify an existing template based on user request
        
        Args:
            current_template: Current template structure
            modification_request: User's modification request
            
        Returns:
            Modified template
        """
        try:
            start_time = datetime.now()
            logger.info(f"✏️ Modifying template: {modification_request}")
            
            # Create modification prompt
            prompt = self._create_modification_prompt(current_template, modification_request)
            
            # Call LLM for modification
            response = self.deepseek_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.2
            )
            
            if response and response.get("choices"):
                content = response["choices"][0]["message"]["content"]
                
                # Parse modification response
                modification_data = self._parse_modification_response(content, current_template)
                
                if modification_data:
                    # Generate updated HTML
                    html_output = self._generate_template_html(modification_data["structure"])
                    
                    duration = (datetime.now() - start_time).total_seconds()
                    
                    return {
                        "success": True,
                        "template": {
                            **current_template,
                            "structure": modification_data["structure"],
                            "html": html_output,
                            "metadata": {
                                **current_template.get("metadata", {}),
                                "last_modified": datetime.now().isoformat(),
                                "modification_request": modification_request
                            }
                        },
                        "changes_made": modification_data.get("changes", []),
                        "duration": duration
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to parse modification from LLM response"
                    }
            else:
                return {
                    "success": False,
                    "error": "No response from LLM for modification"
                }
                
        except Exception as e:
            logger.error(f"Error modifying template: {str(e)}")
            return {
                "success": False,
                "error": f"Template modification error: {str(e)}"
            }
    
    def _retrieve_relevant_examples(self, user_query: str, dataset_name: str, tlf_type: str) -> Dict[str, Any]:
        """Retrieve relevant examples from RAG system"""
        try:
            logger.info(f"🔍 Retrieving relevant examples for: {user_query}")

            # Search in template manager
            search_query = f"{user_query} {dataset_name} {tlf_type}"
            logger.info(f"🔍 Search query: {search_query}")
            search_results = self.template_manager.search_templates(search_query, filter_type="All")
            logger.info(f"🔍 Search results count: {len(search_results)}")
            logger.info(f"🔍 Search results: {str(search_results)[:200] if search_results else 'No results'}")

            # Format results for display (limit to top 3)
            examples = []
            for result in search_results[:3]:
                # Extract template structure information
                template_structure = self._extract_template_structure(result)

                examples.append({
                    "title": result.get("title", "Unknown Template"),
                    "description": result.get("description", "No description available"),
                    "similarity": result.get("similarity", 0),
                    "template_type": result.get("template_type", "unknown"),
                    "template_structure": template_structure,
                    "key_features": self._extract_key_features(result),
                    "r_code_preview": (str(result.get("r_code", ""))[:150] + "..." if result.get("r_code") else "No R code available"),
                    "full_r_code": result.get("r_code", "")
                })

            result = {
                "success": True,
                "query": search_query,
                "examples": examples,
                "count": len(examples)
            }
            logger.info(f"🔍 Final RAG result: success={result['success']}, count={result['count']}")
            return result

        except Exception as e:
            logger.error(f"Error retrieving RAG examples: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "examples": [],
                "count": 0
            }


    def _extract_template_structure(self, template_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract template structure information from search result"""
        try:
            # Try to extract table structure from the template data
            structure = {
                "columns": [],
                "rows_count": 0,
                "table_type": "unknown",
                "has_headers": False,
                "summary": "",
                "mock_preview": ""
            }

            # Determine table type from title
            title = template_result.get("title", "").lower()
            if "demographic" in title or "baseline" in title:
                structure["table_type"] = "Demographics"
            elif "adverse" in title or "ae" in title:
                structure["table_type"] = "Adverse Events"
            elif "vital" in title or "sign" in title:
                structure["table_type"] = "Vital Signs"
            elif "efficacy" in title or "endpoint" in title:
                structure["table_type"] = "Efficacy"
            elif "listing" in title:
                structure["table_type"] = "Listing"
            elif "figure" in title or "plot" in title:
                structure["table_type"] = "Figure"
            else:
                structure["table_type"] = "Summary Table"

            # Check for different template data formats

            # Format 1: Direct column_headers and data structure
            if "column_headers" in template_result and "data" in template_result:
                structure["columns"] = template_result["column_headers"][:8]  # Limit to first 8 columns
                structure["has_headers"] = True

                if isinstance(template_result["data"], list):
                    structure["rows_count"] = len(template_result["data"])

                    # Create mock preview
                    headers = template_result["column_headers"][:4]  # Show first 4 columns
                    data_rows = template_result["data"][:3]  # Show first 3 rows

                    preview_lines = []
                    if headers:
                        preview_lines.append(" | ".join(headers))
                        preview_lines.append("-" * len(" | ".join(headers)))

                    for row in data_rows:
                        if isinstance(row, list):
                            row_data = row[:len(headers)]  # Match header count
                            preview_lines.append(" | ".join(str(cell) for cell in row_data))

                    if len(template_result["data"]) > 3:
                        preview_lines.append("...")

                    structure["mock_preview"] = "\n".join(preview_lines)

            # Format 2: table_structure with metadata
            elif "table_structure" in template_result:
                table_struct = template_result["table_structure"]
                if isinstance(table_struct, dict):
                    # Extract column information from table_structure
                    if "group_columns" in table_struct:
                        structure["columns"] = table_struct["group_columns"][:8]
                        structure["has_headers"] = True

                    # Add table type info from structure
                    if table_struct.get("table_type"):
                        structure["table_type"] = table_struct["table_type"].title()

                    # Create a basic preview from structure info
                    if structure["columns"]:
                        structure["mock_preview"] = f"Grouped by: {', '.join(structure['columns'][:3])}"
                        if table_struct.get("has_statistics"):
                            structure["mock_preview"] += "\nIncludes: Statistical summaries"
                        if table_struct.get("has_percentages"):
                            structure["mock_preview"] += ", Percentages"

            # Format 3: Nested data structure
            elif "data" in template_result and isinstance(template_result["data"], dict):
                data = template_result["data"]

                # Extract columns if available
                if "columns" in data:
                    structure["columns"] = data["columns"][:8]
                    structure["has_headers"] = True
                elif "rows" in data and data["rows"]:
                    # Try to infer columns from first row
                    first_row = data["rows"][0] if data["rows"] else []
                    if isinstance(first_row, list):
                        structure["columns"] = [f"Column {i+1}" for i in range(min(len(first_row), 8))]

                # Count rows
                if "rows" in data:
                    structure["rows_count"] = len(data["rows"])

            # Create a summary
            if structure["columns"]:
                col_summary = f"{len(structure['columns'])} columns"
                if len(structure["columns"]) > 0:
                    col_summary += f" ({', '.join(structure['columns'][:3])}{'...' if len(structure['columns']) > 3 else ''})"
                structure["summary"] = f"{structure['table_type']} with {col_summary}"
                if structure["rows_count"] > 0:
                    structure["summary"] += f" and {structure['rows_count']} rows"
            else:
                structure["summary"] = f"{structure['table_type']} template"

            return structure

        except Exception as e:
            logger.error(f"Error extracting template structure: {str(e)}")
            return {
                "columns": [],
                "rows_count": 0,
                "table_type": "unknown",
                "has_headers": False,
                "summary": "Template structure unavailable",
                "mock_preview": ""
            }

    def _extract_key_features(self, template_result: Dict[str, Any]) -> List[str]:
        """Extract key features from template result"""
        try:
            features = []

            # Analyze title and description for key features
            title = template_result.get("title", "").lower()
            description = template_result.get("description", "").lower()
            text_content = f"{title} {description}"

            # Statistical features
            if any(term in text_content for term in ["mean", "median", "std", "statistics"]):
                features.append("📊 Descriptive Statistics")

            if any(term in text_content for term in ["p-value", "confidence", "test", "significant"]):
                features.append("📈 Statistical Testing")

            if any(term in text_content for term in ["n (%)", "count", "frequency"]):
                features.append("🔢 Frequency Counts")

            # Clinical features
            if any(term in text_content for term in ["baseline", "screening", "demographic"]):
                features.append("👥 Baseline Characteristics")

            if any(term in text_content for term in ["adverse", "safety", "ae"]):
                features.append("⚠️ Safety Data")

            if any(term in text_content for term in ["vital", "sign", "height", "weight", "bp"]):
                features.append("💓 Vital Signs")

            if any(term in text_content for term in ["efficacy", "endpoint", "outcome"]):
                features.append("🎯 Efficacy Measures")

            # Format features
            if any(term in text_content for term in ["by treatment", "by group", "treatment group"]):
                features.append("🔄 By Treatment Group")

            if any(term in text_content for term in ["visit", "time", "week", "day"]):
                features.append("📅 By Visit/Time")

            # Limit to top 4 features
            return features[:4] if features else ["📋 Clinical Table"]

        except Exception as e:
            logger.error(f"Error extracting key features: {str(e)}")
            return ["📋 Clinical Table"]

    def _create_template_generation_prompt(self, user_query: str, dataset_name: str, tlf_type: str, rag_results: Dict[str, Any] = None) -> str:
        """Create prompt for template generation"""

        # Add RAG examples if available
        rag_section = ""
        if rag_results and rag_results.get("success") and rag_results.get("examples"):
            rag_section = "\n=== RELEVANT TEMPLATE EXAMPLES FROM KNOWLEDGE BASE ===\n"
            examples = rag_results["examples"]
            if isinstance(examples, list):
                examples_to_show = examples[:2]  # Show top 2
            else:
                examples_to_show = []

            for i, example in enumerate(examples_to_show, 1):
                template_structure = example.get('template_structure', {})
                key_features = example.get('key_features', [])

                # Safely handle column structure
                columns = template_structure.get('columns', [])
                if isinstance(columns, list):
                    column_str = ', '.join(columns[:6])
                else:
                    column_str = 'Not available'
                
                rag_section += f"""
EXAMPLE {i}: {example['title']}
- Description: {example['description']}
- Template Type: {example['template_type']}
- Similarity Score: {example['similarity']:.2f}
- Template Structure: {template_structure.get('summary', 'Not available')}
- Key Features: {', '.join(key_features) if key_features else 'Not specified'}
- Column Structure: {column_str}
- R Code Approach: {str(example.get('r_code_preview', ''))[:100]}...

"""

        return f"""
You are an expert clinical data analyst creating professional mock templates for regulatory submissions.

User Request: {user_query}
Dataset: {dataset_name}
TLF Type: {tlf_type}
{rag_section}
Create a professional mock template structure. Respond in this EXACT JSON format:

{{
    "title": "Professional table title following regulatory standards",
    "layout_type": "by_treatment_group|by_category|summary|listing",
    "headers": ["Column 1", "Column 2", "Column 3"],
    "rows": [
        {{"label": "Row 1", "data": ["XX", "XX.X", "XX.XX"]}},
        {{"label": "Row 2", "data": ["XXX", "XX.X%", "XX (XX.X)"]}}
    ],
    "footnotes": ["Footnote 1", "Footnote 2"],
    "styling": {{
        "table_class": "clinical-table",
        "header_style": "bold",
        "alignment": "center"
    }}
}}

CRITICAL REQUIREMENTS:
- Professional clinical trial table format
- Appropriate for regulatory submission
- Clear, descriptive headers
- **MOCK DATA ONLY**: Use placeholder values like XX, XX.X, XX.XX, XXX, etc.
- **NO REAL NUMBERS**: Do not use actual numeric values from examples
- **PLACEHOLDER PATTERNS**:
  * Counts: XX, XXX
  * Percentages: XX.X%, XX.XX%
  * Statistics: XX.X (XX.X), XX.XX ± XX.XX
  * Sample sizes: N=XX, n=XX
  * P-values: X.XXX, <X.XXX
- Proper footnotes for clarification
- Use realistic clinical terminology but with placeholder data only

IMPORTANT: This is a MOCK template showing STRUCTURE/PATTERN:
- All data values must be placeholders (XX, XX.X, etc.), not real numbers
- Placeholders will be replaced with real calculations during R code generation
- Focus on showing the correct hierarchy, grouping, and statistical pattern
- Row labels should be realistic examples (e.g., real SOC/PT names for AE tables)

Generate ONLY the JSON, no additional text.
"""
    
    def _create_modification_prompt(self, current_template: Dict[str, Any], modification_request: str) -> str:
        """Create prompt for template modification"""
        current_structure = json.dumps(current_template.get("structure", {}), indent=2)
        
        return f"""
You are modifying a clinical table template based on user feedback.

Current Template Structure:
{current_structure}

User Modification Request: {modification_request}

Provide the modified template structure in this EXACT JSON format:

{{
    "structure": {{
        "title": "Updated title if changed",
        "layout_type": "layout type",
        "headers": ["Updated headers"],
        "rows": [
            {{"label": "Row label", "data": ["Updated data"]}}
        ],
        "footnotes": ["Updated footnotes"],
        "styling": {{"table_class": "clinical-table"}}
    }},
    "changes": ["List of specific changes made"]
}}

Make only the requested changes while maintaining professional clinical standards.
Generate ONLY the JSON, no additional text.
"""
    
    def _parse_template_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse template generation response with robust JSON handling"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)

                # Try direct parsing first
                try:
                    template_data = json.loads(json_str)
                    return template_data
                except json.JSONDecodeError as e:
                    logger.warning(f"Direct JSON parsing failed: {str(e)}")

                    # Try to fix common JSON issues
                    fixed_json = self._fix_json_formatting(json_str)
                    if fixed_json:
                        try:
                            template_data = json.loads(fixed_json)
                            logger.info("✅ JSON fixed and parsed successfully")
                            return template_data
                        except json.JSONDecodeError as e2:
                            logger.error(f"Failed to parse fixed JSON: {str(e2)}")

                    return None
            else:
                logger.warning("No JSON found in template response")
                return None
        except Exception as e:
            logger.error(f"Error in template response parsing: {str(e)}")
            return None

    def _fix_json_formatting(self, json_str: str) -> Optional[str]:
        """Fix common JSON formatting issues"""
        try:
            # Fix missing commas in arrays/objects
            # Look for patterns like "}] followed by {"
            json_str = re.sub(r'"\s*}\s*\n\s*]', '"}]', json_str)  # Fix trailing comma in last object
            json_str = re.sub(r'"\s*}\s*\n\s*{', '"}, {', json_str)  # Fix missing comma between objects
            json_str = re.sub(r']\s*}\s*\n\s*{', ']}, {', json_str)  # Fix missing comma after array

            # Fix trailing commas
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing comma before }
            json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing comma before ]

            # Fix missing quotes around keys
            json_str = re.sub(r'(\w+):', r'"\1":', json_str)

            return json_str
        except Exception as e:
            logger.error(f"Error fixing JSON: {str(e)}")
            return None
    
    def _parse_modification_response(self, content: str, current_template: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse modification response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                modification_data = json.loads(json_match.group(0))
                return modification_data
            else:
                logger.warning("No JSON found in modification response")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse modification JSON: {str(e)}")
            return None
    
    def _generate_template_html(self, template_data: Dict[str, Any]) -> str:
        """Generate HTML representation of template"""
        try:
            title = template_data.get("title", "Untitled Template")
            headers = template_data.get("headers", [])
            rows = template_data.get("rows", [])
            footnotes = template_data.get("footnotes", [])
            
            # Build HTML table
            html = f"""
            <div class="clinical-template">
                <h3 class="template-title">{title}</h3>
                <table class="clinical-table">
                    <thead>
                        <tr>
                            {''.join(f'<th>{header}</th>' for header in headers)}
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for row in rows:
                label = row.get("label", "")
                data = row.get("data", [])
                html += f"""
                        <tr>
                            <td class="row-label">{label}</td>
                            {''.join(f'<td>{value}</td>' for value in data)}
                        </tr>
                """
            
            html += """
                    </tbody>
                </table>
            """
            
            if footnotes:
                html += "<div class='footnotes'>"
                for i, footnote in enumerate(footnotes, 1):
                    html += f"<p class='footnote'>{i}. {footnote}</p>"
                html += "</div>"
            
            html += "</div>"
            
            return html
            
        except Exception as e:
            logger.error(f"Error generating template HTML: {str(e)}")
            return f"<div class='error'>Error generating template preview: {str(e)}</div>"
    
    def validate_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate template structure and content"""
        try:
            issues = []
            suggestions = []
            
            # Check required fields
            if not template_data.get("title"):
                issues.append("Missing template title")
            
            if not template_data.get("headers"):
                issues.append("Missing table headers")
            
            if not template_data.get("rows"):
                issues.append("Missing table rows")
            
            # Check data consistency
            headers = template_data.get("headers", [])
            rows = template_data.get("rows", [])
            
            for i, row in enumerate(rows):
                data = row.get("data", [])
                if len(data) != len(headers) - 1:  # -1 for row label column
                    issues.append(f"Row {i+1} data count doesn't match headers")
            
            # Generate suggestions
            if len(headers) < 3:
                suggestions.append("Consider adding more columns for comprehensive analysis")
            
            if len(rows) < 5:
                suggestions.append("Consider adding more rows for better representation")
            
            if not template_data.get("footnotes"):
                suggestions.append("Consider adding footnotes for clarity")
            
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "suggestions": suggestions,
                "score": max(0, 100 - len(issues) * 20 - len(suggestions) * 5)
            }
            
        except Exception as e:
            logger.error(f"Error validating template: {str(e)}")
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "suggestions": [],
                "score": 0
            }
