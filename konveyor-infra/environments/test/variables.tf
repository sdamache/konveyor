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
  default     = "0eecb239-f1dc-4ab6-8ac7-5d60fd9102d1" # Use the same default or a test-specific one if available
}

# Note: Other variables like openai_sku_name, openai_model_name etc. are defined
# in the root variables.tf and their defaults will be used unless overridden here
# or in a .tfvars file (which we are not using in the script).