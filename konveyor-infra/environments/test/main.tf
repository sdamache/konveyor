# Generate a random suffix for resources that need global uniqueness
resource "random_id" "search_suffix" {
  byte_length = 4 # Creates an 8-character hex string
}

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
  source                       = "../../modules/openai"
  name                         = "${var.prefix}-test-openai"
  resource_group_name          = module.resource_group.name
  location                     = var.location
  sku_name                     = "S0"

  # Chat (GPT) model deployment
  deploy_model                 = var.deploy_model
  model_name                   = var.openai_model_name
  model_version                = var.openai_model_version
  capacity                     = var.openai_capacity

  # Embeddings model deployment
  deploy_embeddings            = var.deploy_embeddings
  embeddings_model_name        = var.openai_embeddings_model_name
  embeddings_model_version     = var.openai_embeddings_model_version
  embeddings_capacity          = var.openai_embeddings_capacity

  tags                         = var.tags
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

module "cognitive_search" {
  count               = var.deploy_search_service ? 1 : 0
  source              = "../../modules/cognitive-search"
  name                = "${var.prefix}-test-search"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku                 = "standard" # Set your desired SKU
  partition_count     = 1
  tags                = var.tags
  random_suffix       = random_id.search_suffix.hex
}

module "app_service" {
  source              = "../../modules/app-service"
  name                = "${var.prefix}-test-app"
  resource_group_name = module.resource_group.name
  location            = "centralus" # Override default location (eastus) for App Service quota
  tags                = var.tags
  app_service_plan_sku = "B1" # Use Basic tier instead of Free due to quota limits

  # Docker/GHCR configuration
  docker_registry_url      = "https://ghcr.io"
  docker_image_name        = "ghcr.io/${var.github_repository}" # Use the same repository path as in GitHub Actions
  docker_image_tag         = var.docker_image_tag # Use the tag passed from GitHub Actions or default to latest
  docker_registry_username = var.docker_registry_username # GitHub username
  docker_registry_password = "${var.GHCR_PAT}" # GitHub PAT

  app_settings = merge(
    {
      # Django settings
      DJANGO_SECRET_KEY        = var.DJANGO_SECRET_KEY
      DJANGO_SETTINGS_MODULE   = var.django_settings_module
      DATABASE_URL             = var.database_url

      # Azure Storage
      AZURE_STORAGE_CONNECTION_STRING = module.storage.storage_connection_string

      # Azure OpenAI settings
      AZURE_OPENAI_ENDPOINT    = var.AZURE_OPENAI_ENDPOINT != "https://example.openai.azure.com" ? var.AZURE_OPENAI_ENDPOINT : module.openai.cognitive_account_endpoint
      AZURE_OPENAI_KEY         = var.AZURE_OPENAI_API_KEY != "dummy-key" ? var.AZURE_OPENAI_API_KEY : module.openai.cognitive_account_primary_key
      AZURE_OPENAI_API_KEY     = var.AZURE_OPENAI_API_KEY != "dummy-key" ? var.AZURE_OPENAI_API_KEY : module.openai.cognitive_account_primary_key
      AZURE_OPENAI_API_VERSION = var.openai_api_version
      AZURE_OPENAI_CHAT_DEPLOYMENT = var.openai_chat_deployment
      AZURE_OPENAI_EMBEDDING_DEPLOYMENT = var.openai_embedding_deployment
      SKIP_AZURE_OPENAI_VALIDATION = tostring(var.skip_openai_validation)

      # Azure Document Intelligence
      DOCUMENT_INTELLIGENCE_ENDPOINT = module.document_intelligence.endpoint
      DOCUMENT_INTELLIGENCE_KEY      = module.document_intelligence.primary_key

      # Azure Search
      AZURE_SEARCH_INDEX_NAME  = var.search_index_name

      # App Service settings
      WEBSITES_ENABLE_APP_SERVICE_STORAGE = "true"
      WEBSITES_PORT            = "8000"
      WEBSITE_HTTPLOGGING_RETENTION_DAYS = "3"
      WEBSITES_CONTAINER_START_TIME_LIMIT = "600"

      # Docker settings
      DOCKER_ENABLE_CI         = "true"
    },
    # Conditionally add search service settings if deployed
    var.deploy_search_service ? {
      AZURE_COGSEARCH_ENDPOINT = module.cognitive_search[0].search_service_endpoint
      AZURE_COGSEARCH_KEY      = module.cognitive_search[0].search_service_primary_key
    } : {
      # Placeholder values when search service is not deployed
      AZURE_COGSEARCH_ENDPOINT = "disabled"
      AZURE_COGSEARCH_KEY      = "disabled"
    }
  )
}

# module "bot_service" {
#   source              = "../../modules/bot-service"
#   name                = "${var.prefix}-test-bot"
#   prefix              = var.prefix
#   resource_group_name = module.resource_group.name
#   location            = "global"
#   sku                 = "F0"
#   microsoft_app_id    = var.microsoft_app_id
#   microsoft_app_password = var.microsoft_app_password
#   slack_client_id     = var.slack_client_id
#   slack_client_secret = var.slack_client_secret
#   slack_signing_secret = var.slack_signing_secret
#   tags                = var.tags
# }

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
