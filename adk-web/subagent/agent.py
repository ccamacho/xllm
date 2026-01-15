"""
ADK Web interface for Multi-Agent Testing.
This module imports the router agent and creates a runner for use with adk-web.
"""

from agents.router_agent import router_agent_tool

# Create the root_agent runner for adk-web
# This runner uses the router_agent from router_agent.py and the shared session service
root_agent = router_agent_tool
