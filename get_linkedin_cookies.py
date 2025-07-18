#!/usr/bin/env python3
"""
LinkedIn Cookie Extractor
Helps users extract LinkedIn cookies for the bot
"""

import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def extract_linkedin_cookies(output_file: str = "linkedin_cookies.json"):
    """Extract LinkedIn cookies from browser session"""
    print("🔧 Setting up browser...")
    
    # Setup Chrome options
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("🌐 Opening LinkedIn...")
        driver.get("https://www.linkedin.com")
        
        print("\n" + "="*60)
        print("📋 INSTRUCTIONS:")
        print("1. Please LOG IN to your LinkedIn account in the browser")
        print("2. Make sure you're fully logged in (see your profile)")
        print("3. Once logged in, press ENTER in this terminal")
        print("="*60)
        
        input("Press ENTER after you've logged in to LinkedIn...")
        
        print("🍪 Extracting cookies...")
        cookies = driver.get_cookies()
        
        if not cookies:
            print("❌ No cookies found!")
            return False
        
        # Filter LinkedIn cookies
        linkedin_cookies = []
        for cookie in cookies:
            if 'linkedin' in cookie.get('domain', '').lower():
                linkedin_cookies.append(cookie)
        
        if not linkedin_cookies:
            print("❌ No LinkedIn cookies found!")
            return False
        
        # Save cookies
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(linkedin_cookies, f, indent=2)
        
        print(f"✅ Successfully extracted {len(linkedin_cookies)} LinkedIn cookies")
        print(f"📁 Saved to: {output_file}")
        
        # Show cookie summary
        print("\n📊 Cookie Summary:")
        for cookie in linkedin_cookies:
            print(f"  - {cookie['name']}: {cookie['value'][:20]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'driver' in locals():
            driver.quit()

def validate_linkedin_cookies(cookie_file: str):
    """Validate LinkedIn cookies"""
    try:
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        linkedin_cookies = [c for c in cookies if 'linkedin' in c.get('domain', '').lower()]
        
        if not linkedin_cookies:
            print("❌ No LinkedIn cookies found in file")
            return False
        
        print(f"✅ Found {len(linkedin_cookies)} LinkedIn cookies")
        
        # Check for important cookies
        important_cookies = ['li_at', 'JSESSIONID', 'li_rm']
        found_important = []
        
        for cookie in linkedin_cookies:
            if cookie['name'] in important_cookies:
                found_important.append(cookie['name'])
        
        if found_important:
            print(f"🔑 Important cookies found: {', '.join(found_important)}")
        else:
            print("⚠️  No important LinkedIn session cookies found")
            print("   You may need to log in again")
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating cookies: {e}")
        return False

def main():
    print("🤖 LinkedIn Cookie Extractor")
    print("="*40)
    
    if len(os.sys.argv) > 1:
        if os.sys.argv[1] == '--validate':
            if len(os.sys.argv) < 3:
                print("Usage: python get_linkedin_cookies.py --validate <cookie_file>")
                return
            validate_linkedin_cookies(os.sys.argv[2])
            return
    
    print("This tool will help you extract LinkedIn cookies for the bot.")
    print("Make sure you have Chrome browser installed.\n")
    
    output_file = input("Enter output filename (default: linkedin_cookies.json): ").strip()
    if not output_file:
        output_file = "linkedin_cookies.json"
    
    if extract_linkedin_cookies(output_file):
        print(f"\n🎉 Success! Use this file with the bot:")
        print(f"python linkedin_apply_bot.py --cookies-file {output_file} ...")
    else:
        print("\n❌ Failed to extract cookies. Please try again.")

if __name__ == "__main__":
    main()