#!/usr/bin/env python3
"""
Test script to verify imports work correctly
"""

import sys
import os

def test_basic_imports():
    """Test basic Python imports"""
    try:
        import csv
        import re
        import time
        import random
        from datetime import datetime
        print("✅ Basic imports successful")
        return True
    except ImportError as e:
        print(f"❌ Basic imports failed: {e}")
        return False

def test_selenium_imports():
    """Test Selenium imports"""
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support.select import Select
        from selenium.webdriver.remote.webelement import WebElement
        from selenium.common.exceptions import NoSuchElementException
        print("✅ Selenium imports successful")
        return True
    except ImportError as e:
        print(f"❌ Selenium imports failed: {e}")
        return False

def test_config_imports():
    """Test config imports"""
    try:
        sys.path.insert(0, 'config')
        from secrets import username, password, use_AI, ai_provider
        from personals import first_name, last_name
        from search import search_terms
        from questions import bad_words
        from settings import file_name
        print("✅ Config imports successful")
        return True
    except ImportError as e:
        print(f"❌ Config imports failed: {e}")
        return False

def test_module_imports():
    """Test module imports"""
    try:
        from modules.helpers import print_lg, buffer, calculate_date_posted
        from modules.clickers_and_finders import try_xp, find_by_class
        from modules.validator import validate_config
        print("✅ Module imports successful")
        return True
    except ImportError as e:
        print(f"❌ Module imports failed: {e}")
        return False

def test_ai_imports():
    """Test AI imports"""
    try:
        from modules.ai.openaiConnections import ai_create_openai_client
        from modules.ai.deepseekConnections import deepseek_create_client
        from modules.ai.geminiConnections import gemini_create_client
        print("✅ AI imports successful")
        return True
    except ImportError as e:
        print(f"❌ AI imports failed: {e}")
        return False

def test_chrome_imports():
    """Test Chrome module imports"""
    try:
        from modules.open_chrome import setup_driver, get_driver, get_wait, get_actions
        print("✅ Chrome module imports successful")
        return True
    except ImportError as e:
        print(f"❌ Chrome module imports failed: {e}")
        return False

def test_job_fetcher_imports():
    """Test job fetcher imports"""
    try:
        from job_fetcher import JobFetcher, main_fetch
        print("✅ Job fetcher imports successful")
        return True
    except ImportError as e:
        print(f"❌ Job fetcher imports failed: {e}")
        return False

def main():
    """Run all import tests"""
    print("=" * 60)
    print("Testing Imports")
    print("=" * 60)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Selenium Imports", test_selenium_imports),
        ("Config Imports", test_config_imports),
        ("Module Imports", test_module_imports),
        ("AI Imports", test_ai_imports),
        ("Chrome Imports", test_chrome_imports),
        ("Job Fetcher Imports", test_job_fetcher_imports),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All imports working correctly!")
        print("\nYou can now run:")
        print("python3 job_fetcher.py")
    else:
        print("❌ Some imports failed. Please check the errors above.")
        print("\nMake sure to install dependencies:")
        print("pip install -r requirements.txt")

if __name__ == "__main__":
    main()