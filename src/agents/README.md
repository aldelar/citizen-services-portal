# Agent Deployment Scripts

This directory contains:
- **Agent definitions** (in subdirectories like `ladbs/`)
- **Generic deployment scripts** (Python files at this level)

The deployment scripts work with any agent definition in a subdirectory.

## Scripts

### `deploy.py` - Master Deployment Script

Orchestrates the complete deployment of an agent, including tools and agent definition.

**Usage:**
```bash
cd src/agents
python deploy.py <agent_name>
```

**Example:**
```bash
python deploy.py ladbs
```

**What it does:**
1. Deploys the agent's tools (via `deploy_tools.py`)
2. Deploys the agent definition (via `deploy_agent.py`)
3. Publishes the agent as a managed deployment

---

### `deploy_tools.py` - Tool Deployment Script

Validates all tools defined in the agent's `agent.yaml` configuration.

**Usage:**
```bash
cd src/agents
python deploy_tools.py <agent_name>
```

**Example:**
```bash
python deploy_tools.py ladbs
```

**What it does:**
1. Reads tools from the agent's `agent.yaml` definition
2. Validates each tool configuration
3. Performs environment variable substitution (e.g., `${MCP_LADBS_URL}`)
4. Registers tools with Azure AI Foundry (when supported)

---

### `deploy_agent.py` - Agent Definition Deployment Script

Deploys the agent definition to Azure AI Foundry and publishes it as a managed deployment.

**Usage:**
```bash
cd src/agents
python deploy_agent.py <agent_name>
```

**Example:**
```bash
python deploy_agent.py ladbs
```

**What it does:**
1. Loads the agent's `agent.yaml` configuration
2. Loads the agent's `system-prompt.md` instructions
3. Creates/updates the agent definition in Azure AI Foundry
4. Publishes the agent as a managed deployment (production-ready)

---

## Required Environment Variables

These scripts require the following environment variables to be set (typically via `azd env`):

- `foundryProjectEndpoint` or `AZURE_AI_PROJECT_ENDPOINT` - Azure AI Foundry project endpoint
- `AZURE_SUBSCRIPTION_ID` - Azure subscription ID
- `resourceGroupName` - Resource group name
- `foundryName` - Azure AI Foundry account name
- `foundryProjectName` - Azure AI Foundry project name

**Example:**
```bash
# Load environment from azd
cd /home/aldelar/Code/citizen-services-portal
azd env get-values > .env
source .env

# Or run with azd env directly
azd env get-values | python src/agents/scripts/deploy.py ladbs
```

---

## Agent Directory Structure

Each agent should follow this structure:

```
src/agents/
  <agent_name>/
    agent.yaml           # Agent configuration with tools defined inline
    system-prompt.md     # Agent instructions
```

**Example for `ladbs` agent:**
```
src/agents/
  ladbs/
    agent.yaml          # Contains agent definition and tools
    system-prompt.md    # System instructions
```

**Note:** Tools are defined directly in `agent.yaml` under `definition.tools`, not in a separate folder.

---

## Dependencies

These scripts use the following Python packages (install via `uv` or `pip`):

- `azure-identity`
- `azure-ai-projects`
- `pyyaml`
- `requests`

**Install with uv:**
```bash
cd src/agents
uv run deploy.py ladbs
```

This will automatically install dependencies and run the script.

---

## Adding a New Agent

To add a new agent:

1. Create a new directory under `src/agents/`:
   ```bash
   mkdir src/agents/my-new-agent
   ```

2. Create the required files:
   ```bash
   touch src/agents/my-new-agent/agent.yaml
   touch src/agents/my-new-agent/system-prompt.md
   ```

3. Configure your agent in `agent.yaml`:
   ```yaml
   name: my-new-agent
   description: My new AI agent
   definition:
     kind: prompt
     model: gpt-4o
     temperature: 0.7
     tools:
       - type: mcp
         server_label: my_mcp_server
         server_url: ${MY_MCP_SERVER_URL}
         project_connection_id: my-mcp-connection
   ```

4. Write your agent's instructions in `system-prompt.md`

5. Deploy your agent:
   ```bash
   cd src/agents
   python deploy.py my-new-agent
   ```

---

## Troubleshooting

### "Agent directory not found"
- Make sure the agent directory exists under `src/agents/`
- Check the agent name spelling

### "Environment variable not set"
- Run `azd env get-values` to check available variables
- Make sure you're running from the correct working directory
- Source the environment: `source <(azd env get-values)`

### "Failed to connect to Azure AI Foundry"
- Run `az login` to authenticate
- Verify the `foundryProjectEndpoint` is correct
- Check your Azure subscription has access to the AI Foundry project
