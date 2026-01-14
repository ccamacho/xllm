# Multi-Agent System with Google ADK & A2A Protocol

A distributed multi-agent system using [Google's Agent Development Kit (ADK)](https://google.github.io/adk-docs/) and the [A2A Protocol](https://a2a-protocol.org/) for agent-to-agent communication.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Router Agent (port 8000)                    │
│                                                                  │
│  Uses RemoteA2aAgent - NO tools, only sub_agents                │
│  Routes queries to appropriate specialist agent                  │
└────────────────────────┬────────────────────────────────────────┘
                         │ A2A Protocol (HTTP/JSON-RPC)
          ┌──────────────┴──────────────┐
          ▼                             ▼
┌─────────────────────┐     ┌─────────────────────┐
│ Weather Agent       │     │ Calculator Agent    │
│ (port 8001)         │     │ (port 8002)         │
│                     │     │                     │
│ Tools:              │     │ Tools:              │
│ - get_weather()     │     │ - calculate()       │
│                     │     │ - convert_units()   │
│                     │     │ - calculate_percent │
└─────────────────────┘     └─────────────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

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
python a2a_server.py --agent weather --port 8001

# Terminal 2: Calculator Agent
python a2a_server.py --agent calculator --port 8002

# Terminal 3: Router Agent (requires agents above)
python a2a_server.py --agent router --port 8000
```

### 4. Test the System

```bash
# Terminal 4: Run demo
python test_agents_a2a.py --url http://localhost:8000

# Or interactive mode
python test_agents_a2a.py --interactive
```

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
- **Calculator Agent** (`agents/calculator_agent.py`): `calculate()`, `convert_units()`, `calculate_percentage()` tools

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
python langfuse_export_traces.py --limit 100

# Run CLEAR evaluation
run-clear-eval-analysis \
  --provider google \
  --data-path clear/traces/clear_langfuse_traces.csv \
  --output-dir clear/results \
  --agent-mode True

# View dashboard
run-clear-eval-dashboard --port 8501
```

## Project Structure

```
xllm/
├── agents/
│   ├── __init__.py
│   ├── router_agent.py     # Router using RemoteA2aAgent (no tools)
│   ├── weather_agent.py    # Weather agent with tools
│   └── calculator_agent.py # Calculator agent with tools
├── a2a_server.py           # A2A HTTP server for any agent
├── test_agents_a2a.py      # A2A client for testing
├── langfuse_export_traces.py # Export traces for CLEAR
├── clear/                  # CLEAR evaluation assets
│   ├── traces/
│   └── results/
└── CLEAR/                  # IBM CLEAR repository
```

## Resources

- [Google ADK Docs](https://google.github.io/adk-docs/)
- [A2A Protocol](https://a2a-protocol.org/)
- [RemoteA2aAgent](https://google.github.io/adk-docs/agents/remote-a2a-agent/)
- [Langfuse](https://langfuse.com/docs)
- [IBM CLEAR](https://github.com/IBM/CLEAR)
