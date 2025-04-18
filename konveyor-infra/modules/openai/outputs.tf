output "cognitive_account_id" {
  description = "Azure OpenAI Service cognitive account ID"
  value       = azurerm_cognitive_account.openai.id
}

output "cognitive_account_name" {
  description = "Azure OpenAI Service cognitive account name"
  value       = azurerm_cognitive_account.openai.name
}

output "cognitive_account_endpoint" {
  description = "Azure OpenAI Service cognitive account endpoint"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "cognitive_account_primary_key" {
  description = "Azure OpenAI Service cognitive account primary key"
  value       = azurerm_cognitive_account.openai.primary_access_key
  sensitive   = true
}

output "deployment_id" {
  description = "Azure OpenAI Service deployment ID"
  value       = var.deploy_model ? azurerm_cognitive_deployment.gpt_deployment[0].id : "deployment-not-created"
}

output "embeddings_deployment_id" {
  description = "ID of the embeddings model deployment"
  value       = var.deploy_embeddings ? azurerm_cognitive_deployment.embeddings[0].id : null
}

output "embeddings_deployment_name" {
  description = "Name of the embeddings model deployment"
  value       = var.deploy_embeddings ? azurerm_cognitive_deployment.embeddings[0].name : null
}
