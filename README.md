# Konveyor

Konveyor is a knowledge transfer (KT) agent designed to help new and existing employees quickly onboard and familiarize themselves with organizational policies, software, procedures, and other information.

## Features

- Integration with Azure OpenAI for intelligent responses
- Document processing and understanding
- Code analysis and explanation
- Teams bot integration for easy access

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL
- Azure account with appropriate services

### Installation

1. Clone the repository
    ```bash
    git clone https://github.com/yourusername/konveyor.git
    cd konveyor
    ```

2. Create a virtual environment
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install dependencies
    ```bash
    pip install -r requirements/development.txt
    ```

4. Set up environment variables
    ```bash
    cp .env.example .env
    # Edit .env with your configuration
    ```

5. Run migrations
    ```bash
    python manage.py migrate
    ```

6. Start the development server
    ```bash
    python manage.py runserver
    ```

## Architecture

Konveyor follows a modular architecture with clear separation of concerns:

- Core: Base functionality and utilities
- Users: User management and authentication
- API: REST API endpoints for integration
