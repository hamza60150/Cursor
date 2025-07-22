# 🤖 Adaptive Job Application Bot

## 🚀 Revolutionary AI-Powered Web Automation

This is not just another job application bot - it's an **intelligent web automation agent** that adapts to any website structure using LLM technology. Built specifically for website integration, it can automatically apply to jobs on ANY platform by intelligently analyzing and navigating website structures in real-time.

## 🎯 What Makes This Bot Special

### 🧠 **AI-Powered Adaptability**
- **Real-time HTML Analysis**: Uses LLM to understand any website structure
- **Dynamic Strategy Adjustment**: Adapts navigation approach based on obstacles
- **Intelligent Form Detection**: Automatically identifies and fills application forms
- **Context-Aware Decision Making**: Makes smart choices based on page content

### 🌐 **Universal Compatibility**
- **Any Job Platform**: LinkedIn, Indeed, Glassdoor, company websites, ATS systems
- **Any Website Structure**: Adapts to different HTML layouts and designs
- **Multiple Form Types**: Handles simple forms to complex multi-step applications
- **Dynamic Content**: Works with JavaScript-heavy and dynamic websites

### 🛡️ **Advanced Anti-Detection**
- **Stealth Browser Technology**: Undetected Chrome with anti-bot measures
- **Human-like Behavior**: Random delays, mouse movements, typing patterns
- **Cookie Management**: Automatic session persistence and management
- **Proxy Support**: IP rotation for large-scale usage

### 📊 **Enterprise-Grade Features**
- **RESTful API**: Easy integration with your website/application
- **Session Management**: Handle multiple concurrent applications
- **Real-time Monitoring**: Track progress and success rates
- **Comprehensive Analytics**: Detailed reporting and insights

## ��️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Your Website  │───▶│  Adaptive Bot    │───▶│   Job Website   │
│                 │    │      API         │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                          │
                              ▼                          │
                    ┌──────────────────┐                 │
                    │  LLM Integration │                 │
                    │  (OpenAI/Ollama) │                 │
                    └──────────────────┘                 │
                              │                          │
                              ▼                          │
                    ┌──────────────────┐                 │
                    │ HTML Analyzer &  │◀────────────────┘
                    │ Resume Parser    │
                    └──────────────────┘
```

## 🚀 Quick Start for Website Integration

### 1. **Start the API Server**
```bash
./start_adaptive_bot_api.sh
```

### 2. **Frontend Integration (JavaScript)**
```javascript
// Apply to a job from your website
async function applyToJob(jobTitle, resumeFile, jobUrl) {
    const response = await fetch('/api/apply-job', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            job_title: jobTitle,
            resume: await fileToBase64(resumeFile),
            website_html: document.documentElement.outerHTML,
            website_url: jobUrl
        })
    });
    
    const result = await response.json();
    return result.session_id;
}

// Monitor application progress
async function checkApplicationStatus(sessionId) {
    const response = await fetch(`/api/session/${sessionId}/status`);
    return await response.json();
}
```

### 3. **Backend Integration (Python)**
```python
import requests

def apply_to_job(user_id, job_id):
    # Get job and user data from your database
    job = get_job(job_id)
    user_resume = get_user_resume(user_id)
    
    # Start application with adaptive bot
    response = requests.post('http://localhost:8000/api/apply-job', json={
        'job_title': job['title'],
        'resume': user_resume,
        'website_html': job['company_html'],
        'website_url': job['application_url']
    })
    
    return response.json()['session_id']
```

## 📡 API Endpoints

### **Core Application Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/apply-job` | Start job application process |
| `GET` | `/api/session/{id}/status` | Check application status |
| `POST` | `/api/session/{id}/cancel` | Cancel application |
| `GET` | `/api/sessions` | List all active sessions |

### **Utility Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/parse-resume` | Parse resume data |
| `POST` | `/api/analyze-website` | Analyze website structure |
| `POST` | `/api/test-connection` | Test website connectivity |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/config` | Get current configuration |

## 📋 API Request Examples

### **Start Job Application**
```bash
curl -X POST http://localhost:8000/api/apply-job \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Senior Python Developer",
    "resume": "John Doe\nsoftware engineer...",
    "website_html": "<html>...</html>",
    "website_url": "https://company.com/jobs/123"
  }'
```

**Response:**
```json
{
  "session_id": "abc123-def456",
  "status": "started",
  "message": "Job application process started"
}
```

### **Check Status**
```bash
curl http://localhost:8000/api/session/abc123-def456/status
```

**Response:**
```json
{
  "session_id": "abc123-def456",
  "status": "completed",
  "job_title": "Senior Python Developer",
  "result": {
    "success": true,
    "message": "Application submitted successfully",
    "navigation_steps": 8,
    "form_fields_filled": 5
  }
}
```

## ⚙️ Configuration

### **Environment Variables**
```bash
# LLM Configuration
LLM_PROVIDER=ollama          # ollama, openai, anthropic
LLM_MODEL=llama2            # Model name
LLM_API_KEY=your_api_key    # Required for OpenAI/Anthropic

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Browser Configuration
HEADLESS_MODE=true
BROWSER_TIMEOUT=30

# Advanced Settings
MAX_CONCURRENT_SESSIONS=5
SESSION_TIMEOUT_HOURS=2
ENABLE_PROXY_ROTATION=false
```

### **LLM Provider Setup**

#### **Ollama (Local, Free)**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama
ollama serve

# Pull a model
ollama pull llama2
```

#### **OpenAI (Cloud)**
```bash
export LLM_PROVIDER=openai
export LLM_API_KEY=your_openai_api_key
export LLM_MODEL=gpt-4
```

#### **Anthropic (Cloud)**
```bash
export LLM_PROVIDER=anthropic
export LLM_API_KEY=your_anthropic_api_key
export LLM_MODEL=claude-3-sonnet-20240229
```

## 🔧 How It Works

### **1. Intelligent HTML Analysis**
```python
# The bot analyzes any website structure
analysis = await html_analyzer.analyze_html(website_html, base_url)

# Results include:
# - Page type (job_listing, application_form, etc.)
# - Apply buttons and their selectors
# - Form fields and their purposes
# - Navigation paths to application
# - Potential obstacles (CAPTCHA, login, etc.)
```

### **2. LLM-Powered Navigation**
```python
# Bot asks LLM for navigation strategy
prompt = f"""
Analyze this HTML and provide navigation steps to apply for job:
{html_content}

Current situation: {current_context}
Previous attempts: {navigation_history}

Provide JSON response with specific actions...
"""

response = await llm.analyze(prompt)
actions = parse_navigation_steps(response)
```

### **3. Adaptive Execution**
```python
# Bot executes steps and adapts based on results
for step in navigation_steps:
    success = await execute_step(step)
    
    if not success:
        # Get new strategy from LLM
        alternative_strategy = await llm.get_alternative_approach(
            current_html, failed_step, context
        )
        
        # Try alternative approach
        success = await execute_alternative(alternative_strategy)
```

## 🛡️ Anti-Detection Features

### **Browser Stealth**
- Undetected Chrome with modified fingerprints
- Random user agents and viewport sizes
- Disabled automation indicators
- Custom Chrome DevTools Protocol commands

### **Human-like Behavior**
- Random delays between actions (1-3 seconds)
- Mouse movements and scrolling
- Typing with realistic speed variation
- Random pauses and "thinking" time

### **Session Management**
- Automatic cookie saving and loading
- Session persistence across requests
- IP rotation support (with proxy configuration)
- User-Agent rotation

## 📊 Success Metrics

The bot tracks comprehensive metrics:

- **Application Success Rate**: % of successful applications
- **Platform Performance**: Success rates by job platform
- **Navigation Efficiency**: Average steps to complete application
- **Obstacle Handling**: How well it handles different challenges
- **Speed Metrics**: Time to complete applications
- **Error Analysis**: Categorization of failures and improvements

## 🔍 Monitoring & Debugging

### **Real-time Logs**
```bash
# View live logs
tail -f logs/adaptive_bot.log

# Check specific session
curl http://localhost:8000/api/session/abc123/status
```

### **Debug Mode**
```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG

# Enable browser screenshots
export ENABLE_SCREENSHOTS=true

# Keep browser open for inspection
export HEADLESS_MODE=false
```

## 🚦 Rate Limiting & Scaling

### **Concurrent Sessions**
- Maximum 5 concurrent applications by default
- Queue management for high-volume usage
- Automatic session cleanup after 2 hours
- Resource monitoring and management

### **Rate Limiting**
- Intelligent delays between applications
- Platform-specific rate limiting
- Respect robots.txt and rate limits
- Automatic backoff on errors

## 🔒 Security & Privacy

### **Data Protection**
- Resume data encrypted in transit
- Temporary session storage only
- Automatic cleanup of sensitive data
- No persistent storage of personal information

### **Ethical Usage**
- Respects website terms of service
- Implements reasonable rate limiting
- Provides user-agent identification
- Supports opt-out mechanisms

## 🆘 Troubleshooting

### **Common Issues**

**LLM Not Responding**
```bash
# Check LLM provider status
curl http://localhost:11434/api/tags  # For Ollama
# or check API key validity for cloud providers
```

**Browser Issues**
```bash
# Install Chrome dependencies
sudo apt-get update
sudo apt-get install -y chromium-browser chromium-chromedriver

# Check Chrome installation
google-chrome --version
```

**High Memory Usage**
```bash
# Limit concurrent sessions
export MAX_CONCURRENT_SESSIONS=2

# Enable cleanup
export AUTO_CLEANUP=true
```

### **Performance Optimization**

**Speed Up Applications**
- Use local LLM (Ollama) for faster responses
- Enable browser reuse across sessions
- Optimize HTML analysis by limiting content size
- Cache common website patterns

**Reduce Resource Usage**
- Enable headless mode
- Limit screenshot capture
- Reduce session timeout
- Implement session pooling

## 📈 Advanced Usage

### **Custom LLM Prompts**
```python
# Customize prompts for specific websites
custom_prompts = {
    'linkedin.com': 'LinkedIn-specific navigation prompt...',
    'indeed.com': 'Indeed-specific navigation prompt...',
    'default': 'Generic navigation prompt...'
}
```

### **Proxy Configuration**
```python
# Configure proxy rotation
proxy_config = {
    'enabled': True,
    'providers': ['proxy1.com', 'proxy2.com'],
    'rotation_interval': 10  # requests
}
```

### **Custom Form Field Mapping**
```python
# Map custom form fields
field_mapping = {
    'years_experience': lambda resume: calculate_experience(resume),
    'salary_expectation': lambda resume: get_salary_range(resume),
    'custom_question': lambda resume: generate_answer(resume)
}
```

## �� Contributing

This adaptive bot system is designed to be extensible:

1. **Add New LLM Providers**: Extend `LLMIntegration` class
2. **Custom Website Handlers**: Add platform-specific logic
3. **Enhanced Anti-Detection**: Improve stealth capabilities
4. **Better Analytics**: Add more comprehensive tracking

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🎉 Ready to Revolutionize Job Applications?

This adaptive bot represents the future of job application automation - intelligent, adaptable, and powerful enough to handle any website structure. It's not just automation; it's **intelligent automation that thinks and adapts like a human**.

**Start building the future of job applications today!** 🚀

For support and questions, check the demo scripts and API documentation.
