# Extendable Research Agent

A production-ready Reflection Agent the provides research on a topic by critiquing responses to understand what additional questions need to be asked to answer query. It then does web searches to answer unknown questions.

## 🚀 Quick Start

Install Python 3 if needed.

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Get your free Google API key from https://makersuite.google.com/app/apikey

# 3. Add it to .env.dev
echo "GOOGLE_API_KEY=your_key_here" > .env.dev

# 4. Run the agent
python3 main.py
```

## 📁 File Structure

```
reflection_agent/
├── __init__.py          # Package initialization & public API
├── config.py            # Configuration settings
├── models.py            # Pydantic data models
├── prompts.py           # LLM prompt templates
├── tools.py             # External tools (search, etc.)
├── nodes.py             # Graph node functions (core logic)
├── graph.py             # LangGraph workflow construction
├── main.py              # Entry point & CLI
└── README.md            # This file
```
---

## 📄 File Explanations

### 1. `config.py`

**What:** All configuration settings in one place
**Contains:**
- Model selection (`MODEL_NAME`)
- Temperature settings
- MAX_ITERATIONS
- Search result limits
- Verbose flag

**Why:** Change behavior without editing code

**Example:**
```python
# Want 3 iterations instead of 2?
# Just edit config.py:
MAX_ITERATIONS = 3
```

---

### 2. `models.py`

**What:** Pydantic models defining data structure
**Contains:**
- `Reflection` - Self-critique structure
- `AnswerQuestion` - Initial response format
- `ReviseAnswer` - Revised response format

**Why:** Type safety and LLM tool binding

**How it works:**
1. Define Pydantic model
2. LangChain converts to LLM tool schema
3. LLM returns structured data matching model
4. Pydantic validates automatically

**Example:**
```python
class Reflection(BaseModel):
    missing: str = Field(description="What's missing")
    superfluous: str = Field(description="What's unnecessary")
```

---

### 3. `prompts.py`

**What:** System prompts for the LLM
**Contains:**
- `initial_prompt` - For generating first answer
- `revision_prompt` - For revising with research

**Why:** Separate prompts from code for easy tweaking

**How it works:**
Uses `ChatPromptTemplate` with `MessagesPlaceholder`:
- System message sets context
- MessagesPlaceholder inserts conversation history

**Example:**
```python
initial_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a research assistant..."),
    MessagesPlaceholder(variable_name="messages")
])
```

---

### 4. `tools.py`

**What:** External tools the agent can use
**Contains:**
- `search_tool` - DuckDuckGo search

**Why:** Centralize tool initialization

**How it works:**
```python
search_tool = DuckDuckGoSearchRun()

# Later in nodes.py:
result = search_tool.run("query")
```

**Easy to extend:**
```python
# Add Wikipedia
from langchain_community.tools import WikipediaQueryRun
wikipedia_tool = WikipediaQueryRun()
```

---

### 5. `nodes.py`

**What:** The core processing logic
**Contains:**
- `generate_initial_response()` - Creates first answer + critique
- `execute_tools()` - Runs searches
- `revise_answer()` - Improves answer with research
- `should_continue()` - Decides whether to iterate

**Why:** Each node is one step in the workflow

**How it works:**

**Node = Function that:**
- Takes `state` (conversation history) as input
- Processes it (call LLM, run tools, etc.)
- Returns new messages to add to state

**Flow:**
```python
# 1. Generate
response = initial_chain.invoke({"messages": messages})
# Returns: AIMessage with answer + critique + queries

# 2. Execute Tools
for query in search_queries:
    result = search_tool.run(query)
# Returns: ToolMessage with search results

# 3. Revise
response = revisor_chain.invoke({"messages": state})
# Returns: AIMessage with improved answer + references
```

---

### 6. `graph.py`

**What:** Assembles nodes into a workflow
**Contains:**
- `create_reflection_agent()` - Builds the LangGraph

**Why:** Define how nodes connect

**How it works:**

**Step 1: Create graph**
```python
graph = MessageGraph()
```

**Step 2: Add nodes**
```python
graph.add_node("generate", generate_initial_response)
graph.add_node("execute_tools", execute_tools)
graph.add_node("revise", revise_answer)
```

**Step 3: Add edges (connections)**
```python
# Fixed edges (always)
graph.add_edge("generate", "execute_tools")
graph.add_edge("execute_tools", "revise")

# Conditional edge (decision)
graph.add_conditional_edges("revise", should_continue)
```

**Step 4: Set starting point**
```python
graph.set_entry_point("generate")
```

**Step 5: Compile**
```python
return graph.compile()
```

---

### 7. `main.py`

**What:** User-facing execution script
**Contains:**
- `run_agent()` - Main execution function
- Helper functions for display
- CLI interface

**Why:** Separate execution from logic

**How it works:**
```python
def run_agent(question: str):
    # 1. Create agent
    agent = create_reflection_agent()

    # 2. Invoke with question
    result_messages = agent.invoke([HumanMessage(content=question)])

    # 3. Extract results
    initial = extract_initial_answer(result_messages)
    final = extract_final_answer(result_messages)

    # 4. Display
    display_initial_answer(initial)
    display_final_answer(final)

    # 5. Return structured data
    return {"initial_answer": initial, "final_answer": final}
```

---

### 8. `__init__.py`

**What:** Makes `reflection_agent` a Python package (optional)
**Contains:**
- Package initialization (can be empty)

**Note:** For this simple project structure, you can use direct imports:
```python
from graph import create_reflection_agent
from main import run_agent
```

---

## 🔑 Setup Instructions

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Get Your Google API Key (Free)

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy your API key

**Note:** No credit card required! The free tier is generous (60 requests/minute).

### 3. Configure Your API Key

Edit the `.env.dev` file and add your API key:

```bash
GOOGLE_API_KEY=your_api_key_here
```

### 4. Run the Agent

```bash
python3 main.py
```

### Available Gemini Models

The agent is configured to use `gemini-2.5-flash` (fast and cost-effective). You can change the model in `config.py`:

- **gemini-2.5-flash** - Fast, efficient, recommended (default)
- **gemini-2.5-pro** - More powerful, better for complex reasoning
- **gemini-2.0-flash** - Alternative fast model
- **gemini-pro-latest** - Latest stable Gemini Pro

All models support:
- ✅ Tool calling (required for this agent)
- ✅ 60 requests/minute (free tier)
- ✅ No credit card required

---

## 🚀 How to Use

### Command Line (Simplest)

```bash
python main.py
```

### As a Script

```python
from main import run_agent

result = run_agent("What are the health benefits of intermittent fasting?")
print(result['final_answer']['answer'])
```

### Advanced Usage

```python
from graph import create_reflection_agent
from langchain_core.messages import HumanMessage

# Create agent
agent = create_reflection_agent()

# Run agent
messages = agent.invoke([HumanMessage("Your question")])

# Process messages however you want
for msg in messages:
    print(type(msg), msg)
```

---

## 🔧 How to Customize

### Change Settings

Edit `config.py`:
```python
MAX_ITERATIONS = 3  # More iterations
TEMPERATURE = 0.5   # More deterministic
MODEL_NAME = "gemini-2.5-pro"  # More powerful model (or "gemini-2.5-flash" for faster)
```

### Modify Prompts

Edit `prompts.py`:
```python
initial_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a nutrition expert..."),  # Custom persona
    MessagesPlaceholder(variable_name="messages")
])
```

### Add New Tools

Edit `tools.py`:
```python
from langchain_community.tools import WikipediaQueryRun

wikipedia_tool = WikipediaQueryRun()
__all__ = ['search_tool', 'wikipedia_tool']
```

Then use in `nodes.py`:
```python
from tools import search_tool, wikipedia_tool

def execute_tools(state):
    # Use wikipedia_tool.run(...) here
    ...
```

### Change Workflow

Edit `graph.py`:
```python
# Add a new node
graph.add_node("fact_check", fact_check_function)

# Insert into flow
graph.add_edge("revise", "fact_check")
graph.add_edge("fact_check", END)
```

---

## 📊 Data Flow

```
User Question
    │
    ▼
[HumanMessage("Question")]
    │
    ▼
generate_initial_response()
    │
    ▼
AIMessage(tool_calls=[{
    answer: "...",
    reflection: {missing, superfluous},
    search_queries: [...]
}])
    │
    ▼
execute_tools()
    │
    ▼
ToolMessage(content="search results")
    │
    ▼
revise_answer()
    │
    ▼
AIMessage(tool_calls=[{
    answer: "improved...",
    references: [...]
}])
    │
    ▼
should_continue() → END or loop back
    │
    ▼
Final Answer Displayed
```

---

## 🧪 Testing Individual Modules

Each module can be tested independently:

### Test Models
```python
from models import AnswerQuestion, Reflection

# Validate data structure
data = {
    "answer": "Test answer",
    "reflection": {"missing": "X", "superfluous": "Y"},
    "search_queries": ["query 1"]
}
result = AnswerQuestion(**data)  # Will validate
```

### Test Prompts
```python
from prompts import initial_prompt
from langchain_core.messages import HumanMessage

messages = initial_prompt.format_messages(
    messages=[HumanMessage("Test question")]
)
print(messages)
```

### Test Tools
```python
from tools import search_tool

result = search_tool.run("intermittent fasting benefits")
print(result)
```

### Test Nodes
```python
from nodes import generate_initial_response
from langchain_core.messages import HumanMessage

response = generate_initial_response([HumanMessage("Test")])
print(response.tool_calls)
```

---

## 📝 Summary

| File | Purpose | Key Contents |
|------|---------|-------------|
| `config.py` | Settings | MODEL_NAME (Gemini), MAX_ITERATIONS, TEMPERATURE |
| `models.py` | Data structure | Reflection, AnswerQuestion, ReviseAnswer |
| `prompts.py` | LLM instructions | initial_prompt, revision_prompt |
| `tools.py` | External services | search_tool (DuckDuckGo) |
| `nodes.py` | Core logic | ChatGoogleGenerativeAI, node functions |
| `graph.py` | Workflow | create_reflection_agent() |
| `main.py` | User interface | run_agent(), display functions |
| `__init__.py` | Package API | Package metadata |

---

## 🎓 Learning Path

1. **Start with `main.py`** - See how it's used
2. **Read `graph.py`** - Understand the workflow
3. **Explore `nodes.py`** - See the core logic
4. **Check `models.py`** - Understand data structure
5. **Review `prompts.py`** - See how LLM is instructed
6. **Look at `tools.py`** - See external integrations
7. **Tweak `config.py`** - Customize behavior

Each file has extensive comments explaining WHY and HOW!

---

**Happy coding! 🚀**
