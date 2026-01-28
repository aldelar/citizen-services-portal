# Unified Local ↔ Azure Hosted Agent API Contract

## 1. Objective
Establish a single, production‑aligned API contract for the CSP Agent across:
- Local development
- Automated tests
- Microsoft Foundry Hosted Agent deployment

The contract standardizes endpoint shape, authentication, request/response payloads, and thread (conversation) persistence semantics. It also defines an infra/RBAC change log and rollback plan to safely trial the hosted approach.

## 2. Scope
In scope:
- Responses API request/response shape
- Authentication requirements
- Conversation/thread ID usage and persistence
- Endpoint selection (deployment vs version‑pinned)
- Required environment variables
- RBAC requirements and rollback logging

Out of scope:
- UI changes
- Prompt engineering changes
- MCP server behavior changes (except access/auth configuration)

## 3. Terminology
- **Hosted Agent**: CSP Agent deployed to Microsoft Foundry using Agent Framework.
- **Responses API**: Foundry data‑plane API used by hosted agents for chat/response interactions.
- **Conversation ID**: Identifier returned by Responses API used as the stable key for thread persistence.
- **Thread persistence**: Agent’s conversation state saved and loaded by a thread repository (Cosmos DB).
- **Deployment endpoint**: Stable endpoint that routes to the active agent deployment rather than a version‑pinned path.

## 4. Current State (Summary)
- Hosted agent is defined with `protocols: responses` and runs via Agent Framework.
- Web app uses `/responses` but does not include `api-version` or auth headers.
- Test scripts use the Threads/Runs API which diverges from the Responses contract.
- Thread persistence exists via Cosmos DB but is gated by env vars.

## 5. Target Contract

### 5.1 Endpoint Format
- Use a stable **deployment endpoint** (preferred), not a version‑pinned agent URL.
- Example pattern (to be verified in deployment output):
  - `/api/projects/{projectName}/applications/{applicationName}/agentdeployments/{deploymentName}/responses?api-version={version}`
  - Alternative stable path if used by your Foundry project: `/api/projects/{projectName}/agents/{agentName}/deployments/{deploymentName}/responses?api-version={version}`

> Note: The exact deployment endpoint must be recorded from deployment outputs.

### 5.2 API Version
- Standardize on one Responses API version across all environments.
- Default target: `2025-11-15-preview` (matching current known‑working calls).

### 5.3 Authentication
- All requests to the hosted agent must include AAD bearer token:
  - Scope: `https://cognitiveservices.azure.com/.default`
- Requests without valid auth must be treated as non‑compliant.

### 5.4 Request Payload
- Request body:
  - `input`: either a string or array of `{ role, content }` messages.
  - `stream`: boolean
  - `conversation`: optional `{ id: "<conversation_id>" }`

### 5.5 Response Payload
- Non‑streaming:
  - Parse OpenAI Responses format: `output[].content[].text`
- Streaming:
  - Parse SSE with `type: response.output_text.delta` and `delta` text.
- Conversation ID:
  - Extract from `conversation.id` (if present in response events).

### 5.6 Conversation / Thread Mapping
- The **conversation ID** returned by the Responses API is the primary key for thread persistence.
- The client must store and replay this ID for all subsequent calls within a “project.”

## 6. Thread Persistence (Cosmos DB)
- Persistence is optional but required for parity with hosted behavior.
- The agent uses a thread repository keyed by `conversation_id` and stores serialized thread state.

### Required Environment Variables
- `AGENT_COSMOS_ENDPOINT`
- `AGENT_COSMOS_DATABASE`
- `AGENT_COSMOS_THREADS_CONTAINER`

### Expected Behavior
- When `conversation.id` is sent, the hosted agent loads existing thread state before responding.
- After responding, the updated serialized thread is saved under the same ID.

## 7. MCP Tool Access
- Hosted agent must reach MCP servers over HTTP(S).
- If MCP servers require auth, the hosted agent must be configured with credentials/headers.
- Any MCP auth updates must be documented and revertible.

## 8. Environment Configuration Matrix

### Local Development
- Endpoint: local agent or local proxy
- Auth: none (if local), but must match shape of hosted requests
- API version: same as hosted
- Conversation: must store and reuse `conversation.id`

### Hosted (Foundry)
- Endpoint: deployment endpoint
- Auth: AAD bearer token
- API version: same as local
- Conversation: must store and reuse `conversation.id`

## 9. Test Alignment Requirements
- Replace Threads/Runs tests with Responses API calls.
- Use the same endpoint, auth, and `api-version` as production.
- Tests must validate:
  1) First response returns a conversation ID
  2) Second request reuses the conversation ID
  3) Agent response includes prior context

## 10. Unit Tests + Integration Tests (TDD Definition)

### 10.1 Unit Tests (Local, isolated)
Unit tests validate the API contract logic **without** calling Azure or MCP servers. They should use mocks/fakes for HTTP calls and token acquisition.

**Must cover:**
- Request construction for Responses API (payload shape, `api-version`, headers).
- Conversation ID capture and reuse logic.
- Response parsing (non‑stream and streaming delta extraction).
- Error handling for non‑200 responses and malformed payloads.

**Pass criteria:**
- No external network calls occur.
- All contract‑parsing paths produce deterministic results.

### 10.2 Integration Tests (End‑to‑end with Hosted Agent)
Integration tests validate the **real** Hosted Agent contract over the network using AAD auth.

**Must cover:**
- Call hosted agent `/responses` with `api-version` and AAD token.
- Capture returned `conversation.id`.
- Send a second request with `conversation.id` and verify context is preserved.
- Optional: streaming response handling (SSE) if streaming is enabled.

**Pass criteria:**
- Requests succeed with authenticated calls.
- Conversation persistence works across requests.
- The response format matches the contract used by unit tests.

## 11. Infra/RBAC Changes

### 11.1 Required Role Assignments (Minimal)
- Hosted agent identity must be granted:
  - Access to AOAI/Foundry model deployment (data plane).
  - Access to Cosmos DB data plane (database or account scope).

### 11.2 Change Log Requirements
For each RBAC change, record:
- Principal ID
- Role name / definition ID
- Scope (resource ID)
- Assignment ID
- Timestamp
- Operator

### 11.3 Rollback Plan
- Remove role assignments by ID.
- Restore previous environment variables for agent configuration.
- Revert any deployment endpoint or route changes.
- Disable Cosmos persistence by removing `AGENT_COSMOS_*` env vars if needed.

## 12. Acceptance Criteria
- All local tests use Responses API and pass with a hosted‑compatible payload.
- Hosted agent responds using the same request/response contract as local tests.
- Conversation ID persists across requests and is used for thread restoration.
- RBAC changes are fully documented with rollback steps.

## 13. Implementation Checklist (Non‑Code)
1) Confirm deployment endpoint format and publish in project docs.
2) Standardize API version across local and hosted.
3) Add AAD token usage to all hosted calls.
4) Update tests to use Responses API.
5) Configure thread persistence env vars and validate Cosmos storage.
6) Record RBAC changes and verify rollback.

## 14. Open Questions
- Exact deployment endpoint path used by your Foundry project (to be confirmed).
- Whether MCP servers will require auth headers in hosted mode.
- Whether stream or non‑stream mode will be the default for the web app.
