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

# Note: Other variables like openai_sku_name, openai_model_name etc. are defined
# in the root variables.tf and their defaults will be used unless overridden here
# or in a .tfvars file (which we are not using in the script).