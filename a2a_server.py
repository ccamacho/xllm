"""
A2A Server - Expose Multi-Agent System via A2A Protocol

This module exposes our ADK agents as A2A-compliant HTTP servers,
enabling external agents (from any framework) to discover and 
communicate with our Weather and Calculator agents.

A2A Protocol Features:
- Agent Cards: Discoverable at /.well-known/agent-card.json
- JSON-RPC 2.0: Standard communication protocol
- Task Management: Create, progress, and complete tasks
- Streaming: Real-time response streaming support
- Langfuse Tracing: Full observability via OpenTelemetry

Usage:
    # Start the router agent (includes all capabilities)
    python a2a_server.py

    # Or start individual specialized agents
    python a2a_server.py --agent weather --port 8001
    python a2a_server.py --agent calculator --port 8002
    python a2a_server.py --agent router --port 8000

    # Test agent discovery
    curl http://localhost:8000/.well-known/agent-card.json

External Communication:
    Other A2A-compatible agents can now discover and call your agents:
    - From LangChain agents
    - From AutoGen agents
    - From CrewAI agents
    - From any A2A-compliant framework
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def setup_langfuse_tracing():
    """
    Setup Langfuse tracing via OpenTelemetry for A2A requests.
    This enables trace capture for all agent invocations.
    """
    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    if not langfuse_public_key or not langfuse_secret_key:
        print("[WARN] Langfuse credentials not found - tracing disabled")
        print("       Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env")
        return False
    
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        
        # Try to use Langfuse's OTEL exporter if available
        try:
            from langfuse.opentelemetry import LangfuseSpanProcessor
            
            # Configure OpenTelemetry with Langfuse
            resource = Resource.create({
                "service.name": "a2a-multi-agent",
                "langfuse.environment": os.getenv("LANGFUSE_ENVIRONMENT", "development"),
            })
            
            provider = TracerProvider(resource=resource)
            provider.add_span_processor(LangfuseSpanProcessor())
            trace.set_tracer_provider(provider)
            
            print("[OK] Langfuse tracing enabled via OpenTelemetry")
            return True
            
        except ImportError:
            # Fallback to direct Langfuse SDK
            from langfuse import Langfuse
            
            # Initialize Langfuse client for manual instrumentation
            global langfuse_client
            langfuse_client = Langfuse(
                public_key=langfuse_public_key,
                secret_key=langfuse_secret_key,
                host=langfuse_host,
            )
            print("[OK] Langfuse tracing enabled (SDK mode)")
            return True
            
    except ImportError as e:
        print(f"[WARN] Langfuse/OpenTelemetry not available: {e}")
        return False


# Global Langfuse client (set if SDK mode is used)
langfuse_client = None


def create_router_a2a_server(port: int = 8000):
    """
    Create A2A server for the main router agent.
    This agent handles all requests and can use weather/calculator tools.
    """
    from google.adk.a2a.utils.agent_to_a2a import to_a2a
    from agents.agent import root_agent
    
    print(f"[INFO] Starting Router Agent A2A Server on port {port}")
    print(f"   Agent Card: http://localhost:{port}/.well-known/agent-card.json")
    print(f"   Skills: Weather queries, Math calculations, General chat")
    
    return to_a2a(root_agent, port=port)


def create_weather_a2a_server(port: int = 8001):
    """
    Create A2A server for the specialized Weather agent.
    Exposes only weather-related capabilities.
    """
    from google.adk.a2a.utils.agent_to_a2a import to_a2a
    from agents.weather_agent import weather_agent
    
    print(f"Starting Weather Agent A2A Server on port {port}")
    print(f"   Agent Card: http://localhost:{port}/.well-known/agent-card.json")
    print(f"   Skills: Current weather, Temperature, Forecasts")
    
    return to_a2a(weather_agent, port=port)


def create_calculator_a2a_server(port: int = 8002):
    """
    Create A2A server for the specialized Calculator agent.
    Exposes only math-related capabilities.
    """
    from google.adk.a2a.utils.agent_to_a2a import to_a2a
    from agents.calculator_agent import calculator_agent
    
    print(f"[INFO] Starting Calculator Agent A2A Server on port {port}")
    print(f"   Agent Card: http://localhost:{port}/.well-known/agent-card.json")
    print(f"   Skills: Arithmetic, Unit conversions, Percentages")
    
    return to_a2a(calculator_agent, port=port)


def run_server(app, host: str = "0.0.0.0", port: int = 8000):
    """Run the A2A server using uvicorn."""
    import uvicorn
    
    print(f"\n{'='*60}")
    print("A2A Server Ready!")
    print(f"{'='*60}")
    print(f"\n[INFO] Server: http://{host}:{port}")
    print(f"[INFO] Agent Card: http://localhost:{port}/.well-known/agent-card.json")
    print(f"\n[TIP] Test with curl:")
    print(f"      curl http://localhost:{port}/.well-known/agent-card.json")
    print(f"\n[INFO] A2A Protocol: https://a2a-protocol.org/")
    print(f"{'='*60}\n")
    
    # to_a2a returns a Starlette app directly (or A2AStarletteApplication)
    # Handle both cases
    if hasattr(app, 'build'):
        uvicorn.run(app.build(), host=host, port=port)
    else:
        uvicorn.run(app, host=host, port=port)


def main():
    parser = argparse.ArgumentParser(
        description="A2A Server for Multi-Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start the main router agent (recommended)
  python a2a_server.py --agent router --port 8000

  # Start all agents on different ports
  python a2a_server.py --agent router --port 8000 &
  python a2a_server.py --agent weather --port 8001 &
  python a2a_server.py --agent calculator --port 8002 &

  # Test agent discovery
  curl http://localhost:8000/.well-known/agent-card.json

  # Test with A2A client
  python test_a2a_client.py
        """
    )
    
    parser.add_argument(
        "--agent",
        choices=["router", "weather", "calculator"],
        default="router",
        help="Which agent to expose via A2A (default: router)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the A2A server on (default: 8000)"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    
    args = parser.parse_args()
    
    # Verify API key is set
    if not os.getenv("GOOGLE_API_KEY"):
        print("[ERROR] GOOGLE_API_KEY not set in .env file")
        print("        Please add your Gemini API key to the .env file")
        sys.exit(1)
    
    # Setup Langfuse tracing
    tracing_enabled = setup_langfuse_tracing()
    
    # Create and run the appropriate server
    if args.agent == "router":
        app = create_router_a2a_server(port=args.port)
    elif args.agent == "weather":
        app = create_weather_a2a_server(port=args.port)
    elif args.agent == "calculator":
        app = create_calculator_a2a_server(port=args.port)
    else:
        print(f"[ERROR] Unknown agent: {args.agent}")
        sys.exit(1)
    
    run_server(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
