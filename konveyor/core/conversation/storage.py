"""
Azure storage utilities for Konveyor.
"""
from typing import Dict, List, Optional, Union, Any
import json
import uuid
import logging
from datetime import datetime, timedelta
import datetime as dt
from json import JSONEncoder

import asyncio

# Simple ObjectId class that just uses string IDs
class ObjectId:
    def __init__(self, id_str=None):
        self.id_str = id_str or str(uuid.uuid4())

    def __str__(self):
        return self.id_str

# Simple no-op implementations for storage
class DummyCollection:
    def __init__(self, name):
        self.name = name

    def create_index(self, *args, **kwargs):
        pass

    def insert_one(self, *args, **kwargs):
        pass

    def delete_one(self, *args, **kwargs):
        pass

    def delete_many(self, *args, **kwargs):
        pass

    def find(self, *args, **kwargs):
        return []

class DummyDatabase:
    def __init__(self, name):
        self.name = name

    def get_collection(self, name):
        return DummyCollection(name)

    def list_collection_names(self):
        return []

    def create_collection(self, *args, **kwargs):
        pass

class DummyRedisClient:
    async def lpush(self, *args, **kwargs):
        return 0

    async def expire(self, *args, **kwargs):
        return True

    async def lrange(self, *args, **kwargs):
        return []

    async def delete(self, *args, **kwargs):
        return 0

    def pipeline(self):
        return self

    async def execute(self):
        return []

    async def close(self):
        pass

class MongoClient:
    def __init__(self, *args, **kwargs):
        pass

    def get_database(self, name):
        return DummyDatabase(name)

class MongoJSONEncoder(JSONEncoder):
    """JSON encoder that can handle MongoDB ObjectId."""
    def default(self, obj):
        if hasattr(obj, '__str__') and (isinstance(obj, ObjectId) or obj.__class__.__name__ == 'ObjectId'):
            return str(obj)
        return super().default(obj)

class AzureStorageManager:
    """Manages interactions with Azure storage services."""

    @staticmethod
    def _convert_mongodb_to_cosmos_connection_string(mongo_conn_str: str) -> str:
        """Convert MongoDB connection string to Azure Cosmos DB format.

        Args:
            mongo_conn_str (str): MongoDB connection string

        Returns:
            str: Azure Cosmos DB connection string

        Example:
            MongoDB: mongodb://user:pass@host:port/...
            Cosmos: AccountEndpoint=https://host:port;AccountKey=key
        """
        try:
            # Parse MongoDB connection string
            if not mongo_conn_str.startswith('mongodb://'):
                raise ValueError("Connection string must start with 'mongodb://'")

            # Extract the username and key
            auth_part = mongo_conn_str[len('mongodb://'):]  # Remove protocol
            first_colon = auth_part.find(':')
            if first_colon == -1:
                raise ValueError("Missing password in connection string")

            username = auth_part[:first_colon]
            rest = auth_part[first_colon + 1:]

            # Find the end of the key (before @)
            at_sign = rest.find('@')
            if at_sign == -1:
                raise ValueError("Invalid MongoDB connection string format")

            key = rest[:at_sign]
            host_part = rest[at_sign + 1:]

            # Split host part before any query parameters or path
            host = host_part.split('?')[0].split('/')[0]

            # Build Cosmos DB connection string
            # For MongoDB API, we need to use the mongo.cosmos.azure.com endpoint
            if not host.endswith('mongo.cosmos.azure.com'):
                host = host.replace('documents.azure.com', 'mongo.cosmos.azure.com')
                if ':443' in host:
                    host = host.replace(':443', ':10255')
                elif not ':' in host:
                    host = f"{host}:10255"

            # Return in Cosmos DB format
            return f"AccountEndpoint=https://{host};AccountKey={key}"

        except Exception as e:
            logging.error(f"Failed to parse MongoDB connection string: {str(e)}")
            # Log a redacted version of the connection string for debugging
            redacted = mongo_conn_str.replace(mongo_conn_str.split('@')[0], '***')
            logging.error(f"Connection string (redacted): {redacted}")
            raise ValueError(f"Failed to parse MongoDB connection string: {str(e)}")

    async def _ensure_database_exists(self) -> None:
        """Ensure the database and required collections exist."""
        try:
            # Get database
            self.db = self.mongo_client.get_database("konveyor")

            # Create collections if they don't exist
            if "conversations" not in self.db.list_collection_names():
                self.db.create_collection(
                    "conversations",
                    # Shard key for conversations
                    collation={"locale": "en", "strength": 2}
                )

            if "messages" not in self.db.list_collection_names():
                self.db.create_collection(
                    "messages",
                    # Shard key for messages
                    collation={"locale": "en", "strength": 2}
                )

            # Get collection references
            self.conversations = self.db.get_collection("conversations")
            self.messages = self.db.get_collection("messages")

            # Create indexes
            self.conversations.create_index("id", unique=True)
            self.messages.create_index("conversation_id")

        except Exception as e:
            logging.error(f"Failed to initialize MongoDB: {str(e)}")
            raise

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_database_exists()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Close clients if they have a close method
        if hasattr(self.redis_client, 'close'):
            await self.redis_client.close()

    async def initialize(self):
        """Initialize the storage manager."""
        await self._ensure_database_exists()

    def __init__(self, cosmos_connection_str: str = None, redis_connection_str: str = None):
        # Use dummy clients for MongoDB and Redis
        logging.info("Using dummy storage clients for development/testing")
        self.mongo_client = MongoClient()
        self.redis_client = DummyRedisClient()

        self.message_ttl = timedelta(days=1)  # Keep active conversations for 1 day in Redis

        # Initialize database and collections
        self.db = self.mongo_client.get_database("konveyor")
        self.messages = self.db.get_collection("messages")
        self.conversations = self.db.get_collection("conversations")

        # Create indexes in background
        self._init_task = asyncio.create_task(self._ensure_database_exists())

    async def create_conversation(self, user_id: Optional[str] = None) -> Dict:
        """Create a new conversation."""
        # Wait for initialization to complete
        await self._init_task

        conversation = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "created_at": datetime.now(dt.timezone.utc),
            "updated_at": datetime.now(dt.timezone.utc)
        }
        self.conversations.insert_one(conversation)
        return conversation

    async def add_message(self, conversation_id: str, message_type: str,
                         content: str, metadata: Optional[Dict] = None) -> Dict:
        """Add a message to a conversation."""
        message = {
            "id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "type": message_type,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }

        # Store in MongoDB
        self.messages.insert_one(message)

        # Cache in Redis for active conversations
        redis_key = f"conv:{conversation_id}:messages"
        await self.redis_client.lpush(redis_key, json.dumps(message, cls=MongoJSONEncoder))
        await self.redis_client.expire(redis_key, self.message_ttl)

        return message

    async def get_conversation_messages(self, conversation_id: str,
                                     limit: int = 50,
                                     use_cache: bool = True) -> List[Dict]:
        """Get messages for a conversation."""
        if use_cache:
            # Try Redis first
            redis_key = f"conv:{conversation_id}:messages"
            cached = await self.redis_client.lrange(redis_key, 0, limit - 1)
            if cached:
                return [json.loads(msg) for msg in cached]

        # Fallback to MongoDB
        messages = list(self.messages.find(
            {"conversation_id": conversation_id},
            sort=[("created_at", -1)],
            limit=limit
        ))

        # Update cache if needed
        if messages and use_cache:
            redis_key = f"conv:{conversation_id}:messages"
            pipeline = self.redis_client.pipeline()
            for msg in reversed(messages):  # Maintain chronological order
                pipeline.lpush(redis_key, json.dumps(msg, cls=MongoJSONEncoder))
            pipeline.expire(redis_key, self.message_ttl)
            await pipeline.execute()

        return messages

    async def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation and all its messages."""
        # Delete from MongoDB
        self.conversations.delete_one({"id": conversation_id})
        self.messages.delete_many({"conversation_id": conversation_id})

        # Delete from Redis
        redis_key = f"conv:{conversation_id}:messages"
        await self.redis_client.delete(redis_key)
