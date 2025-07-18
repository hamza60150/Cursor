#!/usr/bin/env python3
"""
Test script to verify profile normalization
"""

import json
import sys
from linkedin_apply_bot import normalize_profile

def test_profile_normalization():
    """Test the profile normalization function"""
    
    # Sample nested profile structure
    nested_profile = {
        "personal_info": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@email.com",
            "phone": "+1-555-123-4567",
            "address": {
                "street": "123 Main Street",
                "city": "New York",
                "state": "NY",
                "zip_code": "10001",
                "country": "United States"
            },
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "website": "https://johndoe.com"
        },
        "professional_info": {
            "current_title": "Senior Software Engineer",
            "years_of_experience": 5,
            "desired_salary": "120000"
        },
        "files": {
            "resume_path": "./documents/resume.pdf",
            "cover_letter_path": "./documents/cover_letter.pdf"
        },
        "questionnaire_responses": {
            "common_questions": {
                "why_interested": "I am passionate about building scalable software solutions."
            },
            "boolean_responses": {
                "authorized_to_work": True,
                "require_sponsorship": False
            }
        }
    }
    
    print("Testing profile normalization...")
    print("=" * 50)
    
    # Test normalization
    normalized = normalize_profile(nested_profile)
    
    print("Normalized profile fields:")
    for key, value in normalized.items():
        if value:  # Only show non-empty values
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 50)
    
    # Check required fields
    required_fields = ['email', 'first_name', 'last_name']
    missing_fields = [field for field in required_fields if field not in normalized or not normalized[field]]
    
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False
    else:
        print("✅ All required fields present")
        return True

if __name__ == "__main__":
    success = test_profile_normalization()
    sys.exit(0 if success else 1)