"""
Multi-Agent System using Google ADK with A2A Protocol.

This package contains:

Standalone Agents (run as independent A2A servers):
- weather_agent: Gets weather information for locations
- calculator_agent: Performs mathematical calculations

Router Agent (uses RemoteA2aAgent for A2A communication):
- router_agent: Routes requests to remote weather/calculator agents

Architecture:
    Router (port 8000) ──A2A──> Weather Agent (port 8001)
                       ──A2A──> Calculator Agent (port 8002)
"""

# Standalone agents (with tools)
from .weather_agent import weather_agent, get_weather
from .calculator_agent import calculator_agent, calculate, convert_units, calculate_percentage

# Router agent (with RemoteA2aAgent sub-agents, no tools)
from .router_agent import router_agent

__all__ = [
    # Standalone agents
    "weather_agent",
    "calculator_agent",
    # Router agent (A2A mode)
    "router_agent",
    # Tools (for direct use if needed)
    "get_weather",
    "calculate",
    "convert_units",
    "calculate_percentage",
]
