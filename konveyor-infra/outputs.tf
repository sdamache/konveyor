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
  value       = module.key_vault.id
}

output "key_vault_name" {
  description = "Key Vault name"
  value       = module.key_vault.name
}

output "openai_id" {
  description = "Azure OpenAI Service ID"
  value       = module.openai.id
}

output "openai_name" {
  description = "Azure OpenAI Service name"
  value       = module.openai.name
}

output "cognitive_search_id" {
  description = "Azure Cognitive Search Service ID"
  value       = module.cognitive_search.id
}

output "cognitive_search_name" {
  description = "Azure Cognitive Search Service name"
  value       = module.cognitive_search.name
}

output "bot_service_id" {
  description = "Azure Bot Service ID"
  value       = module.bot_service.id
}

output "bot_service_name" {
  description = "Azure Bot Service name"
  value       = module.bot_service.name
}
