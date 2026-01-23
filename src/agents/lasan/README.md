# LASAN Agent

AI Agent for Los Angeles Bureau of Sanitation (LASAN) services, deployed to Azure AI Foundry.

## Overview

This agent provides conversational access to LASAN waste management and sanitation services through natural language. Citizens can ask questions and get help with trash collection, recycling, bulky pickups, and other sanitation services.

## Features

- **Natural Language Interface**: Citizens can ask questions in plain English
- **Collection Schedule Lookup**: Find trash, recycling, and green waste pickup days
- **Bulky Item Pickup**: Schedule and track furniture/appliance pickup requests
- **Illegal Dumping Reports**: Report and track illegal dumping incidents
- **Bin Management**: Request replacement or new waste bins
- **Recycling Guidance**: Get information about what can be recycled
- **Missed Collection Reports**: Report and track missed pickups

## Agent Configuration

- **Model**: GPT-4.1
- **Temperature**: 0.7 (balanced between creativity and consistency)
- **MCP Server**: Connects to `mcp-lasan` service
- **System Prompt**: `system-prompt.md`

## Files

| File | Description |
|------|-------------|
| `agent.yaml` | Agent configuration in Azure AI Foundry format |
| `system-prompt.md` | System instructions and guidelines |
| `README.md` | This documentation file |

## Example Conversations

### Collection Schedule
```
User: When is my trash picked up?
Agent: I'd be happy to help you find your collection schedule. Could you please 
       provide your complete address?
User: 123 Main Street, Los Angeles, CA 90012
Agent: [Calls get_collection_schedule tool]
       Your trash is collected on Tuesdays, recycling on Fridays, and green 
       waste on Wednesdays. Your next pickup is Tuesday, January 28, 2026.
```

### Bulky Item Pickup
```
User: I need to get rid of an old couch and mattress
Agent: I can help you schedule a bulky item pickup! Could you provide:
       1. Your address
       2. Contact phone number
       3. Preferred pickup date
User: [Provides information]
Agent: [Calls schedule_bulky_pickup tool]
       Your bulky pickup has been scheduled! Request ID: BULKY-AB123
       Date: February 15, 2026
       Please place items at curb by 6 AM on pickup day.
```

### Recycling Information
```
User: Can I recycle pizza boxes?
Agent: [Calls get_recycling_info tool]
       Pizza boxes can be recycled in your blue bin IF they're clean and free of 
       grease. If they have food residue or grease stains, they should go in your 
       green waste bin or trash instead.
```

## Deployment

This agent is deployed via the `azd` deployment pipeline defined in the root `azure.yaml`.

### Deploy Agent

From repository root:

```bash
# Deploy all agents (including LASAN)
azd deploy

# The postdeploy hook will automatically deploy the agent
```

### Manual Deployment

```bash
cd src/agents
uv run deploy.py lasan
```

### Required Environment Variables

The deployment script requires:
- `foundryProjectEndpoint` - Azure AI Foundry project endpoint
- `AZURE_SUBSCRIPTION_ID` - Azure subscription ID
- `resourceGroupName` - Resource group name
- `foundryName` - Foundry hub name
- `foundryProjectName` - Foundry project name
- `SERVICE_MCP_LASAN_URI` - LASAN MCP server URI

These are automatically set by `azd` during deployment.

## Testing

### Test in Azure AI Foundry Portal

1. Navigate to your Azure AI Foundry project
2. Go to "Build" → "Agents"
3. Find "lasan-assistant"
4. Click "Test" to open the agent playground
5. Try sample queries:
   - "When is my trash pickup?"
   - "I need to schedule a bulky item pickup"
   - "What can I recycle?"
   - "How do I report illegal dumping?"

### Test via API

```python
from azure.ai.inference import ChatCompletionsClient
from azure.identity import DefaultAzureCredential

client = ChatCompletionsClient(
    endpoint="<your-foundry-endpoint>",
    credential=DefaultAzureCredential()
)

response = client.complete(
    messages=[
        {"role": "user", "content": "When is trash collected on Main Street?"}
    ],
    model="lasan-assistant"
)

print(response.choices[0].message.content)
```

## Monitoring

Monitor agent performance in Azure AI Foundry:
- View conversation traces
- Check MCP tool call success rates
- Review response times
- Analyze user satisfaction metrics

## Troubleshooting

### Agent Not Finding Tools

Ensure the MCP server is deployed and `SERVICE_MCP_LASAN_URI` environment variable is set correctly during deployment.

### Connection Errors

Verify that:
1. MCP server is running: `azd env get-value mcpLasanUri`
2. Network connectivity between agent and MCP server
3. Authentication is properly configured (or disabled)

### Incorrect Responses

Review:
1. System prompt in `system-prompt.md`
2. Tool descriptions in MCP server
3. Model temperature settings

## Related Documentation

- [MCP Server Documentation](../../mcp-servers/lasan/README.md)
- [Azure AI Foundry Docs](https://learn.microsoft.com/azure/ai-studio/)
- [Agent Deployment Guide](../README.md)
