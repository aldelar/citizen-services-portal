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

Registering the ACA-deployed agent in Foundry as a **Registered Agent**:
- The agent is deployed and hosted on ACA, but registered in Microsoft Foundry as a "Registered Agent" (`csp-agent-ra`) pointing to the ACA endpoint.
- This enables **Foundry Tracing**: agent telemetry (spans, traces, token usage) flows from the ACA agent → Azure Monitor SDK → Application Insights → Foundry, and is visible in the Foundry portal under Tracing.
- The agent emits OpenTelemetry traces with `gen_ai.agent.id=csp-agent` via the Agent Framework's `AgentTelemetryLayer`, which Foundry uses to correlate traces to the registered agent.
- The AI Gateway (`aldelar-csp-ai-gateway`, BasicV2 APIM) is linked to the Foundry project to enable API traffic observability.
- AI Gateway linking to a Foundry project is a portal-only operation (not available via Bicep, ARM REST, or CLI as of March 2026).
- Registered Agent creation is also a portal-only operation — defined in Foundry UI by pointing to the ACA FQDN and selecting the Responses API protocol.