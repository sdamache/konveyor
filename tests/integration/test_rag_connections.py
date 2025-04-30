"""Test connections to RAG infrastructure components."""

import os
from datetime import datetime, UTC

from pymongo import MongoClient
import redis

from konveyor.settings import settings_loader

# Load environment variables
settings_loader.load_settings()


def test_cosmos_connection():
    """Test connection to Cosmos DB and basic operations."""
    print("\n=== Testing Cosmos DB Connection ===")

    # Get connection string from Azure CLI
    cosmos_connection_string = os.getenv("AZURE_COSMOS_CONNECTION_STRING")
    if not cosmos_connection_string:
        raise ValueError(
            "AZURE_COSMOS_CONNECTION_STRING environment variable is required"
        )

    # Configure MongoDB client with SSL settings
    client = MongoClient(
        cosmos_connection_string,
        ssl=True,
        ssl_cert_reqs="CERT_NONE",  # For testing only
    )
    db = client["konveyor-db"]

    # Test conversations collection
    try:
        test_doc = {
            "user_id": "test_user",
            "status": "active",
            "conversation_type": "general",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "metadata": {"test": True},
        }

        result = db.conversations.insert_one(test_doc)
        print("✓ Successfully inserted test conversation")

        found = db.conversations.find_one({"_id": result.inserted_id})
        print("✓ Successfully retrieved test conversation")

        db.conversations.delete_one({"_id": result.inserted_id})
        print("✓ Successfully deleted test conversation")

    except Exception as e:
        print(f"✗ Cosmos DB test failed: {str(e)}")
        raise
    finally:
        client.close()


def test_redis_connection():
    """Test connection to Redis Cache and basic operations."""
    print("\n=== Testing Redis Connection ===")

    # Get connection string from Azure CLI
    redis_connection_string = os.getenv("AZURE_REDIS_CONNECTION_STRING")
    if not redis_connection_string:
        raise ValueError(
            "AZURE_REDIS_CONNECTION_STRING environment variable is required"
        )

    # Configure Redis client with SSL settings
    redis_client = redis.from_url(
        redis_connection_string, ssl_cert_reqs=None  # For testing only
    )

    try:
        # Test basic operations
        redis_client.set("test_key", "test_value", ex=60)
        print("✓ Successfully set test key")

        value = redis_client.get("test_key")
        assert value.decode() == "test_value"
        print("✓ Successfully retrieved test key")

        redis_client.delete("test_key")
        print("✓ Successfully deleted test key")

    except Exception as e:
        print(f"✗ Redis test failed: {str(e)}")
        raise
    finally:
        redis_client.close()


def main():
    """Run all connection tests."""
    try:
        test_cosmos_connection()
        test_redis_connection()
        print("\n✓ All connection tests passed!")
    except Exception as e:
        print(f"\n✗ Tests failed: {str(e)}")


if __name__ == "__main__":
    main()
