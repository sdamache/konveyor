# Terraform Backend Setup

This directory contains the configuration to set up the Azure Storage backend for storing Terraform state.

## Usage

1. Initialize and apply the backend infrastructure:
```
cd backend
terraform init
terraform apply
```

2. Note the storage access key from the output

3. Return to the main Terraform directory and initialize with the backend:
```
cd ..
terraform init
```

4. When prompted, provide the access key for the storage account

## Note

This setup needs to be created first, before the main infrastructure, as it provides the remote state storage location.
