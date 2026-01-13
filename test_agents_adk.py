#!/usr/bin/env python3
"""
Test Agents via ADK (Direct Python)

Run agents directly in the same Python process using Google ADK.
All traces are sent to Langfuse for comparison with A2A method.

Usage:
    python test_agents_adk.py --demo        # Run demo queries
    python test_agents_adk.py --query "..." # Single query
    python test_agents_adk.py               # Interactive mode
"""

import os
import asyncio
import time
from datetime import datetime
from typing import Optional, List

# Import shared tracing utilities
import langfuse_tracing as lf

# Set up tracing
lf.setup_langfuse()

# Shortcuts
classify_query = lf.classify_query
save_trace_locally = lf.save_trace_locally
save_session_traces = lf.save_session_traces


def ensure_dataset_exists(dataset_name: str = "agent-evaluations") -> bool:
    """Ensure a dataset exists for storing traces."""
    client = lf.get_client()
    if not client:
        return False
    
    try:
        client.get_dataset(dataset_name)
        return True
    except Exception:
        try:
            client.create_dataset(
                name=dataset_name,
                description="Multi-agent system traces for evaluation and analysis",
                metadata={"created_by": "run_with_tracing.py"},
            )
            print(f"[OK] Created dataset: {dataset_name}")
            return True
        except Exception as e:
            print(f"[WARN] Could not create dataset: {e}")
            return False

# Now import ADK components
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


def create_agents():
    """Create fresh agent instances."""
    
    from agents.weather_agent import get_weather
    from agents.calculator_agent import calculate, convert_units, calculate_percentage
    
    weather_agent = Agent(
        name="weather_agent",
        model="gemini-2.0-flash",
        description="Provides weather information for any location worldwide.",
        instruction="You are a weather assistant. Use the get_weather tool.",
        tools=[get_weather],
    )
    
    calculator_agent = Agent(
        name="calculator_agent",
        model="gemini-2.0-flash",
        description="Performs mathematical calculations and conversions.",
        instruction="You are a math assistant. Use calculation tools.",
        tools=[calculate, convert_units, calculate_percentage],
    )
    
    root_agent = Agent(
        name="router_agent",
        model="gemini-2.0-flash",
        description="A multi-agent coordinator.",
        instruction="""You are a helpful assistant. 
For weather queries → Use get_weather tool
For math queries → Use calculate, convert_units, or calculate_percentage
For general questions → Answer directly""",
        tools=[get_weather, calculate, convert_units, calculate_percentage],
        sub_agents=[weather_agent, calculator_agent],
    )
    
    return root_agent


async def run_query(
    query: str, 
    runner: Runner, 
    session_id: str, 
    user_id: str = "demo-user",
    add_to_dataset: bool = False,
    dataset_name: str = "agent-evaluations",
    tags: Optional[List[str]] = None,
):
    """Run a single query with full Langfuse tracing and local storage."""
    
    print(f"\n[QUERY] {query}")
    print("-" * 50)
    
    start_time = time.time()
    timestamp = datetime.now().isoformat()
    response_text = ""
    tool_calls = []
    trace_id = None
    
    # Auto-classify query for tagging
    query_type = classify_query(query)
    auto_tags = [query_type, "multi-agent"]
    if tags:
        auto_tags.extend(tags)
    
    # Create proper Content object
    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=query)]
    )
    
    try:
        if lf.get_client() and lf.is_enabled():
            # Use Langfuse span context manager with tags
            with lf.get_client().start_as_current_span(
                name="agent-query",
                input={"query": query, "user_id": user_id, "session_id": session_id},
                metadata={
                    "agent": "router_agent", 
                    "model": "gemini-2.0-flash",
                    "query_type": query_type,
                },
            ) as trace_span:
                # Get trace ID for dataset linking
                trace_id = lf.get_client().get_current_trace_id()
                
                # Run the agent inside the trace
                async for event in runner.run_async(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=user_message,
                ):
                    if hasattr(event, 'content') and event.content:
                        if hasattr(event.content, 'parts'):
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    response_text += part.text
                                if hasattr(part, 'function_call') and part.function_call:
                                    tool_calls.append(part.function_call.name)
                
                elapsed = time.time() - start_time
                
                # Estimate tokens
                input_tokens = max(1, len(query) // 4)
                output_tokens = max(1, len(response_text) // 4)
                
                # Update span with full details
                trace_span.update(
                    output={"response": response_text, "tools_used": list(set(tool_calls))},
                    usage_details={
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": input_tokens + output_tokens,
                    },
                    metadata={
                        "latency_ms": int(elapsed * 1000),
                        "tools_used": list(set(tool_calls)),
                        "query_type": query_type,
                        "tags": auto_tags,
                    },
                )
                
                # Score the trace based on response quality
                if response_text and len(response_text) > 10:
                    trace_span.score(
                        name="has_response",
                        value=1,
                        data_type="BOOLEAN",
                        comment="Response was generated successfully",
                    )
                
                if tool_calls:
                    trace_span.score(
                        name="used_tools",
                        value=1,
                        data_type="BOOLEAN", 
                        comment=f"Used tools: {', '.join(set(tool_calls))}",
                    )
                
                # Add to dataset if requested
                if add_to_dataset and trace_id:
                    try:
                        ensure_dataset_exists(dataset_name)
                        lf.get_client().create_dataset_item(
                            dataset_name=dataset_name,
                            input={"query": query},
                            expected_output={"response": response_text},
                            metadata={
                                "tools_used": list(set(tool_calls)),
                                "query_type": query_type,
                                "latency_ms": int(elapsed * 1000),
                            },
                        )
                        print(f"[OK] Added to dataset: {dataset_name}")
                    except Exception as e:
                        print(f"[WARN] Could not add to dataset: {e}")
        else:
            # Run without Langfuse tracing
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_message,
            ):
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts'):
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text += part.text
                            if hasattr(part, 'function_call') and part.function_call:
                                tool_calls.append(part.function_call.name)
        
        elapsed = time.time() - start_time
        input_tokens = max(1, len(query) // 4)
        output_tokens = max(1, len(response_text) // 4)
        
        # Create local trace record
        trace_data = {
            "trace_id": trace_id,
            "timestamp": timestamp,
            "session_id": session_id,
            "user_id": user_id,
            "query": query,
            "query_type": query_type,
            "response": response_text,
            "tools_used": list(set(tool_calls)),
            "latency_ms": int(elapsed * 1000),
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens,
            },
            "tags": auto_tags,
            "success": bool(response_text),
        }
        
        # Save locally
        save_trace_locally(trace_data)
        
        # Print results
        if tool_calls:
            print(f"[TOOLS] {', '.join(set(tool_calls))}")
        print(f"[RESPONSE] {response_text}")
        print(f"[LATENCY] {elapsed:.2f}s")
        print(f"[TOKENS] ~{input_tokens} in / ~{output_tokens} out")
        print(f"[TAGS] {', '.join(auto_tags)}")
        
        return response_text
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


async def run_demo(add_to_dataset: bool = False):
    """Run full demo session with tracing."""
    
    demo_queries = [
        "Hello! What can you help me with?",
        "What's the weather like in Tokyo?",
        "Calculate 25% of 180",
        "What is sqrt(144) + 5^2?",
        "Convert 100 kilometers to miles",
        "What's the weather in Paris?",
    ]
    
    print("\n" + "=" * 60)
    print("  Multi-Agent Demo with Langfuse Tracing")
    print("=" * 60)
    
    if add_to_dataset:
        print("  Adding traces to dataset for evaluation")
    
    root_agent = create_agents()
    session_service = InMemorySessionService()
    
    runner = Runner(
        agent=root_agent,
        app_name="multi-agent-demo",
        session_service=session_service,
    )
    
    session = await session_service.create_session(
        app_name="multi-agent-demo",
        user_id="demo-user",
    )
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n[{i}/{len(demo_queries)}]", end="")
        await run_query(
            query, 
            runner, 
            session.id, 
            "demo-user",
            add_to_dataset=add_to_dataset,
            tags=["demo"],
        )
        await asyncio.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("  Demo completed!")
    print("=" * 60)
    
    # Save session traces locally
    save_session_traces(session.id)
    
    if lf.get_client() and lf.is_enabled():
        print("\n[INFO] Flushing traces to Langfuse...")
        lf.flush()
        await asyncio.sleep(2)
        print("       Done! View at: https://cloud.langfuse.com")


async def run_interactive():
    """Run interactive session."""
    
    print("\n" + "=" * 60)
    print("  Multi-Agent System with Langfuse Tracing")
    print("=" * 60)
    print("\nCapabilities:")
    print("  - Weather: \"What's the weather in Tokyo?\"")
    print("  - Math: \"Calculate 25% of 180\"")
    print("  - Convert: \"Convert 100 km to miles\"")
    print("\nCommands:")
    print("  - 'quit' - Exit")
    print("  - 'demo' - Run demo queries")
    print("  - 'export' - Export traces to JSON")
    print("-" * 60)
    
    root_agent = create_agents()
    session_service = InMemorySessionService()
    
    runner = Runner(
        agent=root_agent,
        app_name="multi-agent-demo",
        session_service=session_service,
    )
    
    session = await session_service.create_session(
        app_name="multi-agent-demo",
        user_id="interactive-user",
    )
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if user_input.lower() == 'demo':
                demo_qs = [
                    "What's the weather in Tokyo?",
                    "Calculate 25% of 180",
                ]
                for q in demo_qs:
                    await run_query(q, runner, session.id, "interactive-user")
                continue
            
            if user_input.lower() == 'export':
                save_session_traces(session.id)
                continue
            
            await run_query(user_input, runner, session.id, "interactive-user")
            
        except KeyboardInterrupt:
            break
    
    # Save traces on exit
    save_session_traces(session.id)
    
    print("\nGoodbye!")
    if lf.get_client():
        lf.flush()


def check_environment():
    """Check required environment variables."""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key or "your_google" in google_api_key:
        print("\n[ERROR] GOOGLE_API_KEY not configured")
        return False
    return True


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Agent System with Langfuse")
    parser.add_argument("--demo", "-d", action="store_true", help="Run demo")
    parser.add_argument("--query", "-q", type=str, help="Single query")
    parser.add_argument("--dataset", action="store_true", help="Add traces to Langfuse dataset")
    args = parser.parse_args()
    
    if not check_environment():
        return
    
    if args.query:
        root_agent = create_agents()
        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="multi-agent-demo",
            session_service=session_service,
        )
        session = await session_service.create_session(
            app_name="multi-agent-demo",
            user_id="cli-user",
        )
        await run_query(
            args.query, 
            runner, 
            session.id, 
            "cli-user",
            add_to_dataset=args.dataset,
        )
        save_session_traces(session.id)
        if lf.get_client():
            lf.flush()
            await asyncio.sleep(1)
    elif args.demo:
        await run_demo(add_to_dataset=args.dataset)
    else:
        await run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
