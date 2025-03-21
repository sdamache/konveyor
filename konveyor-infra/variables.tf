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
  default     = "0eecb239-f1dc-4ab6-8ac7-5d60fd9102d1"
}
