#!/usr/bin/env python3
"""
HTML Structure Fetcher
A script that automatically fetches the HTML structure of any website.

Usage:
    python html_fetcher.py <URL> [options]
    
Options:
    --output, -o: Output file path (optional)
    --format, -f: Output format (html, text, pretty) - default: html
    --timeout, -t: Request timeout in seconds - default: 30
    --headers, -h: Include response headers in output
    --beautify, -b: Pretty print the HTML structure
    --save-raw: Save raw HTML without any processing
"""

import argparse
import sys
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import time
import json
from typing import Optional, Dict, Any


class HTMLFetcher:
    """A class to fetch and process HTML from websites."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set a realistic user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def validate_url(self, url: str) -> str:
        """Validate and normalize the URL."""
        if not url:
            raise ValueError("URL cannot be empty")
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Parse URL to validate
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValueError(f"Invalid URL: {url}")
        
        return url
    
    def fetch_html(self, url: str) -> Dict[str, Any]:
        """
        Fetch HTML content from the given URL.
        
        Returns:
            Dict containing response data, headers, and metadata
        """
        url = self.validate_url(url)
        
        try:
            print(f"Fetching HTML from: {url}")
            start_time = time.time()
            
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            fetch_time = time.time() - start_time
            
            return {
                'url': url,
                'final_url': response.url,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text,
                'encoding': response.encoding,
                'fetch_time': round(fetch_time, 2),
                'content_length': len(response.content),
                'redirected': url != response.url
            }
            
        except requests.exceptions.Timeout:
            raise Exception(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Failed to connect to {url}")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error {response.status_code}: {e}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    def format_html(self, html_content: str, format_type: str = 'html', beautify: bool = False) -> str:
        """
        Format HTML content based on the specified format type.
        
        Args:
            html_content: Raw HTML content
            format_type: 'html', 'text', or 'pretty'
            beautify: Whether to pretty print the HTML
        
        Returns:
            Formatted content string
        """
        if format_type == 'html':
            if beautify:
                soup = BeautifulSoup(html_content, 'html.parser')
                return soup.prettify()
            return html_content
        
        elif format_type == 'text':
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text(strip=True, separator='\n')
        
        elif format_type == 'pretty':
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.prettify()
        
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def save_to_file(self, content: str, filepath: str) -> None:
        """Save content to a file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Content saved to: {filepath}")
        except IOError as e:
            raise Exception(f"Failed to save file: {e}")
    
    def print_metadata(self, data: Dict[str, Any], include_headers: bool = False) -> None:
        """Print metadata about the fetched content."""
        print(f"\n{'='*50}")
        print("FETCH METADATA")
        print(f"{'='*50}")
        print(f"Original URL: {data['url']}")
        if data['redirected']:
            print(f"Final URL: {data['final_url']}")
        print(f"Status Code: {data['status_code']}")
        print(f"Encoding: {data['encoding']}")
        print(f"Content Length: {data['content_length']:,} bytes")
        print(f"Fetch Time: {data['fetch_time']} seconds")
        
        if include_headers:
            print(f"\nRESPONSE HEADERS:")
            print(f"{'-'*30}")
            for key, value in data['headers'].items():
                print(f"{key}: {value}")
        
        print(f"{'='*50}\n")


def main():
    """Main function to handle command line arguments and execute the fetcher."""
    parser = argparse.ArgumentParser(
        description="Fetch HTML structure from any website",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python html_fetcher.py https://example.com
    python html_fetcher.py example.com -o output.html -b
    python html_fetcher.py https://example.com -f text -o content.txt
    python html_fetcher.py https://example.com --headers --timeout 60
        """
    )
    
    parser.add_argument('url', help='URL of the website to fetch')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-f', '--format', choices=['html', 'text', 'pretty'], 
                       default='html', help='Output format (default: html)')
    parser.add_argument('-t', '--timeout', type=int, default=30, 
                       help='Request timeout in seconds (default: 30)')
    parser.add_argument('--headers', action='store_true', 
                       help='Include response headers in output')
    parser.add_argument('-b', '--beautify', action='store_true', 
                       help='Pretty print the HTML structure')
    parser.add_argument('--save-raw', action='store_true', 
                       help='Save raw HTML without any processing')
    parser.add_argument('--metadata-only', action='store_true', 
                       help='Only show metadata, don\'t output content')
    
    args = parser.parse_args()
    
    try:
        # Create fetcher instance
        fetcher = HTMLFetcher(timeout=args.timeout)
        
        # Fetch HTML
        result = fetcher.fetch_html(args.url)
        
        # Print metadata
        fetcher.print_metadata(result, include_headers=args.headers)
        
        # If metadata-only flag is set, exit here
        if args.metadata_only:
            return
        
        # Format content
        if args.save_raw:
            formatted_content = result['content']
        else:
            formatted_content = fetcher.format_html(
                result['content'], 
                format_type=args.format, 
                beautify=args.beautify
            )
        
        # Output content
        if args.output:
            fetcher.save_to_file(formatted_content, args.output)
        else:
            print("HTML CONTENT:")
            print("-" * 50)
            print(formatted_content)
        
        print(f"\n✅ Successfully fetched HTML from {result['url']}")
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()