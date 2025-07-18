#!/usr/bin/env python3
"""
LinkedIn Job Application Bot - Production Grade
Automatically applies to jobs from a JSON file with profile information.
"""

import json
import time
import random
import os
import sys
import argparse
import signal
import traceback
import logging
from urllib.parse import urlparse
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# ========== Configuration ==========
@dataclass
class Config:
    """Configuration settings for the bot"""
    min_delay: float = 1.0
    max_delay: float = 3.0
    form_fill_delay: float = 0.1
    page_load_timeout: int = 30
    element_timeout: int = 10
    max_retries: int = 3
    
    # LinkedIn specific selectors
    linkedin_apply_selectors: List[str] = None
    
    def __post_init__(self):
        if self.linkedin_apply_selectors is None:
            self.linkedin_apply_selectors = [
                "//button[contains(@class, 'jobs-apply-button')]",
                "//button[contains(text(), 'Apply')]",
                "//a[contains(text(), 'Apply')]",
                "//button[@id='jobs-apply-button-id']",
                "//button[contains(@aria-label, 'Apply')]"
            ]

# ========== Global State ==========
class BotState:
    def __init__(self):
        self.applications_submitted = 0
        self.applications_failed = 0
        self.applications_skipped = 0
        self.driver = None
        self.config = Config()
        self.logger = None
        self.start_time = datetime.now()

bot_state = BotState()

# ========== Logging Setup ==========
def setup_logging(log_file: str = None, verbose: bool = False) -> logging.Logger:
    """Setup comprehensive logging"""
    logger = logging.getLogger('linkedin_bot')
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    return logger

# ========== Graceful Shutdown ==========
def handle_termination(signum, frame):
    """Handle graceful shutdown"""
    global bot_state
    
    bot_state.logger.warning("Process interrupted. Finalizing...")
    print_final_stats()
    
    if bot_state.driver:
        try:
            bot_state.driver.quit()
        except Exception as e:
            bot_state.logger.error(f"Error closing driver: {e}")
    
    sys.exit(0)

def print_final_stats():
    """Print final statistics"""
    duration = datetime.now() - bot_state.start_time
    bot_state.logger.info(f"📊 Final Stats:")
    bot_state.logger.info(f"   ✅ Submitted: {bot_state.applications_submitted}")
    bot_state.logger.info(f"   ❌ Failed: {bot_state.applications_failed}")
    bot_state.logger.info(f"   ⏭️ Skipped: {bot_state.applications_skipped}")
    bot_state.logger.info(f"   ⏱️ Duration: {duration}")

signal.signal(signal.SIGINT, handle_termination)
signal.signal(signal.SIGTERM, handle_termination)

# ========== Utility Functions ==========
def human_delay(min_seconds: float = None, max_seconds: float = None):
    """Simulate human-like delays"""
    if min_seconds is None:
        min_seconds = bot_state.config.min_delay
    if max_seconds is None:
        max_seconds = bot_state.config.max_delay
    
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def detect_platform(url: str) -> str:
    """Detect job platform from URL"""
    domain = urlparse(url).netloc.lower()
    
    platform_map = {
        'linkedin.com': 'linkedin',
        'indeed.com': 'indeed',
        'glassdoor.com': 'glassdoor',
        'workable.com': 'workable',
        'lever.co': 'lever',
        'greenhouse.io': 'greenhouse',
        'jobvite.com': 'jobvite',
        'smartrecruiters.com': 'smartrecruiters',
        'bamboohr.com': 'bamboohr',
        'recruitee.com': 'recruitee',
        'workday.com': 'workday'
    }
    
    for domain_key, platform in platform_map.items():
        if domain_key in domain:
            return platform
    
    return 'generic'

def load_json(file_path: str) -> Dict[str, Any]:
    """Load JSON file with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        bot_state.logger.error(f"File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        bot_state.logger.error(f"Invalid JSON in {file_path}: {e}")
        sys.exit(1)

def setup_driver(headless: bool = False, cookies_path: str = None) -> uc.Chrome:
    """Setup Chrome driver with optimal settings"""
    options = uc.ChromeOptions()
    
    if headless:
        options.add_argument('--headless')
    
    # Performance and stealth options
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-images')  # Faster loading
    options.add_argument('--disable-javascript')  # Only for non-JS forms
    
    # User agent
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    try:
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(bot_state.config.page_load_timeout)
        
        # Load cookies if provided
        if cookies_path and os.path.exists(cookies_path):
            bot_state.logger.info("Loading saved cookies...")
            driver.get("https://www.linkedin.com")
            
            with open(cookies_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
                for cookie in cookies:
                    try:
                        driver.add_cookie(cookie)
                    except Exception as e:
                        bot_state.logger.warning(f"Failed to add cookie: {e}")
            
            driver.refresh()
            time.sleep(3)
        
        return driver
        
    except Exception as e:
        bot_state.logger.error(f"Failed to setup driver: {e}")
        sys.exit(1)

# ========== Form Interaction Helpers ==========
def safe_find_element(driver, by, value, timeout=None):
    """Safely find element with timeout"""
    if timeout is None:
        timeout = bot_state.config.element_timeout
    
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        return None

def safe_click(driver, element, field_name: str = "") -> bool:
    """Safely click element with error handling"""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        human_delay(0.3, 0.7)
        
        # Try different click methods
        try:
            element.click()
        except WebDriverException:
            driver.execute_script("arguments[0].click();", element)
        
        bot_state.logger.debug(f"Clicked: {field_name}")
        return True
        
    except Exception as e:
        bot_state.logger.warning(f"Failed to click {field_name}: {e}")
        return False

def fill_text_field(driver, element, value: str, field_name: str = "") -> bool:
    """Fill text field with human-like typing"""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        human_delay(0.3, 0.7)
        
        # Clear field
        element.clear()
        human_delay(0.2, 0.4)
        
        # Type with human-like delays
        for char in str(value):
            element.send_keys(char)
            time.sleep(random.uniform(0.05, bot_state.config.form_fill_delay))
        
        bot_state.logger.debug(f"Filled {field_name}: {value}")
        return True
        
    except Exception as e:
        bot_state.logger.warning(f"Failed to fill {field_name}: {e}")
        return False

def upload_file(element, file_path: str, field_name: str) -> bool:
    """Upload file to input element"""
    if not os.path.exists(file_path):
        bot_state.logger.warning(f"File not found: {file_path}")
        return False
    
    try:
        abs_path = os.path.abspath(file_path)
        element.send_keys(abs_path)
        bot_state.logger.debug(f"Uploaded {field_name}: {file_path}")
        return True
        
    except Exception as e:
        bot_state.logger.warning(f"Failed to upload {field_name}: {e}")
        return False

def find_and_click(driver, xpath: str, timeout: int = 5) -> bool:
    """Find element by XPath and click"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        return safe_click(driver, element, xpath)
    except TimeoutException:
        return False

# ========== URL Prioritization ==========
def get_best_apply_url(job: Dict[str, Any]) -> Optional[str]:
    """Get the best application URL based on platform priority"""
    preferred_platforms = ['LinkedIn', 'Indeed', 'Glassdoor', 'Built In', 'SimplyHired']
    seen_urls = set()
    
    # Check applyLinksDetails first
    if 'applyLinksDetails' in job and job['applyLinksDetails']:
        sorted_links = sorted(
            job['applyLinksDetails'],
            key=lambda x: (
                preferred_platforms.index(x.get('platform', '')) 
                if x.get('platform') in preferred_platforms 
                else len(preferred_platforms)
            )
        )
        
        for link_obj in sorted_links:
            url = link_obj.get('url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                return url
    
    # Fallback to direct links
    links = job.get("link", [])
    if isinstance(links, str):
        links = [links]
    
    for url in links:
        if url and url not in seen_urls:
            seen_urls.add(url)
            return url
    
    return None

# ========== Enhanced Form Detection ==========
def detect_and_fill_form(driver, profile: Dict[str, Any]) -> bool:
    """Detect and fill various form types"""
    filled_fields = 0
    
    # Common field mappings
    field_mappings = {
        'email': ['email', 'e-mail', 'mail', 'email_address'],
        'first_name': ['first', 'firstname', 'fname', 'given_name'],
        'last_name': ['last', 'lastname', 'lname', 'family_name', 'surname'],
        'full_name': ['name', 'full_name', 'fullname', 'applicant_name'],
        'phone': ['phone', 'telephone', 'mobile', 'cell'],
        'address': ['address', 'street', 'location'],
        'city': ['city', 'town'],
        'state': ['state', 'province', 'region'],
        'zip': ['zip', 'postal', 'postcode'],
        'country': ['country'],
        'linkedin': ['linkedin', 'linkedin_url', 'linkedin_profile'],
        'website': ['website', 'portfolio', 'personal_website'],
        'cover_letter': ['cover_letter', 'coverletter', 'message', 'additional_info']
    }
    
    # Find and fill text inputs
    for field in driver.find_elements(By.TAG_NAME, "input"):
        field_type = field.get_attribute("type")
        if field_type in ['text', 'email', 'tel', 'url']:
            field_name = (field.get_attribute("name") or "").lower()
            field_id = (field.get_attribute("id") or "").lower()
            field_placeholder = (field.get_attribute("placeholder") or "").lower()
            
            # Check all identifiers
            identifiers = [field_name, field_id, field_placeholder]
            
            for profile_key, keywords in field_mappings.items():
                if profile_key in profile:
                    for keyword in keywords:
                        if any(keyword in identifier for identifier in identifiers):
                            if fill_text_field(driver, field, profile[profile_key], profile_key):
                                filled_fields += 1
                            break
    
    # Find and fill textareas
    for field in driver.find_elements(By.TAG_NAME, "textarea"):
        field_name = (field.get_attribute("name") or "").lower()
        field_id = (field.get_attribute("id") or "").lower()
        field_placeholder = (field.get_attribute("placeholder") or "").lower()
        
        identifiers = [field_name, field_id, field_placeholder]
        
        # Cover letter or additional info
        if any(keyword in identifier for identifier in identifiers for keyword in ['cover', 'message', 'additional', 'why', 'motivation']):
            if 'cover_letter' in profile:
                if fill_text_field(driver, field, profile['cover_letter'], 'cover_letter'):
                    filled_fields += 1
    
    # Handle file uploads
    for field in driver.find_elements(By.CSS_SELECTOR, "input[type='file']"):
        field_name = (field.get_attribute("name") or "").lower()
        field_id = (field.get_attribute("id") or "").lower()
        
        if any(keyword in field_name or keyword in field_id for keyword in ['resume', 'cv']):
            if 'resume_path' in profile:
                if upload_file(field, profile['resume_path'], 'resume'):
                    filled_fields += 1
        elif any(keyword in field_name or keyword in field_id for keyword in ['cover', 'letter']):
            if 'cover_letter_path' in profile:
                if upload_file(field, profile['cover_letter_path'], 'cover_letter'):
                    filled_fields += 1
    
    # Handle checkboxes and agreements
    for checkbox in driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
        try:
            label_text = ""
            # Try to find associated label
            checkbox_id = checkbox.get_attribute("id")
            if checkbox_id:
                label = driver.find_element(By.CSS_SELECTOR, f"label[for='{checkbox_id}']")
                label_text = label.text.lower()
            
            # Auto-check agreement checkboxes
            if any(keyword in label_text for keyword in ['agree', 'terms', 'privacy', 'consent']):
                if not checkbox.is_selected():
                    safe_click(driver, checkbox, 'agreement_checkbox')
                    filled_fields += 1
        except:
            continue
    
    bot_state.logger.info(f"Filled {filled_fields} form fields")
    return filled_fields > 0

# ========== LinkedIn Specific Handlers ==========
def handle_linkedin_application(driver, job: Dict[str, Any], profile: Dict[str, Any]) -> bool:
    """Handle LinkedIn specific application flow"""
    try:
        # Wait for page to load
        human_delay(3, 5)
        
        # Try multiple selectors for Apply button
        apply_clicked = False
        for selector in bot_state.config.linkedin_apply_selectors:
            if find_and_click(driver, selector):
                apply_clicked = True
                bot_state.logger.debug(f"Clicked apply button with selector: {selector}")
                break
        
        if not apply_clicked:
            bot_state.logger.warning("Could not find LinkedIn apply button")
            return False
        
        human_delay(2, 4)
        
        # Handle new window/tab
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            bot_state.logger.debug("Switched to new window")
            human_delay(2, 3)
        
        # Look for "Apply Now" or similar buttons
        apply_now_selectors = [
            "//button[contains(text(), 'Apply Now')]",
            "//button[contains(text(), 'Apply')]",
            "//a[contains(text(), 'Apply Now')]",
            "//input[@type='submit' and contains(@value, 'Apply')]"
        ]
        
        for selector in apply_now_selectors:
            if find_and_click(driver, selector):
                bot_state.logger.debug(f"Clicked apply now with selector: {selector}")
                break
        
        human_delay(2, 4)
        
        # Fill form
        if detect_and_fill_form(driver, profile):
            # Try to submit
            submit_selectors = [
                "//button[contains(text(), 'Submit')]",
                "//button[contains(text(), 'Apply')]",
                "//button[contains(text(), 'Send')]",
                "//input[@type='submit']"
            ]
            
            for selector in submit_selectors:
                if find_and_click(driver, selector):
                    bot_state.logger.info("Application submitted successfully")
                    return True
            
            bot_state.logger.warning("Could not find submit button")
            return False
        else:
            bot_state.logger.warning("Could not fill form")
            return False
            
    except Exception as e:
        bot_state.logger.error(f"LinkedIn application error: {e}")
        return False

# ========== Main Job Processing ==========
def process_job(driver, job: Dict[str, Any], profile: Dict[str, Any]) -> bool:
    """Process a single job application"""
    try:
        url = get_best_apply_url(job)
        if not url:
            bot_state.logger.warning("No valid application URL found")
            bot_state.applications_skipped += 1
            return False
        
        job_title = job.get('title', 'Unknown')
        company = job.get('companyName', 'Unknown')
        platform = detect_platform(url)
        
        bot_state.logger.info(f"Processing: {job_title} at {company}")
        bot_state.logger.info(f"Platform: {platform} | URL: {url}")
        
        # Navigate to job
        driver.get(url)
        human_delay(4, 6)
        
        # Platform-specific handling
        success = False
        if platform == 'linkedin':
            success = handle_linkedin_application(driver, job, profile)
        else:
            # Generic handling for other platforms
            success = handle_generic_application(driver, job, profile)
        
        if success:
            bot_state.applications_submitted += 1
            bot_state.logger.info("✅ Application submitted successfully")
        else:
            bot_state.applications_failed += 1
            bot_state.logger.warning("❌ Application failed")
        
        return success
        
    except Exception as e:
        bot_state.logger.error(f"Error processing job: {e}")
        bot_state.applications_failed += 1
        return False

def handle_generic_application(driver, job: Dict[str, Any], profile: Dict[str, Any]) -> bool:
    """Handle generic job application flow"""
    try:
        # Look for apply buttons
        apply_selectors = [
            "//button[contains(text(), 'Apply')]",
            "//a[contains(text(), 'Apply')]",
            "//button[contains(text(), 'Submit Application')]",
            "//input[@type='submit' and contains(@value, 'Apply')]"
        ]
        
        for selector in apply_selectors:
            if find_and_click(driver, selector):
                break
        
        human_delay(2, 4)
        
        # Fill form
        if detect_and_fill_form(driver, profile):
            # Try to submit
            submit_selectors = [
                "//button[contains(text(), 'Submit')]",
                "//button[contains(text(), 'Apply')]",
                "//button[contains(text(), 'Send')]",
                "//input[@type='submit']"
            ]
            
            for selector in submit_selectors:
                if find_and_click(driver, selector):
                    return True
        
        return False
        
    except Exception as e:
        bot_state.logger.error(f"Generic application error: {e}")
        return False

# ========== Main Function ==========
def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='LinkedIn Job Application Bot')
    parser.add_argument('--jobs-file', required=True, help='Path to jobs JSON file')
    parser.add_argument('--profile-file', required=True, help='Path to profile JSON file')
    parser.add_argument('--cookies-file', help='Path to cookies JSON file')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--max-applications', type=int, default=5, help='Maximum applications to submit')
    parser.add_argument('--log-file', help='Path to log file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--delay-min', type=float, default=1.0, help='Minimum delay between actions')
    parser.add_argument('--delay-max', type=float, default=3.0, help='Maximum delay between actions')
    
    args = parser.parse_args()
    
    # Setup logging
    bot_state.logger = setup_logging(args.log_file, args.verbose)
    
    # Update config
    bot_state.config.min_delay = args.delay_min
    bot_state.config.max_delay = args.delay_max
    
    # Load data
    bot_state.logger.info("Loading job data and profile...")
    job_data = load_json(args.jobs_file)
    profile = load_json(args.profile_file)
    
    # Validate profile
    required_fields = ['email', 'first_name', 'last_name']
    missing_fields = [field for field in required_fields if field not in profile]
    if missing_fields:
        bot_state.logger.error(f"Missing required profile fields: {missing_fields}")
        sys.exit(1)
    
    # Setup driver
    bot_state.logger.info("Setting up browser...")
    bot_state.driver = setup_driver(headless=args.headless, cookies_path=args.cookies_file)
    
    # Process jobs
    bot_state.logger.info(f"Processing up to {args.max_applications} jobs...")
    
    for i, job in enumerate(job_data):
        if i >= args.max_applications:
            break
        
        bot_state.logger.info(f"Job {i+1}/{min(len(job_data), args.max_applications)}")
        process_job(bot_state.driver, job, profile)
        
        # Delay between jobs
        if i < min(len(job_data), args.max_applications) - 1:
            delay = random.randint(15, 30)
            bot_state.logger.info(f"Waiting {delay}s before next job...")
            time.sleep(delay)
    
    # Cleanup
    bot_state.driver.quit()
    print_final_stats()
    bot_state.logger.info("Bot execution completed")

if __name__ == '__main__':
    main()