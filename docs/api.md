# Konveyor API Documentation

## Endpoints

### Core API

#### `GET /`

Returns the status of the API.

**Response**:
```json
{
  "status": "ok",
  "message": "Konveyor API is running",
  "version": "0.1.0"
}
```

### Azure Integration API

#### `GET /api/azure-openai-status/`

Returns the status of Azure OpenAI integration.

**Response**:
```json
{
  "status": "ok",
  "integration": "Azure OpenAI",
  "configured": true,
  "message": "Placeholder for Azure OpenAI integration"
}
```

## Future Endpoints

### Document Management

#### `POST /api/documents/`

Upload a document for indexing and analysis.

#### `GET /api/documents/`

List available documents.

#### `GET /api/documents/{id}/`

Get document details.

### Knowledge Base

#### `POST /api/query/`

Send a natural language query to the knowledge base.

#### `GET /api/topics/`

Get list of available knowledge topics.

### User Management

#### `POST /api/auth/login/`

Authenticate user.

#### `GET /api/auth/me/`

Get current user profile. 