# This Terraform configuration sets up a backend for storing the Terraform state file in Azure Blob Storage.
# Provider Configuration
provider "azurerm" {
  features {}
  subscription_id = "bc840b1a-fbd5-4e01-8fd0-2511dcfc85da"

}

resource "azurerm_resource_group" "terraform_state" {
  name     = "terraform-state-rg"
  location = "eastus"
}

resource "azurerm_storage_account" "terraform_state" {
  name                     = "konveyortfstate"
  resource_group_name      = azurerm_resource_group.terraform_state.name
  location                 = azurerm_resource_group.terraform_state.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "terraform_state" {
  name                  = "tfstate"
  storage_account_name  = azurerm_storage_account.terraform_state.name
  container_access_type = "private"

  lifecycle {
    ignore_changes = [
      storage_account_name
    ]
  }
}

# Output the storage access key
output "storage_access_key" {
  value     = azurerm_storage_account.terraform_state.primary_access_key
  sensitive = true
}
