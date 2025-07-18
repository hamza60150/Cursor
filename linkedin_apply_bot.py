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
    total_jobs = bot_state.applications_submitted + bot_state.applications_failed + bot_state.applications_skipped
    success_rate = (bot_state.applications_submitted / total_jobs * 100) if total_jobs > 0 else 0
    
    bot_state.logger.info(f"📊 Final Stats:")
    bot_state.logger.info(f"   ✅ Submitted: {bot_state.applications_submitted}")
    bot_state.logger.info(f"   ❌ Failed: {bot_state.applications_failed}")
    bot_state.logger.info(f"   ⏭️ Skipped: {bot_state.applications_skipped}")
    bot_state.logger.info(f"   📈 Success Rate: {success_rate:.1f}%")
    bot_state.logger.info(f"   ⏱️ Duration: {duration}")

def log_application_attempt(job: Dict[str, Any], platform: str, success: bool, error: str = None):
    """Log individual application attempt"""
    from utils import log_application_attempt as utils_log
    try:
        utils_log(job, success, error)
    except:
        # Fallback logging if utils function fails
        pass

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
        'workday.com': 'workday',
        'dice.com': 'dice',
        'ziprecruiter.com': 'ziprecruiter',
        'builtin.com': 'builtin',
        'builtinla.com': 'builtin',
        'builtinseattle.com': 'builtin',
        'builtincolorado.com': 'builtin',
        'themuse.com': 'themuse',
        'simplyhired.com': 'simplyhired',
        'bebee.com': 'bebee',
        'talentify.io': 'talentify',
        'tealhq.com': 'teal',
        'himalayas.app': 'himalayas',
        'startup.jobs': 'startupjobs',
        'jooble.org': 'jooble',
        'whatjobs.com': 'whatjobs',
        'theladders.com': 'ladders',
        'clearancejobs.com': 'clearancejobs',
        'clearedcareers.com': 'clearedcareers',
        'jsfirm.com': 'jsfirm',
        'recruit.net': 'recruitnet'
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

def normalize_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize profile data to flat structure for compatibility"""
    normalized = {}
    
    # Handle nested structure
    if 'personal_info' in profile:
        personal = profile['personal_info']
        normalized['email'] = personal.get('email', '')
        normalized['first_name'] = personal.get('first_name', '')
        normalized['last_name'] = personal.get('last_name', '')
        normalized['full_name'] = personal.get('full_name', '')
        normalized['phone'] = personal.get('phone', '')
        normalized['linkedin'] = personal.get('linkedin_url', '')
        normalized['website'] = personal.get('website', '')
        
        # Handle nested address
        if 'address' in personal:
            addr = personal['address']
            normalized['address'] = addr.get('street', '')
            normalized['city'] = addr.get('city', '')
            normalized['state'] = addr.get('state', '')
            normalized['zip'] = addr.get('zip_code', '')
            normalized['country'] = addr.get('country', '')
    
    # Handle file paths
    if 'files' in profile:
        files = profile['files']
        normalized['resume_path'] = files.get('resume_path', '')
        normalized['cover_letter_path'] = files.get('cover_letter_path', '')
    
    # Handle questionnaire responses for cover letter
    if 'questionnaire_responses' in profile:
        common = profile['questionnaire_responses'].get('common_questions', {})
        normalized['cover_letter'] = common.get('why_interested', '')
    
    # Handle professional info
    if 'professional_info' in profile:
        prof = profile['professional_info']
        normalized['current_title'] = prof.get('current_title', '')
        normalized['years_experience'] = str(prof.get('years_of_experience', ''))
        normalized['desired_salary'] = prof.get('desired_salary', '')
        
        # Handle availability
        if 'availability' in prof:
            avail = prof['availability']
            normalized['start_date'] = avail.get('start_date', '')
            normalized['notice_period'] = avail.get('notice_period', '')
            normalized['willing_to_relocate'] = avail.get('willing_to_relocate', False)
    
    # Handle education (use most recent)
    if 'education' in profile and profile['education']:
        education = profile['education'][0]  # Use first (most recent)
        normalized['education_degree'] = education.get('degree', '')
        normalized['education_field'] = education.get('field', '')
        normalized['education_school'] = education.get('school', '')
        normalized['graduation_year'] = education.get('graduation_year', '')
    
    # Handle skills
    if 'skills' in profile:
        skills = profile['skills']
        # Combine all skills into a comma-separated string
        all_skills = []
        for skill_category in skills.values():
            if isinstance(skill_category, list):
                all_skills.extend(skill_category)
        normalized['skills'] = ', '.join(all_skills)
    
    # Handle boolean responses
    if 'questionnaire_responses' in profile:
        boolean_resp = profile['questionnaire_responses'].get('boolean_responses', {})
        normalized['authorized_to_work'] = boolean_resp.get('authorized_to_work', True)
        normalized['require_sponsorship'] = boolean_resp.get('require_sponsorship', False)
        normalized['background_check_consent'] = boolean_resp.get('background_check_consent', True)
    
    # Fallback to original structure if no nested structure found
    if not normalized and 'personal_info' not in profile:
        normalized = profile.copy()
    
    return normalized

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
            
            # Use the improved cookie loading function
            from utils import load_cookies
            if load_cookies(driver, cookies_path):
                # Navigate back to LinkedIn after loading cookies
                driver.get("https://www.linkedin.com")
                time.sleep(3)
                bot_state.logger.info("Cookies loaded successfully, navigated to LinkedIn")
            else:
                bot_state.logger.warning("Cookie loading failed, continuing without cookies")
                # Still navigate to LinkedIn
                driver.get("https://www.linkedin.com")
                time.sleep(2)
        
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
def get_prioritized_apply_urls(job: Dict[str, Any]) -> List[Dict[str, str]]:
    """Get prioritized list of application URLs to try in order"""
    preferred_platforms = ['LinkedIn', 'Indeed', 'Glassdoor', 'Built In', 'SimplyHired', 'Dice', 'ZipRecruiter']
    seen_urls = set()
    prioritized_urls = []
    
    # Check apply_links first (new format)
    if 'apply_links' in job and job['apply_links']:
        # Sort by platform priority
        sorted_links = sorted(
            job['apply_links'],
            key=lambda x: (
                preferred_platforms.index(x.get('platform', '')) 
                if x.get('platform') in preferred_platforms 
                else len(preferred_platforms)
            )
        )
        
        for link_obj in sorted_links:
            url = link_obj.get('url')
            platform = link_obj.get('platform', 'Unknown')
            if url and url not in seen_urls:
                seen_urls.add(url)
                prioritized_urls.append({
                    'url': url,
                    'platform': platform,
                    'title': link_obj.get('title', f'Apply on {platform}')
                })
    
    # Fallback to applyLinksDetails (old format)
    elif 'applyLinksDetails' in job and job['applyLinksDetails']:
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
            platform = link_obj.get('platform', 'Unknown')
            if url and url not in seen_urls:
                seen_urls.add(url)
                prioritized_urls.append({
                    'url': url,
                    'platform': platform,
                    'title': f'Apply on {platform}'
                })
    
    # Fallback to direct links
    links = job.get("link", [])
    if isinstance(links, str):
        links = [links]
    
    for url in links:
        if url and url not in seen_urls:
            seen_urls.add(url)
            prioritized_urls.append({
                'url': url,
                'platform': 'Generic',
                'title': 'Apply'
            })
    
    return prioritized_urls

# ========== Enhanced Form Detection ==========
def detect_and_fill_form(driver, profile: Dict[str, Any]) -> bool:
    """Detect and fill various form types"""
    filled_fields = 0
    
    # Common field mappings
    field_mappings = {
        'email': ['email', 'e-mail', 'mail', 'email_address', 'emailaddress'],
        'first_name': ['first', 'firstname', 'fname', 'given_name', 'givenname'],
        'last_name': ['last', 'lastname', 'lname', 'family_name', 'surname', 'familyname'],
        'full_name': ['name', 'full_name', 'fullname', 'applicant_name', 'applicantname'],
        'phone': ['phone', 'telephone', 'mobile', 'cell', 'phonenumber'],
        'address': ['address', 'street', 'location', 'streetaddress'],
        'city': ['city', 'town', 'locality'],
        'state': ['state', 'province', 'region', 'administrativearea'],
        'zip': ['zip', 'postal', 'postcode', 'postalcode', 'zipcode'],
        'country': ['country', 'nation'],
        'linkedin': ['linkedin', 'linkedin_url', 'linkedin_profile', 'linkedinurl'],
        'website': ['website', 'portfolio', 'personal_website', 'personalwebsite', 'url'],
        'cover_letter': ['cover_letter', 'coverletter', 'message', 'additional_info', 'additionalinfo', 'motivation'],
        'current_title': ['title', 'position', 'current_title', 'job_title', 'jobtitle'],
        'years_experience': ['experience', 'years_experience', 'yearsexperience', 'years_exp', 'work_experience'],
        'desired_salary': ['salary', 'desired_salary', 'expected_salary', 'salary_expectation', 'compensation'],
        'start_date': ['start_date', 'available_date', 'availability', 'when_can_start'],
        'education_degree': ['degree', 'education', 'highest_degree', 'education_level'],
        'education_school': ['school', 'university', 'college', 'institution', 'alma_mater'],
        'graduation_year': ['graduation', 'grad_year', 'graduation_year', 'year_graduated'],
        'skills': ['skills', 'technical_skills', 'expertise', 'competencies', 'technologies']
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
    
    # Handle dropdowns/select elements
    for select_elem in driver.find_elements(By.TAG_NAME, "select"):
        try:
            select_name = (select_elem.get_attribute("name") or "").lower()
            select_id = (select_elem.get_attribute("id") or "").lower()
            
            # Handle common dropdown fields
            if any(keyword in select_name or keyword in select_id for keyword in ['experience', 'years']):
                if 'years_experience' in profile:
                    select = Select(select_elem)
                    years = profile['years_experience']
                    # Try to find matching option
                    for option in select.options:
                        if years in option.text or str(years) in option.get_attribute("value"):
                            select.select_by_visible_text(option.text)
                            filled_fields += 1
                            break
            
            elif any(keyword in select_name or keyword in select_id for keyword in ['education', 'degree']):
                if 'education_degree' in profile:
                    select = Select(select_elem)
                    degree = profile['education_degree'].lower()
                    for option in select.options:
                        if degree in option.text.lower():
                            select.select_by_visible_text(option.text)
                            filled_fields += 1
                            break
            
            elif any(keyword in select_name or keyword in select_id for keyword in ['country']):
                if 'country' in profile:
                    select = Select(select_elem)
                    country = profile['country']
                    for option in select.options:
                        if country.lower() in option.text.lower():
                            select.select_by_visible_text(option.text)
                            filled_fields += 1
                            break
                            
        except Exception as e:
            bot_state.logger.debug(f"Failed to handle dropdown: {e}")
            continue
    
    # Handle checkboxes and agreements
    for checkbox in driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
        try:
            label_text = ""
            # Try to find associated label
            checkbox_id = checkbox.get_attribute("id")
            if checkbox_id:
                try:
                    label = driver.find_element(By.CSS_SELECTOR, f"label[for='{checkbox_id}']")
                    label_text = label.text.lower()
                except:
                    # Try to find label by looking at parent elements
                    parent = checkbox.find_element(By.XPATH, "..")
                    label_text = parent.text.lower()
            
            # Auto-check agreement checkboxes
            if any(keyword in label_text for keyword in ['agree', 'terms', 'privacy', 'consent', 'authorize']):
                if not checkbox.is_selected():
                    safe_click(driver, checkbox, 'agreement_checkbox')
                    filled_fields += 1
            
            # Handle work authorization questions
            elif any(keyword in label_text for keyword in ['authorized', 'eligible', 'work in']):
                if profile.get('authorized_to_work', True) and not checkbox.is_selected():
                    safe_click(driver, checkbox, 'work_authorization')
                    filled_fields += 1
            
            # Handle sponsorship questions (usually "No" for sponsorship needed)
            elif any(keyword in label_text for keyword in ['sponsor', 'visa']):
                if not profile.get('require_sponsorship', False) and not checkbox.is_selected():
                    safe_click(driver, checkbox, 'sponsorship_checkbox')
                    filled_fields += 1
                    
        except Exception as e:
            bot_state.logger.debug(f"Failed to handle checkbox: {e}")
            continue
    
    # Handle radio buttons
    for radio in driver.find_elements(By.CSS_SELECTOR, "input[type='radio']"):
        try:
            radio_name = radio.get_attribute("name")
            radio_value = radio.get_attribute("value")
            
            # Try to find label
            label_text = ""
            try:
                radio_id = radio.get_attribute("id")
                if radio_id:
                    label = driver.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                    label_text = label.text.lower()
            except:
                pass
            
            # Handle work authorization radio buttons
            if any(keyword in (radio_name or "").lower() for keyword in ['authorized', 'eligible', 'work']):
                if profile.get('authorized_to_work', True) and 'yes' in (radio_value or "").lower():
                    safe_click(driver, radio, 'work_auth_radio')
                    filled_fields += 1
            
            # Handle sponsorship radio buttons
            elif any(keyword in (radio_name or "").lower() for keyword in ['sponsor', 'visa']):
                if not profile.get('require_sponsorship', False) and 'no' in (radio_value or "").lower():
                    safe_click(driver, radio, 'sponsorship_radio')
                    filled_fields += 1
                    
        except Exception as e:
            bot_state.logger.debug(f"Failed to handle radio button: {e}")
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
    """Process a single job application by trying multiple platforms until one succeeds"""
    try:
        apply_urls = get_prioritized_apply_urls(job)
        if not apply_urls:
            bot_state.logger.warning("No valid application URLs found")
            bot_state.applications_skipped += 1
            return False
        
        job_title = job.get('title', 'Unknown')
        company = job.get('company', 'Unknown')
        
        bot_state.logger.info(f"Processing: {job_title} at {company}")
        bot_state.logger.info(f"Found {len(apply_urls)} application URLs to try")
        
        # Try each URL until one succeeds
        for i, url_info in enumerate(apply_urls):
            url = url_info['url']
            platform_name = url_info['platform']
            platform = detect_platform(url)
            
            bot_state.logger.info(f"Attempt {i+1}/{len(apply_urls)}: {platform_name} | {url}")
            
            try:
                # Navigate to job
                driver.get(url)
                human_delay(4, 6)
                
                # Platform-specific handling
                success = False
                if platform == 'linkedin':
                    success = handle_linkedin_application(driver, job, profile)
                else:
                    # Generic handling for other platforms
                    success = handle_generic_application(driver, job, profile, platform_name)
                
                if success:
                    bot_state.applications_submitted += 1
                    bot_state.logger.info(f"✅ Application submitted successfully via {platform_name}")
                    return True
                else:
                    bot_state.logger.warning(f"❌ Application failed on {platform_name}")
                    # Continue to next URL
                    continue
                    
            except Exception as e:
                bot_state.logger.error(f"Error on {platform_name}: {e}")
                # Continue to next URL
                continue
        
        # If we get here, all URLs failed
        bot_state.applications_failed += 1
        bot_state.logger.error(f"❌ All application attempts failed for {job_title}")
        return False
        
    except Exception as e:
        bot_state.logger.error(f"Error processing job: {e}")
        bot_state.applications_failed += 1
        return False

def handle_generic_application(driver, job: Dict[str, Any], profile: Dict[str, Any], platform_name: str = "Generic") -> bool:
    """Handle generic job application flow"""
    try:
        bot_state.logger.info(f"Handling {platform_name} application")
        
        # Look for apply buttons with platform-specific variations
        apply_selectors = [
            "//button[contains(text(), 'Apply')]",
            "//a[contains(text(), 'Apply')]",
            "//button[contains(text(), 'Submit Application')]",
            "//input[@type='submit' and contains(@value, 'Apply')]",
            "//button[contains(@class, 'apply')]",
            "//a[contains(@class, 'apply')]",
            "//button[contains(text(), 'Apply Now')]",
            "//a[contains(text(), 'Apply Now')]"
        ]
        
        apply_clicked = False
        for selector in apply_selectors:
            if find_and_click(driver, selector):
                bot_state.logger.debug(f"Clicked apply button: {selector}")
                apply_clicked = True
                break
        
        if not apply_clicked:
            bot_state.logger.warning(f"No apply button found on {platform_name}")
            # Still try to fill form in case we're already on application page
        
        human_delay(2, 4)
        
        # Handle new window/tab if opened
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            bot_state.logger.debug("Switched to new window")
            human_delay(2, 3)
        
        # Fill form
        form_filled = detect_and_fill_form(driver, profile)
        
        if form_filled:
            bot_state.logger.info(f"Form filled successfully on {platform_name}")
            
            # Try to submit
            submit_selectors = [
                "//button[contains(text(), 'Submit')]",
                "//button[contains(text(), 'Apply')]",
                "//button[contains(text(), 'Send')]",
                "//button[contains(text(), 'Submit Application')]",
                "//input[@type='submit']",
                "//button[@type='submit']"
            ]
            
            for selector in submit_selectors:
                if find_and_click(driver, selector):
                    bot_state.logger.info(f"Application submitted on {platform_name}")
                    human_delay(2, 4)  # Wait for submission to process
                    return True
            
            bot_state.logger.warning(f"Form filled but no submit button found on {platform_name}")
            return False
        else:
            bot_state.logger.warning(f"No form fields found or filled on {platform_name}")
            return False
        
    except Exception as e:
        bot_state.logger.error(f"{platform_name} application error: {e}")
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
    job_data_raw = load_json(args.jobs_file)
    raw_profile = load_json(args.profile_file)
    profile = normalize_profile(raw_profile)
    
    # Handle different job data formats
    if isinstance(job_data_raw, dict):
        if 'jobs' in job_data_raw:
            # Handle format: {"jobs": [...]}
            job_data = job_data_raw['jobs']
            bot_state.logger.info(f"Detected nested jobs format with {len(job_data)} jobs")
        else:
            # Handle format: {"job1": {...}, "job2": {...}}
            job_data = [job_data_raw]
    elif isinstance(job_data_raw, list):
        # Handle format: [{"job1": {...}}, {"job2": {...}}]
        job_data = job_data_raw
    else:
        bot_state.logger.error("Invalid job data format")
        sys.exit(1)
    
    # Validate profile
    required_fields = ['email', 'first_name', 'last_name']
    missing_fields = [field for field in required_fields if field not in profile or not profile[field]]
    if missing_fields:
        bot_state.logger.error(f"Missing required profile fields: {missing_fields}")
        bot_state.logger.info("Available profile fields: " + ", ".join(profile.keys()))
        sys.exit(1)
    
    # Debug: Show normalized profile fields
    bot_state.logger.info(f"Profile loaded successfully with {len(profile)} fields")
    if args.verbose:
        bot_state.logger.debug("Profile fields: " + ", ".join(f"{k}={v}" for k, v in profile.items() if v))
    
    # Show job data statistics
    if job_data:
        total_urls = sum(len(job.get('apply_links', [])) for job in job_data)
        bot_state.logger.info(f"Loaded {len(job_data)} jobs with {total_urls} total application URLs")
    
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