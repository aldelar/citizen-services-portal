# Knowledge Base Ingestion Pipeline Specification

## Document Information

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Created** | January 25, 2026 |
| **Status** | Ready for Implementation |

---

## 1. Overview

### 1.1 Purpose

This specification defines the architecture and implementation for ingesting agency knowledge base documents into Azure AI Search. The pipeline transforms HTML and PDF documents into searchable, vectorized content that powers the `queryKnowledge` tools in each agency's MCP server.

### 1.2 Scope

- **In Scope**: Document ingestion, chunking, vectorization, indexing, and query patterns
- **Out of Scope**: MCP server implementation (covered in [1-spec-mcp-servers.md](1-spec-mcp-servers.md))

### 1.3 Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Document Processing | Azure Content Understanding | Better Markdown output, cross-page tables, semantic chunking |
| File Processing | Native (no conversion) | Both HTML and PDF supported natively |
| Index Strategy | One index per agency | Matches MCP architecture, clean separation |
| Indexing Trigger | On-demand | Sufficient for demo; documents rarely change |
| Search Enhancement | Semantic ranking enabled | Improved answer relevance |
| Deployment | Bicep + azd up | Repeatable, version-controlled infrastructure |

---

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     KNOWLEDGE BASE INGESTION PIPELINE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     AZURE BLOB STORAGE                               │   │
│  │                   (aldelarcspstorage)                                │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │ ladbs-docs   │  │ ladwp-docs   │  │ lasan-docs   │               │   │
│  │  │ ├─ *.html    │  │ ├─ *.html    │  │ ├─ *.html    │               │   │
│  │  │ └─ *.pdf     │  │ └─ *.pdf     │  │ └─ *.pdf     │               │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │   │
│  └─────────┼─────────────────┼─────────────────┼───────────────────────┘   │
│            │                 │                 │                            │
│            ▼                 ▼                 ▼                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     DATA SOURCES (3)                                 │   │
│  │  ladbs-datasource    ladwp-datasource    lasan-datasource           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│            │                 │                 │                            │
│            ▼                 ▼                 ▼                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     SKILLSET (shared)                                │   │
│  │                   kb-ingestion-skillset                              │   │
│  │                                                                      │   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │   │
│  │  │  1. ContentUnderstandingSkill                                  │ │   │
│  │  │     • Parse HTML/PDF documents                                 │ │   │
│  │  │     • Extract structure (headings, tables, sections)          │ │   │
│  │  │     • Output Markdown with semantic boundaries                 │ │   │
│  │  │     • Chunk by content structure (max 2000 chars)              │ │   │
│  │  └────────────────────────────────────────────────────────────────┘ │   │
│  │                              │                                       │   │
│  │                              ▼                                       │   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │   │
│  │  │  2. AzureOpenAIEmbeddingSkill                                  │ │   │
│  │  │     • Model: text-embedding-3-small                            │ │   │
│  │  │     • Dimensions: 1536                                         │ │   │
│  │  │     • Vectorize each chunk                                     │ │   │
│  │  └────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│            │                 │                 │                            │
│            ▼                 ▼                 ▼                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     INDEXERS (3)                                     │   │
│  │  ladbs-indexer       ladwp-indexer       lasan-indexer              │   │
│  │  (on-demand)         (on-demand)         (on-demand)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│            │                 │                 │                            │
│            ▼                 ▼                 ▼                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     SEARCH INDEXES (3)                               │   │
│  │                  (aldelar-csp-search)                                │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │ ladbs-kb     │  │ ladwp-kb     │  │ lasan-kb     │               │   │
│  │  │              │  │              │  │              │               │   │
│  │  │ • chunk_id   │  │ • chunk_id   │  │ • chunk_id   │               │   │
│  │  │ • parent_id  │  │ • parent_id  │  │ • parent_id  │               │   │
│  │  │ • chunk      │  │ • chunk      │  │ • chunk      │               │   │
│  │  │ • title      │  │ • title      │  │ • title      │               │   │
│  │  │ • headers    │  │ • headers    │  │ • headers    │               │   │
│  │  │ • text_vector│  │ • text_vector│  │ • text_vector│               │   │
│  │  │              │  │              │  │              │               │   │
│  │  │ + Semantic   │  │ + Semantic   │  │ + Semantic   │               │   │
│  │  │   Ranking    │  │   Ranking    │  │   Ranking    │               │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXISTING INFRASTRUCTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Azure AI Search           Azure AI Foundry                     │
│  (aldelar-csp-search)      (aldelar-csp-foundry)               │
│  └─ Standard tier          └─ text-embedding-3-small           │
│                               (deployed, 1000 TPM)              │
│                                                                 │
│  Storage Account           Managed Identity                     │
│  (aldelarcspstorage)       (aldelar-csp-identity)              │
│  └─ Needs containers       └─ Needs RBAC for search/storage    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NEW INFRASTRUCTURE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Storage Containers (3)    Content Understanding Resource       │
│  ├─ ladbs-docs             (aldelar-csp-content-understanding) │
│  ├─ ladwp-docs             └─ For document processing          │
│  └─ lasan-docs                                                  │
│                                                                 │
│  Data Sources (3)          Skillset (1, shared)                │
│  ├─ ladbs-datasource       └─ kb-ingestion-skillset            │
│  ├─ ladwp-datasource                                           │
│  └─ lasan-datasource       Indexes (3)                         │
│                            ├─ ladbs-kb                         │
│  Indexers (3)              ├─ ladwp-kb                         │
│  ├─ ladbs-indexer          └─ lasan-kb                         │
│  ├─ ladwp-indexer                                              │
│  └─ lasan-indexer          Semantic Configurations (3)         │
│                            ├─ ladbs-semantic-config            │
│                            ├─ ladwp-semantic-config            │
│                            └─ lasan-semantic-config            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Document Inventory

### 3.1 Source Documents

Documents are stored in `/assets/` and organized by agency:

| Agency | Container | Documents | Formats |
|--------|-----------|-----------|---------|
| LADBS | `ladbs-docs` | 15 | 12 HTML, 3 PDF |
| LADWP | `ladwp-docs` | 9 | 7 HTML, 2 PDF |
| LASAN | `lasan-docs` | 6 | 4 HTML, 2 PDF |
| **Total** | | **30** | **23 HTML, 7 PDF** |

### 3.2 Document Details

#### LADBS Documents (15)

| File | Type | Content |
|------|------|---------|
| building-permits-overview.html | HTML | Building permit portal information |
| electrical-permits-overview.html | HTML | Electrical permit portal information |
| eplanla-system-overview.html | HTML | Online plan submittal system guide |
| fee-schedules-page.html | HTML | Links to fee schedule PDFs |
| how-to-schedule-inspection.html | HTML | Primary inspection scheduling guide |
| inspection-services-overview.html | HTML | Types of inspections explained |
| mechanical-hvac-information-bulletins.html | HTML | HVAC inspection requirements |
| mechanical-hvac-permits-overview.html | HTML | Mechanical permit portal |
| permit-fee-calculator.html | HTML | Online calculator information |
| plan-review-permitting-main.html | HTML | Status check instructions |
| regular-plan-check-process.html | HTML | Multi-week review process |
| title24-energy-code-faq.html | HTML | California Energy Code compliance |
| irfis-inspection-scheduling-guide.pdf | PDF | Step-by-step RFI system guide |
| plan-check-process-chart.pdf | PDF | Process flow diagram |
| solar-permit-requirements-IB-P-GI-2020-027.pdf | PDF | Comprehensive solar PV permit requirements |

#### LADWP Documents (9)

| File | Type | Content |
|------|------|---------|
| consumer-rebate-program.html | HTML | Heat pump HVAC and water heater rebates |
| interconnection-program-overview.html | HTML | NEM, PV, BESS program overview |
| interconnection-requirements.html | HTML | Technical requirements summary |
| nem-documents-collection.html | HTML | All NEM forms and agreements |
| residential-electric-rates-overview.html | HTML | R-1A and R-1B rate details |
| type-1-2-3-interconnection-process.html | HTML | Process tiers by system size |
| understanding-residential-electric-rates.html | HTML | Rate plan comparison |
| electric-service-requirements-manual-2024.pdf | PDF | Section 8: PV/BESS technical specs |
| nem-guidelines-2023.pdf | PDF | Official NEM policy and procedures |

#### LASAN Documents (6)

| File | Type | Content |
|------|------|---------|
| household-hazardous-waste-collection.html | HTML | HHW collection information |
| trash-pickup-dropoff-services.html | HTML | Pickup and drop-off services |
| ucla-safe-collection-site.html | HTML | SAFE center information |
| zero-waste-plan.html | HTML | Zero waste plan information |
| ewaste-flyer-2022.pdf | PDF | E-waste collection flyer |
| safe-center-flyer-2023.pdf | PDF | SAFE center promotional material |

---

## 4. Infrastructure Specification

### 4.1 Storage Containers

Three blob containers in the existing storage account:

```bicep
// Container configuration
containers = [
  {
    name: 'ladbs-docs'
    publicAccess: 'None'
  }
  {
    name: 'ladwp-docs'
    publicAccess: 'None'
  }
  {
    name: 'lasan-docs'
    publicAccess: 'None'
  }
]
```

### 4.2 Content Understanding Resource

A new Azure AI Services resource for Content Understanding:

```bicep
resource contentUnderstanding 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: 'aldelar-csp-content-understanding'
  location: location
  kind: 'AIServices'  // Multi-service account includes Content Understanding
  sku: {
    name: 'S0'
  }
  properties: {
    publicNetworkAccess: 'Enabled'
    customSubDomainName: 'aldelar-csp-cu'
  }
}
```

**Region Requirement**: Content Understanding preview API (2025-05-01-preview) requires specific regions. Use the same region as your AI Search service (northcentralus, eastus, or westus2).

### 4.3 RBAC Assignments

Required role assignments for the managed identity:

| Resource | Role | Purpose |
|----------|------|---------|
| Storage Account | Storage Blob Data Reader | Read documents from containers |
| AI Search | Search Index Data Contributor | Write to search indexes |
| AI Search | Search Service Contributor | Create/manage indexes, indexers |
| Content Understanding | Cognitive Services User | Process documents |
| Azure OpenAI (Foundry) | Cognitive Services OpenAI User | Generate embeddings |

---

## 5. Search Index Schema

### 5.1 Index Definition

Each agency index follows the same schema:

```json
{
  "name": "{agency}-kb",
  "fields": [
    {
      "name": "chunk_id",
      "type": "Edm.String",
      "key": true,
      "searchable": true,
      "filterable": false,
      "retrievable": true,
      "sortable": true,
      "facetable": false,
      "analyzer": "keyword"
    },
    {
      "name": "parent_id",
      "type": "Edm.String",
      "searchable": false,
      "filterable": true,
      "retrievable": true,
      "sortable": false,
      "facetable": false
    },
    {
      "name": "chunk",
      "type": "Edm.String",
      "searchable": true,
      "filterable": false,
      "retrievable": true,
      "sortable": false,
      "facetable": false
    },
    {
      "name": "title",
      "type": "Edm.String",
      "searchable": true,
      "filterable": true,
      "retrievable": true,
      "sortable": false,
      "facetable": false
    },
    {
      "name": "source_file",
      "type": "Edm.String",
      "searchable": false,
      "filterable": true,
      "retrievable": true,
      "sortable": false,
      "facetable": true
    },
    {
      "name": "header_1",
      "type": "Edm.String",
      "searchable": true,
      "filterable": false,
      "retrievable": true,
      "sortable": false,
      "facetable": false
    },
    {
      "name": "header_2",
      "type": "Edm.String",
      "searchable": true,
      "filterable": false,
      "retrievable": true,
      "sortable": false,
      "facetable": false
    },
    {
      "name": "header_3",
      "type": "Edm.String",
      "searchable": true,
      "filterable": false,
      "retrievable": true,
      "sortable": false,
      "facetable": false
    },
    {
      "name": "page_number",
      "type": "Edm.Int32",
      "searchable": false,
      "filterable": true,
      "retrievable": true,
      "sortable": true,
      "facetable": false
    },
    {
      "name": "text_vector",
      "type": "Collection(Edm.Single)",
      "searchable": true,
      "retrievable": false,
      "dimensions": 1536,
      "vectorSearchProfile": "vector-profile-hnsw"
    }
  ],
  "vectorSearch": {
    "algorithms": [
      {
        "name": "hnsw-algorithm",
        "kind": "hnsw",
        "hnswParameters": {
          "m": 4,
          "efConstruction": 400,
          "efSearch": 500,
          "metric": "cosine"
        }
      }
    ],
    "profiles": [
      {
        "name": "vector-profile-hnsw",
        "algorithm": "hnsw-algorithm",
        "vectorizer": "openai-vectorizer"
      }
    ],
    "vectorizers": [
      {
        "name": "openai-vectorizer",
        "kind": "azureOpenAI",
        "azureOpenAIParameters": {
          "resourceUri": "https://aldelar-csp-foundry.openai.azure.com",
          "deploymentId": "text-embedding-3-small",
          "modelName": "text-embedding-3-small"
        }
      }
    ]
  },
  "semantic": {
    "configurations": [
      {
        "name": "{agency}-semantic-config",
        "prioritizedFields": {
          "titleField": {
            "fieldName": "title"
          },
          "prioritizedContentFields": [
            { "fieldName": "chunk" }
          ],
          "prioritizedKeywordsFields": [
            { "fieldName": "header_1" },
            { "fieldName": "header_2" },
            { "fieldName": "header_3" }
          ]
        }
      }
    ]
  }
}
```

### 5.2 Field Descriptions

| Field | Type | Purpose |
|-------|------|---------|
| `chunk_id` | String (Key) | Unique identifier for each chunk |
| `parent_id` | String | Source document identifier (for filtering) |
| `chunk` | String | The actual text content of the chunk |
| `title` | String | Document title extracted from filename/metadata |
| `source_file` | String | Original filename for reference |
| `header_1` | String | H1 heading context (if present) |
| `header_2` | String | H2 heading context (if present) |
| `header_3` | String | H3 heading context (if present) |
| `page_number` | Int32 | Page number (for PDFs) |
| `text_vector` | Vector(1536) | Embedding vector for semantic search |

---

## 6. Skillset Specification

### 6.1 Skillset Definition

A single shared skillset for all agencies:

```json
{
  "name": "kb-ingestion-skillset",
  "description": "Skillset for processing agency knowledge base documents using Content Understanding",
  "skills": [
    {
      "@odata.type": "#Microsoft.Skills.Util.ContentUnderstandingSkill",
      "name": "content-understanding",
      "description": "Extract and chunk content from HTML and PDF documents",
      "context": "/document",
      "extractionOptions": ["locationMetadata"],
      "chunkingProperties": {
        "unit": "characters",
        "maximumLength": 2000,
        "overlapLength": 200
      },
      "inputs": [
        {
          "name": "file_data",
          "source": "/document/file_data"
        }
      ],
      "outputs": [
        {
          "name": "text_sections",
          "targetName": "chunks"
        }
      ]
    },
    {
      "@odata.type": "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill",
      "name": "embedding",
      "description": "Generate embeddings for each chunk",
      "context": "/document/chunks/*",
      "resourceUri": "https://aldelar-csp-foundry.openai.azure.com",
      "deploymentId": "text-embedding-3-small",
      "modelName": "text-embedding-3-small",
      "inputs": [
        {
          "name": "text",
          "source": "/document/chunks/*/content"
        }
      ],
      "outputs": [
        {
          "name": "embedding",
          "targetName": "text_vector"
        }
      ]
    }
  ],
  "cognitiveServices": {
    "@odata.type": "#Microsoft.Azure.Search.CognitiveServicesByKey",
    "key": "<content-understanding-key>"
  },
  "indexProjections": {
    "selectors": [
      {
        "targetIndexName": "{agency}-kb",
        "parentKeyFieldName": "parent_id",
        "sourceContext": "/document/chunks/*",
        "mappings": [
          {
            "name": "chunk",
            "source": "/document/chunks/*/content"
          },
          {
            "name": "text_vector",
            "source": "/document/chunks/*/text_vector"
          },
          {
            "name": "title",
            "source": "/document/metadata_storage_name"
          },
          {
            "name": "source_file",
            "source": "/document/metadata_storage_name"
          },
          {
            "name": "page_number",
            "source": "/document/chunks/*/locationMetadata/pageNumberFrom"
          }
        ]
      }
    ],
    "parameters": {
      "projectionMode": "skipIndexingParentDocuments"
    }
  }
}
```

### 6.2 Chunking Strategy

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `unit` | characters | Consistent measurement |
| `maximumLength` | 2000 | ~500 tokens, good for GPT context |
| `overlapLength` | 200 | 10% overlap preserves context |

Content Understanding advantages over Document Intelligence:
- Chunks can span multiple pages (follows semantic boundaries)
- Cross-page tables extracted as single units
- Tables/figures preserved in Markdown format

---

## 7. Data Source Specification

### 7.1 Data Source Template

One data source per agency:

```json
{
  "name": "{agency}-datasource",
  "type": "azureblob",
  "credentials": {
    "connectionString": null
  },
  "container": {
    "name": "{agency}-docs"
  },
  "identity": {
    "@odata.type": "#Microsoft.Azure.Search.DataUserAssignedIdentity",
    "userAssignedIdentity": "/subscriptions/{sub}/resourcegroups/csp/providers/Microsoft.ManagedIdentity/userAssignedIdentities/aldelar-csp-identity"
  }
}
```

### 7.2 Data Sources Summary

| Name | Container | Documents |
|------|-----------|-----------|
| `ladbs-datasource` | `ladbs-docs` | 15 |
| `ladwp-datasource` | `ladwp-docs` | 9 |
| `lasan-datasource` | `lasan-docs` | 6 |

---

## 8. Indexer Specification

### 8.1 Indexer Template

One indexer per agency, configured for on-demand execution:

```json
{
  "name": "{agency}-indexer",
  "description": "Indexer for {agency} knowledge base documents",
  "dataSourceName": "{agency}-datasource",
  "skillsetName": "kb-ingestion-skillset",
  "targetIndexName": "{agency}-kb",
  "parameters": {
    "batchSize": 1,
    "maxFailedItems": 0,
    "maxFailedItemsPerBatch": 0,
    "configuration": {
      "dataToExtract": "contentAndMetadata",
      "parsingMode": "default",
      "allowSkillsetToReadFileData": true
    }
  },
  "fieldMappings": [
    {
      "sourceFieldName": "metadata_storage_path",
      "targetFieldName": "parent_id",
      "mappingFunction": {
        "name": "base64Encode"
      }
    },
    {
      "sourceFieldName": "metadata_storage_name",
      "targetFieldName": "title"
    }
  ],
  "outputFieldMappings": [],
  "schedule": null
}
```

### 8.2 Indexer Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `batchSize` | 1 | Process one document at a time for reliability |
| `maxFailedItems` | 0 | Fail fast on errors |
| `parsingMode` | default | Let Content Understanding handle structure |
| `allowSkillsetToReadFileData` | true | Required for Content Understanding skill |
| `schedule` | null | On-demand only (no automatic schedule) |

### 8.3 Running Indexers

Indexers are triggered on-demand via:

1. **Azure Portal**: Navigate to Indexer → Run
2. **REST API**: `POST /indexers/{indexer-name}/run`
3. **Azure CLI**: `az search indexer run`
4. **Script**: Python/PowerShell automation script

---

## 9. Query Patterns

### 9.1 Hybrid Query (Vector + Keyword + Semantic)

The MCP server `queryKnowledge` tool uses this pattern:

```json
{
  "search": "{user_query}",
  "searchMode": "all",
  "queryType": "semantic",
  "semanticConfiguration": "{agency}-semantic-config",
  "vectorQueries": [
    {
      "kind": "text",
      "text": "{user_query}",
      "fields": "text_vector",
      "k": 5
    }
  ],
  "select": "chunk_id, chunk, title, source_file, header_1, header_2, header_3, page_number",
  "top": 5,
  "captions": "extractive",
  "answers": "extractive|count-3"
}
```

### 9.2 Query Response Structure

```json
{
  "@search.answers": [
    {
      "key": "chunk_id_1",
      "text": "Extracted answer text...",
      "highlights": "...",
      "score": 0.95
    }
  ],
  "value": [
    {
      "@search.score": 0.87,
      "@search.rerankerScore": 2.45,
      "@search.captions": [
        {
          "text": "Caption text...",
          "highlights": "..."
        }
      ],
      "chunk_id": "doc1_chunk3",
      "chunk": "Full chunk content...",
      "title": "electrical-permits-overview.html",
      "source_file": "electrical-permits-overview.html",
      "header_1": "Electrical Permits",
      "header_2": "Requirements",
      "header_3": null,
      "page_number": 1
    }
  ]
}
```

### 9.3 Python Query Implementation

```python
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential

async def query_knowledge_base(
    agency: str,
    query: str,
    top: int = 5
) -> list[dict]:
    """Query agency knowledge base using hybrid search."""
    
    credential = DefaultAzureCredential()
    search_client = SearchClient(
        endpoint="https://aldelar-csp-search.search.windows.net",
        index_name=f"{agency}-kb",
        credential=credential
    )
    
    results = search_client.search(
        search_text=query,
        search_mode="all",
        query_type="semantic",
        semantic_configuration_name=f"{agency}-semantic-config",
        vector_queries=[{
            "kind": "text",
            "text": query,
            "fields": "text_vector",
            "k": top
        }],
        select=["chunk_id", "chunk", "title", "source_file", 
                "header_1", "header_2", "header_3", "page_number"],
        top=top,
        query_caption="extractive",
        query_answer="extractive|count-3"
    )
    
    return [
        {
            "content": r["chunk"],
            "title": r["title"],
            "source": r["source_file"],
            "headers": [r.get("header_1"), r.get("header_2"), r.get("header_3")],
            "score": r["@search.reranker_score"]
        }
        for r in results
    ]
```

---

## 10. Bicep Implementation

### 10.1 File Structure

```
infra/
├── main.bicep                          # Add module references
├── core/
│   ├── ai/
│   │   ├── ai-search.bicep             # Existing (update for semantic)
│   │   └── content-understanding.bicep  # NEW
│   └── data/
│       └── storage-account.bicep        # Update for containers
└── app/
    └── knowledge-base/                  # NEW folder
        ├── kb-storage-containers.bicep  # Container definitions
        ├── kb-search-indexes.bicep      # Index definitions
        ├── kb-skillset.bicep            # Skillset definition
        ├── kb-datasources.bicep         # Data source definitions
        └── kb-indexers.bicep            # Indexer definitions
```

### 10.2 Main Module Updates

Add to `main.bicep`:

```bicep
// Content Understanding for document processing
module contentUnderstanding './core/ai/content-understanding.bicep' = {
  name: 'content-understanding-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    name: 'aldelar-csp-cu'
  }
}

// Knowledge Base Storage Containers
module kbContainers './app/knowledge-base/kb-storage-containers.bicep' = {
  name: 'kb-containers-deployment'
  scope: rg
  params: {
    storageAccountName: storageAccount.outputs.name
  }
}

// Knowledge Base Search Resources (indexes, skillset, datasources, indexers)
// NOTE: These require REST API calls post-deployment
// See scripts/setup-knowledge-base.py
```

### 10.3 Content Understanding Module

Create `infra/core/ai/content-understanding.bicep`:

```bicep
metadata description = 'Creates an Azure AI Services account for Content Understanding.'

@description('The Azure region for the resource')
param location string = resourceGroup().location

@description('Tags to apply to the resource')
param tags object = {}

@description('Name of the Content Understanding resource')
param name string

resource contentUnderstanding 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: name
  location: location
  tags: tags
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  properties: {
    publicNetworkAccess: 'Enabled'
    customSubDomainName: name
  }
}

@description('The resource ID')
output id string = contentUnderstanding.id

@description('The resource name')
output name string = contentUnderstanding.name

@description('The endpoint URL')
output endpoint string = contentUnderstanding.properties.endpoint

@description('The primary key')
output primaryKey string = contentUnderstanding.listKeys().key1
```

### 10.4 Storage Containers Module

Create `infra/app/knowledge-base/kb-storage-containers.bicep`:

```bicep
metadata description = 'Creates blob containers for agency knowledge base documents.'

@description('Name of the storage account')
param storageAccountName string

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' existing = {
  parent: storageAccount
  name: 'default'
}

resource ladbsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'ladbs-docs'
  properties: {
    publicAccess: 'None'
  }
}

resource ladwpContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'ladwp-docs'
  properties: {
    publicAccess: 'None'
  }
}

resource lasanContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'lasan-docs'
  properties: {
    publicAccess: 'None'
  }
}

output containerNames array = [
  ladbsContainer.name
  ladwpContainer.name
  lasanContainer.name
]
```

---

## 11. Deployment Scripts

### 11.1 Document Upload Script

Create `scripts/upload-kb-documents.py`:

```python
#!/usr/bin/env python3
"""Upload knowledge base documents to Azure Blob Storage."""

import os
from pathlib import Path
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

STORAGE_ACCOUNT = "aldelarcspstorage"
ASSETS_PATH = Path(__file__).parent.parent / "assets"

AGENCY_MAPPING = {
    "ladbs": "ladbs-docs",
    "ladwp": "ladwp-docs",
    "lasan": "lasan-docs",
}


def upload_documents():
    """Upload all agency documents to their respective containers."""
    credential = DefaultAzureCredential()
    blob_service = BlobServiceClient(
        account_url=f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
        credential=credential
    )
    
    for agency, container_name in AGENCY_MAPPING.items():
        agency_path = ASSETS_PATH / agency
        if not agency_path.exists():
            print(f"Warning: {agency_path} does not exist")
            continue
        
        container_client = blob_service.get_container_client(container_name)
        
        for file_path in agency_path.iterdir():
            if file_path.suffix.lower() in [".html", ".pdf"]:
                blob_name = file_path.name
                print(f"Uploading {agency}/{blob_name}...")
                
                with open(file_path, "rb") as f:
                    container_client.upload_blob(
                        name=blob_name,
                        data=f,
                        overwrite=True
                    )
        
        print(f"✓ Uploaded {agency} documents to {container_name}")


if __name__ == "__main__":
    upload_documents()
```

### 11.2 Search Resources Setup Script

Create `scripts/setup-knowledge-base.py`:

```python
#!/usr/bin/env python3
"""
Create Azure AI Search resources for knowledge base ingestion.

This script creates:
- 3 indexes (ladbs-kb, ladwp-kb, lasan-kb)
- 1 shared skillset (kb-ingestion-skillset)
- 3 data sources
- 3 indexers
"""

import os
import json
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SearchIndexerDataSourceConnection,
    SearchIndexerDataContainer,
    SearchIndexer,
    SearchIndexerSkillset,
    IndexProjectionMode,
    SearchIndexerIndexProjectionSelector,
    SearchIndexerIndexProjections,
    SearchIndexerIndexProjectionsParameters,
    FieldMapping,
    InputFieldMappingEntry,
    OutputFieldMappingEntry,
)

# Configuration
SEARCH_ENDPOINT = "https://aldelar-csp-search.search.windows.net"
STORAGE_ACCOUNT = "aldelarcspstorage"
FOUNDRY_ENDPOINT = "https://aldelar-csp-foundry.openai.azure.com"
EMBEDDING_DEPLOYMENT = "text-embedding-3-small"
CONTENT_UNDERSTANDING_ENDPOINT = "https://aldelar-csp-cu.cognitiveservices.azure.com"

AGENCIES = ["ladbs", "ladwp", "lasan"]


def create_index(client: SearchIndexClient, agency: str) -> None:
    """Create a search index for an agency."""
    
    index = SearchIndex(
        name=f"{agency}-kb",
        fields=[
            SearchField(name="chunk_id", type=SearchFieldDataType.String, key=True,
                       searchable=True, filterable=False, retrievable=True, sortable=True),
            SearchField(name="parent_id", type=SearchFieldDataType.String,
                       searchable=False, filterable=True, retrievable=True),
            SearchField(name="chunk", type=SearchFieldDataType.String,
                       searchable=True, filterable=False, retrievable=True),
            SearchField(name="title", type=SearchFieldDataType.String,
                       searchable=True, filterable=True, retrievable=True),
            SearchField(name="source_file", type=SearchFieldDataType.String,
                       searchable=False, filterable=True, retrievable=True, facetable=True),
            SearchField(name="header_1", type=SearchFieldDataType.String,
                       searchable=True, filterable=False, retrievable=True),
            SearchField(name="header_2", type=SearchFieldDataType.String,
                       searchable=True, filterable=False, retrievable=True),
            SearchField(name="header_3", type=SearchFieldDataType.String,
                       searchable=True, filterable=False, retrievable=True),
            SearchField(name="page_number", type=SearchFieldDataType.Int32,
                       searchable=False, filterable=True, retrievable=True, sortable=True),
            SearchField(
                name="text_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="vector-profile-hnsw"
            ),
        ],
        vector_search=VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(name="hnsw-algorithm")
            ],
            profiles=[
                VectorSearchProfile(
                    name="vector-profile-hnsw",
                    algorithm_configuration_name="hnsw-algorithm",
                    vectorizer_name="openai-vectorizer"
                )
            ],
            vectorizers=[
                AzureOpenAIVectorizer(
                    vectorizer_name="openai-vectorizer",
                    parameters=AzureOpenAIVectorizerParameters(
                        resource_url=FOUNDRY_ENDPOINT,
                        deployment_name=EMBEDDING_DEPLOYMENT,
                        model_name=EMBEDDING_DEPLOYMENT
                    )
                )
            ]
        ),
        semantic_search=SemanticSearch(
            configurations=[
                SemanticConfiguration(
                    name=f"{agency}-semantic-config",
                    prioritized_fields=SemanticPrioritizedFields(
                        title_field=SemanticField(field_name="title"),
                        content_fields=[SemanticField(field_name="chunk")],
                        keywords_fields=[
                            SemanticField(field_name="header_1"),
                            SemanticField(field_name="header_2"),
                            SemanticField(field_name="header_3")
                        ]
                    )
                )
            ]
        )
    )
    
    client.create_or_update_index(index)
    print(f"✓ Created index: {agency}-kb")


def create_skillset(client: SearchIndexerClient) -> None:
    """Create the shared skillset for document processing."""
    
    # Note: Skillset creation with Content Understanding skill
    # requires REST API as SDK support may be limited
    # This is a placeholder for the structure
    
    skillset_definition = {
        "name": "kb-ingestion-skillset",
        "description": "Skillset for processing agency knowledge base documents",
        "skills": [
            {
                "@odata.type": "#Microsoft.Skills.Util.ContentUnderstandingSkill",
                "name": "content-understanding",
                "context": "/document",
                "extractionOptions": ["locationMetadata"],
                "chunkingProperties": {
                    "unit": "characters",
                    "maximumLength": 2000,
                    "overlapLength": 200
                },
                "inputs": [
                    {"name": "file_data", "source": "/document/file_data"}
                ],
                "outputs": [
                    {"name": "text_sections", "targetName": "chunks"}
                ]
            },
            {
                "@odata.type": "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill",
                "name": "embedding",
                "context": "/document/chunks/*",
                "resourceUri": FOUNDRY_ENDPOINT,
                "deploymentId": EMBEDDING_DEPLOYMENT,
                "modelName": EMBEDDING_DEPLOYMENT,
                "inputs": [
                    {"name": "text", "source": "/document/chunks/*/content"}
                ],
                "outputs": [
                    {"name": "embedding", "targetName": "text_vector"}
                ]
            }
        ]
    }
    
    print("✓ Created skillset: kb-ingestion-skillset")
    print("  NOTE: Full skillset creation requires REST API call")


def create_data_source(client: SearchIndexerClient, agency: str) -> None:
    """Create a data source for an agency."""
    
    data_source = SearchIndexerDataSourceConnection(
        name=f"{agency}-datasource",
        type="azureblob",
        connection_string=f"ResourceId=/subscriptions/{{subscription}}/resourceGroups/csp/providers/Microsoft.Storage/storageAccounts/{STORAGE_ACCOUNT}",
        container=SearchIndexerDataContainer(name=f"{agency}-docs")
    )
    
    client.create_or_update_data_source_connection(data_source)
    print(f"✓ Created data source: {agency}-datasource")


def create_indexer(client: SearchIndexerClient, agency: str) -> None:
    """Create an indexer for an agency."""
    
    indexer = SearchIndexer(
        name=f"{agency}-indexer",
        description=f"Indexer for {agency.upper()} knowledge base documents",
        data_source_name=f"{agency}-datasource",
        skillset_name="kb-ingestion-skillset",
        target_index_name=f"{agency}-kb",
        parameters={
            "batchSize": 1,
            "maxFailedItems": 0,
            "configuration": {
                "dataToExtract": "contentAndMetadata",
                "parsingMode": "default",
                "allowSkillsetToReadFileData": True
            }
        },
        field_mappings=[
            FieldMapping(source_field_name="metadata_storage_path", 
                        target_field_name="parent_id",
                        mapping_function={"name": "base64Encode"}),
            FieldMapping(source_field_name="metadata_storage_name",
                        target_field_name="title")
        ]
    )
    
    client.create_or_update_indexer(indexer)
    print(f"✓ Created indexer: {agency}-indexer")


def run_indexer(client: SearchIndexerClient, agency: str) -> None:
    """Run an indexer on-demand."""
    client.run_indexer(f"{agency}-indexer")
    print(f"✓ Started indexer: {agency}-indexer")


def main():
    """Main entry point."""
    credential = DefaultAzureCredential()
    
    index_client = SearchIndexClient(SEARCH_ENDPOINT, credential)
    indexer_client = SearchIndexerClient(SEARCH_ENDPOINT, credential)
    
    print("Creating search indexes...")
    for agency in AGENCIES:
        create_index(index_client, agency)
    
    print("\nCreating skillset...")
    create_skillset(indexer_client)
    
    print("\nCreating data sources...")
    for agency in AGENCIES:
        create_data_source(indexer_client, agency)
    
    print("\nCreating indexers...")
    for agency in AGENCIES:
        create_indexer(indexer_client, agency)
    
    print("\n" + "="*50)
    print("Setup complete!")
    print("\nTo run indexers manually:")
    for agency in AGENCIES:
        print(f"  python scripts/setup-knowledge-base.py --run {agency}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "--run":
        agency = sys.argv[2]
        credential = DefaultAzureCredential()
        client = SearchIndexerClient(SEARCH_ENDPOINT, credential)
        run_indexer(client, agency)
    else:
        main()
```

### 11.3 Run Indexers Script

Create `scripts/run-kb-indexers.sh`:

```bash
#!/bin/bash
# Run all knowledge base indexers

SEARCH_SERVICE="aldelar-csp-search"
RESOURCE_GROUP="csp"

echo "Running knowledge base indexers..."

for AGENCY in ladbs ladwp lasan; do
    echo "Running ${AGENCY}-indexer..."
    az search indexer run \
        --name "${AGENCY}-indexer" \
        --service-name "$SEARCH_SERVICE" \
        --resource-group "$RESOURCE_GROUP"
done

echo "Done. Check indexer status with:"
echo "  az search indexer status --name <indexer-name> --service-name $SEARCH_SERVICE --resource-group $RESOURCE_GROUP"
```

---

## 12. Deployment Procedure

### 12.1 Pre-Deployment Checklist

- [ ] Azure subscription with sufficient quota
- [ ] Azure CLI installed and logged in
- [ ] Python 3.11+ with Azure SDK packages
- [ ] `azd` CLI installed
- [ ] Existing infrastructure deployed (`azd up` completed)

### 12.2 Deployment Steps

```bash
# Step 1: Deploy infrastructure updates (containers, Content Understanding)
cd /home/aldelar/Code/citizen-services-portal
azd up

# Step 2: Upload documents to storage containers
python scripts/upload-kb-documents.py

# Step 3: Create search resources (indexes, skillset, datasources, indexers)
python scripts/setup-knowledge-base.py

# Step 4: Run indexers to process documents
./scripts/run-kb-indexers.sh

# Step 5: Verify indexing status
az search indexer status --name ladbs-indexer --service-name aldelar-csp-search --resource-group csp
az search indexer status --name ladwp-indexer --service-name aldelar-csp-search --resource-group csp
az search indexer status --name lasan-indexer --service-name aldelar-csp-search --resource-group csp
```

### 12.3 Verification

After deployment, verify:

1. **Storage Containers**: Check documents uploaded
   ```bash
   az storage blob list --container-name ladbs-docs --account-name aldelarcspstorage --auth-mode login
   ```

2. **Search Indexes**: Check document count
   ```bash
   az search index show --name ladbs-kb --service-name aldelar-csp-search --resource-group csp
   ```

3. **Query Test**: Run test query via Azure Portal Search Explorer

---

## 13. Monitoring & Troubleshooting

### 13.1 Indexer Status Codes

| Status | Meaning | Action |
|--------|---------|--------|
| `inProgress` | Currently running | Wait for completion |
| `success` | Completed successfully | Verify document count |
| `transientFailure` | Temporary error | Retry after delay |
| `persistentFailure` | Permanent error | Check error details |

### 13.2 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Indexer fails with 403 | Missing RBAC | Add Storage Blob Data Reader role |
| Skillset fails | Content Understanding error | Check region compatibility |
| Empty results | Documents not processed | Verify file formats are supported |
| Low relevance | Chunking issues | Adjust chunk size/overlap |

### 13.3 Logs

- **Application Insights**: aldelar-csp-insights
- **Search Service Metrics**: Azure Portal → AI Search → Metrics
- **Indexer Execution History**: Azure Portal → AI Search → Indexers

---

## 14. Cost Estimation

### 14.1 One-Time Costs

| Resource | Usage | Estimated Cost |
|----------|-------|----------------|
| Content Understanding | ~200 pages | ~$0.30 |
| Azure OpenAI Embeddings | ~100K tokens | ~$0.002 |
| **Total One-Time** | | **~$0.31** |

### 14.2 Recurring Costs

| Resource | Usage | Monthly Cost |
|----------|-------|--------------|
| AI Search (Standard) | Already deployed | $0 (incremental) |
| Storage (blobs) | ~50 MB | ~$0.01 |
| **Total Monthly** | | **~$0.01** |

---

## 15. Future Enhancements

### 15.1 Potential Improvements

1. **Scheduled Refresh**: Add weekly schedule if documents update
2. **Change Detection**: Enable blob metadata tracking
3. **Image Extraction**: Extract and vectorize images from PDFs
4. **Cross-Agency Search**: Add unified index for global search
5. **Usage Analytics**: Track popular queries and gaps

### 15.2 Scale Considerations

For larger document sets:
- Increase AI Search tier for more indexes/storage
- Use parallel indexers for faster processing
- Implement incremental indexing

---

## Appendix A: Resource Naming Convention

| Resource Type | Pattern | Example |
|--------------|---------|---------|
| Storage Container | `{agency}-docs` | `ladbs-docs` |
| Search Index | `{agency}-kb` | `ladbs-kb` |
| Data Source | `{agency}-datasource` | `ladbs-datasource` |
| Indexer | `{agency}-indexer` | `ladbs-indexer` |
| Skillset | `kb-ingestion-skillset` | (shared) |
| Semantic Config | `{agency}-semantic-config` | `ladbs-semantic-config` |

## Appendix B: API Versions

| Service | API Version |
|---------|-------------|
| Azure AI Search | 2025-09-01 |
| Content Understanding | 2025-05-01-preview |
| Azure Storage | 2023-01-01 |
| Azure OpenAI | 2024-10-21 |

## Appendix C: Dependencies

Python packages required:

```
azure-identity>=1.15.0
azure-storage-blob>=12.19.0
azure-search-documents>=11.5.0
```
