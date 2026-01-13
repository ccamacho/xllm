#!/usr/bin/env python3
"""
Export Local Traces for CLEAR Evaluation

Reads traces from local JSON files and exports them to CSV format
compatible with IBM CLEAR for LLM-as-a-Judge evaluation.

Usage:
    python langfuse_export_traces.py                    # Export all local traces
    python langfuse_export_traces.py --output my.csv    # Custom output path
"""

import argparse
import json
from pathlib import Path


def export_traces(traces_dir: str, output_path: str):
    """Export local traces to CSV for CLEAR."""
    
    traces_path = Path(traces_dir)
    
    if not traces_path.exists():
        print(f"[ERROR] Traces directory not found: {traces_path}")
        return False
    
    # Find all trace JSON files
    trace_files = list(traces_path.glob("trace_*.json")) + list(traces_path.glob("session_*.json"))
    
    if not trace_files:
        print(f"[WARN] No trace files found in {traces_path}")
        print("       Run 'python test_agents_adk.py --demo' first to generate traces")
        return False
    
    print(f"[INFO] Found {len(trace_files)} trace files in {traces_path}")
    
    try:
        import pandas as pd
        
        rows = []
        
        for trace_file in trace_files:
            with open(trace_file) as f:
                data = json.load(f)
            
            # Handle session files (contain multiple traces)
            if "traces" in data:
                traces = data["traces"]
            else:
                traces = [data]
            
            for trace in traces:
                rows.append({
                    "id": trace.get("trace_id", trace_file.stem),
                    "model_input": trace.get("query", ""),
                    "response": trace.get("response", ""),
                    "trace_name": "agent-query",
                    "latency_ms": trace.get("latency_ms", 0),
                    "tools_used": str(trace.get("tools_used", [])),
                    "query_type": trace.get("query_type", "general"),
                    "method": "adk",
                    "timestamp": trace.get("timestamp", ""),
                })
        
        if not rows:
            print("[WARN] No traces extracted from files")
            return False
        
        # Create DataFrame and save
        df = pd.DataFrame(rows)
        
        # Filter out empty responses
        df = df[df["response"].str.len() > 0]
        
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
        
    except ImportError:
        print("[ERROR] pandas not installed. Run: pip install pandas")
        return False
    except Exception as e:
        print(f"[ERROR] Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Export local traces to CSV for CLEAR evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python langfuse_export_traces.py
  python langfuse_export_traces.py --output my_traces.csv
  python langfuse_export_traces.py --traces-dir traces/
        """
    )
    
    parser.add_argument(
        "--traces-dir", "-t",
        type=str,
        default="traces",
        help="Directory containing trace JSON files (default: traces/)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="clear/traces/clear_langfuse_traces.csv",
        help="Output CSV file path (default: clear/traces/clear_langfuse_traces.csv)"
    )
    
    args = parser.parse_args()
    
    # Run export
    export_traces(args.traces_dir, args.output)


if __name__ == "__main__":
    main()
