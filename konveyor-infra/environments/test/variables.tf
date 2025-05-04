variable "prefix" {
  description = "Prefix for resource names in the test environment"
  type        = string
  default     = "konveyor"
}

variable "location" {
  description = "Azure region for the test environment"
  type        = string
  default     = "eastus"
}

variable "tags" {
  description = "Tags to apply to resources in the test environment"
  type        = map(string)
  default     = {
    project     = "konveyor"
    environment = "test" # Ensure this matches the environment context
  }
}

variable "microsoft_app_id" {
  description = "Microsoft App ID for Azure Bot Service in the test environment"
  type        = string
  default     = "c8218a52-681c-4df2-b558-5fa8e5067b43" # Use the same default or a test-specific one if available
}

variable "microsoft_app_password" {
  description = "Microsoft App Password for the Azure Bot Service in the test environment"
  type        = string
  sensitive   = true
}

variable "slack_client_id" {
  description = "Slack Client ID for bot channel configuration in the test environment"
  type        = string
}

variable "slack_client_secret" {
  description = "Slack Client Secret for bot channel configuration in the test environment"
  type        = string
  sensitive   = true
}

variable "slack_signing_secret" {
  description = "Slack Signing Secret for bot channel configuration in the test environment"
  type        = string
  sensitive   = true
}

variable "deploy_model" {
  description = "Deploy model in the test environment"
  type        = string
  default     = "true"
}

variable "openai_model_name" {
  description = "OpenAI model name in the test environment"
  type        = string
  default     = "gpt-4o"
}
variable "openai_model_version" {
  description = "OpenAI model version in the test environment"
  type        = string
  default     = "2024-05-13"
}

variable "openai_capacity" {
  description = "OpenAI capacity in the test environment"
  type        = string
  default     = "10"
}

variable "deploy_embeddings" {
  description = "Deploy embeddings model in the test environment"
  type        = bool
  default     = true
}

variable "openai_embeddings_model_name" {
  description = "OpenAI embeddings model name in the test environment"
  type        = string
  default     = "text-embedding-ada-002"
}

variable "openai_embeddings_model_version" {
  description = "OpenAI embeddings model version in the test environment"
  type        = string
  default     = "2"
}

variable "openai_embeddings_capacity" {
  description = "OpenAI embeddings model capacity in the test environment"
  type        = number
  default     = 10
}

# Note: Other variables like openai_sku_name, openai_model_name etc. are defined
# in the root variables.tf and their defaults will be used unless overridden here
# or in a .tfvars file (which we are not using in the script).
variable "slack_app_token" {
  description = "Slack App Token for bot channel configuration in the test environment"
  type        = string
  sensitive   = true
}

variable "slack_bot_token" {
  description = "Slack Bot Token for bot channel configuration in the test environment"
  type        = string
  sensitive   = true
}

variable "slack_test_channel_id" {
  description = "ID of the Slack channel for testing in the test environment"
  type        = string
}

variable "GHCR_PAT" {
  description = "GitHub Personal Access Token for accessing the GHCR registry"
  type        = string
  sensitive   = true
}

variable "DJANGO_SECRET_KEY" {
  description = "Django secret key for the test environment"
  type        = string
  sensitive   = true
}

variable "github_repository" {
  description = "GitHub repository name in the format 'username/repo'"
  type        = string
  default     = "sdamache/konveyor"
}

variable "docker_image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

variable "docker_registry_username" {
  description = "GitHub username for accessing the GHCR registry"
  type        = string
  default     = "sdamache"
}

variable "deploy_search_service" {
  description = "Whether to deploy the Azure Cognitive Search service (can be expensive)"
  type        = bool
  default     = false
}
