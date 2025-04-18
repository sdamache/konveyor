output "id" {
  description = "Document Intelligence service ID"
  value       = azurerm_cognitive_account.document_intelligence.id
}

output "endpoint" {
  description = "Document Intelligence service endpoint"
  value       = azurerm_cognitive_account.document_intelligence.endpoint
}

output "primary_key" {
  description = "Document Intelligence service primary key"
  value       = azurerm_cognitive_account.document_intelligence.primary_access_key
  sensitive   = true
}
