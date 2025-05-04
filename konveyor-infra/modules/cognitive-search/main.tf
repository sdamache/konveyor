resource "azurerm_search_service" "search" {
  count               = var.partition_count > 0 ? 1 : 0
  name                = "${var.name}-${var.random_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku
  replica_count       = var.replica_count
  partition_count     = var.partition_count
  tags                = var.tags
}
