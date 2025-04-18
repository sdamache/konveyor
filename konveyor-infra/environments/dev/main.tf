module "resource_group" {
  source   = "../../modules/resource-group"
  name     = "${var.prefix}-dev-rg"
  location = var.location
  tags     = var.tags
}

module "key_vault" {
  source              = "../../modules/key-vault"
  name                = "${var.prefix}-dev-kv"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

module "openai" {
  source              = "../../modules/openai"
  name                = "${var.prefix}-dev-openai"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku_name            = "S0"
  model_name          = "gpt-4o"
  model_version       = "1106-Preview"
  capacity            = 1
  tags                = var.tags
}

module "cognitive_search" {
  source              = "../../modules/cognitive-search"
  name                = "${var.prefix}-dev-search"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku                 = "basic"
  replica_count       = 1
  partition_count     = 1
  tags                = var.tags
}

module "bot_service" {
  source              = "../../modules/bot-service"
  name                = "${var.prefix}-dev-bot"
  resource_group_name = module.resource_group.name
  location            = "global"
  sku                 = "F0"
  microsoft_app_id    = var.microsoft_app_id
  tags                = var.tags
}

module "document_intelligence" {
  source              = "../../modules/document-intelligence"
  name                = "${var.prefix}-dev-docint"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku_name            = "S0"
  tags                = var.tags
}
