#!/usr/bin/env python3
"""
Configuration validation module
"""

import os
from config.personals import *
from config.search import *
from config.settings import *

def validate_config():
    """Validate all configuration settings"""
    print_lg("Validating configuration...")
    
    # Validate personal information
    if not first_name or not last_name:
        raise ValueError("First name and last name are required in config/personals.py")
    
    if not phone_number:
        print_lg("Warning: Phone number not set in config/personals.py")
    
    if not email:
        print_lg("Warning: Email not set in config/personals.py")
    
    # Validate search terms
    if not search_terms or len(search_terms) == 0:
        raise ValueError("At least one search term is required in config/search.py")
    
    # Validate resume path
    if not os.path.exists(default_resume_path):
        print_lg(f"Warning: Resume file not found at {default_resume_path}")
        print_lg("The bot will use previously uploaded resume from LinkedIn")
    
    # Validate search location
    if not search_location:
        print_lg("Warning: Search location not set in config/search.py")
    
    print_lg("Configuration validation completed successfully!")
    return True