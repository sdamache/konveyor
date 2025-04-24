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
  description = "Azure Cognitive Search SKU (e.g., basic, standard, free)"
  type        = string
  default     = "standard"
}

variable "random_suffix" {
  description = "Random suffix to ensure uniqueness for the search service name"
  type        = string
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
  description = "A map of tags to assign to the resource"
  type        = map(string)
  default     = {
    project = "konveyor"
    environment = "test"
  }
}
