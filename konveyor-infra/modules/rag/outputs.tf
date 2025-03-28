output "cosmos_connection_string" {
  description = "Cosmos DB connection string"
  value       = azurerm_cosmosdb_account.konveyor_db.connection_strings[0]
  sensitive   = true
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = "rediss://:${azurerm_redis_cache.konveyor_cache.primary_access_key}@${azurerm_redis_cache.konveyor_cache.hostname}:${azurerm_redis_cache.konveyor_cache.ssl_port}/0"
  sensitive   = true
}

output "cosmos_database_name" {
  description = "Cosmos DB database name"
  value       = azurerm_cosmosdb_mongo_database.konveyor_conversations.name
}

output "cosmos_conversations_collection" {
  description = "Cosmos DB conversations collection name"
  value       = azurerm_cosmosdb_mongo_collection.conversations.name
}

output "cosmos_messages_collection" {
  description = "Cosmos DB messages collection name"
  value       = azurerm_cosmosdb_mongo_collection.messages.name
}
