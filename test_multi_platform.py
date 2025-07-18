#!/usr/bin/env python3
"""
Test script to demonstrate multi-platform job application functionality
"""

import json
from linkedin_apply_bot import get_prioritized_apply_urls, detect_platform

def test_multi_platform_urls():
    """Test the multi-platform URL prioritization"""
    
    # Sample job data matching your format
    sample_job = {
        "title": "Software Engineer",
        "company": "PNC",
        "location": "Strongsville, OH",
        "apply_links": [
            {
                "platform": "PNC Careers",
                "url": "https://careers.pnc.com/global/en/job/R194840/Software-Engineer",
                "title": "Apply on PNC Careers"
            },
            {
                "platform": "LinkedIn",
                "url": "https://www.linkedin.com/jobs/view/software-engineer-at-pnc-4268620760",
                "title": "Apply on LinkedIn"
            },
            {
                "platform": "Dice",
                "url": "https://www.dice.com/job-detail/2f4433d0-9f34-41e4-91e3-f9a262edf5b8",
                "title": "Apply on Dice"
            },
            {
                "platform": "Indeed",
                "url": "https://www.indeed.com/viewjob?jk=e699a8dba9ec37e5",
                "title": "Apply on Indeed"
            },
            {
                "platform": "Glassdoor",
                "url": "https://www.glassdoor.com/job-listing/software-engineer-pnc-financial-services-group-JV_IC1145819_KO0,17_KE18,46.htm",
                "title": "Apply on Glassdoor"
            }
        ]
    }
    
    print("🧪 Testing Multi-Platform URL Prioritization")
    print("=" * 60)
    
    # Get prioritized URLs
    urls = get_prioritized_apply_urls(sample_job)
    
    print(f"Job: {sample_job['title']} at {sample_job['company']}")
    print(f"Found {len(urls)} application URLs")
    print("\nPrioritized Application Order:")
    
    for i, url_info in enumerate(urls, 1):
        platform_detected = detect_platform(url_info['url'])
        print(f"{i}. {url_info['platform']} (detected: {platform_detected})")
        print(f"   URL: {url_info['url']}")
        print(f"   Title: {url_info['title']}")
        print()
    
    # Test with your actual jobs.json format
    print("🔍 Testing with actual jobs.json format...")
    print("=" * 60)
    
    # Load your jobs.json if it exists
    try:
        with open('jobs.json', 'r') as f:
            jobs_data = json.load(f)
        
        if 'jobs' in jobs_data:
            jobs = jobs_data['jobs'][:3]  # Test first 3 jobs
            
            for job in jobs:
                print(f"\nJob: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
                urls = get_prioritized_apply_urls(job)
                print(f"Available platforms: {len(urls)}")
                
                for i, url_info in enumerate(urls[:3], 1):  # Show first 3 URLs
                    platform = detect_platform(url_info['url'])
                    print(f"  {i}. {url_info['platform']} ({platform})")
                
                if len(urls) > 3:
                    print(f"  ... and {len(urls) - 3} more platforms")
                print()
        
    except FileNotFoundError:
        print("jobs.json not found - using sample data only")
    except Exception as e:
        print(f"Error loading jobs.json: {e}")
    
    print("✅ Multi-platform test completed!")
    print("\nHow the bot works:")
    print("1. Tries LinkedIn first (highest priority)")
    print("2. Falls back to Indeed if LinkedIn fails")
    print("3. Continues through all platforms until one succeeds")
    print("4. Only moves to next job after successful application")

if __name__ == "__main__":
    test_multi_platform_urls()