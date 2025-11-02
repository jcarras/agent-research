"""
Configuration Settings for Reflection Agent

WHY THIS FILE:
- Centralize all configuration in one place
- Easy to modify settings without touching logic
- Clear separation of config from code

WHAT IT CONTAINS:
- Model selection (which LLM to use)
- Temperature (creativity vs accuracy)
- Max iterations (how many revision cycles)
"""

from dotenv import load_dotenv

# Load environment variables from .env.dev
# WHY: Keeps API keys out of code (security best practice)
# SETUP: Get your free Google API key from https://makersuite.google.com/app/apikey
load_dotenv('.env.dev')


# ============================================================================
# LLM CONFIGURATION
# ============================================================================

# Which model to use from Google Gemini
# WHY: Centralize so you can easily switch models
# Note: gemini-2.5-flash is fast and available with Google AI Studio API
MODEL_NAME = "gemini-2.5-flash"

# Temperature controls randomness/creativity
# 0.0 = deterministic, factual
# 0.7 = balanced (recommended for research)
# 1.0 = creative, varied
# WHY: Lower temp for factual accuracy, higher for creative tasks
TEMPERATURE = 0.7


# ============================================================================
# AGENT BEHAVIOR
# ============================================================================

# Maximum number of revision cycles
# WHY: Prevent infinite loops and control costs
# Each iteration = 3 LLM calls + searches
MAX_ITERATIONS = 2

# Number of search results per query
# WHY: More results = better research but more tokens/cost
MAX_SEARCH_RESULTS = 3

# Maximum characters per search result
# WHY: Prevent token overload while keeping useful info
SEARCH_RESULT_LIMIT = 800


# ============================================================================
# DISPLAY SETTINGS
# ============================================================================

# Show progress messages during execution
# WHY: Helps debug and understand what the agent is doing
VERBOSE = True