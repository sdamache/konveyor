output "resource_group_id" {
  description = "Resource group ID"
  value       = module.resource_group.id
}

output "resource_group_name" {
  description = "Resource group name"
  value       = module.resource_group.name
}

output "key_vault_id" {
  description = "Key Vault ID"
  value       = module.key_vault.key_vault_id
}

output "key_vault_name" {
  description = "Key Vault name"
  value       = module.key_vault.key_vault_name
}

# Commented out OpenAI outputs (cost optimization)
# output "openai_id" {
#   description = "Azure OpenAI Service ID"
#   value       = module.openai.cognitive_account_id
# }

# output "openai_name" {
#   description = "Azure OpenAI Service name"
#   value       = module.openai.cognitive_account_name
# }

# Commented out Cognitive Search outputs (cost optimization)
# output "cognitive_search_id" {
#   description = "Azure Cognitive Search Service ID"
#   value       = module.cognitive_search.search_service_id
# }

# output "cognitive_search_name" {
#   description = "Azure Cognitive Search Service name"
#   value       = module.cognitive_search.search_service_name
# }

output "bot_service_id" {
  description = "Azure Bot Service ID"
  value       = module.bot_service.bot_service_id
}

output "bot_service_name" {
  description = "Azure Bot Service name"
  value       = module.bot_service.bot_service_name
}

output "document_intelligence_id" {
  description = "Document Intelligence Service ID"
  value       = module.document_intelligence.id
}

output "document_intelligence_endpoint" {
  description = "Document Intelligence Service endpoint"
  value       = module.document_intelligence.endpoint
}

output "storage_account_id" {
  description = "Storage Account ID"
  value       = module.storage.storage_account_id
}

output "storage_account_name" {
  description = "Storage Account name"
  value       = module.storage.storage_account_name
}

output "storage_connection_string" {
  description = "Storage Account connection string for environment configuration"
  value       = module.storage.storage_connection_string
  sensitive   = true
}

output "storage_container_name" {
  description = "Storage container name for environment configuration"
  value       = module.storage.storage_container_name
}

# Commented out OpenAI Embeddings outputs (cost optimization)
# output "openai_embeddings_deployment_id" {
#   description = "Azure OpenAI Embeddings deployment ID"
#   value       = module.openai.embeddings_deployment_id
# }

# output "openai_embeddings_deployment_name" {
#   description = "Azure OpenAI Embeddings deployment name"
#   value       = module.openai.embeddings_deployment_name
# }
