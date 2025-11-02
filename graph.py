"""
LangGraph Construction for Reflection Agent

WHY THIS FILE:
- Assembles nodes into a complete workflow
- Defines the flow: which node comes after which
- Creates the executable agent

WHAT IS LANGGRAPH:
LangGraph is a framework for building stateful, multi-step workflows.
Think of it like a flowchart where:
- Nodes = processing steps
- Edges = connections between steps
- State = data that flows through

ANALOGY:
Like planning a road trip:
- Nodes = cities you visit (do stuff at each city)
- Edges = roads connecting cities (how to get from A to B)
- State = your car with luggage (carries everything with you)
"""

from langgraph.graph import MessageGraph, END

from nodes import (
    generate_initial_response,
    execute_tools,
    revise_answer,
    should_continue
)


# ============================================================================
# GRAPH CREATION FUNCTION
# ============================================================================

def create_reflection_agent():
    """
    Build the Reflection Agent workflow

    RETURNS:
    - Compiled LangGraph that can be invoked

    WORKFLOW:
    1. Generate initial answer with self-critique
    2. Execute searches based on identified gaps
    3. Revise answer with search findings
    4. Check if we should continue (conditional)
       - If yes: repeat from step 2
       - If no: return final answer

    VISUAL:
                 ┌──────────┐
                 │  START   │
                 └────┬─────┘
                      │
                      ▼
              ┌───────────────┐
              │   Generate    │ ← Creates initial answer + critique
              └───────┬───────┘
                      │ (always)
                      ▼
              ┌───────────────┐
              │ Execute Tools │ ← Runs DuckDuckGo searches
              └───────┬───────┘
                      │ (always)
                      ▼
              ┌───────────────┐
              │    Revise     │ ← Improves answer with findings
              └───────┬───────┘
                      │
                      ▼
                  ┌───────┐
                  │ Done? │ ← Conditional check
                  └───┬───┘
                      │
            ┌─────────┴─────────┐
            │                   │
           Yes                 No
            │                   │
            ▼                   ▼
         [END]      ┌─────────────────┐
                    │  Execute Tools  │ ← Loop back
                    └─────────────────┘
                              │
                              ▼
                          (continues...)

    WHY THIS FLOW:
    - Generate first: Get initial answer + identify gaps
    - Search: Fill those gaps with research
    - Revise: Create improved answer
    - Conditional: Decide if we need another round

    The loop allows iterative improvement until satisfied or max iterations.
    """

    # Create graph
    # MessageGraph is designed for conversational workflows
    # State is automatically a list of messages
    graph = MessageGraph()

    # ========================================================================
    # ADD NODES
    # ========================================================================

    """
    Nodes are the processing units.
    Each node is a function that takes state and returns messages.

    The name (first arg) is how you reference it in edges.
    The function (second arg) is what actually runs.
    """

    graph.add_node("generate", generate_initial_response)
    # ^ When "generate" node runs, it calls generate_initial_response()

    graph.add_node("execute_tools", execute_tools)
    # ^ When "execute_tools" node runs, it calls execute_tools()

    graph.add_node("revise", revise_answer)
    # ^ When "revise" node runs, it calls revise_answer()


    # ========================================================================
    # ADD EDGES (Fixed)
    # ========================================================================

    """
    Fixed edges: "Always go from A to B"
    These define deterministic flow.
    """

    graph.add_edge("generate", "execute_tools")
    # After generating initial answer, ALWAYS execute searches

    graph.add_edge("execute_tools", "revise")
    # After executing searches, ALWAYS revise the answer


    # ========================================================================
    # ADD CONDITIONAL EDGES
    # ========================================================================

    """
    Conditional edges: "Decide where to go based on logic"

    should_continue() function determines the next step:
    - Returns "execute_tools" → Go back to searching (another iteration)
    - Returns END → Stop and return final result

    The second argument is a mapping:
    {
        "execute_tools": "execute_tools",  # If returned, go to execute_tools node
        END: END                             # If returned, end the graph
    }

    Note: We could also go back to "revise" or any other node!
    """

    graph.add_conditional_edges(
        "revise",              # From this node...
        should_continue,       # ...call this function to decide...
        {
            "execute_tools": "execute_tools",  # ...if it returns this, go here
            END: END                           # ...if it returns END, finish
        }
    )

    # Alternative syntax (LangGraph handles the mapping automatically):
    # graph.add_conditional_edges("revise", should_continue)
    # If should_continue returns "execute_tools", it goes there
    # If should_continue returns END, it ends


    # ========================================================================
    # SET ENTRY POINT
    # ========================================================================

    """
    Where does the graph start?
    When you invoke the graph, it begins at the entry point.
    """

    graph.set_entry_point("generate")
    # Start at "generate" node


    # ========================================================================
    # COMPILE
    # ========================================================================

    """
    Compiling converts the graph definition into an executable workflow.
    The compiled graph can be invoked with:
        agent = create_reflection_agent()
        result = agent.invoke([HumanMessage("Question here")])
    """

    return graph.compile()


# ============================================================================
# HOW THE COMPILED GRAPH WORKS
# ============================================================================

"""
When you invoke the compiled graph:

    agent = create_reflection_agent()
    result = agent.invoke([HumanMessage("What are benefits of IF?")])

Here's what happens:

1. State starts as: [HumanMessage("What are benefits of IF?")]

2. Execute "generate" node:
   - Calls generate_initial_response([HumanMessage(...)])
   - Returns AIMessage(tool_calls=[{answer, reflection, search_queries}])
   - State becomes: [HumanMessage, AIMessage]

3. Follow edge to "execute_tools":
   - Calls execute_tools([HumanMessage, AIMessage])
   - Returns [ToolMessage(search results)]
   - State becomes: [HumanMessage, AIMessage, ToolMessage]

4. Follow edge to "revise":
   - Calls revise_answer([HumanMessage, AIMessage, ToolMessage])
   - Returns AIMessage(tool_calls=[{improved answer, references}])
   - State becomes: [HumanMessage, AIMessage, ToolMessage, AIMessage]

5. Execute conditional edge:
   - Calls should_continue([...all messages...])
   - Returns "execute_tools" (if tool_count < MAX_ITERATIONS)
   - Goes back to step 3 and repeats

6. Eventually should_continue returns END:
   - Graph execution stops
   - Returns final state (all messages)

You can then extract the final answer from the last AIMessage!
"""


# ============================================================================
# STATE FLOW EXAMPLE
# ============================================================================

"""
Iteration 1:
  State: [HumanMessage]
  → generate
  State: [HumanMessage, AIMessage(initial)]
  → execute_tools
  State: [HumanMessage, AIMessage(initial), ToolMessage]
  → revise
  State: [HumanMessage, AIMessage(initial), ToolMessage, AIMessage(revised1)]
  → should_continue: "execute_tools"

Iteration 2:
  State: [Human, AI(initial), Tool, AI(revised1)]
  → execute_tools
  State: [Human, AI(initial), Tool, AI(revised1), ToolMessage]
  → revise
  State: [Human, AI(initial), Tool, AI(revised1), Tool, AIMessage(revised2)]
  → should_continue: END

Final state returned with 6 messages total.
"""


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['create_reflection_agent']