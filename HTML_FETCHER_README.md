# HTML Fetcher

A robust Python script that automatically fetches the HTML structure of any website with comprehensive error handling, multiple output formats, and flexible options.

## Features

- ✅ **Automatic URL validation and normalization** (adds https:// if missing)
- ✅ **Robust error handling** for network issues, timeouts, and HTTP errors
- ✅ **Multiple output formats**: HTML, text content, or pretty-printed HTML
- ✅ **Flexible output options**: console output or save to file
- ✅ **Request metadata**: shows status codes, headers, timing, and more
- ✅ **Realistic user agent** to avoid being blocked by websites
- ✅ **Configurable timeouts** and request options
- ✅ **Beautiful command-line interface** with comprehensive help
- ✅ **Shell wrapper** for easier usage

## Installation

### Prerequisites

Make sure you have Python 3.6+ installed. The script requires two Python packages:

```bash
pip install requests beautifulsoup4
```

Or if you're in a managed environment:

```bash
pip install --break-system-packages requests beautifulsoup4
```

### Files

The HTML fetcher consists of two main files:

1. **`html_fetcher.py`** - Main Python script
2. **`fetch_html.sh`** - Shell wrapper for easier usage

Make both files executable:

```bash
chmod +x html_fetcher.py fetch_html.sh
```

## Usage

### Using the Python Script Directly

```bash
# Basic usage
python3 html_fetcher.py https://example.com

# Save to file with pretty formatting
python3 html_fetcher.py https://example.com --output page.html --beautify

# Extract only text content
python3 html_fetcher.py https://example.com --format text

# Show response headers and metadata
python3 html_fetcher.py https://example.com --headers

# Custom timeout and metadata only
python3 html_fetcher.py https://example.com --timeout 60 --metadata-only
```

### Using the Shell Wrapper

The shell wrapper provides a simpler interface:

```bash
# Basic usage
./fetch_html.sh https://example.com

# Quick options
./fetch_html.sh example.com --beautify
./fetch_html.sh https://example.com --text
./fetch_html.sh https://example.com --headers
./fetch_html.sh https://example.com --metadata-only
```

## Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output file path (saves to file instead of console) |
| `--format` | `-f` | Output format: `html`, `text`, or `pretty` (default: html) |
| `--timeout` | `-t` | Request timeout in seconds (default: 30) |
| `--headers` | | Include response headers in metadata output |
| `--beautify` | `-b` | Pretty print the HTML structure |
| `--save-raw` | | Save raw HTML without any processing |
| `--metadata-only` | | Show only metadata, don't output content |
| `--help` | `-h` | Show help message and exit |

## Examples

### Basic HTML Fetching

```bash
# Fetch HTML from a website
python3 html_fetcher.py https://httpbin.org/html
```

### Save Pretty-Formatted HTML

```bash
# Save beautifully formatted HTML to a file
python3 html_fetcher.py https://example.com --beautify --output example.html
```

### Extract Text Content

```bash
# Extract only the text content (no HTML tags)
python3 html_fetcher.py https://news.ycombinator.com --format text --output news.txt
```

### Quick Metadata Check

```bash
# Just check if a website is accessible and get basic info
python3 html_fetcher.py https://example.com --metadata-only --headers
```

### Handle Slow Websites

```bash
# Increase timeout for slow websites
python3 html_fetcher.py https://slow-website.com --timeout 120
```

## Output Examples

### Metadata Output

```
==================================================
FETCH METADATA
==================================================
Original URL: https://httpbin.org/html
Status Code: 200
Encoding: utf-8
Content Length: 3,741 bytes
Fetch Time: 1.07 seconds
==================================================
```

### With Headers

```
==================================================
FETCH METADATA
==================================================
Original URL: https://httpbin.org/html
Status Code: 200
Encoding: utf-8
Content Length: 3,741 bytes
Fetch Time: 1.07 seconds

RESPONSE HEADERS:
------------------------------
Content-Type: text/html; charset=utf-8
Content-Length: 3741
Server: gunicorn/19.9.0
==================================================
```

## Error Handling

The script handles various error conditions gracefully:

- **Network timeouts**: Configurable timeout with clear error messages
- **Connection errors**: Handles DNS resolution failures and connection refused
- **HTTP errors**: Reports HTTP status codes (404, 500, etc.) with context
- **Invalid URLs**: Validates and normalizes URLs before making requests
- **File I/O errors**: Clear messages for file saving issues

## Advanced Features

### URL Normalization

The script automatically:
- Adds `https://` protocol if missing
- Validates URL format
- Handles redirects automatically
- Reports final URL if different from original

### Smart User Agent

Uses a realistic browser user agent to avoid being blocked:
```
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36
```

### Session Management

Uses a persistent session for efficient connection reuse and proper cookie handling.

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Install required packages
   ```bash
   pip install requests beautifulsoup4
   ```

2. **Permission denied**: Make scripts executable
   ```bash
   chmod +x html_fetcher.py fetch_html.sh
   ```

3. **Timeout errors**: Increase timeout for slow websites
   ```bash
   python3 html_fetcher.py https://slow-site.com --timeout 120
   ```

4. **Blocked by website**: Some sites block automated requests. The script uses realistic headers, but some sites may still block.

### Getting Help

```bash
# Show full help
python3 html_fetcher.py --help

# Show shell wrapper help
./fetch_html.sh
```

## Integration

The HTML fetcher can be easily integrated into other scripts or workflows:

```python
from html_fetcher import HTMLFetcher

# Create fetcher instance
fetcher = HTMLFetcher(timeout=30)

# Fetch HTML
result = fetcher.fetch_html('https://example.com')

# Access the data
print(f"Status: {result['status_code']}")
print(f"Content: {result['content']}")
```

## License

This script is provided as-is for educational and practical use. Feel free to modify and distribute according to your needs.