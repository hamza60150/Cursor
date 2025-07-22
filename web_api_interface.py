#!/usr/bin/env python3
"""
Web API Interface for Adaptive Job Application Bot
Provides REST API endpoints for website integration.
"""

import os
import json
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import threading
from concurrent.futures import ThreadPoolExecutor
import tempfile

from adaptive_web_agent import AdaptiveWebAgent, JobApplicationInput
from llm_integration import LLMIntegration, load_llm_config
from resume_parser import ResumeParser

app = Flask(__name__)
CORS(app)  # Enable CORS for web integration

# Global variables
agent_pool = {}
active_sessions = {}
executor = ThreadPoolExecutor(max_workers=5)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobApplicationAPI:
    """Main API class for job applications"""
    
    def __init__(self):
        self.llm_config = load_llm_config()
        self.llm = LLMIntegration(self.llm_config)
        self.resume_parser = ResumeParser()
    
    async def create_application_session(self, job_title: str, resume_data: Any, 
                                       website_html: str, website_url: str) -> str:
        """Create a new job application session"""
        try:
            session_id = str(uuid.uuid4())
            
            # Parse resume
            parsed_resume = await self.resume_parser.parse_resume(resume_data)
            
            # Create job input
            job_input = JobApplicationInput(
                job_title=job_title,
                parsed_resume=parsed_resume,
                target_html=website_html,
                website_url=website_url
            )
            
            # Create agent
            agent = AdaptiveWebAgent(self.llm)
            
            # Store session
            active_sessions[session_id] = {
                'agent': agent,
                'job_input': job_input,
                'status': 'initialized',
                'created_at': datetime.now().isoformat(),
                'progress': []
            }
            
            logger.info(f"Created application session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    async def start_application_process(self, session_id: str) -> Dict[str, Any]:
        """Start the job application process"""
        try:
            if session_id not in active_sessions:
                return {"error": "Session not found"}
            
            session = active_sessions[session_id]
            session['status'] = 'running'
            
            # Run application in background
            result = await session['agent'].auto_apply_job(session['job_input'])
            
            session['status'] = 'completed' if result['success'] else 'failed'
            session['result'] = result
            session['completed_at'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in application process: {e}")
            if session_id in active_sessions:
                active_sessions[session_id]['status'] = 'error'
                active_sessions[session_id]['error'] = str(e)
            return {"success": False, "error": str(e)}

# Initialize API
api = JobApplicationAPI()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_sessions': len(active_sessions),
        'llm_provider': api.llm_config.provider.value
    })

@app.route('/api/apply-job', methods=['POST'])
def apply_job():
    """Main endpoint to start job application process"""
    try:
        # Validate request
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        
        # Required fields
        required_fields = ['job_title', 'resume', 'website_html', 'website_url']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Extract data
        job_title = data['job_title']
        resume_data = data['resume']  # Can be text, file path, or base64
        website_html = data['website_html']
        website_url = data['website_url']
        
        # Create session
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        session_id = loop.run_until_complete(
            api.create_application_session(job_title, resume_data, website_html, website_url)
        )
        
        # Start application process in background
        def run_application():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(api.start_application_process(session_id))
        
        # Submit to executor
        future = executor.submit(run_application)
        
        return jsonify({
            'session_id': session_id,
            'status': 'started',
            'message': 'Job application process started'
        })
        
    except Exception as e:
        logger.error(f"Error in apply_job endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/<session_id>/status', methods=['GET'])
def get_session_status(session_id):
    """Get status of a job application session"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session = active_sessions[session_id]
        
        response = {
            'session_id': session_id,
            'status': session['status'],
            'created_at': session['created_at'],
            'job_title': session['job_input'].job_title,
            'website_url': session['job_input'].website_url,
            'progress': session.get('progress', [])
        }
        
        if 'completed_at' in session:
            response['completed_at'] = session['completed_at']
        
        if 'result' in session:
            response['result'] = session['result']
        
        if 'error' in session:
            response['error'] = session['error']
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/<session_id>/cancel', methods=['POST'])
def cancel_session(session_id):
    """Cancel a job application session"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session = active_sessions[session_id]
        
        # Cancel the session
        session['status'] = 'cancelled'
        session['cancelled_at'] = datetime.now().isoformat()
        
        # Cleanup browser if running
        if 'agent' in session and session['agent'].driver:
            try:
                session['agent'].driver.quit()
            except:
                pass
        
        return jsonify({
            'session_id': session_id,
            'status': 'cancelled',
            'message': 'Session cancelled successfully'
        })
        
    except Exception as e:
        logger.error(f"Error cancelling session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """List all active sessions"""
    try:
        sessions_info = []
        for session_id, session in active_sessions.items():
            sessions_info.append({
                'session_id': session_id,
                'status': session['status'],
                'job_title': session['job_input'].job_title,
                'website_url': session['job_input'].website_url,
                'created_at': session['created_at']
            })
        
        return jsonify({
            'sessions': sessions_info,
            'total_count': len(sessions_info)
        })
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a website"""
    try:
        data = request.get_json()
        website_url = data.get('website_url')
        
        if not website_url:
            return jsonify({'error': 'website_url is required'}), 400
        
        # Test connection
        import requests
        response = requests.get(website_url, timeout=10)
        
        return jsonify({
            'success': True,
            'status_code': response.status_code,
            'accessible': response.status_code == 200,
            'content_length': len(response.content)
        })
        
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/parse-resume', methods=['POST'])
def parse_resume_endpoint():
    """Parse resume data"""
    try:
        data = request.get_json()
        resume_data = data.get('resume_data')
        
        if not resume_data:
            return jsonify({'error': 'resume_data is required'}), 400
        
        # Parse resume
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        parsed_resume = loop.run_until_complete(
            api.resume_parser.parse_resume(resume_data)
        )
        
        return jsonify({
            'success': True,
            'parsed_resume': parsed_resume
        })
        
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/analyze-website', methods=['POST'])
def analyze_website():
    """Analyze website structure for job application potential"""
    try:
        data = request.get_json()
        website_html = data.get('website_html')
        website_url = data.get('website_url')
        
        if not website_html:
            return jsonify({'error': 'website_html is required'}), 400
        
        # Create temporary job input for analysis
        temp_job_input = JobApplicationInput(
            job_title="Test Position",
            parsed_resume={"name": "Test User"},
            target_html=website_html,
            website_url=website_url or "https://example.com"
        )
        
        # Analyze with LLM
        agent = AdaptiveWebAgent(api.llm)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        analysis = loop.run_until_complete(
            agent._analyze_page_with_llm(website_html, temp_job_input, 1)
        )
        
        return jsonify({
            'success': True,
            'analysis': {
                'page_type': analysis.page_type,
                'confidence_score': analysis.confidence_score,
                'detected_elements': analysis.detected_elements,
                'obstacles': analysis.obstacles,
                'suggested_actions_count': len(analysis.suggested_actions)
            }
        })
        
    except Exception as e:
        logger.error(f"Error analyzing website: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'llm_provider': api.llm_config.provider.value,
        'llm_model': api.llm_config.model,
        'max_concurrent_sessions': 5,
        'supported_features': [
            'adaptive_navigation',
            'llm_analysis',
            'cookie_management',
            'bot_detection_handling',
            'multi_platform_support'
        ]
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def cleanup_old_sessions():
    """Cleanup old sessions periodically"""
    import time
    from datetime import datetime, timedelta
    
    while True:
        try:
            current_time = datetime.now()
            sessions_to_remove = []
            
            for session_id, session in active_sessions.items():
                created_at = datetime.fromisoformat(session['created_at'])
                if current_time - created_at > timedelta(hours=2):  # Remove sessions older than 2 hours
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                if session_id in active_sessions:
                    # Cleanup browser
                    session = active_sessions[session_id]
                    if 'agent' in session and hasattr(session['agent'], 'driver') and session['agent'].driver:
                        try:
                            session['agent'].driver.quit()
                        except:
                            pass
                    
                    del active_sessions[session_id]
                    logger.info(f"Cleaned up old session: {session_id}")
            
            time.sleep(300)  # Check every 5 minutes
            
        except Exception as e:
            logger.error(f"Error in session cleanup: {e}")
            time.sleep(300)

if __name__ == '__main__':
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_old_sessions, daemon=True)
    cleanup_thread.start()
    
    # Start API server
    port = int(os.getenv('API_PORT', 8000))
    host = os.getenv('API_HOST', '0.0.0.0')
    
    logger.info(f"Starting Adaptive Job Application API on {host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)
