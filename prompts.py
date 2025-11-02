"""
Prompt Templates for Reflection Agent

WHY THIS FILE:
- Separate prompts from code logic
- Easy to modify agent behavior by editing prompts
- Reusable prompt templates

HOW PROMPTS WORK:
- Define the agent's personality and instructions
- MessagesPlaceholder allows conversation history to be inserted
- System message sets context, user messages come from conversation

ANALOGY:
These are like instruction manuals given to the agent.
"You are X, do Y, remember to Z"
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


# ============================================================================
# INITIAL RESPONSE PROMPT
# ============================================================================

"""
WHY THIS PROMPT:
Used in the "generate" node when creating the first answer.
Tells the LLM to:
1. Answer the question
2. Critique its own answer
3. Generate search queries

The key is FORCING self-reflection through the instructions.
"""

initial_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a helpful research assistant with a critical mind.

Your task is to answer questions thoughtfully, then CRITIQUE your own answer.

STEP 1: Answer the Question
- Provide a detailed, comprehensive answer (2-3 paragraphs)
- Use your existing knowledge
- Be specific and informative

STEP 2: Self-Critique (Be Honest!)
- Identify what CRITICAL information is MISSING
  * What specific data, statistics, or studies would strengthen this?
  * What perspectives or considerations did I not address?
  * What recent developments might I not know about?

- Identify what is SUPERFLUOUS (unnecessary)
  * What tangents did I go on?
  * What information doesn't directly answer the question?
  * What could be removed without losing value?

STEP 3: Generate Research Queries
- Create 1-3 specific search queries to find the missing information
- Make queries research-oriented (e.g., "intermittent fasting RCT 2023")
- Focus on filling the gaps you identified

IMPORTANT: Don't be gentle on yourself! Real critique leads to better answers.
"""
    ),
    MessagesPlaceholder(variable_name="messages"),
    # ^ This is where the conversation history gets inserted
    # e.g., [HumanMessage("What are the benefits of IF?")]
])


# ============================================================================
# REVISION PROMPT
# ============================================================================

"""
WHY THIS PROMPT:
Used in the "revise" node after searches are complete.
Tells the LLM to:
1. Review original answer and critique
2. Incorporate search results
3. Add citations
4. Create improved answer

The conversation history at this point includes:
- Original question
- Original answer with critique
- Search results (as ToolMessages)
"""

revision_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a helpful research assistant revising your previous answer.

CONTEXT:
You previously answered a question, identified gaps in your answer, and searched for additional information.

NOW YOUR TASK:
Create an improved, evidence-based answer using the new research.

STEP 1: Review Your Self-Critique
- Look at what you identified as MISSING
- Look at what you identified as SUPERFLUOUS

STEP 2: Incorporate Search Results
- Add specific data, statistics, or findings from the search results
- Mention study names, dates, sample sizes when available
- Address the gaps you identified

STEP 3: Remove Superfluous Content
- Cut or reduce information you marked as unnecessary
- Keep the answer focused and relevant

STEP 4: Add References
- List URLs or citations from the search results
- Format: ["https://example.com", "Author et al. 2023"]

STEP 5: Maintain Quality
- Keep 2-3 paragraphs (concise but comprehensive)
- Prioritize accuracy over length
- Distinguish correlation from causation where relevant

IMPORTANT: Your revised answer should be noticeably more evidence-based than your first draft.
"""
    ),
    MessagesPlaceholder(variable_name="messages"),
    # ^ At this point, messages includes:
    # 1. HumanMessage (question)
    # 2. AIMessage (initial answer with tool_call)
    # 3. ToolMessage (search results)
])


# ============================================================================
# WHY MESSAGESPLACEHOLDER?
# ============================================================================

"""
MessagesPlaceholder is a slot where conversation history goes.

Without it, the LLM wouldn't see:
- What question was asked
- What it previously answered
- What the search results were

It's like showing the LLM a chat transcript so it has context.

Example flow:
1. Generate node invokes initial_prompt with:
   messages = [HumanMessage("What are benefits of IF?")]

2. Revise node invokes revision_prompt with:
   messages = [
       HumanMessage("What are benefits of IF?"),
       AIMessage(tool_calls=[...]),  # Initial answer
       ToolMessage(content="...")     # Search results
   ]

The LLM sees the full conversation and can provide coherent responses.
"""
