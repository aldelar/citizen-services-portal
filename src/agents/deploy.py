#!/usr/bin/env python3
"""
Master deployment script for AI Agents.

Orchestrates the deployment of:
1. Agent tools (deploy_tools.py)
2. Agent definition (deploy_agent.py)

Usage:
    python deploy.py <agent_name>
    
Examples:
    python deploy.py ladbs
    python deploy.py ladwp
"""

import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def run_script(script_name: str, agent_name: str) -> bool:
    """
    Run a deployment script.
    
    Args:
        script_name: Name of the script to run
        agent_name: Name of the agent to deploy
    
    Returns:
        True if successful, False otherwise
    """
    script_path = SCRIPT_DIR / script_name
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_name}")
        return False
    
    print(f"\n{'=' * 60}")
    print(f"Running: {script_name}")
    print(f"{'=' * 60}\n")
    
    try:
        result = subprocess.run(
            ["uv", "run", str(script_path), agent_name],
            cwd=SCRIPT_DIR,
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {script_name} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ Error running {script_name}: {e}")
        return False


def main():
    """Main deployment orchestration."""
    if len(sys.argv) < 2:
        print("Usage: python deploy.py <agent_name>")
        print("\nExamples:")
        print("  python deploy.py ladbs")
        print("  python deploy.py ladwp")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    
    print("=" * 60)
    print(f"{agent_name.upper()} Agent - Master Deployment")
    print("=" * 60)
    
    # Step 1: Deploy tools
    if not run_script("deploy_tools.py", agent_name):
        print("\n⚠️  Tool deployment failed, but continuing with agent deployment...")
        # Don't exit - tools might not be critical for initial deployment
    
    # Step 2: Deploy agent
    if not run_script("deploy_agent.py", agent_name):
        print("\n❌ Agent deployment failed")
        sys.exit(1)
    
    # Success
    print("\n" + "=" * 60)
    print(f"✅ {agent_name.upper()} Agent Deployment Complete!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
