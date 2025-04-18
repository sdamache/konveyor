output "bot_service_id" {
  description = "Azure Bot Service ID"
  value       = azurerm_bot_service_azure_bot.bot.id
}

output "bot_service_name" {
  description = "Azure Bot Service name"
  value       = azurerm_bot_service_azure_bot.bot.name
}

output "endpoint" {
  description = "Azure Bot Service endpoint"
  value       = azurerm_bot_service_azure_bot.bot.endpoint
}

output "slack_channel_id" {
  description = "Slack Channel resource ID"
  value       = azurerm_bot_channel_slack.slack_channel.id
}
