# Development Environment Setup

This project sets up a development environment using a Docker container. The environment is configured to include essential tools and extensions for development.

## Directory Structure

```
.devcontainer
├── devcontainer.json      # Configuration for the development container
├── Dockerfile             # Instructions for building the Docker image
└── scripts
    └── install-tools.sh   # Script to install necessary CLI tools
├── .vscode
│   └── extensions.json    # Essential VS Code extensions
└── README.md              # Documentation for the project
```

## Setup Instructions

1. **Build the Container**: Use the command `docker-compose up` to build and start the development container.
2. **Install Tools**: The `install-tools.sh` script will automatically install Terraform and Azure CLI when the container launches.
3. **VS Code Extensions**: The essential extensions specified in `.vscode/extensions.json` will be installed automatically.

## Usage Guidelines

- Ensure Docker is running before starting the container.
- Modify the `install-tools.sh` script to add or remove tools as needed.
- Update the `extensions.json` file to manage VS Code extensions based on your requirements.
