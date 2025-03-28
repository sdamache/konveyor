resource "azurerm_cognitive_account" "openai" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  kind                = "OpenAI"
  sku_name            = var.sku_name
  tags                = var.tags

  identity {
    type = "SystemAssigned"
  }

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

  depends_on = [azurerm_cognitive_account.openai]
}

resource "azurerm_cognitive_deployment" "embeddings" {
  count                = var.deploy_embeddings ? 1 : 0
  name                 = "embeddings"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = var.embeddings_model_name
    version = var.embeddings_model_version
  }

  scale {
    type     = "Standard"
    capacity = var.embeddings_capacity
  }


  depends_on = [
    azurerm_cognitive_account.openai,
    azurerm_cognitive_deployment.gpt_deployment  # Ensure GPT deploys first if both are being deployed
  ]
}

locals {
  timeouts = {
    create = "1h"
    update = "1h"
    delete = "30m"
  }
}
