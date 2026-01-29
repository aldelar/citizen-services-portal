#!/usr/bin/env python3
"""Query CosmosDB to check project plan data."""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add web-app to path
web_app_dir = Path(__file__).parent.parent / "src" / "web-app"
sys.path.insert(0, str(web_app_dir))
sys.path.insert(0, str(web_app_dir.parent / "shared"))

from cosmos.client import get_cosmos_client, get_database


async def query_project():
    """Query CosmosDB for the project."""
    try:
        # Get database
        database = await get_database()
        container = database.get_container_client("projects")
        
        print("🔍 Querying CosmosDB for project '260129-1349'...")
        print(f"   Database: {database.id}")
        print(f"   Container: projects")
        
        # Query for project with title containing 260129-1349
        query = "SELECT * FROM c WHERE CONTAINS(c.title, '260129-1349')"
        
        items = []
        async for item in container.query_items(
            query=query,
            partition_key=None
        ):
            items.append(item)
        
        if not items:
            print("\n❌ No project found with title containing '260129-1349'")
            
            # Try to list all projects
            print("\n📋 Listing all projects in database:")
            query_all = "SELECT c.id, c.title, c.userId FROM c"
            all_items = []
            async for item in container.query_items(
                query=query_all,
                partition_key=None
            ):
                all_items.append(item)
            
            if all_items:
                for item in all_items:
                    print(f"   - {item.get('title')} (ID: {item.get('id')}, User: {item.get('userId')})")
            else:
                print("   No projects found in database")
            return
        
        print(f"\n✅ Found {len(items)} project(s)")
        
        for project in items:
            print(f"\n{'='*80}")
            print(f"Project: {project.get('title')}")
            print(f"ID: {project.get('id')}")
            print(f"User ID: {project.get('userId')}")
            print(f"Status: {project.get('status')}")
            
            plan = project.get('plan')
            if not plan:
                print("\n❌ No plan found in project")
                continue
            
            steps = plan.get('steps', [])
            print(f"\n📋 Plan has {len(steps)} steps:")
            
            for step in steps:
                step_id = step.get('id')
                title = step.get('title')
                status = step.get('status')
                action_type = step.get('actionType') or step.get('action_type')
                
                print(f"\n  Step: {step_id}")
                print(f"  Title: {title}")
                print(f"  Status: {status}")
                print(f"  Action Type: {action_type}")
                
                # Check for action card
                action_card = step.get('userActionCard') or step.get('user_action_card')
                if action_card:
                    print(f"  ✅ HAS ACTION CARD:")
                    print(f"     Card Type: {action_card.get('cardType') or action_card.get('card_type')}")
                    print(f"     Title: {action_card.get('title')}")
                    
                    # Show full card data
                    print(f"\n     Full card data:")
                    print(json.dumps(action_card, indent=6, default=str))
                else:
                    print(f"  ❌ No action card")
                
                # Check history
                history = step.get('history', [])
                if history:
                    print(f"  📜 History ({len(history)} events):")
                    for event in history:
                        print(f"     - {event.get('eventType')}: {event.get('summary')}")
        
        print(f"\n{'='*80}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(query_project())
