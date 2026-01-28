Abandoned the idea of using Microsoft Foundry Declarative Agents:
- lack of support to publish via SDK (available via REST), and inability to programatically define tools.
- lack of platform stability with MCP tools (e.g. intermittent failures, lack of error outputs, etc.)

Abandoned the idea of using Hosted Agents with Agent Framework:
- lack of full support for Responses API contract (no support for conversations, no support for structured messages (as arrays, only flat strings)): https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/publish-agent?view=foundry#responses
- lack of support to deploy to production via SDK/CLI
- stability issues (inability to delete failed deployments, even after deleting froundry projects and Capability Hosts)
- lack of support for troubleshootin (failed container boot up lead to stuck startups insteaf of failures)
- impossible to have consistent local vs hosted agent experience to handle sending history (conversation ID supported on local, not when deployed)

Azure Container Apps (ACA) provide a stable, production-ready hosting environment with full control over the agent container, allowing us to ensure consistent behavior between local development and hosted deployment. This approach also allows us to fully implement the unified Responses API contract, including conversation persistence and structured message handling, which are critical for our application's functionality.

ACA is also a supported service in Azure Gov if we need to deploy based on data residency requirements of future Governement services enablement in the solution.