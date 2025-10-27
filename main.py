#!/usr/bin/env python3
"""
LinkedIn Job Application Bot - Main Orchestrator
Runs both job fetching and auto-applying functionality
"""

import argparse
import sys
import os
from typing import Optional

def main():
    """Main function to orchestrate job fetching and auto-applying"""
    parser = argparse.ArgumentParser(description='LinkedIn Job Application Bot')
    parser.add_argument('--mode', choices=['fetch', 'apply', 'both'], default='both',
                       help='Mode to run: fetch (job fetching only), apply (auto-applying only), or both (default)')
    parser.add_argument('--max-jobs', type=int, default=50,
                       help='Maximum number of jobs to fetch per search term (default: 50)')
    parser.add_argument('--max-applications', type=int, default=10,
                       help='Maximum number of applications to submit (default: 10)')
    parser.add_argument('--csv-file', default='applicablejobs.csv',
                       help='CSV file to use for job data (default: applicablejobs.csv)')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("LinkedIn Job Application Bot")
    print("=" * 80)
    
    if args.mode in ['fetch', 'both']:
        print("\n🔄 Starting Job Fetching...")
        print("-" * 40)
        try:
            from job_fetcher import main_fetch
            main_fetch()
            print("✅ Job fetching completed successfully!")
        except Exception as e:
            print(f"❌ Job fetching failed: {e}")
            if args.mode == 'fetch':
                sys.exit(1)
    
    if args.mode in ['apply', 'both']:
        print("\n📝 Starting Auto-Applying...")
        print("-" * 40)
        
        # Check if applicablejobs.csv exists
        if not os.path.exists(args.csv_file):
            print(f"❌ File {args.csv_file} not found!")
            print("Please run job fetching first or check the file path.")
            sys.exit(1)
            
        try:
            from auto_applier import main_apply
            main_apply()
            print("✅ Auto-applying completed successfully!")
        except Exception as e:
            print(f"❌ Auto-applying failed: {e}")
            sys.exit(1)
    
    print("\n🎉 All operations completed!")
    print("=" * 80)

if __name__ == "__main__":
    main()