"""
Pydantic Data Models for Reflection Agent

WHY THIS FILE:
- Define the structure of data the LLM should return
- Provide type safety and automatic validation
- These models get bound as "tools" to the LLM

HOW IT WORKS:
- Pydantic models define expected JSON structure
- LangChain converts them to LLM tool schemas
- LLM knows to return data matching these schemas
- Pydantic automatically validates the response

ANALOGY:
Think of these as forms the LLM must fill out.
Each field has a label (Field description) telling the LLM what to write.
"""

from typing import List
from pydantic import BaseModel, Field


# ============================================================================
# REFLECTION MODEL
# ============================================================================

class Reflection(BaseModel):
    """
    Self-critique structure

    WHY: Forces the LLM to think critically about its own answer
    - What did I miss?
    - What was unnecessary?

    This is the "reflection" part of Reflection Agent!
    """

    missing: str = Field(
        description="What critical information or evidence is missing from the answer. "
                    "Be specific: mention studies, data, perspectives, or considerations you didn't include."
    )

    superfluous: str = Field(
        description="What information in the answer is unnecessary or could be removed. "
                    "Identify tangents, redundancies, or irrelevant details."
    )


# ============================================================================
# INITIAL ANSWER MODEL
# ============================================================================

class AnswerQuestion(BaseModel):
    """
    Initial response structure

    WHY: This is what the LLM returns on the FIRST pass
    - The answer itself
    - Self-critique (using Reflection model)
    - Search queries to fill gaps

    WHEN USED: In the "generate" node
    """

    answer: str = Field(
        description="Comprehensive answer to the user's question. "
                    "Write 2-3 detailed paragraphs based on your existing knowledge."
    )

    reflection: Reflection = Field(
        description="Critical self-assessment of your answer. "
                    "Identify what's missing and what's unnecessary."
    )

    search_queries: List[str] = Field(
        description="1-3 specific search queries to find the missing information. "
                    "Base these on what you identified as missing in your reflection. "
                    "Make queries specific and research-oriented."
    )


# ============================================================================
# REVISED ANSWER MODEL
# ============================================================================

class ReviseAnswer(AnswerQuestion):
    """
    Revised response structure

    WHY: This is what the LLM returns AFTER searching
    - Inherits answer, reflection, search_queries from AnswerQuestion
    - ADDS references field for citations

    WHEN USED: In the "revise" node

    NOTE: Inheriting from AnswerQuestion means it has all the same fields
    plus the new 'references' field. This lets us potentially do another
    iteration if needed.
    """

    references: List[str] = Field(
        description="List of URLs or citations used to improve the answer. "
                    "Extract these from the search results. "
                    "Format: ['https://example.com', 'Author et al. 2023']"
    )


# ============================================================================
# USAGE EXAMPLE (for understanding)
# ============================================================================

"""
Example of what the LLM returns when calling AnswerQuestion:

{
    "answer": "Intermittent fasting has several health benefits...",
    "reflection": {
        "missing": "Specific clinical trial data, long-term safety studies",
        "superfluous": "General diet advice not specific to IF"
    },
    "search_queries": [
        "intermittent fasting clinical trials 2023",
        "long-term safety intermittent fasting"
    ]
}

Then after searching and revising, ReviseAnswer returns:

{
    "answer": "A 2023 meta-analysis found intermittent fasting...",
    "reflection": {
        "missing": "Data on specific populations",
        "superfluous": "None"
    },
    "search_queries": ["intermittent fasting elderly populations"],
    "references": [
        "https://jamanetwork.com/...",
        "https://www.ncbi.nlm.nih.gov/..."
    ]
}
"""
