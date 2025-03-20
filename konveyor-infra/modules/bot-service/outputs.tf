output "bot_service_id" {
  description = "Azure Bot Service ID"
  value       = azurerm_bot_service_azure_bot.bot.id
}

output "bot_service_name" {
  description = "Azure Bot Service name"
  value       = azurerm_bot_service_azure_bot.bot.name
}
