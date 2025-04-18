output "key_vault_id" {
  description = "Key Vault ID"
  value       = azurerm_key_vault.vault.id
}

output "key_vault_name" {
  description = "Key Vault name"
  value       = azurerm_key_vault.vault.name
}
