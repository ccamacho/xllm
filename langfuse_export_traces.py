#!/usr/bin/env python3
"""
Export Traces for CLEAR Evaluation

This script exports traces for IBM CLEAR evaluation.

Tracing Architecture:
- Server (a2a_server.py) uses GoogleADKInstrumentor which sends traces 
  directly to Langfuse via OTLP
- View traces at: https://cloud.langfuse.com

For CLEAR evaluation, you have two options:

1. Export from Langfuse UI:
   - Go to https://cloud.langfuse.com
   - Navigate to Traces
   - Export as CSV

2. Use Langfuse API (this script - requires additional setup):
   - Fetches traces from Langfuse API
   - Converts to CLEAR-compatible CSV format

Usage:
    python langfuse_export_traces.py --limit 100
"""

import argparse
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def export_from_langfuse(output_path: str, limit: int = 100, minutes: int = None):
    """
    Export traces from Langfuse API to CSV for CLEAR evaluation.
    
    Args:
        output_path: Path to save the CSV file
        limit: Maximum number of traces to export
        minutes: Optional - only export traces from the last N minutes
    """
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
    
    if not public_key or not secret_key:
        print("[ERROR] Langfuse credentials not found in .env")
        print("        Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")
        return False
    
    try:
        from langfuse import Langfuse
        import pandas as pd
        
        print(f"[INFO] Connecting to Langfuse: {base_url}")
        
        client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=base_url,
            timeout=30,  # Increase timeout for API calls
        )
        
        # Fetch recent traces using the API
        if minutes:
            from_time = datetime.now() - timedelta(minutes=minutes)
            print(f"[INFO] Fetching up to {limit} traces from the last {minutes} minutes (since {from_time.strftime('%Y-%m-%d %H:%M:%S')})...")
            traces_response = client.api.trace.list(
                limit=limit,
                from_timestamp=from_time
            )
        else:
            print(f"[INFO] Fetching up to {limit} traces...")
            traces_response = client.api.trace.list(limit=limit)
        
        if not traces_response.data:
            print("[WARN] No traces found in Langfuse")
            print("       Run some queries first: python test_agents_a2a.py")
            return False
        
        print(f"[OK] Found {len(traces_response.data)} traces")
        
        # Convert to CLEAR format
        # Input/output is in observations, not at trace level
        rows = []
        for trace in traces_response.data:
            # Get full trace with observations
            try:
                full_trace = client.api.trace.get(trace.id)
            except Exception as e:
                print(f"[WARN] Could not fetch trace {trace.id}: {e}")
                continue
            
            if not hasattr(full_trace, 'observations') or not full_trace.observations:
                continue
            
            # Find input from invocation observation
            input_text = ""
            output_text = ""
            agent_name = ""
            
            for obs in full_trace.observations:
                obs_name = obs.name if hasattr(obs, 'name') else ""
                
                # Get input from invocation (contains user message)
                if "invocation" in obs_name.lower() and obs.input:
                    if isinstance(obs.input, dict):
                        # Extract user message from new_message.parts[0].text
                        new_message = obs.input.get("new_message", {})
                        if isinstance(new_message, dict):
                            parts = new_message.get("parts", [])
                            if parts and isinstance(parts, list):
                                # Get the first text part (the actual user message)
                                for part in parts:
                                    if isinstance(part, dict) and "text" in part:
                                        text = part["text"]
                                        # Skip context markers
                                        if not text.startswith("For context:") and not text.startswith("["):
                                            input_text = text
                                            break
                        if not input_text:
                            input_text = str(obs.input)[:300]
                    else:
                        input_text = str(obs.input)[:300]
                
                # Get output from agent_run (contains final response)
                if "agent_run" in obs_name.lower() and obs.output:
                    if isinstance(obs.output, dict):
                        # Extract text from parts
                        content = obs.output.get("content", {})
                        if isinstance(content, dict):
                            parts = content.get("parts", [])
                            if parts and isinstance(parts, list):
                                for part in parts:
                                    if isinstance(part, dict) and "text" in part:
                                        output_text = part["text"]
                                        break
                        if not output_text:
                            output_text = str(obs.output)[:500]
                    else:
                        output_text = str(obs.output)[:500]
                    
                    # Extract agent name from observation name like "agent_run [router_agent]"
                    if "[" in obs_name and "]" in obs_name:
                        agent_name = obs_name.split("[")[1].split("]")[0]
            
            # Skip if no output found
            if not output_text:
                continue
            
            # Calculate latency
            latency_ms = 0
            if hasattr(trace, 'latency') and trace.latency:
                latency_ms = int(trace.latency * 1000)
            
            rows.append({
                "id": trace.id,
                "model_input": input_text[:1000] if input_text else "N/A",
                "response": output_text[:2000] if output_text else "N/A",
                "trace_name": agent_name or trace.name or "agent-query",
                "latency_ms": latency_ms,
                "timestamp": trace.timestamp.isoformat() if hasattr(trace, 'timestamp') and trace.timestamp else "",
            })
        
        if not rows:
            print("[WARN] No valid traces to export")
            return False
        
        # Create DataFrame and save
        df = pd.DataFrame(rows)
        
        # Filter out empty responses
        df = df[df["response"].str.len() > 0]
        
        if df.empty:
            print("[WARN] All traces have empty responses")
            return False
        
        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_file, index=False)
        
        print(f"[OK] Exported {len(df)} traces to {output_file}")
        print(f"\n[INFO] Next step - run CLEAR evaluation:")
        print(f"       run-clear-eval-analysis \\")
        print(f"         --provider google \\")
        print(f"         --data-path {output_file} \\")
        print(f"         --output-dir clear/results \\")
        print(f"         --agent-mode True")
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] Missing dependency: {e}")
        print("        Run: pip install langfuse pandas")
        return False
    except Exception as e:
        print(f"[ERROR] Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Export Langfuse traces to CSV for CLEAR evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python langfuse_export_traces.py
  python langfuse_export_traces.py --limit 500
  python langfuse_export_traces.py --minutes 30  # Last 30 minutes
  python langfuse_export_traces.py --output my_traces.csv --minutes 60
        """
    )
    
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=100,
        help="Maximum number of traces to export (default: 100)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="clear/traces/clear_langfuse_traces.csv",
        help="Output CSV file path"
    )
    
    parser.add_argument(
        "--minutes", "-m",
        type=int,
        default=None,
        help="Only export traces from the last N minutes (default: all traces)"
    )
    
    args = parser.parse_args()
    
    export_from_langfuse(args.output, args.limit, args.minutes)


if __name__ == "__main__":
    main()
