# konveyor

## Azure Infrastructure Setup with Terraform

This section provides detailed instructions on setting up the essential Azure infrastructure for the Konveyor project using Terraform as Infrastructure as Code (IaC). This approach ensures consistency, reproducibility, and proper documentation of the infrastructure.

### Prerequisites

- An Azure account
- Terraform installed on your local machine
- Azure CLI installed and configured

### Terraform Project Structure

The Terraform project structure is organized as follows:

```
konveyor-infra/
├── main.tf           # Main entry point
├── variables.tf      # Input variables
├── outputs.tf        # Output values
├── providers.tf      # Provider configuration
├── modules/
│   ├── resource-group/
│   ├── openai/
│   ├── cognitive-search/
│   ├── bot-service/
│   └── key-vault/
└── environments/
    ├── dev/
    ├── test/
    └── prod/
```

### Configuring the Azure Provider and Backend

Create a `providers.tf` file to configure the Azure provider and backend:

```hcl
# providers.tf
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.75.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "konveyortfstate"
    container_name       = "tfstate"
    key                  = "konveyor.terraform.tfstate"
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = false
      recover_soft_deleted_key_vaults = true
    }
  }
}
```

### Creating and Using Terraform Modules

#### Resource Group Module

Create a `resource-group` module to manage the resource group:

```hcl
# modules/resource-group/main.tf
resource "azurerm_resource_group" "this" {
  name     = var.name
  location = var.location
  tags     = var.tags
}

# modules/resource-group/variables.tf
variable "name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for the resource group"
  type        = string
}

variable "tags" {
  description = "Tags to apply to the resource group"
  type        = map(string)
  default     = {}
}

# modules/resource-group/outputs.tf
output "id" {
  description = "Resource group ID"
  value       = azurerm_resource_group.this.id
}

output "name" {
  description = "Resource group name"
  value       = azurerm_resource_group.this.name
}
```

#### Azure OpenAI Module

Create an `openai` module to manage the Azure OpenAI Service:

```hcl
# modules/openai/main.tf
resource "azurerm_cognitive_account" "openai" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  kind                = "OpenAI"
  sku_name            = var.sku_name
  tags                = var.tags
}

resource "azurerm_cognitive_deployment" "gpt_deployment" {
  name                 = "gpt-deployment"
  cognitive_account_id = azurerm_cognitive_account.openai.id
  model {
    format  = "OpenAI"
    name    = var.model_name
    version = var.model_version
  }
  scale {
    type     = "Standard"
    capacity = var.capacity
  }
}
```

#### Azure Cognitive Search Module

Create a `cognitive-search` module to manage the Azure Cognitive Search service:

```hcl
# modules/cognitive-search/main.tf
resource "azurerm_search_service" "search" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku
  replica_count       = var.replica_count
  partition_count     = var.partition_count
  tags                = var.tags
}
```

#### Azure Bot Service Module

Create a `bot-service` module to manage the Azure Bot Service:

```hcl
# modules/bot-service/main.tf
resource "azurerm_bot_service_azure_bot" "bot" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku
  microsoft_app_id    = var.microsoft_app_id
  tags                = var.tags
}
```

#### Key Vault Module

Create a `key-vault` module to manage the Key Vault for secure storage of secrets:

```hcl
# modules/key-vault/main.tf
resource "azurerm_key_vault" "vault" {
  name                        = var.name
  location                    = var.location
  resource_group_name         = var.resource_group_name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  sku_name                    = "standard"
  tags                        = var.tags
}

resource "azurerm_key_vault_access_policy" "terraform" {
  key_vault_id = azurerm_key_vault.vault.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = [
    "Get", "List", "Set", "Delete", "Purge"
  ]
}
```

### Main Configuration File

Create a `main.tf` file to define the main configuration for the Terraform project:

```hcl
# main.tf
module "resource_group" {
  source   = "./modules/resource-group"
  name     = "${var.prefix}-rg"
  location = var.location
  tags     = var.tags
}

module "key_vault" {
  source              = "./modules/key-vault"
  name                = "${var.prefix}-kv"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

module "openai" {
  source              = "./modules/openai"
  name                = "${var.prefix}-openai"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku_name            = "S0"
  model_name          = "gpt-4o"
  model_version       = "1106-Preview"
  capacity            = 1
  tags                = var.tags
}

module "cognitive_search" {
  source              = "./modules/cognitive-search"
  name                = "${var.prefix}-search"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku                 = "basic"
  replica_count       = 1
  partition_count     = 1
  tags                = var.tags
}

module "bot_service" {
  source              = "./modules/bot-service"
  name                = "${var.prefix}-bot"
  resource_group_name = module.resource_group.name
  location            = "global"
  sku                 = "F0"
  microsoft_app_id    = var.microsoft_app_id
  tags                = var.tags
}
```

### Environments

Create separate directories for different environments (dev, test, prod) and add the main configuration files for each environment.

#### Dev Environment

Create a `main.tf` file for the dev environment:

```hcl
# environments/dev/main.tf
module "resource_group" {
  source   = "../../modules/resource-group"
  name     = "${var.prefix}-dev-rg"
  location = var.location
  tags     = var.tags
}

module "key_vault" {
  source              = "../../modules/key-vault"
  name                = "${var.prefix}-dev-kv"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

module "openai" {
  source              = "../../modules/openai"
  name                = "${var.prefix}-dev-openai"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku_name            = "S0"
  model_name          = "gpt-4o"
  model_version       = "1106-Preview"
  capacity            = 1
  tags                = var.tags
}

module "cognitive_search" {
  source              = "../../modules/cognitive-search"
  name                = "${var.prefix}-dev-search"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku                 = "basic"
  replica_count       = 1
  partition_count     = 1
  tags                = var.tags
}

module "bot_service" {
  source              = "../../modules/bot-service"
  name                = "${var.prefix}-dev-bot"
  resource_group_name = module.resource_group.name
  location            = "global"
  sku                 = "F0"
  microsoft_app_id    = var.microsoft_app_id
  tags                = var.tags
}
```

#### Test Environment

Create a `main.tf` file for the test environment:

```hcl
# environments/test/main.tf
module "resource_group" {
  source   = "../../modules/resource-group"
  name     = "${var.prefix}-test-rg"
  location = var.location
  tags     = var.tags
}

module "key_vault" {
  source              = "../../modules/key-vault"
  name                = "${var.prefix}-test-kv"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

module "openai" {
  source              = "../../modules/openai"
  name                = "${var.prefix}-test-openai"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku_name            = "S0"
  model_name          = "gpt-4o"
  model_version       = "1106-Preview"
  capacity            = 1
  tags                = var.tags
}

module "cognitive_search" {
  source              = "../../modules/cognitive-search"
  name                = "${var.prefix}-test-search"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku                 = "basic"
  replica_count       = 1
  partition_count     = 1
  tags                = var.tags
}

module "bot_service" {
  source              = "../../modules/bot-service"
  name                = "${var.prefix}-test-bot"
  resource_group_name = module.resource_group.name
  location            = "global"
  sku                 = "F0"
  microsoft_app_id    = var.microsoft_app_id
  tags                = var.tags
}
```

#### Prod Environment

Create a `main.tf` file for the prod environment:

```hcl
# environments/prod/main.tf
module "resource_group" {
  source   = "../../modules/resource-group"
  name     = "${var.prefix}-prod-rg"
  location = var.location
  tags     = var.tags
}

module "key_vault" {
  source              = "../../modules/key-vault"
  name                = "${var.prefix}-prod-kv"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

module "openai" {
  source              = "../../modules/openai"
  name                = "${var.prefix}-prod-openai"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku_name            = "S0"
  model_name          = "gpt-4o"
  model_version       = "1106-Preview"
  capacity            = 1
  tags                = var.tags
}

module "cognitive_search" {
  source              = "../../modules/cognitive-search"
  name                = "${var.prefix}-prod-search"
  resource_group_name = module.resource_group.name
  location            = var.location
  sku                 = "basic"
  replica_count       = 1
  partition_count     = 1
  tags                = var.tags
}

module "bot_service" {
  source              = "../../modules/bot-service"
  name                = "${var.prefix}-prod-bot"
  resource_group_name = module.resource_group.name
  location            = "global"
  sku                 = "F0"
  microsoft_app_id    = var.microsoft_app_id
  tags                = var.tags
}
```

### Testing the Setup

To test the setup, follow these steps:

1. Initialize the Terraform project:
   ```sh
   terraform init
   ```

2. Validate the Terraform configuration:
   ```sh
   terraform validate
   ```

3. Plan the Terraform deployment:
   ```sh
   terraform plan
   ```

4. Apply the Terraform configuration:
   ```sh
   terraform apply
   ```

5. Verify the deployed resources in the Azure portal.
