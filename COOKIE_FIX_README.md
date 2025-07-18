# Cookie Loading Fix - LinkedIn Apply Bot

## Problem
The bot was failing to load cookies due to **two main issues**:

1. **Format Issue**: Your `cookies.json` file is in **browser extension format** (from tools like EditThisCookie, Cookie Editor, etc.), but Selenium expects a different format.

2. **Domain Mismatch**: The bot was trying to load Google cookies (`.google.com`) on LinkedIn (`linkedin.com`), which Selenium blocks for security reasons.

## What Was Fixed

### 1. Enhanced Cookie Loading Function
- **File**: `utils.py`
- **Added**: `convert_browser_cookie_to_selenium()` function
- **Enhanced**: `load_cookies()` function with smart domain handling
- **Added**: `load_cookies_for_domain()` function for domain-specific loading
- **Result**: Automatically converts browser extension cookies and handles multiple domains

### 2. Improved Error Handling
- **File**: `linkedin_apply_bot.py`
- **Changed**: Updated main bot to use the improved cookie loading
- **Added**: Better error messages and fallback handling
- **Result**: Bot continues running even if some cookies fail to load

### 3. Cookie Utilities
- **File**: `cookie_converter.py` (NEW) - Standalone utility to convert cookie formats
- **File**: `get_linkedin_cookies.py` (NEW) - Extract LinkedIn cookies directly
- **Features**: Validation, conversion, domain-specific extraction, and detailed reporting

## How to Use

### Option 1: Automatic Conversion (Recommended)
The bot now automatically converts your cookies! Just run:
```bash
python linkedin_apply_bot.py --jobs-file "jobs.json" --profile-file "profile.json" --cookies-file "cookies.json"
```

### Option 2: Manual Conversion
If you want to convert your cookies manually:
```bash
python3 cookie_converter.py cookies.json cookies_converted.json
```

### Option 3: Get LinkedIn Cookies Directly
To extract LinkedIn cookies from your browser:
```bash
python3 get_linkedin_cookies.py
```

### Option 4: Validate Your Cookies
To check if your cookies are valid:
```bash
python3 cookie_converter.py --validate cookies.json
python3 get_linkedin_cookies.py --validate linkedin_cookies.json
```

## Cookie Format Differences

### Browser Extension Format (Your Current Format)
```json
{
    "domain": ".google.com",
    "expirationDate": 1786804147.821597,
    "hostOnly": false,
    "httpOnly": false,
    "name": "__Secure-1PAPISID",
    "path": "/",
    "sameSite": "unspecified",
    "secure": true,
    "session": false,
    "storeId": "0",
    "value": "3NJUuQICwF42AdRp/ASy19C_mOYHuk1zyO",
    "id": 1
}
```

### Selenium Format (What the Bot Needs)
```json
{
    "name": "__Secure-1PAPISID",
    "value": "3NJUuQICwF42AdRp/ASy19C_mOYHuk1zyO",
    "domain": ".google.com",
    "path": "/",
    "secure": true,
    "httpOnly": false,
    "expiry": 1786804147
}
```

## Key Changes Made

1. **Removed Invalid Fields**: `id`, `storeId`, `hostOnly`, `session`
2. **Converted Expiration**: `expirationDate` (float) → `expiry` (int)
3. **Fixed SameSite**: `"unspecified"` → `"None"` (or removed if invalid)
4. **Cleaned Structure**: Only kept Selenium-compatible fields

## Expected Output
After the fix, you should see:
```
INFO: Loading saved cookies...
INFO: Found cookies for domains: ['google.com', 'linkedin.com']
INFO: Loaded 15 cookies for google.com (skipped 2)
INFO: Loaded 8 cookies for linkedin.com (skipped 0)
INFO: Successfully loaded cookies from 2 domains
INFO: Cookies loaded successfully, navigated to LinkedIn
```

Instead of:
```
WARNING: Failed to add cookie: invalid cookie domain: Cookie 'domain' mismatch
WARNING: Failed to add cookie: invalid cookie domain: Cookie 'domain' mismatch
...
```

## Troubleshooting

### If cookies still fail to load:
1. **Check cookie domains**: Make sure you have LinkedIn cookies (`.linkedin.com`)
2. **Verify expiration**: Expired cookies are automatically skipped
3. **Check file format**: Ensure your JSON is valid

### If you need fresh cookies:
1. **Login to LinkedIn** in your browser
2. **Export cookies** using a browser extension
3. **Convert them** using the cookie converter
4. **Use the converted file** with the bot

## Files Modified
- ✅ `utils.py` - Enhanced cookie loading with domain handling
- ✅ `linkedin_apply_bot.py` - Updated to use new cookie loader
- ✅ `cookie_converter.py` - New utility for cookie conversion
- ✅ `get_linkedin_cookies.py` - New utility for LinkedIn cookie extraction

## Quick Fix for Your Current Issue

Since your current cookies are mostly Google cookies, you have two options:

### Option A: Get LinkedIn Cookies (Recommended)
```bash
python3 get_linkedin_cookies.py
```
Then use the generated `linkedin_cookies.json` file.

### Option B: Use Current Cookies (Will work but limited)
Your current cookies will now load without errors, but you'll get a warning about missing LinkedIn cookies.

The bot should now work without domain mismatch errors! 🎉