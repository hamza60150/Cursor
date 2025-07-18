# LinkedIn Job Application Bot

An automated job application bot that applies to jobs from LinkedIn and other job platforms using Selenium WebDriver. The bot intelligently fills out job application forms using your profile information and handles various job platforms.

## Features

- **Multi-Platform Support**: Works with LinkedIn, Indeed, Glassdoor, and other job platforms
- **Intelligent Form Filling**: Automatically detects and fills common form fields
- **Smart Platform Prioritization**: Prioritizes LinkedIn applications over other platforms
- **Comprehensive Logging**: Detailed logging with statistics and error tracking
- **Cookie Management**: Saves and loads browser sessions for faster processing
- **Configurable Delays**: Human-like delays to avoid detection
- **File Upload Support**: Automatically uploads resume and cover letter files
- **Graceful Error Handling**: Continues processing even if individual applications fail
- **Statistics Tracking**: Tracks success rates and application history

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd linkedin-job-application-bot
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install Chrome browser** (if not already installed)

4. **Setup your profile**:
   - Edit `profile.json` with your personal information
   - Place your resume file in the project directory
   - Update the `resume_path` in `profile.json`

## Configuration

### Profile Setup (`profile.json`)

```json
{
  "email": "your.email@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1-555-123-4567",
  "address": "123 Main Street",
  "city": "New York",
  "state": "NY",
  "zip": "10001",
  "country": "United States",
  "linkedin": "https://linkedin.com/in/johndoe",
  "website": "https://johndoe.com",
  "resume_path": "./resume.pdf",
  "cover_letter": "Your cover letter text here..."
}
```

### Jobs Data Format (`jobs.json`)

```json
[
  {
    "title": "Software Engineer",
    "companyName": "Tech Corp",
    "location": "San Francisco, CA",
    "applyLinksDetails": [
      {
        "platform": "LinkedIn",
        "url": "https://www.linkedin.com/jobs/view/1234567890"
      }
    ],
    "link": ["https://www.linkedin.com/jobs/view/1234567890"]
  }
]
```

## Usage

### Basic Usage

```bash
python linkedin_apply_bot.py --jobs-file jobs.json --profile-file profile.json
```

### Advanced Usage

```bash
python linkedin_apply_bot.py \
  --jobs-file jobs.json \
  --profile-file profile.json \
  --cookies-file cookies.json \
  --max-applications 10 \
  --headless \
  --log-file bot.log \
  --verbose
```

### Command Line Arguments

- `--jobs-file`: Path to JSON file containing job listings (required)
- `--profile-file`: Path to JSON file containing your profile information (required)
- `--cookies-file`: Path to save/load browser cookies (optional)
- `--headless`: Run browser in headless mode (optional)
- `--max-applications`: Maximum number of applications to submit (default: 5)
- `--log-file`: Path to log file (optional)
- `--verbose`: Enable verbose logging (optional)
- `--delay-min`: Minimum delay between actions in seconds (default: 1.0)
- `--delay-max`: Maximum delay between actions in seconds (default: 3.0)

## How It Works

1. **Job Processing**: The bot reads job listings from your JSON file
2. **Platform Detection**: Identifies the job platform (LinkedIn, Indeed, etc.)
3. **URL Prioritization**: Prioritizes LinkedIn applications over other platforms
4. **Navigation**: Opens the job application page
5. **Form Detection**: Automatically detects form fields on the page
6. **Form Filling**: Fills out the form using your profile information
7. **File Upload**: Uploads resume and cover letter files if required
8. **Submission**: Submits the application
9. **Logging**: Records the success/failure of each application

## Supported Platforms

- **LinkedIn** (Primary support with advanced selectors)
- **Indeed**
- **Glassdoor**
- **Workable**
- **Lever**
- **Greenhouse**
- **Jobvite**
- **SmartRecruiters**
- **BambooHR**
- **Recruitee**
- **Workday**
- **Generic platforms** (basic form detection)

## LinkedIn Specific Features

The bot includes special handling for LinkedIn applications:

- Multiple selector strategies for the "Apply" button
- Handles LinkedIn's job application redirects
- Supports both direct LinkedIn applications and external redirects
- Optimized for LinkedIn's form structure

## Safety Features

- **Human-like delays**: Random delays between actions to avoid detection
- **Error handling**: Continues processing even if individual applications fail
- **Rate limiting**: Configurable delays between job applications
- **Graceful shutdown**: Proper cleanup on interruption
- **Cookie management**: Maintains session state across runs

## File Structure

```
linkedin-job-application-bot/
├── linkedin_apply_bot.py     # Main bot script
├── config.py                 # Configuration settings
├── utils.py                  # Utility functions
├── requirements.txt          # Python dependencies
├── profile.json             # Your profile information
├── jobs_sample.json         # Sample jobs data format
├── README.md               # This file
├── logs/                   # Log files directory
├── screenshots/            # Screenshots directory
├── data/                   # Application history
└── cookies/               # Browser cookies
```

## Logging

The bot provides comprehensive logging:

- **Console output**: Real-time progress updates
- **File logging**: Detailed logs saved to file
- **Application history**: JSON log of all application attempts
- **Statistics**: Success rates and performance metrics

## Troubleshooting

### Common Issues

1. **Chrome driver issues**: Make sure Chrome browser is installed and up to date
2. **Element not found**: Some websites may have changed their structure
3. **Rate limiting**: Increase delays if you're getting blocked
4. **File upload issues**: Check file paths and permissions

### Debug Mode

Run with `--verbose` flag for detailed debugging information:

```bash
python linkedin_apply_bot.py --jobs-file jobs.json --profile-file profile.json --verbose
```

## Ethical Considerations

- **Use responsibly**: Only apply to jobs you're genuinely interested in
- **Follow platform terms**: Respect the terms of service of job platforms
- **Rate limiting**: Don't overwhelm servers with too many requests
- **Quality over quantity**: Focus on relevant job applications

## Legal Disclaimer

This tool is for educational and personal use only. Users are responsible for complying with the terms of service of job platforms and applicable laws. The authors are not responsible for any misuse of this software.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository.