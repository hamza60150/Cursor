#!/bin/bash

# HTML Fetcher Shell Wrapper
# Makes it easy to fetch HTML from websites with common options

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/html_fetcher.py"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Error: html_fetcher.py not found in $SCRIPT_DIR"
    exit 1
fi

# Check if URL is provided
if [ $# -eq 0 ]; then
    echo "HTML Fetcher - Fetch HTML structure from any website"
    echo ""
    echo "Usage: $0 <URL> [options]"
    echo ""
    echo "Examples:"
    echo "  $0 https://example.com"
    echo "  $0 example.com --beautify"
    echo "  $0 https://example.com --output page.html"
    echo "  $0 https://example.com --format text"
    echo "  $0 https://example.com --headers --timeout 60"
    echo ""
    echo "Quick Options:"
    echo "  --beautify, -b    : Pretty print HTML"
    echo "  --text           : Extract text content only"
    echo "  --headers        : Show response headers"
    echo "  --metadata-only  : Show only metadata"
    echo ""
    echo "For full options, run: python3 $PYTHON_SCRIPT --help"
    exit 1
fi

# Parse arguments and convert some shortcuts
ARGS=()
for arg in "$@"; do
    case $arg in
        --text)
            ARGS+=("--format" "text")
            ;;
        *)
            ARGS+=("$arg")
            ;;
    esac
done

# Run the Python script with all arguments
python3 "$PYTHON_SCRIPT" "${ARGS[@]}"