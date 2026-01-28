# CSP Agent as Azure Container App (Draft Spec)

This document summarizes the required changes to move the CSP Agent from Foundry Hosted Agent to a **classic agent container image** deployed as **Azure Container App (ACA)**. It also proposes conversation-state approaches for the Responses API. This is a **draft for discussion**; implementation will follow once an approach is agreed.

---

## 1. Goals

- Replace Foundry Hosted Agent with a **containerized CSP Agent** running in ACA.
- Keep a **stable Responses API** endpoint for the web app.
- Provide **reliable multi-turn conversation** behavior.
- Preserve MCP tool integration and existing web app UI/UX.

## 2. Non‑Goals

- No UI redesign.
- No change to MCP server APIs.
- No change to knowledge base ingestion.

---

## 3. Architecture Change (High Level)

### Current
Web App → Foundry Application Endpoint → Hosted Agent → MCP Servers → Cosmos

### Proposed
Web App → **ACA CSP Agent** (Responses API) → MCP Servers → Cosmos

The ACA agent becomes the authoritative implementation of the Responses API and conversation behavior.

---

## 4. Required Changes (Summary)

### 4.1 Agent Packaging & Runtime
- **Create/Update agent Dockerfile** for CSP Agent to run as a long‑lived service.
- Ensure **Responses API** is exposed from the agent container at a stable `/responses` endpoint.
- Add ACA‑specific environment config (MCP URLs, model endpoint, auth, Cosmos, telemetry).

### 4.2 Azure Infrastructure
- Add **Azure Container App** for CSP Agent in infra templates.
- Add **Container App Environment** if not already present.
- Configure **Managed Identity** for ACA to access Azure OpenAI, Cosmos DB, etc.
- Update **RBAC assignments** for the ACA identity.
- Add **ingress** (internal or external) and set app URL output.

### 4.3 Web App Configuration
- Update `CSP_AGENT_URL` to ACA endpoint (no Foundry application path).
- Keep Responses API `api-version` unchanged (2025‑11‑15‑preview).
- Remove reliance on Foundry application endpoint constraints.

### 4.4 Conversation State Strategy
- Decide on conversation persistence approach (see options below).
- Update web app + agent to implement chosen approach consistently.

### 4.5 CI/CD & Deployment
- Ensure `azd deploy` builds and deploys ACA agent image.
- Add container build/publish steps as needed.

---

## 5. Conversation State Plan (Responses API)

### **App‑Managed Message History (Cosmos “messages”)**
**Description:** Web app stores messages in `messages` container and sends full history in each request. Agent remains stateless.

**Pros**
- Simple agent runtime; no thread storage.
- Works consistently across ACA and local.

**Cons**
- Larger payloads; must manage truncation.
- Requires careful history formatting.

**Changes**
- Keep app‑side message store and pass history.
- Decommission `threads` container and thread repository.

---

No truncation or summarization yet.

---

## 6. Data Model Impact

- Use `messages` container for conversation history.
- **Retire `threads`** container and remove the agent thread repository.

---

## 7. Decisions

1. ACA agent ingress is **external** so it can be showcased in Foundry later.
2. **No rate‑limit or retry** at agent/web app level (defer to APIM later).

---

## 8. Acceptance Criteria

- Local stack: MCP + ACA agent + web app work with multi‑turn memory.
- Azure: same behavior via ACA endpoint.
- Integration tests updated to match chosen approach.
- No Foundry Hosted Agent dependency remains.
- ACA agent endpoint is externally accessible.
- No APIM changes included in this work.

---

## 9. Next Step

Proceed to full implementation for ACA agent + app‑managed messages once this draft is approved.

---

## 10. Existing Azure Services Context (from specs/0-azure-services.md)

The following services already exist and should be reused:

- Container Apps Environment: `aldelar-csp-cae`
- Container Registry: `aldelarcspcr` (aldelarcspcr.azurecr.io)
- AI Foundry: `aldelar-csp-foundry` (models: `gpt-4.1`, `gpt-4.1-mini`, embeddings)
- Cosmos DB: `aldelar-csp-cosmos` (serverless)
- Application Insights: `aldelar-csp-insights`
- API Management: `aldelar-csp-apim` (**do not configure in this change**)

The ACA CSP Agent should be added alongside existing MCP Container Apps:

- `aldelar-csp-mcp-ladbs`
- `aldelar-csp-mcp-ladwp`
- `aldelar-csp-mcp-lasan`
- `aldelar-csp-mcp-reporting`
