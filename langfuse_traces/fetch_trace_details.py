#!/usr/bin/env python3
"""
Fetch complete trace data from Langfuse including all observations/spans.

Usage:
    python fetch_trace_details.py <trace_id> [<trace_id2> ...]
    
Example:
    python fetch_trace_details.py 68423b551dd9039a58648b8711bb25bc 1fe33d35833c563f063bcd5f365aed5e

Required environment variables:
    LANGFUSE_PUBLIC_KEY
    LANGFUSE_SECRET_KEY
    LANGFUSE_HOST (optional, defaults to https://cloud.langfuse.com)
"""

import os
import json
import argparse

try:
    import requests
except ImportError:
    print("Error: requests package not installed.")
    print("Install it with: pip install requests")
    exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


def fetch_trace(trace_id: str) -> dict:
    """Fetch a trace with all its observations using Langfuse REST API."""
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    base_url = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    if not public_key or not secret_key:
        raise ValueError(
            "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set.\n"
            "Set them in your .env file or as environment variables."
        )
    
    url = f"{base_url}/api/public/traces/{trace_id}"
    
    response = requests.get(
        url,
        auth=(public_key, secret_key),
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        raise Exception(f"API error {response.status_code}: {response.text}")
    
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Fetch complete trace data from Langfuse")
    parser.add_argument("trace_ids", nargs="+", help="Trace IDs to fetch")
    parser.add_argument("-o", "--output", default="trace_details.json", help="Output file")
    
    args = parser.parse_args()
    
    print(f"Fetching {len(args.trace_ids)} traces from Langfuse...")
    print()
    
    results = []
    for trace_id in args.trace_ids:
        try:
            data = fetch_trace(trace_id)
            results.append(data)
            print(f"✓ Fetched trace {trace_id}")
        except Exception as e:
            print(f"✗ Failed to fetch {trace_id}: {e}")
    
    # Save results
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✓ Saved {len(results)} traces to {args.output}")
    
    # Print summary
    for trace in results:
        print(f"\n{'='*60}")
        print(f"Trace ID: {trace.get('id', 'N/A')}")
        print(f"Name: {trace.get('name', 'N/A')}")
        print(f"Latency: {trace.get('latency', 'N/A')}s")
        print(f"Input: {str(trace.get('input', 'N/A'))[:100]}...")
        print(f"Output: {str(trace.get('output', 'N/A'))[:100]}...")
        
        observations = trace.get('observations', [])
        print(f"Observations: {len(observations)}")
        
        for obs in observations[:10]:  # Show first 10
            obs_name = obs.get('name', 'unknown')
            obs_type = obs.get('type', 'unknown')
            prompt_tokens = obs.get('promptTokens', 0) or 0
            completion_tokens = obs.get('completionTokens', 0) or 0
            print(f"  - {obs_type}: {obs_name} (tokens: {prompt_tokens} → {completion_tokens})")
        
        if len(observations) > 10:
            print(f"  ... and {len(observations) - 10} more observations")


if __name__ == "__main__":
    main()

# Example usage:
#  fetch_trace_details.py \
#    68423b551dd9039a58648b8711bb25bc \
#    1fe33d35833c563f063bcd5f365aed5e \
#    -o langfuse_traces/02_delegation_weather/traces.json
