
resource "azurerm_service_plan" "this" {
  name                = "${var.name}-plan"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = var.app_service_plan_sku
  tags                = var.tags
}

resource "azurerm_linux_web_app" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  service_plan_id     = azurerm_service_plan.this.id
  tags                = var.tags

  site_config {
    always_on = true

    container_registry_use_managed_identity = false

    health_check_path = "/healthz/"
    health_check_eviction_time_in_min = 5
  }

  app_settings = merge(
    {
      DOCKER_CUSTOM_IMAGE_NAME           = "${var.docker_image_name}:${var.docker_image_tag}"
      DOCKER_REGISTRY_SERVER_URL         = var.docker_registry_url
      DOCKER_REGISTRY_SERVER_USERNAME    = var.docker_registry_username
      DOCKER_REGISTRY_SERVER_PASSWORD    = var.docker_registry_password
      DOCKER_ENABLE_CI                   = "false"
    },
    var.app_settings
  )
}
