resource "azurerm_cognitive_account" "openai" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  kind                = "OpenAI"
  sku_name            = var.sku_name
  tags                = var.tags
}

resource "azurerm_cognitive_deployment" "gpt_deployment" {
  count                = var.deploy_model ? 1 : 0
  name                 = "gpt-deployment"
  cognitive_account_id = azurerm_cognitive_account.openai.id
  model {
    format  = "OpenAI"
    name    = var.model_name
    version = var.model_version
  }
  scale {
    type     = "GlobalStandard"
    capacity = var.capacity
  }
}
