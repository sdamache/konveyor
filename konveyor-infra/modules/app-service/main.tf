
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
    # linux_fx_version is typically set automatically by Azure for Python apps
  }

  app_settings = merge(
    {
      WEBSITES_ENABLE_APP_SERVICE_STORAGE = "false"
      SCM_DO_BUILD_DURING_DEPLOYMENT     = "true"
      DJANGO_SETTINGS_MODULE             = "konveyor.settings.development"
      WEBSITE_RUN_FROM_PACKAGE           = "0"

    },
    var.app_settings
  )
}
