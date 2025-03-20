variable "name" {
  description = "Name of the Key Vault"
  type        = string
  default     = "konveyor-keyvault"
}

variable "location" {
  description = "Azure region for the Key Vault"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Name of the resource group containing the Key Vault"
  type        = string
  default     = "konveyor-rg"
}

variable "tags" {
  description = "Tags to apply to the Key Vault"
  type        = map(string)
  default     = {
    project = "konveyor"
    environment = "test"
  }
}
