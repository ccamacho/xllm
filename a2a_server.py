"""
A2A Server - Expose ADK agents via A2A Protocol (HTTP)

This server exposes agents as A2A-compatible HTTP services.
Each agent should run on its own port for true distributed A2A.

Architecture:
    python a2a_server.py --agent router --port 8000      # Router (supervisor)
    python a2a_server.py --agent weather --port 8001     # Weather agent
    python a2a_server.py --agent calculator --port 8002  # Calculator agent

The router agent uses RemoteA2aAgent to communicate with weather/calculator
agents running on their respective ports.
"""

import os
import argparse
from dotenv import load_dotenv

load_dotenv()

# Parse arguments early to get agent name for service name
# We need to do this before instrumentation to set the correct service name
def parse_args_early():
    """Parse only the --agent argument early for service name configuration."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--agent", "-a", choices=["router", "weather", "calculator", "advanced_calculator"], default="router")
    parser.add_argument("--port", "-p", type=int, default=8000)
    args, _ = parser.parse_known_args()
    return args

# Get agent name early for service name
_early_args = parse_args_early()
_service_name = f"a2a-{_early_args.agent}"

# Set service name in environment (OpenTelemetry will pick this up)
os.environ["OTEL_SERVICE_NAME"] = _service_name

# Note: All agents use the same Langfuse project (same API keys)
# Traces are separated by service.name and agent.name attributes for filtering
# You can filter in Langfuse UI by: service.name = "a2a-router" | "a2a-weather" | "a2a-calculator"

# Configure tracing - must be done before importing agents
# Follow SPEOL pattern: GoogleADKInstrumentor + langfuse.get_client()
# GoogleADKInstrumentor automatically captures all ADK agent activity via OpenTelemetry
# langfuse.get_client() configures the OTLP exporter to send traces to Langfuse
from openinference.instrumentation.google_adk import GoogleADKInstrumentor
from langfuse import get_client
from opentelemetry.sdk.resources import Resource

# Configure OpenTelemetry Resource with service name and agent metadata
# These attributes allow filtering traces in Langfuse UI by agent
resource = Resource.create({
    "service.name": _service_name,  # Filter by: a2a-router, a2a-weather, a2a-calculator
    "service.type": "a2a-agent",
    "agent.name": _early_args.agent,  # Filter by: router, weather, calculator
    "agent.port": str(_early_args.port),
})

# Instrument ADK first (creates OpenTelemetry spans)
GoogleADKInstrumentor().instrument(resource=resource)

# Get Langfuse client (configures OTLP exporter automatically when env vars are set)
langfuse = get_client()

# Verify connection - handle connection errors gracefully
try:
    if langfuse and langfuse.auth_check():
        print("[OK] Langfuse tracing enabled")
        print(f"     Dashboard: {os.getenv('LANGFUSE_BASE_URL', 'https://cloud.langfuse.com')}")
        print(f"     Service: {_service_name} (filter by this in Langfuse UI)")
        print(f"     Agent: {_early_args.agent} (also filterable)")
        print(f"     All agents share the same project - filter by service.name or agent.name")
    else:
        print("[WARN] Langfuse authentication failed. Running without tracing.")
        langfuse = None
except Exception as e:
    print(f"[WARN] Langfuse connection failed: {e}")
    print("       Continuing without Langfuse monitoring...")
    langfuse = None


def get_agent(agent_name: str):
    """
    Load the specified agent by name.
    
    Args:
        agent_name: One of 'router', 'weather', 'calculator', 'advanced_calculator'
        
    Returns:
        The ADK Agent instance
    """
    if agent_name == "router":
        from agents.router_agent import router_agent
        return router_agent
    elif agent_name == "weather":
        from agents.weather_agent import weather_agent
        return weather_agent
    elif agent_name == "calculator":
        from agents.calculator_agent import calculator_agent
        return calculator_agent
    elif agent_name == "advanced_calculator":
        from agents.advanced_calculator_agent import advanced_calculator_agent
        return advanced_calculator_agent
    else:
        raise ValueError(f"Unknown agent: {agent_name}. Choose from: router, weather, calculator, advanced_calculator")


def create_a2a_app(agent_name: str, port: int):
    """
    Create an A2A-compatible Starlette application for the specified agent.
    
    Args:
        agent_name: Name of the agent to expose
        port: Port number for agent card URL
        
    Returns:
        Starlette application
    """
    from google.adk.a2a.utils.agent_to_a2a import to_a2a
    
    agent = get_agent(agent_name)
    
    print(f"\n[INFO] Creating A2A server for: {agent.name}")
    print(f"       Description: {agent.description[:80]}...")
    
    # Wrap the ADK agent with A2A protocol support
    # GoogleADKInstrumentor automatically captures all traces via OpenTelemetry
    a2a_app = to_a2a(agent, port=port)
    
    return a2a_app


def run_server(app, host: str, port: int, agent_name: str):
    """Run the A2A server with uvicorn."""
    import uvicorn
    
    print(f"\n{'='*60}")
    print(f"A2A Server Ready: {agent_name}")
    print(f"{'='*60}")
    print(f"\n[INFO] Server: http://{host}:{port}")
    print(f"[INFO] Agent Card: http://localhost:{port}/.well-known/agent-card.json")
    print(f"\n[TIP] Test with curl:")
    print(f"      curl http://localhost:{port}/.well-known/agent-card.json")
    
    if agent_name == "router":
        print(f"\n[IMPORTANT] Router requires sub-agents to be running:")
        print(f"            python a2a_server.py --agent weather --port 8001")
        print(f"            python a2a_server.py --agent calculator --port 8002")
    
    print(f"\n{'='*60}\n")
    
    uvicorn.run(app, host=host, port=port)


def main():
    parser = argparse.ArgumentParser(
        description="A2A Server for Multi-Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start all agents (run each in a separate terminal):
  
  # Terminal 1: Weather agent on port 8001
  python a2a_server.py --agent weather --port 8001
  
      # Terminal 2: Calculator agent on port 8002
      python a2a_server.py --agent calculator --port 8002
      
      # Terminal 3: Advanced Calculator agent on port 8003
      python a2a_server.py --agent advanced_calculator --port 8003
      
      # Terminal 4: Router agent on port 8000 (requires agents above)
      python a2a_server.py --agent router --port 8000
  
  # Terminal 4: Test the system
  python test_agents_a2a.py --url http://localhost:8000
        """
    )
    
    parser.add_argument(
        "--agent", "-a",
        choices=["router", "weather", "calculator", "advanced_calculator"],
        default="router",
        help="Agent to expose (default: router)"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port to run on (default: 8000)"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    
    args = parser.parse_args()
    
    # Service name was already set during early parsing
    # Create and run the A2A app
    app = create_a2a_app(args.agent, args.port)
    run_server(app, args.host, args.port, args.agent)


if __name__ == "__main__":
    main()
