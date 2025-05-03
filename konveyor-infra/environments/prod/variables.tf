variable "prefix" {
  description = "Prefix for resource names in the production environment"
  type        = string
  default     = "konveyor"
}

variable "location" {
  description = "Azure region for the production environment"
  type        = string
  default     = "eastus"
}

variable "tags" {
  description = "Tags to apply to resources in the production environment"
  type        = map(string)
  default     = {
    project     = "konveyor"
    environment = "prod"
  }
}

variable "microsoft_app_id" {
  description = "Microsoft App ID for Azure Bot Service in the production environment"
  type        = string
  default     = ""
}

variable "microsoft_app_password" {
  description = "Microsoft App Password for the Azure Bot Service in the production environment"
  type        = string
  sensitive   = true
  default     = ""
}

variable "slack_client_id" {
  description = "Slack Client ID for bot channel configuration in the production environment"
  type        = string
  default     = ""
}

variable "slack_client_secret" {
  description = "Slack Client Secret for bot channel configuration in the production environment"
  type        = string
  sensitive   = true
  default     = ""
}

variable "slack_signing_secret" {
  description = "Slack Signing Secret for bot channel configuration in the production environment"
  type        = string
  sensitive   = true
  default     = ""
}

variable "deploy_model" {
  description = "Deploy model in the production environment"
  type        = string
  default     = "true"
}

variable "openai_model_name" {
  description = "OpenAI model name in the production environment"
  type        = string
  default     = "gpt-4o"
}

variable "openai_model_version" {
  description = "OpenAI model version in the production environment"
  type        = string
  default     = "2024-05-13"
}

variable "openai_capacity" {
  description = "OpenAI capacity in the production environment"
  type        = string
  default     = "20"
}

variable "deploy_embeddings" {
  description = "Deploy embeddings model in the production environment"
  type        = string
  default     = "true"
}

variable "openai_embeddings_model_name" {
  description = "OpenAI embeddings model name in the production environment"
  type        = string
  default     = "text-embedding-ada-002"
}

variable "openai_embeddings_model_version" {
  description = "OpenAI embeddings model version in the production environment"
  type        = string
  default     = "2"
}

variable "openai_embeddings_capacity" {
  description = "OpenAI embeddings model capacity in the production environment"
  type        = number
  default     = 20
}

variable "slack_app_token" {
  description = "Slack App Token for bot channel configuration in the production environment"
  type        = string
  sensitive   = true
  default     = ""
}

variable "slack_bot_token" {
  description = "Slack Bot Token for bot channel configuration in the production environment"
  type        = string
  sensitive   = true
  default     = ""
}

variable "slack_test_channel_id" {
  description = "ID of the Slack channel for testing in the production environment"
  type        = string
  default     = ""
}

variable "GHCR_PAT" {
  description = "GitHub Personal Access Token for accessing the GHCR registry"
  type        = string
  sensitive   = true
  default     = ""
}

variable "DJANGO_SECRET_KEY" {
  description = "Django secret key for the production environment"
  type        = string
  sensitive   = true
  default     = ""
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
  description = "Whether to deploy the Azure Cognitive Search service"
  type        = bool
  default     = true
}
