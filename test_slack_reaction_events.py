import json
import logging
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/slack/events', methods=['POST'])
def slack_events():
    """Handle Slack events."""
    data = request.json
    logger.debug(f"Received Slack event: {json.dumps(data, indent=2)}")
    
    # Handle URL verification
    if data.get('type') == 'url_verification':
        return jsonify({'challenge': data.get('challenge')})
    
    # Handle events
    if data.get('type') == 'event_callback':
        event = data.get('event', {})
        event_type = event.get('type')
        
        logger.info(f"Received event type: {event_type}")
        
        if event_type == 'reaction_added' or event_type == 'reaction_removed':
            logger.info(f"Reaction event: {json.dumps(event, indent=2)}")
            
    return '', 200

if __name__ == '__main__':
    logger.info("Starting test server for Slack reaction events...")
    app.run(port=5000, debug=True)
