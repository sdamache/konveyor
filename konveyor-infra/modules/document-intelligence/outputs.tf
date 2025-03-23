output "id" {
  description = "Document Intelligence service ID"
  value       = azurerm_cognitive_account.document_intelligence.id
}

output "endpoint" {
  description = "Document Intelligence service endpoint"
  value       = azurerm_cognitive_account.document_intelligence.endpoint
}
