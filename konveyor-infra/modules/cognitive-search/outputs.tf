output "search_service_id" {
  description = "Azure Cognitive Search Service ID"
  value       = azurerm_search_service.search.id
}

output "search_service_name" {
  description = "Azure Cognitive Search Service name"
  value       = azurerm_search_service.search.name
}
