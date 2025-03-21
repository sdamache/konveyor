variable "name" {
  description = "Name of the Azure OpenAI Service"
  type        = string
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
}

variable "model_name" {
  description = "Name of the model for the Azure OpenAI Service"
  type        = string
}

variable "model_version" {
  description = "Version of the model for the Azure OpenAI Service"
  type        = string
}

variable "capacity" {
  description = "Capacity for the Azure OpenAI Service"
  type        = number
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
