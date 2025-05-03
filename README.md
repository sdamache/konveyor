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
- PostgreSQL (for production) or SQLite (for development)
- Azure account with appropriate services (for production)

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
   python3 manage.py runserver
   ```

## Project Structure

```
konveyor/
├── konveyor/                   # Django project root
│   ├── apps/                   # Django applications
│   │   ├── core/               # Core functionality
│   │   ├── users/              # User management
│   │   └── api/                # API endpoints
│   ├── settings/               # Split settings
│   │   ├── __init__.py
│   │   ├── base.py             # Base settings
│   │   ├── development.py      # Development settings
│   │   ├── production.py       # Production settings
│   │   └── testing.py          # Testing settings
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── static/                     # Static files
├── templates/                  # HTML templates
├── docs/                       # Documentation
├── requirements/               # Split requirements
│   ├── base.txt                # Base requirements
│   ├── development.txt         # Development requirements
│   ├── production.txt          # Production requirements
│   └── testing.txt             # Testing requirements
├── manage.py
└── README.md
```

## API Endpoints

- `/` - Index endpoint to verify the API is running
- `/api/azure-openai-status/` - Status of Azure OpenAI integration

## TODOs for Future Improvements

### Core Infrastructure
- [ ] Implement actual Azure OpenAI integration using Azure SDK
- [ ] Create document ingestion and processing pipeline
- [ ] Implement authentication and authorization using Azure AD

### Azure Integration
- [ ] Configure Azure Database for PostgreSQL in production settings
- [ ] Set up Azure App Service deployment
- [ ] Implement Azure Key Vault for secure secrets management
- [ ] Configure Azure Blob Storage for static files and uploads
- [ ] Set up Azure Application Insights for monitoring

### Development & Operations
- [ ] Implement containerization with Docker
- [ ] Set up CI/CD pipeline with GitHub Actions
- [ ] Create comprehensive test suite
- [ ] Document API endpoints with Swagger/OpenAPI

### User Interface
- [ ] Implement Teams bot integration
- [ ] Create admin interface for content management

## Environment Setup
1. Copy `.env.example` to `.env`
2. Update `.env` with your local values
