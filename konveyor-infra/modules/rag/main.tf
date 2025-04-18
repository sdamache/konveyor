# RAG infrastructure module for Konveyor
# Provisions Cosmos DB and Redis Cache for conversation storage

# Cosmos DB for long-term storage (Cost-optimized)
resource "azurerm_cosmosdb_account" "konveyor_db" {
  name                = "${var.prefix}-cosmos-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  offer_type         = "Standard"
  kind               = "MongoDB"  # Using MongoDB API

  consistency_policy {
    consistency_level = "Eventual"  # Most cost-effective
  }

  geo_location {
    location          = var.location
    failover_priority = 0
  }

  capabilities {
    name = "EnableMongo"
  }

  capabilities {
    name = "EnableServerless"  # Pay per request, good for hackathon
  }

  # Cost optimization settings
  backup {
    type = "Periodic"
    interval_in_minutes = 1440  # Daily backup
    retention_in_hours = 48     # 2 days retention
  }

  tags = var.tags
}

# Redis Cache for active conversations (Basic SKU)
resource "azurerm_redis_cache" "konveyor_cache" {
  name                = "${var.prefix}-redis-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  capacity            = 0        # Smallest size
  family              = "C"      # Basic/Standard family
  sku_name           = "Basic"  # Most cost-effective tier
  # enable_non_ssl_port = false # This argument is no longer supported/needed; SSL is mandatory

  redis_configuration {
    maxmemory_policy = "volatile-lru"  # Evict least recently used keys first
  }

  tags = var.tags
}

# Cosmos DB Database (Serverless)
resource "azurerm_cosmosdb_mongo_database" "konveyor_conversations" {
  name                = "${var.prefix}-db"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.konveyor_db.name
}

# Cosmos DB Collections with optimized indexes
resource "azurerm_cosmosdb_mongo_collection" "conversations" {
  name                = "conversations"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.konveyor_db.name
  database_name       = azurerm_cosmosdb_mongo_database.konveyor_conversations.name

  # Primary key index
  index {
    keys   = ["_id"]
    unique = true
  }

  # User conversations index
  index {
    keys = ["user_id", "created_at"]
  }

  # Status and type index
  index {
    keys = ["status", "conversation_type"]
  }

  # Project and repository index
  index {
    keys = ["project_id", "repository_id"]
  }
}

resource "azurerm_cosmosdb_mongo_collection" "messages" {
  name                = "messages"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.konveyor_db.name
  database_name       = azurerm_cosmosdb_mongo_database.konveyor_conversations.name

  # Primary key index
  index {
    keys   = ["_id"]
    unique = true
  }

  # Conversation timeline index
  index {
    keys = ["conversation_id", "created_at"]
  }

  # Message type and role index
  index {
    keys = ["message_type", "role"]
  }
}
