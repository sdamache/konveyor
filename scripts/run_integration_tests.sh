#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
# Point to the specific test environment directory
INFRA_DIR="$PROJECT_ROOT/Konveyor-infra/environments/test"
TF_WORKSPACE="integration-test"

# --- Ensure jq is installed ---
if ! command -v jq &> /dev/null
then
    echo "Error: jq is not installed. Please install it (e.g., 'brew install jq' or 'sudo apt-get install jq')."
    exit 1
fi

# --- Cleanup Function ---
cleanup() {
  echo "--- Cleaning up Terraform resources --- "
  cd "$INFRA_DIR"

  read -p "Do you want to destroy the Terraform resources? (y/N) " confirm
  if [[ "$confirm" =~ ^[Yy]$ ]]; then
    echo "Proceeding with terraform destroy..."
    terraform destroy -auto-approve
  else
    echo "Skipping terraform destroy."
  fi

  # Remove the workspace
  terraform workspace select default
  terraform workspace delete integration-test

  echo "--- Cleanup complete ---"
  cd "$PROJECT_ROOT"
}

# --- Trap to ensure cleanup runs ---
# Call cleanup function on script exit or interruption (SIGINT, SIGTERM)
trap cleanup EXIT SIGINT SIGTERM

# --- Main Script ---
echo "--- Starting Integration Test Setup ---"
echo "Project Root: $PROJECT_ROOT"
echo "Infra Dir: $INFRA_DIR"

# 1. Navigate to Infra Dir
# Navigate to the specific test environment directory
cd "$INFRA_DIR"

# 2. Select or Create Terraform Workspace
echo "--- Selecting/Creating Terraform Workspace: $TF_WORKSPACE ---"
terraform workspace select "$TF_WORKSPACE" || terraform workspace new "$TF_WORKSPACE"

# 3. Initialize Terraform
echo "--- Initializing Terraform ---"
terraform init -upgrade

# 4. Apply Terraform Configuration
echo "--- Applying Terraform Configuration (Requires Azure Login & uncommented modules in main.tf) ---"
# Apply configuration from within the test environment directory
# Remove -var-file flag
terraform apply -auto-approve

# 5. Capture Terraform Outputs
echo "--- Capturing Terraform Outputs ---"
# Use -json flag and parse with jq
# Map terraform outputs to expected ENV VARS for the Django app
# Note: Ensure these outputs are defined and NOT commented out in outputs.tf
#       Handle potential nulls from jq if outputs might be missing
tf_outputs=$(terraform output -json)

export AZURE_SEARCH_ENDPOINT=$(echo "$tf_outputs" | jq -r '.cognitive_search_endpoint.value // empty')
export AZURE_SEARCH_API_KEY=$(echo "$tf_outputs" | jq -r '.cognitive_search_primary_key.value // empty') # Assuming primary_key output exists
export AZURE_OPENAI_ENDPOINT=$(echo "$tf_outputs" | jq -r '.openai_endpoint.value // empty') # Assuming openai_endpoint output exists
export AZURE_OPENAI_API_KEY=$(echo "$tf_outputs" | jq -r '.openai_primary_key.value // empty') # Assuming openai_primary_key output exists
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT=$(echo "$tf_outputs" | jq -r '.openai_embeddings_deployment_name.value // empty')
export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=$(echo "$tf_outputs" | jq -r '.document_intelligence_endpoint.value // empty')
export AZURE_DOCUMENT_INTELLIGENCE_API_KEY=$(echo "$tf_outputs" | jq -r '.document_intelligence_primary_key.value // empty') # Assuming primary_key output exists
export AZURE_STORAGE_CONNECTION_STRING=$(echo "$tf_outputs" | jq -r '.storage_connection_string.value // empty')
# Add Cosmos/Redis connection strings if they are Terraform outputs
# export AZURE_COSMOS_CONNECTION_STRING=$(echo "$tf_outputs" | jq -r '.cosmos_connection_string.value // empty')
# export AZURE_REDIS_CONNECTION_STRING=$(echo "$tf_outputs" | jq -r '.redis_connection_string.value // empty')

# Explicitly set the correct API version based on endpoint analysis
export AZURE_OPENAI_API_VERSION="2023-05-15"

echo "--- Environment Variables Set (Keys Masked) ---"
echo "AZURE_SEARCH_ENDPOINT=${AZURE_SEARCH_ENDPOINT}"
echo "AZURE_SEARCH_API_KEY=${AZURE_SEARCH_API_KEY:0:4}..."
echo "AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}"
echo "AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY:0:4}..."
echo "AZURE_OPENAI_EMBEDDING_DEPLOYMENT=${AZURE_OPENAI_EMBEDDING_DEPLOYMENT}"
echo "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=${AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT}"
echo "AZURE_DOCUMENT_INTELLIGENCE_API_KEY=${AZURE_DOCUMENT_INTELLIGENCE_API_KEY:0:4}..."
echo "AZURE_STORAGE_CONNECTION_STRING=${AZURE_STORAGE_CONNECTION_STRING:0:20}..."
# echo "AZURE_COSMOS_CONNECTION_STRING=${AZURE_COSMOS_CONNECTION_STRING:0:20}..."
# echo "AZURE_REDIS_CONNECTION_STRING=${AZURE_REDIS_CONNECTION_STRING:0:20}..."
echo "AZURE_OPENAI_API_VERSION=${AZURE_OPENAI_API_VERSION}" # Verify the version is set

# Check if essential variables are set (add more as needed)
if [ -z "$AZURE_SEARCH_ENDPOINT" ] || [ -z "$AZURE_OPENAI_ENDPOINT" ] || [ -z "$AZURE_OPENAI_EMBEDDING_DEPLOYMENT" ]; then
  echo "Error: Essential Terraform outputs (Search/OpenAI endpoints/embedding deployment) not found. Check outputs.tf and ensure modules are applied."
  exit 1
fi

# 6. Navigate back to Project Root (adjust path)
cd "$PROJECT_ROOT" # Already correct as PROJECT_ROOT is the base

# 7. Run Django Tests
echo "--- Installing Python Dependencies ---"
# Assuming pip and python are available in the path
# Use python -m pip to ensure using the pip associated with the python interpreter
python -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install Python dependencies."
    cleanup
    exit 1
fi

echo "--- Running Django Tests ---"
# Navigate to the project root where manage.py is located
# Assuming the script is run from the repository root
python manage.py test
TEST_EXIT_CODE=$?

# Check if tests passed
if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo "Error: Django tests failed with exit code $TEST_EXIT_CODE"
    # Optionally decide if failure should prevent cleanup
    # cleanup
    # exit $TEST_EXIT_CODE
else
    echo "Success: Django tests passed."
fi

# --- Cleanup ---
cleanup
exit $TEST_EXIT_CODE # Exit with the test exit code
