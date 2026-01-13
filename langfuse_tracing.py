"""
Langfuse Tracing Utilities

Shared tracing functionality for both direct ADK and A2A client methods.
This module provides:
- Langfuse client initialization
- Query classification for tagging
- Trace export to CSV for CLEAR evaluation
- Local trace storage
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

# Global state
langfuse_client = None
tracing_enabled = False

# Local trace storage
LOCAL_TRACES_DIR = Path("traces")
local_traces: List[Dict[str, Any]] = []


def setup_langfuse() -> bool:
    """
    Initialize Langfuse tracing client.
    
    Returns:
        True if tracing was successfully enabled, False otherwise.
    """
    global langfuse_client, tracing_enabled
    
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
    
    if not public_key or not secret_key:
        print("[WARN] Langfuse credentials not found. Running without tracing.")
        return False
    
    if "your_langfuse" in public_key:
        print("[WARN] Langfuse using placeholder keys. Running without tracing.")
        return False
    
    try:
        from langfuse import Langfuse
        
        langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=base_url,
            environment="development",
        )
        
        tracing_enabled = True
        print("[OK] Langfuse tracing enabled")
        print(f"     Dashboard: {base_url}")
        return True
        
    except ImportError as e:
        print(f"[WARN] Missing dependency: {e}")
        return False
    except Exception as e:
        print(f"[WARN] Failed to initialize tracing: {e}")
        return False


def get_client():
    """Get the Langfuse client instance."""
    return langfuse_client


def is_enabled() -> bool:
    """Check if tracing is enabled."""
    return tracing_enabled


def flush():
    """Flush pending traces to Langfuse."""
    if langfuse_client:
        langfuse_client.flush()


def classify_query(query: str) -> str:
    """
    Classify query type for tagging.
    
    Args:
        query: The user's query string
        
    Returns:
        Query type: 'weather', 'calculation', 'conversion', 'greeting', or 'general'
    """
    query_lower = query.lower()
    
    if any(word in query_lower for word in ["weather", "temperature", "forecast", "rain", "sunny", "climate"]):
        return "weather"
    elif any(word in query_lower for word in ["calculate", "compute", "math", "%", "percent", "sqrt", "sum", "add", "multiply", "divide"]):
        return "calculation"
    elif any(word in query_lower for word in ["convert", "to miles", "to km", "to celsius", "to fahrenheit", "to lbs", "to kg"]):
        return "conversion"
    elif any(word in query_lower for word in ["hello", "hi", "help", "what can you"]):
        return "greeting"
    else:
        return "general"


def save_trace_locally(trace_data: Dict[str, Any]):
    """
    Save trace to local JSON file for offline analysis.
    
    Args:
        trace_data: Dictionary containing trace information
    """
    global local_traces
    
    local_traces.append(trace_data)
    LOCAL_TRACES_DIR.mkdir(exist_ok=True)
    
    timestamp = trace_data.get("timestamp", datetime.now().isoformat())
    filename = f"trace_{timestamp.replace(':', '-').replace('.', '-')}.json"
    filepath = LOCAL_TRACES_DIR / filename
    
    with open(filepath, "w") as f:
        json.dump(trace_data, f, indent=2, default=str)


def save_session_traces(session_id: str):
    """
    Save all traces from a session to a single file.
    
    Args:
        session_id: The session identifier
    """
    if not local_traces:
        return
    
    LOCAL_TRACES_DIR.mkdir(exist_ok=True)
    
    session_file = LOCAL_TRACES_DIR / f"session_{session_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(session_file, "w") as f:
        json.dump({
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "trace_count": len(local_traces),
            "traces": local_traces,
        }, f, indent=2, default=str)
    
    print(f"[SAVED] {len(local_traces)} traces to {session_file}")


def clear_local_traces():
    """Clear the in-memory trace list."""
    global local_traces
    local_traces = []


def create_trace_span(name: str, input_data: dict, metadata: dict = None):
    """
    Create a trace span context manager.
    
    Args:
        name: Name of the trace span
        input_data: Input data for the trace
        metadata: Additional metadata
        
    Returns:
        Trace span context manager or None if tracing disabled
    """
    if not langfuse_client or not tracing_enabled:
        return None
    
    return langfuse_client.start_as_current_span(
        name=name,
        input=input_data,
        metadata=metadata or {},
    )
