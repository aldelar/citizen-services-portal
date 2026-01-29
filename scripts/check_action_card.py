#!/usr/bin/env python3
"""Check if action card is stored in a project step."""

import asyncio
import os
import sys
from pathlib import Path

# Run from web-app directory to get the right imports
web_app_dir = Path(__file__).parent.parent / "src" / "web-app"
os.chdir(web_app_dir)
sys.path.insert(0, str(web_app_dir))
sys.path.insert(0, str(web_app_dir.parent / "shared"))

from services.project_service import get_project_service


async def check_action_card():
    """Check if action card exists in the project."""
    print("🔍 Checking for action card in project step...")
    
    service = get_project_service()
    
    # Default user_id (same as in main.py)
    user_id = "user123"
    
    try:
        # Get all projects
        print(f"\n📋 Loading projects for user: {user_id}")
        projects = await service.get_user_projects(user_id)
        print(f"   Found {len(projects)} projects")
        
        # Find the project with title containing 260129-1349
        target_project = None
        for project in projects:
            if "260129-1349" in project.get("title", ""):
                target_project = project
                break
        
        if not target_project:
            print(f"\n❌ Project with title containing '260129-1349' not found")
            print(f"\nAvailable projects:")
            for p in projects:
                print(f"   - {p.get('title')} (ID: {p.get('id')})")
            return
        
        print(f"\n✅ Found project: {target_project['title']}")
        print(f"   Project ID: {target_project['id']}")
        
        # Check for plan and steps
        plan = target_project.get("plan")
        if not plan or not plan.get("steps"):
            print("❌ Project has no plan or steps")
            return
        
        steps = plan.get("steps", [])
        print(f"   Steps: {len(steps)} total")
        
        # Find TRD-1
        trd_step = None
        for step in steps:
            if step.get("id") == "TRD-1":
                trd_step = step
                break
        
        if not trd_step:
            print("\n❌ Step TRD-1 not found in project")
            print(f"   Available steps: {[s.get('id') for s in steps]}")
            return
        
        print(f"\n✅ Found step TRD-1:")
        print(f"   Title: {trd_step.get('title')}")
        print(f"   Status: {trd_step.get('status')}")
        print(f"   Action Type: {trd_step.get('action_type')}")
        
        # Check for action card
        action_card = trd_step.get("user_action_card") or trd_step.get("userActionCard")
        
        if action_card:
            print(f"\n✅ *** ACTION CARD FOUND! ***")
            print(f"   Step ID: {action_card.get('step_id') or action_card.get('stepId')}")
            print(f"   Card Type: {action_card.get('card_type') or action_card.get('cardType')}")
            print(f"   Title: {action_card.get('title')}")
            instructions = action_card.get('instructions', '')
            print(f"   Instructions: {instructions[:100]}..." if len(instructions) > 100 else f"   Instructions: {instructions}")
            
            # Show all fields
            print(f"\n   All card fields:")
            for key, value in action_card.items():
                if isinstance(value, str) and len(value) > 80:
                    print(f"      {key}: {value[:80]}...")
                else:
                    print(f"      {key}: {value}")
        else:
            print(f"\n❌ No action card found for step TRD-1")
            print(f"   Step fields: {list(trd_step.keys())}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_action_card())
