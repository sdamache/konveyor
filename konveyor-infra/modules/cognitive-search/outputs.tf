output "search_service_id" {
  description = "Azure Cognitive Search Service ID"
  value       = length(azurerm_search_service.search) > 0 ? azurerm_search_service.search[0].id : null
}

output "search_service_name" {
  description = "Azure Cognitive Search Service name"
  value       = length(azurerm_search_service.search) > 0 ? azurerm_search_service.search[0].name : null
}

output "search_service_endpoint" {
  description = "Azure Cognitive Search Service endpoint"
  # Endpoint URL is constructed from the service name
  value       = length(azurerm_search_service.search) > 0 ? "https://${azurerm_search_service.search[0].name}.search.windows.net" : null
}

output "search_service_primary_key" {
  description = "Azure Cognitive Search Service primary key"
  value       = length(azurerm_search_service.search) > 0 ? azurerm_search_service.search[0].primary_key : null
  sensitive   = true
}
