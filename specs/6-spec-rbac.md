# RBAC Specification

This document defines all Role-Based Access Control (RBAC) configurations for the Citizen Services Portal solution.

## Overview

The solution uses Azure RBAC for managing access between services. All role assignments are defined in Bicep templates and deployed via `azd provision`. This ensures permissions are:

- **Codified** - All assignments are in source control
- **Reproducible** - Permissions are recreated on each deployment
- **Auditable** - Easy to review who/what has access to which resources

## Principals

### User Principal
- **Name**: Developer/Admin user
- **Type**: User
- **Source**: `principalId` parameter (from `azd` environment)

### Managed Identity
- **Name**: `aldelar-csp-identity`
- **Type**: ServicePrincipal (User-Assigned Managed Identity)
- **Purpose**: Service-to-service authentication for Container Apps and agents
- **Bicep**: `infra/core/security/managed-identity.bicep`

### AI Search Service Identity
- **Name**: `aldelar-csp-search`
- **Type**: ServicePrincipal (System-Assigned Managed Identity)
- **Purpose**: AI Search accessing storage, cognitive services for indexing/enrichment
- **Bicep**: `infra/core/ai/ai-search.bicep`

### Foundry Project Identity
- **Name**: `aldelar-csp-foundry-project`
- **Type**: ServicePrincipal (Project Managed Identity)
- **Purpose**: AI agents accessing MCP servers
- **Bicep**: `infra/core/ai/foundry-project.bicep`

---

## Role Assignments by Resource

### Azure AI Foundry (`aldelar-csp-foundry`)

| Principal | Role | Role ID | Purpose | Bicep Module |
|-----------|------|---------|---------|--------------|
| User | Cognitive Services User | `a97b65f3-24c7-4388-baec-2e87135dc908` | Full data plane access including agents | `foundry-rbac.bicep` |
| User | Azure AI Developer | `64702f94-c441-49e6-a78b-ef80e0188fee` | Access to view and work with AI resources | `foundry-rbac.bicep` |
| AI Search | Cognitive Services User | `a97b65f3-24c7-4388-baec-2e87135dc908` | AI enrichment during indexing | `foundry-rbac.bicep` (foundrySearchRbac) |
| AI Search | Azure AI Developer | `64702f94-c441-49e6-a78b-ef80e0188fee` | Access to AI resources for enrichment | `foundry-rbac.bicep` (foundrySearchRbac) |

**Bicep File**: `infra/core/security/foundry-rbac.bicep`

---

### Azure Key Vault (`aldelar-csp-kv`)

| Principal | Role | Role ID | Purpose | Bicep Module |
|-----------|------|---------|---------|--------------|
| User | Key Vault Secrets Officer | `b86a8fe4-44ce-4948-aee5-eccb2c155cd7` | Read/write/delete secrets | `key-vault.bicep` |

**Bicep File**: `infra/core/security/key-vault.bicep`

---

### Azure Storage Account (`aldelarcspstorage`)

| Principal | Role | Role ID | Purpose | Bicep Module |
|-----------|------|---------|---------|--------------|
| User | Storage Blob Data Contributor | `ba92f5b4-2d11-453d-a403-e96b0029c9fe` | Read/write/delete blob data | `storage-rbac.bicep` |
| AI Search | Storage Blob Data Reader | `2a2b9908-6ea1-4ae2-8e65-a410df84e7d1` | Read blobs for indexing | `storage-rbac.bicep` |
| Managed Identity | Storage Blob Data Reader | `2a2b9908-6ea1-4ae2-8e65-a410df84e7d1` | Read blobs for agents/services | `storage-rbac.bicep` |

**Bicep File**: `infra/core/security/storage-rbac.bicep`

---

### Azure Content Understanding (`aldelar-csp-cu-westus`)

| Principal | Role | Role ID | Purpose | Bicep Module |
|-----------|------|---------|---------|--------------|
| User | Cognitive Services Contributor | `25fbc0a9-bd7c-42a3-aa1a-3b75d497ee68` | Management + data plane access | `content-understanding-rbac.bicep` |
| AI Search | Cognitive Services User | `a97b65f3-24c7-4388-baec-2e87135dc908` | Document analysis for indexing | `content-understanding-rbac.bicep` |
| Managed Identity | Cognitive Services User | `a97b65f3-24c7-4388-baec-2e87135dc908` | Document analysis for agents | `content-understanding-rbac.bicep` |

**Bicep File**: `infra/core/security/content-understanding-rbac.bicep`

---

### MCP Server Container Apps

Each MCP server (LADBS, LADWP, LASAN, Reporting) is hosted on Azure Container Apps and requires RBAC for the Foundry Project identity to invoke tools.

| Resource | Principal | Role | Role ID | Purpose |
|----------|-----------|------|---------|---------|
| `mcp-ladbs` | Foundry Project | Reader | `acdd72a7-3385-48ef-bd42-f606fba81ae7` | Agent discovers and invokes MCP server |
| `mcp-ladwp` | Foundry Project | Reader | `acdd72a7-3385-48ef-bd42-f606fba81ae7` | Agent discovers and invokes MCP server |
| `mcp-lasan` | Foundry Project | Reader | `acdd72a7-3385-48ef-bd42-f606fba81ae7` | Agent discovers and invokes MCP server |
| `mcp-reporting` | Foundry Project | Reader | `acdd72a7-3385-48ef-bd42-f606fba81ae7` | Agent discovers and invokes MCP server |

**Bicep File**: `infra/core/security/mcp-server-rbac.bicep`

---

## Azure Built-in Role Reference

| Role Name | Role ID | Description |
|-----------|---------|-------------|
| Cognitive Services User | `a97b65f3-24c7-4388-baec-2e87135dc908` | Read and list Cognitive Services keys, perform inference |
| Cognitive Services Contributor | `25fbc0a9-bd7c-42a3-aa1a-3b75d497ee68` | Full access to manage Cognitive Services resources |
| Azure AI Developer | `64702f94-c441-49e6-a78b-ef80e0188fee` | Access to view and work with AI resources |
| Key Vault Secrets Officer | `b86a8fe4-44ce-4948-aee5-eccb2c155cd7` | Read, write, delete Key Vault secrets |
| Storage Blob Data Contributor | `ba92f5b4-2d11-453d-a403-e96b0029c9fe` | Read, write, delete blob data |
| Storage Blob Data Reader | `2a2b9908-6ea1-4ae2-8e65-a410df84e7d1` | Read blob data |
| Reader | `acdd72a7-3385-48ef-bd42-f606fba81ae7` | View resources, no modifications |

**Reference**: [Azure Built-in Roles](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles)

---

## RBAC Module Invocations in main.bicep

```bicep
// Foundry RBAC - User access
module foundryRbac './core/security/foundry-rbac.bicep' = if (principalId != '') {
  params: {
    foundryId: foundry.outputs.id
    principalId: principalId
    principalType: 'User'
  }
}

// Foundry RBAC - AI Search access
module foundrySearchRbac './core/security/foundry-rbac.bicep' = {
  params: {
    foundryId: foundry.outputs.id
    principalId: aiSearch.outputs.principalId
    principalType: 'ServicePrincipal'
  }
}

// Storage RBAC
module storageRbac './core/security/storage-rbac.bicep' = {
  params: {
    storageAccountName: storageAccount.outputs.name
    userPrincipalId: principalId
    searchPrincipalId: aiSearch.outputs.principalId
    identityPrincipalId: managedIdentity.outputs.principalId
  }
}

// Content Understanding RBAC
module contentUnderstandingRbac './core/security/content-understanding-rbac.bicep' = {
  params: {
    contentUnderstandingId: contentUnderstanding.outputs.id
    userPrincipalId: principalId
    searchPrincipalId: aiSearch.outputs.principalId
    identityPrincipalId: managedIdentity.outputs.principalId
  }
}

// MCP Server RBAC (per server)
module mcpLadbsRbac './core/security/mcp-server-rbac.bicep' = {
  params: {
    containerAppId: mcpLadbs.outputs.id
    principalIds: [foundryProject.outputs.principalId]
    principalType: 'ServicePrincipal'
  }
}
```

---

## Deployment

All RBAC assignments are deployed automatically with:

```bash
azd provision
```

The `principalId` parameter is automatically populated from the signed-in Azure CLI user.

---

## Troubleshooting

### Permission Denied Errors

1. **Verify role assignment exists**:
   ```bash
   az role assignment list --scope <resource-id> --output table
   ```

2. **Check principal ID**:
   ```bash
   # For managed identity
   az identity show -n aldelar-csp-identity -g csp --query principalId -o tsv
   
   # For AI Search
   az search service show -n aldelar-csp-search -g csp --query identity.principalId -o tsv
   ```

3. **Re-run provisioning** to ensure all RBAC is applied:
   ```bash
   azd provision
   ```

### Role Propagation Delay

Azure RBAC can take up to 5-10 minutes to propagate. If access is denied immediately after provisioning, wait and retry.
