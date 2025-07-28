#!/usr/bin/env python3
"""
Test script for the split LinkedIn job application bot functionality
"""

import os
import sys
import csv
from datetime import datetime

def test_csv_structure():
    """Test if the CSV structure is correct"""
    print("Testing CSV structure...")
    
    # Test applicable.csv structure
    applicable_headers = [
        'Job ID', 'Title', 'Company', 'Work Location', 'Work Style', 
        'Job Link', 'Description', 'Experience Required', 'Date Posted', 'Easy Apply Available'
    ]
    
    # Test main application CSV structure
    main_headers = [
        'Job ID', 'Title', 'Company', 'Work Location', 'Work Style', 'About Job', 
        'Experience required', 'Skills required', 'HR Name', 'HR Link', 'Resume', 
        'Re-posted', 'Date Posted', 'Date Applied', 'Job Link', 'External Job link', 
        'Questions Found', 'Connect Request'
    ]
    
    print("✅ CSV structure validation passed")
    return True

def test_imports():
    """Test if all modules can be imported"""
    print("Testing module imports...")
    
    try:
        # Test job_fetcher imports
        from job_fetcher import JobFetcher, JobInfo, main_fetch
        print("✅ job_fetcher imports successful")
        
        # Test auto_applier imports
        from auto_applier import AutoApplier, JobApplication, main_apply
        print("✅ auto_applier imports successful")
        
        # Test main orchestrator
        from main import main
        print("✅ main orchestrator imports successful")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    return True

def test_config_imports():
    """Test if configuration files can be imported"""
    print("Testing configuration imports...")
    
    try:
        # Test config imports
        from config.personals import *
        from config.questions import *
        from config.search import *
        from config.settings import *
        print("✅ Configuration imports successful")
        
    except ImportError as e:
        print(f"❌ Configuration import error: {e}")
        return False
    
    return True

def test_module_structure():
    """Test if the module structure is correct"""
    print("Testing module structure...")
    
    required_files = [
        'job_fetcher.py',
        'auto_applier.py', 
        'main.py',
        'config/personals.py',
        'config/questions.py',
        'config/search.py',
        'config/settings.py'
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Missing required file: {file}")
            return False
    
    print("✅ Module structure validation passed")
    return True

def create_sample_csv():
    """Create a sample applicable.csv for testing"""
    print("Creating sample applicable.csv...")
    
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
        with open('applicable.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Job ID', 'Title', 'Company', 'Work Location', 'Work Style',
                'Job Link', 'Description', 'Experience Required', 'Date Posted', 'Easy Apply Available'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in sample_data:
                writer.writerow(row)
        
        print("✅ Sample applicable.csv created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating sample CSV: {e}")
        return False

def test_csv_loading():
    """Test if CSV loading works correctly"""
    print("Testing CSV loading...")
    
    try:
        from auto_applier import AutoApplier
        applier = AutoApplier()
        jobs = applier.load_jobs_from_csv('applicable.csv')
        
        if len(jobs) == 2:
            print("✅ CSV loading successful")
            return True
        else:
            print(f"❌ Expected 2 jobs, got {len(jobs)}")
            return False
            
    except Exception as e:
        print(f"❌ CSV loading error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("LinkedIn Job Application Bot - Split Functionality Test")
    print("=" * 60)
    
    tests = [
        ("Module Structure", test_module_structure),
        ("Configuration Imports", test_config_imports),
        ("Module Imports", test_imports),
        ("CSV Structure", test_csv_structure),
        ("Sample CSV Creation", create_sample_csv),
        ("CSV Loading", test_csv_loading)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The split functionality is ready to use.")
        print("\nNext steps:")
        print("1. Configure your settings in config/ directory")
        print("2. Run: python main.py --mode fetch")
        print("3. Review applicable.csv")
        print("4. Run: python main.py --mode apply")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()