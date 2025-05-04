variable "name" {
  description = "Name of the OpenAI service"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9-]{2,64}$", var.name))
    error_message = "Name must be 2-64 characters long and can only contain alphanumeric characters and hyphens."
  }
}

variable "location" {
  description = "Azure region for the Azure OpenAI Service"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group for the Azure OpenAI Service"
  type        = string
}

variable "sku_name" {
  description = "SKU name for the Azure OpenAI Service"
  type        = string
  default     = "S0"

  validation {
    condition     = contains(["S0"], var.sku_name)
    error_message = "SKU name must be S0 for Azure OpenAI Service."
  }
}

variable "model_name" {
  description = "Name of the model for the Azure OpenAI Service"
  type        = string

  validation {
    condition     = contains(["gpt-4", "gpt-4o", "gpt-35-turbo"], var.model_name)
    error_message = "Model name must be one of: gpt-4, gpt-4o, gpt-35-turbo."
  }
}

variable "model_version" {
  description = "Version of the model for the Azure OpenAI Service"
  type        = string

  validation {
    condition     = can(regex("^\\d{4}-\\d{2}-\\d{2}$", var.model_version))
    error_message = "Model version must be in format YYYY-MM-DD."
  }
}

variable "capacity" {
  description = "Tokens-per-Minute (TPM) capacity in thousands. Example: capacity = 300 means 300K TPM (300,000 tokens per minute)"
  type        = number
  default     = 300  # This gives us 300K TPM

  validation {
    condition     = var.capacity >= 1 && var.capacity <= 500
    error_message = "Capacity must be between 1 and 500 (1K to 500K TPM). Each unit represents 1,000 tokens per minute."
  }
}

variable "tags" {
  description = "Tags to apply to the Azure OpenAI Service"
  type        = map(string)
  default     = {
    project = "konveyor"
    environment = "test"
  }
}

variable "deploy_model" {
  description = "Whether to deploy the model (set to false if you don't have quota)"
  type        = bool
  default     = false
}

variable "deploy_embeddings" {
  description = "Whether to deploy the embeddings model"
  type        = bool
  default     = true
}

variable "embeddings_model_name" {
  description = "Name of the embeddings model"
  type        = string
  default     = "text-embedding-ada-002"

  validation {
    condition     = var.embeddings_model_name == "text-embedding-ada-002"
    error_message = "Only text-embedding-ada-002 is supported for embeddings."
  }
}

variable "embeddings_model_version" {
  description = "Version of the embeddings model"
  type        = string
  default     = "2"

  validation {
    condition     = var.embeddings_model_version == "2"
    error_message = "Only version 2 is supported for text-embedding-ada-002."
  }
}

variable "embeddings_capacity" {
  description = "Tokens-per-Minute (TPM) capacity in thousands for embeddings model. Example: capacity = 1 means 1K TPM (1,000 tokens per minute)"
  type        = number
  default     = 10  # 10K TPM for embeddings

  validation {
    condition     = var.embeddings_capacity >= 1 && var.embeddings_capacity <= 100
    error_message = "Embeddings capacity must be between 1 and 100 (1K to 100K TPM). Each unit represents 1,000 tokens per minute."
  }
}
