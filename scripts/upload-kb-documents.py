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
        uploaded_count = 0
        
        for file_path in agency_path.iterdir():
            if file_path.suffix.lower() in [".html", ".pdf"]:
                blob_name = file_path.name
                try:
                    print(f"Uploading {agency}/{blob_name}...")
                    with open(file_path, "rb") as f:
                        container_client.upload_blob(
                            name=blob_name,
                            data=f,
                            overwrite=True
                        )
                    uploaded_count += 1
                except PermissionError as e:
                    print(f"✗ Permission denied for {file_path}: {e}")
                except OSError as e:
                    print(f"✗ Error reading {file_path}: {e}")
                except Exception as e:
                    print(f"✗ Failed to upload {blob_name}: {e}")
        
        print(f"✓ Uploaded {uploaded_count} {agency} documents to {container_name}")


if __name__ == "__main__":
    upload_documents()
