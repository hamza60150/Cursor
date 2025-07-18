#!/usr/bin/env python3
"""
Cookie Converter Utility
Converts browser extension cookies to Selenium-compatible format
"""

import json
import sys
from typing import Dict, Any, List

def convert_browser_cookie_to_selenium(cookie: Dict[str, Any]) -> Dict[str, Any]:
    """Convert browser extension cookie format to Selenium format"""
    selenium_cookie = {
        'name': cookie.get('name', ''),
        'value': cookie.get('value', ''),
        'domain': cookie.get('domain', ''),
        'path': cookie.get('path', '/'),
        'secure': cookie.get('secure', False),
        'httpOnly': cookie.get('httpOnly', False)
    }
    
    # Handle expiration date
    if 'expirationDate' in cookie and cookie['expirationDate']:
        # Convert from Unix timestamp to integer
        expiry = cookie['expirationDate']
        if isinstance(expiry, float):
            selenium_cookie['expiry'] = int(expiry)
        elif isinstance(expiry, int):
            selenium_cookie['expiry'] = expiry
    
    # Handle sameSite attribute
    if 'sameSite' in cookie and cookie['sameSite']:
        same_site = cookie['sameSite'].lower()
        if same_site in ['strict', 'lax', 'none']:
            selenium_cookie['sameSite'] = same_site.capitalize()
    
    return selenium_cookie

def convert_cookies_file(input_file: str, output_file: str = None):
    """Convert cookies from browser extension format to Selenium format"""
    if not output_file:
        output_file = input_file.replace('.json', '_converted.json')
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        converted_cookies = []
        skipped_count = 0
        
        for cookie in cookies:
            try:
                selenium_cookie = convert_browser_cookie_to_selenium(cookie)
                
                # Skip empty cookies
                if not selenium_cookie['name'] or not selenium_cookie['value']:
                    skipped_count += 1
                    continue
                
                converted_cookies.append(selenium_cookie)
            except Exception as e:
                print(f"Warning: Failed to convert cookie {cookie.get('name', 'unknown')}: {e}")
                skipped_count += 1
        
        # Save converted cookies
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(converted_cookies, f, indent=2)
        
        print(f"✅ Successfully converted {len(converted_cookies)} cookies")
        print(f"⚠️  Skipped {skipped_count} invalid cookies")
        print(f"📁 Saved to: {output_file}")
        
    except FileNotFoundError:
        print(f"❌ Error: File '{input_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{input_file}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def validate_cookies(cookies_file: str):
    """Validate cookies file format"""
    try:
        with open(cookies_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        if not isinstance(cookies, list):
            print("❌ Error: Cookies file should contain a list of cookies")
            return False
        
        valid_count = 0
        for i, cookie in enumerate(cookies):
            if not isinstance(cookie, dict):
                print(f"⚠️  Warning: Cookie {i} is not a dictionary")
                continue
            
            required_fields = ['name', 'value', 'domain']
            missing_fields = [field for field in required_fields if not cookie.get(field)]
            
            if missing_fields:
                print(f"⚠️  Warning: Cookie {i} missing required fields: {missing_fields}")
                continue
            
            valid_count += 1
        
        print(f"✅ Found {valid_count} valid cookies out of {len(cookies)} total")
        return valid_count > 0
        
    except Exception as e:
        print(f"❌ Error validating cookies: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python cookie_converter.py <input_file> [output_file]")
        print("  python cookie_converter.py --validate <cookies_file>")
        print("")
        print("Examples:")
        print("  python cookie_converter.py cookies.json")
        print("  python cookie_converter.py cookies.json cookies_selenium.json")
        print("  python cookie_converter.py --validate cookies.json")
        sys.exit(1)
    
    if sys.argv[1] == '--validate':
        if len(sys.argv) < 3:
            print("❌ Error: Please provide cookies file to validate")
            sys.exit(1)
        validate_cookies(sys.argv[2])
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        convert_cookies_file(input_file, output_file)

if __name__ == "__main__":
    main()