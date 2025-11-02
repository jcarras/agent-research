"""
Reflection Agent Package

WHY THIS FILE:
- Makes 'reflection_agent' a Python package
- Can be used for package initialization (currently minimal)

USAGE:
    Run directly:
        python main.py

    Or import in scripts:
        from main import run_agent
        result = run_agent("What are the benefits of exercise?")

    Advanced usage:
        from graph import create_reflection_agent
        from langchain_core.messages import HumanMessage

        agent = create_reflection_agent()
        messages = agent.invoke([HumanMessage("Question")])
"""

# ============================================================================
# PACKAGE METADATA
# ============================================================================

__version__ = "1.0.0"
__author__ = "Reflection Agent Team"
__description__ = "A self-improving AI agent using the Reflection pattern with LangGraph"
