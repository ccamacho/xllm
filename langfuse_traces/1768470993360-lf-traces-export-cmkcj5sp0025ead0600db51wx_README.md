# Langfuse Traces

This document explains how to read the trace flows in this multi-agent A2A system.

## Trace Flow Examples

Each query generates multiple traces as it flows through agents. Below are the actual trace chains from the export.

---

### Example 1: Greeting (No Delegation)

**Query:** `"Hello! What can you do?"`

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

---

### Example 2: Weather Query (Router → Weather Agent)

**Query:** `"What's the weather in Tokyo?"`

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

---

### Example 3: Basic Math (Router → Calculator)

**Query:** `"Calculate 25 * 4 + 10"`

```
Step 1: Router receives query
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trace ID: c0688acaac9af598f5de008661532cd4                                  │
│ Agent:    router_agent (port 8000)                                          │
│ Latency:  2699ms                                                            │
│                                                                             │
│ Input:    "Calculate 25 * 4 + 10"                                           │
│ Action:   Detects "Calculate" keyword → delegates to calculator_agent       │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
Step 2: Calculator Agent processes query
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trace ID: f1bb0d2af870877d0d3ed36328ba63e7                                  │
│ Agent:    calculator_agent (port 8002)                                      │
│ Latency:  1949ms                                                            │
│                                                                             │
│ Input:    "Calculate 25 * 4 + 10"                                           │
│ Action:   Calls basic_calculate("25 * 4 + 10") tool                         │
│ Output:   "25 * 4 + 10 = 110"                                               │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
                        Response returns to user
```

---

### Example 4: Unit Conversion (Router → Calculator)

**Query:** `"Convert 100 kilometers to miles"`

```
Step 1: Router receives query
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trace ID: bed532d329ef8fbd53afc37e90d921f3                                  │
│ Agent:    router_agent (port 8000)                                          │
│ Latency:  2425ms                                                            │
│                                                                             │
│ Input:    "Convert 100 kilometers to miles"                                 │
│ Action:   Detects "Convert" keyword → delegates to calculator_agent         │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
Step 2: Calculator Agent processes query
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trace ID: 9695525d62b2b857c3a787877b69544c                                  │
│ Agent:    calculator_agent (port 8002)                                      │
│ Latency:  1371ms                                                            │
│                                                                             │
│ Input:    "Convert 100 kilometers to miles"                                 │
│ Action:   Calls convert_units(100, "km", "miles") tool                      │
│ Output:   "100 kilometers is equal to 62.1371 miles."                       │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
                        Response returns to user
```

---

### Example 5: Advanced Math (Router → Calculator → Advanced Calculator)

**Query:** `"What is the square root of 144?"`

```
Step 1: Router receives query
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trace ID: 8a148eaad992e3b9192712726feb2b0a                                  │
│ Agent:    router_agent (port 8000)                                          │
│ Latency:  2884ms                                                            │
│                                                                             │
│ Input:    "What is the square root of 144?"                                 │
│ Action:   Detects math query → delegates to calculator_agent                │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
Step 2: Calculator detects advanced operation
┌─────────────────────────────────────────────────────────────────────────────┐
│ Agent:    calculator_agent (port 8002)                                      │
│                                                                             │
│ Input:    "What is the square root of 144?"                                 │
│ Action:   Detects "sqrt" in advanced_keywords list                          │
│           → delegates to advanced_calculator_agent                          │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
Step 3: Advanced Calculator executes
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trace ID: a6122abb25289a3a13c2b8a08711b3f2                                  │
│ Agent:    advanced_calculator_agent (port 8003)                             │
│ Latency:  2091ms                                                            │
│                                                                             │
│ Input:    "What is the square root of 144?"                                 │
│ Action:   Calls advanced_calculate("sqrt(144)") tool                        │
│ Output:   "Calculating advanced expression: sqrt(144)                       │
│            Result: 12                                                       │
│            This is the square root of 144, which equals 12."                │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
                        Response returns to user
```

---

### Example 6: Trigonometry (Router → Calculator → Advanced Calculator)

**Query:** `"Calculate sin(pi/2)"`

```
Step 1: Router receives query
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trace ID: 2abbffdc982ee83d2079577b2e45910a                                  │
│ Agent:    router_agent (port 8000)                                          │
│ Latency:  3788ms                                                            │
│                                                                             │
│ Input:    "Calculate sin(pi/2)"                                             │
│ Action:   Detects "Calculate" → delegates to calculator_agent               │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
Step 2: Calculator detects trigonometry
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trace ID: 3ffdf40852a6ebd5a6dae05387925fae                                  │
│ Agent:    calculator_agent (port 8002)                                      │
│ Latency:  3047ms                                                            │
│                                                                             │
│ Input:    "Calculate sin(pi/2)"                                             │
│ Action:   Detects "sin" and "pi" in advanced_keywords list                  │
│           → delegates to advanced_calculator_agent                          │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
Step 3: Advanced Calculator executes
┌─────────────────────────────────────────────────────────────────────────────┐
│ Agent:    advanced_calculator_agent (port 8003)                             │
│                                                                             │
│ Input:    "Calculate sin(pi/2)"                                             │
│ Action:   Calls advanced_calculate("sin(pi/2)") tool                        │
│ Output:   "Calculating advanced expression: sin(pi/2)                       │
│            Result: 1                                                        │
│            Here, the angle is in radians. sin(pi/2) equals 1."              │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
                        Response returns to user
```

---

### Example 7: Custom Operation `chimichanga` (Router → Calculator → Advanced Calculator)

**Query:** `"Calculate chimichanga(7)"`

The `chimichanga` function is a custom operation that multiplies a number by 3.75.

```
Step 1: Router receives query
┌─────────────────────────────────────────────────────────────────────────────┐
│ Agent:    router_agent (port 8000)                                          │
│                                                                             │
│ Input:    "Calculate chimichanga(7)"                                        │
│ Action:   Detects "chimichanga" keyword in routing rules                    │
│           → delegates to calculator_agent                                   │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
Step 2: Calculator detects custom operation
┌─────────────────────────────────────────────────────────────────────────────┐
│ Agent:    calculator_agent (port 8002)                                      │
│                                                                             │
│ Input:    "Calculate chimichanga(7)"                                        │
│ Action:   Checks advanced_keywords list:                                    │
│           ['sqrt', 'sin', 'cos', 'tan', 'log', 'exp',                       │
│            'factorial', 'pi', 'e', 'chimichanga']                           │
│           Finds "chimichanga" → delegates to advanced_calculator_agent      │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
Step 3: Advanced Calculator executes custom function
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trace ID: 1597cf4f345a5e01127a2f8c18b9a4ab                                  │
│ Agent:    advanced_calculator_agent (port 8003)                             │
│ Latency:  1020ms                                                            │
│                                                                             │
│ Input:    "Calculate chimichanga(7)"                                        │
│ Action:   Evaluates using: "chimichanga": lambda x: x * 3.75                │
│ Calculation: 7 × 3.75 = 26.25                                               │
│                                                                             │
│ Output:   "Calculating advanced expression: chimichanga(7)                  │
│            Result: 26.25                                                    │
│            The chimichanga operation multiplies the number by 3.75,         │
│            so 7 × 3.75 = 26.25."                                            │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
                        Response returns to user
```

---

## Summary: Delegation Patterns

| Query Type | Trace Chain | Example |
|------------|-------------|---------|
| Greeting | Router only | "Hello!" |
| Weather | Router → Weather | "Weather in Tokyo?" |
| Basic Math | Router → Calculator | "25 * 4 + 10" |
| Conversion | Router → Calculator | "100 km to miles" |
| Advanced Math | Router → Calculator → Advanced | "sqrt(144)" |
| Trigonometry | Router → Calculator → Advanced | "sin(pi/2)" |
| Custom Function | Router → Calculator → Advanced | "chimichanga(7)" |

---

## How to Find Related Traces

Traces for the same query share similar timestamps. Look for:

1. **Router trace** - Highest latency (includes all delegation time)
2. **Subagent trace** - Lower latency (actual processing time)
3. **Timestamp order** - Subagent trace starts slightly before router completes

**Example for "What's the weather in Tokyo?":**
```
68423b551dd9039a58648b8711bb25bc  router_agent   1827ms  08:55:48.160
1fe33d35833c563f063bcd5f365aed5e  weather_agent   991ms  08:55:48.991
```

The weather_agent trace ends ~800ms before router, showing the delegation overhead.
