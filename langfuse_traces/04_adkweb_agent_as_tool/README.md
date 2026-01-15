# Example 4: ADK Web with Agent-as-Tool Mode (Router → Calculator Agent)

**Query:** `"how much is 4*5"`

## Trace Flow

```
Step 1: Router receives query via ADK Web
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trace ID: 927849bbb00a82bf011d119bc56e4d4b                                  │
│ Agent:    router_agent_tool (ADK Web)                                       │
│ Latency:  3716ms (total invocation time)                                    │
│                                                                             │
│ Input:    "how much is 4*5"                                                 │
│ Action:   Detects calculation → invokes calculator_agent as a tool          │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
Step 2: Calculator Agent invoked as Tool
┌─────────────────────────────────────────────────────────────────────────────┐
│ Agent:    calculator_agent (port 8002)                                      │
│ Latency:  1196ms                                                            │
│                                                                             │
│ Input:    "4*5"                                                             │
│ Action:   Calls basic_calculate("4*5") tool                                 │
│ Output:   { "expression": "4*5", "result": 20, "type": "basic arithmetic"}  │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
Step 3: Router processes tool response
┌─────────────────────────────────────────────────────────────────────────────┐
│ Agent:    router_agent_tool                                                 │
│ Action:   Receives tool result, generates final response                    │
│ Reasoning: "The calculator_agent calculated the result of 4*5, which is 20" │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
                         Response: "20"
```

## Explanation

This trace demonstrates the **Agent-as-Tool Mode** using ADK Web interface:

1. User submits query through ADK Web UI
2. Router agent receives the query
3. Router detects a calculation request
4. Router invokes `calculator_agent` as a **tool** (wrapped with `AgentTool`)
5. Calculator agent calls `basic_calculate("4*5")` via A2A protocol
6. Calculator returns result to router as tool output
7. Router processes the tool result with reasoning
8. Router generates final response: "20"

### Key Difference: Agent-as-Tool Mode

In **Agent-as-Tool Mode**, the router uses `AgentTool` wrapper:
- Remote agents are wrapped as tools using `AgentTool(agent=remote_agent)`
- Router maintains control and receives tool results
- Router can reason about the result before responding
- Uses `PlanReActPlanner` for structured reasoning

The trace shows the router's internal reasoning:
> "The calculator_agent calculated the result of 4*5, which is 20. Now I can return this result to the user."

## Traces in This Folder

| Component | Latency | Action |
|-----------|---------|--------|
| `invocation [agent_as_tool]` | 3716ms | Total request time |
| `agent_run [router_agent_tool]` | 3679ms | Router processing + tool calls |
| `agent_run [calculator_agent]` | 1196ms | Calculator processing |
| `call_llm` (routing) | 1328ms | Initial LLM call for tool selection |
| `call_llm` (response) | 2348ms | Final LLM call for response generation |

## Latency Analysis

- **Total invocation:** 3716ms
- **Router processing:** 3679ms (includes tool call + response generation)
- **Calculator agent:** 1196ms (tool call + response)
- **LLM calls:** 1328ms + 2348ms = 3676ms (two LLM calls in ReAct pattern)

### Comparison with Subagent Mode

| Metric | Subagent Mode | Agent-as-Tool Mode |
|--------|---------------|-------------------|
| Total latency | 1902ms | 3716ms |
| LLM calls | 1 | 2 |
| Router control | Hands off | Maintains control |
| Reasoning visible | No | Yes (thought tokens) |

Agent-as-Tool mode is slower due to the additional LLM call for reasoning about the tool result, but provides more control and transparency.

## Configuration

This trace was generated using:
```bash
uv run adk web adk-web/agent-as-tool
```

The agent-as-tool configuration uses `router_agent_tool` with:
```python
tools=[weather_remote_tool, calculator_remote_tool]
planner=PlanReActPlanner()
```
