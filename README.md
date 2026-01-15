# Multi-Agent System with Google ADK & A2A Protocol

A distributed multi-agent system using [Google's Agent Development Kit (ADK)](https://google.github.io/adk-docs/) and the [A2A Protocol](https://a2a-protocol.org/) for agent-to-agent communication.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Router Agent (port 8000)                             │
│                                                                              │
│  Uses RemoteA2aAgent - NO tools, only sub_agents                            │
│  Routes queries to appropriate specialist agent                              │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ A2A Protocol (HTTP/JSON-RPC)
             ┌──────────────────┴──────────────────┐
             ▼                                     ▼
┌─────────────────────────┐         ┌─────────────────────────────────────────┐
│ Weather Agent           │         │ Calculator Agent (port 8002)            │
│ (port 8001)             │         │                                         │
│                         │         │ Tools:                                  │
│ Tools:                  │         │ - basic_calculate()                     │
│ - get_weather()         │         │ - convert_units()                       │
│                         │         │ - calculate_percentage()                │
└─────────────────────────┘         └────────────────┬────────────────────────┘
                                                     │ Delegates advanced math
                                                     ▼
                                    ┌─────────────────────────────────────────┐
                                    │ Advanced Calculator Agent (port 8003)   │
                                    │                                         │
                                    │ Tools:                                  │
                                    │ - advanced_calculate()                  │
                                    │   (sqrt, sin, cos, tan, log, exp,       │
                                    │    factorial, chimichanga)              │
                                    └─────────────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (creates .venv automatically)
uv sync
```

> **Note:** `uv sync` creates a virtual environment in `.venv/` and installs all dependencies there. Use `uv run` to execute commands within this environment, or activate it manually with `source .venv/bin/activate`.

### 2. Configure Environment

Create `.env` file:

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key

# Optional: Langfuse tracing
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

### 3. Start Agents (Each in Separate Terminal)

```bash
# Terminal 1: Weather Agent
uv run python a2a_server.py --agent weather --port 8001

# Terminal 2: Advanced Calculator Agent (must start before Calculator)
uv run python a2a_server.py --agent advanced_calculator --port 8003

# Terminal 3: Calculator Agent
uv run python a2a_server.py --agent calculator --port 8002

# Terminal 4: Router Agent (requires agents above)
uv run python a2a_server.py --agent router --port 8000
```

### 4. Test the System

```bash
# Terminal 5: Run demo
uv run python test_agents_a2a.py --url http://localhost:8000

# Or interactive mode
uv run python test_agents_a2a.py --interactive
```

### 5. Using ADK Web Interface (Optional)

The Google ADK provides a web-based interface (`adk web`) for interactively testing agents. This project includes two configurations:

**Option A: Subagent Mode** (uses `sub_agents` for routing)

```bash
# First, start the remote agents (in separate terminals)
uv run python a2a_server.py --agent weather --port 8001
uv run python a2a_server.py --agent advanced_calculator --port 8003
uv run python a2a_server.py --agent calculator --port 8002

# Then launch adk web from the subagent directory
uv run adk web adk-web   (and choose subagent in the menu)
```

**Option B: Agent-as-Tool Mode** (uses `AgentTool` wrapper for routing)

```bash
# First, start the remote agents (in separate terminals)
uv run python a2a_server.py --agent weather --port 8001
uv run python a2a_server.py --agent advanced_calculator --port 8003
uv run python a2a_server.py --agent calculator --port 8002

# Then launch adk web from the agent-as-tool directory
uv run adk web adk-web (and choose agent_as_tool in the menu)
```

Once running, open `http://localhost:8000` in your browser to interact with the multi-agent system through a chat interface.

## Key Components

### Router Agent (`agents/router_agent.py`)

Uses `RemoteA2aAgent` for true A2A communication - **no tools**, only sub-agents:

```python
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

weather_remote = RemoteA2aAgent(
    name="weather_agent",
    agent_card="http://localhost:8001/.well-known/agent-card.json",
)

router_agent = Agent(
    name="router_agent",
    sub_agents=[weather_remote, calculator_remote],  # NO tools!
)
```

### Specialist Agents

Each agent has its own tools and runs as an independent A2A server:

- **Weather Agent** (`agents/weather_agent.py`): `get_weather()` tool
- **Calculator Agent** (`agents/calculator_agent.py`): `basic_calculate()`, `convert_units()`, `calculate_percentage()` tools. Delegates advanced math to the Advanced Calculator.
- **Advanced Calculator Agent** (`agents/advanced_calculator_agent.py`): `advanced_calculate()` tool for sqrt, sin, cos, tan, log, exp, factorial, and custom operations like `chimichanga`

#### Custom Operations

The `chimichanga` function is a custom mathematical operation that multiplies any number by 3.75:

```python
# In advanced_calculator_agent.py
safe_dict = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    # ...
    "chimichanga": lambda x: x * 3.75,  # Custom operation
}
```

Example: `chimichanga(7)` → `7 × 3.75 = 26.25`

## Tracing with Langfuse

All A2A servers auto-capture traces via `GoogleADKInstrumentor`:

```python
from openinference.instrumentation.google_adk import GoogleADKInstrumentor
GoogleADKInstrumentor().instrument()
```

Traces are sent to Langfuse via OTLP. View at: https://cloud.langfuse.com

## IBM CLEAR Evaluation

Export traces and evaluate with LLM-as-a-Judge:

```bash
# Export traces from Langfuse to CSV
uv run python langfuse_export_traces.py --limit 100

# Run CLEAR evaluation
uv run run-clear-eval-analysis \
  --provider google \
  --data-path clear/traces/clear_langfuse_traces.csv \
  --output-dir clear/results \
  --agent-mode True \
  --perform-generation False

# View dashboard
uv run run-clear-eval-dashboard --port 8501
```

### Understanding `--perform-generation`

The `--perform-generation` flag controls whether CLEAR generates new responses or evaluates existing ones:

| Mode | Command | Use Case |
|------|---------|----------|
| **Evaluate existing responses** | `--perform-generation False` | Evaluate your **actual agent outputs** from the `response` column in your CSV |
| **Generate new responses** | `--perform-generation True` (default) | Have CLEAR's LLM generate responses to compare against or evaluate |

#### When to use each mode:

**`--perform-generation False`** (Recommended for agent evaluation)
```bash
run-clear-eval-analysis \
  --provider google \
  --data-path clear/traces/clear_langfuse_traces.csv \
  --output-dir clear/results \
  --agent-mode True \
  --perform-generation False
```
- ✅ Evaluates your **actual agent responses** captured in traces
- ✅ Identifies issues in your real system behavior
- ✅ Required when your agents have custom tools/functions (like `chimichanga`)
- Your CSV must have a `response` column with agent outputs

**`--perform-generation True`** (Default)
```bash
run-clear-eval-analysis \
  --provider google \
  --data-path clear/traces/clear_langfuse_traces.csv \
  --output-dir clear/results \
  --agent-mode True \
  --perform-generation True
```
- Uses CLEAR's LLM (e.g., Gemini) to generate new responses
- ⚠️ The LLM won't know about your custom agent tools/functions
- Useful for baseline comparisons or when you only have inputs (no responses)

## Project Structure

```
xllm/
├── pyproject.toml              # Project dependencies (uv)
├── agents/
│   ├── __init__.py
<<<<<<< Updated upstream
│   ├── router_agent.py         # Router using RemoteA2aAgent (sub_agents mode)
│   ├── router_agent_tool.py    # Router using AgentTool (tools mode)
│   ├── weather_agent.py        # Weather agent with tools
│   ├── calculator_agent.py     # Calculator agent (delegates to advanced)
│   └── advanced_calculator_agent.py  # Advanced math + custom operations
├── adk-web/                    # ADK Web interface configurations
│   ├── subagent/               # Uses sub_agents for routing
│   │   └── agent.py
│   └── agent-as-tool/          # Uses AgentTool for routing
│       └── agent.py
├── a2a_server.py               # A2A HTTP server for any agent
├── test_agents_a2a.py          # A2A client for testing
├── langfuse_export_traces.py   # Export traces for CLEAR
├── langfuse_traces/            # Exported traces with documentation
│   ├── all/                    # Complete trace exports (CSV + JSON + README)
│   ├── 01_no_delegation_greeting/   # Router-only example
│   └── 02_delegation_weather/       # Router → Weather delegation
├── clear/                      # CLEAR evaluation assets
=======
│   ├── router_agent.py     # Router using RemoteA2aAgent (sub_agents mode)
│   ├── router_agent_tool.py # Router using AgentTool (tools mode)
│   ├── weather_agent.py    # Weather agent with tools
│   └── calculator_agent.py # Calculator agent with tools
├── adk-web/                # ADK Web interface configurations
│   ├── subagent/           # Uses sub_agents for routing
│   │   └── agent.py        # Exports root_agent for adk web
│   └── agent_as_tool/      # Uses AgentTool for routing
│       └── agent.py        # Exports root_agent for adk web
├── a2a_server.py           # A2A HTTP server for any agent
├── test_agents_a2a.py      # A2A client for testing
├── langfuse_export_traces.py # Export traces for CLEAR
├── clear/                  # CLEAR evaluation assets
>>>>>>> Stashed changes
│   ├── traces/
│   └── results/
└── CLEAR-gemini/               # IBM CLEAR with Gemini support
```

## Trace Documentation

The `langfuse_traces/` folder contains exported traces with detailed documentation showing how queries flow through the multi-agent system:

| Folder | Pattern | Example Query |
|--------|---------|---------------|
| `01_no_delegation_greeting/` | Router only | "Hello! What can you do?" |
| `02_delegation_weather/` | Router → Weather | "What's the weather in Tokyo?" |

Each folder contains:
- `traces.csv` - The relevant traces for that example
- `README.md` - Step-by-step explanation with trace IDs and flow diagrams

The `all/` folder contains the complete trace export in both CSV and JSON formats, including documentation of all 7 example query types (greeting, weather, basic math, unit conversion, sqrt, trigonometry, and chimichanga). See `all/*_README.md` for:
- Detailed flow diagrams for each delegation pattern
- Trace ID correlation across agents
- CSV vs JSON format comparison

## Resources

- [uv - Python Package Manager](https://docs.astral.sh/uv/)
- [Google ADK Docs](https://google.github.io/adk-docs/)
- [ADK Web Interface](https://google.github.io/adk-docs/get-started/quickstart/#step-4-run-your-agent)
- [A2A Protocol](https://a2a-protocol.org/)
- [RemoteA2aAgent](https://google.github.io/adk-docs/agents/remote-a2a-agent/)
- [Langfuse](https://langfuse.com/docs)
- [IBM CLEAR](https://github.com/IBM/CLEAR)
