# RBAC Changes and Rollback Plan

## Purpose
This document tracks all RBAC (Role-Based Access Control) changes required for the unified local ↔ Azure Hosted Agent API contract implementation. It provides a complete audit trail and rollback procedures.

## Change Date
January 27, 2026

## Implementation Phase
ACA agent deployment with app-managed message history (threads retired)

---

## Required RBAC Changes

### 1. ACA Agent Managed Identity Access to Azure OpenAI/Foundry

**Purpose**: Allow the ACA agent's managed identity to invoke Azure OpenAI models deployed in Foundry.

**Role**: `Cognitive Services User`  
**Role Definition ID**: `a97b65f3-24c7-4388-baec-2e87135dc908`  
**Principal**: ACA agent user-assigned managed identity (`aldelar-csp-identity`)  
**Scope**: Foundry account resource ID

**Assignment Command**:
```bash
# Get managed identity principal ID
IDENTITY_PRINCIPAL_ID=$(az identity show \
  --name aldelar-csp-identity \
  --resource-group csp \
  --query principalId -o tsv)

# Get Foundry resource ID
FOUNDRY_ID=$(az cognitiveservices account show \
  --name aldelar-csp-foundry \
  --resource-group csp \
  --query id -o tsv)

# Assign role
az role assignment create \
  --assignee $IDENTITY_PRINCIPAL_ID \
  --role "Cognitive Services User" \
  --scope $FOUNDRY_ID
```

---

### 2. ACA Agent Managed Identity Access to Cosmos DB (messages only)

**Purpose**: Allow the ACA agent identity to access Cosmos DB if needed in the future.
Currently the web app owns message persistence; the agent remains stateless.

**Role**: `Cosmos DB Built-in Data Contributor`  
**Role Definition ID**: `00000000-0000-0000-0000-000000000002`  
**Principal**: ACA agent managed identity (`aldelar-csp-identity`)  
**Scope**: Cosmos DB account resource ID

**Assignment Command**:
```bash
COSMOS_ACCOUNT_NAME="aldelar-csp-cosmos"
COSMOS_RESOURCE_ID=$(az cosmosdb show \
  --name $COSMOS_ACCOUNT_NAME \
  --resource-group csp \
  --query id -o tsv)

az cosmosdb sql role assignment create \
  --account-name $COSMOS_ACCOUNT_NAME \
  --resource-group csp \
  --role-definition-id 00000000-0000-0000-0000-000000000002 \
  --principal-id $IDENTITY_PRINCIPAL_ID \
  --scope $COSMOS_RESOURCE_ID
```

---

### 3. Web App Identity Access to Cosmos DB (if using managed identity)

**Purpose**: Allow web app to read thread history for display (if not using connection string).

**Role**: `Cosmos DB Built-in Data Reader`  
**Role Definition ID**: `00000000-0000-0000-0000-000000000001`  
**Principal**: Web app managed identity  
**Scope**: Cosmos DB account

**Note**: Currently the web app uses connection string. This is optional for future enhancement.

---

## Rollback Procedures

### Rollback Step 1: Remove ACA Agent → Azure OpenAI Role Assignment

```bash
az role assignment delete --assignee $IDENTITY_PRINCIPAL_ID \
  --role "Cognitive Services User" \
  --scope $FOUNDRY_ID
```

---

### Rollback Step 2: Remove ACA Agent → Cosmos DB Role Assignment (if created)

```bash
az cosmosdb sql role assignment delete \
  --account-name $COSMOS_ACCOUNT_NAME \
  --resource-group csp \
  --id <ASSIGNMENT_ID>
```

---

## Verification After Rollback

### 1. Verify ACA identity has no Cosmos access:
```bash
az cosmosdb sql role assignment list \
  --account-name aldelar-csp-cosmos \
  --resource-group csp \
  --query "[?principalId=='$IDENTITY_PRINCIPAL_ID']"
```

Should return: `[]`

### 2. Verify agent runs stateless:
- Confirm conversation history is managed by the web app

### 3. Verify local tests still pass:
```bash
cd src/web-app
pytest tests/test_agent_service_unit.py
```

---

## Change Log

| Date | Change | Principal | Role | Scope | Assignment ID | Operator |
|------|--------|-----------|------|-------|---------------|----------|
| 2026-01-27 | Initial RBAC setup documented | N/A | N/A | N/A | N/A | System |
| TBD | ACA Agent → Foundry access | `<IDENTITY_PRINCIPAL_ID>` | Cognitive Services User | Foundry account | `<ASSIGNMENT_ID>` | `<OPERATOR>` |
| TBD | ACA Agent → Cosmos access (optional) | `<IDENTITY_PRINCIPAL_ID>` | Cosmos DB Data Contributor | Cosmos account | `<ASSIGNMENT_ID>` | `<OPERATOR>` |

---

## Notes

1. **Minimal Permissions**: The roles assigned are the minimum required for functionality.
2. **Scope Isolation**: Assignments are scoped to specific resources, not subscription-wide.
3. **Audit Trail**: All assignment IDs are recorded for precise rollback.
4. **Testing**: Each RBAC change should be tested independently before proceeding.
5. **Monitoring**: After deployment, monitor agent logs for access denied errors.

---

## Related Documentation

- [specs/7-unified-local-azure-agent-api-contract.md](../specs/7-unified-local-azure-agent-api-contract.md)
- [infra/core/security/foundry-rbac.bicep](../infra/core/security/foundry-rbac.bicep)
- [infra/core/security/cosmos-rbac.bicep](../infra/core/security/cosmos-rbac.bicep)
