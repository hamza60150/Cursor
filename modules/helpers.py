#!/usr/bin/env python3
"""
Helper functions module
"""

import time
import random
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def print_lg(message, *args):
    """Print log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    for arg in args:
        print(f"[{timestamp}] {arg}")

def buffer(delay: float):
    """Add a buffer delay"""
    time.sleep(delay)

def calculate_date_posted(time_posted_text: str) -> str:
    """Calculate the actual date from 'X days ago' text"""
    try:
        if "ago" in time_posted_text:
            # Extract number and unit
            parts = time_posted_text.split()
            number = int(parts[0])
            unit = parts[1].lower()
            
            now = datetime.now()
            
            if "day" in unit:
                date = now - timedelta(days=number)
            elif "hour" in unit:
                date = now - timedelta(hours=number)
            elif "minute" in unit:
                date = now - timedelta(minutes=number)
            elif "week" in unit:
                date = now - timedelta(weeks=number)
            elif "month" in unit:
                date = now - timedelta(days=number*30)
            else:
                return time_posted_text
            
            return date.strftime("%Y-%m-%d")
        else:
            return time_posted_text
    except:
        return time_posted_text

def manual_login_retry(check_func, max_retries: int = 3):
    """Manual login retry function"""
    for i in range(max_retries):
        print_lg(f"Manual login attempt {i+1}/{max_retries}")
        if check_func():
            print_lg("Manual login successful!")
            return True
        time.sleep(5)
    return False

def critical_error_log(context: str, error: Exception):
    """Log critical errors"""
    print_lg(f"Critical error in {context}: {error}")
    print_lg(f"Error type: {type(error).__name__}")
    print_lg(f"Error details: {str(error)}")