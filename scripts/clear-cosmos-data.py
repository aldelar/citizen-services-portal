#!/usr/bin/env python3
"""
Clear all data from CosmosDB containers.

Usage:
    python scripts/clear-cosmos-data.py [--confirm] [--database DATABASE] [--containers CONTAINERS]

Without --confirm, shows what would be deleted. With --confirm, performs deletion.
Use --database to specify which database (default: csp).
Use --containers to specify which containers to clear (comma-separated).
"""

import asyncio
import argparse
import sys
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential
from azure.cosmos import exceptions


# Default values - override with environment variables if needed
COSMOS_ENDPOINT = "https://aldelar-csp-cosmos.documents.azure.com:443/"

# Database configurations: containers and their partition key paths
DATABASES = {
    "csp": {
        "users": "/id",
        "projects": "/userId",
        "messages": "/projectId",
        "step_completions": "/projectId",
    },
    "ladbs": {
        "permits": "/userId",
        "inspections": "/permitId",
    },
    "ladwp": {
        "interconnections": "/userId",
        "rebates": "/userId",
        "tou_enrollments": "/userId",
    },
    "lasan": {
        "pickups": "/userId",
    },
}


async def count_items(container) -> int:
    """Count items in a container."""
    count = 0
    async for _ in container.read_all_items():
        count += 1
    return count


async def delete_items(container, partition_key_path: str, dry_run: bool = True) -> tuple[int, int]:
    """Delete all items from a container. Returns (deleted, errors)."""
    deleted = 0
    errors = 0
    
    # Get the partition key field name (remove leading /)
    pk_field = partition_key_path.lstrip("/")
    
    async for item in container.read_all_items():
        item_id = item["id"]
        partition_key = item.get(pk_field, item_id)  # fallback to id if pk field not found
        
        if dry_run:
            print(f"  Would delete: {item_id}")
            deleted += 1
        else:
            try:
                await container.delete_item(item_id, partition_key=partition_key)
                deleted += 1
            except exceptions.CosmosResourceNotFoundError:
                # Already deleted
                pass
            except Exception as e:
                print(f"  Error deleting {item_id}: {e}")
                errors += 1
    
    return deleted, errors


async def main(confirm: bool = False, database: str = "csp", containers: list[str] | None = None):
    """Main function to clear all containers."""
    # Validate database
    if database not in DATABASES:
        print(f"❌ Invalid database: {database}")
        print(f"   Valid databases: {', '.join(DATABASES.keys())}")
        return
    
    all_containers = DATABASES[database]
    
    # Determine which containers to clear
    if containers:
        target_containers = {k: v for k, v in all_containers.items() if k in containers}
        invalid = set(containers) - set(all_containers.keys())
        if invalid:
            print(f"❌ Invalid container names: {', '.join(invalid)}")
            print(f"   Valid containers for {database}: {', '.join(all_containers.keys())}")
            return
    else:
        target_containers = all_containers
    
    print("=" * 60)
    print("🗑️  CosmosDB Data Cleaner")
    print("=" * 60)
    print(f"\nEndpoint: {COSMOS_ENDPOINT}")
    print(f"Database: {database}")
    print(f"Containers: {', '.join(target_containers.keys())}")
    print(f"Mode: {'DELETE (confirmed)' if confirm else 'DRY RUN'}")
    print()
    
    credential = DefaultAzureCredential()
    client = CosmosClient(COSMOS_ENDPOINT, credential=credential)
    
    try:
        db = client.get_database_client(database)
        
        for container_name, partition_key_path in target_containers.items():
            print(f"\n📦 Container: {container_name}")
            print(f"   Partition key: {partition_key_path}")
            
            try:
                container = db.get_container_client(container_name)
                
                # Count items first
                item_count = await count_items(container)
                print(f"   Items found: {item_count}")
                
                if item_count == 0:
                    print("   ✅ Already empty")
                    continue
                
                if confirm:
                    deleted, errors = await delete_items(container, partition_key_path, dry_run=False)
                    if errors > 0:
                        print(f"   ⚠️  Deleted {deleted} items, {errors} errors")
                    else:
                        print(f"   ✅ Deleted {deleted} items")
                else:
                    deleted, _ = await delete_items(container, partition_key_path, dry_run=True)
                    print(f"   Would delete {deleted} items")
                    
            except exceptions.CosmosResourceNotFoundError:
                print(f"   ⚠️  Container not found (skipping)")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("\n" + "=" * 60)
        if confirm:
            print("✅ Done! All containers cleared.")
        else:
            print("ℹ️  Dry run complete. Run with --confirm to delete.")
        print("=" * 60 + "\n")
        
    finally:
        await client.close()
        await credential.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clear all data from CosmosDB containers")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually perform the deletion (without this flag, shows what would be deleted)"
    )
    parser.add_argument(
        "--database",
        type=str,
        default="csp",
        help=f"Database to clear (default: csp). Valid: {', '.join(DATABASES.keys())}"
    )
    parser.add_argument(
        "--containers",
        type=str,
        help="Comma-separated list of containers to clear (default: all in database)"
    )
    args = parser.parse_args()
    
    containers = args.containers.split(",") if args.containers else None
    asyncio.run(main(confirm=args.confirm, database=args.database, containers=containers))
