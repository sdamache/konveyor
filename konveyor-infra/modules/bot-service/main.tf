resource "azurerm_bot_service_azure_bot" "bot" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku
  microsoft_app_id    = var.microsoft_app_id
  tags                = var.tags
}
