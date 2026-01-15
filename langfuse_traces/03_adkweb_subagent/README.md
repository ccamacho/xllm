# Example 3: ADK Web with Subagent Mode (Router → Calculator Agent)

**Query:** `"how much is 5 *4"`

## Trace Flow

```
Step 1: Router receives query via ADK Web
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trace ID: 1793fd7f673e4b6ae6ded90493e9b6d2                                  │
│ Agent:    router_agent (ADK Web)                                            │
│ Latency:  1902ms (total invocation time)                                    │
│                                                                             │
│ Input:    "how much is 5 *4"                                                │
│ Action:   Detects calculation → calls transfer_to_agent(calculator_agent)   │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
Step 2: Calculator Agent processes query
┌─────────────────────────────────────────────────────────────────────────────┐
│ Agent:    calculator_agent (port 8002)                                      │
│ Latency:  1247ms                                                            │
│                                                                             │
│ Input:    "how much is 5 *4" + transfer context                             │
│ Action:   Calls basic_calculate("5 * 4") tool                               │
│ Output:   { "expression": "5 * 4", "result": 20, "type": "basic arithmetic"}│
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
                    Response: "5 * 4 is 20."
```

## Explanation

This trace demonstrates the **Subagent Mode** using ADK Web interface:

1. User submits query through ADK Web UI
2. Router agent receives the query
3. Router detects a calculation request
4. Router uses `transfer_to_agent` to delegate to `calculator_agent`
5. Calculator agent calls `basic_calculate("5 * 4")` tool via A2A protocol
6. Calculator returns result: `20`
7. Router formats and returns: "5 * 4 is 20."

### Key Difference: Subagent Mode

In **Subagent Mode**, the router uses `sub_agents` with `transfer_to_agent`:
- The router completely hands off control to the sub-agent
- Context is passed with the transfer
- The sub-agent's response is returned directly

## Traces in This Folder

| Component | Latency | Action |
|-----------|---------|--------|
| `invocation [subagent]` | 1902ms | Total request time |
| `agent_run [router_agent]` | 1874ms | Router processing + delegation |
| `agent_run [calculator_agent]` | 1247ms | Calculator processing |
| `call_llm` | 1872ms | LLM inference for routing decision |
| `a2a.client.transports.jsonrpc` | 1215ms | A2A communication overhead |

## Latency Analysis

- **Total invocation:** 1902ms
- **Router processing:** 1874ms (includes waiting for calculator)
- **Calculator agent:** 1247ms (tool call + response generation)
- **A2A transport:** 1215ms (JSON-RPC communication)

## Configuration

This trace was generated using:
```bash
uv run adk web adk-web/subagent
```

The subagent configuration uses `router_agent` with `sub_agents=[weather_remote, calculator_remote]`.
