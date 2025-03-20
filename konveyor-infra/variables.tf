variable "prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "konveyor"
}

variable "location" {
  description = "Azure region for resources"
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
  default     = "your-microsoft-app-id"
}
