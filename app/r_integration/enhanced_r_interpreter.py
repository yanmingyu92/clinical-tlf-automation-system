"""
Enhanced R Interpreter for R TLF System

This module provides an advanced R execution environment with intelligent error handling,
code debugging, and LLM-assisted fixes.
"""
# Author: Jaime Yan

import os
import re
import subprocess
import tempfile
import logging
import shutil
import json
import time
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path

from app.core.config_loader import config
from app.api.deepseek_client import DeepSeekClient

# Configure logging
logger = logging.getLogger(__name__)

class EnhancedRInterpreter:
    """Enhanced R Interpreter class with intelligent error handling"""
    
    def __init__(self, session_context=None):
        """Initialize the Enhanced R Interpreter with optional session context"""
        self.deepseek_client = DeepSeekClient()
        self.r_executable = "Rscript"  # Default fallback
        self.dev_mode = not self._check_r_installed()
        self.debug_mode = config.get("r_interpreter.debug_mode", True)
        self.auto_fix = config.get("r_interpreter.auto_fix", False)  # Disabled by default
        self.max_fix_attempts = config.get("r_interpreter.max_fix_attempts", 1)  # Reduced attempts

        # Use session context if provided, otherwise use defaults
        if session_context:
            self.session_id = session_context.get('execution_id', f"r_session_{int(time.time())}")
            self.session_dir = session_context.get('session_directory', None)
            self.work_dir = session_context.get('work_dir', config.get("paths.output_dir", "./output"))

            # If session_dir is provided, use it directly
            if self.session_dir:
                self.work_dir = os.path.dirname(self.session_dir)  # Parent directory
            else:
                self.session_dir = os.path.join(self.work_dir, self.session_id)
        else:
            # Default behavior for backward compatibility
            self.work_dir = config.get("paths.output_dir", "./output")
            self.session_id = f"r_session_{int(time.time())}"
            self.session_dir = os.path.join(self.work_dir, self.session_id)

        # Create session directory if it doesn't exist
        os.makedirs(self.session_dir, exist_ok=True)
        logger.info(f"📁 R Interpreter session directory: {self.session_dir}")

        # Initialize error patterns for common R errors
        self.error_patterns = self._init_error_patterns()

        # Store execution history
        self.execution_history = []
    
    def _check_r_installed(self) -> bool:
        """
        Check if R is installed, prioritizing system R over conda R

        Returns:
            True if R is installed, False otherwise
        """
        try:
            logger.info("Checking for R installation...")

            # Priority order: System R > PATH R > Conda R
            r_paths_to_check = [
                # System R installations (Windows) - including the newly installed version
                r"C:\Program Files\R\R-4.3.3\bin\Rscript.exe",
                r"C:\Program Files\R\R-4.4.0\bin\Rscript.exe",
                r"C:\Program Files\R\R-4.3.0\bin\Rscript.exe",
                r"C:\Program Files\R\R-4.2.0\bin\Rscript.exe",
                r"C:\Program Files\R\R-4.1.0\bin\Rscript.exe",
                # PATH R (could be system or conda)
                "Rscript"
            ]

            for r_path in r_paths_to_check:
                try:
                    logger.info(f"Testing R path: {r_path}")
                    r_version = subprocess.run(
                        [r_path, "--version"],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=10
                    )

                    if r_version.returncode == 0:
                        version_info = r_version.stderr.strip()
                        logger.info(f"✅ R installation found: {version_info}")
                        logger.info(f"✅ Using R executable: {r_path}")

                        # Store the working R path for subprocess execution
                        self.r_executable = r_path
                        return True
                    else:
                        logger.debug(f"❌ R path failed: {r_path}")

                except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
                    logger.debug(f"❌ R path error {r_path}: {str(e)}")
                    continue

            logger.error("❌ No working R installation found")
            logger.warning("⚠️ Development mode enabled - continuing without R")
            return False

        except Exception as e:
            logger.error(f"Error checking for R installation: {str(e)}", exc_info=True)
            logger.warning("Development mode enabled - continuing without R")
            return False
    
    def _init_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize error patterns for common R errors
        
        Returns:
            Dictionary of error patterns and their fixes
        """
        return {
            # Package not installed
            "could not find function": {
                "regex": r"could not find function \"([^\"]+)\"",
                "fix_template": "install.packages(\"{package}\", repos=\"https://cloud.r-project.org\")\nlibrary({package})",
                "extract_vars": lambda match: {"package": self._guess_package_from_function(match.group(1))}
            },
            # Package not loaded
            "no package called": {
                "regex": r"there is no package called '([^']+)'",
                "fix_template": "install.packages(\"{package}\", repos=\"https://cloud.r-project.org\")\nlibrary({package})",
                "extract_vars": lambda match: {"package": match.group(1)}
            },
            # Undefined variable
            "object not found": {
                "regex": r"object '([^']+)' not found",
                "fix_template": "# Creating a placeholder for the missing object\n{object} <- NA",
                "extract_vars": lambda match: {"object": match.group(1)}
            },
            # Syntax error in function call
            "argument is missing": {
                "regex": r"argument \"([^\"]+)\" is missing, with no default",
                "fix_suggestion": "Check function call - missing required argument"
            },
            # Column not in dataframe
            "column not found": {
                "regex": r"Column '([^']+)' not found",
                "fix_suggestion": "Verify column name exists in dataframe"
            },
            # File not found
            "cannot open file": {
                "regex": r"cannot open (file|the connection) '([^']+)'",
                "fix_suggestion": "Check file path - file may not exist",
                "extract_vars": lambda match: {"file_path": match.group(2)}
            },
            # Parsing error
            "parsing error": {
                "regex": r"parse error: ([^\n]+)",
                "fix_suggestion": "Syntax error in R code"
            }
        }
    
    def _guess_package_from_function(self, function_name: str) -> str:
        """
        Guess the package name from a function name
        
        Args:
            function_name: Function name
            
        Returns:
            Guessed package name
        """
        # Common R function to package mapping
        function_to_package = {
            "ggplot": "ggplot2",
            "theme_": "ggplot2",
            "geom_": "ggplot2",
            "aes": "ggplot2",
            "read_": "readr",
            "tibble": "tibble",
            "mutate": "dplyr",
            "filter": "dplyr",
            "select": "dplyr",
            "group_by": "dplyr",
            "summarize": "dplyr",
            "summarise": "dplyr",
            "arrange": "dplyr",
            "join": "dplyr",
            "rtf_": "r2rtf",
            "read_sas": "haven",
            "read_spss": "haven",
            "read_stata": "haven"
        }
        
        for func_prefix, package in function_to_package.items():
            if function_name.startswith(func_prefix):
                return package
        
        # Default to the function name as package name
        return function_name
    
    def _diagnose_error(self, error_output: str) -> Dict[str, Any]:
        """
        Diagnose an R error and suggest a fix
        
        Args:
            error_output: Error output from R
            
        Returns:
            Dictionary with error diagnosis and fix suggestion
        """
        for error_type, pattern_info in self.error_patterns.items():
            match = re.search(pattern_info["regex"], error_output)
            if match:
                diagnosis = {
                    "error_type": error_type,
                    "matched_text": match.group(0)
                }
                
                # Add fix template if available
                if "fix_template" in pattern_info:
                    if "extract_vars" in pattern_info:
                        vars_dict = pattern_info["extract_vars"](match)
                        diagnosis["fix"] = pattern_info["fix_template"].format(**vars_dict)
                        diagnosis["extracted_vars"] = vars_dict
                    else:
                        diagnosis["fix"] = pattern_info["fix_template"]
                
                # Add fix suggestion if available
                if "fix_suggestion" in pattern_info:
                    diagnosis["fix_suggestion"] = pattern_info["fix_suggestion"]
                
                return diagnosis
        
        # If no pattern matches, use LLM to suggest a fix
        return self._get_llm_error_diagnosis(error_output)
    
    def _get_llm_error_diagnosis(self, error_output: str) -> Dict[str, Any]:
        """
        Use LLM to diagnose an R error and suggest a fix
        
        Args:
            error_output: Error output from R
            
        Returns:
            Dictionary with error diagnosis and fix suggestion
        """
        if self.dev_mode or not self.auto_fix:
            return {
                "error_type": "unknown",
                "matched_text": error_output,
                "fix_suggestion": "Unable to diagnose error in development mode"
            }
        
        prompt = f"""You are an expert R programmer. Please analyze the following R error message and suggest a fix:

```
{error_output}
```

Response Format:
{{
  "error_type": "brief description of the error type",
  "root_cause": "detailed explanation of what caused the error",
  "fix": "R code that would fix the issue",
  "explanation": "explanation of why this fix works"
}}

Return only the JSON, no additional text or markdown formatting.
"""
        
        try:
            response = self.deepseek_client.generate_text(prompt)
            
            # Extract JSON from response
            import json
            import re
            
            # Try to find a JSON block in the response
            json_match = re.search(r'{.*}', response, re.DOTALL)
            if json_match:
                diagnosis = json.loads(json_match.group(0))
                return diagnosis
            else:
                return {
                    "error_type": "unknown",
                    "matched_text": error_output,
                    "fix_suggestion": "LLM did not return valid JSON"
                }
        except Exception as e:
            logger.error(f"Error getting LLM diagnosis: {str(e)}", exc_info=True)
            return {
                "error_type": "unknown",
                "matched_text": error_output,
                "fix_suggestion": "Error connecting to LLM API"
            }
    
    def _apply_fix(self, r_code: str, diagnosis: Dict[str, Any]) -> str:
        """
        Apply a fix to R code based on diagnosis
        
        Args:
            r_code: Original R code
            diagnosis: Error diagnosis
            
        Returns:
            Fixed R code
        """
        # If we have a direct fix, prepend it to the R code
        if "fix" in diagnosis:
            # Check if fix should be applied at the beginning
            if diagnosis.get("error_type") in ["could not find function", "no package called"]:
                # Prepend library loading
                fixed_code = diagnosis["fix"] + "\n\n" + r_code
            else:
                # For other cases, request LLM to merge the fix properly
                fixed_code = self._get_llm_code_fix(r_code, diagnosis)
            
            return fixed_code
        else:
            # Request LLM to fix the code
            return self._get_llm_code_fix(r_code, diagnosis)
    
    def _get_llm_code_fix(self, r_code: str, diagnosis: Dict[str, Any]) -> str:
        """
        Use LLM to fix R code based on error diagnosis
        
        Args:
            r_code: Original R code
            diagnosis: Error diagnosis
            
        Returns:
            Fixed R code
        """
        if self.dev_mode or not self.auto_fix:
            return r_code
        
        prompt = f"""You are an expert R programmer. Fix the following R code that has an error.

Original R Code:
```r
{r_code}
```

Error Information:
{json.dumps(diagnosis, indent=2)}

Please provide the complete fixed version of the code without any explanations.
Return only the fixed R code, nothing else.
"""
        
        try:
            response = self.deepseek_client.generate_text(prompt)
            
            # Extract code from response (in case LLM adds explanations)
            import re
            code_match = re.search(r'```r?\n(.*?)```', response, re.DOTALL)
            if code_match:
                fixed_code = code_match.group(1).strip()
                return fixed_code
            else:
                # If no code block is found, return the entire response
                return response.strip()
        except Exception as e:
            logger.error(f"Error getting LLM code fix: {str(e)}", exc_info=True)
            return r_code
    
    def execute_code(self, r_code: str, dataset_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute R code with intelligent error handling and fix suggestions
        
        Args:
            r_code: R code to execute
            dataset_path: Optional path to dataset to load
            
        Returns:
            Dictionary with execution results and diagnostics
        """
        if self.dev_mode:
            logger.info("Running in development mode - skipping R execution")
            return {
                "success": True,
                "result": "Development mode - R execution skipped",
                "plots": []
            }
        
        # Add to execution history
        self.execution_history.append({"code": r_code, "dataset": dataset_path})
        
        # Record execution start time
        start_time = time.time()
        
        try:
            # Create a temporary directory for this execution
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create files for code, output, and error
                script_path = os.path.join(temp_dir, "script.R")
                output_path = os.path.join(temp_dir, "output.txt")
                error_path = os.path.join(temp_dir, "error.txt")
                
                # If dataset path is provided, add code to load it
                if dataset_path:
                    dataset_load_code = self._generate_dataset_load_code(dataset_path)
                    full_code = dataset_load_code + "\n\n" + r_code
                else:
                    full_code = r_code

                # Prepend session directory setup to ensure files are saved correctly
                session_setup_code = f'''
# Set working directory to session directory for proper file isolation
setwd("{self.session_dir.replace(os.sep, "/")}")
cat("📁 Working directory set to:", getwd(), "\\n")

# Create session directory if it doesn't exist
if (!dir.exists("{self.session_dir.replace(os.sep, "/")}")) {{
  dir.create("{self.session_dir.replace(os.sep, "/")}", recursive = TRUE)
  cat("📁 Created session directory\\n")
}}

'''
                full_code = session_setup_code + full_code
                
                # Write R code to file
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(full_code)
                
                # First execution attempt
                result = self._execute_r_script(script_path, output_path, error_path)
                
                # No auto-fix - return errors immediately for user to handle
                # If there's an error, provide helpful context for manual fixing
                if not result["success"]:
                    # Add helpful error context
                    result["error_context"] = {
                        "code_executed": full_code,
                        "suggestion": "Use the 'Ask Assistant to Modify' button to get help fixing this error",
                        "common_fixes": self._get_common_fixes_for_error(result.get("error", ""))
                    }
                
                # Record execution end time
                end_time = time.time()
                result["execution_time"] = end_time - start_time
                
                return result
        except Exception as e:
            logger.error(f"Error executing R code: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "plots": [],
                "error_context": {
                    "suggestion": "Check the R code syntax and try again, or ask the assistant for help"
                }
            }

    def _get_common_fixes_for_error(self, error_msg: str) -> List[str]:
        """Get common fixes for R errors"""
        error_msg_lower = error_msg.lower()
        fixes = []

        if "object not found" in error_msg_lower:
            fixes.append("Check if all required libraries are loaded")
            fixes.append("Verify variable names are spelled correctly")
            fixes.append("Make sure data is loaded before using it")

        if "package" in error_msg_lower and "not found" in error_msg_lower:
            fixes.append("Install missing packages with install.packages()")
            fixes.append("Load packages with library()")

        if "syntax" in error_msg_lower or "unexpected" in error_msg_lower:
            fixes.append("Check for missing commas, parentheses, or quotes")
            fixes.append("Verify R syntax is correct")

        if "file" in error_msg_lower and "not found" in error_msg_lower:
            fixes.append("Check file path is correct")
            fixes.append("Verify file exists in the specified location")

        if not fixes:
            fixes.append("Review the error message and R code carefully")
            fixes.append("Ask the assistant to help fix the specific error")

        return fixes
    
    def _execute_r_script(self, script_path: str, output_path: str, error_path: str) -> Dict[str, Any]:
        """
        Execute an R script and capture the output
        
        Args:
            script_path: Path to the R script
            output_path: Path to save stdout
            error_path: Path to save stderr
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Execute R script with output redirection
            with open(output_path, "w", encoding="utf-8") as out_file, \
                 open(error_path, "w", encoding="utf-8") as err_file:
                
                # Allow longer timeout for complex scripts
                # Use the detected R executable instead of hardcoded "Rscript"
                # Set environment to use UTF-8 encoding
                env = os.environ.copy()
                env['LC_ALL'] = 'en_US.UTF-8'
                env['LANG'] = 'en_US.UTF-8'

                result = subprocess.run(
                    [self.r_executable, script_path],
                    stdout=out_file,
                    stderr=err_file,
                    check=False,
                    timeout=60,  # 60 second timeout
                    env=env  # Use UTF-8 environment
                )
            
            # Read output and error
            with open(output_path, "r", encoding="utf-8") as f:
                output = f.read()
            
            with open(error_path, "r", encoding="utf-8") as f:
                error = f.read()
            
            # Check for plots
            plots = []
            plot_extensions = [".png", ".jpg", ".pdf"]
            script_dir = os.path.dirname(script_path)
            
            for file in os.listdir(script_dir):
                for ext in plot_extensions:
                    if file.endswith(ext):
                        # Copy plot to output directory with timestamp
                        plot_path = os.path.join(script_dir, file)
                        dest_name = f"plot_{int(time.time())}_{file}"
                        dest_path = os.path.join(self.session_dir, dest_name)
                        shutil.copy(plot_path, dest_path)
                        plots.append(dest_path)
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "result": output,
                    "plots": plots,
                    "return_code": result.returncode,
                }
            else:
                return {
                    "success": False,
                    "error": error,
                    "output": output,
                    "plots": plots,
                    "return_code": result.returncode,
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Execution timed out (60 seconds)",
                "output": "",
                "plots": [],
                "return_code": -1,
            }
        except Exception as e:
            logger.error(f"Error during R script execution: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "plots": [],
                "return_code": -1,
            }
    
    def _generate_dataset_load_code(self, dataset_path: str) -> str:
        """
        Generate R code to load a dataset
        
        Args:
            dataset_path: Path to the dataset
            
        Returns:
            R code to load the dataset
        """
        file_ext = os.path.splitext(dataset_path)[1].lower()
        
        if file_ext == ".sas7bdat":
            dataset_path_fixed = dataset_path.replace('\\', '/')
            return f"""
# Load required packages
if (!requireNamespace("haven", quietly=TRUE)) {{
  install.packages("haven", repos="https://cloud.r-project.org")
}}

# Load dataset
library(haven)
data <- read_sas("{dataset_path_fixed}")
"""

        elif file_ext == ".rds":
            dataset_path_fixed = dataset_path.replace('\\', '/')
            return f"""
# Load dataset
data <- readRDS("{dataset_path_fixed}")
"""
        else:
            dataset_path_fixed = dataset_path.replace('\\', '/')
            return f"""
# Unknown dataset format, attempting to load
data <- tryCatch({{
  if (file.exists("{dataset_path_fixed}")) {{
    # Try common methods
    if (requireNamespace("haven", quietly=TRUE)) {{
      haven::read_sas("{dataset_path_fixed}")
    }} else {{
      stop("Only SAS7BDAT files are supported")
    }}
  }} else {{
    stop("Dataset file not found: {dataset_path}")
  }}
}}, error = function(e) {{
  message("Error loading dataset: ", e$message)
  NULL
}})
"""
    
    def load_adam_dataset(self, dataset_path: str) -> Dict[str, Any]:
        """
        Load and summarize an ADaM dataset
        
        Args:
            dataset_path: Path to the dataset
            
        Returns:
            Dictionary with dataset information
        """
        if self.dev_mode:
            logger.info(f"Development mode: Using default variables for dataset {dataset_path}")
            dataset_name = os.path.basename(dataset_path).split('.')[0].lower()
            
            # Return mock data based on common dataset types
            if dataset_name == "adsl":
                return {
                    "success": True,
                    "variables": ["USUBJID", "AGE", "SEX", "RACE", "ETHNIC", "ARM", "SITEID", "COUNTRY"],
                    "preview": {
                        "columns": ["USUBJID", "AGE", "SEX", "ARM"],
                        "data": [
                            ["001-001", 45, "M", "Treatment"],
                            ["001-002", 52, "F", "Placebo"],
                            ["001-003", 38, "M", "Treatment"]
                        ]
                    }
                }
            elif dataset_name == "adae":
                return {
                    "success": True,
                    "variables": ["USUBJID", "AEDECOD", "AESEV", "AESOC", "AESER", "ARM", "AESTDT", "AEENDT"],
                    "preview": {
                        "columns": ["USUBJID", "AEDECOD", "AESEV", "ARM"],
                        "data": [
                            ["001-001", "Headache", "Mild", "Treatment"],
                            ["001-002", "Nausea", "Moderate", "Placebo"],
                            ["001-003", "Fatigue", "Mild", "Treatment"]
                        ]
                    }
                }
            elif dataset_name == "advs":
                return {
                    "success": True,
                    "variables": ["USUBJID", "PARAM", "AVAL", "CHG", "VISIT", "VISITNUM", "ARM", "AVISITN"],
                    "preview": {
                        "columns": ["USUBJID", "PARAM", "AVAL", "ARM"],
                        "data": [
                            ["001-001", "Systolic Blood Pressure", 120, "Treatment"],
                            ["001-002", "Diastolic Blood Pressure", 80, "Placebo"],
                            ["001-003", "Heart Rate", 72, "Treatment"]
                        ]
                    }
                }
            else:
                return {
                    "success": True,
                    "variables": ["VAR1", "VAR2", "VAR3", "VAR4", "VAR5"],
                    "preview": {
                        "columns": ["VAR1", "VAR2", "VAR3"],
                        "data": [
                            ["Value1", "Value2", "Value3"],
                            ["Value4", "Value5", "Value6"],
                            ["Value7", "Value8", "Value9"]
                        ]
                    }
                }
        
        # Generate and execute R code to load and summarize the dataset
        r_code = self._generate_dataset_summary_code(dataset_path)
        result = self.execute_code(r_code)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Unknown error")
            }
        
        # Parse the output to extract variables and preview
        output = result.get("result", "")
        
        # Extract variables
        variables = []
        var_section = False
        for line in output.split("\n"):
            if line.startswith("Variables:"):
                var_section = True
                continue
            if var_section and line.strip() and not line.startswith("Preview:"):
                # Extract variable names
                vars_line = line.strip()
                variables.extend([v.strip() for v in vars_line.split(",") if v.strip()])
            if line.startswith("Preview:"):
                var_section = False
        
        # Extract preview data
        preview_data = []
        preview_columns = []
        preview_section = False
        for line in output.split("\n"):
            if line.startswith("Preview:"):
                preview_section = True
                continue
            if preview_section and line.strip():
                # First line contains column names
                if not preview_columns:
                    preview_columns = [col.strip() for col in line.strip().split("|") if col.strip()]
                else:
                    # Data rows
                    row_data = [cell.strip() for cell in line.strip().split("|") if cell.strip()]
                    if row_data and len(row_data) == len(preview_columns):
                        preview_data.append(row_data)
        
        return {
            "success": True,
            "variables": variables,
            "preview": {
                "columns": preview_columns,
                "data": preview_data
            }
        }
    
    def _generate_dataset_summary_code(self, dataset_path: str) -> str:
        """
        Generate R code to summarize a dataset

        Args:
            dataset_path: Path to the dataset

        Returns:
            R code to summarize the dataset
        """
        dataset_path_fixed = dataset_path.replace('\\', '/')
        return f"""
# Load required packages
if (!requireNamespace("haven", quietly=TRUE)) {{
  install.packages("haven", repos="https://cloud.r-project.org")
}}

# Load dataset
data <- NULL
if (file.exists("{dataset_path_fixed}")) {{
  if (grepl("\\\\.sas7bdat$", "{dataset_path}")) {{
    library(haven)
    data <- read_sas("{dataset_path_fixed}")
  
  }} else if (grepl("\\\\.rds$", "{dataset_path}")) {{
    data <- readRDS("{dataset_path_fixed}")
  }} else {{
    stop("Unsupported file format")
  }}
}} else {{
  stop("Dataset file not found")
}}

# Get variables
variables <- names(data)
cat("Variables:", paste(variables, collapse=", "), "\\n")

# Get preview
cat("Preview:\\n")
head_data <- head(data, 5)
# Print column names
cat(paste(names(head_data), collapse=" | "), "\\n")
# Print data rows
for (i in 1:nrow(head_data)) {{
  row_data <- as.character(unlist(head_data[i,]))
  cat(paste(row_data, collapse=" | "), "\\n")
}}
"""
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """
        Get execution history
        
        Returns:
            List of execution history items
        """
        return self.execution_history
    
    def restart(self) -> None:
        """
        Restart the R interpreter session
        """
        # Create a new session ID and directory
        old_session_id = self.session_id
        self.session_id = f"r_session_{int(time.time())}"
        self.session_dir = os.path.join(self.work_dir, self.session_id)
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Clear execution history
        self.execution_history = []
        
        logger.info(f"R interpreter session restarted: {old_session_id} -> {self.session_id}")

# Create a singleton instance
enhanced_r_interpreter = EnhancedRInterpreter() 