"""
Utility functions for LinkedIn Job Application Bot
"""

import os
import json
import time
import random
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from pathlib import Path

def setup_directories():
    """Create necessary directories for the bot"""
    directories = ['logs', 'screenshots', 'data', 'cookies']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)

def save_cookies(driver, filepath: str):
    """Save browser cookies to file"""
    try:
        cookies = driver.get_cookies()
        with open(filepath, 'w') as f:
            json.dump(cookies, f, indent=2)
        logging.info(f"Cookies saved to {filepath}")
    except Exception as e:
        logging.error(f"Failed to save cookies: {e}")

def load_cookies(driver, filepath: str):
    """Load cookies from file into browser"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
            logging.info(f"Cookies loaded from {filepath}")
            return True
    except Exception as e:
        logging.error(f"Failed to load cookies: {e}")
    return False

def take_screenshot(driver, name: str, directory: str = "screenshots"):
    """Take a screenshot with timestamp"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = os.path.join(directory, filename)
        
        Path(directory).mkdir(exist_ok=True)
        driver.save_screenshot(filepath)
        logging.debug(f"Screenshot saved: {filepath}")
        return filepath
    except Exception as e:
        logging.error(f"Failed to take screenshot: {e}")
        return None

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:100]  # Limit length

def validate_profile(profile: Dict[str, Any]) -> List[str]:
    """Validate profile data and return list of missing required fields"""
    required_fields = ['email', 'first_name', 'last_name']
    optional_fields = ['phone', 'address', 'city', 'state', 'zip', 'country', 
                      'linkedin', 'website', 'resume_path', 'cover_letter']
    
    missing_fields = []
    
    for field in required_fields:
        if field not in profile or not profile[field]:
            missing_fields.append(field)
    
    # Check if resume file exists
    if 'resume_path' in profile and profile['resume_path']:
        if not os.path.exists(profile['resume_path']):
            missing_fields.append('resume_path (file not found)')
    
    return missing_fields

def validate_jobs_data(jobs_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate jobs data and return statistics"""
    stats = {
        'total_jobs': len(jobs_data),
        'jobs_with_apply_links': 0,
        'jobs_with_linkedin_links': 0,
        'platform_distribution': {},
        'invalid_jobs': []
    }
    
    for i, job in enumerate(jobs_data):
        # Check required fields
        required_fields = ['title', 'companyName']
        missing_fields = [field for field in required_fields if field not in job]
        
        if missing_fields:
            stats['invalid_jobs'].append({
                'index': i,
                'title': job.get('title', 'Unknown'),
                'missing_fields': missing_fields
            })
            continue
        
        # Check for apply links
        has_apply_links = False
        if 'applyLinksDetails' in job and job['applyLinksDetails']:
            has_apply_links = True
            stats['jobs_with_apply_links'] += 1
            
            # Count platforms
            for link in job['applyLinksDetails']:
                platform = link.get('platform', 'Unknown')
                stats['platform_distribution'][platform] = stats['platform_distribution'].get(platform, 0) + 1
                
                if platform.lower() == 'linkedin':
                    stats['jobs_with_linkedin_links'] += 1
        
        elif 'link' in job and job['link']:
            has_apply_links = True
            stats['jobs_with_apply_links'] += 1
    
    return stats

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"

def get_random_user_agent() -> str:
    """Get a random user agent string"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ]
    return random.choice(user_agents)

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters that might cause issues
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    return text.strip()

def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def get_domain_from_url(url: str) -> str:
    """Extract domain from URL"""
    try:
        return urlparse(url).netloc.lower()
    except:
        return ""

def create_backup(filepath: str) -> str:
    """Create a backup of a file"""
    try:
        if os.path.exists(filepath):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{filepath}.backup_{timestamp}"
            
            import shutil
            shutil.copy2(filepath, backup_path)
            logging.info(f"Backup created: {backup_path}")
            return backup_path
    except Exception as e:
        logging.error(f"Failed to create backup: {e}")
    return ""

def log_application_attempt(job: Dict[str, Any], success: bool, error: str = None):
    """Log application attempt details"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'job_title': job.get('title', 'Unknown'),
        'company': job.get('companyName', 'Unknown'),
        'success': success,
        'error': error
    }
    
    # Append to applications log
    log_file = "data/applications_log.json"
    Path("data").mkdir(exist_ok=True)
    
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_entry)
        
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
            
    except Exception as e:
        logging.error(f"Failed to log application attempt: {e}")

def get_application_stats() -> Dict[str, Any]:
    """Get application statistics from log"""
    log_file = "data/applications_log.json"
    
    if not os.path.exists(log_file):
        return {'total': 0, 'successful': 0, 'failed': 0}
    
    try:
        with open(log_file, 'r') as f:
            logs = json.load(f)
        
        total = len(logs)
        successful = sum(1 for log in logs if log.get('success', False))
        failed = total - successful
        
        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0
        }
    except Exception as e:
        logging.error(f"Failed to get application stats: {e}")
        return {'total': 0, 'successful': 0, 'failed': 0}

def smart_delay(base_delay: float = 1.0, variance: float = 0.5) -> float:
    """Generate smart delay with variance"""
    delay = base_delay + random.uniform(-variance, variance)
    return max(0.1, delay)  # Minimum 0.1 seconds

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying functions on failure"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(delay * (attempt + 1))
            return None
        return wrapper
    return decorator