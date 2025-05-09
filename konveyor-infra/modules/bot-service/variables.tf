variable "name" {
  description = "Name of the Azure Bot Service"
  type        = string
  default     = "konveyor-bot"
}

variable "location" {
  description = "Azure region for the Azure Bot Service"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Name of the resource group for the Azure Bot Service"
  type        = string
  default     = "konveyor-rg"
}

variable "sku" {
  description = "SKU for the Azure Bot Service"
  type        = string
  default     = "F0"
}

variable "microsoft_app_id" {
  description = "Microsoft App ID for the Azure Bot Service"
  type        = string
  default     = "c8218a52-681c-4df2-b558-5fa8e5067b43"
}

variable "microsoft_app_password" {
  description = "Microsoft App Password for the Azure Bot Service"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Tags to apply to the Azure Bot Service"
  type        = map(string)
  default     = {
    project = "konveyor"
    environment = "test"
  }
}

variable "slack_client_id" {
  description = "Slack Client ID for bot channel configuration"
  type        = string
}

variable "slack_client_secret" {
  description = "Slack Client Secret for bot channel configuration"
  type        = string
  sensitive   = true
}

variable "slack_signing_secret" {
  description = "Slack Signing Secret for bot channel configuration"
  type        = string
  sensitive   = true
}

variable "prefix" {
  description = "Prefix to use for resource naming"
  type        = string
}
