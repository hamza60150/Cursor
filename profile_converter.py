#!/usr/bin/env python3
"""
Profile Converter and Validator for LinkedIn Job Application Bot
"""

import json
import sys
import argparse
from linkedin_apply_bot import normalize_profile

def load_profile(file_path):
    """Load profile from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Profile file not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in profile file: {e}")
        return None

def validate_profile(profile):
    """Validate profile and show available fields"""
    print("🔍 Validating profile...")
    
    normalized = normalize_profile(profile)
    
    required_fields = ['email', 'first_name', 'last_name']
    missing_fields = [field for field in required_fields if field not in normalized or not normalized[field]]
    
    print(f"\n📊 Profile Summary:")
    print(f"   Total fields: {len(normalized)}")
    print(f"   Non-empty fields: {len([v for v in normalized.values() if v])}")
    
    if missing_fields:
        print(f"\n❌ Missing required fields: {', '.join(missing_fields)}")
        return False
    else:
        print(f"\n✅ All required fields present")
    
    print(f"\n📋 Available fields:")
    for key, value in normalized.items():
        if value:
            display_value = str(value)
            if len(display_value) > 50:
                display_value = display_value[:47] + "..."
            print(f"   ✓ {key}: {display_value}")
        else:
            print(f"   ○ {key}: (empty)")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Profile Validator')
    parser.add_argument('profile_file', help='Path to profile JSON file')
    
    args = parser.parse_args()
    
    print("LinkedIn Job Application Bot - Profile Validator")
    print("=" * 50)
    
    profile = load_profile(args.profile_file)
    if not profile:
        return 1
    
    print(f"📁 Loaded profile from: {args.profile_file}")
    
    if validate_profile(profile):
        print("\n🎉 Profile is valid and ready to use!")
        return 0
    else:
        print("\n❌ Profile validation failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())