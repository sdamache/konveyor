
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
    always_on = false

    container_registry_use_managed_identity = false
  }

  app_settings = merge(
    {
      WEBSITES_ENABLE_APP_SERVICE_STORAGE = "false"
      WEBSITES_PORT                      = "8000"
      DJANGO_SETTINGS_MODULE             = "konveyor.settings.production"
      DOCKER_CUSTOM_IMAGE_NAME           = "${var.docker_image_name}:${var.docker_image_tag}"
      DOCKER_REGISTRY_SERVER_URL         = var.docker_registry_url
      DOCKER_REGISTRY_SERVER_USERNAME    = var.docker_registry_username
      DOCKER_REGISTRY_SERVER_PASSWORD    = var.docker_registry_password
    },
    var.app_settings
  )
}
