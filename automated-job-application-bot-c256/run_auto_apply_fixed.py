#!/usr/bin/env python3
"""
Runner for the FIXED Auto Apply Agent
"""

import os
import sys
import json
from auto_apply_agent_fixed import AutoApplyAgent

def main():
    # Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    JOBS_FILE = 'sample_jobs.json'
    RESUME_FILE = 'sample_resume.json' 
    HEADLESS = False  # Set to True to hide browser
    
    if not OPENAI_API_KEY:
        print("❌ Error: Please set OPENAI_API_KEY environment variable")
        print("   export OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    if not os.path.exists(JOBS_FILE):
        print(f"❌ Error: Jobs file not found: {JOBS_FILE}")
        sys.exit(1)
        
    if not os.path.exists(RESUME_FILE):
        print(f"❌ Error: Resume file not found: {RESUME_FILE}")
        sys.exit(1)
    
    print("🤖 Starting FIXED Auto Apply Agent...")
    print(f"   Jobs file: {JOBS_FILE}")
    print(f"   Resume file: {RESUME_FILE}")
    print(f"   Headless mode: {HEADLESS}")
    
    # Create and run agent
    agent = AutoApplyAgent(
        openai_api_key=OPENAI_API_KEY,
        headless=HEADLESS
    )
    
    try:
        results = agent.apply_to_jobs(JOBS_FILE, RESUME_FILE)
        
        # Print results
        print("\n📊 RESULTS:")
        print(f"Total Jobs: {results.get('total_jobs', 0)}")
        print(f"Successful: {results.get('successful_applications', 0)}")
        print(f"Failed: {results.get('failed_applications', 0)}")
        
        # Save results
        with open(f"results_fixed.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Results saved to: results_fixed.json")
        
    except KeyboardInterrupt:
        print("\n⚠️ Application interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n🏁 Auto Apply Agent finished")

if __name__ == "__main__":
    main()
