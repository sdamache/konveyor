#!/bin/bash
set -e

# Update package list
echo "Updating package list..."
sudo apt-get update

# Install required packages
echo "Installing prerequisites..."
sudo apt-get install -y \
    curl \
    unzip \
    jq \
    apt-transport-https \
    lsb-release \
    gnupg

# Install Terraform
echo "Installing Terraform..."
TERRAFORM_VERSION=$(curl -s https://checkpoint-api.hashicorp.com/v1/check/terraform | jq -r .current_version)
curl -LO "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip"
unzip "terraform_${TERRAFORM_VERSION}_linux_amd64.zip"
sudo mv terraform /usr/local/bin/
rm "terraform_${TERRAFORM_VERSION}_linux_amd64.zip"

# Install Azure CLI
echo "Installing Azure CLI..."
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Verify installations
echo "Verifying installations..."
terraform version
az --version

echo "Installation complete!"
