variable "name" {
  description = "Name of the Document Intelligence service"
  type        = string
}

variable "location" {
  description = "Azure region for the Document Intelligence service"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "sku_name" {
  description = "SKU name for the Document Intelligence service"
  type        = string
  default     = "S0"
}

variable "tags" {
  description = "Tags to apply to the Document Intelligence service"
  type        = map(string)
  default     = {}
}
