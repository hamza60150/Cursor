#!/usr/bin/env python3
"""
GitHub Webhook Handler for LinkedIn Job Application Bot
Handles GitHub events and automates responses.
"""

import os
import json
import logging
import hmac
import hashlib
from typing import Dict, Any
from datetime import datetime
from flask import Flask, request, jsonify
import asyncio
import threading

from github_integration import GitHubIntegration, load_github_config
from llm_integration import LLMIntegration, load_llm_config

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Global integrations
github_integration = None
llm_integration = None

def verify_webhook_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature"""
    if not signature.startswith('sha256='):
        return False
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature[7:], expected_signature)

@app.route('/webhook/github', methods=['POST'])
def handle_github_webhook():
    """Handle incoming GitHub webhook events"""
    try:
        # Verify signature
        signature = request.headers.get('X-Hub-Signature-256', '')
        payload = request.get_data()
        
        github_config = load_github_config()
        if github_config.webhook_secret and not verify_webhook_signature(payload, signature, github_config.webhook_secret):
            logger.warning("Invalid webhook signature")
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Parse event
        event_type = request.headers.get('X-GitHub-Event')
        payload_data = request.get_json()
        
        logger.info(f"Received GitHub webhook: {event_type}")
        
        # Handle different event types
        if event_type == 'issues':
            return handle_issues_event(payload_data)
        elif event_type == 'issue_comment':
            return handle_issue_comment_event(payload_data)
        elif event_type == 'push':
            return handle_push_event(payload_data)
        elif event_type == 'schedule':
            return handle_schedule_event(payload_data)
        else:
            logger.info(f"Unhandled event type: {event_type}")
            return jsonify({'message': 'Event received but not handled'}), 200
        
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def handle_issues_event(payload: Dict[str, Any]):
    """Handle issues events (opened, closed, labeled, etc.)"""
    try:
        action = payload.get('action')
        issue = payload.get('issue', {})
        issue_number = issue.get('number')
        labels = [label['name'] for label in issue.get('labels', [])]
        
        logger.info(f"Issue {issue_number} {action}")
        
        # Handle job application issues
        if 'job-application' in labels:
            if action == 'opened':
                return handle_new_job_application_issue(issue)
            elif action == 'closed':
                return handle_closed_job_application_issue(issue)
            elif action == 'labeled':
                return handle_labeled_job_application_issue(issue, payload.get('label', {}))
        
        return jsonify({'message': 'Issue event processed'}), 200
        
    except Exception as e:
        logger.error(f"Error handling issues event: {e}")
        return jsonify({'error': 'Failed to process issue event'}), 500

def handle_issue_comment_event(payload: Dict[str, Any]):
    """Handle issue comment events"""
    try:
        action = payload.get('action')
        issue = payload.get('issue', {})
        comment = payload.get('comment', {})
        
        if action != 'created':
            return jsonify({'message': 'Comment event ignored'}), 200
        
        issue_number = issue.get('number')
        comment_body = comment.get('body', '').lower()
        labels = [label['name'] for label in issue.get('labels', [])]
        
        # Handle commands in job application issues
        if 'job-application' in labels:
            if '/status' in comment_body:
                return handle_status_command(issue, comment)
            elif '/follow-up' in comment_body:
                return handle_follow_up_command(issue, comment)
            elif '/analyze' in comment_body:
                return handle_analyze_command(issue, comment)
        
        return jsonify({'message': 'Comment processed'}), 200
        
    except Exception as e:
        logger.error(f"Error handling comment event: {e}")
        return jsonify({'error': 'Failed to process comment'}), 500

def handle_new_job_application_issue(issue: Dict[str, Any]):
    """Handle newly created job application issues"""
    try:
        # Extract job information from issue body
        issue_body = issue.get('body', '')
        issue_number = issue.get('number')
        
        logger.info(f"Processing new job application issue #{issue_number}")
        
        # Add automatic labels and comments
        if github_integration:
            # Schedule follow-up reminder
            threading.Thread(
                target=schedule_follow_up_reminder,
                args=(issue_number, 7)  # 7 days
            ).start()
        
        return jsonify({'message': 'New job application issue processed'}), 200
        
    except Exception as e:
        logger.error(f"Error processing new job application: {e}")
        return jsonify({'error': 'Failed to process new job application'}), 500

def handle_status_command(issue: Dict[str, Any], comment: Dict[str, Any]):
    """Handle /status command in issue comments"""
    try:
        comment_body = comment.get('body', '')
        issue_number = issue.get('number')
        
        # Parse status from comment
        # Format: /status <new_status> [notes]
        parts = comment_body.split()
        if len(parts) < 2:
            return jsonify({'error': 'Invalid status command format'}), 400
        
        new_status = parts[1].lower()
        notes = ' '.join(parts[2:]) if len(parts) > 2 else ''
        
        valid_statuses = ['applied', 'interview', 'rejected', 'offer', 'withdrawn']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Valid statuses: {", ".join(valid_statuses)}'}), 400
        
        # Update status
        if github_integration:
            asyncio.run(github_integration.update_application_status(issue_number, new_status, notes))
        
        return jsonify({'message': f'Status updated to {new_status}'}), 200
        
    except Exception as e:
        logger.error(f"Error handling status command: {e}")
        return jsonify({'error': 'Failed to update status'}), 500

def handle_follow_up_command(issue: Dict[str, Any], comment: Dict[str, Any]):
    """Handle /follow-up command"""
    try:
        issue_number = issue.get('number')
        
        # Generate follow-up message using LLM if available
        if llm_integration and github_integration:
            # Extract job data from issue
            job_data = extract_job_data_from_issue(issue)
            profile_data = load_default_profile()  # You'll need to implement this
            
            follow_up_message = asyncio.run(
                llm_integration.generate_follow_up_message(job_data, profile_data)
            )
            
            # Add comment with follow-up message
            comment_body = f"**Generated Follow-up Message:**\n\n{follow_up_message}\n\n*Generated automatically by LLM integration*"
            
            # Post comment (you'll need to implement this)
            # github_integration.add_comment_to_issue(issue_number, comment_body)
        
        return jsonify({'message': 'Follow-up message generated'}), 200
        
    except Exception as e:
        logger.error(f"Error handling follow-up command: {e}")
        return jsonify({'error': 'Failed to generate follow-up'}), 500

def schedule_follow_up_reminder(issue_number: int, days: int):
    """Schedule a follow-up reminder for an issue"""
    import time
    
    # Wait for the specified number of days
    time.sleep(days * 24 * 60 * 60)  # Convert days to seconds
    
    try:
        if github_integration:
            reminder_message = f"""
**Follow-up Reminder** 🔔

It's been {days} days since you applied for this position. Consider:
- [ ] Checking the application status on the company's website
- [ ] Sending a polite follow-up email to the hiring manager
- [ ] Connecting with employees at the company on LinkedIn
- [ ] Updating the status of this application

*This is an automated reminder. Update the issue status when you have news!*
            """
            
            # Add comment to issue (implement this method in GitHubIntegration)
            # asyncio.run(github_integration.add_comment_to_issue(issue_number, reminder_message))
            
    except Exception as e:
        logger.error(f"Error sending follow-up reminder: {e}")

def extract_job_data_from_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Extract job data from issue body"""
    # This is a simplified implementation
    # You would parse the issue body to extract job details
    title = issue.get('title', '')
    body = issue.get('body', '')
    
    # Basic parsing - you might want to make this more sophisticated
    job_data = {
        'title': title.replace('Job Application: ', '').split(' at ')[0] if ' at ' in title else 'Unknown',
        'companyName': title.split(' at ')[-1] if ' at ' in title else 'Unknown',
        'location': 'Unknown',
        'description': body
    }
    
    return job_data

def load_default_profile() -> Dict[str, Any]:
    """Load default profile data"""
    # Load from your profile file
    try:
        profile_file = os.getenv('PROFILE_FILE', 'profile.json')
        with open(profile_file, 'r') as f:
            return json.load(f)
    except:
        return {}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'integrations': {
            'github': github_integration is not None,
            'llm': llm_integration is not None
        }
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get application statistics"""
    try:
        if not github_integration:
            return jsonify({'error': 'GitHub integration not available'}), 503
        
        stats = asyncio.run(github_integration.get_application_statistics())
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500

def initialize_integrations():
    """Initialize global integrations"""
    global github_integration, llm_integration
    
    try:
        github_config = load_github_config()
        if github_config.token:
            github_integration = GitHubIntegration(github_config)
            logger.info("GitHub integration initialized")
        
        llm_config = load_llm_config()
        if llm_config.api_key or llm_config.provider.value == 'ollama':
            llm_integration = LLMIntegration(llm_config)
            logger.info(f"LLM integration initialized: {llm_config.provider.value}")
            
    except Exception as e:
        logger.error(f"Error initializing integrations: {e}")

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize integrations
    initialize_integrations()
    
    # Run webhook server
    port = int(os.getenv('WEBHOOK_PORT', 5000))
    host = os.getenv('WEBHOOK_HOST', '0.0.0.0')
    
    logger.info(f"Starting webhook server on {host}:{port}")
    app.run(host=host, port=port, debug=False)
