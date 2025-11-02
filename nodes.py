"""
Graph Nodes for Reflection Agent

WHY THIS FILE:
- Contains the core processing logic
- Each node is one step in the agent workflow
- Keeps graph construction separate from execution logic

WHAT IS A NODE:
A node is a function that:
- Takes state (conversation history) as input
- Does some processing (call LLM, run searches, etc.)
- Returns new messages to add to state

ANALOGY:
Nodes are like workers on an assembly line.
Each worker has a specific job:
- Worker 1: Draft the answer
- Worker 2: Do research
- Worker 3: Improve the draft
"""

import json
from typing import List
from langchain_core.messages import AIMessage, ToolMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from config import MODEL_NAME, TEMPERATURE, VERBOSE, SEARCH_RESULT_LIMIT
from models import AnswerQuestion, ReviseAnswer
from prompts import initial_prompt, revision_prompt
from tools import search_tool


# ============================================================================
# LLM INITIALIZATION
# ============================================================================

"""
WHY GOOGLE GEMINI:
- Excellent tool calling support (handles nested JSON well)
- Very generous free tier (60 requests/minute)
- Fast and high quality
- Works reliably with complex Pydantic models

The LLM is initialized once and reused across nodes.
"""

llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    convert_system_message_to_human=True,  # Required for some models
)


# ============================================================================
# CHAIN CREATION
# ============================================================================

"""
WHAT IS A CHAIN:
A chain is: Prompt Template | LLM | Tool Binding

It means:
1. Format the prompt with conversation history
2. Send to LLM
3. LLM returns structured output (tool call)

WHY BIND_TOOLS:
- Tells LLM "you must return data matching this Pydantic model"
- tool_choice="AnswerQuestion" FORCES the LLM to use that tool
- No manual JSON parsing needed!
"""

# Initial chain: Generates first answer with self-critique
initial_chain = initial_prompt | llm.bind_tools(
    tools=[AnswerQuestion],
    tool_choice="AnswerQuestion"  # Must use this tool
)

# Revision chain: Generates improved answer with references
revisor_chain = revision_prompt | llm.bind_tools(
    tools=[ReviseAnswer],
    tool_choice="ReviseAnswer"  # Must use this tool
)


# ============================================================================
# NODE 1: GENERATE INITIAL RESPONSE
# ============================================================================

def generate_initial_response(messages: List[BaseMessage]) -> AIMessage:
    """
    Generate initial answer with self-critique and search queries

    WHAT IT DOES:
    1. Receives user's question (in messages)
    2. Calls LLM with initial_chain
    3. LLM returns:
       - answer (based on existing knowledge)
       - reflection (self-critique: what's missing/superfluous)
       - search_queries (to find missing info)

    PARAMETERS:
    - messages: List[BaseMessage] - Conversation so far
      Usually just [HumanMessage("What are benefits of IF?")]

    RETURNS:
    - AIMessage with tool_calls containing the structured response

    WHY THIS STRUCTURE:
    The LLM doesn't just answer - it REFLECTS on its answer.
    This is the key to the Reflection pattern!

    EXAMPLE OUTPUT:
    AIMessage(
        tool_calls=[{
            "name": "AnswerQuestion",
            "args": {
                "answer": "Intermittent fasting has benefits...",
                "reflection": {
                    "missing": "Clinical trial data, safety studies",
                    "superfluous": "General diet advice"
                },
                "search_queries": [
                    "intermittent fasting RCT 2023",
                    "IF safety studies"
                ]
            }
        }]
    )
    """

    if VERBOSE:
        print("\n🤖 Generating initial response with self-critique...")

    # Invoke the chain
    # The prompt template inserts messages into MessagesPlaceholder
    # LLM is bound to AnswerQuestion tool
    # Result has structured tool_call automatically
    response = initial_chain.invoke({"messages": messages})

    # Display info if verbose
    if VERBOSE and response.tool_calls:
        args = response.tool_calls[0]['args']
        print(f"   ✓ Answer generated ({len(args['answer'])} chars)")
        print(f"   ✓ Self-critique: {args['reflection']['missing'][:80]}...")
        print(f"   ✓ Search queries: {len(args['search_queries'])} queries")

    return response


# ============================================================================
# NODE 2: EXECUTE SEARCH TOOLS
# ============================================================================

def execute_tools(state: List[BaseMessage]) -> List[ToolMessage]:
    """
    Execute search queries using DuckDuckGo

    WHAT IT DOES:
    1. Gets last AI message from state
    2. Extracts search_queries from its tool_call
    3. Runs each query through DuckDuckGo
    4. Returns results as ToolMessages

    PARAMETERS:
    - state: List[BaseMessage] - Full conversation history
      At this point contains: [HumanMessage, AIMessage with tool_call]

    RETURNS:
    - List[ToolMessage] - Search results for each query

    WHY TOOLMESSAGE:
    ToolMessage tells the LLM: "Here are the results from the tool you called"
    It references the tool_call_id so LLM knows which call these results are for

    FLOW:
    1. Extract: Get search_queries from AI's tool_call
    2. Search: Run each query through DuckDuckGo
    3. Package: Wrap results in ToolMessage
    4. Return: These get added to conversation state

    EXAMPLE:
    Input state: [HumanMessage, AIMessage(tool_calls=[{
        "id": "call_123",
        "args": {"search_queries": ["IF RCT 2023", "IF safety"]}
    }])]

    Output: [ToolMessage(
        content='{"IF RCT 2023": "...results...", "IF safety": "...results..."}',
        tool_call_id="call_123"
    )]
    """

    if VERBOSE:
        print("\n🔍 Executing search queries...")

    # Get the most recent AI message (has the tool_call with queries)
    last_ai_message = state[-1]
    tool_messages = []

    # Process each tool call
    # (Usually just one, but LLM could make multiple)
    for tool_call in last_ai_message.tool_calls:

        # Check if this is a tool call we handle
        if tool_call["name"] in ["AnswerQuestion", "ReviseAnswer"]:
            call_id = tool_call["id"]
            search_queries = tool_call["args"].get("search_queries", [])

            # Execute each search query
            query_results = {}
            for i, query in enumerate(search_queries, 1):
                try:
                    if VERBOSE:
                        print(f"   [{i}] Searching: {query}")

                    # Actually run the search!
                    result = search_tool.run(query)

                    # Limit result length to avoid token overload
                    query_results[query] = result[:SEARCH_RESULT_LIMIT]

                except Exception as e:
                    if VERBOSE:
                        print(f"   ⚠ Search error: {str(e)}")
                    query_results[query] = f"Search unavailable: {str(e)}"

            # Create ToolMessage with all search results
            # JSON format makes it easy for LLM to parse
            tool_messages.append(
                ToolMessage(
                    content=json.dumps(query_results, indent=2),
                    tool_call_id=call_id  # Links to the AI's tool_call
                )
            )

    if VERBOSE:
        print(f"   ✓ Completed {len(search_queries)} searches")

    return tool_messages


# ============================================================================
# NODE 3: REVISE ANSWER
# ============================================================================

def revise_answer(state: List[BaseMessage]) -> AIMessage:
    """
    Revise answer incorporating search results

    WHAT IT DOES:
    1. Receives full conversation (question + initial answer + search results)
    2. Calls LLM with revisor_chain
    3. LLM creates improved answer using search findings
    4. Returns revised answer with references

    PARAMETERS:
    - state: List[BaseMessage] - Full conversation
      At this point: [HumanMessage, AIMessage, ToolMessage(s)]

    RETURNS:
    - AIMessage with tool_calls containing revised response

    WHY THIS WORKS:
    The LLM sees:
    - Original question (HumanMessage)
    - Its first answer + self-critique (AIMessage)
    - Search results (ToolMessage)

    So it can intelligently incorporate the new info to address gaps!

    FLOW:
    1. LLM reviews conversation history
    2. Sees what it said was missing
    3. Sees search results with that info
    4. Creates improved answer citing sources

    EXAMPLE OUTPUT:
    AIMessage(
        tool_calls=[{
            "name": "ReviseAnswer",
            "args": {
                "answer": "A 2023 meta-analysis found IF leads to...",
                "reflection": {
                    "missing": "Long-term data still needed",
                    "superfluous": "None"
                },
                "search_queries": ["IF 5-year outcomes"],
                "references": [
                    "https://jamanetwork.com/...",
                    "Smith et al. 2023"
                ]
            }
        }]
    )
    """

    if VERBOSE:
        print("\n✍️  Revising answer with research findings...")

    # Invoke revisor chain with full conversation history
    # MessagesPlaceholder inserts all state messages
    # LLM sees question, initial answer, and search results
    response = revisor_chain.invoke({"messages": state})

    # Display info if verbose
    if VERBOSE and response.tool_calls:
        args = response.tool_calls[0]['args']
        print(f"   ✓ Answer revised ({len(args['answer'])} chars)")
        if args.get('references'):
            print(f"   ✓ Added {len(args['references'])} references")

    return response


# ============================================================================
# CONDITIONAL EDGE FUNCTION
# ============================================================================

def should_continue(state: List[BaseMessage]) -> str:
    """
    Decide whether to continue revising or end

    WHAT IT DOES:
    Counts how many times we've searched and revised.
    If we've hit MAX_ITERATIONS, stop. Otherwise, continue.

    PARAMETERS:
    - state: List[BaseMessage] - Full conversation

    RETURNS:
    - "execute_tools" = continue another iteration
    - END = stop and return final answer

    WHY COUNT TOOLMESSAGES:
    Each ToolMessage represents one search execution.
    So counting them = counting iterations.

    FLOW:
    Iteration 1: [Human, AI, Tool] -> count=1 -> continue
    Iteration 2: [Human, AI, Tool, AI, Tool] -> count=2 -> END

    WHY LIMIT ITERATIONS:
    - Prevents infinite loops
    - Controls costs (each iteration = $$$)
    - Prevents diminishing returns (answer gets good enough)
    """

    from langgraph.graph import END
    from config import MAX_ITERATIONS

    # Count ToolMessages to track iterations
    tool_count = sum(isinstance(msg, ToolMessage) for msg in state)

    if tool_count >= MAX_ITERATIONS:
        if VERBOSE:
            print(f"\n🏁 Reached max iterations ({MAX_ITERATIONS}). Finishing...")
        return END
    else:
        if VERBOSE:
            print(f"\n🔄 Iteration {tool_count} complete. Continuing...")
        return "execute_tools"


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'generate_initial_response',
    'execute_tools',
    'revise_answer',
    'should_continue'
]
