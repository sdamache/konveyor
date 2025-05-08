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
      purge_soft_delete_on_destroy    = true  # Changed to true for test environment
      recover_soft_deleted_key_vaults = false # Changed to false for test environment
    }
    # Allow deleting RG even if resources linger (useful for test cleanup)
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    # Add cognitive_account settings for test environment
    cognitive_account {
      purge_soft_delete_on_destroy = true  # Automatically purge on destroy
    }
  }
}
