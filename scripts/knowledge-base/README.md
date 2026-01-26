# Knowledge Base Ingestion Scripts

This folder contains scripts to set up and run the knowledge base ingestion pipeline for the Citizen Services Portal.

## Prerequisites

Before running these scripts:

1. **Infrastructure must be deployed** via `azd up` from the project root
2. **Azure CLI** must be installed and logged in (`az login`)
3. **Python environment** with required packages (see `pyproject.toml`)

## Scripts

### 1. `setup-kb-permissions.sh`

**Run this first!** Sets up the required RBAC permissions for the ingestion pipeline.

```bash
chmod +x setup-kb-permissions.sh
./setup-kb-permissions.sh
```

This script:
- Associates the user-assigned managed identity with the Search service
- Assigns `Storage Blob Data Reader` role on storage account
- Assigns `Cognitive Services User` role on AI Foundry (North Central US)
- Assigns `Cognitive Services User` role on Content Understanding (West US)

**Note:** Content Understanding is deployed in **West US** (`aldelar-csp-cu-westus`) because the Content Understanding API is only available in specific regions (westus, swedencentral, australiaeast). All other resources remain in North Central US.

### 2. `upload-kb-documents.py`

Uploads documents from `/assets/{agency}/` to blob storage containers.

```bash
source .venv/bin/activate  # or your Python environment
python upload-kb-documents.py
```

### 3. `setup-knowledge-base.py`

Creates the Azure AI Search resources:
- 3 indexes (ladbs-kb, ladwp-kb, lasan-kb)
- 3 skillsets (ladbs-kb-skillset, ladwp-kb-skillset, lasan-kb-skillset)
- 3 data sources (using managed identity)
- 3 indexers

```bash
python setup-knowledge-base.py
```

### 4. `run-kb-indexers.sh`

Runs all three indexers to process documents and populate the indexes.

```bash
chmod +x run-kb-indexers.sh
./run-kb-indexers.sh
```

## Complete Setup Workflow

```bash
cd scripts/knowledge-base

# 1. Setup permissions (one-time, or after infra redeployment)
./setup-kb-permissions.sh

# 2. Upload documents to blob storage
python upload-kb-documents.py

# 3. Create Search resources (indexes, skillsets, data sources, indexers)
python setup-knowledge-base.py

# 4. Run indexers to populate indexes
./run-kb-indexers.sh

# 5. Run tests to verify everything works
./run-all-tests.sh
```

## Test Scripts

After setup, you can run these test scripts to verify the knowledge base is working:

### `run-all-tests.sh`
Runs all tests in sequence:
```bash
./run-all-tests.sh
```

### Individual Tests

| Script | Purpose |
|--------|---------|
| `test-document-counts.py` | Verifies each index has the expected number of document chunks |
| `test-regular-search.py` | Tests keyword/full-text search functionality |
| `test-semantic-search.py` | Tests semantic/natural language search functionality |

```bash
# Run individual tests
python test-document-counts.py
python test-regular-search.py
python test-semantic-search.py
```

## Troubleshooting

### "Ensure managed identity is enabled for your service"

This error occurs when:
- The Search service doesn't have the user-assigned identity associated
- Run `setup-kb-permissions.sh` to fix

### "Credentials provided in the connection string are invalid"

This error occurs when:
- RBAC roles haven't propagated yet (wait 5-10 minutes)
- Storage Blob Data Reader role is missing on the storage account
- Run `setup-kb-permissions.sh` and wait a few minutes

### Skillset creation fails with API version error

The ContentUnderstandingSkill requires API version `2025-11-01-Preview`. The scripts already use this version.

### Index projection path conflict

If you see errors about paths being used in multiple projections, ensure you're using one skillset per agency (not a shared skillset).

## Security Configuration

The pipeline uses **managed identity authentication** throughout:

| Component | Identity Used | Target Resource | Region |
|-----------|---------------|-----------------|--------|
| Data Source | Search service system-assigned identity | Storage Account (via ResourceId) | North Central US |
| Skillset | Search service system-assigned identity | AI Foundry | North Central US |
| Skillset | Search service system-assigned identity | Content Understanding | **West US** |
| Indexer | Search service system-assigned identity | Inherits from data source | N/A |

**Region Note:** Content Understanding (`aldelar-csp-cu-westus`) is deployed in West US because the Content Understanding API (2025-05-01-preview) is only available in: West US, Sweden Central, and Australia East.

The storage account has shared key access disabled (`allowSharedKeyAccess: false`), forcing all access through managed identity.
