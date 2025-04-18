terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.75.0"
    }
  }
}

provider "azurerm" {
  skip_provider_registration = true
  features {
    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }
    # Allow deleting RG even if resources linger (useful for test cleanup)
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}