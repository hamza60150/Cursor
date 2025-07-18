"""
Configuration file for LinkedIn Job Application Bot
"""

import os
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class BotConfig:
    """Main configuration class for the bot"""
    
    # Timing settings
    MIN_DELAY: float = 1.0
    MAX_DELAY: float = 3.0
    FORM_FILL_DELAY: float = 0.1
    PAGE_LOAD_TIMEOUT: int = 30
    ELEMENT_TIMEOUT: int = 10
    
    # Application settings
    MAX_APPLICATIONS_PER_RUN: int = 10
    MAX_RETRIES: int = 3
    ENABLE_SCREENSHOTS: bool = True
    SCREENSHOT_DIR: str = "screenshots"
    
    # Browser settings
    HEADLESS_MODE: bool = False
    WINDOW_SIZE: str = "1920,1080"
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    # Platform priorities (higher number = higher priority)
    PLATFORM_PRIORITIES: Dict[str, int] = {
        'LinkedIn': 10,
        'Indeed': 8,
        'Glassdoor': 7,
        'Built In': 6,
        'SimplyHired': 5,
        'Workable': 4,
        'Lever': 3,
        'Greenhouse': 2,
        'Generic': 1
    }
    
    # LinkedIn specific selectors
    LINKEDIN_APPLY_SELECTORS: List[str] = [
        "//button[contains(@class, 'jobs-apply-button')]",
        "//button[contains(text(), 'Apply')]",
        "//a[contains(text(), 'Apply')]",
        "//button[@id='jobs-apply-button-id']",
        "//button[contains(@aria-label, 'Apply')]",
        "//button[contains(@class, 'artdeco-button--primary')]"
    ]
    
    # Form field mappings
    FIELD_MAPPINGS: Dict[str, List[str]] = {
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
        'cover_letter': ['cover_letter', 'coverletter', 'message', 'additional_info', 'additionalinfo', 'motivation']
    }
    
    # Skip keywords (jobs containing these will be skipped)
    SKIP_KEYWORDS: List[str] = [
        'senior', 'lead', 'principal', 'architect', 'director', 'manager',
        'unpaid', 'volunteer', 'internship', 'contract', 'temporary'
    ]
    
    # Required keywords (jobs must contain at least one)
    REQUIRED_KEYWORDS: List[str] = [
        'engineer', 'developer', 'programmer', 'software', 'python', 'javascript',
        'react', 'node', 'full-stack', 'backend', 'frontend'
    ]
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "linkedin_bot.log"
    
    # Chrome options
    CHROME_OPTIONS: List[str] = [
        "--start-maximized",
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-images",
        "--disable-notifications",
        "--disable-popup-blocking"
    ]

# Environment-based configuration
def load_config_from_env() -> BotConfig:
    """Load configuration from environment variables"""
    config = BotConfig()
    
    # Override with environment variables if present
    config.MIN_DELAY = float(os.getenv('BOT_MIN_DELAY', config.MIN_DELAY))
    config.MAX_DELAY = float(os.getenv('BOT_MAX_DELAY', config.MAX_DELAY))
    config.MAX_APPLICATIONS_PER_RUN = int(os.getenv('BOT_MAX_APPLICATIONS', config.MAX_APPLICATIONS_PER_RUN))
    config.HEADLESS_MODE = os.getenv('BOT_HEADLESS', 'false').lower() == 'true'
    config.LOG_LEVEL = os.getenv('BOT_LOG_LEVEL', config.LOG_LEVEL)
    
    return config

# Default configuration instance
DEFAULT_CONFIG = load_config_from_env()