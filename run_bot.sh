#!/bin/bash

# LinkedIn Job Application Bot Runner Script
# This script provides an easy way to run the bot with common configurations

# Default values
JOBS_FILE="jobs.json"
PROFILE_FILE="profile.json"
COOKIES_FILE="cookies/linkedin_cookies.json"
MAX_APPLICATIONS=5
LOG_FILE="logs/bot_$(date +%Y%m%d_%H%M%S).log"
HEADLESS=false
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show help
show_help() {
    echo "LinkedIn Job Application Bot Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -j, --jobs-file FILE        Jobs JSON file (default: jobs.json)"
    echo "  -p, --profile-file FILE     Profile JSON file (default: profile.json)"
    echo "  -c, --cookies-file FILE     Cookies JSON file (default: cookies/linkedin_cookies.json)"
    echo "  -m, --max-applications NUM  Maximum applications (default: 5)"
    echo "  -l, --log-file FILE         Log file (default: logs/bot_TIMESTAMP.log)"
    echo "  -H, --headless              Run in headless mode"
    echo "  -v, --verbose               Enable verbose logging"
    echo "  -h, --help                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                          # Run with default settings"
    echo "  $0 -j my_jobs.json -m 10   # Custom jobs file, max 10 applications"
    echo "  $0 -H -v                    # Headless mode with verbose logging"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -j|--jobs-file)
            JOBS_FILE="$2"
            shift 2
            ;;
        -p|--profile-file)
            PROFILE_FILE="$2"
            shift 2
            ;;
        -c|--cookies-file)
            COOKIES_FILE="$2"
            shift 2
            ;;
        -m|--max-applications)
            MAX_APPLICATIONS="$2"
            shift 2
            ;;
        -l|--log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        -H|--headless)
            HEADLESS=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Pre-flight checks
print_info "Running pre-flight checks..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if required files exist
if [[ ! -f "$JOBS_FILE" ]]; then
    print_error "Jobs file not found: $JOBS_FILE"
    exit 1
fi

if [[ ! -f "$PROFILE_FILE" ]]; then
    print_error "Profile file not found: $PROFILE_FILE"
    exit 1
fi

if [[ ! -f "linkedin_apply_bot.py" ]]; then
    print_error "Main bot script not found: linkedin_apply_bot.py"
    exit 1
fi

# Check if requirements are installed
if [[ ! -f "requirements.txt" ]]; then
    print_warning "requirements.txt not found, skipping dependency check"
else
    print_info "Checking Python dependencies..."
    if ! python3 -c "import undetected_chromedriver, selenium" &> /dev/null; then
        print_warning "Some dependencies may be missing. Installing..."
        pip3 install -r requirements.txt
    fi
fi

# Create necessary directories
print_info "Creating directories..."
mkdir -p logs screenshots data cookies

# Build command
CMD="python3 linkedin_apply_bot.py"
CMD="$CMD --jobs-file '$JOBS_FILE'"
CMD="$CMD --profile-file '$PROFILE_FILE'"
CMD="$CMD --max-applications $MAX_APPLICATIONS"
CMD="$CMD --log-file '$LOG_FILE'"

if [[ -f "$COOKIES_FILE" ]]; then
    CMD="$CMD --cookies-file '$COOKIES_FILE'"
fi

if [[ "$HEADLESS" == "true" ]]; then
    CMD="$CMD --headless"
fi

if [[ "$VERBOSE" == "true" ]]; then
    CMD="$CMD --verbose"
fi

# Show configuration
print_info "Configuration:"
echo "  Jobs file: $JOBS_FILE"
echo "  Profile file: $PROFILE_FILE"
echo "  Cookies file: $COOKIES_FILE"
echo "  Max applications: $MAX_APPLICATIONS"
echo "  Log file: $LOG_FILE"
echo "  Headless mode: $HEADLESS"
echo "  Verbose logging: $VERBOSE"
echo ""

# Confirm before running
read -p "Do you want to proceed? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Operation cancelled by user"
    exit 0
fi

# Run the bot
print_info "Starting LinkedIn Job Application Bot..."
print_info "Command: $CMD"
echo ""

eval $CMD
exit_code=$?

# Check results
if [[ $exit_code -eq 0 ]]; then
    print_success "Bot execution completed successfully!"
else
    print_error "Bot execution failed with exit code: $exit_code"
fi

# Show log file location
if [[ -f "$LOG_FILE" ]]; then
    print_info "Log file saved to: $LOG_FILE"
fi

exit $exit_code