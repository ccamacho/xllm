"""
Multi-Agent System - Main Agent Definition

This module defines the root_agent that the ADK CLI will use.
It creates a routing agent that coordinates between Weather and Calculator agents.
"""

from google.adk.agents import Agent
from agents.weather_agent import weather_agent, get_weather
from agents.calculator_agent import calculator_agent, calculate, convert_units, calculate_percentage


# Create the root agent - this is what ADK CLI will look for
root_agent = Agent(
    name="router_agent",
    model="gemini-2.0-flash",
    description="A multi-agent coordinator that routes requests to specialized agents for weather information and mathematical calculations.",
    instruction="""You are a helpful assistant coordinator. Your role is to:

1. Understand user requests and route them to the appropriate specialist agent
2. For weather-related queries → Use the weather tools or transfer to weather_agent
3. For math/calculation queries → Use the calculator tools or transfer to calculator_agent
4. For general questions → Answer directly

**Routing Guidelines:**

WEATHER QUERIES (use weather tools):
- Current weather conditions
- Temperature in a location  
- Climate or atmospheric conditions
- Questions like "What's the weather in...", "Is it raining in...", "Temperature in..."

MATH QUERIES (use calculator tools):
- Mathematical calculations (arithmetic, algebra)
- Unit conversions (km to miles, celsius to fahrenheit, etc.)
- Percentage calculations
- Trigonometric or logarithmic functions
- Questions like "Calculate...", "What is 2+2", "Convert 10 km to miles"

GENERAL (answer directly):
- Greetings
- Questions about your capabilities
- General questions

Be conversational and helpful!
""",
    # Include tools directly for simpler routing
    tools=[
        get_weather,
        calculate,
        convert_units,
        calculate_percentage,
    ],
    # Sub-agents for LLM-driven delegation if needed
    sub_agents=[
        weather_agent,
        calculator_agent,
    ],
)
