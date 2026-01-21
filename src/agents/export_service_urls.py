#!/usr/bin/env python3
"""
Helper script to programmatically resolve service URLs for agent deployment.

This script:
1. Reads azd environment variables
2. Discovers all service URIs based on azure.yaml services
3. Exports them in a format that can be sourced by deployment scripts

Convention:
- azure.yaml service name: mcp-ladbs
- azd env variable: mcpLadbsUri
- Exported variable: SERVICE_MCP_LADBS_URI
"""

import os
import sys
import subprocess
import json
import yaml
from pathlib import Path


def service_name_to_env_var(service_name: str) -> str:
    """
    Convert azure.yaml service name to azd environment variable name.
    
    Example: mcp-ladbs -> mcpLadbsUri
    """
    # Remove hyphens and camelCase the parts
    parts = service_name.split('-')
    camel_case = parts[0] + ''.join(word.capitalize() for word in parts[1:])
    return f"{camel_case}Uri"


def service_name_to_export_var(service_name: str) -> str:
    """
    Convert azure.yaml service name to export variable name.
    
    Example: mcp-ladbs -> SERVICE_MCP_LADBS_URI
    """
    return f"SERVICE_{service_name.upper().replace('-', '_')}_URI"


def get_azd_services() -> list[str]:
    """Get list of services from azure.yaml."""
    # Find azure.yaml (should be in project root)
    script_dir = Path(__file__).parent.parent.parent
    azure_yaml_path = script_dir / "azure.yaml"
    
    if not azure_yaml_path.exists():
        print(f"Warning: azure.yaml not found at {azure_yaml_path}", file=sys.stderr)
        return []
    
    with open(azure_yaml_path, 'r') as f:
        config = yaml.safe_load(f)
    
    services = config.get('services', {})
    return list(services.keys())


def get_azd_env_value(var_name: str) -> str:
    """Get a value from azd environment."""
    try:
        result = subprocess.run(
            ['azd', 'env', 'get-value', var_name],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"Warning: Could not get {var_name}: {e}", file=sys.stderr)
    return ""


def main():
    """Main entry point."""
    # Get all services from azure.yaml
    services = get_azd_services()
    
    if not services:
        print("No services found in azure.yaml", file=sys.stderr)
        sys.exit(1)
    
    print(f"# Auto-generated service URLs from azd environment", file=sys.stderr)
    print(f"# Found {len(services)} service(s)", file=sys.stderr)
    
    # For each service, try to get its URI from azd env
    exports = []
    for service_name in services:
        azd_var = service_name_to_env_var(service_name)
        export_var = service_name_to_export_var(service_name)
        
        value = get_azd_env_value(azd_var)
        if value:
            exports.append(f'export {export_var}="{value}"')
            print(f"# {service_name} -> {export_var}", file=sys.stderr)
        else:
            print(f"# Warning: No URI found for service '{service_name}' (tried {azd_var})", file=sys.stderr)
    
    # Output shell commands that can be eval'd
    print()  # Empty line after stderr output
    for export in exports:
        print(export)


if __name__ == "__main__":
    main()
