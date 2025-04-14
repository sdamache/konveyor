output "search_service_id" {
  description = "Azure Cognitive Search Service ID"
  value       = azurerm_search_service.search.id
}

output "search_service_name" {
  description = "Azure Cognitive Search Service name"
  value       = azurerm_search_service.search.name
}

output "search_service_endpoint" {
  description = "Azure Cognitive Search Service endpoint"
  # Endpoint URL is constructed from the service name
  value       = "https://${azurerm_search_service.search.name}.search.windows.net"
}

output "search_service_primary_key" {
  description = "Azure Cognitive Search Service primary key"
  value       = azurerm_search_service.search.primary_key
  sensitive   = true
}
