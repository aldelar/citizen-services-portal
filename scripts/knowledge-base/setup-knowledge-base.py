#!/usr/bin/env python3
"""
Create Azure AI Search resources for knowledge base ingestion.

This script creates:
- 3 indexes (ladbs-kb, ladwp-kb, lasan-kb)
- 3 skillsets (ladbs-kb-skillset, ladwp-kb-skillset, lasan-kb-skillset)
- 3 data sources (using managed identity with ResourceId connection string)
- 3 indexers

Prerequisites:
- Run setup-kb-permissions.sh first to configure RBAC roles
- The Search service must have both system-assigned and user-assigned managed identities
- Storage Blob Data Reader role on storage account for Search service identity
- Cognitive Services User role on AI Foundry and Content Understanding for Search service identity
"""

import os
import json
import requests
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
    FieldMapping,
)

# Configuration
SEARCH_ENDPOINT = "https://aldelar-csp-search.search.windows.net"
STORAGE_ACCOUNT = "aldelarcspstorage"
FOUNDRY_ENDPOINT = "https://aldelar-csp-foundry.openai.azure.com"
EMBEDDING_DEPLOYMENT = "text-embedding-3-small"
# Note: Content Understanding API is only available in specific regions (westus, swedencentral, australiaeast)
# We use a separate resource in West US for Content Understanding
CONTENT_UNDERSTANDING_ENDPOINT = "https://aldelar-csp-cu-westus.cognitiveservices.azure.com"

AGENCIES = ["ladbs", "ladwp", "lasan"]


def get_subscription_id() -> str:
    """Get current Azure subscription ID."""
    import subprocess
    result = subprocess.run(
        ["az", "account", "show", "--query", "id", "-o", "tsv"],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def create_index(client: SearchIndexClient, agency: str) -> None:
    """Create a search index for an agency."""
    
    index = SearchIndex(
        name=f"{agency}-kb",
        fields=[
            SearchField(name="chunk_id", type=SearchFieldDataType.String, key=True,
                       searchable=True, filterable=False, retrievable=True, sortable=True,
                       analyzer_name="keyword"),
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
                HnswAlgorithmConfiguration(
                    name="hnsw-algorithm",
                    parameters={
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": "cosine"
                    }
                )
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


def create_skillset_via_rest(credential: DefaultAzureCredential, subscription_id: str, agency: str) -> None:
    """Create a skillset for document processing using REST API."""
    
    # Get access token for Azure Search
    token = credential.get_token("https://search.azure.com/.default")
    
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }
    
    # Identity for skillset to access Azure OpenAI
    identity_resource_id = f"/subscriptions/{subscription_id}/resourcegroups/csp/providers/Microsoft.ManagedIdentity/userAssignedIdentities/aldelar-csp-identity"
    
    skillset_name = f"{agency}-kb-skillset"
    
    skillset_definition = {
        "name": skillset_name,
        "description": f"Skillset for processing {agency.upper()} knowledge base documents using Content Understanding",
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
                "resourceUri": FOUNDRY_ENDPOINT,
                "deploymentId": EMBEDDING_DEPLOYMENT,
                "modelName": EMBEDDING_DEPLOYMENT,
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
            "@odata.type": "#Microsoft.Azure.Search.AIServicesByIdentity",
            "subdomainUrl": CONTENT_UNDERSTANDING_ENDPOINT
        },
        "indexProjections": {
            "selectors": [
                {
                    "targetIndexName": f"{agency}-kb",
                    "parentKeyFieldName": "parent_id",
                    "sourceContext": "/document/chunks/*",
                    "mappings": [
                        {"name": "chunk", "source": "/document/chunks/*/content"},
                        {"name": "text_vector", "source": "/document/chunks/*/text_vector"},
                        {"name": "title", "source": "/document/metadata_storage_name"},
                        {"name": "source_file", "source": "/document/metadata_storage_name"},
                        {"name": "page_number", "source": "/document/chunks/*/locationMetadata/pageNumberFrom"}
                    ]
                }
            ],
            "parameters": {
                "projectionMode": "skipIndexingParentDocuments"
            }
        }
    }
    
    response = requests.put(
        f"{SEARCH_ENDPOINT}/skillsets/{skillset_name}?api-version=2025-11-01-Preview",
        headers=headers,
        json=skillset_definition
    )
    
    if response.status_code in [200, 201, 204]:
        print(f"✓ Created skillset: {skillset_name}")
    else:
        print(f"✗ Failed to create skillset {skillset_name}: {response.status_code}")
        print(f"  Response: {response.text}")
        raise Exception(f"Skillset creation failed: {response.text}")


def create_data_source_via_rest(credential: DefaultAzureCredential, agency: str, subscription_id: str) -> None:
    """Create a data source for an agency using REST API."""
    
    # Get access token for Azure Search
    token = credential.get_token("https://search.azure.com/.default")
    
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }
    
    datasource_name = f"{agency}-datasource"
    container_name = f"{agency}-docs"
    
    # Use system-assigned managed identity with ResourceId connection string
    datasource_definition = {
        "name": datasource_name,
        "type": "azureblob",
        "credentials": {
            "connectionString": f"ResourceId=/subscriptions/{subscription_id}/resourceGroups/csp/providers/Microsoft.Storage/storageAccounts/{STORAGE_ACCOUNT};"
        },
        "container": {
            "name": container_name
        }
    }
    
    response = requests.put(
        f"{SEARCH_ENDPOINT}/datasources/{datasource_name}?api-version=2025-11-01-Preview",
        headers=headers,
        json=datasource_definition
    )
    
    if response.status_code in [200, 201, 204]:
        print(f"✓ Created data source: {datasource_name}")
    else:
        print(f"✗ Failed to create data source {datasource_name}: {response.status_code}")
        print(f"  Response: {response.text}")
        raise Exception(f"Data source creation failed: {response.text}")


def create_indexer_via_rest(credential: DefaultAzureCredential, agency: str) -> None:
    """Create an indexer for an agency using REST API."""
    
    # Get access token for Azure Search
    token = credential.get_token("https://search.azure.com/.default")
    
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }
    
    indexer_name = f"{agency}-indexer"
    
    indexer_definition = {
        "name": indexer_name,
        "description": f"Indexer for {agency.upper()} knowledge base documents",
        "dataSourceName": f"{agency}-datasource",
        "skillsetName": f"{agency}-kb-skillset",
        "targetIndexName": f"{agency}-kb",
        "parameters": {
            "batchSize": 1,
            "maxFailedItems": 0,
            "maxFailedItemsPerBatch": 0,
            "configuration": {
                "dataToExtract": "contentAndMetadata",
                "parsingMode": "default",
                "allowSkillsetToReadFileData": True
            }
        },
        "fieldMappings": [
            {
                "sourceFieldName": "metadata_storage_path",
                "targetFieldName": "parent_id",
                "mappingFunction": {"name": "base64Encode"}
            },
            {
                "sourceFieldName": "metadata_storage_name",
                "targetFieldName": "title"
            }
        ],
        "schedule": None
    }
    
    response = requests.put(
        f"{SEARCH_ENDPOINT}/indexers/{indexer_name}?api-version=2025-11-01-Preview",
        headers=headers,
        json=indexer_definition
    )
    
    if response.status_code in [200, 201, 204]:
        print(f"✓ Created indexer: {indexer_name}")
    else:
        print(f"✗ Failed to create indexer {indexer_name}: {response.status_code}")
        print(f"  Response: {response.text}")
        raise Exception(f"Indexer creation failed: {response.text}")


def run_indexer(client: SearchIndexerClient, agency: str) -> None:
    """Run an indexer on-demand."""
    client.run_indexer(f"{agency}-indexer")
    print(f"✓ Started indexer: {agency}-indexer")


def main():
    """Main entry point."""
    credential = DefaultAzureCredential()
    subscription_id = get_subscription_id()
    
    index_client = SearchIndexClient(SEARCH_ENDPOINT, credential)
    indexer_client = SearchIndexerClient(SEARCH_ENDPOINT, credential)
    
    print("Creating search indexes...")
    for agency in AGENCIES:
        create_index(index_client, agency)
    
    print("\nCreating skillsets...")
    for agency in AGENCIES:
        create_skillset_via_rest(credential, subscription_id, agency)
    
    print("\nCreating data sources...")
    for agency in AGENCIES:
        create_data_source_via_rest(credential, agency, subscription_id)
    
    print("\nCreating indexers...")
    for agency in AGENCIES:
        create_indexer_via_rest(credential, agency)
    
    print("\n" + "="*50)
    print("Setup complete!")
    print("\nTo run indexers manually:")
    for agency in AGENCIES:
        print(f"  python scripts/knowledge-base/setup-knowledge-base.py --run {agency}")
    print("\nOr run all indexers:")
    print("  ./scripts/knowledge-base/run-kb-indexers.sh")
    print("\nTo test the indexes:")
    print("  ./scripts/knowledge-base/run-all-tests.sh")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "--run":
        agency = sys.argv[2]
        credential = DefaultAzureCredential()
        client = SearchIndexerClient(SEARCH_ENDPOINT, credential)
        run_indexer(client, agency)
    else:
        main()
