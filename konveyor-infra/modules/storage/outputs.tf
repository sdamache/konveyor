output "storage_account_id" {
  description = "Storage Account ID"
  value       = azurerm_storage_account.storage.id
}

output "storage_account_name" {
  description = "Storage Account name"
  value       = azurerm_storage_account.storage.name
}

output "storage_connection_string" {
  description = "Storage Account connection string"
  value       = azurerm_storage_account.storage.primary_connection_string
  sensitive   = true
}

output "storage_container_name" {
  description = "Storage container name"
  value       = azurerm_storage_container.documents.name
}

output "primary_access_key" {
  description = "Storage Account primary access key"
  value       = azurerm_storage_account.storage.primary_access_key
  sensitive   = true
}
