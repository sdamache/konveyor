variable "name" {
  description = "Name of the Azure Cognitive Search service"
  type        = string
  default     = "konveyor-search"
}

variable "location" {
  description = "Azure region for the Azure Cognitive Search service"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Name of the resource group for the Azure Cognitive Search service"
  type        = string
}

variable "sku" {
  description = "SKU for the Azure Cognitive Search service"
  type        = string
  default     = "basic"
}

variable "replica_count" {
  description = "Number of replicas for the Azure Cognitive Search service"
  type        = number
  default     = 1
}

variable "partition_count" {
  description = "Number of partitions for the Azure Cognitive Search service"
  type        = number
  default     = 1
}

variable "tags" {
  description = "Tags to apply to the Azure Cognitive Search service"
  type        = map(string)
  default     = {
    project = "konveyor"
    environment = "test"
  }
}
