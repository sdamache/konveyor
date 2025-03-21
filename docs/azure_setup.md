# Azure Services Setup

## Quick Start

1. Deploy Azure resources using Terraform:
```bash
cd terraform
terraform init
terraform apply
```

2. Update environment variables with Terraform outputs:
```bash
./scripts/update_env.sh
```

3. Install dependencies:
```bash
pip install azure-identity azure-keyvault-secrets openai azure-search-documents
```

4. Basic usage:
```python
from konveyor.config.azure import AzureConfig

azure = AzureConfig()
openai_client = azure.get_openai_client()
search_client = azure.get_search_client()
```

## Environment Variables

The environment variables are automatically populated from Terraform outputs:
- `AZURE_KEY_VAULT_URL`: URL of the Azure Key Vault
- `AZURE_OPENAI_ENDPOINT`: Endpoint for Azure OpenAI service
- `AZURE_COGNITIVE_SEARCH_ENDPOINT`: Endpoint for Azure Cognitive Search
- `AZURE_TENANT_ID`: Azure tenant ID

For local development, you'll need to manually set:
- `AZURE_CLIENT_ID`: Service principal client ID
- `AZURE_CLIENT_SECRET`: Service principal secret

## Azure CLI Commands for Configuration

### Get Resource Information
```bash
# Get OpenAI Endpoint
az cognitiveservices account show --name konveyor-openai \
    --resource-group konveyor-rg \
    --query properties.endpoint -o tsv

# Get Cognitive Search Endpoint
az search service show --name konveyor-search \
    --resource-group konveyor-rg \
    --query properties.hostingInfo.publicEndpoint -o tsv

# Get Key Vault URL
az keyvault show --name konveyor-kv \
    --resource-group konveyor-rg \
    --query properties.vaultUri -o tsv

# Get Tenant ID
az account show --query tenantId -o tsv
```

### Export to Environment Variables
```bash
# One-line export commands
export AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)
export AZURE_KEY_VAULT_URL=$(az keyvault show --name konveyor-kv \
    --resource-group konveyor-rg --query properties.vaultUri -o tsv)
export AZURE_OPENAI_ENDPOINT=$(az cognitiveservices account show --name konveyor-openai \
    --resource-group konveyor-rg --query properties.endpoint -o tsv)
export AZURE_COGNITIVE_SEARCH_ENDPOINT=$(az search service show --name konveyor-search \
    --resource-group konveyor-rg --query properties.hostingInfo.publicEndpoint -o tsv)
```

### Getting API Keys (if not using managed identity)
```bash
# Get OpenAI API Key
az cognitiveservices account keys list --name konveyor-openai \
    --resource-group konveyor-rg --query 'key1' -o tsv

# Get Cognitive Search Admin Key
az search admin-key show --service-name konveyor-search \
    --resource-group konveyor-rg --query 'primaryKey' -o tsv
```

## TODO

- [ ] Add detailed service configuration guides
- [ ] Document security best practices
- [ ] Add monitoring setup instructions
- [ ] Document backup and disaster recovery procedures
- [ ] Add cost optimization guidelines
