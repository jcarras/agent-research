# -*- coding: utf-8 -*-
"""
Main Entry Point for Reflection Agent

WHY THIS FILE:
- User-facing execution script
- Handles running the agent
- Displays results nicely
- Easy to customize for different use cases

HOW TO RUN:
    python main.py
"""

from langchain_core.messages import HumanMessage, AIMessage

from graph import create_reflection_agent


# ============================================================================
# RESULT EXTRACTION HELPERS
# ============================================================================

"""
WHY THESE FUNCTIONS:
After the agent runs, we get a list of messages.
These helpers extract the relevant information to display.
"""

def extract_initial_answer(messages):
    """
    Find and extract the initial answer from messages

    WHAT IT DOES:
    Loops through messages to find the first AIMessage with an
    "AnswerQuestion" tool call (the initial response).

    RETURNS:
    - Dictionary with answer, reflection, search_queries
    - None if not found
    """

    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            if msg.tool_calls[0]["name"] == "AnswerQuestion":
                return msg.tool_calls[0]["args"]
    return None


def extract_final_answer(messages):
    """
    Find and extract the final revised answer from messages

    WHAT IT DOES:
    Loops BACKWARDS through messages to find the most recent
    "ReviseAnswer" tool call (the final polished response).

    WHY BACKWARDS:
    The final answer is at the end of the message list.
    Searching backwards finds it immediately.

    RETURNS:
    - Dictionary with answer, reflection, search_queries, references
    - None if not found
    """

    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.tool_calls:
            if msg.tool_calls[0]["name"] == "ReviseAnswer":
                return msg.tool_calls[0]["args"]
    return None


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

"""
WHY THESE FUNCTIONS:
Make the output pretty and readable.
Separates display logic from core agent logic.
"""

def display_header(question):
    """Display a nice header"""
    print("=" * 70)
    print("🔬 REFLECTION AGENT")
    print("=" * 70)
    print(f"\n❓ Question: {question}\n")


def display_initial_answer(initial):
    """Display the initial answer and self-critique"""
    print("-" * 70)
    print("📝 INITIAL ANSWER")
    print("-" * 70)
    print(initial["answer"])

    print(f"\n💭 Self-Critique:")
    print(f"   Missing: {initial['reflection']['missing']}")
    print(f"   Superfluous: {initial['reflection']['superfluous']}")

    print(f"\n🔍 Generated Queries:")
    for i, q in enumerate(initial['search_queries'], 1):
        print(f"   {i}. {q}")


def display_final_answer(revised):
    """Display the final revised answer with references"""
    print("\n" + "-" * 70)
    print("✨ FINAL REVISED ANSWER")
    print("-" * 70)
    print(revised["answer"])

    if revised.get("references"):
        print(f"\n📚 References:")
        for i, ref in enumerate(revised["references"], 1):
            print(f"   [{i}] {ref}")


def display_footer():
    """Display completion message"""
    print("\n" + "=" * 70)
    print("✅ Agent execution complete!")
    print("=" * 70 + "\n")


# ============================================================================
# MAIN EXECUTION FUNCTION
# ============================================================================

def run_agent(question: str):
    """
    Run the Reflection Agent on a question

    PARAMETERS:
    - question: str - The question to answer

    WHAT IT DOES:
    1. Creates the agent (builds the graph)
    2. Invokes it with the question
    3. Extracts and displays results

    RETURNS:
    - Dictionary with initial and final answers
      (useful if you want to programmatically use results)
    """

    # Display header
    display_header(question)

    # Create the agent
    # This builds the LangGraph workflow
    agent = create_reflection_agent()

    # Prepare initial message
    # Wrap user's question in HumanMessage
    initial_messages = [HumanMessage(content=question)]

    try:
        # ====================================================================
        # INVOKE THE AGENT
        # ====================================================================

        """
        This is where the magic happens!

        agent.invoke() runs the entire workflow:
        1. Generate initial answer
        2. Search for missing info
        3. Revise with findings
        4. Repeat if needed
        5. Return final state

        result_messages is a list of all messages (state history)
        """

        result_messages = agent.invoke(initial_messages)


        # ====================================================================
        # EXTRACT RESULTS
        # ====================================================================

        """
        Parse the message list to get:
        - Initial answer (first AnswerQuestion tool call)
        - Final answer (last ReviseAnswer tool call)
        """

        initial = extract_initial_answer(result_messages)
        final = extract_final_answer(result_messages)


        # ====================================================================
        # DISPLAY RESULTS
        # ====================================================================

        """
        Show the user:
        1. Initial answer with self-critique
        2. Final improved answer with references
        """

        if initial:
            display_initial_answer(initial)

        if final:
            display_final_answer(final)
        elif initial:
            # If no final (shouldn't happen), show initial as final
            print("\n⚠️  No revision occurred (using initial answer)")

        display_footer()


        # ====================================================================
        # RETURN STRUCTURED DATA
        # ====================================================================

        """
        Return both answers for programmatic use
        (in case you want to save to database, use in API, etc.)
        """

        return {
            "question": question,
            "initial_answer": initial,
            "final_answer": final,
            "message_count": len(result_messages)
        }


    except Exception as e:
        # ====================================================================
        # ERROR HANDLING
        # ====================================================================

        print(f"\n❌ Error: {e}")

        # Print full traceback for debugging
        import traceback
        traceback.print_exc()

        return {
            "question": question,
            "error": str(e)
        }


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

"""
This runs when you execute the file directly:
    python reflection_agent/main.py
"""

if __name__ == "__main__":

    # ========================================================================
    # EXAMPLE QUESTION
    # ========================================================================

    """
    You can change this to test different questions!

    Try:
    - "What are the health benefits of intermittent fasting?"
    - "How does climate change affect ocean acidification?"
    - "What are the latest developments in quantum computing?"
    - "What are the best practices for React performance optimization?"
    """

    question = "What are the health benefits of intermittent fasting?"


    # ========================================================================
    # RUN THE AGENT
    # ========================================================================

    result = run_agent(question)


    # ========================================================================
    # OPTIONAL: SAVE RESULTS
    # ========================================================================

    """
    You could save results to a file, database, etc.

    Example:
        import json
        with open('results.json', 'w') as f:
            json.dump(result, f, indent=2)
    """


# ============================================================================
# USING AS A MODULE
# ============================================================================

"""
You can import and use this in other scripts:

    from main import run_agent

    result = run_agent("Your question here")
    print(result['final_answer']['answer'])

Or customize the display:

    from graph import create_reflection_agent
    from langchain_core.messages import HumanMessage

    agent = create_reflection_agent()
    messages = agent.invoke([HumanMessage("Question")])

    # Process messages however you want
    ...
"""
