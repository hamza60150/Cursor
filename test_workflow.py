#!/usr/bin/env python3
"""
Test script for the complete LinkedIn job application workflow
"""

import os
import sys
import csv
from datetime import datetime

def test_config_files():
    """Test if all config files exist and are properly structured"""
    print("Testing configuration files...")
    
    config_files = [
        'config/secrets.py',
        'config/personals.py',
        'config/search.py',
        'config/questions.py',
        'config/settings.py'
    ]
    
    for file in config_files:
        if not os.path.exists(file):
            print(f"❌ Missing config file: {file}")
            return False
        else:
            print(f"✅ Found config file: {file}")
    
    return True

def test_module_files():
    """Test if all module files exist"""
    print("\nTesting module files...")
    
    module_files = [
        'modules/__init__.py',
        'modules/open_chrome.py',
        'modules/helpers.py',
        'modules/clickers_and_finders.py',
        'modules/validator.py',
        'modules/ai/__init__.py',
        'modules/ai/openaiConnections.py',
        'modules/ai/deepseekConnections.py',
        'modules/ai/geminiConnections.py'
    ]
    
    for file in module_files:
        if not os.path.exists(file):
            print(f"❌ Missing module file: {file}")
            return False
        else:
            print(f"✅ Found module file: {file}")
    
    return True

def test_main_files():
    """Test if main application files exist"""
    print("\nTesting main application files...")
    
    main_files = [
        'job_fetcher.py',
        'auto_applier.py',
        'main.py'
    ]
    
    for file in main_files:
        if not os.path.exists(file):
            print(f"❌ Missing main file: {file}")
            return False
        else:
            print(f"✅ Found main file: {file}")
    
    return True

def test_imports():
    """Test if all imports work correctly"""
    print("\nTesting imports...")
    
    try:
        # Test config imports
        import sys
        sys.path.insert(0, 'config')
        from secrets import username, password, use_AI, ai_provider
        print("✅ Config imports successful")
        
        # Test module imports
        try:
            from modules.open_chrome import setup_driver
            from modules.helpers import print_lg, buffer
            from modules.clickers_and_finders import try_xp, find_by_class
            from modules.validator import validate_config
            print("✅ Module imports successful")
        except ImportError as e:
            print(f"⚠️  Module imports failed (missing dependencies): {e}")
            print("   Install dependencies with: pip install -r requirements.txt")
            return False
        
        # Test AI imports
        try:
            from modules.ai.openaiConnections import ai_create_openai_client
            from modules.ai.deepseekConnections import deepseek_create_client
            from modules.ai.geminiConnections import gemini_create_client
            print("✅ AI module imports successful")
        except ImportError as e:
            print(f"⚠️  AI module imports failed (missing dependencies): {e}")
            print("   Install dependencies with: pip install -r requirements.txt")
            return False
        
        # Test main application imports
        try:
            from job_fetcher import JobFetcher, main_fetch
            from auto_applier import AutoApplier, main_apply
            print("✅ Main application imports successful")
        except ImportError as e:
            print(f"⚠️  Main application imports failed: {e}")
            return False
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    return True

def test_configuration():
    """Test if configuration is properly set up"""
    print("\nTesting configuration...")
    
    try:
        import sys
        sys.path.insert(0, 'config')
        from secrets import username, password
        from personals import first_name, last_name
        from search import search_terms
        
        if username == "your_linkedin_email@example.com":
            print("⚠️  Warning: Default username in config/secrets.py")
        else:
            print("✅ Username configured")
            
        if password == "your_linkedin_password":
            print("⚠️  Warning: Default password in config/secrets.py")
        else:
            print("✅ Password configured")
            
        if first_name == "John" and last_name == "Doe":
            print("⚠️  Warning: Default personal info in config/personals.py")
        else:
            print("✅ Personal info configured")
            
        if len(search_terms) > 0:
            print("✅ Search terms configured")
        else:
            print("❌ No search terms configured")
            return False
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    return True

def create_sample_csv():
    """Create a sample applicablejobs.csv for testing"""
    print("\nCreating sample applicablejobs.csv...")
    
    sample_data = [
        {
            'Job ID': '123456',
            'Title': 'Software Engineer',
            'Company': 'Google',
            'Work Location': 'Mountain View, CA',
            'Work Style': 'Hybrid',
            'Job Link': 'https://linkedin.com/jobs/view/123456',
            'Description': 'We are looking for a software engineer...',
            'Experience Required': '3',
            'Date Posted': '2 days ago',
            'Easy Apply Available': 'true'
        },
        {
            'Job ID': '789012',
            'Title': 'Frontend Developer',
            'Company': 'Microsoft',
            'Work Location': 'Seattle, WA',
            'Work Style': 'Remote',
            'Job Link': 'https://linkedin.com/jobs/view/789012',
            'Description': 'Join our team as a frontend developer...',
            'Experience Required': '2',
            'Date Posted': '1 day ago',
            'Easy Apply Available': 'true'
        }
    ]
    
    try:
        with open('applicablejobs.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Job ID', 'Title', 'Company', 'Work Location', 'Work Style',
                'Job Link', 'Description', 'Experience Required', 'Date Posted', 'Easy Apply Available'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in sample_data:
                writer.writerow(row)
        
        print("✅ Sample applicablejobs.csv created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating sample CSV: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 80)
    print("LinkedIn Job Application Bot - Complete Workflow Test")
    print("=" * 80)
    
    tests = [
        ("Configuration Files", test_config_files),
        ("Module Files", test_module_files),
        ("Main Files", test_main_files),
        ("Import Tests", test_imports),
        ("Configuration Validation", test_configuration),
        ("Sample CSV Creation", create_sample_csv)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 80)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The workflow is ready to use.")
        print("\nNext steps:")
        print("1. Update your credentials in config/secrets.py")
        print("2. Update your personal info in config/personals.py")
        print("3. Update your search terms in config/search.py")
        print("4. Run: python job_fetcher.py")
        print("5. Review applicablejobs.csv")
        print("6. Run: python auto_applier.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()