#!/usr/bin/env python3
# Author: Jaime Yan
"""
Simple R Executor - Clean session directory management
Bypasses complex EnhancedRInterpreter session logic to prevent nested directories
"""

import os
import subprocess
import tempfile
import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SimpleRExecutor:
    """Simple R executor with direct session directory control - no nesting"""
    
    def __init__(self, session_dir: str, execution_id: str = 'default'):
        self.session_dir = session_dir
        self.execution_id = execution_id
        self.interrupt_signal = False
        self.enable_workspace_persistence = False  # Can be enabled for session continuity
        self.workspace_file = os.path.join(session_dir, "session_workspace.RData")

        # Ensure session directory exists
        os.makedirs(session_dir, exist_ok=True)

        # Find R executable
        self.r_executable = self._find_r_executable()

        logger.info(f"📁 Simple R Executor initialized with session directory: {self.session_dir}")
        logger.info(f"⚡ R executable: {self.r_executable}")

        self.available_functions = {
            'execute_r_code': self.execute_r_code,
        }

    def _find_r_executable(self) -> str:
        """Find R executable on the system"""
        # Common R installation paths
        r_paths = [
            "C:\\Program Files\\R\\R-4.3.3\\bin\\Rscript.exe",
            "C:\\Program Files\\R\\R-4.2.3\\bin\\Rscript.exe", 
            "C:\\Program Files\\R\\R-4.1.3\\bin\\Rscript.exe",
            "/usr/bin/Rscript",
            "/usr/local/bin/Rscript",
            "Rscript"  # Try system PATH
        ]
        
        for r_path in r_paths:
            try:
                result = subprocess.run([r_path, "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    logger.info(f"✅ Found R at: {r_path}")
                    return r_path
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                continue
        
        raise RuntimeError("R installation not found. Please install R.")

    def execute_r_code(self, code: str) -> Dict[str, Any]:
        """
        Execute R code with proper session directory isolation
        
        Args:
            code: R code to execute
            
        Returns:
            Dict with execution results
        """
        try:
            # Create working directory setup code (avoid emoji for encoding compatibility)
            # Convert to absolute path for R compatibility
            abs_session_dir = os.path.abspath(self.session_dir).replace(os.sep, "/")
            workspace_file_path = self.workspace_file.replace(os.sep, "/")

            # Add workspace persistence if enabled
            workspace_load_code = ""
            workspace_save_code = ""

            if self.enable_workspace_persistence:
                # Use absolute path and ensure directory exists
                abs_workspace_path = os.path.abspath(self.workspace_file).replace(os.sep, "/")
                workspace_load_code = f'''
# Load previous workspace for session continuity
workspace_file <- "{abs_workspace_path}"
if (file.exists(workspace_file)) {{
    load(workspace_file)
    cat("✅ Previous workspace loaded for session continuity\\n")
}} else {{
    cat("🆕 Starting new R session\\n")
}}
'''
                workspace_save_code = f'''
# Save workspace for session continuity
workspace_file <- "{abs_workspace_path}"
workspace_dir <- dirname(workspace_file)

# Ensure directory exists
if (!dir.exists(workspace_dir)) {{
    dir.create(workspace_dir, recursive = TRUE)
    cat("📁 Created workspace directory\\n")
}}

tryCatch({{
    save.image(file = workspace_file)
    cat("💾 Workspace saved for session continuity\\n")
}}, error = function(e) {{
    cat("⚠️ Warning: Could not save workspace:", e$message, "\\n")
    cat("⚠️ Workspace file path:", workspace_file, "\\n")
    cat("⚠️ Current working directory:", getwd(), "\\n")
}})
'''

            setup_code = f'''
# Set working directory to session directory (no nesting)
setwd("{abs_session_dir}")
cat("Working directory set to:", getwd(), "\\n")

# Ensure we're in the correct directory
if (getwd() != "{abs_session_dir}") {{
    stop("Failed to set working directory")
}}

# CRITICAL FIX: Prevent nested output directory creation
# Override any attempts to create additional output directories
options(warn = 1)  # Show warnings immediately
cat("🔍 Session directory:", "{abs_session_dir}", "\\n")
cat("🔍 Current working directory:", getwd(), "\\n")

# Ensure all file operations stay in current directory
if (!identical(getwd(), "{abs_session_dir}")) {{
    stop("Working directory mismatch detected!")
}}

{workspace_load_code}
'''
            
            # CRITICAL FIX: Clean up problematic R code patterns that create nested directories
            import re

            # Remove problematic session directory setup patterns
            code = self._clean_nested_directory_patterns(code)

            # Get project root directory (where data folder is located)
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            project_root = project_root.replace(os.sep, '/')

            # Fix relative data paths to absolute paths
            def fix_data_paths(match):
                quote = match.group(1)
                path = match.group(2)

                # Convert backslashes to forward slashes
                path = path.replace('\\', '/')

                # Convert relative data paths to absolute paths
                if path.startswith('../') and 'data/' in path:
                    # Extract the data part (e.g., "data/adam/adae.sas7bdat")
                    data_part = path.split('data/', 1)[1] if 'data/' in path else path
                    absolute_path = f"{project_root}/data/{data_part}"
                    return f"{quote}{absolute_path}{quote}"
                elif path.startswith('data/'):
                    # Already relative to project root
                    absolute_path = f"{project_root}/{path}"
                    return f"{quote}{absolute_path}{quote}"
                else:
                    # Other paths, just fix separators
                    return f"{quote}{path}{quote}"

            # Apply path fixes to quoted strings
            fixed_code = re.sub(r'(["\'])([^"\']*(?:\\|/)[^"\']*)\1', fix_data_paths, code)

            # Combine setup code with fixed user code and workspace save code
            full_code = setup_code + fixed_code + workspace_save_code
            
            # Execute R code using subprocess
            result = self._execute_r_subprocess(full_code)
            
            # Get list of files in session directory
            files_generated = self._get_generated_files()
            
            return {
                'success': result['success'],
                'output': result['output'],
                'error': result.get('error', ''),
                'files_generated': files_generated,
                'output_directory': self.session_dir,
                'execution_time': result.get('execution_time', 0),
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"R execution error: {e}")
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'files_generated': [],
                'output_directory': self.session_dir,
                'execution_time': 0,
                'timestamp': time.time()
            }

    def _execute_r_subprocess(self, code: str) -> Dict[str, Any]:
        """Execute R code using subprocess"""
        start_time = time.time()
        
        try:
            # Create temporary script file with UTF-8 encoding
            with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False, encoding='utf-8') as f:
                f.write(code)
                script_path = f.name
            
            try:
                # Execute R script with explicit UTF-8 encoding to avoid gbk codec errors
                result = subprocess.run(
                    [self.r_executable, script_path],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',  # Explicitly use UTF-8 to avoid gbk codec errors
                    errors='replace',  # Replace invalid characters instead of failing
                    timeout=300,  # 5 minute timeout
                    cwd=self.session_dir  # Run in session directory
                )
                
                execution_time = time.time() - start_time
                
                if result.returncode == 0:
                    # Return both summary and raw output for different use cases
                    llm_summary = self._create_execution_summary(result.stdout, True)
                    raw_output = result.stdout.strip()  # Raw R console output

                    return {
                        'success': True,
                        'output': raw_output,  # Raw R console output for UI display
                        'summary': llm_summary,  # Summary for LLM consumption
                        'execution_time': execution_time
                    }
                else:
                    # For errors, return both summary and raw output
                    llm_summary = self._create_execution_summary(result.stdout, False, result.stderr)
                    raw_output = f"{result.stdout}\n{result.stderr}".strip()

                    return {
                        'success': False,
                        'output': raw_output,  # Raw error output for UI display
                        'summary': llm_summary,  # Summary for LLM consumption
                        'error': result.stderr,
                        'execution_time': execution_time
                    }
                    
            finally:
                # Clean up temporary script
                try:
                    os.unlink(script_path)
                except OSError:
                    pass
                    
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': 'R execution timed out after 5 minutes',
                'execution_time': time.time() - start_time
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'R execution failed: {str(e)}',
                'execution_time': time.time() - start_time
            }

    def _get_generated_files(self) -> List[str]:
        """Get list of files generated in session directory"""
        try:
            files = []
            for item in os.listdir(self.session_dir):
                item_path = os.path.join(self.session_dir, item)
                if os.path.isfile(item_path):
                    files.append(item)
            return sorted(files)
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []

    def execute_r_code_(self, code: str) -> str:
        """Execute R code and return output (internal method for compatibility)"""
        result = self.execute_r_code(code)
        if result['success']:
            return result['output']
        else:
            return f"Error: {result['error']}"

    def interrupt(self):
        """Set interrupt signal"""
        self.interrupt_signal = True
        logger.info("R execution interrupt signal set")

    def restart(self):
        """Restart R session (clear session directory)"""
        try:
            # Clear session directory but keep the directory itself
            for item in os.listdir(self.session_dir):
                item_path = os.path.join(self.session_dir, item)
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    import shutil
                    shutil.rmtree(item_path)
            
            logger.info(f"R session restarted - cleared {self.session_dir}")
            
        except Exception as e:
            logger.error(f"Error restarting R session: {e}")

    def get_session_info(self) -> Dict[str, Any]:
        """Get session information"""
        return {
            'session_dir': self.session_dir,
            'execution_id': self.execution_id,
            'r_executable': self.r_executable,
            'files_count': len(self._get_generated_files())
        }

    def _create_execution_summary(self, stdout: str, success: bool, stderr: str = "") -> str:
        """
        Create meaningful execution feedback for LLM (ChatGPT Code Interpreter style)
        Provides specific accomplishments, not just generic success messages
        """
        if success:
            summary = "✅ R code executed successfully"

            # Extract specific accomplishments from stdout (avoid false positives)
            lines = stdout.split('\n')
            accomplishments = set()  # Use set to avoid duplicates

            # Check for actual file operations and code patterns
            full_output = stdout.lower()

            # File creation detection
            if 'write.csv(' in full_output or 'write_csv(' in full_output:
                accomplishments.add("📄 CSV file created")
            if 'write.table(' in full_output:
                accomplishments.add("📄 Table file created")
            if 'ggsave(' in full_output:
                accomplishments.add("📊 Plot/chart saved")

            # HTML table detection (only if actual HTML is generated)
            if ('<table' in full_output and '</table>' in full_output and
                ('<th>' in full_output or '<td>' in full_output)):
                accomplishments.add("📋 HTML table generated")

            # Data operations detection
            if 'data.frame(' in full_output or 'tibble(' in full_output:
                accomplishments.add("📊 Data frame created")
            if 'summary(' in full_output:
                accomplishments.add("📈 Data summary computed")

            # Check for printed output (data results) - be more selective
            meaningful_lines = [line.strip() for line in lines
                              if (line.strip() and
                                  not line.startswith('[') and
                                  not 'Working directory' in line and
                                  not line.startswith('>'))]
            if meaningful_lines:
                accomplishments.add(f"📋 Output: {len(meaningful_lines)} lines of results")

            # Add specific accomplishments (convert set to sorted list)
            if accomplishments:
                summary += "\n" + "\n".join(sorted(accomplishments))
            else:
                summary += "\n📂 Code executed, working directory configured"

            return summary
        else:
            # For failures, include specific error information
            summary = "❌ R code execution failed"
            if stderr:
                error_lines = stderr.strip().split('\n')[:2]
                summary += f"\n🔍 Error: {' '.join(error_lines)}"
            return summary

    def _clean_nested_directory_patterns(self, code: str) -> str:
        """Remove problematic R code patterns that create nested directories"""
        import re

        # Patterns that create nested directories
        patterns_to_remove = [
            # Remove session directory variable assignments
            r'session_dir\s*<-\s*["\'][^"\']*["\'].*?\n',
            # Remove setwd() calls to session directories
            r'setwd\s*\(\s*["\'][^"\']*execution_[^"\']*["\']\s*\).*?\n',
            # Remove dir.create() calls for session directories
            r'if\s*\(\s*!dir\.exists\s*\([^)]*session_dir[^)]*\)\s*\)\s*\{[^}]*dir\.create[^}]*\}',
            # Remove standalone dir.create() for outputs/execution_ paths
            r'dir\.create\s*\(\s*["\'][^"\']*outputs/execution_[^"\']*["\'][^)]*\).*?\n',
        ]

        cleaned_code = code
        for pattern in patterns_to_remove:
            cleaned_code = re.sub(pattern, '', cleaned_code, flags=re.MULTILINE | re.DOTALL)

        # Clean up extra newlines
        cleaned_code = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_code)

        if cleaned_code != code:
            logger.info("🧹 Cleaned problematic directory creation patterns from R code")

        return cleaned_code
