# Example 2: Weather Query (Router → Weather Agent)

**Query:** `"What's the weather in Tokyo?"`

## Trace Flow

```
Step 1: Router receives query
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trace ID: 68423b551dd9039a58648b8711bb25bc                                  │
│ Agent:    router_agent (port 8000)                                          │
│ Latency:  1827ms (includes delegation time)                                 │
│                                                                             │
│ Input:    "What's the weather in Tokyo?"                                    │
│ Action:   Detects "weather" keyword → delegates to weather_agent            │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
Step 2: Weather Agent processes query
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trace ID: 1fe33d35833c563f063bcd5f365aed5e                                  │
│ Agent:    weather_agent (port 8001)                                         │
│ Latency:  991ms                                                             │
│                                                                             │
│ Input:    "What's the weather in Tokyo?"                                    │
│ Action:   Calls get_weather("Tokyo") tool                                   │
│ Output:   "Temperature: 27°C, partly cloudy, humidity 78%, wind 3 m/s"      │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
                        Response returns to user
```

## Explanation

This query demonstrates a **single delegation**:
1. Router receives the query
2. Router detects "weather" keyword in the query
3. Router delegates to `weather_agent` via A2A protocol
4. Weather agent calls `get_weather("Tokyo")` tool
5. Weather agent returns the weather data
6. Router forwards the response to the user

## Traces in This Folder

| Trace ID | Agent | Latency | Action |
|----------|-------|---------|--------|
| `68423b551dd9039a58648b8711bb25bc` | router_agent | 1827ms | Delegates to weather_agent |
| `1fe33d35833c563f063bcd5f365aed5e` | weather_agent | 991ms | Calls get_weather() tool |

## Latency Analysis

- **Router total:** 1827ms (includes waiting for weather_agent)
- **Weather agent:** 991ms (actual API call time)
- **Delegation overhead:** ~836ms (router processing + A2A communication)
