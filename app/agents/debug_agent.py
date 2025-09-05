#!/usr/bin/env python3
# Author: Jaime Yan
"""
Debug Agent - Specialized agent for error detection and code fixing
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DebugAgent:
    """Specialized agent for debugging and error fixing"""
    
    def __init__(self, deepseek_client, r_interpreter):
        self.deepseek_client = deepseek_client
        self.r_interpreter = r_interpreter
        self.agent_name = "Debug Agent"
        
    def fix_code_error(self, code: str, error: str) -> Dict[str, Any]:
        """Fix R code errors with enhanced context and analysis"""
        try:
            # First analyze the error
            analysis_prompt = f"""
Analyze this R code error in detail:

Code:
```r
{code}
```

Error:
{error}

Provide analysis in this format:
ERROR_TYPE:
[Classify the type of error: Syntax, Runtime, Logic, etc.]

ROOT_CAUSE:
[Identify the fundamental cause]

AFFECTED_COMPONENTS:
[List the specific code parts affected]

POTENTIAL_FIXES:
[List possible solutions]
"""
            
            analysis_response = self.deepseek_client.chat_completion(
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=1000,
                temperature=0.1
            )
            
            # Use the analysis to guide the fix
            if analysis_response and analysis_response.get("choices"):
                analysis = analysis_response["choices"][0]["message"]["content"]
                
                fix_prompt = f"""
Based on this analysis:
{analysis}

Fix the R code:
```r
{code}
```

Error:
{error}

Provide the solution in this format:
FIXED_CODE:
```r
[fixed code here]
```

EXPLANATION:
[Detailed explanation of changes made]

VERIFICATION_STEPS:
[Steps to verify the fix works]
"""
                
                fix_response = self.deepseek_client.chat_completion(
                    messages=[
                        {"role": "user", "content": analysis_prompt},
                        {"role": "assistant", "content": analysis},
                        {"role": "user", "content": fix_prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.1
                )
                
                if fix_response and fix_response.get("choices"):
                    content = fix_response["choices"][0]["message"]["content"]
                    
                    import re
                    code_match = re.search(r'FIXED_CODE:\s*```r\s*(.*?)\s*```', content, re.DOTALL)
                    explanation_match = re.search(r'EXPLANATION:\s*(.*?)(?=VERIFICATION_STEPS:|$)', content, re.DOTALL)
                    verification_match = re.search(r'VERIFICATION_STEPS:\s*(.*?)$', content, re.DOTALL)
                    
                    if code_match:
                        fixed_code = code_match.group(1).strip()
                        
                        # Try to verify the fix works
                        verification_result = self.r_interpreter.execute_code(fixed_code)
                        
                        if verification_result.get("success"):
                            return {
                                "success": True,
                                "fixed_code": fixed_code,
                                "explanation": explanation_match.group(1).strip() if explanation_match else "",
                                "verification_steps": verification_match.group(1).strip() if verification_match else "",
                                "analysis": analysis,
                                "agent": self.agent_name
                            }
                        else:
                            # Fix didn't work, try one more time with the error feedback
                            retry_prompt = f"""
The previous fix didn't work. Here's the new error:
{verification_result.get('stderr', 'Unknown error')}

Please provide a different solution that addresses both the original error and this new one.

Original code:
```r
{code}
```

Previous fix attempt:
```r
{fixed_code}
```

Provide a new solution in the same format as before.
"""
                            retry_response = self.deepseek_client.chat_completion(
                                messages=[
                                    {"role": "user", "content": analysis_prompt},
                                    {"role": "assistant", "content": analysis},
                                    {"role": "user", "content": fix_prompt},
                                    {"role": "assistant", "content": content},
                                    {"role": "user", "content": retry_prompt}
                                ],
                                max_tokens=1500,
                                temperature=0.1
                            )
                            
                            if retry_response and retry_response.get("choices"):
                                retry_content = retry_response["choices"][0]["message"]["content"]
                                retry_code_match = re.search(r'FIXED_CODE:\s*```r\s*(.*?)\s*```', retry_content, re.DOTALL)
                                
                                if retry_code_match:
                                    return {
                                        "success": True,
                                        "fixed_code": retry_code_match.group(1).strip(),
                                        "explanation": "Second attempt fix after verification failure",
                                        "previous_attempt": fixed_code,
                                        "analysis": analysis,
                                        "agent": self.agent_name
                                    }
            
            return {
                "success": False,
                "error": "Failed to generate a working fix",
                "analysis": analysis if 'analysis' in locals() else None,
                "agent": self.agent_name
            }
            
        except Exception as e:
            logger.error(f"Error in debug agent: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.agent_name
            }

    def debug_code_error(self, code: str, error_info: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Intelligent debugging with context-aware error analysis and auto-fixing"""
        try:
            logger.info("🐛 Starting intelligent code debugging...")

            if not error_info or not error_info.get("has_error"):
                return {
                    "success": False,
                    "error": "No error information provided",
                    "agent": self.agent_name
                }

            error_type = error_info.get("error_type", "unknown")
            error_message = error_info.get("error_message", "")

            # Build context-aware debugging prompt
            debug_prompt = f"""
You are an expert R debugging assistant. Analyze and fix this R code error with intelligent context awareness.

CONTEXT:
- Error Type: {error_type}
- Error Message: {error_message}
- Template Context: {context.get('mock_template', {}).get('title', 'Unknown') if context else 'Unknown'}
- Dataset: {context.get('dataset_name', 'Unknown') if context else 'Unknown'}

PROBLEMATIC CODE:
```r
{code}
```

ERROR DETAILS:
{error_info}

TASK: Provide intelligent debugging analysis and auto-fix solution.

RESPONSE FORMAT:
ANALYSIS:
[Detailed analysis of the error cause and context]

CONFIDENCE: [0-100]
[Your confidence level in the diagnosis]

EXPLANATION:
[Clear explanation of what went wrong and why]

FIXED_CODE:
```r
[Corrected R code that should work]
```

SUGGESTIONS:
- [Specific actionable suggestions]
- [Best practices to prevent similar errors]
- [Alternative approaches if applicable]

PREVENTION:
[How to prevent this error in the future]
"""

            # Get intelligent debugging response
            response = self.deepseek_client.chat_completion(
                messages=[{"role": "user", "content": debug_prompt}],
                max_tokens=2000,
                temperature=0.1  # Low temperature for precise debugging
            )

            if not response or not response.get("choices"):
                return {
                    "success": False,
                    "error": "No debugging response received",
                    "agent": self.agent_name
                }

            debug_content = response["choices"][0]["message"]["content"]

            # Parse the structured response
            parsed_result = self._parse_debug_response(debug_content)

            # Validate the fixed code if provided
            if parsed_result.get("fixed_code"):
                validation_result = self._validate_fixed_code(parsed_result["fixed_code"])
                parsed_result["validation"] = validation_result

            return {
                "success": True,
                "explanation": parsed_result.get("explanation", "Error analysis completed"),
                "fixed_code": parsed_result.get("fixed_code", ""),
                "suggestions": parsed_result.get("suggestions", []),
                "confidence": parsed_result.get("confidence", 75),
                "analysis": parsed_result.get("analysis", ""),
                "prevention": parsed_result.get("prevention", ""),
                "validation": parsed_result.get("validation", {}),
                "agent": self.agent_name
            }

        except Exception as e:
            logger.error(f"Error in intelligent debugging: {str(e)}")
            return {
                "success": False,
                "error": f"Debugging failed: {str(e)}",
                "agent": self.agent_name
            }

    def _parse_debug_response(self, content: str) -> Dict[str, Any]:
        """Parse structured debugging response"""
        result = {
            "analysis": "",
            "explanation": "",
            "fixed_code": "",
            "suggestions": [],
            "confidence": 75,
            "prevention": ""
        }

        try:
            # Extract sections using markers
            sections = {
                "ANALYSIS:": "analysis",
                "EXPLANATION:": "explanation",
                "CONFIDENCE:": "confidence",
                "PREVENTION:": "prevention"
            }

            for marker, key in sections.items():
                if marker in content:
                    start = content.find(marker) + len(marker)
                    # Find next section or end
                    next_markers = [m for m in sections.keys() if m != marker]
                    end = len(content)
                    for next_marker in next_markers:
                        pos = content.find(next_marker, start)
                        if pos != -1 and pos < end:
                            end = pos

                    value = content[start:end].strip()
                    if key == "confidence":
                        # Extract numeric confidence
                        import re
                        conf_match = re.search(r'(\d+)', value)
                        result[key] = int(conf_match.group(1)) if conf_match else 75
                    else:
                        result[key] = value

            # Extract fixed code
            if "FIXED_CODE:" in content:
                start = content.find("FIXED_CODE:")
                code_start = content.find("```r", start)
                if code_start != -1:
                    code_start += 4
                    code_end = content.find("```", code_start)
                    if code_end != -1:
                        result["fixed_code"] = content[code_start:code_end].strip()

            # Extract suggestions
            if "SUGGESTIONS:" in content:
                start = content.find("SUGGESTIONS:")
                end = content.find("PREVENTION:", start)
                if end == -1:
                    end = len(content)

                suggestions_text = content[start:end]
                suggestions = []
                for line in suggestions_text.split('\n'):
                    line = line.strip()
                    if line.startswith('- '):
                        suggestions.append(line[2:])
                result["suggestions"] = suggestions

        except Exception as e:
            logger.error(f"Error parsing debug response: {str(e)}")

        return result

    def _validate_fixed_code(self, fixed_code: str) -> Dict[str, Any]:
        """Validate the fixed code for basic syntax"""
        try:
            # Basic R syntax validation
            validation = {
                "syntax_valid": True,
                "issues": [],
                "warnings": []
            }

            # Check for common syntax issues
            if fixed_code.count('(') != fixed_code.count(')'):
                validation["syntax_valid"] = False
                validation["issues"].append("Mismatched parentheses")

            if fixed_code.count('[') != fixed_code.count(']'):
                validation["syntax_valid"] = False
                validation["issues"].append("Mismatched square brackets")

            if fixed_code.count('{') != fixed_code.count('}'):
                validation["syntax_valid"] = False
                validation["issues"].append("Mismatched curly braces")

            # Check for basic R patterns
            if not any(keyword in fixed_code for keyword in ['<-', '=', 'library', 'data', 'function']):
                validation["warnings"].append("Code may be incomplete")

            return validation

        except Exception as e:
            return {
                "syntax_valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "warnings": []
            }
