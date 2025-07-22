# Enhanced LinkedIn Job Application Bot

## 🚀 New Features Overview

This enhanced version of the LinkedIn Job Application Bot includes powerful new features that leverage LLM technology and GitHub integration for intelligent job matching and comprehensive application tracking.

## 🤖 LLM Integration

### Features
- **Intelligent Job Analysis**: Uses LLM to analyze job compatibility with your profile
- **Custom Cover Letter Generation**: Automatically generates tailored cover letters for each job
- **Smart Job Filtering**: Skips jobs with low relevance scores to save time
- **Application Strategy Recommendations**: Gets AI-powered advice on how to approach each application

### Supported LLM Providers
- **OpenAI** (GPT-4, GPT-3.5-turbo)
- **Anthropic** (Claude models)
- **Ollama** (Local models like Llama2, CodeLlama)

### Configuration
```bash
# In .env file
LLM_PROVIDER=ollama  # or openai, anthropic
LLM_MODEL=llama2     # Model name
LLM_API_KEY=your_api_key  # Required for OpenAI/Anthropic
OLLAMA_BASE_URL=http://localhost:11434  # For local Ollama
```

## 🐙 GitHub Integration

### Features
- **Automatic Issue Creation**: Creates GitHub issues to track each job application
- **Status Tracking**: Updates application status through issue labels and comments
- **Application Statistics**: Generates comprehensive stats from your application history
- **Automated Backups**: Backs up application data to your repository
- **Weekly Reports**: Generates weekly summary reports

### GitHub Issue Management
Each job application creates an issue with:
- Job details and application information
- Automatic labels for status tracking
- Links to job postings
- Follow-up reminders and notes

### Issue Commands
Use these commands in issue comments:
- `/status <new_status>` - Update application status
- `/follow-up` - Generate follow-up message
- `/analyze` - Re-analyze job compatibility

### Configuration
```bash
# In .env file
GITHUB_TOKEN=your_personal_access_token
GITHUB_REPO_OWNER=your_username
GITHUB_REPO_NAME=your_repo_name
```

## 🎯 Intelligent Job Filtering

### Smart Analysis
- **Relevance Scoring**: Each job gets a 0-100 relevance score
- **Skill Matching**: Analyzes required skills vs. your profile
- **Location Compatibility**: Considers location preferences
- **Experience Level**: Matches seniority requirements

### Filtering Options
```bash
MIN_RELEVANCE_SCORE=60  # Skip jobs below this score
ENABLE_SMART_FILTERING=true
SKIP_LOW_RELEVANCE_JOBS=true
```

## 📊 Enhanced Reporting

### Session Reports
- Detailed application statistics
- Success/failure analysis
- Time tracking and performance metrics
- LLM analysis results

### GitHub Statistics
- Total applications by status
- Platform breakdown (LinkedIn, Indeed, etc.)
- Monthly application trends
- Success rate calculations

## 🔧 Webhook Automation

### GitHub Webhooks
The webhook handler responds to GitHub events:
- **Issue Creation**: Automatically sets up tracking
- **Status Updates**: Processes status changes
- **Follow-up Reminders**: Schedules automatic reminders

### Webhook Server
```bash
# Start webhook server
./run_webhook_server.sh

# Server runs on port 5000 by default
# Endpoint: http://your-server:5000/webhook/github
```

## 🚀 Quick Start

### 1. Setup
```bash
# Run the setup script
python3 setup_enhanced_bot.py

# Follow the interactive setup process
```

### 2. Configuration
Edit the generated files:
- `.env` - API keys and configuration
- `profile.json` - Your personal information
- `jobs.json` - Job listings to apply to

### 3. Run Enhanced Bot
```bash
# Basic usage
./run_enhanced_bot.sh

# Or with custom parameters
python3 enhanced_bot.py --jobs-file jobs.json --profile-file profile.json --max-applications 10
```

### 4. Start Webhook Server (Optional)
```bash
./run_webhook_server.sh
```

## 📁 File Structure

```
enhanced-linkedin-bot/
├── enhanced_bot.py           # Main enhanced bot controller
├── llm_integration.py        # LLM analysis and generation
├── github_integration.py     # GitHub API integration
├── webhook_handler.py        # GitHub webhook server
├── setup_enhanced_bot.py     # Setup and configuration script
├── run_enhanced_bot.sh       # Bot startup script
├── run_webhook_server.sh     # Webhook server startup script
├── linkedin_apply_bot.py     # Original bot (enhanced)
├── config.py                 # Configuration settings
├── utils.py                  # Utility functions
├── requirements.txt          # Python dependencies
├── .env                      # Environment configuration
├── profile.json              # Your profile information
├── jobs.json                 # Job listings
├── logs/                     # Application logs
├── reports/                  # Session reports
├── screenshots/              # Browser screenshots
└── backups/                  # Application data backups
```

## 🎛️ Command Line Options

### Enhanced Bot
```bash
python3 enhanced_bot.py [options]

Options:
  --jobs-file FILE          Path to jobs JSON file (required)
  --profile-file FILE       Path to profile JSON file (required)
  --max-applications N      Maximum applications to submit (default: 5)
  --log-file FILE          Path to log file
  --verbose                Enable verbose logging
  --headless               Run browser in headless mode
```

### Webhook Server
```bash
python3 webhook_handler.py

Environment Variables:
  WEBHOOK_PORT=5000        Server port (default: 5000)
  WEBHOOK_HOST=0.0.0.0     Server host (default: 0.0.0.0)
```

## 🔍 Monitoring and Debugging

### Logs
- Console output with real-time progress
- Detailed file logs in `logs/` directory
- Session reports in `reports/` directory

### Health Check
```bash
# Check webhook server status
curl http://localhost:5000/health

# Get application statistics
curl http://localhost:5000/stats
```

### Debugging
```bash
# Enable verbose logging
python3 enhanced_bot.py --verbose --jobs-file jobs.json --profile-file profile.json

# Check LLM integration
python3 -c "from llm_integration import load_llm_config; print(load_llm_config())"

# Test GitHub integration
python3 -c "from github_integration import load_github_config; print(load_github_config())"
```

## 🔐 Security Best Practices

### API Keys
- Store API keys in `.env` file (never commit to git)
- Use environment variables in production
- Rotate keys regularly

### GitHub Tokens
- Use personal access tokens with minimal required permissions
- Enable token expiration
- Use separate tokens for different environments

### Webhook Security
- Set webhook secrets for signature verification
- Use HTTPS in production
- Validate all incoming webhook payloads

## 🤝 Contributing

### Development Setup
```bash
# Clone and setup
git clone <your-repo>
cd enhanced-linkedin-bot
python3 setup_enhanced_bot.py

# Install development dependencies
pip install -r requirements-dev.txt
```

### Adding New LLM Providers
1. Extend `LLMProvider` enum in `llm_integration.py`
2. Implement provider-specific client in `LLMIntegration` class
3. Add configuration options to `LLMConfig`
4. Update documentation

### Adding New Features
1. Follow existing code patterns
2. Add comprehensive logging
3. Include error handling
4. Update configuration options
5. Add tests and documentation

## 📞 Support

### Common Issues
- **LLM API Errors**: Check API keys and quotas
- **GitHub Rate Limits**: Implement proper rate limiting
- **Webhook Failures**: Verify server accessibility and secrets

### Getting Help
- Check logs for detailed error messages
- Review configuration files
- Test individual components
- Open GitHub issues for bugs

### Resources
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic API Documentation](https://docs.anthropic.com)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [Ollama Documentation](https://ollama.ai/docs)

## 📄 License

This enhanced version maintains the same license as the original project. See LICENSE file for details.

---

**Happy job hunting with AI-powered automation! 🚀**
