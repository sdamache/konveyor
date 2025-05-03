FROM mcr.microsoft.com/vscode/devcontainers/base:latest

# Install Terraform
RUN apt-get update && \
    apt-get install -y wget unzip && \
    wget https://releases.hashicorp.com/terraform/1.7.4/terraform_1.7.4_linux_amd64.zip && \
    unzip terraform_1.7.4_linux_amd64.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/terraform && \
    rm terraform_1.7.4_linux_amd64.zip

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Set up the working directory
WORKDIR /workspace

# Copy the install script
COPY scripts/install-tools.sh /usr/local/bin/install-tools.sh
RUN chmod +x /usr/local/bin/install-tools.sh

# Run the install script
RUN /usr/local/bin/install-tools.sh

# Expose any ports if necessary
# EXPOSE 8080

# Define the default command
CMD ["bash"]
