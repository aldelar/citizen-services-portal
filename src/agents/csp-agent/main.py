# Copyright (c) Microsoft. All rights reserved.

import os
from pathlib import Path

from agent_framework import HostedMCPTool
from agent_framework.azure import AzureOpenAIChatClient
from azure.ai.agentserver.agentframework import from_agent_framework  # pyright: ignore[reportUnknownVariableType]
from azure.identity import DefaultAzureCredential


def load_system_prompt() -> str:
    """Load the system prompt from the prompts directory."""
    prompt_path = Path(__file__).parent / "prompts" / "system_prompt.md"
    if prompt_path.exists():
        return prompt_path.read_text()
    
    # Fallback to a basic prompt if file not found
    return (
        "You are the Citizen Services Portal Agent (CSP Agent), an AI assistant for "
        "City of Los Angeles government services. You help citizens navigate services across "
        "LADBS (Building & Safety), LADWP (Water & Power), LASAN (Sanitation), and other departments."
    )


def create_agent():
    """Create the CSP Agent with connections to all MCP servers."""
    
    # Get MCP server URLs from environment variables
    mcp_ladbs_url = os.environ.get("MCP_LADBS_URL")
    mcp_ladwp_url = os.environ.get("MCP_LADWP_URL")
    mcp_lasan_url = os.environ.get("MCP_LASAN_URL")
    mcp_reporting_url = os.environ.get("MCP_REPORTING_URL")
    
    # Build list of available MCP tools
    tools = []
    
    if mcp_ladbs_url:
        tools.append(HostedMCPTool(
            name="LADBS",
            url=mcp_ladbs_url,
        ))
    
    if mcp_ladwp_url:
        tools.append(HostedMCPTool(
            name="LADWP",
            url=mcp_ladwp_url,
        ))
    
    if mcp_lasan_url:
        tools.append(HostedMCPTool(
            name="LASAN",
            url=mcp_lasan_url,
        ))
    
    if mcp_reporting_url:
        tools.append(HostedMCPTool(
            name="Reporting",
            url=mcp_reporting_url,
        ))
    
    # Get Azure OpenAI configuration
    model_url = os.environ.get("AZURE_OPENAI_ENDPOINT")
    
    # Load system prompt
    instructions = load_system_prompt()
    
    # Create the agent using Azure OpenAI Chat Client
    agent = AzureOpenAIChatClient(credential=DefaultAzureCredential()).create_agent(
        name="csp-agent",
        instructions=instructions,
        model_url=model_url,
        tools=tools,
    )
    
    return agent


def main():
    """Run the CSP Agent as a hosted agent."""
    from_agent_framework(lambda _: create_agent()).run()


if __name__ == "__main__":
    main()
