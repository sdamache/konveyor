output "cognitive_account_id" {
  description = "Azure OpenAI Service cognitive account ID"
  value       = azurerm_cognitive_account.openai.id
}

output "deployment_id" {
  description = "Azure OpenAI Service deployment ID"
  value       = azurerm_cognitive_deployment.gpt_deployment.id
}
