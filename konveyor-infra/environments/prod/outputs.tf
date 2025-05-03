# Outputs specific to the 'prod' environment

output "cognitive_search_endpoint" {
  description = "Production Azure Cognitive Search Service endpoint"
  value       = module.cognitive_search.search_service_endpoint
}

output "cognitive_search_primary_key" {
  description = "Production Azure Cognitive Search Service primary key"
  value       = module.cognitive_search.search_service_primary_key
  sensitive   = true
}

output "openai_endpoint" {
  description = "Production Azure OpenAI Service endpoint"
  value       = module.openai.cognitive_account_endpoint
}

output "openai_primary_key" {
  description = "Production Azure OpenAI Service primary key"
  value       = module.openai.cognitive_account_primary_key
  sensitive   = true
}

output "openai_embeddings_deployment_name" {
  description = "Production Azure OpenAI Embeddings Deployment Name"
  value       = module.openai.embeddings_deployment_name
}

output "document_intelligence_endpoint" {
  description = "Production Document Intelligence Service endpoint"
  value       = module.document_intelligence.endpoint
}

output "document_intelligence_primary_key" {
  description = "Production Document Intelligence Service primary key"
  value       = module.document_intelligence.primary_key
  sensitive   = true
}

output "storage_connection_string" {
  description = "Production Storage Account connection string"
  value       = module.storage.storage_connection_string
  sensitive   = true
}

output "bot_service_endpoint" {
  description = "Production Azure Bot Service endpoint"
  value       = module.bot_service.endpoint
}

output "bot_service_slack_channel_id" {
  description = "Production Azure Bot Service Slack Channel ID"
  value       = module.bot_service.slack_channel_id
}

output "app_service_name" {
  description = "Production Azure App Service name"
  value       = module.app_service.name
}

output "app_service_default_site_hostname" {
  description = "Production Azure App Service default site hostname"
  value       = module.app_service.default_site_hostname
}
