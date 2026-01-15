"""
Router Agent - Supervisor agent using RemoteA2aAgent for true A2A communication.

This agent routes requests to specialized remote agents running as independent
A2A servers. It does NOT expose tools directly - only sub_agents.

Architecture:
    Router (port 8000) → Weather Agent (port 8001)
                       → Calculator Agent (port 8002)
"""

import os
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()

# Configuration for remote agent URLs
WEATHER_AGENT_URL = os.getenv("WEATHER_AGENT_URL", "http://localhost:8001")
CALCULATOR_AGENT_URL = os.getenv("CALCULATOR_AGENT_URL", "http://localhost:8002")


# Remote A2A Agents - these connect to agents running on separate processes
weather_remote = RemoteA2aAgent(
    name="weather_agent",
    description="Specialist agent that provides current weather information and forecasts for any location worldwide. Use this agent when users ask about weather, temperature, climate conditions, or forecasts.",
    agent_card=f"{WEATHER_AGENT_URL}{AGENT_CARD_WELL_KNOWN_PATH}",
)

calculator_remote = RemoteA2aAgent(
    name="calculator_agent",
    description="Specialist agent that performs mathematical calculations including basic arithmetic, trigonometry, logarithms, unit conversions, and percentage calculations. Use this agent when users need to compute mathematical expressions or convert between units.",
    agent_card=f"{CALCULATOR_AGENT_URL}{AGENT_CARD_WELL_KNOWN_PATH}",
)


# Router instruction - focused on delegation, not tool usage
router_instruction = """
You are a supervisor agent responsible for intelligently routing queries to the most appropriate specialized sub-agent. If a sub-agent is invoked, always ensure that the sub-agent's complete response is returned to the user. If it is not clear which agent you should use, ask the user for more information.

AVAILABLE SUB-AGENTS:

1. weather_agent - Specializes in weather information and forecasts
   Keywords: weather, temperature, forecast, rain, sunny, climate, humidity, wind
   Query patterns:
   - "What's the weather in Tokyo?"
   - "Is it raining in London?"
   - "Temperature in New York"
   - "Will it be sunny tomorrow?"

2. calculator_agent - Specializes in mathematical calculations and unit conversions
   Keywords: calculate, compute, math, convert, percentage, sqrt, sum, add, multiply, chimichanga
   Query patterns:
   - "Calculate 25 * 4 + 10"
   - "What is sqrt(144)?"
   - "Convert 100 km to miles"
   - "What is 15% of 200?"
   - "Calculate chimichanga(7)"

ROUTING RULES (in priority order):
1. Weather queries (location, temperature, forecast) → delegate to weather_agent
2. Math/calculation queries (arithmetic, conversions) → delegate to calculator_agent
3. When uncertain → ask the user for clarification, do not guess

INSTRUCTIONS:
- Analyze the user's intent carefully before delegating
- Pass ALL relevant context from the conversation to the sub-agent
- IMPORTANT: Return the sub-agent's response directly and completely to the user
- Do not truncate or summarize the sub-agent's response
- For greetings or capability questions, respond directly without delegation
"""


# Router agent - NO tools, only remote sub_agents
router_agent = Agent(
    name="router_agent",
    model="gemini-2.0-flash",
    description="A supervisor agent that routes requests to specialized remote agents for weather information and mathematical calculations.",
    instruction=router_instruction,
    # NO tools - only remote sub_agents
    sub_agents=[weather_remote, calculator_remote],
)


# Session service for the runner
session_service = InMemorySessionService()

# Runner for the router agent
runner = Runner(
    agent=router_agent,
    app_name="multi_agent_router",
    session_service=session_service,
)
