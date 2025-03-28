variable "prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "konveyor"
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {
    project = "konveyor"
    environment = "test"
  }
}

variable "microsoft_app_id" {
  description = "Microsoft App ID for Azure Bot Service"
  type        = string
  default     = "0eecb239-f1dc-4ab6-8ac7-5d60fd9102d1"
}

variable "search_sku" {
  description = "SKU for Azure Cognitive Search"
  type        = string
  default     = "basic"
}

# OpenAI variables
variable "openai_sku_name" {
  description = "SKU name for the Azure OpenAI Service"
  type        = string
  default     = "S0"
}

variable "openai_model_name" {
  description = "Name of the model for the Azure OpenAI Service"
  type        = string
  default     = "gpt-4o"
}

variable "openai_model_version" {
  description = "Version of the model for the Azure OpenAI Service"
  type        = string
  default     = "2024-11-20"
}

variable "openai_capacity" {
  description = "Tokens-per-Minute (TPM) capacity in thousands for GPT model. Example: capacity = 300 means 300K TPM (300,000 tokens per minute)"
  type        = number
  default     = 30  # 300K TPM for GPT-4
  
  validation {
    condition     = var.openai_capacity >= 1 && var.openai_capacity <= 500
    error_message = "Capacity must be between 1 and 500 (1K to 500K TPM). Each unit represents 1,000 tokens per minute."
  }
}

variable "openai_deploy_model" {
  description = "Whether to deploy the GPT model"
  type        = bool
  default     = true
}

variable "openai_deploy_embeddings" {
  description = "Whether to deploy the embeddings model"
  type        = bool
  default     = true
}

variable "openai_embeddings_model_name" {
  description = "Name of the embeddings model to deploy"
  type        = string
  default     = "text-embedding-ada-002"
}

variable "openai_embeddings_model_version" {
  description = "Version of the embeddings model"
  type        = string
  default     = "2"
}

variable "openai_embeddings_capacity" {
  description = "Tokens-per-Minute (TPM) capacity in thousands for embeddings model. Example: capacity = 1 means 1K TPM (1,000 tokens per minute)"
  type        = number
  default     = 10  # 10K TPM for embeddings
  
  validation {
    condition     = var.openai_embeddings_capacity >= 1 && var.openai_embeddings_capacity <= 100
    error_message = "Embeddings capacity must be between 1 and 100 (1K to 100K TPM). Each unit represents 1,000 tokens per minute."
  }
}
