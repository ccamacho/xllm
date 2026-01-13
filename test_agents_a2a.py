"""
Test Agents via A2A Protocol (HTTP)

Run agents via A2A protocol over HTTP (separate processes).
All traces are sent to Langfuse for comparison with ADK method.

Usage:
    # First, start the A2A server:
    python a2a_server.py --port 8000

    # Then run this client:
    python test_agents_a2a.py              # Run demo queries
    python test_agents_a2a.py --interactive # Interactive mode
    python test_agents_a2a.py --card-only   # Just fetch agent card
"""

import asyncio
import argparse
import json
import time
import httpx

# Import shared tracing utilities
import langfuse_tracing as lf


async def get_agent_card(base_url: str) -> dict:
    """
    Fetch the Agent Card from an A2A server.
    Agent Cards describe the agent's capabilities and are used for discovery.
    """
    url = f"{base_url}/.well-known/agent-card.json"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


async def send_message(base_url: str, message: str, session_id: str = None, trace: bool = True) -> dict:
    """
    Send a message to an A2A agent using JSON-RPC 2.0.
    
    The A2A protocol uses JSON-RPC for all communication:
    - message/send: Send a new message
    - message/stream: Send with streaming response
    - tasks/get: Get task status
    - tasks/cancel: Cancel a running task
    """
    import uuid
    url = base_url.rstrip('/')  # Root endpoint for JSON-RPC
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "message/send",
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"type": "text", "text": message}]
            }
        }
    }
    
    if session_id:
        payload["params"]["contextId"] = session_id
    
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
    
    elapsed = time.time() - start_time
    
    # Extract response text for tracing
    response_text = ""
    if "result" in result and "artifacts" in result["result"]:
        for artifact in result["result"].get("artifacts", []):
            for part in artifact.get("parts", []):
                if "text" in part:
                    response_text += part["text"]
    
    # Create Langfuse trace if enabled
    if trace and lf.get_client() and lf.is_enabled():
        try:
            with lf.get_client().start_as_current_span(
                name="a2a-client-call",
                input={"query": message, "method": "a2a", "url": base_url},
                metadata={"protocol": "a2a", "query_type": lf.classify_query(message)},
            ) as span:
                span.update(
                    output={"response": response_text},
                    metadata={
                        "latency_ms": int(elapsed * 1000),
                        "method": "a2a",
                        "tags": ["a2a", "client", lf.classify_query(message)],
                    },
                )
        except Exception:
            pass  # Don't fail on tracing errors
    
    return result


async def stream_message(base_url: str, message: str, session_id: str = None):
    """
    Send a message and receive streaming response.
    Uses Server-Sent Events (SSE) for real-time updates.
    """
    url = f"{base_url}/a2a"
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tasks/sendSubscribe",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": message}]
            }
        }
    }
    
    if session_id:
        payload["params"]["sessionId"] = session_id
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    yield data


async def run_demo(base_url: str):
    """Run a demo of the A2A client."""
    
    print("=" * 60)
    print("A2A Client Demo")
    print("=" * 60)
    print(f"\n[INFO] Connecting to: {base_url}")
    
    # Step 1: Discover the agent
    print("\n" + "-" * 40)
    print("Step 1: Agent Discovery")
    print("-" * 40)
    
    try:
        agent_card = await get_agent_card(base_url)
        print(f"\n[OK] Agent Card retrieved successfully!\n")
        print(f"   Name: {agent_card.get('name', 'Unknown')}")
        print(f"   Description: {agent_card.get('description', 'No description')}")
        print(f"   Version: {agent_card.get('version', '0.0.0')}")
        print(f"   URL: {agent_card.get('url', base_url)}")
        
        if 'capabilities' in agent_card:
            caps = agent_card['capabilities']
            print(f"   Streaming: {caps.get('streaming', False)}")
            print(f"   Push Notifications: {caps.get('pushNotifications', False)}")
        
        if 'skills' in agent_card:
            print(f"\n   Skills ({len(agent_card['skills'])}):")
            for skill in agent_card['skills']:
                print(f"     - {skill.get('name', 'Unknown')}: {skill.get('description', '')}")
        
        print("\n[DEBUG] Full Agent Card:")
        print(json.dumps(agent_card, indent=2))
        
    except httpx.HTTPError as e:
        print(f"\n[ERROR] Failed to get agent card: {e}")
        print("        Make sure the A2A server is running:")
        print("        python a2a_server.py --agent router --port 8000")
        return
    
    # Step 2: Send test messages
    print("\n" + "-" * 40)
    print("Step 2: Sending Test Messages")
    print("-" * 40)
    
    test_messages = [
        "Hello! What can you do?",
        "What's the weather in Tokyo?",
        "Calculate 25 * 4 + 10",
        "Convert 100 kilometers to miles",
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n[TEST {i}] \"{message}\"")
        
        try:
            response = await send_message(base_url, message)
            
            if "result" in response:
                result = response["result"]
                
                # Extract the response text
                if "status" in result:
                    status = result.get("status", {})
                    print(f"   Status: {status.get('state', 'unknown')}")
                
                if "artifacts" in result:
                    for artifact in result.get("artifacts", []):
                        for part in artifact.get("parts", []):
                            text = part.get("text", "")
                            if text:
                                # Truncate long responses
                                display_text = text[:200] + "..." if len(text) > 200 else text
                                print(f"   Response: {display_text}")
                
                # Show token usage if available
                if "metadata" in result and "adk_usage_metadata" in result["metadata"]:
                    tokens = result["metadata"]["adk_usage_metadata"].get("totalTokenCount", 0)
                    print(f"   Tokens: {tokens}")
                                
            elif "error" in response:
                print(f"   [ERROR] {response['error']}")
                
        except httpx.HTTPError as e:
            print(f"   [ERROR] HTTP Error: {e}")
        except Exception as e:
            print(f"   [ERROR] {e}")
    
    # Step 3: Interactive mode hint
    print("\n" + "-" * 40)
    print("Interactive Mode")
    print("-" * 40)
    print("\nTo interact with the agent programmatically:")
    print("""
from test_a2a_client import send_message, get_agent_card
import asyncio

async def chat():
    base_url = "http://localhost:8000"
    
    # Discover agent
    card = await get_agent_card(base_url)
    print(f"Talking to: {card['name']}")
    
    # Send message
    response = await send_message(base_url, "What's 2+2?")
    print(response)

asyncio.run(chat())
""")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


async def interactive_mode(base_url: str):
    """Run interactive chat mode."""
    print("\nInteractive A2A Chat")
    print("Type 'quit' or 'exit' to end the session")
    print("-" * 40)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            if not user_input:
                continue
            
            response = await send_message(base_url, user_input)
            
            if "result" in response:
                result = response["result"]
                if "artifacts" in result:
                    for artifact in result.get("artifacts", []):
                        for part in artifact.get("parts", []):
                            text = part.get("text", "")
                            if text:
                                print(f"\nAgent: {text}")
            elif "error" in response:
                print(f"\n[ERROR] {response['error']}")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")


def main():
    # Initialize Langfuse tracing
    lf.setup_langfuse()
    
    parser = argparse.ArgumentParser(
        description="A2A Client for testing multi-agent system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run demo against router agent
  python test_a2a_client.py

  # Test specific agent
  python test_a2a_client.py --url http://localhost:8001

  # Interactive chat mode
  python test_a2a_client.py --interactive

  # Just get agent card
  python test_a2a_client.py --card-only
        """
    )
    
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="A2A server URL (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive chat mode"
    )
    
    parser.add_argument(
        "--card-only", "-c",
        action="store_true",
        help="Only fetch and display the agent card"
    )
    
    args = parser.parse_args()
    
    try:
        if args.card_only:
            async def show_card():
                try:
                    card = await get_agent_card(args.url)
                    print(json.dumps(card, indent=2))
                except Exception as e:
                    print(f"[ERROR] {e}")
            asyncio.run(show_card())
        elif args.interactive:
            asyncio.run(interactive_mode(args.url))
        else:
            asyncio.run(run_demo(args.url))
    finally:
        # Flush traces to Langfuse
        if lf.get_client() and lf.is_enabled():
            lf.flush()
            print("\n[OK] Traces sent to Langfuse")


if __name__ == "__main__":
    main()
