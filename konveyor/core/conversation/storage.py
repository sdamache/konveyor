"""
Azure storage utilities for Konveyor.

This module provides a persistent storage implementation of the ConversationInterface
using Azure Cosmos DB and Redis. It's designed for production use where persistence
and scalability are required.

**IMPORTANT: REDUNDANCY NOTICE**
This conversation storage implementation has potential integration points with the
Semantic Kernel implementation in konveyor/skills/. Specifically:

1. The ChatSkill in konveyor/skills/ChatSkill.py manages conversation history in memory,
   but could be enhanced to use this storage manager for persistence.

2. Future work in Task #3 (Agent Orchestration) should consider integrating the
   Semantic Kernel framework with this storage system to avoid duplicating conversation
   management logic.
"""

import asyncio
import datetime as dt
import json
import logging
import uuid
from datetime import datetime, timedelta
from json import JSONEncoder
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as redis
from pymongo import MongoClient

from konveyor.core.conversation.interface import ConversationInterface


class MongoJSONEncoder(JSONEncoder):
    """JSON encoder that can handle MongoDB ObjectId."""

    def default(self, obj):
        if hasattr(obj, "__str__") and (
            obj.__class__.__name__ == "ObjectId"  # noqa: E501
        ):
            return str(obj)
        return super().default(obj)


class AzureStorageManager(ConversationInterface):
    """
    Persistent implementation of the ConversationInterface using Azure services.

    This class provides a persistent storage implementation for conversations and messages  # noqa: E501
    using Azure Cosmos DB for long-term storage and Redis for caching. It's designed for
    production use where persistence and scalability are required.
    """

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
            if not mongo_conn_str.startswith("mongodb://"):
                raise ValueError("Connection string must start with 'mongodb://'")

            # Extract the username and key
            auth_part = mongo_conn_str[len("mongodb://") :]  # Remove protocol
            first_colon = auth_part.find(":")
            if first_colon == -1:
                raise ValueError("Missing password in connection string")

            username = auth_part[:first_colon]  # noqa: F841
            rest = auth_part[first_colon + 1 :]

            # Find the end of the key (before @)
            at_sign = rest.find("@")
            if at_sign == -1:
                raise ValueError("Invalid MongoDB connection string format")

            key = rest[:at_sign]
            host_part = rest[at_sign + 1 :]

            # Split host part before any query parameters or path
            host = host_part.split("?")[0].split("/")[0]

            # Build Cosmos DB connection string
            # For MongoDB API, we need to use the mongo.cosmos.azure.com endpoint
            if not host.endswith("mongo.cosmos.azure.com"):
                host = host.replace("documents.azure.com", "mongo.cosmos.azure.com")
                if ":443" in host:
                    host = host.replace(":443", ":10255")
                elif not ":" in host:  # noqa: E713
                    host = f"{host}:10255"

            # Return in Cosmos DB format
            return f"AccountEndpoint=https://{host};AccountKey={key}"

        except Exception as e:
            logging.error(f"Failed to parse MongoDB connection string: {str(e)}")
            # Log a redacted version of the connection string for debugging
            redacted = mongo_conn_str.replace(mongo_conn_str.split("@")[0], "***")
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
                    collation={"locale": "en", "strength": 2},
                )

            if "messages" not in self.db.list_collection_names():
                self.db.create_collection(
                    "messages",
                    # Shard key for messages
                    collation={"locale": "en", "strength": 2},
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
        await self.cosmos_client.close()
        await self.redis_client.close()

    async def initialize(self):
        """Initialize the storage manager."""
        await self._ensure_database_exists()

    def __init__(self, cosmos_connection_str: str, redis_connection_str: str):
        # MongoDB setup
        if not cosmos_connection_str:
            raise ValueError("MongoDB connection string is required")

        # Convert Cosmos format to MongoDB if needed
        if cosmos_connection_str.startswith("AccountEndpoint="):
            # Extract host and key from Cosmos format
            parts = cosmos_connection_str.split(";")
            endpoint = parts[0].replace("AccountEndpoint=https://", "")
            key = parts[1].replace("AccountKey=", "")

            # Convert to MongoDB format
            cosmos_connection_str = f"mongodb://{key}@{endpoint}"

        elif not cosmos_connection_str.startswith("mongodb://"):
            raise ValueError("Invalid connection string format")

        # Initialize MongoDB client
        self.mongo_client = MongoClient(
            cosmos_connection_str,
            ssl=True,
            tls=True,
            tlsAllowInvalidCertificates=True,  # For testing only
            retryWrites=False,  # Required for Cosmos DB
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=10000,  # 10 second timeout
            socketTimeoutMS=10000,  # 10 second timeout
        )

        # Redis setup
        if not redis_connection_str:
            raise ValueError("Redis connection string is required")
        self.redis_client = redis.from_url(
            redis_connection_str,
            ssl_cert_reqs=None,  # Skip SSL verification for testing
        )
        self.message_ttl = timedelta(
            days=1
        )  # Keep active conversations for 1 day in Redis

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
            "updated_at": datetime.now(dt.timezone.utc),
        }
        self.conversations.insert_one(conversation)
        return conversation

    async def add_message(
        self,
        conversation_id: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """Add a message to a conversation."""
        message = {
            "id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "type": message_type,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }

        # Store in MongoDB
        self.messages.insert_one(message)

        # Cache in Redis for active conversations
        redis_key = f"conv:{conversation_id}:messages"
        await self.redis_client.lpush(
            redis_key, json.dumps(message, cls=MongoJSONEncoder)
        )
        await self.redis_client.expire(redis_key, self.message_ttl)

        return message

    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        skip: int = 0,
        include_metadata: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a conversation.

        Args:
            conversation_id: Identifier for the conversation
            limit: Maximum number of messages to retrieve
            skip: Number of messages to skip
            include_metadata: Whether to include message metadata

        Returns:
            List of message dictionaries
        """
        # Try Redis first
        redis_key = f"conv:{conversation_id}:messages"
        cached = await self.redis_client.lrange(redis_key, skip, skip + limit - 1)
        if cached:
            messages = [json.loads(msg) for msg in cached]

            # Remove metadata if not requested
            if not include_metadata:
                for message in messages:
                    message.pop("metadata", None)

            return messages

        # Fallback to MongoDB
        messages = list(
            self.messages.find(
                {"conversation_id": conversation_id},
                sort=[("created_at", -1)],
                skip=skip,
                limit=limit,
            )
        )

        # Update cache if needed
        if messages:
            redis_key = f"conv:{conversation_id}:messages"
            pipeline = self.redis_client.pipeline()
            for msg in reversed(messages):  # Maintain chronological order
                pipeline.lpush(redis_key, json.dumps(msg, cls=MongoJSONEncoder))
            pipeline.expire(redis_key, self.message_ttl)
            await pipeline.execute()

        # Remove metadata if not requested
        if not include_metadata:
            for message in messages:
                message.pop("metadata", None)

        return messages

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: Identifier for the conversation

        Returns:
            True if the conversation was deleted, False otherwise
        """
        # Check if conversation exists
        conversation = self.conversations.find_one({"id": conversation_id})
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")  # noqa: F821
            return False

        # Delete from MongoDB
        self.conversations.delete_one({"id": conversation_id})
        self.messages.delete_many({"conversation_id": conversation_id})

        # Delete from Redis
        redis_key = f"conv:{conversation_id}:messages"
        await self.redis_client.delete(redis_key)

        logger.debug(f"Deleted conversation: {conversation_id}")  # noqa: F821
        return True

    async def update_conversation_metadata(
        self, conversation_id: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update the metadata for a conversation.

        Args:
            conversation_id: Identifier for the conversation
            metadata: New metadata for the conversation

        Returns:
            Updated conversation dictionary
        """
        # Check if conversation exists
        conversation = self.conversations.find_one({"id": conversation_id})
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")  # noqa: F821
            raise ValueError(f"Conversation not found: {conversation_id}")

        # Update the metadata
        current_metadata = conversation.get("metadata", {})
        current_metadata.update(metadata)

        # Update in MongoDB
        self.conversations.update_one(
            {"id": conversation_id},
            {
                "$set": {
                    "metadata": current_metadata,
                    "updated_at": datetime.now(dt.timezone.utc),
                }
            },
        )

        # Get the updated conversation
        updated_conversation = self.conversations.find_one({"id": conversation_id})

        # Debug log for metadata update
        print(f"Updated metadata for conversation: {conversation_id}")  # noqa: E501
        return updated_conversation

    async def get_user_conversations(
        self, user_id: str, limit: int = 10, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get conversations for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of conversations to retrieve
            skip: Number of conversations to skip

        Returns:
            List of conversation dictionaries
        """
        # Query MongoDB for conversations by user_id
        conversations = list(
            self.conversations.find(
                {"user_id": user_id}, sort=[("updated_at", -1)], skip=skip, limit=limit
            )
        )

        # Debug log for retrieved conversations
        print(
            f"Retrieved {len(conversations)} conversations for user {user_id}"
        )  # noqa: E501
        return conversations

    async def get_conversation_context(
        self,
        conversation_id: str,
        format: str = "string",
        max_messages: Optional[int] = None,
    ) -> Union[str, List[Dict[str, Any]]]:
        """
        Get the conversation context in the specified format.

        Args:
            conversation_id: Identifier for the conversation
            format: Format of the context ('string', 'dict', 'openai')
            max_messages: Maximum number of messages to include in the context

        Returns:
            Conversation context in the specified format
        """
        # Check if conversation exists
        conversation = self.conversations.find_one({"id": conversation_id})
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")  # noqa: F821
            return "" if format == "string" else []

        # Get messages
        limit = max_messages if max_messages is not None else 50
        messages = await self.get_conversation_messages(
            conversation_id=conversation_id, limit=limit, include_metadata=True
        )

        # Sort by created_at (oldest first)
        sorted_messages = sorted(messages, key=lambda m: m["created_at"])

        if format == "string":
            # Format as a string
            context = ""
            for message in sorted_messages:
                role = message["type"].capitalize()
                content = message["content"]
                context += f"{role}: {content}\n"
            return context.strip()

        elif format == "dict":
            # Return as a list of dictionaries
            return sorted_messages

        elif format == "openai":
            # Format for OpenAI API
            openai_messages = []
            for message in sorted_messages:
                role = message["type"]
                # Map message types to OpenAI roles
                if role == "user":
                    openai_role = "user"
                elif role == "assistant":
                    openai_role = "assistant"
                elif role == "system":
                    openai_role = "system"
                else:
                    # Default to user for unknown roles
                    openai_role = "user"

                openai_messages.append(
                    {"role": openai_role, "content": message["content"]}
                )
            return openai_messages

        else:
            logger.warning(f"Unsupported format: {format}")  # noqa: F821
            return "" if format == "string" else []
