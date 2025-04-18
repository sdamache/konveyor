module "resource_group" {
  source   = "./modules/resource-group"
  name     = "${var.prefix}-rg"
  location = var.location
  tags     = var.tags
}

module "key_vault" {
  source              = "./modules/key-vault"
  name                = "${var.prefix}-kv"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

# OpenAI service (uncommented for testing)
module "openai" {
  source              = "./modules/openai"
  name                = "${var.prefix}-openai"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku_name            = var.openai_sku_name
  
  # GPT model configuration
  model_name          = var.openai_model_name
  model_version       = var.openai_model_version
  capacity            = var.openai_capacity
  deploy_model        = var.openai_deploy_model
  
  # Embeddings model configuration
  deploy_embeddings        = var.openai_deploy_embeddings
  embeddings_model_name    = var.openai_embeddings_model_name
  embeddings_model_version = var.openai_embeddings_model_version
  embeddings_capacity      = var.openai_embeddings_capacity
  
  tags                = var.tags
}

# Cognitive Search service (uncommented for testing)
module "cognitive_search" {
  source              = "./modules/cognitive-search"
  name                = "${var.prefix}-search"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku                 = "basic"
  replica_count       = 1
  partition_count     = 1
  tags                = var.tags
}

module "bot_service" {
  source              = "./modules/bot-service"
  name                = "${var.prefix}-bot"
  prefix              = var.prefix
  resource_group_name = module.resource_group.name
  location            = "global"
  sku                 = "F0"
  microsoft_app_id    = var.microsoft_app_id
  slack_client_id     = var.slack_client_id
  slack_client_secret = var.slack_client_secret
  slack_signing_secret = var.slack_signing_secret
  tags                = var.tags
}

module "document_intelligence" {
  source              = "./modules/document-intelligence"
  name                = "${var.prefix}-docint"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku_name            = "S0"
  tags                = var.tags
}

module "storage" {
  source              = "./modules/storage"
  name                = "${var.prefix}storage"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

# RAG infrastructure (includes Redis Cache - uncommented for testing)
module "rag" {
  source              = "./modules/rag"
  prefix              = var.prefix
  environment         = var.environment
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = merge(var.tags, {
    component = "rag"
  })
}
