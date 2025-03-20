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
  default     = "your-microsoft-app-id"
}

variable "tags" {
  description = "Tags to apply to the Azure Bot Service"
  type        = map(string)
  default     = {
    project = "konveyor"
    environment = "test"
  }
}
