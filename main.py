"""
Multi-Agent System with Google ADK and Langfuse Tracing

This is the main entry point for the multi-agent system that demonstrates:
1. A Router Agent that coordinates between specialist agents
2. A Weather Agent for weather-related queries
3. A Calculator Agent for mathematical calculations
4. Langfuse integration for tracing and observability

Usage:
    python main.py                    # Interactive mode
    python main.py --query "..."      # Single query mode
    python main.py --demo             # Run demo queries
"""

import os
import sys
import asyncio
import argparse
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


async def run_agent(query: str, verbose: bool = False) -> str:
    """
    Run the router agent with a user query.
    
    Args:
        query: The user's question or request
        verbose: Whether to print detailed output
    
    Returns:
        The agent's response as a string
    """
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from agents.agent import root_agent
    
    # Create a session service to manage conversation state
    session_service = InMemorySessionService()
    
    # Create a runner with the router agent
    runner = Runner(
        agent=root_agent,
        app_name="multi-agent-demo",
        session_service=session_service,
    )
    
    # Create or get a session
    session = await session_service.create_session(
        app_name="multi-agent-demo",
        user_id="demo-user",
    )
    
    if verbose:
        print(f"\n[INFO] Processing: {query}")
        print("-" * 50)
    
    # Run the agent and collect the response
    response_parts = []
    
    async for event in runner.run_async(
        user_id="demo-user",
        session_id=session.id,
        new_message=query,
    ):
        # Process events from the agent
        if hasattr(event, 'content') and event.content:
            if hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_parts.append(part.text)
        
        if verbose and hasattr(event, 'author'):
            print(f"  [{event.author}] Event received")
    
    response = "".join(response_parts)
    
    if verbose:
        print("-" * 50)
        print(f"[RESPONSE] {response}")
    
    return response


async def run_interactive():
    """
    Run the agent in interactive mode with a chat loop.
    """
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from agents.agent import root_agent
    
    print("\n" + "=" * 60)
    print("  Multi-Agent System with Google ADK")
    print("=" * 60)
    print("\nAvailable agents:")
    print("  - WeatherAgent: Ask about weather in any location")
    print("  - CalculatorAgent: Perform math calculations")
    print("\nType 'quit' or 'exit' to end the session")
    print("Type 'help' for usage examples")
    print("-" * 60 + "\n")
    
    # Create session service and runner
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="multi-agent-interactive",
        session_service=session_service,
    )
    
    # Create a session
    session = await session_service.create_session(
        app_name="multi-agent-interactive",
        user_id="interactive-user",
    )
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!\n")
                break
            
            if user_input.lower() == 'help':
                print_help()
                continue
            
            # Run the agent
            print("\nAgent: ", end="", flush=True)
            
            response_text = ""
            async for event in runner.run_async(
                user_id="interactive-user",
                session_id=session.id,
                new_message=user_input,
            ):
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts'):
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text += part.text
            
            print(response_text)
            print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!\n")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}\n")


def print_help():
    """Print usage examples."""
    print("""
Usage Examples:
-------------------------------------------------------------
Weather queries:
  - "What's the weather in London?"
  - "Tell me the temperature in Tokyo"
  - "Is it raining in Paris?"

Math calculations:
  - "Calculate 15% of 200"
  - "What is sqrt(144) + 5^2?"
  - "Convert 100 kilometers to miles"
  - "What is sin(pi/2)?"

General:
  - "Hello!" - Greeting
  - "What can you do?" - Learn about capabilities
-------------------------------------------------------------
""")


async def run_demo():
    """
    Run demo queries to showcase the multi-agent system.
    """
    demo_queries = [
        "Hello! What can you help me with?",
        "What's the weather like in Tokyo?",
        "Calculate 25% of 180",
        "What is the square root of 144 plus 5 squared?",
        "Convert 100 kilometers to miles",
        "What's the weather in London and is 15°C considered warm?",
    ]
    
    print("\n" + "=" * 60)
    print("  Multi-Agent Demo")
    print("=" * 60 + "\n")
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n[{i}/{len(demo_queries)}] Query: {query}")
        print("-" * 50)
        
        try:
            response = await run_agent(query, verbose=False)
            print(f"Response: {response}")
        except Exception as e:
            print(f"[ERROR] {e}")
        
        print()
        
        # Small delay between queries
        await asyncio.sleep(0.5)
    
    print("=" * 60)
    print("  Demo completed!")
    print("=" * 60 + "\n")


def check_environment():
    """
    Check if required environment variables are set.
    """
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key:
        print("\n[ERROR] GOOGLE_API_KEY environment variable is not set")
        print("\nTo fix this:")
        print("  1. Get an API key from https://aistudio.google.com/app/apikey")
        print("  2. Set it: export GOOGLE_API_KEY='your-key-here'")
        print("  3. Or add it to a .env file")
        return False
    
    if google_api_key == "your_google_api_key_here":
        print("\n[ERROR] GOOGLE_API_KEY is set to placeholder value")
        print("        Please set your actual API key")
        return False
    
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent System with Google ADK and Langfuse",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Interactive mode
  python main.py --query "What's 2+2?"     # Single query
  python main.py --demo                    # Run demo queries
  python main.py --no-tracing              # Disable Langfuse tracing
        """,
    )
    
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Run a single query and exit",
    )
    parser.add_argument(
        "--demo", "-d",
        action="store_true",
        help="Run demo queries to showcase the system",
    )
    parser.add_argument(
        "--no-tracing",
        action="store_true",
        help="Disable Langfuse tracing",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )
    
    args = parser.parse_args()
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Set up tracing
    if not args.no_tracing:
        from tracing import setup_langfuse_tracing, log_trace_url
        tracing_enabled = setup_langfuse_tracing(debug=args.verbose)
        if tracing_enabled:
            log_trace_url()
    else:
        from tracing import setup_basic_tracing
        setup_basic_tracing()
    
    # Run the appropriate mode
    if args.query:
        # Single query mode
        response = asyncio.run(run_agent(args.query, verbose=args.verbose))
        if not args.verbose:
            print(response)
    elif args.demo:
        # Demo mode
        asyncio.run(run_demo())
    else:
        # Interactive mode
        asyncio.run(run_interactive())


if __name__ == "__main__":
    main()
