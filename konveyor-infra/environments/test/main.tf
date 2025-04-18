module "resource_group" {
  source   = "../../modules/resource-group"
  name     = "${var.prefix}-test-rg"
  location = var.location
  tags     = var.tags
}

module "key_vault" {
  source              = "../../modules/key-vault"
  name                = "${var.prefix}-test-kv"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

module "openai" {
  source              = "../../modules/openai"
  name                = "${var.prefix}-test-openai"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku_name            = "S0"
  model_name          = "gpt-4o"
  model_version       = "2024-05-13" # Use valid YYYY-MM-DD format
  capacity            = 1
  tags                = var.tags
}

module "document_intelligence" {
  source              = "../../modules/document-intelligence"
  name                = "${var.prefix}-test-docint" # Added -test suffix
  resource_group_name = module.resource_group.name
  location            = var.location
  sku_name            = "S0" # Assuming S0 is okay for test
  tags                = var.tags
}

module "storage" {
  source              = "../../modules/storage"
  name                = "${var.prefix}teststorage" # Added test infix
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

# RAG infrastructure (includes Redis Cache) - Temporarily commented out for faster testing
# module "rag" {
#   source              = "../../modules/rag"
#   prefix              = var.prefix
#   environment         = "test" # Explicitly set environment for RAG module if needed
#   resource_group_name = module.resource_group.name
#   location            = var.location
#   tags                = merge(var.tags, {
#     component = "rag"
#   })
# }

module "cognitive_search" {
  source              = "../../modules/cognitive-search"
  name                = "${var.prefix}-test-search"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku                 = "basic"
  replica_count       = 1
  partition_count     = 1
  tags                = var.tags
}

module "bot_service" {
  source              = "../../modules/bot-service"
  name                = "${var.prefix}-test-bot"
  prefix              = var.prefix
  resource_group_name = module.resource_group.name
  location            = "global"
  sku                 = "F0"
  microsoft_app_id    = var.microsoft_app_id
  microsoft_app_password = var.microsoft_app_password
  slack_client_id     = var.slack_client_id
  slack_client_secret = var.slack_client_secret
  slack_signing_secret = var.slack_signing_secret
  tags                = var.tags
}
