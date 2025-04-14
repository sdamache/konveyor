# Outputs specific to the 'test' environment

output "cognitive_search_endpoint" {
  description = "Test Azure Cognitive Search Service endpoint"
  value       = module.cognitive_search.search_service_endpoint
}

output "cognitive_search_primary_key" {
  description = "Test Azure Cognitive Search Service primary key"
  value       = module.cognitive_search.search_service_primary_key
  sensitive   = true
}

output "openai_endpoint" {
  description = "Test Azure OpenAI Service endpoint"
  value       = module.openai.cognitive_account_endpoint
}

output "openai_primary_key" {
  description = "Test Azure OpenAI Service primary key"
  value       = module.openai.cognitive_account_primary_key
  sensitive   = true
}

output "openai_embeddings_deployment_name" {
  description = "Test Azure OpenAI Embeddings Deployment Name"
  value       = module.openai.embeddings_deployment_name
}

output "document_intelligence_endpoint" {
  description = "Test Document Intelligence Service endpoint"
  value       = module.document_intelligence.endpoint
}

output "document_intelligence_primary_key" {
  description = "Test Document Intelligence Service primary key"
  value       = module.document_intelligence.primary_key
  sensitive   = true
}

output "storage_connection_string" {
  description = "Test Storage Account connection string"
  value       = module.storage.storage_connection_string
  sensitive   = true
}

# Optional: Add outputs for RAG module if/when uncommented
# output "cosmos_connection_string" {
#   description = "Test Cosmos DB connection string"
#   value       = module.rag.cosmos_connection_string
#   sensitive   = true
# }
#
# output "redis_connection_string" {
#   description = "Test Redis connection string"
#   value       = module.rag.redis_connection_string
#   sensitive   = true
# }