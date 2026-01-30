#!/usr/bin/env python3
"""Query Cosmos DB for step completion statistics."""

import asyncio
import os
import sys
from collections import defaultdict

# Add the mcp-csp src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src/mcp-servers/csp"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src/mcp-servers/csp/src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src/shared"))

from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential


async def get_step_stats():
    """Query step completions and generate statistics."""
    
    # Get Cosmos endpoint from environment or use the known endpoint
    cosmos_endpoint = os.environ.get("COSMOS_ENDPOINT", "https://aldelar-csp-cosmos.documents.azure.com:443/")
    database_name = os.environ.get("COSMOS_DATABASE", "csp")
    container_name = "step_completions"
    
    print(f"Connecting to Cosmos DB: {cosmos_endpoint}")
    print(f"Database: {database_name}, Container: {container_name}")
    print("-" * 60)
    
    credential = DefaultAzureCredential()
    
    async with CosmosClient(cosmos_endpoint, credential) as client:
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        # Query all step completions
        query = "SELECT * FROM c"
        
        items = []
        async for item in container.query_items(query=query):
            items.append(item)
        
        print(f"\nTotal step completions: {len(items)}")
        print("=" * 60)
        
        if not items:
            print("No step completions found.")
            return
        
        # Stats by step type
        by_step_type = defaultdict(list)
        for item in items:
            step_type = item.get("stepType", "unknown")
            by_step_type[step_type].append(item)
        
        print("\n📊 STEP COMPLETIONS BY TYPE:")
        print("-" * 60)
        
        for step_type, completions in sorted(by_step_type.items(), key=lambda x: -len(x[1])):
            count = len(completions)
            
            # Calculate average duration
            durations = [c.get("durationDays", 0) for c in completions if c.get("durationDays") is not None]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Calculate average attempts
            attempts = [c.get("attempts", 1) for c in completions if c.get("attempts") is not None]
            avg_attempts = sum(attempts) / len(attempts) if attempts else 1
            
            print(f"\n  {step_type}:")
            print(f"    Count: {count}")
            print(f"    Avg Duration: {avg_duration:.2f} days")
            print(f"    Avg Attempts: {avg_attempts:.2f}")
        
        # Summary statistics
        print("\n" + "=" * 60)
        print("📈 SUMMARY STATISTICS:")
        print("-" * 60)
        
        all_durations = [item.get("durationDays", 0) for item in items if item.get("durationDays") is not None]
        all_attempts = [item.get("attempts", 1) for item in items if item.get("attempts") is not None]
        
        if all_durations:
            print(f"  Overall Avg Duration: {sum(all_durations)/len(all_durations):.2f} days")
            print(f"  Min Duration: {min(all_durations):.4f} days")
            print(f"  Max Duration: {max(all_durations):.4f} days")
        
        if all_attempts:
            print(f"  Overall Avg Attempts: {sum(all_attempts)/len(all_attempts):.2f}")
            print(f"  Max Attempts: {max(all_attempts)}")
        
        print(f"\n  Total Step Types: {len(by_step_type)}")
        print(f"  Total Completions: {len(items)}")


if __name__ == "__main__":
    asyncio.run(get_step_stats())
