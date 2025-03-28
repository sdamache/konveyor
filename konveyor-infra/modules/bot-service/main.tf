resource "azurerm_bot_service_azure_bot" "bot" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku
  microsoft_app_id    = var.microsoft_app_id
  tags                = var.tags
}

resource "azurerm_bot_channel_slack" "slack_channel" {
  bot_name            = azurerm_bot_service_azure_bot.bot.name
  location            = "global"
  resource_group_name = var.resource_group_name
  
  slack_channel {
    client_id         = var.slack_client_id
    client_secret     = var.slack_client_secret
    verification_token = var.slack_signing_secret
    landing_page_url  = "https://${var.name}.azurewebsites.net/api/messages"
  }
}
