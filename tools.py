"""
External Tools for Reflection Agent

WHY THIS FILE:
- Initialize external tools the agent can use
- Centralize tool configuration
- Easy to swap out or add new tools

WHAT IS A TOOL:
A tool is any function or service the agent can call to get information:
- Search engines (DuckDuckGo, Tavily, Google)
- Databases (SQL, vector stores)
- APIs (weather, stock prices, etc.)
- Calculators, code executors, etc.

CURRENT TOOLS:
- DuckDuckGo search (free, no API key needed!)
"""

from langchain_community.tools import DuckDuckGoSearchRun


# ============================================================================
# SEARCH TOOL
# ============================================================================

"""
WHY DUCKDUCKGO:
- No API key required (completely free!)
- Good search quality
- Privacy-focused
- No rate limits for reasonable use

ALTERNATIVES:
- TavilySearchResults (better quality, requires API key)
- GoogleSearchAPIWrapper (requires API key)
- WikipediaQueryRun (for encyclopedic info)
"""

# Initialize DuckDuckGo search
# This creates a callable tool: search_tool.run("query") -> results
search_tool = DuckDuckGoSearchRun()


# ============================================================================
# HOW SEARCH TOOL IS USED
# ============================================================================

"""
In the execute_tools node, we do:

    search_queries = ["intermittent fasting RCT 2023", "IF safety studies"]

    for query in search_queries:
        result = search_tool.run(query)
        # result is a string with search snippets

The agent doesn't directly call the search tool!
Instead:
1. LLM generates search queries (in tool_call)
2. Our code extracts those queries
3. Our code runs the search
4. Results go back to LLM as ToolMessage

DIAGRAM:
  LLM: "I need to search for X"
   ↓ (tool_call with search_queries)
  execute_tools node: Actually runs searches
   ↓ (ToolMessage with results)
  LLM: "Now I can revise with this new info"
"""


# ============================================================================
# ADDING MORE TOOLS (Examples)
# ============================================================================

"""
You can easily add more tools here:

# Wikipedia for encyclopedic info
from langchain_community.tools import WikipediaQueryRun
wikipedia_tool = WikipediaQueryRun()

# Calculator for math
from langchain.tools import Tool
def calculate(expression: str) -> str:
    try:
        return str(eval(expression))
    except:
        return "Invalid expression"

calculator_tool = Tool(
    name="Calculator",
    func=calculate,
    description="Performs mathematical calculations"
)

# Weather API
def get_weather(city: str) -> str:
    # Call weather API here
    return f"Weather for {city}: ..."

weather_tool = Tool(
    name="Weather",
    func=get_weather,
    description="Gets current weather for a city"
)

Then in nodes.py, you'd run these tools based on what the LLM requests.
"""


# ============================================================================
# EXPORT
# ============================================================================

# Make search_tool available to other modules
__all__ = ['search_tool']
