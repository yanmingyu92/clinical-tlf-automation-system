#!/usr/bin/env python3
# Author: Jaime Yan
"""
Code Generator Agent - Specialized agent for R code generation

This agent handles:
- R code generation from templates and data exploration
- Code optimization and best practices
- Integration with clinical data standards
- Code documentation and comments
"""

import logging
import json
import re
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class CodeGeneratorAgent:
    """Specialized agent for R code generation"""
    
    def __init__(self, deepseek_client, vector_store, evaluation_integration=None):
        """Initialize the Code Generator Agent"""
        self.deepseek_client = deepseek_client
        self.vector_store = vector_store
        self.evaluation_integration = evaluation_integration
        self.agent_name = "Code Generator Agent"

        # Initialize code cache
        try:
            from app.core.code_cache import code_cache
            self.code_cache = code_cache
            logger.info("💾 Code cache initialized")
        except ImportError:
            logger.warning("Code cache not available, proceeding without caching")
            self.code_cache = None

        logger.info("💻 Code Generator Agent initialized")
    
    def generate_r_code(self, template_structure: Dict[str, Any], data_exploration: Dict[str, Any], user_query: str, session_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate R code based on template and data exploration with session context

        Args:
            template_structure: Approved template structure
            data_exploration: Data exploration results
            user_query: Original user query
            session_context: Session information for file path management

        Returns:
            Generated R code and metadata
        """
        try:
            start_time = time.time()
            logger.info("💻 Generating R code from template and data exploration with session management")

            # Log session context for debugging
            if session_context:
                logger.info(f"📁 Session context: {session_context}")

            # Check cache first
            if self.code_cache:
                cached_code = self.code_cache.get_similar(
                    template_structure, data_exploration, user_query
                )
                if cached_code:
                    logger.info(f"🎯 Using cached code (success rate: {cached_code.success_rate:.2f})")
                    return {
                        "success": True,
                        "r_code": cached_code.code,
                        "cached": True,
                        "cache_success_rate": cached_code.success_rate,
                        "generation_time": time.time() - start_time,
                        "metadata": cached_code.metadata
                    }

            # Step 1: Retrieve relevant code examples from vector store
            code_examples = self._retrieve_code_examples(user_query, template_structure)
            
            # Step 2: Create comprehensive prompt with session context
            prompt = self._create_code_generation_prompt(
                template_structure, data_exploration, user_query, code_examples, session_context
            )
            
            # Step 3: Generate code using LLM
            response = self.deepseek_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=3000,
                temperature=0.1
            )
            
            if response and response.get("choices"):
                content = response["choices"][0]["message"]["content"]
                
                # Parse the structured response
                code_data = self._parse_code_response(content)
                
                if code_data:
                    duration = time.time() - start_time

                    result = {
                        "success": True,
                        "r_code": code_data["code"],
                        "explanation": code_data.get("explanation", ""),
                        "expected_output": code_data.get("expected_output", ""),
                        "code_quality": self._assess_code_quality(code_data["code"]),
                        "cached": False,
                        "metadata": {
                            "generated_at": datetime.now().isoformat(),
                            "agent": self.agent_name,
                            "template_id": template_structure.get("id"),
                            "user_query": user_query
                        },
                        "duration": duration
                    }

                    # Evaluate result if evaluation integration is available
                    if self.evaluation_integration and result.get("success"):
                        evaluation_result = self.evaluation_integration.evaluate_code_generation(
                            result, template_structure, data_exploration, "enhanced"
                        )
                        
                        # Add evaluation to result
                        result["evaluation"] = evaluation_result

                    # Cache the generated code
                    if self.code_cache:
                        self.code_cache.store(
                            template=template_structure,
                            data=data_exploration,
                            query=user_query,
                            code=code_data["code"],
                            success_rate=1.0,  # Assume success for now
                            execution_time=duration,
                            metadata=result["metadata"]
                        )
                        logger.info("💾 Code cached for future use")

                    return result
                else:
                    return {
                        "success": False,
                        "error": "Failed to parse R code from LLM response"
                    }
            else:
                return {
                    "success": False,
                    "error": "No response from LLM"
                }
                
        except Exception as e:
            logger.error(f"Error generating R code: {str(e)}")
            return {
                "success": False,
                "error": f"Code generation error: {str(e)}"
            }
    
    def modify_r_code(self, current_code: str, modification_request: str, execution_error: Optional[str] = None) -> Dict[str, Any]:
        """
        Modify existing R code based on user request or error
        
        Args:
            current_code: Current R code
            modification_request: User's modification request
            execution_error: Optional execution error to fix
            
        Returns:
            Modified R code
        """
        try:
            start_time = datetime.now()
            logger.info(f"✏️ Modifying R code: {modification_request}")
            
            # Create modification prompt
            prompt = self._create_modification_prompt(current_code, modification_request, execution_error)
            
            response = self.deepseek_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.1
            )
            
            if response and response.get("choices"):
                content = response["choices"][0]["message"]["content"]
                
                # Parse modification response
                modification_data = self._parse_modification_response(content)
                
                if modification_data:
                    duration = (datetime.now() - start_time).total_seconds()
                    
                    return {
                        "success": True,
                        "r_code": modification_data["code"],
                        "explanation": modification_data.get("explanation", ""),
                        "changes_made": modification_data.get("changes", []),
                        "code_quality": self._assess_code_quality(modification_data["code"]),
                        "duration": duration
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to parse modified code from LLM response"
                    }
            else:
                return {
                    "success": False,
                    "error": "No response from LLM for code modification"
                }
                
        except Exception as e:
            logger.error(f"Error modifying R code: {str(e)}")
            return {
                "success": False,
                "error": f"Code modification error: {str(e)}"
            }

    def generate_and_execute_code(self, template_data: Dict[str, Any], dataset_info: Dict[str, Any], r_interpreter) -> Dict[str, Any]:
        """
        Generate R code from template and dataset information, then execute it with iterative fixing

        Args:
            template_data: Template information
            dataset_info: Dataset structure information
            r_interpreter: R interpreter instance

        Returns:
            Dictionary with generation and execution results
        """
        try:
            logger.info("💻 Generating and executing R code from template with iterative fixing")

            max_iterations = 3
            current_iteration = 0

            # First generate the code using the existing method
            generation_result = self.generate_r_code(template_data, dataset_info, "Generate R code for the template")

            if not generation_result.get("success"):
                return generation_result

            # Extract the generated code
            r_code = generation_result.get("r_code", "")
            if not r_code:
                return {
                    "success": False,
                    "error": "No R code was generated"
                }

            execution_history = []

            while current_iteration < max_iterations:
                current_iteration += 1
                logger.info(f"🔄 Execution attempt {current_iteration}/{max_iterations}")

                # Execute the code
                execution_result = r_interpreter.execute_code(r_code)
                execution_history.append({
                    "iteration": current_iteration,
                    "code": r_code,
                    "result": execution_result
                })

                # If successful, return the result
                if execution_result.get("success"):
                    logger.info("✅ Code executed successfully!")
                    return {
                        "success": True,
                        "r_code": r_code,
                        "output": execution_result.get("output", ""),
                        "stderr": execution_result.get("stderr", ""),
                        "html_output": execution_result.get("html_output", ""),
                        "images": execution_result.get("images", []),
                        "generation_details": generation_result,
                        "execution_details": execution_result,
                        "execution_history": execution_history,
                        "iterations": current_iteration
                    }

                # If failed and we have more iterations, try to fix the code
                if current_iteration < max_iterations:
                    logger.warning(f"⚠️ Execution failed, attempting to fix code (iteration {current_iteration})")

                    # Try to fix the code using the existing modify method
                    error_message = execution_result.get("stderr", "Unknown execution error")
                    fix_result = self.modify_r_code(r_code, f"Fix this R code error: {error_message}", error_message)

                    if fix_result.get("success") and fix_result.get("r_code"):
                        r_code = fix_result["r_code"]
                        logger.info("🔧 Code fixed, retrying execution...")
                    else:
                        logger.error("❌ Failed to fix code, stopping iterations")
                        break

            # If we get here, all iterations failed
            return {
                "success": False,
                "error": f"Code execution failed after {max_iterations} attempts",
                "r_code": r_code,
                "execution_history": execution_history,
                "final_error": execution_history[-1]["result"].get("stderr", "Unknown error") if execution_history else "No execution attempts"
            }

        except Exception as e:
            logger.error(f"Error in generate_and_execute_code: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Code generation and execution failed: {str(e)}"
            }

    def _retrieve_code_examples(self, user_query: str, template_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieve relevant code examples from vector store"""
        try:
            if self.vector_store and hasattr(self, 'deepseek_client'):
                # Create search query and generate embedding
                search_query = f"{user_query} {template_structure.get('title', '')} {template_structure.get('layout_type', '')}"

                # Generate embedding for the search query
                query_embedding = self.deepseek_client.generate_embedding(search_query)

                # Search using embedding and correct parameter name 'k'
                results = self.vector_store.search(query_embedding, k=3)

                return [
                    {
                        "code": result.get("r_code", ""),
                        "description": result.get("description", ""),
                        "similarity": result.get("similarity", 0)
                    }
                    for result in results
                ]
            else:
                return []
        except Exception as e:
            logger.error(f"Error retrieving code examples: {str(e)}")
            return []
    
    def _create_code_generation_prompt(self, template_structure: Dict[str, Any], data_exploration: Dict[str, Any], user_query: str, code_examples: List[Dict[str, Any]], session_context: Dict[str, Any] = None) -> str:
        """Create comprehensive prompt for R code generation with session context"""

        # Extract key information
        dataset_name = data_exploration.get("dataset_info", {}).get("name", "unknown")
        relevant_vars = data_exploration.get("relevant_variables", {})
        template_title = template_structure.get("title", "Unknown Table")
        headers = template_structure.get("headers", [])

        # Extract session information for robust file handling
        execution_id = session_context.get('execution_id', 'default') if session_context else 'default'
        output_directory = session_context.get('session_directory', 'output') if session_context else 'output'

        # Format variable information
        primary_vars = relevant_vars.get("primary_variables", [])
        secondary_vars = relevant_vars.get("secondary_variables", [])
        grouping_vars = relevant_vars.get("grouping_variables", [])

        var_info = "Primary Variables:\n"
        for var in primary_vars:
            var_info += f"- {var['name']}: {var['label']} (Role: {var['role']})\n"

        var_info += "\nSecondary Variables:\n"
        for var in secondary_vars:
            var_info += f"- {var['name']}: {var['label']} (Role: {var['role']})\n"

        var_info += "\nGrouping Variables:\n"
        for var in grouping_vars:
            var_info += f"- {var['name']}: {var['label']} (Role: {var['role']})\n"

        # Format code examples
        examples_text = ""
        if code_examples:
            examples_text = "\nRelevant Code Examples:\n"
            for i, example in enumerate(code_examples, 1):
                examples_text += f"\nExample {i}:\n```r\n{example['code'][:500]}...\n```\n"

        # Extract output information with session-specific paths
        output_filename = f"{dataset_name}_{template_structure.get('domain', 'analysis')}_table"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return f"""
You are an expert R programmer specializing in clinical trial data analysis and regulatory reporting.

SESSION CONTEXT:
- Execution ID: {execution_id}
- Output Directory: {output_directory}
- Session Isolation: Enabled

User Request: {user_query}

Template Information:
- Title: {template_title}
- Headers: {headers}
- Layout Type: {template_structure.get('layout_type', 'unknown')}
- Rows Structure: {len(template_structure.get('rows', []))} rows expected

Dataset Information:
- Name: {dataset_name}
- Path: data/adam/{dataset_name}.sas7bdat
- Domain: {template_structure.get('domain', 'unknown')}

{var_info}

{examples_text}

Generate complete, production-ready R code that:
1. Loads the dataset from "data/adam/{dataset_name}.sas7bdat"
2. Understands the template as a PATTERN/HIERARCHY guide, not literal content to copy
3. Uses the actual variable names provided in the variable information
4. Includes proper error handling and data validation
5. Generates professional output suitable for regulatory submission
6. Saves output files for Step 4 display to SESSION DIRECTORY:
   - HTML table: "{output_directory}/{output_filename}_{timestamp}.html"
   - CSV data: "{output_directory}/{output_filename}_{timestamp}.csv"
   - R object: "{output_directory}/{output_filename}_{timestamp}.rds"
7. Uses modern R packages (tidyverse, gt, haven, flextable)

CRITICAL UNDERSTANDING - TEMPLATE INTERPRETATION:
- The template shows the STRUCTURE/HIERARCHY pattern, NOT literal content to copy
- Row labels should come from ACTUAL DATA (e.g., real SOC/PT names from dataset)
- Placeholders (XX, XX.X, XX(XX.X)) represent DATA CALCULATIONS to be performed:
  * XX = count/frequency from actual data
  * XX.X = percentage from actual data
  * XX(XX.X) = count(percentage) from actual data
  * XX.X(XX.X) = mean(SD) from actual data
- Column headers should match template pattern but use actual treatment groups from data
- Hierarchy (indentation, grouping) should follow template pattern with real data values
- NEVER hardcode placeholder values - always calculate from real data

EXAMPLE - WRONG vs RIGHT approach for AE table:
❌ WRONG (literal copying):
ae_table_data <- tibble(
  `System Organ Class / Preferred Term` = c("Any Adverse Event", "  Gastrointestinal disorders", "    Nausea"),
  `Placebo (N=XX)` = c("XX (XX.X)", "XX (XX.X)", "XX (XX.X)")
)

✅ RIGHT (pattern-based with real data):
ae_summary <- adae %>%
  group_by(AESOC, AEDECOD, TRT01A) %>%
  summarise(n = n()) %>%
  mutate(pct = round(n/total_n*100, 1),
         display = paste0(n, " (", pct, ")"))

- MUST save ALL output files to: {output_directory}/
- Include proper clinical table formatting and footnotes
- Handle missing data appropriately
- Set working directory to session directory at start

Respond in this EXACT format:

EXPLANATION:
[Brief explanation of the approach and methodology]

R_CODE:
```r
# Load required libraries
library(tidyverse)
library(haven)
library(gt)
library(flextable)

# Working directory is already configured by the execution environment
cat("Current working directory:", getwd(), "\\n")

# All output files will be saved to the current directory
# No additional directory setup needed

# Load dataset with error handling
tryCatch({{
  {dataset_name}_data <- read_sas("data/adam/{dataset_name}.sas7bdat")
  cat("Dataset loaded successfully: ", nrow({dataset_name}_data), " records\\n")
}}, error = function(e) {{
  stop("Failed to load dataset: ", e$message)
}})

# [Complete data processing and table generation code here]
# Create table that matches the template structure exactly

# Save outputs to session directory for Step 4 display
write_html(final_table, "{output_directory}/{output_filename}_{timestamp}.html")
write_csv(table_data, "{output_directory}/{output_filename}_{timestamp}.csv")
saveRDS(final_table, "{output_directory}/{output_filename}_{timestamp}.rds")

cat("Files saved to session directory: {output_directory}/\\n")

# Display final table
final_table
```

EXPECTED_OUTPUT:
[Description of what the code will produce, including file paths]

OUTPUT_FILES:
- HTML: output/{output_filename}_{timestamp}.html
- CSV: output/{output_filename}_{timestamp}.csv
- RDS: output/{output_filename}_{timestamp}.rds

Generate COMPLETE, EXECUTABLE R code that produces the exact table structure requested and saves all output files.
"""
    
    def _create_modification_prompt(self, current_code: str, modification_request: str, execution_error: Optional[str] = None) -> str:
        """Create prompt for code modification"""
        
        error_section = ""
        if execution_error:
            error_section = f"""
Execution Error to Fix:
{execution_error}

Priority: Fix the error while implementing the requested changes.
"""
        
        return f"""
You are modifying R code for clinical data analysis.

Current R Code:
```r
{current_code}
```

Modification Request: {modification_request}

{error_section}

Provide the modified R code in this EXACT format:

EXPLANATION:
[Brief explanation of changes made]

R_CODE:
```r
[Complete modified R code here]
```

CHANGES:
- [List specific changes made]
- [Each change on a new line]

Ensure the modified code:
1. Maintains clinical data standards
2. Fixes any errors if present
3. Implements the requested changes
4. Remains production-ready and well-documented
"""
    
    def _parse_code_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse code generation response"""
        try:
            # Extract sections using regex
            explanation_match = re.search(r'EXPLANATION:\s*(.*?)\s*R_CODE:', content, re.DOTALL)
            code_match = re.search(r'R_CODE:\s*```r\s*(.*?)\s*```', content, re.DOTALL)
            output_match = re.search(r'EXPECTED_OUTPUT:\s*(.*?)$', content, re.DOTALL)
            
            if code_match:
                return {
                    "explanation": explanation_match.group(1).strip() if explanation_match else "",
                    "code": code_match.group(1).strip(),
                    "expected_output": output_match.group(1).strip() if output_match else ""
                }
            else:
                logger.warning("No R code found in response")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing code response: {str(e)}")
            return None
    
    def _parse_modification_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse code modification response"""
        try:
            # Extract sections
            explanation_match = re.search(r'EXPLANATION:\s*(.*?)\s*R_CODE:', content, re.DOTALL)
            code_match = re.search(r'R_CODE:\s*```r\s*(.*?)\s*```', content, re.DOTALL)
            changes_match = re.search(r'CHANGES:\s*(.*?)$', content, re.DOTALL)
            
            if code_match:
                changes_text = changes_match.group(1).strip() if changes_match else ""
                changes = [
                    line.strip().lstrip('- ') 
                    for line in changes_text.split('\n') 
                    if line.strip() and line.strip().startswith('-')
                ]
                
                return {
                    "explanation": explanation_match.group(1).strip() if explanation_match else "",
                    "code": code_match.group(1).strip(),
                    "changes": changes
                }
            else:
                logger.warning("No R code found in modification response")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing modification response: {str(e)}")
            return None
    
    def _assess_code_quality(self, r_code: str) -> Dict[str, Any]:
        """Assess the quality of generated R code"""
        try:
            quality_score = 100
            issues = []
            suggestions = []
            
            # Check for required libraries
            required_libs = ['tidyverse', 'haven', 'gt']
            for lib in required_libs:
                if f'library({lib})' not in r_code and f'require({lib})' not in r_code:
                    quality_score -= 10
                    issues.append(f"Missing library: {lib}")
            
            # Check for error handling
            if 'try(' not in r_code and 'tryCatch(' not in r_code:
                quality_score -= 5
                suggestions.append("Consider adding error handling")
            
            # Check for comments
            comment_lines = len([line for line in r_code.split('\n') if line.strip().startswith('#')])
            total_lines = len([line for line in r_code.split('\n') if line.strip()])
            
            if total_lines > 0:
                comment_ratio = comment_lines / total_lines
                if comment_ratio < 0.1:
                    quality_score -= 10
                    suggestions.append("Add more comments for clarity")
            
            # Check for data validation
            if 'nrow(' not in r_code and 'dim(' not in r_code:
                quality_score -= 5
                suggestions.append("Consider adding data validation checks")
            
            return {
                "score": max(0, quality_score),
                "issues": issues,
                "suggestions": suggestions,
                "assessment": "excellent" if quality_score >= 90 else "good" if quality_score >= 70 else "needs_improvement"
            }
            
        except Exception as e:
            logger.error(f"Error assessing code quality: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Assessment error: {str(e)}"],
                "suggestions": [],
                "assessment": "unknown"
            }
