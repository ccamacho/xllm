# Multi-Agent System with Google ADK

A multi-agent system built with [Google ADK](https://google.github.io/adk-docs/) featuring weather and calculator agents, with full observability via Langfuse and evaluation via IBM CLEAR.

## Quick Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e CLEAR/

# Configure API keys in .env
cp .env.example .env
# Edit .env with your keys
```

**Required API Keys:**
- `GOOGLE_API_KEY` - [Get from Google AI Studio](https://aistudio.google.com/app/apikey)
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` - [Get from Langfuse](https://cloud.langfuse.com)

---

## 1. Running ADK Agents (Same Process)

All agents run together in one Python process with automatic routing:

```bash
# Interactive mode
python test_agents_adk.py

# Demo mode
python test_agents_adk.py --demo

# Single query
python test_agents_adk.py --query "What's the weather in Tokyo?"
```

**Architecture:**
```
┌─────────────────────────────────────────┐
│              Router Agent               │
│    (LLM decides which agent to use)     │
└─────────────┬───────────────┬───────────┘
              │               │
    ┌─────────▼─────┐  ┌──────▼──────┐
    │ Weather Agent │  │ Calculator  │
    │  get_weather  │  │  calculate  │
    └───────────────┘  └─────────────┘
```

---

## 2. Running A2A Agents (Separate Processes)

Expose agents as HTTP services using the [A2A Protocol](https://a2a-protocol.org/):

```bash
# Terminal 1: Start the router agent
python a2a_server.py --port 8000

# Terminal 2: Test with the client (also creates Langfuse traces)
python test_agents_a2a.py

# Or test with curl
curl http://localhost:8000/.well-known/agent-card.json
```

**Why A2A?** Other frameworks (LangChain, AutoGen, CrewAI) can discover and call your agents over HTTP.

**Tracing:** Both server and client create Langfuse traces, so you can evaluate A2A interactions with CLEAR.

---

## 3. Tracing with Langfuse

All agent runs are automatically traced to Langfuse when credentials are configured.

**What's captured:**
- Full conversation flow
- Tool calls and responses
- Token usage and latency
- Query classification tags

**View traces:** https://cloud.langfuse.com/traces

**Local storage:**
```bash
# Traces are also saved locally as JSON
ls traces/

# Export from Langfuse to CSV for CLEAR
python langfuse_export_traces.py
```

---

## 4. Evaluating with CLEAR

[IBM CLEAR](https://github.com/IBM/CLEAR) provides LLM-as-a-Judge evaluation using Gemini models.

### Workflow

```
1. Run agents          2. Export traces         3. Run CLEAR           4. View dashboard
   (ADK or A2A)    →      from Langfuse      →      evaluation      →      results
   
test_agents_adk.py  langfuse_export_       run-clear-eval-        run-clear-eval-
test_agents_a2a.py  traces.py              analysis ...           dashboard
```

### Step-by-Step

```bash
# 1. Run agents (both methods send traces to Langfuse)
python test_agents_adk.py --demo      # ADK method (same process)
# OR
python a2a_server.py --port 8000 &    # Start A2A server first
python test_agents_a2a.py             # A2A method (HTTP client)

# 2. Export ALL traces from Langfuse to CSV for CLEAR
#    (includes traces from both ADK and A2A runs)
python langfuse_export_traces.py --limit 100

# 3. Run CLEAR evaluation with Gemini
run-clear-eval-analysis \
  --provider google \
  --data-path clear/traces/clear_langfuse_traces.csv \
  --output-dir clear/results \
  --agent-mode True

# 4. View results in dashboard
run-clear-eval-dashboard --port 8501
# Upload: clear/results/*.zip
```

### Evaluation Criteria

CLEAR evaluates each agent response on:
- **Tool Selection** - Did it pick the right tool?
- **Response Accuracy** - Is the answer correct?
- **Routing Logic** - Was delegation appropriate?
- **Error Handling** - Are edge cases handled?
- **Response Clarity** - Is it clear and helpful?

---

## Project Structure

```
xllm/
├── agents/                 # Agent definitions
│   ├── agent.py            # Router agent (main entry)
│   ├── weather_agent.py    # Weather tools
│   └── calculator_agent.py # Math tools
├── langfuse_tracing.py     # Shared Langfuse utilities
├── langfuse_export_traces.py # Export traces for CLEAR
├── test_agents_adk.py      # Test via ADK (same process)
├── test_agents_a2a.py      # Test via A2A protocol (HTTP)
├── a2a_server.py           # A2A HTTP server
├── main.py                 # Basic CLI runner
├── traces/                 # Local trace JSONs
├── clear/                  # CLEAR evaluation
│   ├── traces/             # Input CSVs
│   └── results/            # Output analysis
└── CLEAR/                  # IBM CLEAR (with Google provider)
```

### Shared Tracing Module

`langfuse_tracing.py` provides shared utilities used by both test scripts:

- `setup_langfuse()` - Initialize Langfuse client
- `classify_query()` - Auto-tag queries (weather, calculation, etc.)
- `save_trace_locally()` - Save traces to local JSON files

`langfuse_export_traces.py` is a standalone script that exports traces from Langfuse to CSV for CLEAR evaluation.

---

## Resources

- [Google ADK Docs](https://google.github.io/adk-docs/)
- [A2A Protocol](https://a2a-protocol.org/)
- [Langfuse](https://langfuse.com/docs)
- [IBM CLEAR](https://github.com/IBM/CLEAR)
