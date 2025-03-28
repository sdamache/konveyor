#!/bin/bash

# Script to run document service tests with proper environment setup
# This helps ensure all required Azure services are properly configured

echo "=== Document Service Test Runner ==="
echo "Checking environment configuration..."

# Determine the project root (going up 3 directories from this script)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../../../../" && pwd )"
echo "Script directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_ROOT"

# Check if manage.py exists at project root
if [ ! -f "$PROJECT_ROOT/manage.py" ]; then
    echo "Error: manage.py not found at $PROJECT_ROOT"
    echo "Make sure this script is being run from inside the konveyor project structure"
    exit 1
fi

# Check if .env file exists and source it
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo "Loading environment from local .env file..."
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
elif [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Loading environment from project root .env file..."
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
else
    echo "Warning: No .env file found. Using existing environment variables."
    echo "Consider copying .env.example to .env and filling in your actual values."
fi

# Check required environment variables
REQUIRED_VARS=(
    "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"
    "AZURE_DOCUMENT_INTELLIGENCE_API_KEY"
    "AZURE_STORAGE_CONNECTION_STRING"
    "AZURE_STORAGE_CONTAINER_NAME"
    "AZURE_SEARCH_ENDPOINT"
    "AZURE_SEARCH_API_KEY"
    "AZURE_SEARCH_INDEX_NAME"
)

MISSING_VARS=()
for VAR in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!VAR}" ]; then
        MISSING_VARS+=("$VAR")
    else
        # Mask the value for security but confirm it's set
        VALUE="${!VAR}"
        MASKED="${VALUE:0:5}...${VALUE: -5}"
        echo "✓ $VAR is set: $MASKED"
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "Error: Missing required environment variables:"
    for VAR in "${MISSING_VARS[@]}"; do
        echo "  - $VAR"
    done
    echo "Please set these variables and try again."
    exit 1
fi

echo "Environment check passed."
echo ""

# Create test_files directory if it doesn't exist
TEST_FILES_DIR="$SCRIPT_DIR/test_files"
if [ ! -d "$TEST_FILES_DIR" ]; then
    echo "Creating test_files directory: $TEST_FILES_DIR"
    mkdir -p "$TEST_FILES_DIR"
    
    # Create a sample text file for tests
    echo "Creating sample.txt for tests..."
    cat > "$TEST_FILES_DIR/sample.txt" << EOF
This is a sample text file for testing the document service.
It contains multiple paragraphs to test the chunking functionality.

This paragraph has information about Azure services and document processing.
EOF
fi

# Explicitly set PYTHONPATH to include project root to ensure imports work correctly
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
echo "PYTHONPATH set to: $PYTHONPATH"

# Change to project root directory to run manage.py commands
cd "$PROJECT_ROOT"
echo "Changed directory to: $(pwd)"

# Check if manage.py is executable
if [ ! -x "manage.py" ]; then
    echo "Making manage.py executable..."
    chmod +x manage.py
fi

# Check for migrations before running tests
echo "Checking Django migrations..."
python manage.py makemigrations
python manage.py migrate

# Set Django settings module explicitly if needed
if [ -z "$DJANGO_SETTINGS_MODULE" ]; then
    export DJANGO_SETTINGS_MODULE=konveyor.settings
    echo "Set DJANGO_SETTINGS_MODULE to: $DJANGO_SETTINGS_MODULE"
fi

# Run the tests with increased verbosity
echo ""
echo "Running document service tests..."
echo "--------------------------------"
# Add a diagnostic print of crucial environment variables before test run
python -c "import os; print('Document Intelligence Endpoint:', bool(os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'))); print('Document Intelligence Key:', bool(os.getenv('AZURE_DOCUMENT_INTELLIGENCE_API_KEY')));"

# Run specific test or all document service tests
if [ -n "$1" ]; then
    # Run specific test method if provided as argument
    echo "Running specific test: $1"
    python manage.py test "konveyor.apps.documents.tests.test_document_service.TestDocumentServiceIntegration.$1" -v 2
else
    # Run all document service tests
    echo "Running all document service tests"
    python manage.py test konveyor.apps.documents.tests.test_document_service -v 2
fi

# Handle test result
TEST_RESULT=$?
if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo "All tests passed successfully!"
else
    echo ""
    echo "Tests failed. Check the error messages above."
    echo "For more detailed logging, add this to your settings:"
    echo ""
    echo "LOGGING = {"
    echo "    'version': 1,"
    echo "    'disable_existing_loggers': False,"
    echo "    'handlers': {"
    echo "        'console': {"
    echo "            'class': 'logging.StreamHandler',"
    echo "        },"
    echo "    },"
    echo "    'loggers': {"
    echo "        'konveyor.apps.documents': {"
    echo "            'handlers': ['console'],"
    echo "            'level': 'DEBUG',"
    echo "        },"
    echo "    },"
    echo "}"
fi

exit $TEST_RESULT 