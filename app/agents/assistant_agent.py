#!/usr/bin/env python3
# Author: Jaime Yan
"""
Assistant Agent - Specialized agent for Q&A and user guidance
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AssistantAgent:
    """Specialized agent for user assistance and guidance"""
    
    def __init__(self, deepseek_client):
        self.deepseek_client = deepseek_client
        self.agent_name = "Assistant Agent"
        
    def answer_question(self, question: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Answer user questions with context"""
        try:
            prompt = f"""
You are a clinical data analysis assistant. Answer the user's question based on the current workflow context.

Context:
- Current workflow state: {context.get('state', 'unknown')}
- Template: {context.get('template_title', 'None')}
- Dataset: {context.get('dataset', 'None')}

User Question: {question}

Provide a helpful, accurate answer focused on clinical data analysis and R programming.
"""
            
            response = self.deepseek_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            if response and response.get("choices"):
                return {
                    "success": True,
                    "answer": response["choices"][0]["message"]["content"],
                    "agent": self.agent_name
                }
            
            return {"success": False, "error": "No response from assistant"}
            
        except Exception as e:
            logger.error(f"Error in assistant agent: {str(e)}")
            return {"success": False, "error": str(e)}
