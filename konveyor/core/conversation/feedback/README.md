# Feedback Mechanism for Konveyor

This module provides a feedback mechanism for collecting, storing, and analyzing user feedback on bot responses.

## Overview

The feedback mechanism allows users to provide feedback on bot responses using Slack reactions (👍/👎). This feedback is stored and can be used to improve the bot's responses over time.

## Components

### Core Components

- **FeedbackService**: The main service for processing feedback events and managing feedback data.
- **FeedbackStorageProvider**: An interface for feedback storage providers.
- **DjangoFeedbackRepository**: A Django-based implementation of the feedback storage provider.
- **FeedbackType**: An enumeration of feedback types (positive, negative, neutral, removed).

### Integration with Existing Storage

The feedback mechanism integrates with the existing conversation storage mechanisms in Konveyor:

1. Primary feedback data is stored in Django models for efficient querying and reporting.
2. Additional metadata is stored in the conversation storage for context and correlation.
3. The repository pattern allows for different storage implementations while maintaining a consistent API.

### Integration with Slack

The feedback mechanism integrates with Slack by:

1. Processing `reaction_added` and `reaction_removed` events from Slack.
2. Mapping reactions to feedback types (👍 = positive, 👎 = negative).
3. Storing the feedback along with the original question and answer.

### API Endpoints

The feedback mechanism provides the following API endpoints:

- `/api/bot/feedback/stats/`: Get feedback statistics.
- `/api/bot/feedback/by-skill/`: Get feedback statistics grouped by skill.
- `/api/bot/feedback/export/`: Export feedback data in JSON or CSV format.

## Usage

### Initializing the Feedback Service

```python
from konveyor.core.conversation.feedback.factory import create_feedback_service

# Create a feedback service with the default storage provider
feedback_service = create_feedback_service()
```

### Processing Feedback Events

```python
# Process a reaction event from Slack
feedback = feedback_service.process_reaction_event(event)
```

### Getting Feedback Statistics

```python
# Get feedback statistics for the last 30 days
stats = feedback_service.get_feedback_stats(days=30)

# Get feedback statistics grouped by skill
skill_stats = feedback_service.get_feedback_by_skill(days=30)
```

### Exporting Feedback Data

```python
# Export feedback data as JSON
json_data = feedback_service.export_feedback_data(days=30, format='json')

# Export feedback data as CSV
csv_data = feedback_service.export_feedback_data(days=30, format='csv')
```

## Storage Architecture

The feedback mechanism uses a dual-storage approach:

1. **Django Models**: The `BotFeedback` model in `konveyor/apps/bot/models.py` stores the primary feedback data, including:
   - Message identifiers (timestamp, channel)
   - User information
   - Feedback type and reaction
   - Message content (question, answer)
   - Metadata (skill used, function used)

2. **Conversation Storage**: The existing conversation storage in `konveyor/core/conversation/storage.py` is used to store additional metadata and link feedback to conversations. This allows for:
   - Correlation between feedback and conversation context
   - Retrieval of feedback in the context of a conversation
   - Integration with existing conversation analytics

## Integration with Azure

The feedback data can be integrated with Azure dashboards and analytics by:

1. Using the API endpoints to export feedback data.
2. Setting up Azure Logic Apps or Functions to periodically fetch the data.
3. Storing the data in Azure Storage or Cosmos DB.
4. Visualizing the data using Azure Dashboard or Power BI.

## Future Improvements

- Add more sophisticated feedback analysis using Azure AI services.
- Implement feedback-based learning to improve the bot's responses.
- Add more feedback types beyond simple positive/negative reactions.
- Implement user-specific feedback analysis to personalize responses.
