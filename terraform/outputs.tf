output "key_vault_url" {
  value = azurerm_key_vault.konveyor.vault_uri
}

output "openai_endpoint" {
  value = azurerm_cognitive_account.openai.endpoint
}

output "cognitive_search_endpoint" {
  value = azurerm_search_service.konveyor.endpoint
}

output "resource_group_name" {
  value = azurerm_resource_group.konveyor.name
}

output "tenant_id" {
  value = data.azurerm_client_config.current.tenant_id
}
