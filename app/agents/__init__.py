#!/usr/bin/env python3
# Author: Jaime Yan
"""
AI Agents Package - Advanced Agentic Workflow System

This package implements a sophisticated multi-agent system for clinical data analysis
with the following specialized agents:

- AgentOrchestrator: Main controller coordinating all agents
- TemplateAgent: Mock template generation and modification
- DataExplorerAgent: Dataset analysis and variable exploration  
- CodeGeneratorAgent: R code generation and optimization
- DebugAgent: Error detection and code fixing
- AssistantAgent: Q&A and user guidance
- ReflectionAgent: Quality review and improvement suggestions

Key Features:
- Reflection Pattern: Agents review and improve outputs
- Planning Pattern: Multi-step workflow with user control
- Tool Use Pattern: Specialized tools for different tasks
- Multi-Agent Collaboration: Coordinated agent interactions
- Iterative Refinement: User-guided improvement cycles
"""

from .agent_orchestrator import AgentOrchestrator, WorkflowState, AgentRole
from .template_agent import TemplateAgent
from .data_explorer_agent import DataExplorerAgent
from .code_generator_agent import CodeGeneratorAgent

__all__ = [
    'AgentOrchestrator',
    'WorkflowState', 
    'AgentRole',
    'TemplateAgent',
    'DataExplorerAgent', 
    'CodeGeneratorAgent'
]

__version__ = "1.0.0"
__author__ = "R TLF System Team"
__description__ = "Advanced AI Agent System for Clinical Data Analysis"
