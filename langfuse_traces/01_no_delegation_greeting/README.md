# Example 1: Greeting (No Delegation)

**Query:** `"Hello! What can you do?"`

## Trace Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trace ID: 77eb2b7914c97a4ca1512ca98f4ae95a                                  │
│ Agent:    router_agent (port 8000)                                          │
│ Latency:  971ms                                                             │
│                                                                             │
│ Input:    "Hello! What can you do?"                                         │
│ Output:   "I can route your requests to specialized agents..."              │
│                                                                             │
│ Flow:     User → Router → User (no delegation needed)                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Explanation

This is a simple greeting query. The router agent:
1. Receives the query
2. Recognizes it as a capability question (not weather or math)
3. Responds directly without delegating to any subagent

## Traces in This Folder

| Trace ID | Agent | Latency | Action |
|----------|-------|---------|--------|
| `77eb2b7914c97a4ca1512ca98f4ae95a` | router_agent | 971ms | Direct response |
