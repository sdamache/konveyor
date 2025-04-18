terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "konveyortfstate"
    container_name       = "tfstate"
    key                  = "konveyor.terraform.tfstate"
  }
} 