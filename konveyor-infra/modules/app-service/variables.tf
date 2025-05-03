variable "name" {
  description = "Name of the App Service"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string

}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "app_settings" {
  description = "App settings for the App Service"
  type        = map(string)
  default     = {}
}

variable "app_service_plan_sku" {
  description = "SKU for the App Service Plan"
  type        = string
  default     = "B1"
}

variable "docker_registry_url" {
  description = "The URL of the Docker registry (e.g., https://ghcr.io)."
  type        = string
  default     = null # Must be provided if using container deployment
}

variable "docker_image_name" {
  description = "The name of the Docker image (e.g., ghcr.io/your-user/your-repo/app)."
  type        = string
  default     = null # Must be provided if using container deployment
}

variable "docker_image_tag" {
  description = "The tag of the Docker image to deploy (e.g., 'latest' or a specific version)."
  type        = string
  default     = "latest"
}

variable "docker_registry_username" {
  description = "The username for the Docker registry."
  type        = string
  default     = null # Required for private registries
}

variable "docker_registry_password" {
  description = "The password (or PAT) for the Docker registry."
  type        = string
  sensitive   = true
  default     = null # Required for private registries
}
