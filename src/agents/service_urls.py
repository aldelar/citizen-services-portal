#!/usr/bin/env python3
"""
Library for resolving service URLs from Azure deployment.

This module:
1. Reads azure.yaml to discover services
2. Queries azd environment for service URIs
3. Returns them in a standardized format for agent deployment

Convention:
- azure.yaml service name: mcp-ladbs or mcp-ladwp
- azd env variable: mcpLadbsUri or mcpLadwpUri
- Dictionary key: SERVICE_MCP_LADBS_URI or SERVICE_MCP_LADWP_URI
"""

import os
import sys
import subprocess
import yaml
from pathlib import Path


def service_name_to_env_var(service_name: str) -> str:
    """
    Convert azure.yaml service name to azd environment variable name.
    
    Examples: 
        mcp-ladbs -> mcpLadbsUri
        mcp-ladwp -> mcpLadwpUri
    """
    parts = service_name.split('-')
    camel_case = parts[0] + ''.join(word.capitalize() for word in parts[1:])
    return f"{camel_case}Uri"


def service_name_to_export_var(service_name: str) -> str:
    """
    Convert azure.yaml service name to export variable name.
    
    Examples: 
        mcp-ladbs -> SERVICE_MCP_LADBS_URI
        mcp-ladwp -> SERVICE_MCP_LADWP_URI
    """
    return f"SERVICE_{service_name.upper().replace('-', '_')}_URI"


def get_azd_services() -> list[str]:
    """Get list of services from azure.yaml."""
    script_dir = Path(__file__).parent.parent.parent
    azure_yaml_path = script_dir / "azure.yaml"
    
    if not azure_yaml_path.exists():
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
    except Exception:
        pass
    return ""


def get_service_urls() -> dict[str, str]:
    """
    Get all service URLs from azd environment.
    
    Returns:
        Dictionary mapping service variable names to their URLs.
        Example: {
            "SERVICE_MCP_LADBS_URI": "https://...", 
            "SERVICE_MCP_LADWP_URI": "https://...",
            "MCP_LADBS_SCOPE_URI": "https://...",
            "MCP_LADWP_SCOPE_URI": "https://..."
        }
    """
    services = get_azd_services()
    
    if not services:
        return {}
    
    service_urls = {}
    for service_name in services:
        azd_var = service_name_to_env_var(service_name)
        export_var = service_name_to_export_var(service_name)
        
        value = get_azd_env_value(azd_var)
        if value:
            service_urls[export_var] = value
            
        # Also check for scope URI for MCP servers (for authentication)
        scope_azd_var = service_name_to_env_var(service_name.replace('uri', 'ScopeUri'))
        scope_export_var = f"{service_name.upper().replace('-', '_')}_SCOPE_URI"
        
        scope_value = get_azd_env_value(f"{service_name_to_env_var(service_name).replace('Uri', 'ScopeUri')}")
        if scope_value:
            service_urls[scope_export_var] = scope_value
    
    return service_urls


def main():
    """
    Main entry point for CLI usage.
    
    Outputs shell export commands that can be eval'd.
    """
    services = get_azd_services()
    
    if not services:
        print("No services found in azure.yaml", file=sys.stderr)
        sys.exit(1)
    
    print(f"# Auto-generated service URLs from azd environment", file=sys.stderr)
    print(f"# Found {len(services)} service(s)", file=sys.stderr)
    
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
    
    print()
    for export in exports:
        print(export)


if __name__ == "__main__":
    main()
